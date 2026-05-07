import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, today, now


class SCBatch(Document):

    def validate(self):
        if self.expiry_date and self.manufacturing_date:
            if getdate(self.expiry_date) <= getdate(self.manufacturing_date):
                frappe.throw(_("Hạn dùng phải sau ngày sản xuất"))
        if self.blocked and not self.block_reason:
            frappe.throw(_("Phải ghi lý do khi block batch"))
        if self.blocked and not self.blocked_by:
            self.blocked_by = frappe.session.user
            self.blocked_at = now()
        if not self.blocked:
            self.blocked_by = None
            self.blocked_at = None

    def get_qty_at_warehouse(self, warehouse: str) -> float:
        """Trả tồn kho lô tại warehouse từ SC Stock Ledger Entry."""
        from frappe.utils import flt
        return flt(frappe.db.sql("""
            SELECT COALESCE(SUM(qty_change), 0)
            FROM `tabSC Stock Ledger Entry`
            WHERE batch = %s AND warehouse = %s AND is_cancelled = 0
        """, (self.name, warehouse))[0][0])
