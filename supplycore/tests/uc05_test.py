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
    item.uom = frappe.db.get_value("SC UOM", {}, "name") or "Cái"
    item.is_stock_item = 1
    item.is_purchase_item = 1
    item.flags.ignore_permissions = True
    for k, v in kwargs.items():
        setattr(item, k, v)
    return item


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


def run():
    """Run all UC-05 tests sequentially, return aggregate."""
    tests = [test_negative_threshold_rejected]
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
