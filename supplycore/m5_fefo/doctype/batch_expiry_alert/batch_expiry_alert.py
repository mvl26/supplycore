import frappe
from frappe.model.document import Document
from frappe.utils import now


class BatchExpiryAlert(Document):

    def validate(self):
        if self.resolved and not self.resolved_by:
            self.resolved_by = frappe.session.user
            self.resolved_at = now()
