"""Test GĐ MVL — Workstream B: portal giao nhận/nghiệm thu/hoá đơn + cách ly.

- b6: SC Acceptance Record scope theo customer (list + download) — KH chỉ thấy của mình.
- b4: portal_confirm_delivery — KH tự xác nhận nhận hàng -> tạo biên bản nghiệm thu.
- c1: portal_deliveries / portal_acceptance_records / portal_invoices own-only.
- c7: portal_contracts trả order_count + total_ordered_qty.

Run: bench --site supplycore-miyano.local execute supplycore.tests.mvl_portal_test.run
"""

import frappe
from frappe.utils import flt, today, add_days

from supplycore.tests.portal_api_test import (
    _seed_customer_with_contract, _make_approved_so, _pick_warehouse,
    _make_batch, _seed_stock, _get_uom,
)


def _make_delivered_dn(suffix, qty=10, unit_price=1000):
    """Chuỗi tới DN đã submit (status 'Đã giao'), CHƯA nghiệm thu.
    Trả (cust, email, sfc, item, so_name, dn_name)."""
    cust, email, sfc, item = _seed_customer_with_contract(suffix, 100, unit_price)
    so = _make_approved_so(cust, sfc, item, qty)
    wh = _pick_warehouse()
    batch = _make_batch(item, add_days(today(), 200))
    _seed_stock(item, wh, batch.name, qty * 2, rate=unit_price)
    dn = frappe.new_doc("SC Delivery Note")
    dn.sales_order = so.name
    dn.from_warehouse = wh
    dn.delivery_date = today()
    dn.append("items", {"item": item, "uom": _get_uom(), "qty": flt(qty)})
    dn.flags.ignore_permissions = True
    dn.insert()
    dn.submit()
    dn.reload()
    return cust, email, sfc, item, so.name, dn.name


def test_confirm_delivery_creates_acceptance():
    orig = frappe.session.user
    try:
        cust, email, sfc, item, so, dn = _make_delivered_dn("CONF")
        from supplycore.api.portal import portal_confirm_delivery
        frappe.set_user(email)
        res = portal_confirm_delivery(dn, note="Đã nhận đủ")
        ar = res.get("acceptance_record")
        frappe.set_user(orig)
        ar_customer = frappe.db.get_value("SC Acceptance Record", ar, "customer")
        dn_status = frappe.db.get_value("SC Delivery Note", dn, "status")
        ok = ar and ar_customer == cust and dn_status == "Đã nghiệm thu"
        return {"pass": bool(ok), "msg": f"OK biên bản {ar}, DN -> {dn_status}" if ok
                else f"X ar={ar} cust={ar_customer} dn_status={dn_status}"}
    finally:
        frappe.set_user(orig)
        frappe.db.rollback()


def test_confirm_delivery_other_customer_denied():
    orig = frappe.session.user
    try:
        custA, emailA, *_ = _make_delivered_dn("CONFA")
        custB, emailB, sfcB, itemB, soB, dnB = _make_delivered_dn("CONFB")
        from supplycore.api.portal import portal_confirm_delivery
        # Khách A cố xác nhận phiếu giao của khách B -> PermissionError
        frappe.set_user(emailA)
        try:
            portal_confirm_delivery(dnB)
            return {"pass": False, "msg": "X khách A xác nhận được DN của khách B"}
        except frappe.PermissionError:
            return {"pass": True, "msg": "OK chặn xác nhận chéo khách (PermissionError)"}
    finally:
        frappe.set_user(orig)
        frappe.db.rollback()


