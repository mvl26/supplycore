"""Test UC-12 — Bin Location + Putaway Rule.

Run individual: bench --site supplycore execute supplycore.tests.uc12_test.test_<name>
Run all:        bench --site supplycore execute supplycore.tests.uc12_test.run
"""

import frappe
from frappe.utils import random_string, flt


def _pick_warehouse() -> str:
    rows = frappe.get_all("SC Warehouse", filters={"is_group": 0, "disabled": 0},
                           pluck="name", order_by="name", limit=1)
    if not rows:
        frappe.throw("uc12_test: cần seed SC Warehouse")
    return rows[0]


def _get_uom() -> str:
    uom = frappe.db.get_value("SC UOM", {}, "name")
    if not uom:
        frappe.throw("uc12_test: cần seed SC UOM")
    return uom


def _make_bin(suffix: str, warehouse: str = None, **kwargs):
    bin_doc = frappe.new_doc("Bin Location")
    bin_doc.warehouse = warehouse or _pick_warehouse()
    bin_doc.bin_code = f"UC12-{suffix}-{random_string(5)}"
    bin_doc.description = f"UC-12 test bin {suffix}"
    bin_doc.enabled = 1
    bin_doc.flags.ignore_permissions = True
    for k, v in kwargs.items():
        setattr(bin_doc, k, v)
    bin_doc.insert()
    return bin_doc


def _make_item(suffix: str, **kwargs):
    item = frappe.new_doc("SC Item")
    item.item_code = f"UC12-{suffix}-{random_string(5)}"
    item.item_name = f"UC-12 test {suffix}"
    item.uom = _get_uom()
    item.is_stock_item = 1
    item.flags.ignore_permissions = True
    for k, v in kwargs.items():
        setattr(item, k, v)
    item.insert()
    return item


# ---------- Tests ----------

