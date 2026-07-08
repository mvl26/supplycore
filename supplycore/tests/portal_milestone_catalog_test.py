"""Test fix uifix-portal-qc: 3 defect portal (api/portal.py).

1. compute_milestones: don SO status "Tu choi" (rejected) khong duoc danh
   dau moc nao la "current" (UI khong duoc hien pulsing-current tren don
   da bi tu choi).
2. portal_catalog/portal_contracts: tra them field `item_name` (UC-41 tim
   theo ten hoac ma).
3. portal_catalog/portal_contracts: SFC het han (valid_to < today) du
   status con "Hieu luc" trong DB (chua duoc scheduler cham nhat) khong
   duoc xuat hien qua Portal.

Run individual: bench --site supplycore-miyano.local execute supplycore.tests.portal_milestone_catalog_test.test_<name>
Run all:        bench --site supplycore-miyano.local execute supplycore.tests.portal_milestone_catalog_test.run
"""

import frappe
from frappe.utils import today, add_days, flt

from supplycore.tests.portal_api_test import (
    _get_uom,
    _seed_customer_with_contract,
    _make_submitted_sfc,
    _make_item,
    _make_portal_customer,
)


def _make_rejected_so(customer, framework_contract, item, qty):
    so = frappe.new_doc("SC Sales Order")
    so.customer = customer
    so.framework_contract = framework_contract
    so.order_date = today()
    so.append("items", {"item": item, "uom": _get_uom(), "qty": flt(qty)})
    so.flags.ignore_permissions = True
    so.insert()
    so.submit()
    so.reject()
    so.reload()
    return so


def test_rejected_order_no_current_milestone():
    """SO submit -> reject() (status "Tu choi") -> compute_milestones khong
    co moc nao "current" (chi moc 1 'placed' done, cac moc sau pending)."""
    orig_user = frappe.session.user
    try:
        from supplycore.api.portal import compute_milestones

        cust, portal_email, sfc, item = _seed_customer_with_contract(
            "MSREJ", contract_qty=50, unit_price=1000)
        so = _make_rejected_so(cust, sfc, item, 10)

        if so.status != "Từ chối":
            return {"pass": False, "msg": f"X setup sai: so.status={so.status}"}

        milestones = compute_milestones(so.name)
        current_ms = [m for m in milestones if m["status"] == "current"]
        if current_ms:
            return {"pass": False, "msg": f"X co moc 'current' tren don Tu choi: {current_ms}"}

        # Moc 1 'placed' van phai done (don da ton tai), cac moc sau khong current
        if milestones[0]["status"] != "done":
            return {"pass": False, "msg": f"X moc 1 khong done: {milestones[0]}"}
        downstream_statuses = [m["status"] for m in milestones[1:]]
        if any(s == "current" for s in downstream_statuses):
            return {"pass": False, "msg": f"X moc sau van co current: {downstream_statuses}"}

        return {"pass": True, "msg": f"OK khong co moc current tren don Tu choi: {[m['status'] for m in milestones]}"}
    except Exception as e:
        return {"pass": False, "msg": f"X threw: {str(e)[:250]}"}
    finally:
        frappe.set_user(orig_user)
        frappe.db.rollback()


def test_catalog_includes_item_name():
    """portal_catalog / portal_contracts tra ve item_name (khong rong) cho
    tung dong, khong chi item code (UC-41 tim theo ten hoac ma)."""
    orig_user = frappe.session.user
    try:
        from supplycore.api.portal import portal_catalog, portal_contracts

        cust, portal_email, sfc, item = _seed_customer_with_contract(
            "ITMNAME", contract_qty=50, unit_price=1000)
        expected_item_name = frappe.db.get_value("SC Item", item, "item_name")

        frappe.set_user(portal_email)
        catalog = portal_catalog()
        contracts = portal_contracts()

        cat_row = next((r for r in catalog if r["item"] == item), None)
        if not cat_row or not cat_row.get("item_name"):
            return {"pass": False, "msg": f"X portal_catalog thieu item_name: {catalog}"}
        if cat_row["item_name"] != expected_item_name:
            return {"pass": False, "msg": f"X item_name sai: {cat_row}"}

        contract_row = next((c for c in contracts if c["name"] == sfc), None)
        if not contract_row:
            return {"pass": False, "msg": f"X portal_contracts thieu contract {sfc}"}
        item_row = next((r for r in contract_row["items"] if r["item"] == item), None)
        if not item_row or not item_row.get("item_name"):
            return {"pass": False, "msg": f"X portal_contracts.items thieu item_name: {contract_row}"}

        return {"pass": True, "msg": f"OK item_name co mat: catalog={cat_row} contract_item={item_row}"}
    except Exception as e:
        return {"pass": False, "msg": f"X threw: {str(e)[:250]}"}
    finally:
        frappe.set_user(orig_user)
        frappe.db.rollback()


def test_expired_contract_not_in_catalog():
    """SFC het han (valid_to < today) nhung status con "Hieu luc" trong DB
    (chua duoc cham nhat qua validate()/scheduler) -> khong duoc xuat hien
    qua portal_contracts/portal_catalog."""
    orig_user = frappe.session.user
    try:
        from supplycore.api.portal import portal_catalog, portal_contracts

        cust, portal_email = _make_portal_customer("EXPCONT")
        item = _make_item("EXPCONT")
        sfc = _make_submitted_sfc(cust.name, item.name, 50, 1000)

        if sfc.status != "Hiệu lực":
            return {"pass": False, "msg": f"X setup sai: sfc.status={sfc.status}"}

        # Gia lap SFC da het han nhung status chua duoc cham nhat (bug that:
        # khong co scheduler chay _derive_status() moi ngay) -- ghi thang
        # xuong DB, khong qua validate(), de status van la "Hieu luc" stale.
        frappe.db.set_value("SC Sales Framework Contract", sfc.name, "valid_to", add_days(today(), -1))

        frappe.set_user(portal_email)
        contracts = portal_contracts()
        catalog = portal_catalog()

        contract_names = [c["name"] for c in contracts]
        catalog_items = [c["item"] for c in catalog]

        if sfc.name in contract_names:
            return {"pass": False, "msg": f"X portal_contracts van tra HD het han: {contract_names}"}
        if item.name in catalog_items:
            return {"pass": False, "msg": f"X portal_catalog van tra item cua HD het han: {catalog_items}"}

        return {"pass": True, "msg": "OK HD het han khong xuat hien trong portal_contracts/portal_catalog"}
    except Exception as e:
        return {"pass": False, "msg": f"X threw: {str(e)[:250]}"}
    finally:
        frappe.set_user(orig_user)
        frappe.db.rollback()


def run():
    tests = [
        test_rejected_order_no_current_milestone,
        test_catalog_includes_item_name,
        test_expired_contract_not_in_catalog,
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
