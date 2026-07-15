"""SC Sales Order -- đơn hàng bán MVL (M7 Sales, GĐ2 Task 4).

Business rules:
- BRU-SFC-001: mỗi dòng item phải tồn tại trong Hợp đồng khung bán hàng (SFC) đang
  Hiệu lực, nếu không → throw.
- BRU-SFC-002: đơn giá luôn lấy từ SFC Item, người dùng KHÔNG được sửa (bị ghi đè).
- BRU-SO-001: tổng SL đặt (gộp theo item) không được vượt SL còn lại của SFC Item.
  Kiểm LIVE (SUM SO Item.qty của các SC Sales Order khác đã submit cùng
  framework_contract+item) thay vì tin remaining_qty đã lưu (remaining_qty chỉ
  cập nhật lúc approve()) — chặn TOCTOU khi 2 SO submit gần như đồng thời trong
  lúc remaining_qty còn nguyên. approve() kiểm lại lần nữa (defense-in-depth)
  sau khi recalc, nếu SFC Item.remaining_qty âm thì không cho duyệt.
- BRU-AR-001: khi submit, nếu (dư nợ AR hiện tại + tổng đơn) vượt hạn mức công nợ
  của khách hàng → giữ đơn (credit_hold) + throw, cần duyệt cấp cao xử lý riêng.
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate, today

from supplycore.utils.permissions import block_portal


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

        # BRU-SFC-001 (hiệu lực theo NGÀY): không được đặt đơn trên HĐ khung
        # CHƯA tới ngày hiệu lực hoặc ĐÃ hết hạn. KHÔNG tin `fc.status` cho việc
        # này — SFC không có scheduler tự chuyển "Hiệu lực"→"Hết hạn", và
        # on_submit set cứng status="Hiệu lực" bất kể valid_from tương lai, nên
        # status có thể stale. Kiểm ngày ở write-path đóng mọi đường (portal/
        # desk/API) vì mọi SC Sales Order đều chạy validate().
        today_d = getdate(today())
        if fc.valid_from and getdate(fc.valid_from) > today_d:
            frappe.throw(_(
                "BRU-SFC-001: Hợp đồng khung {0} chưa tới ngày hiệu lực ({1}) — "
                "không thể đặt đơn."
            ).format(self.framework_contract, fc.valid_from), title="BRU-SFC-001")
        if fc.valid_to and getdate(fc.valid_to) < today_d:
            frappe.throw(_(
                "BRU-SFC-001: Hợp đồng khung {0} đã hết hạn ({1}) — không thể đặt đơn."
            ).format(self.framework_contract, fc.valid_to), title="BRU-SFC-001")

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

        # BRU-SO-001: gộp SL theo item rồi so với SL còn lại của SFC Item, tính
        # LIVE (không tin remaining_qty đã lưu — remaining_qty chỉ cập nhật lúc
        # approve(), nên 2 SO submit gần như đồng thời đều thấy remaining còn
        # nguyên → TOCTOU). Cộng thêm SL đã cam kết bởi các SC Sales Order KHÁC
        # đã submit (docstatus=1) cùng framework_contract+item, so với tổng
        # contract_qty của SFC Item.
        qty_by_item = {}
        for row in self.items:
            qty_by_item[row.item] = qty_by_item.get(row.item, 0) + flt(row.qty)
        for item_code, qty in qty_by_item.items():
            sfc_item = sfc_items_by_item[item_code]
            committed = flt(frappe.db.sql("""
                SELECT COALESCE(SUM(soi.qty), 0)
                FROM `tabSO Item` soi
                JOIN `tabSC Sales Order` so ON so.name = soi.parent
                WHERE so.framework_contract = %s
                  AND so.docstatus = 1
                  AND so.status != 'Từ chối'
                  AND so.name != %s
                  AND soi.item = %s
            """, (self.framework_contract, self.name or "", item_code))[0][0])
            contract_qty = flt(sfc_item.contract_qty)
            if (qty + committed) > contract_qty:
                frappe.throw(_(
                    "BRU-SO-001: Vật tư {0} đặt {1} + đã cam kết {2} (đơn khác đã submit) "
                    "vượt tổng SL Hợp đồng khung ({3})."
                ).format(item_code, qty, committed, contract_qty), title="BRU-SO-001")

    def _compute_totals(self):
        self.total_amount = sum(flt(r.amount) for r in self.items)

    # ------------------------------------------------------------------
    # BRU-INV-002 — chặn tồn ngay lúc gọi hàng (Q1: chặn sớm)
    # ------------------------------------------------------------------
    def check_stock_availability(self):
        """Chặn đặt hàng khi tồn khả dụng < SL đặt — chốt chặn SỚM lúc khách gọi
        hàng qua Portal (khác BRU-INV-001 chỉ chặn ở khâu lập phiếu giao). Gọi
        TƯỜNG MINH từ `portal_order_place` (KHÔNG nằm trong validate) để chỉ áp
        cho đường khách gọi hàng — nhân viên tạo SO nội bộ/đặt trước vẫn qua chốt
        cứng ở DN, không bị chặn sớm. Tính tổng tồn khả dụng của item trên TẤT CẢ
        kho (chưa chọn kho xuất lúc này), loại lô QC Pending/Rejected/blocked.
        Bật/tắt qua Settings.block_order_on_insufficient_stock (không hard-code).
        """
        from supplycore.utils.receivables import is_stock_block_enabled
        if not is_stock_block_enabled():
            return
        from supplycore.supplycore.doctype.sc_stock_ledger_entry.sc_stock_ledger_entry import (
            SCStockLedgerEntry,
        )
        qty_by_item = {}
        for row in self.items:
            qty_by_item[row.item] = qty_by_item.get(row.item, 0) + flt(row.qty)
        for item_code, qty in qty_by_item.items():
            avail = SCStockLedgerEntry.get_available_qty(item_code)
            if flt(qty) > flt(avail):
                item_name = frappe.db.get_value("SC Item", item_code, "item_name") or item_code
                frappe.throw(_(
                    "BRU-INV-002: Tồn kho khả dụng của vật tư {0} không đủ — cần {1}, "
                    "còn {2}. Vui lòng giảm số lượng hoặc liên hệ nhà cung cấp."
                ).format(item_name, qty, avail), title="BRU-INV-002")

    # ------------------------------------------------------------------
    # BRU-AR-001
    # ------------------------------------------------------------------
    def _check_credit_limit(self):
        # GĐ MVL — dùng HÀM CHUẨN DUY NHẤT get_customer_outstanding/credit_limit
        # (utils.receivables), KHÔNG tự resolve TK 131 hay tự SUM (đóng finding
        # audit D: rule cũ fail-open khi default_receivable_account trống → bỏ
        # lọt dư nợ; và lệch số với portal). Cờ bật/tắt + ngưỡng mặc định lấy từ
        # SupplyCore Settings (không hard-code).
        from supplycore.utils.receivables import (
            is_credit_check_enabled, get_customer_outstanding,
            get_customer_credit_limit, get_min_payment,
        )

        if not is_credit_check_enabled():
            self.db_set("credit_hold", 0)
            return

        credit_limit = get_customer_credit_limit(self.customer)
        if credit_limit <= 0:
            # Không đặt ngưỡng (khách không có hạn mức riêng và Settings không đặt
            # default) → không chặn. Đặt Settings.default_credit_limit > 0 để chặn
            # cả khách tự đăng ký (credit_limit=0).
            self.db_set("credit_hold", 0)
            return

        bal = get_customer_outstanding(self.customer)
        if (bal + flt(self.total_amount)) > credit_limit:
            min_pay = get_min_payment(self.customer, self.total_amount)
            self.credit_hold = 1
            self.db_set("credit_hold", 1)
            frappe.throw(_(
                "BRU-AR-001: Đơn hàng {0} (tổng {1}) cộng dư nợ hiện tại ({2}) vượt hạn "
                "mức công nợ của khách hàng ({3}). Cần thanh toán tối thiểu {4} trước khi "
                "gọi hàng. Đơn bị giữ (credit_hold)."
            ).format(self.name, flt(self.total_amount), bal, credit_limit, min_pay),
                title="BRU-AR-001")

        self.db_set("credit_hold", 0)

    # ------------------------------------------------------------------
    # Workflow: approve / reject
    # ------------------------------------------------------------------
    @frappe.whitelist()
    def approve(self):
        # GĐ4 Task 5 (security sweep): `run_doc_method` (đường gọi whitelisted
        # instance method) chỉ kiểm `doc.has_permission("read")` trước khi gọi
        # method — KHÔNG kiểm thêm gì cho hành động này. Vì role
        # "SC Customer Portal" có read=1 (đã scope đúng theo khách) trên
        # chính SC Sales Order của khách, nếu không chặn ở đây khách hàng có
        # thể tự gọi approve() duyệt luôn đơn hàng của chính mình — bỏ qua
        # bước duyệt nội bộ (đặc quyền leo thang, không phải rò rỉ chéo
        # khách nhưng vẫn là bypass quy trình nghiệp vụ nội bộ).
        block_portal()
        if self.docstatus != 1:
            frappe.throw(_("Chỉ duyệt đơn đã submit"))
        self._recalculate_sfc()
        self._check_sfc_not_oversold()
        self.db_set("status", "Đã duyệt")
        self.db_set("approval_by", frappe.session.user)
        return {"status": "Đã duyệt"}

    @frappe.whitelist()
    def reject(self):
        block_portal()
        if self.docstatus != 1:
            frappe.throw(_("Chỉ từ chối đơn đã submit"))
        self.db_set("status", "Từ chối")
        return {"status": "Từ chối"}

    def _recalculate_sfc(self):
        if not self.framework_contract:
            return
        frappe.get_doc("SC Sales Framework Contract", self.framework_contract).recalculate_sold_qty()

    def _check_sfc_not_oversold(self):
        """Defense-in-depth cho BRU-SO-001: sau recalc, nếu SFC Item.remaining_qty
        âm (over-commit lọt qua check ở validate() — vd race condition thực sự
        đồng thời) thì KHÔNG cho duyệt đơn này."""
        if not self.framework_contract:
            return
        fc = frappe.get_doc("SC Sales Framework Contract", self.framework_contract)
        for row in fc.items:
            if flt(row.remaining_qty) < 0:
                frappe.throw(_(
                    "BRU-SO-001: Sau khi duyệt, Vật tư {0} của Hợp đồng khung {1} có SL "
                    "còn lại âm ({2}) — over-commit, không thể duyệt đơn này."
                ).format(row.item, self.framework_contract, row.remaining_qty),
                    title="BRU-SO-001")
