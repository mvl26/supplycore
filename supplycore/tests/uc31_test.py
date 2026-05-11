"""Test UC-31 — Investigation.

Run individual: bench --site supplycore execute supplycore.tests.uc31_test.test_<name>
Run all:        bench --site supplycore execute supplycore.tests.uc31_test.run
"""

import frappe
from frappe.utils import today, add_days, random_string, flt, add_to_date


# ---------- Helpers ----------

def _pick_warehouse() -> str:
    rows = frappe.get_all("SC Warehouse", filters={"is_group": 0, "disabled": 0},
                           pluck="name", order_by="name", limit=1)
    return rows[0] if rows else None


def _get_uom() -> str:
    return frappe.db.get_value("SC UOM", {}, "name")


def _make_item(suffix: str):
    item = frappe.new_doc("SC Item")
    item.item_code = f"UC31-{suffix}-{random_string(5)}"
    item.item_name = f"UC-31 test {suffix}"
    item.uom = _get_uom()
    item.is_stock_item = 1
    item.has_batch_no = 0
    item.flags.ignore_permissions = True
    item.insert()
    return item


def _seed_sle(item, warehouse, qty, vtype="Manual"):
    from supplycore.supplycore.doctype.sc_stock_ledger_entry.sc_stock_ledger_entry import SCStockLedgerEntry
    return SCStockLedgerEntry.post(
        item=item, warehouse=warehouse, qty_change=flt(qty),
        valuation_rate=1000,
        voucher_type=vtype, voucher_no=f"UC31-{random_string(6)}",
        posting_date=today(),
    )


def _make_inv_report(item, warehouse, **kwargs):
    inv = frappe.new_doc("SC Investigation Report")
    inv.investigation_date = today()
    inv.investigation_type = kwargs.get("investigation_type", "Stock Loss")
    inv.item = item
    inv.warehouse = warehouse
    inv.period_start = kwargs.get("period_start", add_days(today(), -30))
    inv.period_end = kwargs.get("period_end", today())
    inv.description = kwargs.get("description", "Test investigation")
    if "actual_qty" in kwargs:
        inv.actual_qty = kwargs["actual_qty"]
    inv.flags.ignore_permissions = True
    inv.insert()
    return inv


# ---------- Tests ----------

