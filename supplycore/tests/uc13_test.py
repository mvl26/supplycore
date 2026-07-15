"""Test UC-13 — Quick stock entry (no PDA, manual web form).

Run individual: bench --site supplycore execute supplycore.tests.uc13_test.test_<name>
Run all:        bench --site supplycore execute supplycore.tests.uc13_test.run
"""

import frappe
from frappe.utils import today, add_days, random_string, flt


def _pick_warehouse() -> str:
    rows = frappe.get_all("SC Warehouse", filters={"is_group": 0, "disabled": 0},
                           pluck="name", order_by="name", limit=1)
    if not rows:
        frappe.throw("uc13_test: cần seed SC Warehouse")
    return rows[0]


def _get_uom() -> str:
    uom = frappe.db.get_value("SC UOM", {}, "name")
    if not uom:
        frappe.throw("uc13_test: cần seed SC UOM")
    return uom


def _make_item(suffix: str, has_batch: int = 0):
    item = frappe.new_doc("SC Item")
    item.item_code = f"UC13-{suffix}-{random_string(5)}"
    item.item_name = f"UC-13 test {suffix}"
    item.uom = _get_uom()
    item.is_stock_item = 1
    item.is_purchase_item = 1
    item.has_batch_no = has_batch
    item.flags.ignore_permissions = True
    item.insert()
    return item


def _make_bin(suffix: str, warehouse: str = None, capacity_qty: float = 100):
    bin_doc = frappe.new_doc("Bin Location")
    bin_doc.warehouse = warehouse or _pick_warehouse()
    bin_doc.bin_code = f"UC13-BIN-{suffix}-{random_string(4)}"
    bin_doc.capacity_qty = capacity_qty
    bin_doc.capacity_uom = _get_uom()
    bin_doc.enabled = 1
    bin_doc.flags.ignore_permissions = True
    bin_doc.insert()
    return bin_doc


def _make_batch(item: str, suffix: str):
    batch = frappe.new_doc("SC Batch")
    batch.batch_id = f"UC13-BAT-{suffix}-{random_string(4)}"
    batch.item = item
    batch.expiry_date = add_days(today(), 365)
    batch.manufacturing_date = today()
    batch.qc_status = "Accepted"
    batch.flags.ignore_permissions = True
    batch.insert()
    return batch


# ---------- Tests ----------

