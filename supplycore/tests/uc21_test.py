"""Test UC-21 — Process Dispensing.

Run individual: bench --site supplycore execute supplycore.tests.uc21_test.test_<name>
Run all:        bench --site supplycore execute supplycore.tests.uc21_test.run
"""

import frappe
from frappe.utils import today, add_days, random_string, flt


def _pick_warehouse() -> str:
    rows = frappe.get_all("SC Warehouse", filters={"is_group": 0, "disabled": 0},
                           pluck="name", order_by="name", limit=1)
    if not rows:
        frappe.throw("uc21_test: cần seed SC Warehouse")
    return rows[0]


def _pick_department() -> str:
    rows = frappe.get_all("SC Department", filters={"disabled": 0},
                           pluck="name", order_by="name", limit=1)
    if not rows:
        d = frappe.new_doc("SC Department")
        d.department_name = f"UC21-Dept-{random_string(4)}"
        d.department_type = "Clinical"
        d.flags.ignore_permissions = True
        d.insert()
        return d.name
    return rows[0]


def _get_uom() -> str:
    uom = frappe.db.get_value("SC UOM", {}, "name")
    if not uom:
        frappe.throw("uc21_test: cần seed SC UOM")
    return uom


def _make_item(suffix: str, has_batch: int = 1):
    item = frappe.new_doc("SC Item")
    item.item_code = f"UC21-{suffix}-{random_string(5)}"
    item.item_name = f"UC-21 test {suffix}"
    item.uom = _get_uom()
    item.is_stock_item = 1
    item.has_batch_no = has_batch
    item.flags.ignore_permissions = True
    item.insert()
    return item


def _make_batch(item: str, expiry_offset_days: int = 365):
    from supplycore.m5_fefo.api.batch_helpers import generate_batch_id
    expiry = add_days(today(), expiry_offset_days)
    mfg = add_days(expiry, -730)
    batch = frappe.new_doc("SC Batch")
    batch.batch_id = generate_batch_id(item, str(expiry))
    batch.item = item
    batch.expiry_date = expiry
    batch.manufacturing_date = mfg
    batch.qc_status = "Accepted"
    batch.flags.ignore_permissions = True
    batch.flags.ignore_short_expiry = 1
    batch.insert()
    return batch


def _seed_stock(item, warehouse, batch, qty):
    from supplycore.supplycore.doctype.sc_stock_ledger_entry.sc_stock_ledger_entry import SCStockLedgerEntry
    return SCStockLedgerEntry.post(
        item=item, warehouse=warehouse, qty_change=flt(qty), batch=batch,
        voucher_type="Manual", voucher_no=f"UC21-{random_string(6)}",
        posting_date=today(), valuation_rate=1000,
    )


def _make_dr(dept, warehouse, items, submit: bool = True, **kwargs):
    """items = list of {item, qty, batch?, approved_qty?, shortage_note?}"""
    dr = frappe.new_doc("SC Dispensing Request")
    dr.request_date = today()
    dr.required_by = today()
    dr.purpose = "Routine"
    dr.department = dept
    dr.from_warehouse = warehouse
    for it in items:
        row = {
            "item": it["item"], "uom": _get_uom(),
            "requested_qty": flt(it["qty"]),
            "approved_qty": flt(it.get("approved_qty", it["qty"])),
        }
        if it.get("batch"):
            row["batch"] = it["batch"]
        if it.get("shortage_note"):
            row["shortage_note"] = it["shortage_note"]
        dr.append("items", row)
    dr.flags.ignore_permissions = True
    for k, v in kwargs.items():
        setattr(dr, k, v)
    dr.insert()
    if submit:
        dr.submit()
    return dr


# ---------- Tests ----------

