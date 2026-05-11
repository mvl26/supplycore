"""Test UC-28 — Đối soát kho + investigation.

Run individual: bench --site supplycore execute supplycore.tests.uc28_test.test_<name>
Run all:        bench --site supplycore execute supplycore.tests.uc28_test.run
"""

import frappe
from frappe.utils import today, random_string, flt


def _pick_warehouse() -> str:
    rows = frappe.get_all("SC Warehouse", filters={"is_group": 0, "disabled": 0},
                           pluck="name", order_by="name", limit=1)
    return rows[0] if rows else None


def _get_uom() -> str:
    return frappe.db.get_value("SC UOM", {}, "name")


def _make_item(suffix: str):
    item = frappe.new_doc("SC Item")
    item.item_code = f"UC28-{suffix}-{random_string(5)}"
    item.item_name = f"UC-28 test {suffix}"
    item.uom = _get_uom()
    item.is_stock_item = 1
    item.flags.ignore_permissions = True
    item.insert()
    return item


def _seed_stock(item, warehouse, qty, rate=1000):
    from supplycore.supplycore.doctype.sc_stock_ledger_entry.sc_stock_ledger_entry import SCStockLedgerEntry
    return SCStockLedgerEntry.post(
        item=item, warehouse=warehouse, qty_change=flt(qty), valuation_rate=flt(rate),
        voucher_type="Manual", voucher_no=f"UC28-{random_string(6)}",
        posting_date=today(),
    )


def _make_sr(warehouse, items: list):
    sr = frappe.new_doc("SC Stock Reconciliation")
    sr.posting_date = today()
    sr.warehouse = warehouse
    for it in items:
        sr.append("items", {
            "item": it["item"], "uom": _get_uom(),
            "actual_qty": flt(it["actual_qty"]),
            "valuation_rate": flt(it.get("valuation_rate", 1000)),
            "reason": it.get("reason", "Counting Error"),
        })
    sr.flags.ignore_permissions = True
    return sr


# ---------- Tests ----------

