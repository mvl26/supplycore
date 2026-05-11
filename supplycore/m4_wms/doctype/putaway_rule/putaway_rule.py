"""Putaway Rule (UC-12) — match item/item_group → target bin để suggest putaway."""

import frappe
from frappe import _
from frappe.model.document import Document


class PutawayRule(Document):

    def validate(self):
        if not self.item and not self.item_group:
            frappe.throw(_(
                "SC-E-PUTAWAY-RULE: Phải nhập 'Vật tư cụ thể' HOẶC 'Nhóm vật tư'"
            ))
        if not self.title:
            self.title = self.name
