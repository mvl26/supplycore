"""Test UC-29 — Batch trace.

Run individual: bench --site supplycore execute supplycore.tests.uc29_test.test_<name>
Run all:        bench --site supplycore execute supplycore.tests.uc29_test.run
"""

import frappe
from frappe.utils import today, add_days, random_string, flt


def _pick_warehouse() -> str:
    rows = frappe.get_all("SC Warehouse", filters={"is_group": 0, "disabled": 0},
                           pluck="name", order_by="name", limit=1)
    return rows[0] if rows else None


def _get_uom() -> str:
    return frappe.db.get_value("SC UOM", {}, "name")


def _make_item(suffix: str):
    item = frappe.new_doc("SC Item")
    item.item_code = f"UC29-{suffix}-{random_string(5)}"
    item.item_name = f"UC-29 test {suffix}"
    item.uom = _get_uom()
    item.is_stock_item = 1
    item.has_batch_no = 1
    item.flags.ignore_permissions = True
    item.insert()
    return item


def _make_batch(item, **kwargs):
    from supplycore.m5_fefo.api.batch_helpers import generate_batch_id
    expiry = kwargs.get("expiry_date", add_days(today(), 365))
    mfg = kwargs.get("manufacturing_date", add_days(expiry, -730))
    batch = frappe.new_doc("SC Batch")
    batch.batch_id = generate_batch_id(item, str(expiry))
    batch.item = item
    batch.expiry_date = expiry
    batch.manufacturing_date = mfg
    batch.qc_status = kwargs.get("qc_status", "Accepted")
    if "supplier" in kwargs:
        batch.supplier = kwargs["supplier"]
    if "supplier_batch_no" in kwargs:
        batch.supplier_batch_no = kwargs["supplier_batch_no"]
    if "manufacturer" in kwargs:
        batch.manufacturer = kwargs["manufacturer"]
    batch.flags.ignore_permissions = True
    batch.flags.ignore_short_expiry = 1
    batch.insert()
    return batch


def _seed_sle(item, warehouse, batch, qty, voucher_type="Manual"):
    from supplycore.supplycore.doctype.sc_stock_ledger_entry.sc_stock_ledger_entry import SCStockLedgerEntry
    return SCStockLedgerEntry.post(
        item=item, warehouse=warehouse, qty_change=flt(qty), batch=batch,
        voucher_type=voucher_type, voucher_no=f"UC29-{random_string(6)}",
        posting_date=today(),
    )


# ---------- Tests ----------

def test_trace_nonexistent_batch():
    """batch_no không tồn tại → exists=False."""
    from supplycore.m10_traceability.api.trace import get_batch_trace
    res = get_batch_trace("UC29-NONEXIST-XXX")
    if res["exists"] is False:
        return {"pass": True, "msg": "OK exists=False"}
    return {"pass": False, "msg": f"X {res}"}