def test_sr_small_variance_no_investigation():
    """Δ value < 10tr → requires_investigation=0."""
    wh = _pick_warehouse()
    item = _make_item("SMALL")
    _seed_stock(item.name, wh, 100)
    sr = _make_sr(wh, [{"item": item.name, "actual_qty": 105,
                         "valuation_rate": 1000}])  # Δ value = 5000
    try:
        sr.insert()
        ok = (sr.requires_investigation == 0)
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": "OK no investigation needed"}
        return {"pass": False, "msg": f"X requires={sr.requires_investigation}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_sr_large_variance_flag_investigation():
    """Δ value > 10tr → requires_investigation=1."""
    wh = _pick_warehouse()
    item = _make_item("LARGE")
    _seed_stock(item.name, wh, 100)
    sr = _make_sr(wh, [{"item": item.name, "actual_qty": 1100,
                         "valuation_rate": 50_000}])  # Δ value = 50tr > 10tr
    try:
        sr.insert()
        ok = (sr.requires_investigation == 1)
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": "OK investigation flagged"}
        return {"pass": False, "msg": f"X requires={sr.requires_investigation} value={sr.total_difference_value}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_sr_large_variance_submit_blocked_without_notes():
    """requires_investigation + no notes → SC-E-SR-INVESTIGATION-REQUIRED."""
    wh = _pick_warehouse()
    item = _make_item("BLKINV")
    _seed_stock(item.name, wh, 100)
    sr = _make_sr(wh, [{"item": item.name, "actual_qty": 1100,
                         "valuation_rate": 50_000}])
    try:
        sr.insert()
        sr.submit()
        frappe.db.rollback()
        return {"pass": False, "msg": "X submit không bị block"}
    except frappe.ValidationError as e:
        msg = str(e)
        frappe.db.rollback()
        if "SC-E-SR-INVESTIGATION-REQUIRED" in msg:
            return {"pass": True, "msg": f"OK: {msg[:120]}"}
        return {"pass": False, "msg": f"Wrong error: {msg[:120]}"}


def test_sr_large_variance_submit_with_notes_ok():
    """requires_investigation + notes → submit OK."""
    wh = _pick_warehouse()
    item = _make_item("OKINV")
    _seed_stock(item.name, wh, 100)
    sr = _make_sr(wh, [{"item": item.name, "actual_qty": 1100,
                         "valuation_rate": 50_000}])
    sr.investigation_notes = "Đã làm việc với Bảo vệ, phát hiện hàng thừa do nhập trùng"
    try:
        sr.insert()
        sr.submit()
        sr.reload()
        ok = (sr.docstatus == 1 and sr.investigated_by)
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK investigated_by={sr.investigated_by}"}
        return {"pass": False, "msg": f"X doc={sr.docstatus} by={sr.investigated_by}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_sr_threshold_from_settings():
    """Set threshold = 5tr → Δ 7tr triggers."""
    original = frappe.db.get_single_value("SupplyCore Settings", "large_variance_threshold")
    frappe.db.set_single_value("SupplyCore Settings", "large_variance_threshold", 5_000_000)
    try:
        wh = _pick_warehouse()
        item = _make_item("THR")
        _seed_stock(item.name, wh, 100)
        sr = _make_sr(wh, [{"item": item.name, "actual_qty": 170,
                             "valuation_rate": 100_000}])  # Δ value = 7tr
        sr.insert()
        ok = (sr.requires_investigation == 1)
        frappe.db.rollback()
        # Restore
        frappe.db.set_single_value("SupplyCore Settings",
                                     "large_variance_threshold", original or 10_000_000)
        if ok:
            return {"pass": True, "msg": "OK threshold respected"}
        return {"pass": False, "msg": f"X requires={sr.requires_investigation}"}
    except Exception as e:
        frappe.db.set_single_value("SupplyCore Settings",
                                     "large_variance_threshold", original or 10_000_000)
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_get_reconciliation_minutes_data():
    """Method trả dict đủ field cho biên bản."""
    wh = _pick_warehouse()
    item = _make_item("MIN")
    _seed_stock(item.name, wh, 100)
    sr = _make_sr(wh, [{"item": item.name, "actual_qty": 110}])
    try:
        sr.insert()
        data = sr.get_reconciliation_minutes_data()
        required = {"name", "warehouse", "items", "total_difference_value",
                    "signatures", "url"}
        frappe.db.rollback()
        if required.issubset(set(data.keys())):
            return {"pass": True, "msg": "OK minutes data complete"}
        return {"pass": False, "msg": f"X missing: {required - set(data.keys())}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_sr_excess_item_supported():
    """Item mới với actual=10, system=0 → diff=10 (hàng thừa)."""
    wh = _pick_warehouse()
    item = _make_item("EXC")  # no SLE seeded
    sr = _make_sr(wh, [{"item": item.name, "actual_qty": 10,
                         "valuation_rate": 1000}])
    try:
        sr.insert()
        row = sr.items[0]
        ok = (abs(flt(row.system_qty) - 0) < 0.01
              and abs(flt(row.difference) - 10) < 0.01)
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": "OK excess item recorded (system=0, actual=10)"}
        return {"pass": False, "msg": f"X system={row.system_qty} diff={row.difference}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_sr_minutes_includes_signatures():
    """Minutes có signatures dict."""
    wh = _pick_warehouse()
    item = _make_item("SIG")
    _seed_stock(item.name, wh, 50)
    sr = _make_sr(wh, [{"item": item.name, "actual_qty": 55}])
    try:
        sr.insert()
        data = sr.get_reconciliation_minutes_data()
        sigs = data.get("signatures", {})
        frappe.db.rollback()
        if "storekeeper" in sigs and "accountant" in sigs and "manager" in sigs:
            return {"pass": True, "msg": "OK 3 signature placeholders"}
        return {"pass": False, "msg": f"X sigs={sigs}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def run():
    tests = [
        test_sr_small_variance_no_investigation,
        test_sr_large_variance_flag_investigation,
        test_sr_large_variance_submit_blocked_without_notes,
        test_sr_large_variance_submit_with_notes_ok,
        test_sr_threshold_from_settings,
        test_get_reconciliation_minutes_data,
        test_sr_excess_item_supported,
        test_sr_minutes_includes_signatures,
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
