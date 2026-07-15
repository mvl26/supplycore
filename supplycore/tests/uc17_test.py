"""Test UC-17 — Batch expiry alert + actions.

Run individual: bench --site supplycore execute supplycore.tests.uc17_test.test_<name>
Run all:        bench --site supplycore execute supplycore.tests.uc17_test.run
"""

import frappe
from frappe.utils import today, add_days, random_string, flt


def _pick_warehouse() -> str:
    rows = frappe.get_all("SC Warehouse", filters={"is_group": 0, "disabled": 0},
                           pluck="name", order_by="name", limit=1)
    if not rows:
        frappe.throw("uc17_test: cần seed SC Warehouse")
    return rows[0]


def _get_uom() -> str:
    uom = frappe.db.get_value("SC UOM", {}, "name")
    if not uom:
        frappe.throw("uc17_test: cần seed SC UOM")
    return uom


def _make_item(suffix: str):
    item = frappe.new_doc("SC Item")
    item.item_code = f"UC17-{suffix}-{random_string(5)}"
    item.item_name = f"UC-17 test {suffix}"
    item.uom = _get_uom()
    item.is_stock_item = 1
    item.has_batch_no = 1
    item.flags.ignore_permissions = True
    item.insert()
    return item


def _make_batch(item: str, expiry_offset_days: int):
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
        voucher_type="Manual", voucher_no=f"UC17-{random_string(6)}",
        posting_date=today(),
    )


def _clear_alerts(batch_no):
    frappe.db.delete("Batch Expiry Alert", {"batch_no": batch_no})


# ---------- Tests ----------

