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
    # Use a stable offset keyed on the last character of `name` to get distinct WHs
    idx = 0 if name.endswith("A") else 1 if name.endswith("B") else 0
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


def run():
    """Run all UC-05 tests sequentially, return aggregate."""
    tests = [
        test_negative_threshold_rejected,
        test_min_max_inversion_rejected,
        test_valid_thresholds_pass,
        test_child_warehouse_duplicate_rejected,
        test_child_row_inversion_rejected,
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
