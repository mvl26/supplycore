"""Test UC-05 — Min/Max/Reorder Level scenarios.

Run individual: bench --site supplycore execute supplycore.tests.uc05_test.test_<name>
Run all:        bench --site supplycore execute supplycore.tests.uc05_test.run
"""

import frappe
from frappe.utils import random_string


def _make_item(suffix: str, **kwargs) -> "frappe.model.document.Document":
    """Helper: build a draft SC Item with required fields, do not insert yet."""
    item = frappe.new_doc("SC Item")
    item.item_code = f"UC05-{suffix}-{random_string(5)}"
    item.item_name = f"UC-05 test {suffix}"
    uom_name = frappe.db.get_value("SC UOM", {}, "name")
    if not uom_name:
        frappe.throw("_make_item: không tìm thấy SC UOM nào — chạy seed trước")
    item.uom = uom_name
    item.is_stock_item = 1
    item.is_purchase_item = 1
    item.flags.ignore_permissions = True
    for k, v in kwargs.items():
        setattr(item, k, v)
    return item


def _ensure_test_warehouse(name: str) -> str:
    """Return a real SC Warehouse name for tests.

    SC Warehouse is a NestedSet without lft/rgt columns — inserting test rows
    fails in the nestedset hook. Instead we reuse a seeded warehouse: try to
    find one whose warehouse_name matches `name` exactly, then fall back to any
    non-group, non-disabled warehouse. Returns the doctype primary key (name).
    """
    existing = frappe.db.get_value("SC Warehouse", {"warehouse_name": name}, "name")
    if existing:
        return existing
    # Fall back to any real warehouse; the helper is called with distinct labels
    # ("UC05 Test WH A", "B") so if two different fallbacks exist, pick offset.
    all_wh = frappe.db.get_all(
        "SC Warehouse",
        filters={"is_group": 0, "disabled": 0},
        fields=["name"],
        order_by="name asc",
        limit=10,
    )
    if not all_wh:
        frappe.throw("_ensure_test_warehouse: không tìm thấy SC Warehouse nào — chạy seed trước")
    if len(all_wh) < 2:
        frappe.throw("_ensure_test_warehouse: cần ≥2 SC Warehouse trong seed (hiện chỉ có 1)")
    # Use a stable offset keyed on the last character of `name` to get distinct WHs
    # A=0, B=1, C=2, D=3, etc. (letter→index)
    last_char = name[-1].upper()
    idx = ord(last_char) - ord("A") if last_char.isalpha() else 0
    idx = min(idx, len(all_wh) - 1)
    return all_wh[idx]["name"]


def test_negative_threshold_rejected():
    """safety_stock=-1 → throw SC-E-NEGATIVE."""
    item = _make_item("NEG", safety_stock=-1)
    try:
        item.insert()
        return {"pass": False, "msg": "X did not throw on negative safety_stock"}
    except frappe.ValidationError as e:
        msg = str(e)
        if "SC-E-NEGATIVE" in msg:
            return {"pass": True, "msg": f"OK: {msg[:120]}"}
        return {"pass": False, "msg": f"Wrong error code: {msg[:120]}"}


def test_min_max_inversion_rejected():
    """safety=10, reorder=5, max=20 → throw SC-E-MIN-MAX."""
    item = _make_item("INV", safety_stock=10, reorder_level=5, max_stock=20)
    try:
        item.insert()
        return {"pass": False, "msg": "X did not throw on safety>reorder"}
    except frappe.ValidationError as e:
        msg = str(e)
        if "SC-E-MIN-MAX" in msg:
            return {"pass": True, "msg": f"OK: {msg[:120]}"}
        return {"pass": False, "msg": f"Wrong error: {msg[:120]}"}


def test_valid_thresholds_pass():
    """safety=5, reorder=10, max=20 → save OK."""
    item = _make_item("OK", safety_stock=5, reorder_level=10, max_stock=20)
    try:
        item.insert()
        frappe.db.rollback()
        return {"pass": True, "msg": f"OK item {item.name} saved"}
    except Exception as e:
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_child_warehouse_duplicate_rejected():
    """2 row override cùng warehouse → throw SC-E-DUPLICATE-WAREHOUSE."""
    wh = _ensure_test_warehouse("UC05 Test WH A")
    item = _make_item("DUP")
    item.append("reorder_levels", {"warehouse": wh, "safety_stock": 5})
    item.append("reorder_levels", {"warehouse": wh, "safety_stock": 10})
    try:
        item.insert()
        return {"pass": False, "msg": "X did not throw on duplicate warehouse"}
    except frappe.ValidationError as e:
        msg = str(e)
        if "SC-E-DUPLICATE-WAREHOUSE" in msg:
            return {"pass": True, "msg": f"OK: {msg[:120]}"}
        return {"pass": False, "msg": f"Wrong error: {msg[:120]}"}


