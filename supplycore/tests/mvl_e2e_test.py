"""Test GĐ MVL — E2E chuỗi bán hàng đầy đủ (Workstream F).

Kịch bản DoD: HĐ khung -> KH portal gọi hàng -> duyệt -> giao -> KH xác nhận
nhận hàng -> hoá đơn -> thu MỘT PHẦN -> gọi tiếp bị CHẶN vì nợ (hiện min phải
trả) -> thu ĐỦ -> gọi tiếp được.

Chạy dưới nhiều user (nhân viên nội bộ + portal KH) như luồng thật.
Run: bench --site supplycore-miyano.local execute supplycore.tests.mvl_e2e_test.run
"""

import frappe
from frappe.utils import flt, today, add_days

from supplycore.tests.portal_api_test import (
    _seed_customer_with_contract, _pick_warehouse, _make_batch, _seed_stock, _get_uom,
)


def _set(field, value):
    frappe.db.set_single_value("SupplyCore Settings", field, value)


def test_full_o2c_with_debt_gate():
    orig = frappe.session.user
    try:
        _set("credit_check_enabled", 1)
        _set("block_order_on_insufficient_stock", 1)
        _set("default_credit_limit", 0)

        # --- Setup: khách hạn mức 10000, HĐ 100 cái x 1000, tồn 500 ---
        cust, email, sfc, item = _seed_customer_with_contract("E2E", contract_qty=100, unit_price=1000)
        frappe.db.set_value("SC Customer", cust, "credit_limit", 10000)
        wh = _pick_warehouse()
        _seed_stock(item, wh, _make_batch(item, add_days(today(), 300)).name, 500, rate=1000)

        from supplycore.api.portal import portal_order_place, portal_confirm_delivery
        from supplycore.api import sales

        # --- (1) KH gọi hàng qty=10 (total 10000, dư nợ 0 -> ok) ---
        frappe.set_user(email)
        r1 = portal_order_place(sfc, [{"item": item, "qty": 10}])
        so1 = r1["order"]
        frappe.set_user(orig)

        # --- (2) Nội bộ duyệt -> tạo phiếu giao ---
        sales.sales_order_approve(so1)
        dn1 = sales.make_delivery(so1, from_warehouse=wh)["name"]

        # --- (3) KH xác nhận nhận hàng -> biên bản ---
        frappe.set_user(email)
        portal_confirm_delivery(dn1)
        frappe.set_user(orig)

        # --- (4) Xuất hoá đơn -> dư nợ 10000 ---
        si = sales.sales_invoice_create(dn1, tax_rate=0)["name"]
        from supplycore.utils.receivables import get_customer_outstanding
        out1 = get_customer_outstanding(cust)
        if flt(out1) != 10000:
            return {"pass": False, "msg": f"X dư nợ sau HĐ = {out1}, kỳ vọng 10000"}

        # --- (5) Gọi tiếp qty=1 -> CHẶN vì nợ (10000+1000 > 10000) ---
        frappe.set_user(email)
        try:
            portal_order_place(sfc, [{"item": item, "qty": 1}])
            frappe.set_user(orig)
            return {"pass": False, "msg": "X gọi tiếp không bị chặn dù vượt hạn mức"}
        except frappe.ValidationError as e:
            if "BRU-AR-001" not in str(e):
                frappe.set_user(orig)
                return {"pass": False, "msg": f"X sai lỗi khi vượt nợ: {str(e)[:120]}"}
        frappe.set_user(orig)

        # --- (6) Thu MỘT PHẦN 4000 -> dư nợ 6000 ---
        sales.receipt_collect(si, 4000)
        out2 = get_customer_outstanding(cust)
        if flt(out2) != 6000:
            return {"pass": False, "msg": f"X dư nợ sau thu một phần = {out2}, kỳ vọng 6000"}

        # --- (7) Gọi qty=5 (6000+5000=11000>10000) -> vẫn CHẶN ---
        frappe.set_user(email)
        try:
            portal_order_place(sfc, [{"item": item, "qty": 5}])
            frappe.set_user(orig)
            return {"pass": False, "msg": "X vẫn còn nợ nhưng không chặn"}
        except frappe.ValidationError:
            pass
        frappe.set_user(orig)

        # --- (8) Thu ĐỦ 6000 -> dư nợ 0 ---
        sales.receipt_collect(si, 6000)
        out3 = get_customer_outstanding(cust)
        if flt(out3) != 0:
            return {"pass": False, "msg": f"X dư nợ sau thu đủ = {out3}, kỳ vọng 0"}

        # --- (9) Gọi tiếp qty=5 -> OK (0+5000<10000) ---
        frappe.set_user(email)
        r9 = portal_order_place(sfc, [{"item": item, "qty": 5}])
        frappe.set_user(orig)
        if not r9.get("order"):
            return {"pass": False, "msg": "X sau thu đủ vẫn không gọi được"}

        return {"pass": True, "msg": f"OK chuỗi O2C: HĐ->giao->nghiệm thu->HĐ->thu 1 phần(chặn)->thu đủ->gọi tiếp {r9['order']}"}
    finally:
        frappe.set_user(orig)
        _set("credit_check_enabled", 1)
        frappe.db.rollback()


