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

    def on_submit(self): self.db_set("status", "Pending")
    def on_cancel(self): self.db_set("status", "Cancelled")


class SCMaterialRequestItem(Document): pass