def test_bin_create_basic():
    """Tạo bin với warehouse + bin_code + capacity → save OK."""
    try:
        b = _make_bin("BASIC", capacity_qty=100, capacity_uom=_get_uom())
        ok = (b.name and b.bin_code.startswith("UC12-BASIC"))
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK bin {b.name}"}
        return {"pass": False, "msg": f"X bin not created properly"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_bin_temperature_range_validate():
    """min ≥ max → throw."""
    try:
        b = _make_bin("TEMP", temperature_controlled=1,
                      min_temperature=10, max_temperature=5)
        frappe.db.rollback()
        return {"pass": False, "msg": "X did not throw on temp range"}
    except frappe.ValidationError as e:
        msg = str(e)
        frappe.db.rollback()
        if "Nhiệt độ" in msg or "max" in msg.lower():
            return {"pass": True, "msg": f"OK: {msg[:120]}"}
        return {"pass": False, "msg": f"Wrong error: {msg[:120]}"}


def test_bin_delete_blocked_when_has_stock():
    """Bin có SLE qty > 0 → delete throw SC-E-BIN-NOT-EMPTY."""
    from supplycore.supplycore.doctype.sc_stock_ledger_entry.sc_stock_ledger_entry import SCStockLedgerEntry
    from frappe.utils import today

    wh = _pick_warehouse()
    item = _make_item("DELBIN")
    b = _make_bin("DELSTOCK", warehouse=wh, capacity_qty=50)
    SCStockLedgerEntry.post(
        item=item.name, warehouse=wh, qty_change=10,
        voucher_type="Manual", voucher_no=f"UC12-DEL-{random_string(6)}",
        posting_date=today(), bin_location=b.name,
    )
    try:
        frappe.delete_doc("Bin Location", b.name, ignore_permissions=True)
        frappe.db.rollback()
        return {"pass": False, "msg": "X delete không bị block"}
    except frappe.ValidationError as e:
        msg = str(e)
        frappe.db.rollback()
        if "SC-E-BIN-NOT-EMPTY" in msg:
            return {"pass": True, "msg": f"OK: {msg[:120]}"}
        return {"pass": False, "msg": f"Wrong error: {msg[:120]}"}


def test_bin_delete_allowed_when_empty():
    """Bin không có qty → delete OK."""
    try:
        b = _make_bin("DELOK", capacity_qty=50)
        frappe.delete_doc("Bin Location", b.name, ignore_permissions=True)
        frappe.db.rollback()
        return {"pass": True, "msg": f"OK deleted empty bin"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_bin_recompute_occupancy_empty():
    """Bin chưa có SLE → status=Empty."""
    try:
        b = _make_bin("EMPTY", capacity_qty=100)
        res = b.recompute_occupancy()
        frappe.db.rollback()
        if res["status"] == "Empty" and res["current_qty"] == 0:
            return {"pass": True, "msg": f"OK status=Empty pct=0"}
        return {"pass": False, "msg": f"X {res}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_bin_recompute_occupancy_in_use():
    """SLE +50 vào bin (cap=100) → status=In Use, pct≈50."""
    from supplycore.supplycore.doctype.sc_stock_ledger_entry.sc_stock_ledger_entry import SCStockLedgerEntry
    from frappe.utils import today

    wh = _pick_warehouse()
    item = _make_item("INUSE")
    b = _make_bin("INUSE", warehouse=wh, capacity_qty=100)
    SCStockLedgerEntry.post(
        item=item.name, warehouse=wh, qty_change=50,
        voucher_type="Manual", voucher_no=f"UC12-IU-{random_string(6)}",
        posting_date=today(), bin_location=b.name,
    )
    try:
        res = b.recompute_occupancy()
        frappe.db.rollback()
        if res["status"] == "In Use" and abs(res["occupancy_pct"] - 50) < 1:
            return {"pass": True, "msg": f"OK status=In Use pct={res['occupancy_pct']}"}
        return {"pass": False, "msg": f"X {res}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_bin_recompute_occupancy_full():
    """SLE +95 vào bin (cap=100) → status=Full."""
    from supplycore.supplycore.doctype.sc_stock_ledger_entry.sc_stock_ledger_entry import SCStockLedgerEntry
    from frappe.utils import today

    wh = _pick_warehouse()
    item = _make_item("FULL")
    b = _make_bin("FULL", warehouse=wh, capacity_qty=100)
    SCStockLedgerEntry.post(
        item=item.name, warehouse=wh, qty_change=95,
        voucher_type="Manual", voucher_no=f"UC12-FL-{random_string(6)}",
        posting_date=today(), bin_location=b.name,
    )
    try:
        res = b.recompute_occupancy()
        frappe.db.rollback()
        if res["status"] == "Full" and abs(res["occupancy_pct"] - 95) < 1:
            return {"pass": True, "msg": f"OK status=Full pct={res['occupancy_pct']}"}
        return {"pass": False, "msg": f"X {res}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_putaway_rule_requires_item_or_group():
    """Tạo Putaway Rule không item/group → SC-E-PUTAWAY-RULE."""
    b = _make_bin("PWRBAD", capacity_qty=100)
    pwr = frappe.new_doc("Putaway Rule")
    pwr.target_bin = b.name
    pwr.priority = 1
    pwr.enabled = 1
    pwr.flags.ignore_permissions = True
    try:
        pwr.insert()
        frappe.db.rollback()
        return {"pass": False, "msg": "X did not throw"}
    except frappe.ValidationError as e:
        msg = str(e)
        frappe.db.rollback()
        if "SC-E-PUTAWAY-RULE" in msg:
            return {"pass": True, "msg": f"OK: {msg[:120]}"}
        return {"pass": False, "msg": f"Wrong error: {msg[:120]}"}


def test_suggest_bin_uses_item_rule():
    """Rule item + warehouse → suggest_bin trả bin đó."""
    from supplycore.m4_wms.api.bin_helpers import suggest_bin

    wh = _pick_warehouse()
    item = _make_item("SUGITEM")
    b = _make_bin("SUGITEM", warehouse=wh, capacity_qty=100)
    pwr = frappe.new_doc("Putaway Rule")
    pwr.item = item.name
    pwr.warehouse = wh
    pwr.target_bin = b.name
    pwr.priority = 10
    pwr.enabled = 1
    pwr.flags.ignore_permissions = True
    pwr.insert()
    try:
        res = suggest_bin(item.name, wh, qty=10)
        frappe.db.rollback()
        if res["bin"] == b.name and res["source"] == "rule_item_wh":
            return {"pass": True, "msg": f"OK suggested={b.name} via item rule"}
        return {"pass": False, "msg": f"X {res}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_suggest_bin_falls_back_to_default():
    """Không rule, có item.default_bin_location cùng warehouse → suggest trả default."""
    from supplycore.m4_wms.api.bin_helpers import suggest_bin

    wh = _pick_warehouse()
    b = _make_bin("DEFB", warehouse=wh, capacity_qty=100)
    item = _make_item("DEFI", default_bin_location=b.name)
    try:
        res = suggest_bin(item.name, wh, qty=10)
        frappe.db.rollback()
        if res["bin"] == b.name and res["source"] == "item_default":
            return {"pass": True, "msg": f"OK fallback default={b.name}"}
        return {"pass": False, "msg": f"X {res}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_suggest_bin_skips_full_bin():
    """Rule trỏ bin đầy → suggest trả no_match hoặc fallback khác."""
    from supplycore.m4_wms.api.bin_helpers import suggest_bin
    from supplycore.supplycore.doctype.sc_stock_ledger_entry.sc_stock_ledger_entry import SCStockLedgerEntry
    from frappe.utils import today

    wh = _pick_warehouse()
    item = _make_item("SKIPFULL")
    b = _make_bin("SKIPFULL", warehouse=wh, capacity_qty=10)
    # Fill bin to capacity
    SCStockLedgerEntry.post(
        item=item.name, warehouse=wh, qty_change=10,
        voucher_type="Manual", voucher_no=f"UC12-SF-{random_string(6)}",
        posting_date=today(), bin_location=b.name,
    )
    b.recompute_occupancy()
    pwr = frappe.new_doc("Putaway Rule")
    pwr.item = item.name
    pwr.warehouse = wh
    pwr.target_bin = b.name
    pwr.priority = 10
    pwr.enabled = 1
    pwr.flags.ignore_permissions = True
    pwr.insert()
    try:
        res = suggest_bin(item.name, wh, qty=5)  # +5 vượt cap 10
        frappe.db.rollback()
        # Either no_match (no fallback) or different bin
        if res["bin"] != b.name:
            return {"pass": True, "msg": f"OK skipped full bin: result={res}"}
        return {"pass": False, "msg": f"X returned full bin: {res}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_get_alternative_bin_same_zone_first():
    """Bin đầy → alternative ưu tiên cùng zone."""
    from supplycore.m4_wms.api.bin_helpers import get_alternative_bin

    wh = _pick_warehouse()
    b_full = _make_bin("ALTSRC", warehouse=wh, zone="Z1", aisle="A1", capacity_qty=10)
    b_same_zone = _make_bin("ALTZ1", warehouse=wh, zone="Z1", aisle="A2", capacity_qty=100)
    b_diff_zone = _make_bin("ALTZ2", warehouse=wh, zone="Z2", aisle="A1", capacity_qty=100)
    try:
        res = get_alternative_bin(b_full.name, qty=5)
        alts = res.get("alternatives", [])
        frappe.db.rollback()
        if alts and alts[0]["name"] == b_same_zone.name:
            return {"pass": True, "msg": f"OK same-zone {b_same_zone.name} first in alts"}
        return {"pass": False, "msg": f"X alts={[a['name'] for a in alts]}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_get_barcode_label_data():
    """Method trả dict đủ field cho in barcode."""
    try:
        b = _make_bin("BCLBL", capacity_qty=100, barcode="BC-UC12-TEST")
        data = b.get_barcode_label_data()
        frappe.db.rollback()
        required = {"barcode", "bin_code", "warehouse", "url"}
        if required.issubset(set(data.keys())):
            return {"pass": True, "msg": f"OK barcode label data: {list(data.keys())}"}
        return {"pass": False, "msg": f"X missing fields: {required - set(data.keys())}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_suggest_bin_falls_back_to_item_group():
    """Không rule item, có rule item_group + warehouse → suggest trả rule group bin."""
    from supplycore.m4_wms.api.bin_helpers import suggest_bin

    wh = _pick_warehouse()
    # Sử dụng item_group đã seed
    item_group = frappe.db.get_value("SC Item Group", {}, "name")
    if not item_group:
        return {"pass": False, "msg": "X cần seed SC Item Group"}
    item = _make_item("GRPI", item_group=item_group)
    b = _make_bin("GRPB", warehouse=wh, capacity_qty=100)
    pwr = frappe.new_doc("Putaway Rule")
    pwr.item_group = item_group
    pwr.warehouse = wh
    pwr.target_bin = b.name
    pwr.priority = 5
    pwr.enabled = 1
    pwr.flags.ignore_permissions = True
    pwr.insert()
    try:
        res = suggest_bin(item.name, wh, qty=10)
        frappe.db.rollback()
        if res["bin"] == b.name and res["source"] == "rule_group_wh":
            return {"pass": True, "msg": f"OK via group rule = {b.name}"}
        return {"pass": False, "msg": f"X {res}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def run():
    tests = [
        test_bin_create_basic,
        test_bin_temperature_range_validate,
        test_bin_delete_blocked_when_has_stock,
        test_bin_delete_allowed_when_empty,
        test_bin_recompute_occupancy_empty,
        test_bin_recompute_occupancy_in_use,
        test_bin_recompute_occupancy_full,
        test_putaway_rule_requires_item_or_group,
        test_suggest_bin_uses_item_rule,
        test_suggest_bin_falls_back_to_default,
        test_suggest_bin_falls_back_to_item_group,
        test_suggest_bin_skips_full_bin,
        test_get_alternative_bin_same_zone_first,
        test_get_barcode_label_data,
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