def test_quota_then_stock_block():
    """Sau khi hết định mức -> chặn BRU-SO-001; đơn vượt tồn -> chặn BRU-INV-002."""
    orig = frappe.session.user
    try:
        _set("block_order_on_insufficient_stock", 1)
        _set("credit_check_enabled", 0)  # tách khỏi rule nợ để cô lập 2 rule này
        cust, email, sfc, item = _seed_customer_with_contract("QS", contract_qty=20, unit_price=1000)
        wh = _pick_warehouse()
        _seed_stock(item, wh, _make_batch(item, add_days(today(), 300)).name, 15, rate=1000)

        from supplycore.api.portal import portal_order_place
        frappe.set_user(email)

        # Vượt định mức: đặt 25 > contract 20 -> BRU-SO-001 (trước cả check tồn)
        try:
            portal_order_place(sfc, [{"item": item, "qty": 25}])
            frappe.set_user(orig)
            return {"pass": False, "msg": "X vượt định mức không chặn"}
        except frappe.ValidationError as e:
            if "BRU-SO-001" not in str(e):
                frappe.set_user(orig)
                return {"pass": False, "msg": f"X sai lỗi vượt định mức: {str(e)[:120]}"}

        # Trong định mức (18<=20) nhưng vượt tồn (15) -> BRU-INV-002
        try:
            portal_order_place(sfc, [{"item": item, "qty": 18}])
            frappe.set_user(orig)
            return {"pass": False, "msg": "X vượt tồn không chặn"}
        except frappe.ValidationError as e:
            frappe.set_user(orig)
            if "BRU-INV-002" not in str(e):
                return {"pass": False, "msg": f"X sai lỗi vượt tồn: {str(e)[:120]}"}
            return {"pass": True, "msg": "OK vượt định mức->BRU-SO-001, vượt tồn->BRU-INV-002"}
    finally:
        frappe.set_user(orig)
        _set("credit_check_enabled", 1)
        frappe.db.rollback()


TESTS = [test_full_o2c_with_debt_gate, test_quota_then_stock_block]


def run():
    results = []; passed = 0
    for t in TESTS:
        try:
            r = t()
        except Exception as e:
            r = {"pass": False, "msg": f"EXCEPTION: {repr(e)[:200]}"}
        results.append(r)
        if r.get("pass"):
            passed += 1
        print(f"  {'✓' if r.get('pass') else '✗'} {t.__name__}: {r.get('msg')}")
    print(f"mvl_e2e_test: {passed}/{len(TESTS)}")
    return {"passed": passed, "total": len(TESTS), "results": results}