def test_create_investigation_report_draft():
    """Tạo Draft → status=Draft (no findings)."""
    wh = _pick_warehouse()
    item = _make_item("DRAFT")
    try:
        inv = _make_inv_report(item.name, wh)
        frappe.db.rollback()
        if inv.status == "Draft":
            return {"pass": True, "msg": f"OK status={inv.status}"}
        return {"pass": False, "msg": f"X status={inv.status}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_investigation_requires_scope():
    """Không có item/warehouse/batch → throw SC-E-INV-NO-SCOPE."""
    inv = frappe.new_doc("SC Investigation Report")
    inv.investigation_date = today()
    inv.investigation_type = "Discrepancy"
    inv.period_start = add_days(today(), -10)
    inv.period_end = today()
    inv.flags.ignore_permissions = True
    try:
        inv.insert()
        frappe.db.rollback()
        return {"pass": False, "msg": "X insert thành công không có scope"}
    except frappe.ValidationError as e:
        frappe.db.rollback()
        if "SC-E-INV-NO-SCOPE" in str(e):
            return {"pass": True, "msg": "OK throw SC-E-INV-NO-SCOPE"}
        return {"pass": False, "msg": f"X wrong: {str(e)[:120]}"}


def test_get_audit_trail_filters_by_item():
    """audit_trail trả chỉ SLE của item filter."""
    from supplycore.m10_traceability.api.investigation import get_audit_trail
    wh = _pick_warehouse()
    item1 = _make_item("AT1")
    item2 = _make_item("AT2")
    _seed_sle(item1.name, wh, 100)
    _seed_sle(item2.name, wh, 50)
    try:
        rows = get_audit_trail(item=item1.name, start_date=add_days(today(), -1),
                                end_date=today())
        frappe.db.rollback()
        if all(r["item"] == item1.name for r in rows) and len(rows) >= 1:
            return {"pass": True, "msg": f"OK {len(rows)} rows all item1"}
        return {"pass": False, "msg": f"X items={set(r['item'] for r in rows)}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_compare_theoretical_vs_actual():
    """SLE +100, -30 → theoretical=70."""
    from supplycore.m10_traceability.api.investigation import compare_theoretical_vs_actual
    wh = _pick_warehouse()
    item = _make_item("CMP")
    _seed_sle(item.name, wh, 100)
    _seed_sle(item.name, wh, -30)
    try:
        res = compare_theoretical_vs_actual(item.name, warehouse=wh)
        frappe.db.rollback()
        if abs(flt(res["theoretical_qty"]) - 70) < 0.01:
            return {"pass": True, "msg": f"OK theoretical={res['theoretical_qty']}"}
        return {"pass": False, "msg": f"X theo={res['theoretical_qty']}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_compare_stock_method_updates_variance():
    """inv.compare_stock() sets variance_qty = actual - theoretical."""
    wh = _pick_warehouse()
    item = _make_item("VAR")
    _seed_sle(item.name, wh, 100)
    inv = _make_inv_report(item.name, wh, actual_qty=80)
    try:
        res = inv.compare_stock()
        inv.reload()
        frappe.db.rollback()
        # theoretical=100, actual=80 → variance=-20
        if (abs(flt(res["theoretical_qty"]) - 100) < 0.01
            and abs(flt(res["variance_qty"]) + 20) < 0.01):
            return {"pass": True, "msg": f"OK variance={res['variance_qty']}"}
        return {"pass": False, "msg": f"X res={res}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_detect_anomalies_large_qty_change():
    """SLE qty=10000 → finding type=Large Qty Change."""
    wh = _pick_warehouse()
    item = _make_item("LRG")
    _seed_sle(item.name, wh, 10000)
    inv = _make_inv_report(item.name, wh)
    try:
        res = inv.detect_anomalies(large_qty_threshold=1000)
        inv.reload()
        types = {f.finding_type for f in inv.findings}
        frappe.db.rollback()
        if "Large Qty Change" in types:
            return {"pass": True, "msg": f"OK types={types}"}
        return {"pass": False, "msg": f"X types={types}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_lock_user_disables_account():
    """lock_user(testuser) → User.enabled=0."""
    wh = _pick_warehouse()
    item = _make_item("LCK")
    _seed_sle(item.name, wh, 50)
    # Tạo dummy user
    email = f"uc31-lock-{random_string(6)}@example.com"
    user = frappe.new_doc("User")
    user.email = email
    user.first_name = "UC31"
    user.send_welcome_email = 0
    user.enabled = 1
    user.flags.ignore_permissions = True
    user.insert()
    inv = _make_inv_report(item.name, wh)
    try:
        res = inv.lock_user(user.name, reason="Test fraud detection")
        enabled = frappe.db.get_value("User", user.name, "enabled")
        log = frappe.db.get_value("SC Investigation Report", inv.name, "suspended_users_log")
        frappe.db.rollback()
        if int(enabled or 0) == 0 and "LOCKED" in (log or "") and user.name in (log or ""):
            return {"pass": True, "msg": f"OK locked + logged"}
        return {"pass": False, "msg": f"X enabled={enabled} log={(log or '')[:100]}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_lock_user_rejects_admin():
    """lock_user('Administrator') → throw SC-E-INV-USER-IS-ADMIN."""
    wh = _pick_warehouse()
    item = _make_item("LCKADMIN")
    inv = _make_inv_report(item.name, wh)
    try:
        inv.lock_user("Administrator", reason="should fail")
        frappe.db.rollback()
        return {"pass": False, "msg": "X locked Administrator"}
    except frappe.ValidationError as e:
        frappe.db.rollback()
        if "SC-E-INV-USER-IS-ADMIN" in str(e):
            return {"pass": True, "msg": "OK rejected"}
        return {"pass": False, "msg": f"X wrong: {str(e)[:120]}"}


def test_lock_user_not_found():
    """lock_user user không tồn tại → throw SC-E-INV-USER-NOT-FOUND."""
    wh = _pick_warehouse()
    item = _make_item("LCK404")
    inv = _make_inv_report(item.name, wh)
    try:
        inv.lock_user("nonexist-user-xxx@example.com", reason="should fail")
        frappe.db.rollback()
        return {"pass": False, "msg": "X locked non-existent user"}
    except frappe.ValidationError as e:
        frappe.db.rollback()
        if "SC-E-INV-USER-NOT-FOUND" in str(e):
            return {"pass": True, "msg": "OK rejected"}
        return {"pass": False, "msg": f"X wrong: {str(e)[:120]}"}


def test_create_system_error_adjustment():
    """create_system_error_adjustment(actual=80, theoretical via SLE=100) →
    SR draft với reason 'System Error' và Δ=-20."""
    wh = _pick_warehouse()
    item = _make_item("SE")
    _seed_sle(item.name, wh, 100)
    inv = _make_inv_report(item.name, wh)
    try:
        res = inv.create_system_error_adjustment(actual_qty=80, valuation_rate=1000)
        sr_doc = frappe.get_doc("SC Stock Reconciliation", res["stock_reconciliation"])
        row = sr_doc.items[0] if sr_doc.items else None
        frappe.db.rollback()
        if (row and abs(flt(row.actual_qty) - 80) < 0.01
            and row.reason == "System Error"
            and "Investigation" in (sr_doc.investigation_notes or "")):
            return {"pass": True, "msg": f"OK SR={res['stock_reconciliation']}"}
        return {"pass": False, "msg": f"X reason={row.reason if row else None} notes={(sr_doc.investigation_notes or '')[:60]}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:200]}"}


def test_create_system_error_no_variance():
    """variance=0 → throw SC-E-INV-NO-VARIANCE."""
    wh = _pick_warehouse()
    item = _make_item("NOVAR")
    _seed_sle(item.name, wh, 50)
    inv = _make_inv_report(item.name, wh)
    try:
        inv.create_system_error_adjustment(actual_qty=50, valuation_rate=1000)
        frappe.db.rollback()
        return {"pass": False, "msg": "X allowed adjustment with zero variance"}
    except frappe.ValidationError as e:
        frappe.db.rollback()
        if "SC-E-INV-NO-VARIANCE" in str(e):
            return {"pass": True, "msg": "OK rejected"}
        return {"pass": False, "msg": f"X wrong: {str(e)[:120]}"}


def test_submit_investigation_sets_approved():
    """Submit → status=Resolved, approved_by + approved_at set."""
    wh = _pick_warehouse()
    item = _make_item("SUB")
    _seed_sle(item.name, wh, 100)
    inv = _make_inv_report(item.name, wh)
    inv.conclusion = "No anomalies found"
    inv.recommendation = "Monitor closely"
    inv.save(ignore_permissions=True)
    try:
        inv.submit()
        inv.reload()
        frappe.db.rollback()
        if (inv.status == "Resolved" and inv.approved_by and inv.approved_at):
            return {"pass": True, "msg": f"OK status={inv.status}"}
        return {"pass": False, "msg": f"X status={inv.status} approved_by={inv.approved_by}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:200]}"}


def test_verify_audit_integrity_count():
    """verify_audit_integrity trả version_count cho 1 SLE."""
    from supplycore.m10_traceability.api.investigation import verify_audit_integrity
    wh = _pick_warehouse()
    item = _make_item("AUD")
    sle_name = _seed_sle(item.name, wh, 50)
    try:
        res = verify_audit_integrity("SC Stock Ledger Entry", sle_name)
        frappe.db.rollback()
        if "version_count" in res and "doctype" in res and "docname" in res:
            return {"pass": True, "msg": f"OK count={res['version_count']}"}
        return {"pass": False, "msg": f"X {list(res.keys())}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_get_minutes_data_structure():
    """get_investigation_minutes_data trả đủ keys."""
    wh = _pick_warehouse()
    item = _make_item("MIN")
    _seed_sle(item.name, wh, 100)
    inv = _make_inv_report(item.name, wh)
    try:
        data = inv.get_investigation_minutes_data()
        frappe.db.rollback()
        required = {"name", "scope", "findings", "signatures", "url"}
        if required.issubset(set(data.keys())):
            return {"pass": True, "msg": "OK minutes structure"}
        return {"pass": False, "msg": f"X missing: {required - set(data.keys())}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def run():
    tests = [
        test_create_investigation_report_draft,
        test_investigation_requires_scope,
        test_get_audit_trail_filters_by_item,
        test_compare_theoretical_vs_actual,
        test_compare_stock_method_updates_variance,
        test_detect_anomalies_large_qty_change,
        test_lock_user_disables_account,
        test_lock_user_rejects_admin,
        test_lock_user_not_found,
        test_create_system_error_adjustment,
        test_create_system_error_no_variance,
        test_submit_investigation_sets_approved,
        test_verify_audit_integrity_count,
        test_get_minutes_data_structure,
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
