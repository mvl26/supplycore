"""Patch: tạo các role URS-aligned cho M1+ (idempotent — chạy lại được)."""

import frappe

URS_ROLES = [
    "SupplyCore Storekeeper",
    "SupplyCore Ward Staff",
    "SupplyCore Accountant",
    "SupplyCore Executive",
    "SupplyCore Purchaser",
]


def execute():
    for r in URS_ROLES:
        if not frappe.db.exists("Role", r):
            frappe.get_doc({
                "doctype": "Role",
                "role_name": r,
                "desk_access": 1,
            }).insert(ignore_permissions=True)
    frappe.db.commit()