def test_child_row_inversion_rejected():
    """Row safety=10, reorder=5, max=20 → throw SC-E-MIN-MAX."""
    wh = _ensure_test_warehouse("UC05 Test WH B")
    item = _make_item("ROWINV")
    item.append("reorder_levels", {
        "warehouse": wh, "safety_stock": 10,
        "reorder_level": 5, "max_stock": 20,
    })
    try:
        item.insert()
        return {"pass": False, "msg": "X did not throw on row safety>reorder"}
    except frappe.ValidationError as e:
        msg = str(e)
        if "SC-E-MIN-MAX" in msg:
            return {"pass": True, "msg": f"OK: {msg[:120]}"}
        return {"pass": False, "msg": f"Wrong error: {msg[:120]}"}


def test_lead_time_zero_warns_not_throws():
    """lead_time_days=0 → save OK (msgprint warning, no throw)."""
    item = _make_item("LT0", lead_time_days=0)
    try:
        item.insert()
        frappe.db.rollback()
        return {"pass": True, "msg": f"OK item {item.name} saved with lead_time=0"}
    except frappe.ValidationError as e:
        return {"pass": False, "msg": f"X threw on lead_time=0: {str(e)[:120]}"}


def test_get_reorder_thresholds_item_fallback():
    """No override → return item-level values."""
    from supplycore.m2_planning.reorder import get_reorder_thresholds
    item = _make_item("FB", safety_stock=10, reorder_level=15,
                      max_stock=30, standard_order_qty=20, lead_time_days=7)
    item.insert()
    result = get_reorder_thresholds(item.name)
    frappe.db.rollback()
    expected = {"safety_stock": 10, "reorder_level": 15, "max_stock": 30,
                "standard_order_qty": 20, "lead_time_days": 7}
    for k, v in expected.items():
        if float(result.get(k, -1)) != float(v):
            return {"pass": False, "msg": f"X {k}: expected {v}, got {result.get(k)}"}
    return {"pass": True, "msg": f"OK fallback returns item-level: {result}"}


def test_get_reorder_thresholds_full_override():
    """Override row > 0 cho mọi field → return override values."""
    from supplycore.m2_planning.reorder import get_reorder_thresholds
    wh = _ensure_test_warehouse("UC05 Test WH C")
    item = _make_item("FULL", safety_stock=10, reorder_level=15, max_stock=30)
    item.append("reorder_levels", {
        "warehouse": wh, "safety_stock": 50, "reorder_level": 70,
        "max_stock": 100, "standard_order_qty": 25,
    })
    item.insert()
    result = get_reorder_thresholds(item.name, warehouse=wh)
    frappe.db.rollback()
    if (float(result["safety_stock"]) == 50.0
        and float(result["reorder_level"]) == 70.0
        and float(result["max_stock"]) == 100.0
        and float(result["standard_order_qty"]) == 25.0):
        return {"pass": True, "msg": f"OK full override: {result}"}
    return {"pass": False, "msg": f"X mismatch: {result}"}


def test_get_reorder_thresholds_partial_override():
    """Override row chỉ set safety_stock; reorder_level/max_stock=0 →
       fallback item-level cho field bỏ trống."""
    from supplycore.m2_planning.reorder import get_reorder_thresholds
    wh = _ensure_test_warehouse("UC05 Test WH D")
    item = _make_item("PART", safety_stock=10, reorder_level=15, max_stock=30)
    item.append("reorder_levels", {"warehouse": wh, "safety_stock": 99})
    item.insert()
    result = get_reorder_thresholds(item.name, warehouse=wh)
    frappe.db.rollback()
    if (float(result["safety_stock"]) == 99.0
        and float(result["reorder_level"]) == 15.0
        and float(result["max_stock"]) == 30.0):
        return {"pass": True, "msg": f"OK partial override: {result}"}
    return {"pass": False, "msg": f"X mismatch: {result}"}


