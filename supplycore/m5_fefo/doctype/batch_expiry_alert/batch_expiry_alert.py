import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, now, today


class BatchExpiryAlert(Document):

    def validate(self):
        if self.resolved and not self.resolved_by:
            self.resolved_by = frappe.session.user
            self.resolved_at = now()

    @frappe.whitelist()
    def dispose_expired_batch(self, warehouse: str = None, qty: float = None) -> dict:
        """UC-17 5a: tạo SC Stock Entry Material Issue purpose Expired Disposal."""
        wh = warehouse or self.warehouse
        if not wh:
            frappe.throw(_("SC-E-DISPOSE-NO-WH: Phải truyền warehouse"))

        if qty is None or flt(qty) <= 0:
            qty = flt(frappe.db.sql("""
                SELECT COALESCE(SUM(qty_change), 0)
                FROM `tabSC Stock Ledger Entry`
                WHERE batch = %s AND warehouse = %s AND is_cancelled = 0
            """, (self.batch_no, wh))[0][0])

        if flt(qty) <= 0:
            frappe.throw(_(
                "SC-E-DISPOSE-ZERO: Không có tồn kho để hủy ({0} = 0)"
            ).format(self.batch_no))

        item_uom = frappe.db.get_value("SC Item", self.item_code, "uom")
        se = frappe.new_doc("SC Stock Entry")
        se.entry_type = "Material Issue"
        se.posting_date = today()
        se.from_warehouse = wh
        se.purpose = "Expired Disposal (UC-17)"
        se.remarks = (f"Hủy lô hết hạn {self.batch_no} per Batch Expiry Alert "
                      f"{self.name}. Expiry: {self.expiry_date}")
        se.append("items", {
            "item": self.item_code, "qty": flt(qty), "uom": item_uom,
            "batch": self.batch_no,
        })
        se.flags.ignore_permissions = True
        se.insert()
        se.submit()

        self.db_set("resolved", 1)
        self.db_set("resolution_action", "Write Off")
        self.db_set("resolution_notes", f"Hủy qua SE {se.name}, qty={qty}")
        self.db_set("resolved_by", frappe.session.user)
        self.db_set("resolved_at", now())
        frappe.db.set_value("SC Batch", self.batch_no, "disabled", 1)
        return {"stock_entry": se.name, "qty": flt(qty), "status": "disposed"}

    @frappe.whitelist()
    def mark_priority_issue(self, notes: str = None) -> dict:
        """UC-17 5b: mark batch để FEFO ưu tiên cấp phát tiếp theo."""
        self.db_set("resolved", 1)
        self.db_set("resolution_action", "Priority Issue")
        self.db_set("resolution_notes", notes or "Ưu tiên cấp phát đợt tiếp theo")
        self.db_set("resolved_by", frappe.session.user)
        self.db_set("resolved_at", now())
        return {"status": "marked_priority"}
