"""SC Sales Order -- đơn hàng bán MVL (M7 Sales, GĐ2 Task 4).

Business rules:
- BRU-SFC-001: mỗi dòng item phải tồn tại trong Hợp đồng khung bán hàng (SFC) đang
  Hiệu lực, nếu không → throw.
- BRU-SFC-002: đơn giá luôn lấy từ SFC Item, người dùng KHÔNG được sửa (bị ghi đè).
- BRU-SO-001: tổng SL đặt (gộp theo item) không được vượt remaining_qty của SFC Item.
- BRU-AR-001: khi submit, nếu (dư nợ AR hiện tại + tổng đơn) vượt hạn mức công nợ
  của khách hàng → giữ đơn (credit_hold) + throw, cần duyệt cấp cao xử lý riêng.
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class SCSalesOrder(Document):

    def validate(self):
        self._apply_sfc_pricing_and_limits()
        self._compute_totals()

    def on_submit(self):
        self._check_credit_limit()

    def on_cancel(self):
        if self.status == "Đã duyệt":
            self._recalculate_sfc()

    # ------------------------------------------------------------------
    # BRU-SFC-001 / BRU-SFC-002 / BRU-SO-001
    # ------------------------------------------------------------------
    def _apply_sfc_pricing_and_limits(self):
        if not self.framework_contract:
            return
        fc = frappe.get_doc("SC Sales Framework Contract", self.framework_contract)
        sfc_items_by_item = {r.item: r for r in fc.items}

        for row in self.items:
            sfc_item = sfc_items_by_item.get(row.item)
            if not sfc_item or fc.status != "Hiệu lực":
                frappe.throw(_(
                    "BRU-SFC-001: Vật tư {0} không nằm trong Hợp đồng khung {1} "
                    "đang Hiệu lực."
                ).format(row.item, self.framework_contract), title="BRU-SFC-001")
            # BRU-SFC-002: đơn giá luôn lấy từ SFC, không cho sửa
            row.unit_price = flt(sfc_item.unit_price)
            row.amount = flt(row.qty) * flt(row.unit_price)

        # BRU-SO-001: gộp SL theo item rồi so với remaining_qty của SFC Item
        qty_by_item = {}
        for row in self.items:
            qty_by_item[row.item] = qty_by_item.get(row.item, 0) + flt(row.qty)
        for item_code, qty in qty_by_item.items():
            sfc_item = sfc_items_by_item[item_code]
            remaining = flt(sfc_item.remaining_qty)
            if qty > remaining:
                frappe.throw(_(
                    "BRU-SO-001: Vật tư {0} đặt tổng {1} vượt SL còn lại của Hợp đồng "
                    "khung ({2})."
                ).format(item_code, qty, remaining), title="BRU-SO-001")

    def _compute_totals(self):
        self.total_amount = sum(flt(r.amount) for r in self.items)

    # ------------------------------------------------------------------
    # BRU-AR-001
    # ------------------------------------------------------------------
    def _check_credit_limit(self):
        from supplycore.supplycore.doctype.sc_gl_entry.sc_gl_entry import SCGLEntry

        credit_limit = flt(frappe.db.get_value("SC Customer", self.customer, "credit_limit"))
        if not credit_limit or credit_limit <= 0:
            self.db_set("credit_hold", 0)
            return

        ar_account = frappe.db.get_single_value("SupplyCore Settings", "default_receivable_account")
        bal = flt(SCGLEntry.get_balance(ar_account, self.customer)) if ar_account else 0

        if (bal + flt(self.total_amount)) > credit_limit:
            self.credit_hold = 1
            self.db_set("credit_hold", 1)
            frappe.throw(_(
                "BRU-AR-001: Đơn hàng {0} (tổng {1}) cộng dư nợ hiện tại ({2}) vượt hạn "
                "mức công nợ của khách hàng ({3}). Đơn bị giữ (credit_hold) — cần lãnh đạo "
                "duyệt bổ sung hạn mức hoặc điều chỉnh trước khi submit."
            ).format(self.name, self.total_amount, bal, credit_limit), title="BRU-AR-001")

        self.db_set("credit_hold", 0)

    # ------------------------------------------------------------------
    # Workflow: approve / reject
    # ------------------------------------------------------------------
    @frappe.whitelist()
    def approve(self):
        if self.docstatus != 1:
            frappe.throw(_("Chỉ duyệt đơn đã submit"))
        self.db_set("status", "Đã duyệt")
        self.db_set("approval_by", frappe.session.user)
        self._recalculate_sfc()
        return {"status": "Đã duyệt"}

    @frappe.whitelist()
    def reject(self):
        if self.docstatus != 1:
            frappe.throw(_("Chỉ từ chối đơn đã submit"))
        self.db_set("status", "Từ chối")
        return {"status": "Từ chối"}

    def _recalculate_sfc(self):
        if not self.framework_contract:
            return
        frappe.get_doc("SC Sales Framework Contract", self.framework_contract).recalculate_sold_qty()