def _ensure_low_stock_rule():
    """Get or create an active SC Alert Rule for low_stock."""
    existing = frappe.db.exists("SC Alert Rule", {"alert_type": "low_stock", "enabled": 1})
    if existing:
        return frappe.get_doc("SC Alert Rule", existing)
    rule = frappe.new_doc("SC Alert Rule")
    rule.title = "UC-05 Low Stock Test"
    rule.alert_type = "low_stock"
    rule.severity = "Warning"
    rule.enabled = 1
    rule.flags.ignore_permissions = True
    rule.insert()
    return rule


def test_low_stock_alert_per_warehouse():
    """Item có override WH-X safety=50, qty WH-X=30 → alert chỉ tạo cho (item, WH-X)."""
    from supplycore.m11_dashboard.tasks import _scan_low_stock
    from frappe.utils import today

    wh_a = _ensure_test_warehouse("UC05 Alert WH A")
    wh_b = _ensure_test_warehouse("UC05 Alert WH B")
    item = _make_item("ALERTWH", safety_stock=0)  # item-level=0, only override matters
    item.append("reorder_levels", {"warehouse": wh_a, "safety_stock": 50})
    item.insert()

    # Seed SLE: WH-A has 30 (below safety 50), WH-B has 200 (no override)
    from supplycore.supplycore.doctype.sc_stock_ledger_entry.sc_stock_ledger_entry import SCStockLedgerEntry
    for (wh, qty) in [(wh_a, 30), (wh_b, 200)]:
        SCStockLedgerEntry.post(
            item=item.name, warehouse=wh, qty_change=qty,
            voucher_type="Stock Entry", voucher_no=f"UC05-ALERTWH-{wh[-4:]}",
            posting_date=today(),
        )

    frappe.db.delete("SC Alert", {"reference_doctype": "SC Item", "reference_name": item.name})

    rule = _ensure_low_stock_rule()
    rule_proxy = frappe._dict({
        "name": rule.name, "alert_type": "low_stock", "severity": "Warning"
    })
    _scan_low_stock(rule_proxy)
    alerts = frappe.get_all("SC Alert",
        filters={"reference_doctype": "SC Item", "reference_name": item.name, "resolved": 0},
        fields=["message"])
    frappe.db.rollback()

    if len(alerts) == 1 and wh_a in alerts[0].message:
        return {"pass": True, "msg": f"OK 1 alert for WH-A only: {alerts[0].message[:120]}"}
    return {"pass": False, "msg": f"X expected 1 alert {wh_a}, got {len(alerts)}: {[a.message[:60] for a in alerts]}"}


def test_low_stock_alert_item_level_regression():
    """Item KHÔNG có override + safety_stock=10 + qty=5 → alert tạo (logic cũ)."""
    from supplycore.m11_dashboard.tasks import _scan_low_stock
    from frappe.utils import today

    wh = _ensure_test_warehouse("UC05 Alert WH E")
    item = _make_item("ALERTLEG", safety_stock=10)  # no override rows
    item.insert()

    from supplycore.supplycore.doctype.sc_stock_ledger_entry.sc_stock_ledger_entry import SCStockLedgerEntry
    SCStockLedgerEntry.post(
        item=item.name, warehouse=wh, qty_change=5,
        voucher_type="Stock Entry", voucher_no="UC05-ALERTLEG-TEST",
        posting_date=today(),
    )

    frappe.db.delete("SC Alert", {"reference_doctype": "SC Item", "reference_name": item.name})
    rule = _ensure_low_stock_rule()
    rule_proxy = frappe._dict({
        "name": rule.name, "alert_type": "low_stock", "severity": "Warning"
    })
    _scan_low_stock(rule_proxy)
    alerts = frappe.get_all("SC Alert",
        filters={"reference_doctype": "SC Item", "reference_name": item.name, "resolved": 0},
        fields=["message"])
    frappe.db.rollback()

    if len(alerts) == 1 and "@ " not in alerts[0].message:
        return {"pass": True, "msg": f"OK item-level alert: {alerts[0].message[:120]}"}
    return {"pass": False, "msg": f"X expected 1 item-level alert, got {len(alerts)}"}


def run():
    """Run all UC-05 tests sequentially, return aggregate."""
    tests = [
        test_negative_threshold_rejected,
        test_min_max_inversion_rejected,
        test_valid_thresholds_pass,
        test_child_warehouse_duplicate_rejected,
        test_child_row_inversion_rejected,
        test_lead_time_zero_warns_not_throws,
        test_get_reorder_thresholds_item_fallback,
        test_get_reorder_thresholds_full_override,
        test_get_reorder_thresholds_partial_override,
        test_low_stock_alert_per_warehouse,
        test_low_stock_alert_item_level_regression,
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
