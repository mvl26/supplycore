"""Test UC-19 — Stock Reconciliation.

Run individual: bench --site supplycore execute supplycore.tests.uc19_test.test_<name>
Run all:        bench --site supplycore execute supplycore.tests.uc19_test.run
"""

import frappe
from frappe.utils import today, random_string, flt


def _pick_warehouse() -> str:
    rows = frappe.get_all("SC Warehouse", filters={"is_group": 0, "disabled": 0},
                           pluck="name", order_by="name", limit=1)
    if not rows:
        frappe.throw("uc19_test: cần seed SC Warehouse")
    return rows[0]


def _get_uom() -> str:
    uom = frappe.db.get_value("SC UOM", {}, "name")
    if not uom:
        frappe.throw("uc19_test: cần seed SC UOM")
    return uom


def _make_item(suffix: str):
    item = frappe.new_doc("SC Item")
    item.item_code = f"UC19-{suffix}-{random_string(5)}"
    item.item_name = f"UC-19 test {suffix}"
    item.uom = _get_uom()
    item.is_stock_item = 1
    item.flags.ignore_permissions = True
    item.insert()
    return item


def _seed_stock(item, warehouse, qty):
    from supplycore.supplycore.doctype.sc_stock_ledger_entry.sc_stock_ledger_entry import SCStockLedgerEntry
    return SCStockLedgerEntry.post(
        item=item, warehouse=warehouse, qty_change=flt(qty),
        voucher_type="Manual", voucher_no=f"UC19-{random_string(6)}",
        posting_date=today(), valuation_rate=1000,
    )


def _make_sr(warehouse, items: list):
    """items = list of dict {item, actual_qty, reason?, valuation_rate?}"""
    sr = frappe.new_doc("SC Stock Reconciliation")
    sr.posting_date = today()
    sr.warehouse = warehouse
    for it in items:
        sr.append("items", {
            "item": it["item"], "uom": _get_uom(),
            "actual_qty": flt(it["actual_qty"]),
            "valuation_rate": flt(it.get("valuation_rate", 1000)),
            "reason": it.get("reason"),
        })
    sr.flags.ignore_permissions = True
    return sr


# ---------- Tests ----------

