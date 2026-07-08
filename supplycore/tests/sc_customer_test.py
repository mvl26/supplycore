"""Test GD2 Task 2 -- SC Customer master (BRU-CUS-002).

Run individual: bench --site supplycore-miyano.local execute supplycore.tests.sc_customer_test.test_<name>
Run all:        bench --site supplycore-miyano.local execute supplycore.tests.sc_customer_test.run
"""

import frappe
from frappe.utils import random_string


def _make_customer(name_suffix, tax_code=None, portal_user=None):
    c = frappe.new_doc("SC Customer")
    c.customer_name = f"Khach hang test {name_suffix}"
    c.tax_code = tax_code or f"TAX-{random_string(8)}"
    if portal_user:
        c.portal_user = portal_user
    c.flags.ignore_permissions = True
    return c


def test_create_customer():
    """Tao SC Customer -> save OK, name bat dau bang SC-CUS-."""
    c = _make_customer("CREATE")
    try:
        c.insert()
        ok = c.name and c.name.startswith("SC-CUS-")
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK {c.name}"}
        return {"pass": False, "msg": f"X name={c.name}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:200]}"}


def test_tax_code_unique():
    """2 customer cung tax_code -> cai thu 2 raise."""
    tax_code = f"TAX-DUP-{random_string(8)}"
    c1 = _make_customer("DUP1", tax_code=tax_code)
    c1.insert()
    c2 = _make_customer("DUP2", tax_code=tax_code)
    try:
        c2.insert()
        frappe.db.rollback()
        return {"pass": False, "msg": "X did not throw on duplicate tax_code"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": True, "msg": f"OK threw: {str(e)[:150]}"}


def test_portal_user_unique_if_set():
    """2 customer cung portal_user -> cai thu 2 raise (BRU-CUS-002)."""
    user = "Administrator"
    c1 = _make_customer("PU1", portal_user=user)
    c1.insert()
    c2 = _make_customer("PU2", portal_user=user)
    try:
        c2.insert()
        frappe.db.rollback()
        return {"pass": False, "msg": "X did not throw on duplicate portal_user"}
    except frappe.ValidationError as e:
        msg = str(e)
        frappe.db.rollback()
        if "BRU-CUS-002" in msg:
            return {"pass": True, "msg": f"OK: {msg[:150]}"}
        return {"pass": False, "msg": f"X wrong error: {msg[:150]}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X unexpected exception: {str(e)[:150]}"}


def run():
    tests = [
        test_create_customer,
        test_tax_code_unique,
        test_portal_user_unique_if_set,
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