def test_acceptance_records_list_isolation():
    """Portal A get_all SC Acceptance Record -> chỉ thấy biên bản của A (permission_query)."""
    orig = frappe.session.user
    try:
        custA, emailA, sfcA, itemA, soA, dnA = _make_delivered_dn("ISOA")
        custB, emailB, sfcB, itemB, soB, dnB = _make_delivered_dn("ISOB")
        from supplycore.api.portal import portal_confirm_delivery
        frappe.set_user(emailA); portal_confirm_delivery(dnA); frappe.set_user(orig)
        frappe.set_user(emailB); portal_confirm_delivery(dnB); frappe.set_user(orig)

        frappe.set_user(emailA)
        # get_list áp permission_query_conditions (get_all bỏ qua permission) — đây
        # là đường REST/list mà portal thực sự đi, cần verify scope theo customer.
        rows = frappe.get_list("SC Acceptance Record", fields=["name", "customer"])
        frappe.set_user(orig)
        others = [r for r in rows if r.customer != custA]
        ok = len(rows) >= 1 and not others
        return {"pass": ok, "msg": f"OK A thấy {len(rows)} biên bản, đều của A" if ok
                else f"X rò rỉ: {others[:3]}"}
    finally:
        frappe.set_user(orig)
        frappe.db.rollback()


def test_acceptance_download_other_denied():
    orig = frappe.session.user
    try:
        custA, emailA, sfcA, itemA, soA, dnA = _make_delivered_dn("DLA")
        custB, emailB, sfcB, itemB, soB, dnB = _make_delivered_dn("DLB")
        from supplycore.api.portal import portal_confirm_delivery, portal_document_download
        frappe.set_user(emailB)
        resB = portal_confirm_delivery(dnB)
        arB = resB["acceptance_record"]
        frappe.set_user(orig)
        # Khách A cố tải biên bản của B
        frappe.set_user(emailA)
        try:
            portal_document_download("SC Acceptance Record", arB)
            return {"pass": False, "msg": "X khách A tải được biên bản của B"}
        except frappe.PermissionError:
            return {"pass": True, "msg": "OK chặn tải biên bản chéo khách"}
    finally:
        frappe.set_user(orig)
        frappe.db.rollback()


def test_portal_deliveries_own_only():
    orig = frappe.session.user
    try:
        custA, emailA, sfcA, itemA, soA, dnA = _make_delivered_dn("DELA")
        custB, emailB, sfcB, itemB, soB, dnB = _make_delivered_dn("DELB")
        from supplycore.api.portal import portal_deliveries
        frappe.set_user(emailA)
        rows = portal_deliveries()
        frappe.set_user(orig)
        names = {r["name"] for r in rows}
        ok = dnA in names and dnB not in names
        return {"pass": ok, "msg": "OK portal_deliveries chỉ trả DN của A" if ok
                else f"X names={names}"}
    finally:
        frappe.set_user(orig)
        frappe.db.rollback()


def test_portal_contracts_call_stats():
    orig = frappe.session.user
    try:
        cust, email, sfc, item = _seed_customer_with_contract("STATS", 100, 1000)
        so = _make_approved_so(cust, sfc, item, 10)
        from supplycore.api.portal import portal_contracts
        frappe.set_user(email)
        contracts = portal_contracts()
        frappe.set_user(orig)
        c = next((x for x in contracts if x["name"] == sfc), None)
        ok = c and c.get("order_count") == 1 and flt(c.get("total_ordered_qty")) == 10
        return {"pass": bool(ok), "msg": f"OK order_count={c.get('order_count')} ordered={c.get('total_ordered_qty')}" if ok
                else f"X c={c}"}
    finally:
        frappe.set_user(orig)
        frappe.db.rollback()


TESTS = [
    test_confirm_delivery_creates_acceptance,
    test_confirm_delivery_other_customer_denied,
    test_acceptance_records_list_isolation,
    test_acceptance_download_other_denied,
    test_portal_deliveries_own_only,
    test_portal_contracts_call_stats,
]


def run():
    results = []; passed = 0
    for t in TESTS:
        try:
            r = t()
        except Exception as e:
            r = {"pass": False, "msg": f"EXCEPTION: {repr(e)[:180]}"}
        results.append(r)
        if r.get("pass"):
            passed += 1
        print(f"  {'✓' if r.get('pass') else '✗'} {t.__name__}: {r.get('msg')}")
    print(f"mvl_portal_test: {passed}/{len(TESTS)}")
    return {"passed": passed, "total": len(TESTS), "results": results}
