"""Test UC-27 — Inventory Count Sheet.

Run individual: bench --site supplycore execute supplycore.tests.uc27_test.test_<name>
Run all:        bench --site supplycore execute supplycore.tests.uc27_test.run
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
    item.item_code = f"UC27-{suffix}-{random_string(5)}"
    item.item_name = f"UC-27 test {suffix}"
    item.uom = _get_uom()
    item.is_stock_item = 1
    item.flags.ignore_permissions = True
    item.insert()
    return item


def _seed_stock(item, warehouse, qty, rate=1000):
    from supplycore.supplycore.doctype.sc_stock_ledger_entry.sc_stock_ledger_entry import SCStockLedgerEntry
    return SCStockLedgerEntry.post(
        item=item, warehouse=warehouse, qty_change=flt(qty), valuation_rate=flt(rate),
        voucher_type="Manual", voucher_no=f"UC27-{random_string(6)}",
        posting_date=today(),
    )


def _make_ics(warehouse, scope="All Items", items=None):
    ics = frappe.new_doc("SC Inventory Count Sheet")
    ics.count_date = today()
    ics.warehouse = warehouse
    ics.count_scope = scope
    ics.recount_threshold_pct = 5
    for it in (items or []):
        ics.append("items", {
            "item": it["item"], "uom": _get_uom(),
            "actual_qty": flt(it.get("actual_qty", 0)),
        })
    ics.flags.ignore_permissions = True
    return ics


# ---------- Tests ----------

def test_ics_create_basic():
    """Tạo ICS Draft."""
    wh = _pick_warehouse()
    ics = _make_ics(wh)
    try:
        ics.insert()
        ok = (ics.name and ics.status == "Draft")
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK ICS {ics.name}"}
        return {"pass": False, "msg": f"X status={ics.status}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_ics_auto_load_items():
    """auto_load_items → 2 rows từ SLE."""
    wh = _pick_warehouse()
    item1 = _make_item("AL1")
    item2 = _make_item("AL2")
    _seed_stock(item1.name, wh, 100)
    _seed_stock(item2.name, wh, 50)
    ics = _make_ics(wh)
    try:
        ics.insert()
        ics.auto_load_items()
        ics.reload()
        item_names = {r.item for r in ics.items}
        frappe.db.rollback()
        if item1.name in item_names and item2.name in item_names:
            return {"pass": True, "msg": f"OK loaded {len(ics.items)} items"}
        return {"pass": False, "msg": f"X items={item_names}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_ics_snapshot_system_qty():
    """Save ICS → system_qty auto fill từ SLE."""
    wh = _pick_warehouse()
    item = _make_item("SNAP")
    _seed_stock(item.name, wh, 75)
    ics = _make_ics(wh, items=[{"item": item.name, "actual_qty": 0}])
    try:
        ics.insert()
        row = ics.items[0]
        frappe.db.rollback()
        if abs(flt(row.system_qty) - 75) < 0.01:
            return {"pass": True, "msg": f"OK system_qty=75"}
        return {"pass": False, "msg": f"X system_qty={row.system_qty}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_ics_compute_variance():
    """actual=120, system=100 → diff=20, variance_pct=20."""
    wh = _pick_warehouse()
    item = _make_item("VAR")
    _seed_stock(item.name, wh, 100)
    ics = _make_ics(wh, items=[{"item": item.name, "actual_qty": 120}])
    try:
        ics.insert()
        row = ics.items[0]
        ok = (abs(flt(row.difference) - 20) < 0.01
              and abs(flt(row.variance_pct) - 20) < 0.5)
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK diff=20 pct=20"}
        return {"pass": False, "msg": f"X diff={row.difference} pct={row.variance_pct}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_ics_needs_recount_flag():
    """variance > threshold → needs_recount=1."""
    wh = _pick_warehouse()
    item = _make_item("RECT")
    _seed_stock(item.name, wh, 100)
    ics = _make_ics(wh, items=[{"item": item.name, "actual_qty": 120}])  # 20% > 5%
    try:
        ics.insert()
        ok = (ics.items[0].needs_recount == 1)
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": "OK needs_recount=1"}
        return {"pass": False, "msg": f"X needs_recount={ics.items[0].needs_recount}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_ics_recount_priority():
    """recount_actual_qty=110 vs actual=120 → diff dùng 110."""
    wh = _pick_warehouse()
    item = _make_item("RECP")
    _seed_stock(item.name, wh, 100)
    ics = _make_ics(wh, items=[{"item": item.name, "actual_qty": 120}])
    ics.insert()
    ics.items[0].recount_actual_qty = 110
    try:
        ics.save()
        row = ics.items[0]
        ok = (abs(flt(row.difference) - 10) < 0.01)  # 110-100
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK diff=10 (used recount)"}
        return {"pass": False, "msg": f"X diff={row.difference}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_ics_third_count_priority():
    """third_count_qty=105 → diff dùng 105."""
    wh = _pick_warehouse()
    item = _make_item("THIR")
    _seed_stock(item.name, wh, 100)
    ics = _make_ics(wh, items=[{"item": item.name, "actual_qty": 120}])
    ics.insert()
    ics.items[0].recount_actual_qty = 110
    ics.items[0].third_count_qty = 105
    try:
        ics.save()
        row = ics.items[0]
        ok = (abs(flt(row.difference) - 5) < 0.01)  # 105-100
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": "OK diff=5 (used third_count)"}
        return {"pass": False, "msg": f"X diff={row.difference}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_ics_third_count_requires_witness():
    """submit với third_count + no witness → SC-E-ICS-WITNESS-REQUIRED."""
    wh = _pick_warehouse()
    item = _make_item("WITNEED")
    _seed_stock(item.name, wh, 100)
    ics = _make_ics(wh, items=[{"item": item.name, "actual_qty": 120}])
    ics.insert()
    ics.items[0].third_count_qty = 105
    ics.save()
    try:
        ics.submit()
        frappe.db.rollback()
        return {"pass": False, "msg": "X did not throw"}
    except frappe.ValidationError as e:
        msg = str(e)
        frappe.db.rollback()
        if "SC-E-ICS-WITNESS-REQUIRED" in msg:
            return {"pass": True, "msg": f"OK: {msg[:120]}"}
        return {"pass": False, "msg": f"Wrong error: {msg[:120]}"}


def test_ics_third_count_with_witness_ok():
    """third_count + witness → submit OK."""
    wh = _pick_warehouse()
    item = _make_item("WITOK")
    _seed_stock(item.name, wh, 100)
    ics = _make_ics(wh, items=[{"item": item.name, "actual_qty": 120}])
    ics.manager_witness = "Administrator"
    ics.insert()
    ics.items[0].third_count_qty = 105
    ics.save()
    try:
        ics.submit()
        ok = (ics.docstatus == 1 and ics.status == "Counted")
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": "OK submitted with witness"}
        return {"pass": False, "msg": f"X doc={ics.docstatus}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_ics_start_counting_sets_status():
    """start_counting → status=In Progress."""
    wh = _pick_warehouse()
    item = _make_item("SC")
    _seed_stock(item.name, wh, 50)
    ics = _make_ics(wh, items=[{"item": item.name, "actual_qty": 0}])
    ics.insert()
    try:
        ics.start_counting()
        ics.reload()
        ok = (ics.status == "In Progress")
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": "OK status=In Progress"}
        return {"pass": False, "msg": f"X status={ics.status}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_ics_make_sr():
    """ICS Counted + diff > 0 → make_stock_reconciliation tạo SR Draft."""
    wh = _pick_warehouse()
    item = _make_item("MKSR")
    _seed_stock(item.name, wh, 100)
    ics = _make_ics(wh, items=[{"item": item.name, "actual_qty": 110}])
    ics.insert()
    # Set reason for SR (UC-19 reqd)
    ics.items[0].reason = "Counting Error"
    ics.save()
    ics.submit()
    try:
        sr_name = ics.make_stock_reconciliation()
        sr = frappe.get_doc("SC Stock Reconciliation", sr_name)
        ok = (sr.docstatus == 0 and len(sr.items) == 1)
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK SR {sr_name}"}
        return {"pass": False, "msg": f"X doc={sr.docstatus} items={len(sr.items)}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_get_count_sheet_print_data_hides_system():
    """hide=1 → row không có system_qty key."""
    wh = _pick_warehouse()
    item = _make_item("PRINT1")
    _seed_stock(item.name, wh, 50)
    ics = _make_ics(wh, items=[{"item": item.name, "actual_qty": 0}])
    ics.insert()
    try:
        data = ics.get_count_sheet_print_data(hide_system_qty=1)
        has_system_qty = any("system_qty" in r for r in data["items"])
        frappe.db.rollback()
        if not has_system_qty:
            return {"pass": True, "msg": "OK system_qty hidden"}
        return {"pass": False, "msg": "X system_qty leaked"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_get_count_sheet_print_data_shows_system():
    """hide=0 → row có system_qty."""
    wh = _pick_warehouse()
    item = _make_item("PRINT0")
    _seed_stock(item.name, wh, 50)
    ics = _make_ics(wh, items=[{"item": item.name, "actual_qty": 0}])
    ics.insert()
    try:
        data = ics.get_count_sheet_print_data(hide_system_qty=0)
        has_system_qty = all("system_qty" in r for r in data["items"])
        frappe.db.rollback()
        if has_system_qty:
            return {"pass": True, "msg": "OK system_qty shown"}
        return {"pass": False, "msg": "X system_qty not shown"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def run():
    tests = [
        test_ics_create_basic,
        test_ics_auto_load_items,
        test_ics_snapshot_system_qty,
        test_ics_compute_variance,
        test_ics_needs_recount_flag,
        test_ics_recount_priority,
        test_ics_third_count_priority,
        test_ics_third_count_requires_witness,
        test_ics_third_count_with_witness_ok,
        test_ics_start_counting_sets_status,
        test_ics_make_sr,
        test_get_count_sheet_print_data_hides_system,
        test_get_count_sheet_print_data_shows_system,
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
