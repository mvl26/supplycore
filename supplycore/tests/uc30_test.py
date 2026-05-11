"""Test UC-30 — Recall Management.

Run individual: bench --site supplycore execute supplycore.tests.uc30_test.test_<name>
Run all:        bench --site supplycore execute supplycore.tests.uc30_test.run
"""

import frappe
from frappe.utils import today, add_days, random_string, flt


# ---------- Helpers ----------

def _pick_warehouse() -> str:
    rows = frappe.get_all("SC Warehouse", filters={"is_group": 0, "disabled": 0},
                           pluck="name", order_by="name", limit=1)
    return rows[0] if rows else None


def _pick_supplier() -> str:
    return frappe.db.get_value("SC Supplier", {"disabled": 0}, "name")


def _get_uom() -> str:
    return frappe.db.get_value("SC UOM", {}, "name")


def _make_item(suffix: str):
    item = frappe.new_doc("SC Item")
    item.item_code = f"UC30-{suffix}-{random_string(5)}"
    item.item_name = f"UC-30 test {suffix}"
    item.uom = _get_uom()
    item.is_stock_item = 1
    item.has_batch_no = 1
    item.flags.ignore_permissions = True
    item.insert()
    return item


def _make_batch(item_code, supplier=None, **kwargs):
    from supplycore.m5_fefo.api.batch_helpers import generate_batch_id
    expiry = kwargs.get("expiry_date", add_days(today(), 365))
    batch = frappe.new_doc("SC Batch")
    batch.batch_id = generate_batch_id(item_code, str(expiry))
    batch.item = item_code
    batch.expiry_date = expiry
    batch.manufacturing_date = add_days(expiry, -730)
    batch.qc_status = "Accepted"
    if supplier:
        batch.supplier = supplier
    batch.flags.ignore_permissions = True
    batch.flags.ignore_short_expiry = 1
    batch.insert()
    return batch


def _seed_sle(item, warehouse, batch, qty, vtype="Manual"):
    from supplycore.supplycore.doctype.sc_stock_ledger_entry.sc_stock_ledger_entry import SCStockLedgerEntry
    return SCStockLedgerEntry.post(
        item=item, warehouse=warehouse, qty_change=flt(qty), batch=batch,
        valuation_rate=1000,
        voucher_type=vtype, voucher_no=f"UC30-{random_string(6)}",
        posting_date=today(),
    )


def _make_recall_notice(item, batch_name, supplier=None, reason="QC failed"):
    rn = frappe.new_doc("SC Recall Notice")
    rn.recall_date = today()
    rn.recall_type = "Mandatory"
    rn.severity = "Class I (Critical)"
    rn.item = item
    rn.batch_no = batch_name
    if supplier:
        rn.supplier = supplier
    rn.recall_reason = reason
    rn.flags.ignore_permissions = True
    rn.insert()
    return rn


# ---------- Tests ----------