def test_scan_critical_severity():
    """Batch expiry+20d → severity=Critical."""
    from supplycore.m5_fefo.api.fefo_picker import scan_expiring_batches
    wh = _pick_warehouse()
    item = _make_item("CRIT")
    b = _make_batch(item.name, 20)
    _seed_stock(item.name, wh, b.name, 50)
    _clear_alerts(b.name)
    try:
        scan_expiring_batches()
        alert = frappe.db.get_value("Batch Expiry Alert",
            {"batch_no": b.name, "warehouse": wh}, "severity")
        frappe.db.rollback()
        if alert == "Critical":
            return {"pass": True, "msg": "OK Critical severity"}
        return {"pass": False, "msg": f"X severity={alert}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_scan_warning_severity():
    """Batch expiry+60d → severity=Warning."""
    from supplycore.m5_fefo.api.fefo_picker import scan_expiring_batches
    wh = _pick_warehouse()
    item = _make_item("WARN")
    b = _make_batch(item.name, 60)
    _seed_stock(item.name, wh, b.name, 50)
    _clear_alerts(b.name)
    try:
        scan_expiring_batches()
        alert = frappe.db.get_value("Batch Expiry Alert",
            {"batch_no": b.name, "warehouse": wh}, "severity")
        frappe.db.rollback()
        if alert == "Warning":
            return {"pass": True, "msg": "OK Warning severity"}
        return {"pass": False, "msg": f"X severity={alert}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_scan_info_severity():
    """Batch expiry+120d → severity=Info."""
    from supplycore.m5_fefo.api.fefo_picker import scan_expiring_batches
    wh = _pick_warehouse()
    item = _make_item("INFO")
    b = _make_batch(item.name, 120)
    _seed_stock(item.name, wh, b.name, 50)
    _clear_alerts(b.name)
    try:
        scan_expiring_batches()
        alert = frappe.db.get_value("Batch Expiry Alert",
            {"batch_no": b.name, "warehouse": wh}, "severity")
        frappe.db.rollback()
        if alert == "Info":
            return {"pass": True, "msg": "OK Info severity"}
        return {"pass": False, "msg": f"X severity={alert}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_scan_skips_no_stock():
    """Batch không có SLE → không tạo alert."""
    from supplycore.m5_fefo.api.fefo_picker import scan_expiring_batches
    item = _make_item("NOSTK")
    b = _make_batch(item.name, 30)  # no SLE
    _clear_alerts(b.name)
    try:
        scan_expiring_batches()
        alerts = frappe.get_all("Batch Expiry Alert", filters={"batch_no": b.name})
        frappe.db.rollback()
        if not alerts:
            return {"pass": True, "msg": "OK no alert for no-stock batch"}
        return {"pass": False, "msg": f"X {len(alerts)} alerts created"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_scan_per_warehouse():
    """Batch ở 2 warehouse → 2 alerts riêng."""
    from supplycore.m5_fefo.api.fefo_picker import scan_expiring_batches
    whs = frappe.get_all("SC Warehouse", filters={"is_group": 0, "disabled": 0},
                          pluck="name", order_by="name", limit=2)
    if len(whs) < 2:
        return {"pass": True, "msg": "OK (skipped: < 2 warehouses)"}
    item = _make_item("PERWH")
    b = _make_batch(item.name, 30)
    _seed_stock(item.name, whs[0], b.name, 20)
    _seed_stock(item.name, whs[1], b.name, 30)
    _clear_alerts(b.name)
    try:
        scan_expiring_batches()
        alerts = frappe.get_all("Batch Expiry Alert",
            filters={"batch_no": b.name},
            fields=["warehouse"])
        warehouses = {a["warehouse"] for a in alerts}
        frappe.db.rollback()
        if whs[0] in warehouses and whs[1] in warehouses:
            return {"pass": True, "msg": f"OK 2 alerts per-warehouse"}
        return {"pass": False, "msg": f"X warehouses={warehouses}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_scan_dedup_within_7d():
    """Scan 2 lần → không tạo duplicate."""
    from supplycore.m5_fefo.api.fefo_picker import scan_expiring_batches
    wh = _pick_warehouse()
    item = _make_item("DEDUP")
    b = _make_batch(item.name, 30)
    _seed_stock(item.name, wh, b.name, 50)
    _clear_alerts(b.name)
    try:
        scan_expiring_batches()
        count1 = frappe.db.count("Batch Expiry Alert", {"batch_no": b.name})
        scan_expiring_batches()
        count2 = frappe.db.count("Batch Expiry Alert", {"batch_no": b.name})
        frappe.db.rollback()
        if count1 == count2 == 1:
            return {"pass": True, "msg": "OK dedup — 1 alert after 2 scans"}
        return {"pass": False, "msg": f"X count1={count1} count2={count2}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_dispose_expired_batch_creates_se():
    """dispose_expired_batch → SE Material Issue submitted."""
    wh = _pick_warehouse()
    item = _make_item("DISP")
    b = _make_batch(item.name, 5)  # near expiry
    _seed_stock(item.name, wh, b.name, 30)
    _clear_alerts(b.name)
    # Tạo alert manual
    alert = frappe.new_doc("Batch Expiry Alert")
    alert.alert_date = today()
    alert.batch_no = b.name
    alert.item_code = item.name
    alert.expiry_date = b.expiry_date
    alert.days_to_expiry = 5
    alert.severity = "Critical"
    alert.warehouse = wh
    alert.current_qty = 30
    alert.flags.ignore_permissions = True
    alert.insert()
    try:
        res = alert.dispose_expired_batch()
        se = frappe.get_doc("SC Stock Entry", res["stock_entry"])
        ok = (se.docstatus == 1 and se.entry_type == "Material Issue"
              and abs(flt(res["qty"]) - 30) < 0.01)
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK SE {se.name} qty=30"}
        return {"pass": False, "msg": f"X doc={se.docstatus} type={se.entry_type} qty={res['qty']}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_dispose_sets_alert_resolved():
    """dispose → alert resolved=1, action=Write Off."""
    wh = _pick_warehouse()
    item = _make_item("DISPR")
    b = _make_batch(item.name, 5)
    _seed_stock(item.name, wh, b.name, 10)
    alert = frappe.new_doc("Batch Expiry Alert")
    alert.alert_date = today()
    alert.batch_no = b.name
    alert.item_code = item.name
    alert.expiry_date = b.expiry_date
    alert.days_to_expiry = 5
    alert.severity = "Critical"
    alert.warehouse = wh
    alert.current_qty = 10
    alert.flags.ignore_permissions = True
    alert.insert()
    try:
        alert.dispose_expired_batch()
        alert.reload()
        ok = (alert.resolved == 1 and alert.resolution_action == "Write Off"
              and alert.resolved_by)
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK resolved by {alert.resolved_by}"}
        return {"pass": False, "msg": f"X resolved={alert.resolved} action={alert.resolution_action}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_dispose_disables_batch():
    """dispose → batch.disabled=1."""
    wh = _pick_warehouse()
    item = _make_item("DISBAT")
    b = _make_batch(item.name, 5)
    _seed_stock(item.name, wh, b.name, 5)
    alert = frappe.new_doc("Batch Expiry Alert")
    alert.alert_date = today()
    alert.batch_no = b.name
    alert.item_code = item.name
    alert.expiry_date = b.expiry_date
    alert.days_to_expiry = 5
    alert.severity = "Critical"
    alert.warehouse = wh
    alert.current_qty = 5
    alert.flags.ignore_permissions = True
    alert.insert()
    try:
        alert.dispose_expired_batch()
        disabled = frappe.db.get_value("SC Batch", b.name, "disabled")
        frappe.db.rollback()
        if disabled == 1:
            return {"pass": True, "msg": "OK batch.disabled=1"}
        return {"pass": False, "msg": f"X disabled={disabled}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_mark_priority_issue():
    """mark_priority_issue → alert.resolved=1, action=Priority Issue."""
    wh = _pick_warehouse()
    item = _make_item("PRIO")
    b = _make_batch(item.name, 30)
    _seed_stock(item.name, wh, b.name, 10)
    alert = frappe.new_doc("Batch Expiry Alert")
    alert.alert_date = today()
    alert.batch_no = b.name
    alert.item_code = item.name
    alert.expiry_date = b.expiry_date
    alert.days_to_expiry = 30
    alert.severity = "Critical"
    alert.warehouse = wh
    alert.current_qty = 10
    alert.flags.ignore_permissions = True
    alert.insert()
    try:
        alert.mark_priority_issue("Cấp ngay tuần sau")
        alert.reload()
        ok = (alert.resolved == 1 and alert.resolution_action == "Priority Issue")
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK marked priority"}
        return {"pass": False, "msg": f"X resolved={alert.resolved} action={alert.resolution_action}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_dashboard_counts_by_severity():
    """3 alerts (Crit/Warn/Info) → dashboard trả counts đúng."""
    from supplycore.api.fefo import get_expiring_dashboard
    wh = _pick_warehouse()
    item = _make_item("DASH")
    for offset, sev_label in ((20, "Critical"), (60, "Warning"), (120, "Info")):
        b = _make_batch(item.name, offset)
        _seed_stock(item.name, wh, b.name, 10)
        a = frappe.new_doc("Batch Expiry Alert")
        a.alert_date = today()
        a.batch_no = b.name
        a.item_code = item.name
        a.expiry_date = b.expiry_date
        a.days_to_expiry = offset
        a.severity = sev_label
        a.warehouse = wh
        a.current_qty = 10
        a.flags.ignore_permissions = True
        a.insert()
    try:
        res = get_expiring_dashboard(warehouse=wh)
        frappe.db.rollback()
        if res["critical"] >= 1 and res["warning"] >= 1 and res["info"] >= 1:
            return {"pass": True, "msg": f"OK counts: {res['critical']}/{res['warning']}/{res['info']}"}
        return {"pass": False, "msg": f"X {res}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_dashboard_filter_warehouse():
    """Filter warehouse → chỉ count alerts của warehouse đó."""
    from supplycore.api.fefo import get_expiring_dashboard
    whs = frappe.get_all("SC Warehouse", filters={"is_group": 0, "disabled": 0},
                          pluck="name", order_by="name", limit=2)
    if len(whs) < 2:
        return {"pass": True, "msg": "OK (skipped: <2 warehouses)"}
    item = _make_item("DASHF")
    b = _make_batch(item.name, 20)
    for wh in whs:
        _seed_stock(item.name, wh, b.name, 5)
        a = frappe.new_doc("Batch Expiry Alert")
        a.alert_date = today()
        a.batch_no = b.name
        a.item_code = item.name
        a.expiry_date = b.expiry_date
        a.days_to_expiry = 20
        a.severity = "Critical"
        a.warehouse = wh
        a.current_qty = 5
        a.flags.ignore_permissions = True
        a.insert()
    try:
        res_wh0 = get_expiring_dashboard(warehouse=whs[0])
        all_batches = res_wh0["batches"]
        warehouses_in_result = {b["warehouse"] for b in all_batches}
        frappe.db.rollback()
        if warehouses_in_result == {whs[0]}:
            return {"pass": True, "msg": f"OK filter only whs[0]"}
        return {"pass": False, "msg": f"X warehouses in result: {warehouses_in_result}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def run():
    tests = [
        test_scan_critical_severity,
        test_scan_warning_severity,
        test_scan_info_severity,
        test_scan_skips_no_stock,
        test_scan_per_warehouse,
        test_scan_dedup_within_7d,
        test_dispose_expired_batch_creates_se,
        test_dispose_sets_alert_resolved,
        test_dispose_disables_batch,
        test_mark_priority_issue,
        test_dashboard_counts_by_severity,
        test_dashboard_filter_warehouse,
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
