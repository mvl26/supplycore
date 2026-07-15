"""Test UC-14 — Stock balance lookup theo vị trí.

Run individual: bench --site supplycore execute supplycore.tests.uc14_test.test_<name>
Run all:        bench --site supplycore execute supplycore.tests.uc14_test.run
"""

import frappe
from frappe.utils import today, add_days, random_string, flt


def _pick_warehouse() -> str:
    rows = frappe.get_all("SC Warehouse", filters={"is_group": 0, "disabled": 0},
                           pluck="name", order_by="name", limit=1)
    if not rows:
        frappe.throw("uc14_test: cần seed SC Warehouse")
    return rows[0]


def _get_uom() -> str:
    uom = frappe.db.get_value("SC UOM", {}, "name")
    if not uom:
        frappe.throw("uc14_test: cần seed SC UOM")
    return uom


def _make_item(suffix: str, has_batch: int = 0, item_group: str = None):
    item = frappe.new_doc("SC Item")
    item.item_code = f"UC14-{suffix}-{random_string(5)}"
    item.item_name = f"UC-14 test {suffix}"
    item.uom = _get_uom()
    item.is_stock_item = 1
    item.has_batch_no = has_batch
    if item_group:
        item.item_group = item_group
    item.flags.ignore_permissions = True
    item.insert()
    return item


def _make_bin(suffix: str, warehouse: str = None):
    b = frappe.new_doc("Bin Location")
    b.warehouse = warehouse or _pick_warehouse()
    b.bin_code = f"UC14-BIN-{suffix}-{random_string(4)}"
    b.capacity_qty = 1000
    b.capacity_uom = _get_uom()
    b.enabled = 1
    b.flags.ignore_permissions = True
    b.insert()
    return b


def _make_batch(item: str, suffix: str, expiry_offset_days: int = 365):
    batch = frappe.new_doc("SC Batch")
    batch.batch_id = f"UC14-BAT-{suffix}-{random_string(4)}"
    batch.item = item
    batch.expiry_date = add_days(today(), expiry_offset_days)
    batch.manufacturing_date = today()
    batch.qc_status = "Accepted"
    batch.flags.ignore_permissions = True
    batch.flags.ignore_short_expiry = 1  # UC-15 — skip short expiry block in test
    batch.insert()
    return batch


def _putaway(item, qty, uom, warehouse, bin_location, batch=None, rate=10_000, days_offset=0):
    """Direct SLE insertion với posting_date override để test as_of_date."""
    from supplycore.supplycore.doctype.sc_stock_ledger_entry.sc_stock_ledger_entry import SCStockLedgerEntry
    return SCStockLedgerEntry.post(
        item=item, warehouse=warehouse, qty_change=flt(qty),
        valuation_rate=flt(rate), batch=batch, bin_location=bin_location,
        voucher_type="Manual",
        voucher_no=f"UC14-PUT-{random_string(6)}",
        posting_date=add_days(today(), days_offset),
    )


def _picking(item, qty, warehouse, bin_location, batch=None):
    from supplycore.supplycore.doctype.sc_stock_ledger_entry.sc_stock_ledger_entry import SCStockLedgerEntry
    return SCStockLedgerEntry.post(
        item=item, warehouse=warehouse, qty_change=-flt(qty),
        batch=batch, bin_location=bin_location,
        voucher_type="Manual",
        voucher_no=f"UC14-PICK-{random_string(6)}",
        posting_date=today(),
    )


# ---------- Tests ----------