def test_quick_putaway_creates_se_and_sle():
    """quick_putaway → SE submitted + SLE +qty tại bin."""
    from supplycore.m4_wms.api.quick_stock import quick_putaway

    wh = _pick_warehouse()
    item = _make_item("PUT")
    b = _make_bin("PUT", warehouse=wh)
    try:
        res = quick_putaway(item=item.name, qty=10, uom=item.uom,
                              warehouse=wh, bin_location=b.name)
        se = frappe.get_doc("SC Stock Entry", res["stock_entry"])
        sle_qty = flt(frappe.db.sql("""
            SELECT COALESCE(SUM(qty_change), 0)
            FROM `tabSC Stock Ledger Entry`
            WHERE voucher_no = %s AND bin_location = %s AND is_cancelled = 0
        """, (se.name, b.name))[0][0])
        frappe.db.rollback()
        if se.docstatus == 1 and abs(sle_qty - 10) < 0.01:
            return {"pass": True, "msg": f"OK SE {se.name} SLE={sle_qty}"}
        return {"pass": False, "msg": f"X doc={se.docstatus} sle_qty={sle_qty}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_quick_picking_creates_se_and_sle():
    """quick_putaway +20 → quick_picking 5 → SLE +20 -5 = 15 tại bin."""
    from supplycore.m4_wms.api.quick_stock import quick_putaway, quick_picking

    wh = _pick_warehouse()
    item = _make_item("PICK")
    b = _make_bin("PICK", warehouse=wh)
    try:
        quick_putaway(item=item.name, qty=20, uom=item.uom,
                      warehouse=wh, bin_location=b.name)
        pick = quick_picking(item=item.name, qty=5, uom=item.uom,
                              warehouse=wh, bin_location=b.name)
        pick_qty = flt(frappe.db.sql("""
            SELECT COALESCE(SUM(qty_change), 0)
            FROM `tabSC Stock Ledger Entry`
            WHERE item = %s AND bin_location = %s AND is_cancelled = 0
        """, (item.name, b.name))[0][0])
        frappe.db.rollback()
        if abs(pick_qty - 15) < 0.01:
            return {"pass": True, "msg": f"OK net qty = 15 (20-5) at bin"}
        return {"pass": False, "msg": f"X net_qty={pick_qty}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_lookup_item_by_code():
    """lookup_item('UC13') trả items có name LIKE."""
    from supplycore.m4_wms.api.quick_stock import lookup_item
    item = _make_item("LOOK")
    try:
        res = lookup_item("UC13-LOOK")
        names = [r["item_code"] for r in res]
        frappe.db.rollback()
        if item.name in names:
            return {"pass": True, "msg": f"OK found {item.name}"}
        return {"pass": False, "msg": f"X not found in {names[:5]}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_lookup_item_by_name():
    """lookup_item('UC-13 test NAMEX') trả items có item_name LIKE."""
    from supplycore.m4_wms.api.quick_stock import lookup_item
    item = _make_item("NAMEX")
    try:
        res = lookup_item("NAMEX")
        names = [r["item_code"] for r in res]
        frappe.db.rollback()
        if item.name in names:
            return {"pass": True, "msg": f"OK found {item.name} via name"}
        return {"pass": False, "msg": f"X not found in {names[:5]}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_lookup_batch_by_id():
    """lookup_batch(item, 'UC13-BAT') trả batches có batch_id LIKE."""
    from supplycore.m4_wms.api.quick_stock import lookup_batch
    item = _make_item("BATL", has_batch=1)
    batch = _make_batch(item.name, "BATL")
    try:
        res = lookup_batch(item.name, "UC13-BAT")
        names = [r["batch_no"] for r in res]
        frappe.db.rollback()
        if batch.name in names:
            return {"pass": True, "msg": f"OK found {batch.name}"}
        return {"pass": False, "msg": f"X not found in {names[:5]}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_lookup_bin_by_code():
    """lookup_bin('UC13-BIN') trả bins có bin_code LIKE."""
    from supplycore.m4_wms.api.quick_stock import lookup_bin
    b = _make_bin("LOOKB")
    try:
        res = lookup_bin("UC13-BIN-LOOKB")
        names = [r["name"] for r in res]
        frappe.db.rollback()
        if b.name in names:
            return {"pass": True, "msg": f"OK found {b.name}"}
        return {"pass": False, "msg": f"X not found in {names[:5]}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_query_stock_position_all():
    """Sau putaway → query_stock_position trả row đúng item/batch/bin/qty."""
    from supplycore.m4_wms.api.quick_stock import quick_putaway, query_stock_position

    wh = _pick_warehouse()
    item = _make_item("QPOS", has_batch=1)
    batch = _make_batch(item.name, "QPOS")
    b = _make_bin("QPOS", warehouse=wh)
    try:
        quick_putaway(item=item.name, qty=25, uom=item.uom,
                      warehouse=wh, bin_location=b.name, batch=batch.name)
        rows = query_stock_position(item=item.name)
        frappe.db.rollback()
        matching = [r for r in rows
                     if r["item"] == item.name and r["batch"] == batch.name
                     and r["bin_location"] == b.name]
        if matching and abs(flt(matching[0]["qty"]) - 25) < 0.01:
            return {"pass": True, "msg": f"OK item={item.name} batch={batch.name} bin={b.bin_code} qty=25"}
        return {"pass": False, "msg": f"X rows={rows}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_query_stock_position_filter_by_item():
    """Filter item → chỉ trả rows item đó."""
    from supplycore.m4_wms.api.quick_stock import quick_putaway, query_stock_position

    wh = _pick_warehouse()
    item1 = _make_item("F1")
    item2 = _make_item("F2")
    b = _make_bin("FILT", warehouse=wh)
    try:
        quick_putaway(item=item1.name, qty=10, uom=item1.uom,
                      warehouse=wh, bin_location=b.name)
        quick_putaway(item=item2.name, qty=20, uom=item2.uom,
                      warehouse=wh, bin_location=b.name)
        rows = query_stock_position(item=item1.name)
        frappe.db.rollback()
        item1_only = all(r["item"] == item1.name for r in rows)
        item1_present = any(r["item"] == item1.name for r in rows)
        if item1_only and item1_present:
            return {"pass": True, "msg": f"OK filter item returned {len(rows)} rows (all item1)"}
        return {"pass": False, "msg": f"X rows mixed items: {[r['item'] for r in rows[:5]]}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_query_stock_position_filter_by_bin():
    """Filter bin → chỉ trả rows bin đó."""
    from supplycore.m4_wms.api.quick_stock import quick_putaway, query_stock_position

    wh = _pick_warehouse()
    item = _make_item("FBIN")
    b1 = _make_bin("FB1", warehouse=wh)
    b2 = _make_bin("FB2", warehouse=wh)
    try:
        quick_putaway(item=item.name, qty=10, uom=item.uom,
                      warehouse=wh, bin_location=b1.name)
        quick_putaway(item=item.name, qty=20, uom=item.uom,
                      warehouse=wh, bin_location=b2.name)
        rows = query_stock_position(bin_location=b1.name)
        frappe.db.rollback()
        bin1_only = all(r["bin_location"] == b1.name for r in rows)
        if bin1_only and rows:
            return {"pass": True, "msg": f"OK filter bin returned {len(rows)} rows (all b1)"}
        return {"pass": False, "msg": f"X rows mixed bins: {[r['bin_location'] for r in rows[:5]]}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_query_stock_position_excludes_picked():
    """putaway +50, picking -30 → query trả qty=20."""
    from supplycore.m4_wms.api.quick_stock import quick_putaway, quick_picking, query_stock_position

    wh = _pick_warehouse()
    item = _make_item("EXCL")
    b = _make_bin("EXCL", warehouse=wh)
    try:
        quick_putaway(item=item.name, qty=50, uom=item.uom,
                      warehouse=wh, bin_location=b.name)
        quick_picking(item=item.name, qty=30, uom=item.uom,
                       warehouse=wh, bin_location=b.name)
        rows = query_stock_position(item=item.name, bin_location=b.name)
        frappe.db.rollback()
        matching = [r for r in rows if r["bin_location"] == b.name]
        if matching and abs(flt(matching[0]["qty"]) - 20) < 0.01:
            return {"pass": True, "msg": f"OK net qty=20 (50-30)"}
        return {"pass": False, "msg": f"X matching={matching}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def run():
    tests = [
        test_quick_putaway_creates_se_and_sle,
        test_quick_picking_creates_se_and_sle,
        test_lookup_item_by_code,
        test_lookup_item_by_name,
        test_lookup_batch_by_id,
        test_lookup_bin_by_code,
        test_query_stock_position_all,
        test_query_stock_position_filter_by_item,
        test_query_stock_position_filter_by_bin,
        test_query_stock_position_excludes_picked,
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
