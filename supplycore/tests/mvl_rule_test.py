"""Test GĐ MVL — Workstream D: rule công nợ + chặn tồn lúc gọi hàng.

Khoá các hành vi MỚI:
- BRU-AR-001 dùng hàm chuẩn get_customer_outstanding + hiện "số tối thiểu phải trả".
- Ngưỡng nợ hiệu lực: SC Customer.credit_limit > 0 ưu tiên, else Settings.default_credit_limit (Q3).
- credit_check_enabled=0 → tắt rule.
- BRU-INV-002: portal_order_place chặn khi tồn khả dụng < SL đặt (Q1), bật/tắt qua Settings.

Run: bench --site supplycore-miyano.local execute supplycore.tests.mvl_rule_test.run
"""

import frappe
from frappe.utils import flt, today, add_days, random_string

from supplycore.tests.sc_sales_order_test import (
    _make_customer, _make_item, _make_submitted_sfc, _make_so,
)
from supplycore.tests.portal_api_test import (
    _make_portal_customer, _make_submitted_sfc as _make_portal_sfc,
    _pick_warehouse, _make_batch, _seed_stock, _get_uom,
)


def _set_setting(field, value):
    frappe.db.set_single_value("SupplyCore Settings", field, value)


# ---------------------------------------------------------------------------
# Rule công nợ
# ---------------------------------------------------------------------------

def test_min_payment_shown_when_over_limit():
    """credit_limit=5000, đơn total=10000, dư nợ=0 -> throw BRU-AR-001 kèm số tối
    thiểu phải trả = 0+10000-5000 = 5000."""
    try:
        _set_setting("credit_check_enabled", 1)
        cust = _make_customer("MINPAY", credit_limit=5000)
        item = _make_item("MINPAY")
        sfc = _make_submitted_sfc(cust.name, item.name, 100, 1000)
        so = _make_so(cust.name, sfc.name, [{"item": item.name, "qty": 10}])  # total 10000
        so.insert()
        try:
            so.submit()
            return {"pass": False, "msg": "X không throw dù vượt hạn mức"}
        except frappe.ValidationError as e:
            msg = str(e)
            if "BRU-AR-001" in msg and "5000" in msg:
                return {"pass": True, "msg": "OK throw BRU-AR-001 + hiện min phải trả 5000"}
            return {"pass": False, "msg": f"X thiếu min-pay trong msg: {msg[:160]}"}
    finally:
        frappe.db.rollback()


def test_effective_limit_from_settings_default():
    """Khách credit_limit=0 (vd tự đăng ký) nhưng Settings.default_credit_limit=5000
    -> đơn 10000 vẫn bị chặn (đóng lỗ hổng KH tự đăng ký lách rule)."""
    try:
        _set_setting("credit_check_enabled", 1)
        _set_setting("default_credit_limit", 5000)
        cust = _make_customer("EFFLIM", credit_limit=0)
        item = _make_item("EFFLIM")
        sfc = _make_submitted_sfc(cust.name, item.name, 100, 1000)
        so = _make_so(cust.name, sfc.name, [{"item": item.name, "qty": 10}])
        so.insert()
        try:
            so.submit()
            return {"pass": False, "msg": "X credit_limit=0 lọt dù Settings default=5000"}
        except frappe.ValidationError as e:
            if "BRU-AR-001" in str(e):
                return {"pass": True, "msg": "OK ngưỡng mặc định Settings chặn được KH credit_limit=0"}
            return {"pass": False, "msg": f"X wrong error: {str(e)[:160]}"}
    finally:
        frappe.db.rollback()


def test_credit_check_disabled_allows():
    """credit_check_enabled=0 -> không chặn dù vượt hạn mức."""
    try:
        _set_setting("credit_check_enabled", 0)
        cust = _make_customer("NOCHK", credit_limit=5000)
        item = _make_item("NOCHK")
        sfc = _make_submitted_sfc(cust.name, item.name, 100, 1000)
        so = _make_so(cust.name, sfc.name, [{"item": item.name, "qty": 10}])
        so.insert()
        so.submit()
        ok = flt(so.credit_hold) == 0 and so.docstatus == 1
        return {"pass": ok, "msg": "OK tắt rule -> đơn submit được" if ok
                else f"X credit_hold={so.credit_hold} docstatus={so.docstatus}"}
    finally:
        _set_setting("credit_check_enabled", 1)
        frappe.db.rollback()


