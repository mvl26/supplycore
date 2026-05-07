"""Framework Contract — Hợp đồng khung NCC (M1)."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, today, flt, date_diff


class FrameworkContract(Document):

    def validate(self):
        self._validate_dates()
        self._validate_supplier_active()
        self._compute_items()
        self._compute_totals()
        self._derive_status()

    def on_submit(self):
        self.db_set("status", self._compute_active_or_expired())

    def on_cancel(self):
        self.db_set("status", "Terminated")
        # Block các Release Order đang draft tham chiếu HĐ này
        for ro in frappe.get_all("Release Order",
                                  filters={"framework_contract": self.name, "docstatus": 0},
                                  fields=["name"]):
            frappe.db.set_value("Release Order", ro.name, "status", "Cancelled")

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    def _validate_dates(self):
        if getdate(self.valid_to) <= getdate(self.valid_from):
            frappe.throw(_("Ngày hết hạn phải sau ngày hiệu lực"), title="SC-E-DATE")
        if getdate(self.contract_date) > getdate(self.valid_from):
            frappe.throw(_("Ngày ký không được sau ngày hiệu lực"), title="SC-E-DATE")

    def _validate_supplier_active(self):
        disabled = frappe.db.get_value("SC Supplier", self.supplier, "disabled")
        if disabled:
            frappe.throw(_("NCC {0} đang bị vô hiệu hóa").format(self.supplier))
        # Check blacklist (blacklist_flag custom field — sẽ tạo qua patch)
        blacklist = frappe.db.get_value("SC Supplier", self.supplier, "blacklist_flag") or 0
        if blacklist and self.docstatus == 0:
            frappe.msgprint(_("Cảnh báo: NCC này đang trong blacklist. Cần xác nhận từ Lãnh đạo."),
                            indicator="orange", alert=True)

    # ------------------------------------------------------------------
    # Computations
    # ------------------------------------------------------------------
    def _compute_items(self):
        for row in self.items:
            row.total_amount = flt(row.contract_qty) * flt(row.unit_price)
            row.remaining_qty = flt(row.contract_qty) - flt(row.ordered_qty or 0)

    def _compute_totals(self):
        items_total = sum(flt(r.total_amount) for r in self.items)
        # total_value do user nhập — kiểm tra so với tổng items
        if self.total_value and abs(flt(self.total_value) - items_total) > 1:
            frappe.msgprint(_("Tổng giá trị nhập tay ({0}) khác tổng các dòng vật tư ({1})").format(
                frappe.format(self.total_value, {"fieldtype": "Currency"}),
                frappe.format(items_total, {"fieldtype": "Currency"})),
                indicator="orange", alert=True)
        used = flt(self.used_value or 0)
        committed = flt(self.committed_value or 0)
        self.remaining_value = flt(self.total_value) - used - committed

    def _derive_status(self):
        if self.docstatus == 0:
            self.status = "Draft"
        elif self.docstatus == 2:
            self.status = "Terminated"
        else:
            self.status = self._compute_active_or_expired()
        # Cờ sắp hết hạn
        days_left = date_diff(self.valid_to, today())
        self.expiring_soon = 1 if 0 <= days_left <= 30 else 0

    def _compute_active_or_expired(self) -> str:
        """Đã submit (docstatus=1) → Active hoặc Expired tùy valid_to.

        Lưu ý: không trả 'Draft' vì 'Draft' = docstatus 0. Hợp đồng đã ký
        nhưng chưa tới valid_from vẫn là Active (đã có hiệu lực pháp lý;
        chỉ chưa thể bắt đầu gọi hàng — kiểm tra ở Release Order)."""
        today_d = getdate(today())
        if today_d > getdate(self.valid_to):
            return "Expired"
        return "Active"

    # ------------------------------------------------------------------
    # Public API — gọi từ Release Order / Purchase Order
    # ------------------------------------------------------------------
    @frappe.whitelist()
    def recalculate_used_value(self):
        """Tính lại used_value (PO submit) + committed_value (RO Approved chưa convert)."""
        used = frappe.db.sql("""
            SELECT COALESCE(SUM(grand_total), 0)
            FROM `tabSC Purchase Order`
            WHERE framework_contract = %s AND docstatus = 1
        """, self.name)[0][0]

        committed = frappe.db.sql("""
            SELECT COALESCE(SUM(total_amount), 0)
            FROM `tabRelease Order`
            WHERE framework_contract = %s
              AND docstatus = 1
              AND status = 'Approved'
        """, self.name)[0][0]

        self.db_set("used_value", flt(used))
        self.db_set("committed_value", flt(committed))
        self.db_set("remaining_value", flt(self.total_value) - flt(used) - flt(committed))

        # Per-item: ordered_qty = SL từ PO submit + SL từ RO Approved chưa convert
        for row in self.items:
            po_qty = frappe.db.sql("""
                SELECT COALESCE(SUM(poi.qty), 0)
                FROM `tabSC Purchase Order Item` poi
                JOIN `tabSC Purchase Order` po ON po.name = poi.parent
                WHERE po.framework_contract = %s
                  AND po.docstatus = 1
                  AND poi.item = %s
            """, (self.name, row.item_code))[0][0]
            ro_qty = frappe.db.sql("""
                SELECT COALESCE(SUM(roi.qty), 0)
                FROM `tabRO Item` roi
                JOIN `tabRelease Order` ro ON ro.name = roi.parent
                WHERE ro.framework_contract = %s
                  AND ro.docstatus = 1
                  AND ro.status = 'Approved'
                  AND roi.item_code = %s
            """, (self.name, row.item_code))[0][0]
            committed_qty = flt(po_qty) + flt(ro_qty)
            frappe.db.set_value("FC Item", row.name, {
                "ordered_qty": committed_qty,
                "remaining_qty": flt(row.contract_qty) - committed_qty,
            })

    def get_item_unit_price(self, item_code: str) -> float:
        """Tra đơn giá HĐK cho 1 item — gọi từ Release Order."""
        for row in self.items:
            if row.item_code == item_code:
                return flt(row.unit_price)
        frappe.throw(_("Vật tư {0} không có trong hợp đồng khung {1}").format(item_code, self.name))

    def get_item_remaining_qty(self, item_code: str) -> float:
        for row in self.items:
            if row.item_code == item_code:
                return flt(row.remaining_qty)
        return 0