def test_get_stock_balance_basic():
    """Putaway → balance returns qty + value + flags."""
    from supplycore.m4_wms.api.quick_stock import get_stock_balance

    wh = _pick_warehouse()
    item = _make_item("BAL")
    b = _make_bin("BAL", warehouse=wh)
    _putaway(item.name, 50, item.uom, wh, b.name, rate=20_000)
    try:
        rows = get_stock_balance(item=item.name)
        frappe.db.rollback()
        matching = [r for r in rows if r["item"] == item.name and r["bin_location"] == b.name]
        if matching and abs(flt(matching[0]["qty"]) - 50) < 0.01 \
           and abs(flt(matching[0]["value"]) - 50 * 20_000) < 1:
            return {"pass": True, "msg": f"OK qty=50 value={matching[0]['value']}"}
        return {"pass": False, "msg": f"X rows={rows[:3]}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_get_stock_balance_filter_item_group():
    """Filter item_group → chỉ trả items thuộc group."""
    from supplycore.m4_wms.api.quick_stock import get_stock_balance

    group = frappe.db.get_value("SC Item Group", {}, "name")
    if not group:
        return {"pass": False, "msg": "X cần seed SC Item Group"}
    wh = _pick_warehouse()
    item_in = _make_item("GIN", item_group=group)
    item_out = _make_item("GOUT")  # no group
    b = _make_bin("GRP", warehouse=wh)
    _putaway(item_in.name, 10, item_in.uom, wh, b.name)
    _putaway(item_out.name, 20, item_out.uom, wh, b.name)
    try:
        rows = get_stock_balance(item_group=group)
        frappe.db.rollback()
        in_present = any(r["item"] == item_in.name for r in rows)
        out_present = any(r["item"] == item_out.name for r in rows)
        if in_present and not out_present:
            return {"pass": True, "msg": f"OK filter item_group correct"}
        return {"pass": False, "msg": f"X in={in_present} out={out_present}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_get_stock_balance_filter_expiry_range():
    """Filter expiry_from/to → chỉ batches trong range."""
    from supplycore.m4_wms.api.quick_stock import get_stock_balance

    wh = _pick_warehouse()
    item = _make_item("EXP", has_batch=1)
    bat_near = _make_batch(item.name, "NEAR", expiry_offset_days=30)
    bat_far = _make_batch(item.name, "FAR", expiry_offset_days=365)
    b = _make_bin("EXP", warehouse=wh)
    _putaway(item.name, 10, item.uom, wh, b.name, batch=bat_near.name)
    _putaway(item.name, 20, item.uom, wh, b.name, batch=bat_far.name)
    try:
        rows = get_stock_balance(item=item.name,
                                  expiry_from=add_days(today(), 0),
                                  expiry_to=add_days(today(), 60))
        frappe.db.rollback()
        near = any(r["batch"] == bat_near.name for r in rows)
        far = any(r["batch"] == bat_far.name for r in rows)
        if near and not far:
            return {"pass": True, "msg": f"OK expiry filter — near only"}
        return {"pass": False, "msg": f"X near={near} far={far}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_get_stock_balance_as_of_date():
    """as_of_date trong quá khứ → exclude SLE sau."""
    from supplycore.m4_wms.api.quick_stock import get_stock_balance

    wh = _pick_warehouse()
    item = _make_item("ASOF")
    b = _make_bin("ASOF", warehouse=wh)
    _putaway(item.name, 100, item.uom, wh, b.name, days_offset=-10)  # 10 days ago
    _putaway(item.name, 50, item.uom, wh, b.name, days_offset=0)     # today
    try:
        rows = get_stock_balance(item=item.name,
                                  as_of_date=add_days(today(), -5))
        frappe.db.rollback()
        matching = [r for r in rows if r["item"] == item.name and r["bin_location"] == b.name]
        # As of 5 days ago: only the -10 day putaway should count = 100
        if matching and abs(flt(matching[0]["qty"]) - 100) < 0.01:
            return {"pass": True, "msg": f"OK as_of qty=100 (excluded today's putaway)"}
        return {"pass": False, "msg": f"X qty={matching[0]['qty'] if matching else 'none'}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_get_stock_balance_negative_flag():
    """Net -qty → row.is_negative=1."""
    from supplycore.m4_wms.api.quick_stock import get_stock_balance

    wh = _pick_warehouse()
    item = _make_item("NEG")
    b = _make_bin("NEG", warehouse=wh)
    _putaway(item.name, 10, item.uom, wh, b.name)
    _picking(item.name, 30, wh, b.name)  # net = -20
    try:
        rows = get_stock_balance(item=item.name)
        frappe.db.rollback()
        matching = [r for r in rows if r["item"] == item.name and r["bin_location"] == b.name]
        if matching and matching[0]["is_negative"] == 1 and flt(matching[0]["qty"]) < 0:
            return {"pass": True, "msg": f"OK is_negative=1 qty={matching[0]['qty']}"}
        return {"pass": False, "msg": f"X matching={matching}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_get_bin_history_recent():
    """Putaway + Picking → get_bin_history trả 2 entries, newest first."""
    from supplycore.m4_wms.api.quick_stock import get_bin_history

    wh = _pick_warehouse()
    item = _make_item("HIST")
    b = _make_bin("HIST", warehouse=wh)
    _putaway(item.name, 20, item.uom, wh, b.name)
    _picking(item.name, 5, wh, b.name)
    try:
        history = get_bin_history(b.name, limit=10)
        frappe.db.rollback()
        if len(history) >= 2:
            return {"pass": True, "msg": f"OK history count={len(history)}"}
        return {"pass": False, "msg": f"X count={len(history)}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_reconcile_bin_updates_current_qty():
    """SLE +50 + reconcile_bin → bin.current_qty=50."""
    from supplycore.m4_wms.api.quick_stock import reconcile_bin

    wh = _pick_warehouse()
    item = _make_item("RECON")
    b = _make_bin("RECON", warehouse=wh)
    _putaway(item.name, 50, item.uom, wh, b.name)
    try:
        res = reconcile_bin(b.name)
        frappe.db.rollback()
        if abs(flt(res["current_qty"]) - 50) < 0.01:
            return {"pass": True, "msg": f"OK current_qty=50 status={res['status']}"}
        return {"pass": False, "msg": f"X {res}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_reconcile_all_bins_processes_multiple():
    """3 bins + reconcile_all → reconciled count ≥ 3."""
    from supplycore.m4_wms.api.quick_stock import reconcile_all_bins

    wh = _pick_warehouse()
    b1 = _make_bin("RA1", warehouse=wh)
    b2 = _make_bin("RA2", warehouse=wh)
    b3 = _make_bin("RA3", warehouse=wh)
    try:
        res = reconcile_all_bins(warehouse=wh)
        frappe.db.rollback()
        if res.get("reconciled", 0) >= 3:
            return {"pass": True, "msg": f"OK reconciled={res['reconciled']}"}
        return {"pass": False, "msg": f"X {res}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def run():
    tests = [
        test_get_stock_balance_basic,
        test_get_stock_balance_filter_item_group,
        test_get_stock_balance_filter_expiry_range,
        test_get_stock_balance_as_of_date,
        test_get_stock_balance_negative_flag,
        test_get_bin_history_recent,
        test_reconcile_bin_updates_current_qty,
        test_reconcile_all_bins_processes_multiple,
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