def test_outstanding_uses_gl_131():
    """get_customer_outstanding = số dư GL 131 theo party (khách mới = 0)."""
    try:
        from supplycore.utils.receivables import get_customer_outstanding, get_receivable_account
        cust = _make_customer("GLBAL")
        acct = get_receivable_account()
        ok = acct == "131" and flt(get_customer_outstanding(cust.name)) == 0.0
        return {"pass": ok, "msg": f"OK AR account={acct}, outstanding=0" if ok
                else f"X account={acct} outstanding={get_customer_outstanding(cust.name)}"}
    finally:
        frappe.db.rollback()


# ---------------------------------------------------------------------------
# BRU-INV-002 — chặn tồn lúc gọi hàng (portal)
# ---------------------------------------------------------------------------

def test_portal_order_blocked_when_no_stock():
    """Tồn = 0 -> portal_order_place throw BRU-INV-002."""
    orig = frappe.session.user
    try:
        _set_setting("block_order_on_insufficient_stock", 1)
        cust, email, sfc, item = _seed_portal_contract("NOSTK")
        from supplycore.api.portal import portal_order_place
        frappe.set_user(email)
        try:
            portal_order_place(sfc, [{"item": item, "qty": 5}])
            return {"pass": False, "msg": "X đặt được dù tồn = 0"}
        except frappe.ValidationError as e:
            ok = "BRU-INV-002" in str(e)
            return {"pass": ok, "msg": "OK chặn BRU-INV-002 khi hết tồn" if ok
                    else f"X wrong error: {str(e)[:160]}"}
    finally:
        frappe.set_user(orig)
        frappe.db.rollback()


def test_portal_order_ok_when_stock_seeded():
    """Có tồn đủ -> đặt hàng thành công."""
    orig = frappe.session.user
    try:
        _set_setting("block_order_on_insufficient_stock", 1)
        cust, email, sfc, item = _seed_portal_contract("HASSTK")
        _seed_stock(item, _pick_warehouse(),
                    _make_batch(item, add_days(today(), 365)).name, 100)
        from supplycore.api.portal import portal_order_place
        frappe.set_user(email)
        res = portal_order_place(sfc, [{"item": item, "qty": 5}])
        ok = bool(res.get("order"))
        return {"pass": ok, "msg": f"OK đặt được order {res.get('order')}" if ok
                else f"X không tạo được order: {res}"}
    finally:
        frappe.set_user(orig)
        frappe.db.rollback()


def test_stock_block_disabled_allows_order():
    """block_order_on_insufficient_stock=0 -> đặt được dù hết tồn (chỉ chặn ở DN)."""
    orig = frappe.session.user
    try:
        _set_setting("block_order_on_insufficient_stock", 0)
        cust, email, sfc, item = _seed_portal_contract("STKOFF")
        from supplycore.api.portal import portal_order_place
        frappe.set_user(email)
        res = portal_order_place(sfc, [{"item": item, "qty": 5}])
        ok = bool(res.get("order"))
        return {"pass": ok, "msg": "OK tắt chặn tồn -> đặt được" if ok else f"X {res}"}
    finally:
        frappe.set_user(orig)
        _set_setting("block_order_on_insufficient_stock", 1)
        frappe.db.rollback()


def _seed_portal_contract(suffix):
    """Tạo portal customer + SFC (item has_batch_no=1), trả (cust, email, sfc, item)."""
    cust, email = _make_portal_customer(suffix)
    item = _make_item(suffix)
    sfc = _make_portal_sfc(cust, item.name, 100, 1000)
    return cust, email, sfc, item


TESTS = [
    test_min_payment_shown_when_over_limit,
    test_effective_limit_from_settings_default,
    test_credit_check_disabled_allows,
    test_outstanding_uses_gl_131,
    test_portal_order_blocked_when_no_stock,
    test_portal_order_ok_when_stock_seeded,
    test_stock_block_disabled_allows_order,
]


def run():
    results = []
    passed = 0
    for t in TESTS:
        try:
            r = t()
        except Exception as e:
            r = {"pass": False, "msg": f"EXCEPTION: {repr(e)[:180]}"}
        results.append(r)
        if r.get("pass"):
            passed += 1
        print(f"  {'✓' if r.get('pass') else '✗'} {t.__name__}: {r.get('msg')}")
    print(f"mvl_rule_test: {passed}/{len(TESTS)}")
    return {"passed": passed, "total": len(TESTS), "results": results}
