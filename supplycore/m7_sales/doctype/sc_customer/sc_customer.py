"""SC Customer -- master khách hàng M7 Sales (BRU-CUS-002)."""

import frappe
from frappe import _
from frappe.model.document import Document


class SCCustomer(Document):

    def validate(self):
        self._validate_portal_user_unique()
        self._validate_portal_required_for_active()

    def _validate_portal_user_unique(self):
        if not self.portal_user:
            return
        if frappe.db.exists("SC Customer", {
            "portal_user": self.portal_user,
            "name": ["!=", self.name or ""],
        }):
            frappe.throw(_(
                "BRU-CUS-002: Tài khoản Portal {0} đã được gán cho khách hàng khác"
            ).format(self.portal_user))

    def _validate_portal_required_for_active(self):
        if self.status == "Hoạt động" and not self.portal_user:
            frappe.throw(_(
                "BRU-CUS-001: Khách hàng phải có tài khoản Portal trước khi kích hoạt (Hoạt động)."
            ))