def test_auto_pick_fefo_fills_batch():
    """auto_pick_fefo_for_dr → batch FEFO fill."""
    dept = _pick_department()
    wh = _pick_warehouse()
    item = _make_item("FEFO1")
    b_near = _make_batch(item.name, 30)
    b_far = _make_batch(item.name, 365)
    _seed_stock(item.name, wh, b_near.name, 50)
    _seed_stock(item.name, wh, b_far.name, 100)
    dr = _make_dr(dept, wh, [{"item": item.name, "qty": 20}], submit=False)
    try:
        dr.auto_pick_fefo_for_dr()
        dr.reload()
        row = dr.items[0]
        ok = (row.batch == b_near.name and abs(flt(row.approved_qty) - 20) < 0.01)
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK fefo picked {b_near.name} qty=20"}
        return {"pass": False, "msg": f"X batch={row.batch} approved={row.approved_qty}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_auto_pick_fefo_partial_shortage():
    """Stock < requested → approved = available, shortage_note set."""
    dept = _pick_department()
    wh = _pick_warehouse()
    item = _make_item("FEFO2")
    b = _make_batch(item.name, 60)
    _seed_stock(item.name, wh, b.name, 30)  # only 30
    dr = _make_dr(dept, wh, [{"item": item.name, "qty": 50}], submit=False)
    try:
        dr.auto_pick_fefo_for_dr()
        dr.reload()
        row = dr.items[0]
        ok = (abs(flt(row.approved_qty) - 30) < 0.01 and row.shortage_note)
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK partial approved=30, note set"}
        return {"pass": False, "msg": f"X approved={row.approved_qty} note={row.shortage_note}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_check_stock_match_ok():
    """DR approved ≤ stock → mismatches=[]."""
    dept = _pick_department()
    wh = _pick_warehouse()
    item = _make_item("MATCH")
    b = _make_batch(item.name, 60)
    _seed_stock(item.name, wh, b.name, 100)
    dr = _make_dr(dept, wh, [{"item": item.name, "qty": 50, "batch": b.name}], submit=True)
    try:
        res = dr.check_stock_match_for_dr()
        frappe.db.rollback()
        if res["ok"]:
            return {"pass": True, "msg": "OK no mismatches"}
        return {"pass": False, "msg": f"X {res}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_check_stock_match_deficit():
    """DR approved > stock → mismatches có deficit."""
    dept = _pick_department()
    wh = _pick_warehouse()
    item = _make_item("DEFIC")
    b = _make_batch(item.name, 60)
    _seed_stock(item.name, wh, b.name, 30)  # only 30
    # Bypass quota for high requested
    frappe.db.set_value("SC Department", dept, "monthly_dispensing_quota", 0)
    dr = _make_dr(dept, wh, [{"item": item.name, "qty": 50, "batch": b.name,
                                "approved_qty": 50}], submit=True)
    try:
        res = dr.check_stock_match_for_dr()
        frappe.db.rollback()
        if not res["ok"] and len(res["mismatches"]) == 1:
            return {"pass": True, "msg": f"OK deficit detected"}
        return {"pass": False, "msg": f"X {res}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_make_stock_entry_blocks_on_mismatch():
    """approved > stock + make_stock_entry → SC-E-DR-STOCK-MISMATCH."""
    dept = _pick_department()
    wh = _pick_warehouse()
    item = _make_item("BLKMM")
    b = _make_batch(item.name, 60)
    _seed_stock(item.name, wh, b.name, 30)
    frappe.db.set_value("SC Department", dept, "monthly_dispensing_quota", 0)
    dr = _make_dr(dept, wh, [{"item": item.name, "qty": 50, "batch": b.name,
                                "approved_qty": 50}], submit=True)
    try:
        try:
            dr.make_stock_entry()
            frappe.db.rollback()
            return {"pass": False, "msg": "X did not throw"}
        except frappe.ValidationError as e:
            msg = str(e)
            frappe.db.rollback()
            if "SC-E-DR-STOCK-MISMATCH" in msg:
                return {"pass": True, "msg": f"OK: {msg[:120]}"}
            return {"pass": False, "msg": f"Wrong error: {msg[:120]}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X setup: {str(e)[:120]}"}


def test_make_stock_entry_succeeds_normal():
    """Đủ stock → SE created OK."""
    dept = _pick_department()
    wh = _pick_warehouse()
    item = _make_item("OK")
    b = _make_batch(item.name, 60)
    _seed_stock(item.name, wh, b.name, 100)
    dr = _make_dr(dept, wh, [{"item": item.name, "qty": 30, "batch": b.name}], submit=True)
    try:
        se_name = dr.make_stock_entry()
        se = frappe.get_doc("SC Stock Entry", se_name)
        ok = (se.entry_type == "Material Issue" and se.docstatus == 0)
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK SE {se_name}"}
        return {"pass": False, "msg": f"X type={se.entry_type} doc={se.docstatus}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_make_stock_entry_sets_status_issued():
    """SE created → DR.status=Issued."""
    dept = _pick_department()
    wh = _pick_warehouse()
    item = _make_item("ISS")
    b = _make_batch(item.name, 60)
    _seed_stock(item.name, wh, b.name, 100)
    dr = _make_dr(dept, wh, [{"item": item.name, "qty": 20, "batch": b.name}], submit=True)
    try:
        dr.make_stock_entry()
        dr.reload()
        ok = (dr.status == "Issued")
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": "OK status=Issued"}
        return {"pass": False, "msg": f"X status={dr.status}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_partial_dispense_with_shortage_note():
    """approved < requested + shortage_note → save OK."""
    dept = _pick_department()
    wh = _pick_warehouse()
    item = _make_item("PART")
    b = _make_batch(item.name, 60)
    _seed_stock(item.name, wh, b.name, 100)
    dr = _make_dr(dept, wh, [{
        "item": item.name, "qty": 50, "batch": b.name,
        "approved_qty": 30,  # partial
        "shortage_note": "Hết hàng tạm thời, cấp 30/50",
    }], submit=False)
    try:
        ok = (dr.items[0].shortage_note == "Hết hàng tạm thời, cấp 30/50"
              and abs(flt(dr.items[0].approved_qty) - 30) < 0.01)
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": "OK partial dispense with note"}
        return {"pass": False, "msg": f"X note={dr.items[0].shortage_note}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_get_dispensing_slip_data():
    """Method trả dict đủ field."""
    dept = _pick_department()
    wh = _pick_warehouse()
    item = _make_item("SLIP")
    b = _make_batch(item.name, 60)
    _seed_stock(item.name, wh, b.name, 100)
    dr = _make_dr(dept, wh, [{"item": item.name, "qty": 10, "batch": b.name}], submit=False)
    try:
        data = dr.get_dispensing_slip_data()
        frappe.db.rollback()
        required = {"name", "barcode", "department", "items", "url"}
        if required.issubset(set(data.keys())) and len(data["items"]) == 1:
            return {"pass": True, "msg": "OK slip data complete"}
        return {"pass": False, "msg": f"X missing: {required - set(data.keys())}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_notify_department_runs_without_error():
    """make_stock_entry → _notify_department không throw."""
    dept = _pick_department()
    # Set head_user nếu chưa có
    if not frappe.db.get_value("SC Department", dept, "head_user"):
        frappe.db.set_value("SC Department", dept, "head_user", "Administrator")
    wh = _pick_warehouse()
    item = _make_item("NOTIFY")
    b = _make_batch(item.name, 60)
    _seed_stock(item.name, wh, b.name, 100)
    dr = _make_dr(dept, wh, [{"item": item.name, "qty": 10, "batch": b.name}], submit=True)
    try:
        dr.make_stock_entry()  # should not throw even if email fails
        frappe.db.rollback()
        return {"pass": True, "msg": "OK make_stock_entry + notify ran"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def run():
    tests = [
        test_auto_pick_fefo_fills_batch,
        test_auto_pick_fefo_partial_shortage,
        test_check_stock_match_ok,
        test_check_stock_match_deficit,
        test_make_stock_entry_blocks_on_mismatch,
        test_make_stock_entry_succeeds_normal,
        test_make_stock_entry_sets_status_issued,
        test_partial_dispense_with_shortage_note,
        test_get_dispensing_slip_data,
        test_notify_department_runs_without_error,
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