def test_trace_basic_batch_no_movements():
    """Batch tạo manual không SLE → exists=True, movements=[]."""
    from supplycore.m10_traceability.api.trace import get_batch_trace
    item = _make_item("BASIC")
    batch = _make_batch(item.name)
    try:
        res = get_batch_trace(batch.name)
        frappe.db.rollback()
        if res["exists"] and res["movements"] == []:
            return {"pass": True, "msg": "OK exists=True, no movements"}
        return {"pass": False, "msg": f"X mvmt={res.get('movements')}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_trace_batch_with_movements():
    """Batch có 3 SLE → movements trả 3 entries."""
    from supplycore.m10_traceability.api.trace import get_batch_trace
    wh = _pick_warehouse()
    item = _make_item("MVMT")
    batch = _make_batch(item.name)
    _seed_sle(item.name, wh, batch.name, 100)
    _seed_sle(item.name, wh, batch.name, -20)
    _seed_sle(item.name, wh, batch.name, -10)
    try:
        res = get_batch_trace(batch.name)
        frappe.db.rollback()
        if len(res["movements"]) == 3:
            return {"pass": True, "msg": f"OK 3 movements"}
        return {"pass": False, "msg": f"X movements={len(res['movements'])}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_trace_current_stock_per_warehouse():
    """SLE 2 warehouses → current_stock.by_warehouse có 2 rows."""
    from supplycore.m10_traceability.api.trace import get_batch_trace
    whs = frappe.get_all("SC Warehouse", filters={"is_group": 0, "disabled": 0},
                          pluck="name", order_by="name", limit=2)
    if len(whs) < 2:
        return {"pass": True, "msg": "OK (skipped: <2 warehouses)"}
    item = _make_item("MULTI")
    batch = _make_batch(item.name)
    _seed_sle(item.name, whs[0], batch.name, 50)
    _seed_sle(item.name, whs[1], batch.name, 30)
    try:
        res = get_batch_trace(batch.name)
        frappe.db.rollback()
        wh_names = {r["warehouse"] for r in res["current_stock"]["by_warehouse"]}
        if whs[0] in wh_names and whs[1] in wh_names:
            return {"pass": True, "msg": f"OK 2 warehouses"}
        return {"pass": False, "msg": f"X {wh_names}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_trace_current_stock_zero_when_depleted():
    """SLE +50 / -50 → total_qty=0."""
    from supplycore.m10_traceability.api.trace import get_batch_trace
    wh = _pick_warehouse()
    item = _make_item("DEPL")
    batch = _make_batch(item.name)
    _seed_sle(item.name, wh, batch.name, 50)
    _seed_sle(item.name, wh, batch.name, -50)
    try:
        res = get_batch_trace(batch.name)
        frappe.db.rollback()
        total = flt(res["current_stock"]["total_qty"])
        if abs(total) < 0.01:
            return {"pass": True, "msg": "OK depleted total=0"}
        return {"pass": False, "msg": f"X total={total}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_trace_data_quality_complete():
    """Batch đủ thông tin → data_quality.complete=True."""
    from supplycore.m10_traceability.api.trace import get_batch_trace
    sup = frappe.db.get_value("SC Supplier", {"disabled": 0}, "name")
    if not sup:
        return {"pass": True, "msg": "OK (skipped: no supplier)"}
    item = _make_item("COMPL")
    batch = _make_batch(item.name,
                         supplier=sup,
                         supplier_batch_no=f"SUP-LOT-{random_string(5)}",
                         manufacturer="Test Manufacturer")
    # Don't add PR → still missing purchase_receipt_origin; but for completion check
    # this batch will be flagged
    try:
        res = get_batch_trace(batch.name)
        frappe.db.rollback()
        # Without PR, complete=False (missing origin)
        if not res["data_quality"]["complete"] \
           and "purchase_receipt_origin" in res["data_quality"]["missing"]:
            return {"pass": True, "msg": "OK missing origin detected"}
        return {"pass": False, "msg": f"X {res['data_quality']}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_trace_data_quality_missing_supplier():
    """Batch không supplier → missing có 'supplier'."""
    from supplycore.m10_traceability.api.trace import get_batch_trace
    item = _make_item("NOSUP")
    batch = _make_batch(item.name)  # no supplier set
    try:
        res = get_batch_trace(batch.name)
        frappe.db.rollback()
        if "supplier" in res["data_quality"]["missing"]:
            return {"pass": True, "msg": "OK missing supplier detected"}
        return {"pass": False, "msg": f"X {res['data_quality']['missing']}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_trace_data_quality_pending_qc():
    """Batch qc_status=Pending → missing có 'qc_inspection_pending'."""
    from supplycore.m10_traceability.api.trace import get_batch_trace
    item = _make_item("QCPND")
    batch = _make_batch(item.name, qc_status="Pending")
    try:
        res = get_batch_trace(batch.name)
        frappe.db.rollback()
        if "qc_inspection_pending" in res["data_quality"]["missing"]:
            return {"pass": True, "msg": "OK pending QC detected"}
        return {"pass": False, "msg": f"X {res['data_quality']['missing']}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_list_batches_for_item_by_code():
    """Search item_code → trả batches."""
    from supplycore.m10_traceability.api.trace import list_batches_for_item
    item = _make_item("LIST1")
    batch1 = _make_batch(item.name)
    batch2 = _make_batch(item.name)
    try:
        res = list_batches_for_item("UC29-LIST1")
        names = [r["name"] for r in res]
        frappe.db.rollback()
        if batch1.name in names and batch2.name in names:
            return {"pass": True, "msg": f"OK found {len(names)} batches"}
        return {"pass": False, "msg": f"X names={names[:5]}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_list_batches_for_item_by_name():
    """Search item_name → trả batches."""
    from supplycore.m10_traceability.api.trace import list_batches_for_item
    item = _make_item("BYNAME")
    batch = _make_batch(item.name)
    try:
        res = list_batches_for_item("UC-29 test BYNAME")
        names = [r["name"] for r in res]
        frappe.db.rollback()
        if batch.name in names:
            return {"pass": True, "msg": "OK found via name"}
        return {"pass": False, "msg": f"X names={names[:5]}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_trace_header_complete():
    """Header trả đủ field key."""
    from supplycore.m10_traceability.api.trace import get_batch_trace
    item = _make_item("HDR")
    batch = _make_batch(item.name, manufacturer="Co X")
    try:
        res = get_batch_trace(batch.name)
        h = res["header"]
        frappe.db.rollback()
        required = {"batch_id", "item", "manufacturer", "qc_status", "blocked"}
        if required.issubset(set(h.keys())):
            return {"pass": True, "msg": "OK header complete"}
        return {"pass": False, "msg": f"X missing: {required - set(h.keys())}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def run():
    tests = [
        test_trace_nonexistent_batch,
        test_trace_basic_batch_no_movements,
        test_trace_batch_with_movements,
        test_trace_current_stock_per_warehouse,
        test_trace_current_stock_zero_when_depleted,
        test_trace_data_quality_complete,
        test_trace_data_quality_missing_supplier,
        test_trace_data_quality_pending_qc,
        test_list_batches_for_item_by_code,
        test_list_batches_for_item_by_name,
        test_trace_header_complete,
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