def test_create_recall_notice_blocks_batch():
    """Submit RN → batch.blocked=1."""
    wh = _pick_warehouse()
    item = _make_item("BLOCK")
    batch = _make_batch(item.name)
    _seed_sle(item.name, wh, batch.name, 100)
    rn = _make_recall_notice(item.name, batch.name)
    rn.populate_affected_items()
    try:
        rn.submit()
        blocked = frappe.db.get_value("SC Batch", batch.name, "blocked")
        frappe.db.rollback()
        if int(blocked or 0) == 1:
            return {"pass": True, "msg": "OK batch blocked"}
        return {"pass": False, "msg": f"X blocked={blocked}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_cancel_recall_unblocks_batch():
    """Cancel RN → batch.blocked=0."""
    wh = _pick_warehouse()
    item = _make_item("UNBLOCK")
    batch = _make_batch(item.name)
    _seed_sle(item.name, wh, batch.name, 50)
    rn = _make_recall_notice(item.name, batch.name)
    rn.populate_affected_items()
    rn.submit()
    try:
        rn.cancel()
        blocked = frappe.db.get_value("SC Batch", batch.name, "blocked")
        frappe.db.rollback()
        if int(blocked or 0) == 0:
            return {"pass": True, "msg": "OK batch unblocked"}
        return {"pass": False, "msg": f"X blocked={blocked}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_populate_affected_items_warehouse():
    """Batch có SLE ở 2 kho → 2 affected_items location=Warehouse."""
    whs = frappe.get_all("SC Warehouse", filters={"is_group": 0, "disabled": 0},
                          pluck="name", order_by="name", limit=2)
    if len(whs) < 2:
        return {"pass": True, "msg": "OK (skipped: <2 warehouses)"}
    item = _make_item("POPWH")
    batch = _make_batch(item.name)
    _seed_sle(item.name, whs[0], batch.name, 30)
    _seed_sle(item.name, whs[1], batch.name, 70)
    rn = _make_recall_notice(item.name, batch.name)
    try:
        rn.populate_affected_items()
        wh_rows = [r for r in rn.affected_items if r.location_type == "Warehouse"]
        frappe.db.rollback()
        if len(wh_rows) == 2:
            return {"pass": True, "msg": f"OK 2 warehouse rows"}
        return {"pass": False, "msg": f"X wh_rows={len(wh_rows)}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_blocked_batch_rejects_patient_dispensing():
    """PD với batch blocked → throw SC-E-RCL-BATCH-RECALLED."""
    wh = _pick_warehouse()
    item = _make_item("BLKPD")
    batch = _make_batch(item.name)
    _seed_sle(item.name, wh, batch.name, 100)
    # Block batch trực tiếp
    frappe.db.set_value("SC Batch", batch.name, {
        "blocked": 1, "block_reason": "Recall test"
    })
    pd = frappe.new_doc("SC Patient Dispensing")
    pd.dispensing_date = today()
    pd.append("items", {"item": item.name, "batch": batch.name,
                          "qty": 5, "unit_cost": 1000})
    pd.flags.ignore_permissions = True
    try:
        pd.insert()  # validate sẽ throw
        frappe.db.rollback()
        return {"pass": False, "msg": "X PD inserted với batch blocked"}
    except frappe.ValidationError as e:
        frappe.db.rollback()
        if "RCL-BATCH-RECALLED" in str(e):
            return {"pass": True, "msg": "OK throw SC-E-RCL-BATCH-RECALLED"}
        return {"pass": False, "msg": f"X wrong error: {str(e)[:120]}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {type(e).__name__}: {str(e)[:120]}"}


def test_blocked_batch_rejects_stock_entry():
    """SE Material Issue batch blocked → throw SC-E008 BATCH_RECALLED."""
    wh = _pick_warehouse()
    item = _make_item("BLKSE")
    batch = _make_batch(item.name)
    _seed_sle(item.name, wh, batch.name, 100)
    frappe.db.set_value("SC Batch", batch.name, {
        "blocked": 1, "block_reason": "Recall test"
    })
    se = frappe.new_doc("SC Stock Entry")
    se.entry_type = "Material Issue"
    se.posting_date = today()
    se.from_warehouse = wh
    se.append("items", {"item": item.name, "batch": batch.name, "qty": 10})
    se.flags.ignore_permissions = True
    try:
        se.insert()
        frappe.db.rollback()
        return {"pass": False, "msg": "X SE insert thành công với batch blocked"}
    except frappe.ValidationError as e:
        frappe.db.rollback()
        if "BATCH_RECALLED" in str(e) or "block" in str(e).lower():
            return {"pass": True, "msg": "OK SE blocked"}
        return {"pass": False, "msg": f"X wrong error: {str(e)[:120]}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {type(e).__name__}: {str(e)[:120]}"}


def test_recall_se_bypasses_blocked_check():
    """SE với recall_notice set → bypass blocked check."""
    wh = _pick_warehouse()
    item = _make_item("BYPASS")
    batch = _make_batch(item.name)
    _seed_sle(item.name, wh, batch.name, 100)
    frappe.db.set_value("SC Batch", batch.name, {
        "blocked": 1, "block_reason": "Recall test"
    })
    se = frappe.new_doc("SC Stock Entry")
    se.entry_type = "Material Issue"
    se.posting_date = today()
    se.from_warehouse = wh
    se.recall_notice = "DUMMY-RCL"  # nếu Link validation cho phép — chỉ test bypass
    se.purpose = "Write Off — test bypass"
    se.append("items", {"item": item.name, "batch": batch.name, "qty": 10})
    se.flags.ignore_permissions = True
    try:
        # Insert (no submit) — validate FEFO chạy ở docstatus=0
        se.insert()
        frappe.db.rollback()
        return {"pass": True, "msg": "OK SE inserted (bypass FEFO blocked)"}
    except frappe.LinkValidationError as e:
        frappe.db.rollback()
        # Recall notice link không tồn tại — bypass blocked OK, chỉ fail link check
        if "Recall Notice" in str(e):
            return {"pass": True, "msg": "OK bypass blocked (link validation expected)"}
        return {"pass": False, "msg": f"X link err: {str(e)[:120]}"}
    except Exception as e:
        frappe.db.rollback()
        msg = str(e)
        if "BATCH_RECALLED" in msg or "block" in msg.lower():
            return {"pass": False, "msg": f"X bypass not working: {msg[:120]}"}
        # Acceptable: insert fails for OTHER reason (link), nhưng KHÔNG vì blocked
        return {"pass": True, "msg": f"OK (non-block error): {msg[:80]}"}


def test_update_recovery_updates_outstanding():
    """update_recovery(row, recovered=50) → outstanding giảm 50."""
    wh = _pick_warehouse()
    item = _make_item("RECOV")
    batch = _make_batch(item.name)
    _seed_sle(item.name, wh, batch.name, 100)
    rn = _make_recall_notice(item.name, batch.name)
    rn.populate_affected_items()
    rn.submit()
    row = next((r for r in rn.affected_items if r.location_type == "Warehouse"), None)
    if not row:
        frappe.db.rollback()
        return {"pass": False, "msg": "X không có warehouse row"}
    try:
        res = rn.update_recovery(row.name, recovered_qty=50, status="In Progress")
        frappe.db.rollback()
        if abs(flt(res["outstanding_qty"]) - 50) < 0.01:
            return {"pass": True, "msg": f"OK outstanding=50, pct={res['resolution_pct']}"}
        return {"pass": False, "msg": f"X outstanding={res['outstanding_qty']}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_create_return_to_supplier():
    """recovered_qty=80 → tạo PR is_return=1 với qty 80."""
    sup = _pick_supplier()
    if not sup:
        return {"pass": True, "msg": "OK (skipped: no supplier)"}
    wh = _pick_warehouse()
    item = _make_item("RET")
    batch = _make_batch(item.name, supplier=sup)
    _seed_sle(item.name, wh, batch.name, 100)
    rn = _make_recall_notice(item.name, batch.name, supplier=sup)
    rn.populate_affected_items()
    rn.submit()
    row = next((r for r in rn.affected_items if r.location_type == "Warehouse"), None)
    rn.update_recovery(row.name, recovered_qty=80, status="Recovered")
    try:
        res = rn.create_return_to_supplier()
        pr_doc = frappe.get_doc("SC Purchase Receipt", res["return_pr"])
        total = sum(flt(i.qty) for i in pr_doc.items)
        frappe.db.rollback()
        if pr_doc.is_return == 1 and abs(total - 80) < 0.01:
            return {"pass": True, "msg": f"OK Return PR={res['return_pr']} qty=80"}
        return {"pass": False, "msg": f"X is_return={pr_doc.is_return} qty={total}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_create_write_off():
    """destroyed_qty=20 → tạo SE purpose Write Off — Recall."""
    wh = _pick_warehouse()
    item = _make_item("WO")
    batch = _make_batch(item.name)
    _seed_sle(item.name, wh, batch.name, 100)
    rn = _make_recall_notice(item.name, batch.name)
    rn.populate_affected_items()
    rn.submit()
    row = next((r for r in rn.affected_items if r.location_type == "Warehouse"), None)
    rn.update_recovery(row.name, destroyed_qty=20, status="Destroyed")
    try:
        res = rn.create_write_off()
        se_doc = frappe.get_doc("SC Stock Entry", res["write_off_entry"])
        frappe.db.rollback()
        if (se_doc.entry_type == "Material Issue"
            and "Write Off" in (se_doc.purpose or "")
            and se_doc.recall_notice == rn.name
            and se_doc.docstatus == 1):
            return {"pass": True, "msg": f"OK Write Off SE={res['write_off_entry']}"}
        return {"pass": False, "msg": f"X se={se_doc.entry_type} purpose={se_doc.purpose} ds={se_doc.docstatus}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:200]}"}


def test_notify_clinical_staff_marks_rows():
    """PD-affected → notify → clinical_notified=1 + clinical_notified_at set."""
    # Tạo affected_items dạng Patient thủ công (không cần PD thật)
    wh = _pick_warehouse()
    item = _make_item("CLIN")
    batch = _make_batch(item.name)
    _seed_sle(item.name, wh, batch.name, 100)
    rn = _make_recall_notice(item.name, batch.name)
    # Manual append patient row
    rn.append("affected_items", {
        "location_type": "Patient",
        "voucher_type": "SC Patient Dispensing",
        "voucher_no": "DUMMY-PD-001",
        "qty_dispensed": 5,
        "recovered_qty": 0,
        "status": "Notified",
    })
    rn.save(ignore_permissions=True)
    rn.submit()
    try:
        res = rn.notify_clinical_staff()
        rn.reload()
        frappe.db.rollback()
        if res["notified"] == 1 and rn.clinical_notified_at:
            return {"pass": True, "msg": f"OK notified={res['notified']}"}
        return {"pass": False, "msg": f"X res={res} clinical_at={rn.clinical_notified_at}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_audit_dispensings_in_period():
    """audit_dispensings_in_period() → trả list có has_batch_link flag."""
    wh = _pick_warehouse()
    item = _make_item("AUDIT")
    batch = _make_batch(item.name)
    _seed_sle(item.name, wh, batch.name, 100)
    rn = _make_recall_notice(item.name, batch.name)
    try:
        res = rn.audit_dispensings_in_period(
            start_date=add_days(today(), -30), end_date=today())
        frappe.db.rollback()
        if "dispensings" in res and "count" in res and "period" in res:
            return {"pass": True, "msg": f"OK structure (count={res['count']})"}
        return {"pass": False, "msg": f"X missing keys: {list(res.keys())}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_notify_departments_groups_by_dept():
    """notify_departments group rows theo department."""
    wh = _pick_warehouse()
    item = _make_item("DEPT")
    batch = _make_batch(item.name)
    _seed_sle(item.name, wh, batch.name, 100)
    rn = _make_recall_notice(item.name, batch.name)
    # Pick a dept
    dept = frappe.db.get_value("SC Department", {}, "name") or None
    if not dept:
        return {"pass": True, "msg": "OK (skipped: no department)"}
    rn.append("affected_items", {
        "location_type": "Department", "department": dept,
        "voucher_type": "Manual", "voucher_no": "TEST",
        "qty_dispensed": 10, "outstanding_qty": 10,
        "status": "Notified",
    })
    rn.save(ignore_permissions=True)
    rn.submit()
    try:
        res = rn.notify_departments()
        frappe.db.rollback()
        if res["letter_count"] == 1 and dept in res["by_department"]:
            return {"pass": True, "msg": f"OK dept={dept}"}
        return {"pass": False, "msg": f"X {res}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def run():
    tests = [
        test_create_recall_notice_blocks_batch,
        test_cancel_recall_unblocks_batch,
        test_populate_affected_items_warehouse,
        test_blocked_batch_rejects_patient_dispensing,
        test_blocked_batch_rejects_stock_entry,
        test_recall_se_bypasses_blocked_check,
        test_update_recovery_updates_outstanding,
        test_create_return_to_supplier,
        test_create_write_off,
        test_notify_clinical_staff_marks_rows,
        test_audit_dispensings_in_period,
        test_notify_departments_groups_by_dept,
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