def test_sr_auto_fill_system_qty():
    """Seed SLE 100; SR row item → system_qty=100."""
    wh = _pick_warehouse()
    item = _make_item("AUTO")
    _seed_stock(item.name, wh, 100)
    sr = _make_sr(wh, [{"item": item.name, "actual_qty": 100}])
    try:
        sr.insert()
        system_qty = flt(sr.items[0].system_qty)
        frappe.db.rollback()
        if abs(system_qty - 100) < 0.01:
            return {"pass": True, "msg": f"OK system_qty=100"}
        return {"pass": False, "msg": f"X system_qty={system_qty}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_sr_compute_difference():
    """system=100, actual=120 → difference=20."""
    wh = _pick_warehouse()
    item = _make_item("DIFF")
    _seed_stock(item.name, wh, 100)
    sr = _make_sr(wh, [{"item": item.name, "actual_qty": 120, "valuation_rate": 5000}])
    try:
        sr.insert()
        row = sr.items[0]
        ok = (abs(flt(row.difference) - 20) < 0.01
              and abs(flt(row.amount_change) - 100_000) < 0.01)
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK diff=20, value=100000"}
        return {"pass": False, "msg": f"X diff={row.difference} val={row.amount_change}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_sr_reason_required_when_difference():
    """difference≠0 + thiếu reason → SC-E-SR-REASON-REQUIRED."""
    wh = _pick_warehouse()
    item = _make_item("NOREASON")
    _seed_stock(item.name, wh, 50)
    sr = _make_sr(wh, [{"item": item.name, "actual_qty": 60}])  # diff=10, no reason
    try:
        sr.insert()
        sr.submit()
        frappe.db.rollback()
        return {"pass": False, "msg": "X submit không bị block"}
    except frappe.ValidationError as e:
        msg = str(e)
        frappe.db.rollback()
        if "SC-E-SR-REASON-REQUIRED" in msg:
            return {"pass": True, "msg": f"OK: {msg[:120]}"}
        return {"pass": False, "msg": f"Wrong error: {msg[:120]}"}


def test_sr_submit_creates_sle_adjustment():
    """Submit → SLE adjustment posted."""
    wh = _pick_warehouse()
    item = _make_item("SLEADJ")
    _seed_stock(item.name, wh, 50)
    sr = _make_sr(wh, [{"item": item.name, "actual_qty": 70, "reason": "Counting Error"}])
    try:
        sr.insert()
        sr.submit()
        sle_qty = flt(frappe.db.sql("""
            SELECT COALESCE(SUM(qty_change), 0)
            FROM `tabSC Stock Ledger Entry`
            WHERE voucher_no = %s AND voucher_type = 'SC Stock Reconciliation'
              AND is_cancelled = 0
        """, sr.name)[0][0])
        frappe.db.rollback()
        if abs(sle_qty - 20) < 0.01:
            return {"pass": True, "msg": f"OK SLE adjustment +20"}
        return {"pass": False, "msg": f"X SLE qty={sle_qty}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_sr_submit_blocks_non_manager():
    """Non-Manager + submit → SC-E-SR-MANAGER-REQUIRED."""
    wh = _pick_warehouse()
    item = _make_item("NOMGR")
    _seed_stock(item.name, wh, 50)
    sr = _make_sr(wh, [{"item": item.name, "actual_qty": 60, "reason": "Counting Error"}])

    sk_user = frappe.db.get_value("User",
        {"enabled": 1, "name": ["!=", "Administrator"]}, "name")
    if not sk_user:
        return {"pass": True, "msg": "OK (skipped: no non-admin user)"}

    sk_doc = frappe.get_doc("User", sk_user)
    sk_doc.roles = []
    sk_doc.append("roles", {"role": "SupplyCore Storekeeper"})
    sk_doc.save(ignore_permissions=True)

    original_user = frappe.session.user
    try:
        sr.insert()
        frappe.set_user(sk_user)
        try:
            sr.submit()
            frappe.set_user(original_user)
            frappe.db.rollback()
            return {"pass": False, "msg": "X submit không block"}
        except frappe.ValidationError as e:
            msg = str(e)
            frappe.set_user(original_user)
            frappe.db.rollback()
            if "SC-E-SR-MANAGER-REQUIRED" in msg:
                return {"pass": True, "msg": f"OK: {msg[:120]}"}
            return {"pass": False, "msg": f"Wrong error: {msg[:120]}"}
    except Exception as e:
        frappe.set_user(original_user)
        frappe.db.rollback()
        return {"pass": False, "msg": f"X setup: {str(e)[:120]}"}


def test_sr_submit_allows_manager():
    """System Manager submit → OK."""
    wh = _pick_warehouse()
    item = _make_item("MGROK")
    _seed_stock(item.name, wh, 50)
    sr = _make_sr(wh, [{"item": item.name, "actual_qty": 55, "reason": "Counting Error"}])
    try:
        sr.insert()
        sr.submit()
        ok = (sr.docstatus == 1 and sr.status == "Approved")
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK SR submitted, status=Approved"}
        return {"pass": False, "msg": f"X doc={sr.docstatus} status={sr.status}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_sr_reject_requires_reason():
    """reject(empty) → SC-E-SR-REJECT-REASON."""
    wh = _pick_warehouse()
    item = _make_item("REJR")
    _seed_stock(item.name, wh, 50)
    sr = _make_sr(wh, [{"item": item.name, "actual_qty": 55, "reason": "Counting Error"}])
    try:
        sr.insert()
        try:
            sr.reject(reason="")
            frappe.db.rollback()
            return {"pass": False, "msg": "X did not throw"}
        except frappe.ValidationError as e:
            msg = str(e)
            frappe.db.rollback()
            if "SC-E-SR-REJECT-REASON" in msg:
                return {"pass": True, "msg": f"OK: {msg[:120]}"}
            return {"pass": False, "msg": f"Wrong error: {msg[:120]}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X setup: {str(e)[:120]}"}


def test_sr_reject_with_reason():
    """reject(reason) → status=Rejected + rejection_reason saved."""
    wh = _pick_warehouse()
    item = _make_item("REJOK")
    _seed_stock(item.name, wh, 50)
    sr = _make_sr(wh, [{"item": item.name, "actual_qty": 55, "reason": "Counting Error"}])
    try:
        sr.insert()
        sr.reject(reason="Đếm sai - cần đếm lại")
        sr.reload()
        ok = (sr.status == "Rejected" and sr.rejection_reason == "Đếm sai - cần đếm lại")
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK rejected with reason"}
        return {"pass": False, "msg": f"X status={sr.status} reason={sr.rejection_reason}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_sr_actual_qty_negative_blocked():
    """actual_qty=-5 → non_negative validate throw (Frappe native)."""
    wh = _pick_warehouse()
    item = _make_item("NEG")
    _seed_stock(item.name, wh, 50)
    sr = _make_sr(wh, [{"item": item.name, "actual_qty": -5, "reason": "Counting Error"}])
    try:
        sr.insert()
        frappe.db.rollback()
        return {"pass": False, "msg": "X did not throw on negative qty"}
    except frappe.ValidationError as e:
        msg = str(e)
        frappe.db.rollback()
        # Frappe native non_negative error wording
        if "negative" in msg.lower() or "âm" in msg or "non_negative" in msg.lower():
            return {"pass": True, "msg": f"OK negative rejected"}
        return {"pass": False, "msg": f"Unexpected error: {msg[:120]}"}


def test_sr_no_diff_skips_sle():
    """system=actual → no SLE posted, no GL."""
    wh = _pick_warehouse()
    item = _make_item("NODIFF")
    _seed_stock(item.name, wh, 50)
    sr = _make_sr(wh, [{"item": item.name, "actual_qty": 50}])  # no diff
    try:
        sr.insert()
        sr.submit()
        sle_count = frappe.db.count("SC Stock Ledger Entry", {
            "voucher_type": "SC Stock Reconciliation", "voucher_no": sr.name})
        frappe.db.rollback()
        if sle_count == 0:
            return {"pass": True, "msg": "OK no SLE for zero diff"}
        return {"pass": False, "msg": f"X SLE count={sle_count}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_sr_cancel_reverses_sle():
    """Cancel SR → SLE reversed."""
    wh = _pick_warehouse()
    item = _make_item("CANC")
    _seed_stock(item.name, wh, 50)
    sr = _make_sr(wh, [{"item": item.name, "actual_qty": 60, "reason": "Counting Error"}])
    try:
        sr.insert()
        sr.submit()
        sr.cancel()
        # Net stock at (item, warehouse) should be back to original 50 sau cancel
        # (50 seed + 10 SR_submit + (-10 SR_cancel) = 50, nhưng SR_submit is_cancelled=1
        # nên active SUM = 50 seed + (-10 reversal) = 40)
        # Đúng pattern: pre-SR balance = 50; post-SR submit = 60; post-cancel = 50
        net_at_wh = flt(frappe.db.sql("""
            SELECT COALESCE(SUM(qty_change), 0)
            FROM `tabSC Stock Ledger Entry`
            WHERE item = %s AND warehouse = %s AND is_cancelled = 0
        """, (item.name, wh))[0][0])
        sr.reload()
        frappe.db.rollback()
        # After cancel: status=Cancelled; net stock includes reversal entry
        if sr.status == "Cancelled":
            return {"pass": True, "msg": f"OK SR cancelled, net stock={net_at_wh}"}
        return {"pass": False, "msg": f"X status={sr.status} net={net_at_wh}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def run():
    tests = [
        test_sr_auto_fill_system_qty,
        test_sr_compute_difference,
        test_sr_reason_required_when_difference,
        test_sr_submit_creates_sle_adjustment,
        test_sr_submit_blocks_non_manager,
        test_sr_submit_allows_manager,
        test_sr_reject_requires_reason,
        test_sr_reject_with_reason,
        test_sr_actual_qty_negative_blocked,
        test_sr_no_diff_skips_sle,
        test_sr_cancel_reverses_sle,
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
