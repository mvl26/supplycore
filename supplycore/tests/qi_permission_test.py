"""Test fix uifix-portal-qc: BRU-QC-002 -- Chi QC Officer/Manager duoc ket
luan QC (submit SC Quality Inspection). SupplyCore Storekeeper va Warehouse
Officer chuan bi/nhap lieu (read/write/create) nhung KHONG duoc submit.

Run individual: bench --site supplycore-miyano.local execute supplycore.tests.qi_permission_test.test_<name>
Run all:        bench --site supplycore-miyano.local execute supplycore.tests.qi_permission_test.run
"""

import frappe
from frappe.utils import random_string


def _make_role_only_user(role, suffix):
    """1 System User CHI co `role` truyen vao (khong co role nao khac ngoai
    mac dinh) -- de kiem tra permission khong bi vacuously True vi user co
    them System Manager/role khac."""
    email = f"qiperm_{suffix.lower()}_{random_string(8)}@example.com"
    u = frappe.new_doc("User")
    u.email = email
    u.first_name = f"QIPerm {suffix}"
    u.user_type = "System User"
    u.send_welcome_email = 0
    u.append("roles", {"role": role})
    u.flags.ignore_permissions = True
    u.insert()
    return email


def test_storekeeper_cannot_submit_qi():
    """User CHI co role 'SupplyCore Storekeeper' -> has_permission(submit)=False.
    User CHI co role 'Warehouse Officer' -> has_permission(submit)=False.
    User CHI co role 'QC Officer' -> has_permission(submit)=True (BRU-QC-002:
    chi QC Officer/Manager duoc ket luan QC)."""
    try:
        storekeeper_email = _make_role_only_user("SupplyCore Storekeeper", "SK")
        warehouse_email = _make_role_only_user("Warehouse Officer", "WH")
        qc_email = _make_role_only_user("QC Officer", "QC")

        sk_can_submit = frappe.has_permission("SC Quality Inspection", "submit", user=storekeeper_email)
        wh_can_submit = frappe.has_permission("SC Quality Inspection", "submit", user=warehouse_email)
        qc_can_submit = frappe.has_permission("SC Quality Inspection", "submit", user=qc_email)

        # Doi chieu voi read -- storekeeper/warehouse van phai giu duoc read
        # (chi bi tuoc submit, khong phai toan bo quyen)
        sk_can_read = frappe.has_permission("SC Quality Inspection", "read", user=storekeeper_email)

        if sk_can_submit:
            return {"pass": False, "msg": "X Storekeeper van submit duoc QI (BRU-QC-002 vi pham)"}
        if wh_can_submit:
            return {"pass": False, "msg": "X Warehouse Officer van submit duoc QI (BRU-QC-002 vi pham)"}
        if not qc_can_submit:
            return {"pass": False, "msg": "X QC Officer khong submit duoc QI"}
        if not sk_can_read:
            return {"pass": False, "msg": "X Storekeeper mat luon ca quyen read (chi nen mat submit)"}

        return {"pass": True, "msg": "OK Storekeeper/Warehouse Officer khong submit duoc, QC Officer submit duoc, Storekeeper van read duoc"}
    except Exception as e:
        return {"pass": False, "msg": f"X threw: {str(e)[:250]}"}
    finally:
        frappe.db.rollback()


def run():
    tests = [test_storekeeper_cannot_submit_qi]
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
