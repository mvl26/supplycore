"""Patch: tao Role "SC Customer Portal" (desk_access=0) cho M12 Customer Portal (idempotent)."""

import frappe


def execute():
    if not frappe.db.exists("Role", "SC Customer Portal"):
        frappe.get_doc({
            "doctype": "Role",
            "role_name": "SC Customer Portal",
            "desk_access": 0,
        }).insert(ignore_permissions=True)
    frappe.db.commit()
