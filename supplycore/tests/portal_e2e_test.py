"""Test GD3 M12 Task 4 -- 4 cot moc theo doi don hang (compute_milestones)
+ E2E Portal (dat hang -> giao & nghiem thu -> xuat HD -> thu tien) + hoi quy
co lap (khach khac khong track duoc don).

Run individual: bench --site supplycore-miyano.local execute supplycore.tests.portal_e2e_test.test_<name>
Run all:        bench --site supplycore-miyano.local execute supplycore.tests.portal_e2e_test.run
"""

import frappe
from frappe.utils import today, add_days, flt

from supplycore.tests.portal_api_test import (
    _get_uom,
    _pick_warehouse,
    _make_batch,
    _seed_stock,
    _seed_customer_with_contract,
    _make_approved_so,
    _accept_dn,
)

EXPECTED_KEYS = ["placed", "delivered_accepted", "invoiced", "paid"]


def _done_count(milestones):
    return sum(1 for m in milestones if m["status"] == "done")


def test_portal_milestones_progress():
    """Dung chuoi 1 khach qua tung buoc (SO duyet -> DN nghiem thu -> SI ->
    SR thu du), goi portal_order_track (as portal user) sau moi buoc va
    assert so moc 'done' tang dan 1 -> 2 -> 3 -> 4; dung 4 moc, dung
    key/thu tu; moc 'time' dung field nghiep vu (invoice_date, receipt_date
    -- khong phai 'modified' chung chung); khach khac khong track duoc don
    nay (hoi quy co lap)."""
    orig_user = frappe.session.user
    try:
        from supplycore.api.portal import portal_order_track

        cust, portal_email, sfc, item = _seed_customer_with_contract(
            "MS", contract_qty=100, unit_price=1000)

        # ---- Buoc 1: SO dat + duyet ----
        so = _make_approved_so(cust, sfc, item, 10)

        frappe.set_user(portal_email)
        res = portal_order_track(so.name)
        milestones = res["milestones"]

        keys = [m["key"] for m in milestones]
        if len(milestones) != 4 or keys != EXPECTED_KEYS:
            return {"pass": False, "msg": f"X so moc/khoa sai: {keys}"}
        if _done_count(milestones) != 1:
            return {"pass": False, "msg": f"X sau SO done!=1: {milestones}"}
        if milestones[0]["status"] != "done" or not milestones[0]["time"]:
            return {"pass": False, "msg": f"X placed chua done/khong co time: {milestones[0]}"}
        if milestones[1]["status"] != "current":
            return {"pass": False, "msg": f"X moc 2 phai la current sau SO: {milestones[1]}"}

        # ---- Buoc 2: giao hang (DN) + nghiem thu -- thao tac noi bo ----
        frappe.set_user(orig_user)
        wh = _pick_warehouse()
        batch = _make_batch(item, add_days(today(), 200))
        _seed_stock(item, wh, batch.name, 20, rate=1000)

        dn = frappe.new_doc("SC Delivery Note")
        dn.sales_order = so.name
        dn.from_warehouse = wh
        dn.delivery_date = today()
        dn.append("items", {"item": item, "uom": _get_uom(), "qty": 10})
        dn.flags.ignore_permissions = True
        dn.insert()
        dn.submit()
        dn.reload()
        _accept_dn(dn)

        frappe.set_user(portal_email)
        res = portal_order_track(so.name)
        milestones = res["milestones"]
        if _done_count(milestones) != 2:
            return {"pass": False, "msg": f"X sau nghiem thu done!=2: {milestones}"}
        if milestones[1]["status"] != "done" or not milestones[1]["time"]:
            return {"pass": False, "msg": f"X delivered_accepted chua done/khong co time: {milestones[1]}"}
        if milestones[2]["status"] != "current":
            return {"pass": False, "msg": f"X moc 3 phai la current sau nghiem thu: {milestones[2]}"}

        # ---- Buoc 3: xuat hoa don (SI) -- thao tac noi bo ----
        frappe.set_user(orig_user)
        si = frappe.new_doc("SC Sales Invoice")
        si.customer = cust
        si.delivery_note = dn.name
        si.invoice_date = today()
        si.append("items", {"item": item, "qty": 10, "unit_price": 1000})
        si.flags.ignore_permissions = True
        si.insert()
        si.submit()
        si.reload()
        expected_invoice_date = si.invoice_date

        frappe.set_user(portal_email)
        res = portal_order_track(so.name)
        milestones = res["milestones"]
        if _done_count(milestones) != 3:
            return {"pass": False, "msg": f"X sau SI done!=3: {milestones}"}
        if milestones[2]["status"] != "done":
            return {"pass": False, "msg": f"X invoiced chua done: {milestones[2]}"}
        if str(milestones[2]["time"]) != str(expected_invoice_date):
            return {"pass": False, "msg": (
                f"X invoiced.time phai la invoice_date ({expected_invoice_date}), "
                f"khong phai truong khac: got {milestones[2]['time']}")}
        if milestones[3]["status"] != "current":
            return {"pass": False, "msg": f"X moc 4 phai la current sau SI: {milestones[3]}"}

        # ---- Buoc 4: thu du tien (SR) -- thao tac noi bo ----
        frappe.set_user(orig_user)
        sr = frappe.new_doc("SC Sales Receipt")
        sr.customer = cust
        sr.sales_invoice = si.name
        sr.receipt_date = today()
        sr.amount = flt(si.grand_total)
        sr.mode = "Chuyển khoản"
        sr.flags.ignore_permissions = True
        sr.insert()
        sr.submit()
        expected_receipt_date = sr.receipt_date

        frappe.set_user(portal_email)
        res = portal_order_track(so.name)
        milestones = res["milestones"]
        if _done_count(milestones) != 4 or any(m["status"] != "done" for m in milestones):
            return {"pass": False, "msg": f"X sau thu du khong phai ca 4 moc done: {milestones}"}
        if str(milestones[3]["time"]) != str(expected_receipt_date):
            return {"pass": False, "msg": (
                f"X paid.time phai la receipt_date ({expected_receipt_date}), "
                f"khong phai truong khac: got {milestones[3]['time']}")}

        # ---- Hoi quy co lap: khach khac (B) khong duoc track don cua A ----
        frappe.set_user(orig_user)
        cust_b, email_b, sfc_b, item_b = _seed_customer_with_contract(
            "MSB", contract_qty=50, unit_price=1000)

        frappe.set_user(email_b)
        try:
            portal_order_track(so.name)
            return {"pass": False, "msg": "X khach B track duoc don cua khach A"}
        except frappe.PermissionError:
            pass

        return {"pass": True, "msg": f"OK tien trien 1->2->3->4 dung, time dung field, co lap OK"}
    except Exception as e:
        return {"pass": False, "msg": f"X threw: {str(e)[:250]}"}
    finally:
        frappe.set_user(orig_user)
        frappe.db.rollback()


def run():
    tests = [test_portal_milestones_progress]
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
