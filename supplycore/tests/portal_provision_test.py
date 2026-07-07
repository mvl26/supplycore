"""Test GD3 M12 Task 1 -- Role Portal + provisioning + BRU-CUS-001.

Run individual: bench --site supplycore-miyano.local execute supplycore.tests.portal_provision_test.test_<name>
Run all:        bench --site supplycore-miyano.local execute supplycore.tests.portal_provision_test.run
"""

import frappe
from frappe.utils import random_string


def _make_customer(status="Tạm ngưng", portal_user=None):
    c = frappe.new_doc("SC Customer")
    c.customer_name = f"KH Portal test {random_string(6)}"
    c.tax_code = f"TAX-PORTAL-{random_string(8)}"
    c.status = status
    if portal_user:
        c.portal_user = portal_user
    c.flags.ignore_permissions = True
    c.insert()
    return c


def test_portal_role_exists():
    """Sau migrate, Role 'SC Customer Portal' phai ton tai voi desk_access=0."""
    try:
        exists = frappe.db.exists("Role", "SC Customer Portal")
        if not exists:
            return {"pass": False, "msg": "X Role 'SC Customer Portal' chua ton tai"}
        desk_access = frappe.db.get_value("Role", "SC Customer Portal", "desk_access")
        if desk_access:
            return {"pass": False, "msg": f"X desk_access={desk_access} (expect 0)"}
        return {"pass": True, "msg": "OK Role exists, desk_access=0"}
    except Exception as e:
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_activate_customer_without_portal_blocked():
    """Customer Tam ngung -> flip Hoat dong khong portal_user -> throw BRU-CUS-001."""
    c = _make_customer(status="Tạm ngưng")
    try:
        c.status = "Hoạt động"
        c.save()
        frappe.db.rollback()
        return {"pass": False, "msg": "X khong throw khi kich hoat ma khong co portal_user"}
    except frappe.ValidationError as e:
        frappe.db.rollback()
        if "BRU-CUS-001" in str(e):
            return {"pass": True, "msg": f"OK throw: {str(e)[:120]}"}
        return {"pass": False, "msg": f"X wrong error: {str(e)[:120]}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X unexpected: {str(e)[:120]}"}


def test_provision_creates_website_user_and_links():
    """portal_provision(customer, email) -> tao Website User + role Portal + link customer.portal_user."""
    from supplycore.api.portal import portal_provision

    c = _make_customer(status="Tạm ngưng")
    email = f"portaltest_{random_string(8)}@example.com"
    try:
        result = portal_provision(c.name, email)
        if result != email:
            frappe.db.rollback()
            return {"pass": False, "msg": f"X return={result}, expect {email}"}

        if not frappe.db.exists("User", email):
            frappe.db.rollback()
            return {"pass": False, "msg": "X User khong duoc tao"}

        user_doc = frappe.get_doc("User", email)
        roles = [r.role for r in user_doc.roles]
        if "SC Customer Portal" not in roles:
            frappe.db.rollback()
            return {"pass": False, "msg": f"X role Portal chua duoc gan: {roles}"}

        if user_doc.user_type != "Website User":
            frappe.db.rollback()
            return {"pass": False, "msg": f"X user_type={user_doc.user_type}"}

        portal_user = frappe.db.get_value("SC Customer", c.name, "portal_user")
        frappe.db.rollback()
        if portal_user != email:
            return {"pass": False, "msg": f"X customer.portal_user={portal_user}"}

        return {"pass": True, "msg": f"OK provisioned {email}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:200]}"}


def run():
    tests = [
        test_portal_role_exists,
        test_activate_customer_without_portal_blocked,
        test_provision_creates_website_user_and_links,
    ]
    results = []
    for t in tests:
        try:
            r = t()
            r["test"] = t.__name__
        except Exception as e:
            r = {"test": t.__name__, "pass": False, "msg": f"EXCEPTION: {str(e)[:200]}"}
        results.append(r)
    frappe.db.rollback()
    passed = sum(1 for r in results if r.get("pass"))
    return {"passed": passed, "total": len(results), "results": results}
