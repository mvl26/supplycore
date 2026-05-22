"""Tạo 11 user test cho RBAC E2E — mỗi user 1 role chính.

Chạy: bench --site supplycore execute supplycore.setup.seed_test_users.run
"""

import frappe


TEST_USERS = [
    ("test.storekeeper@sc.local",  "Test Storekeeper",  "SupplyCore Storekeeper"),
    ("test.accountant@sc.local",   "Test Accountant",   "SupplyCore Accountant"),
    ("test.executive@sc.local",    "Test Executive",    "SupplyCore Executive"),
    ("test.ward@sc.local",         "Test Ward Staff",   "SupplyCore Ward Staff"),
    ("test.purchaser@sc.local",    "Test Purchaser",    "SupplyCore Purchaser"),
    ("test.auditor@sc.local",      "Test Auditor",      "SupplyCore Auditor"),
    ("test.pharmacy@sc.local",     "Test Pharmacy",     "Pharmacy Officer"),
    ("test.warehouse@sc.local",    "Test Warehouse",    "Warehouse Officer"),
    ("test.qc@sc.local",           "Test QC",           "QC Officer"),
    ("test.bhyt@sc.local",         "Test BHYT",         "BHYT Officer"),
    ("test.manager@sc.local",      "Test Manager",      "SupplyCore Manager"),
]

PASSWORD = "TestPass123!"


def run() -> dict:
    created = 0
    updated = 0
    for email, full_name, role in TEST_USERS:
        if frappe.db.exists("User", email):
            u = frappe.get_doc("User", email)
            # Reset roles → CHỈ role test (không thêm SupplyCore User để cô lập quyền)
            u.set("roles", [])
            u.append("roles", {"role": role})
            u.enabled = 1
            u.flags.ignore_permissions = True
            u.save()
            updated += 1
        else:
            u = frappe.new_doc("User")
            u.email = email
            u.first_name = full_name
            u.full_name = full_name
            u.enabled = 1
            u.send_welcome_email = 0
            u.new_password = PASSWORD
            u.user_type = "System User"
            u.append("roles", {"role": role})
            u.flags.ignore_permissions = True
            u.insert()
            created += 1
    # Force password reset for all test users
    from frappe.utils.password import update_password
    for email, _, _ in TEST_USERS:
        try:
            update_password(email, PASSWORD)
        except Exception:
            pass
    frappe.db.commit()
    return {"created": created, "updated": updated, "total": len(TEST_USERS),
            "password": PASSWORD}
