"""Test UC-34 — Alert Handling.

Run individual: bench --site supplycore execute supplycore.tests.uc34_test.test_<name>
Run all:        bench --site supplycore execute supplycore.tests.uc34_test.run
"""

import frappe
from frappe.utils import now, today, add_days, add_to_date, random_string, flt


def _pick_warehouse():
    return frappe.db.get_value("SC Warehouse",
        {"is_group": 0, "disabled": 0}, "name")


def _make_alert(**kwargs):
    a = frappe.new_doc("SC Alert")
    a.alert_date = kwargs.get("alert_date", now())
    a.alert_type = kwargs.get("alert_type", "low_stock")
    a.severity = kwargs.get("severity", "Warning")
    a.title = kwargs.get("title", f"UC34 test {random_string(5)}")
    a.message = kwargs.get("message", "Test alert")
    if "reference_doctype" in kwargs:
        a.reference_doctype = kwargs["reference_doctype"]
        a.reference_name = kwargs["reference_name"]
    a.flags.ignore_permissions = True
    a.insert()
    return a


# ---------- Tests ----------

def test_mark_resolved_sets_resolved_at():
    a = _make_alert()
    try:
        res = a.mark_resolved(action="Acknowledged", remarks="OK xử lý")
        a.reload()
        frappe.db.rollback()
        if a.resolved == 1 and a.resolved_at and "OK xử lý" in (a.remarks or ""):
            return {"pass": True, "msg": "OK resolved + remarks"}
        return {"pass": False, "msg": f"X resolved={a.resolved} remarks={a.remarks}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_mark_resolved_rejects_double():
    a = _make_alert()
    a.mark_resolved(action="Acknowledged", remarks="first")
    a.reload()
    try:
        a.mark_resolved(action="Acknowledged", remarks="second")
        frappe.db.rollback()
        return {"pass": False, "msg": "X allowed double resolve"}
    except frappe.ValidationError as e:
        frappe.db.rollback()
        if "SC-E-ALERT-RESOLVED" in str(e):
            return {"pass": True, "msg": "OK rejected"}
        return {"pass": False, "msg": f"X wrong: {str(e)[:120]}"}


def test_snooze_alert_sets_until():
    a = _make_alert()
    try:
        res = a.snooze_alert(2, "Đang họp")
        a.reload()
        frappe.db.rollback()
        if a.snooze_until and a.snooze_reason == "Đang họp":
            return {"pass": True, "msg": f"OK snooze_until={a.snooze_until}"}
        return {"pass": False, "msg": f"X until={a.snooze_until} reason={a.snooze_reason}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_snooze_alert_rejects_zero_hours():
    a = _make_alert()
    try:
        a.snooze_alert(0, "test")
        frappe.db.rollback()
        return {"pass": False, "msg": "X allowed 0 hours"}
    except frappe.ValidationError as e:
        frappe.db.rollback()
        if "SC-E-ALERT-SNOOZE-HOURS" in str(e):
            return {"pass": True, "msg": "OK rejected"}
        return {"pass": False, "msg": f"X wrong: {str(e)[:120]}"}


def test_assign_alert_sets_user():
    # Create dummy user
    email = f"uc34-assign-{random_string(5)}@example.com"
    u = frappe.new_doc("User")
    u.email = email; u.first_name = "UC34"
    u.send_welcome_email = 0; u.enabled = 1
    u.flags.ignore_permissions = True
    u.insert()
    a = _make_alert()
    try:
        a.assign_alert(u.name, note="Em xử lý nhé")
        a.reload()
        frappe.db.rollback()
        if a.assigned_to == u.name:
            return {"pass": True, "msg": f"OK assigned_to={u.name}"}
        return {"pass": False, "msg": f"X assigned={a.assigned_to}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_assign_alert_rejects_invalid_user():
    a = _make_alert()
    try:
        a.assign_alert("nope-no-such-user@example.com", note="test")
        frappe.db.rollback()
        return {"pass": False, "msg": "X allowed invalid user"}
    except frappe.ValidationError as e:
        frappe.db.rollback()
        if "SC-E-ALERT-NO-USER" in str(e):
            return {"pass": True, "msg": "OK rejected"}
        return {"pass": False, "msg": f"X wrong: {str(e)[:120]}"}


def test_auto_resolve_low_stock_when_qty_recovered():
    """Item qty >= safety_stock → auto-resolve alert."""
    from supplycore.m11_dashboard.tasks import auto_resolve_alerts
    # Create item with safety_stock=10, give it 50 qty
    item = frappe.new_doc("SC Item")
    item.item_code = f"UC34-LS-{random_string(5)}"
    item.item_name = "UC34 low stock recover"
    item.uom = frappe.db.get_value("SC UOM", {}, "name")
    item.is_stock_item = 1
    item.safety_stock = 10
    item.flags.ignore_permissions = True
    item.insert()
    wh = _pick_warehouse()
    from supplycore.supplycore.doctype.sc_stock_ledger_entry.sc_stock_ledger_entry import SCStockLedgerEntry
    SCStockLedgerEntry.post(item=item.name, warehouse=wh, qty_change=50,
        voucher_type="Manual", voucher_no=f"UC34-{random_string(6)}",
        posting_date=today(), valuation_rate=1000)
    # Create alert
    a = _make_alert(alert_type="low_stock",
                     reference_doctype="SC Item", reference_name=item.name)
    try:
        # Run auto-resolve
        auto_resolve_alerts()
        a.reload()
        frappe.db.rollback()
        if a.resolved == 1 and "Auto-resolved" in (a.remarks or ""):
            return {"pass": True, "msg": "OK auto-resolved"}
        return {"pass": False, "msg": f"X resolved={a.resolved}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_auto_resolve_skip_when_condition_still_holds():
    """Item qty still below safety → KHÔNG auto-resolve."""
    from supplycore.m11_dashboard.tasks import auto_resolve_alerts
    item = frappe.new_doc("SC Item")
    item.item_code = f"UC34-LSH-{random_string(5)}"
    item.item_name = "UC34 low stock holds"
    item.uom = frappe.db.get_value("SC UOM", {}, "name")
    item.is_stock_item = 1
    item.safety_stock = 100  # qty (0) < safety
    item.flags.ignore_permissions = True
    item.insert()
    a = _make_alert(alert_type="low_stock",
                     reference_doctype="SC Item", reference_name=item.name)
    try:
        auto_resolve_alerts()
        a.reload()
        frappe.db.rollback()
        if a.resolved == 0:
            return {"pass": True, "msg": "OK still open"}
        return {"pass": False, "msg": f"X resolved={a.resolved}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_escalate_after_48h():
    """Alert created 50h ago, severity=Warning, resolved=0 → escalated=1."""
    from supplycore.m11_dashboard.tasks import escalate_overdue_alerts
    a = _make_alert(severity="Warning",
                     alert_date=add_to_date(now(), hours=-50))
    # Force alert_date in DB (validate may not touch alert_date)
    frappe.db.set_value("SC Alert", a.name, "alert_date", add_to_date(now(), hours=-50))
    try:
        count = escalate_overdue_alerts(threshold_hours=48)
        a.reload()
        frappe.db.rollback()
        if a.escalated == 1 and a.escalated_to and a.severity == "Critical":
            return {"pass": True, "msg": f"OK escalated, count={count}"}
        return {"pass": False, "msg": f"X escalated={a.escalated} to={a.escalated_to} sev={a.severity}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_escalate_skips_resolved():
    """Resolved alert dù 50h → KHÔNG escalate."""
    from supplycore.m11_dashboard.tasks import escalate_overdue_alerts
    a = _make_alert(severity="Critical")
    frappe.db.set_value("SC Alert", a.name, {
        "alert_date": add_to_date(now(), hours=-50),
        "resolved": 1,
    })
    try:
        escalate_overdue_alerts(threshold_hours=48)
        a.reload()
        frappe.db.rollback()
        if a.escalated == 0:
            return {"pass": True, "msg": "OK skipped resolved"}
        return {"pass": False, "msg": f"X escalated={a.escalated}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_action_priority_dispense_resolves():
    """expiring_batch action → resolution_action=Acted Upon, resolved=1."""
    # Create a batch (simple)
    item = frappe.new_doc("SC Item")
    item.item_code = f"UC34-PD-{random_string(5)}"
    item.item_name = "UC34 priority"
    item.uom = frappe.db.get_value("SC UOM", {}, "name")
    item.is_stock_item = 1
    item.has_batch_no = 1
    item.flags.ignore_permissions = True
    item.insert()
    from supplycore.m5_fefo.api.batch_helpers import generate_batch_id
    batch = frappe.new_doc("SC Batch")
    expiry = add_days(today(), 20)
    batch.batch_id = generate_batch_id(item.name, str(expiry))
    batch.item = item.name
    batch.expiry_date = expiry
    batch.qc_status = "Accepted"
    batch.flags.ignore_permissions = True
    batch.flags.ignore_short_expiry = 1
    batch.insert()
    a = _make_alert(alert_type="expiring_batch",
                     reference_doctype="SC Batch", reference_name=batch.name)
    try:
        a.action_priority_dispense(note="Ưu tiên cho ICU")
        a.reload()
        frappe.db.rollback()
        if (a.resolved == 1 and a.resolution_action == "Acted Upon"
            and "Ưu tiên" in (a.remarks or "")):
            return {"pass": True, "msg": "OK marked priority"}
        return {"pass": False, "msg": f"X resolved={a.resolved} action={a.resolution_action}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_action_contact_supplier_needs_supplier():
    """contact_supplier không có reference → throw."""
    a = _make_alert(alert_type="low_stock")  # no reference
    try:
        a.action_contact_supplier(message="test")
        frappe.db.rollback()
        return {"pass": False, "msg": "X allowed contact without supplier"}
    except Exception as e:
        frappe.db.rollback()
        msg = str(e)
        if "ncc" in msg.lower() or "supplier" in msg.lower() or "không xác định" in msg.lower():
            return {"pass": True, "msg": "OK rejected"}
        return {"pass": False, "msg": f"X wrong: {msg[:120]}"}


def run():
    tests = [
        test_mark_resolved_sets_resolved_at,
        test_mark_resolved_rejects_double,
        test_snooze_alert_sets_until,
        test_snooze_alert_rejects_zero_hours,
        test_assign_alert_sets_user,
        test_assign_alert_rejects_invalid_user,
        test_auto_resolve_low_stock_when_qty_recovered,
        test_auto_resolve_skip_when_condition_still_holds,
        test_escalate_after_48h,
        test_escalate_skips_resolved,
        test_action_priority_dispense_resolves,
        test_action_contact_supplier_needs_supplier,
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
