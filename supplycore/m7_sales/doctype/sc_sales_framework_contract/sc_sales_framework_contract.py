"""SC Sales Framework Contract — Hợp đồng khung bán hàng (M7 Sales, GĐ2 Task 3)."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, today, flt


class SCSalesFrameworkContract(Document):

    def validate(self):
        self._compute_items()
        self._compute_totals()
        self._derive_status()

    def on_submit(self):
        self.db_set("status", "Hiệu lực")
        if not self.approved_by:
            self.db_set("approved_by", frappe.session.user)

    def on_cancel(self):
        self.db_set("status", "Thanh lý")

    # ------------------------------------------------------------------
    # Computations
    # ------------------------------------------------------------------
    def _compute_items(self):
        for row in self.items:
            row.remaining_qty = flt(row.contract_qty) - flt(row.sold_qty or 0)

    def _compute_totals(self):
        self.total_value = sum(flt(r.contract_qty) * flt(r.unit_price) for r in self.items)

    def _derive_status(self):
        if self.docstatus == 0:
            self.status = "Nháp"
            return
        if self.docstatus == 2:
            return  # on_cancel đã db_set "Thanh lý"
        # docstatus == 1 (đã submit): chỉ chuyển "Hiệu lực" -> "Hết hạn" khi quá hạn
        if self.status == "Hiệu lực" and self.valid_to and getdate(today()) > getdate(self.valid_to):
            self.status = "Hết hạn"

    # ------------------------------------------------------------------
    # Public API — gọi từ SC Sales Order khi submit/cancel (Task 4)
    # ------------------------------------------------------------------
    @frappe.whitelist()
    def recalculate_sold_qty(self):
        """Tính lại sold_qty/remaining_qty theo SC Sales Order đã submit.

        SC Sales Order chưa tồn tại ở Task 3 — guard bằng table_exists để
        no-op an toàn (Task 4 sẽ wire lại reduction thật khi SO ra đời).
        """
        # Chặn portal gọi trực tiếp qua run_doc_method (chỉ check read) — nhất
        # quán với SC Sales Order.approve/reject. Caller nội bộ (SO submit/cancel)
        # chạy dưới session nhân viên nên không bị chặn.
        from supplycore.utils.permissions import block_portal
        block_portal()
        has_so = frappe.db.table_exists("SC Sales Order")
        for row in self.items:
            sold = 0
            if has_so:
                sold = frappe.db.sql("""
                    SELECT COALESCE(SUM(soi.qty), 0)
                    FROM `tabSO Item` soi
                    JOIN `tabSC Sales Order` so ON so.name = soi.parent
                    WHERE so.framework_contract = %s
                      AND so.docstatus = 1
                      AND soi.item = %s
                """, (self.name, row.item))[0][0]
            sold = flt(sold)
            frappe.db.set_value("SFC Item", row.name, {
                "sold_qty": sold,
                "remaining_qty": flt(row.contract_qty) - sold,
            })
