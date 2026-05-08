import frappe
from frappe.model.document import Document
from frappe.utils import flt


class SCMaterialRequest(Document):
    def validate(self):
        total_qty = 0; total = 0
        for r in self.items:
            r.estimated_amount = flt(r.qty) * flt(r.estimated_unit_cost)
            total_qty += flt(r.qty); total += flt(r.estimated_amount)
        self.total_qty = total_qty
        self.total_estimated_cost = total
        if self.docstatus == 0:
            self.status = "Draft"

    def on_submit(self):
        self.db_set("status", "Approved")

    def on_cancel(self):
        self.db_set("status", "Cancelled")

    @frappe.whitelist()
    def get_po_suggestion(self):
        """UI helper: preview groupings + unmatched items trước khi user click "Tạo PO"."""
        from supplycore.m2_planning.api.po_suggest import suggest_po_from_mr
        return suggest_po_from_mr(self.name, auto_create=0)

    @frappe.whitelist()
    def create_purchase_orders(self):
        """UI button: tạo draft PO theo nhóm FC. Items không match FC → unmatched."""
        from supplycore.m2_planning.api.po_suggest import suggest_po_from_mr
        return suggest_po_from_mr(self.name, auto_create=1)


class SCMaterialRequestItem(Document): pass
