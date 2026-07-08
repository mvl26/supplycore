"""Test GD2 Task 3 -- SC Sales Framework Contract + SFC Item.

Run individual: bench --site supplycore-miyano.local execute supplycore.tests.sc_sfc_test.test_<name>
Run all:        bench --site supplycore-miyano.local execute supplycore.tests.sc_sfc_test.run
"""

import frappe
from frappe.utils import today, add_days, random_string, flt


def _get_uom() -> str:
    return frappe.db.get_value("SC UOM", {}, "name")


def _make_customer(suffix):
    c = frappe.new_doc("SC Customer")
    c.customer_name = f"KH SFC test {suffix}"
    c.tax_code = f"TAX-SFC-{random_string(8)}"
    c.flags.ignore_permissions = True
    c.insert()
    return c


def _make_item(suffix):
    item = frappe.new_doc("SC Item")
    item.item_code = f"SFC-{suffix}-{random_string(5)}"
    item.item_name = f"SFC test item {suffix}"
    item.uom = _get_uom()
    item.is_stock_item = 1
    item.flags.ignore_permissions = True
    item.insert()
    return item


def _make_sfc(customer, items, **kwargs):
    sfc = frappe.new_doc("SC Sales Framework Contract")
    sfc.customer = customer
    sfc.valid_from = today()
    sfc.valid_to = add_days(today(), 365)
    for it in items:
        sfc.append("items", {
            "item": it["item"], "uom": _get_uom(),
            "contract_qty": flt(it["contract_qty"]),
            "unit_price": flt(it["unit_price"]),
        })
    sfc.flags.ignore_permissions = True
    for k, v in kwargs.items():
        setattr(sfc, k, v)
    return sfc


def test_create_submit_sfc():
    """Tao SFC 1 dong (contract_qty=100,unit_price=1000) -> submit -> status Hieu luc, remaining_qty=100."""
    cust = _make_customer("SUBMIT")
    item = _make_item("SUBMIT")
    sfc = _make_sfc(cust.name, [{"item": item.name, "contract_qty": 100, "unit_price": 1000}])
    try:
        sfc.insert()
        sfc.submit()
        sfc.reload()
        ok = (sfc.status == "Hiệu lực" and flt(sfc.items[0].remaining_qty) == 100)
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK {sfc.name} status={sfc.status} remaining={sfc.items[0].remaining_qty}"}
        return {"pass": False, "msg": f"X status={sfc.status} remaining={sfc.items[0].remaining_qty}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:200]}"}


def test_total_value_computed():
    """total_value == Sigma(contract_qty * unit_price) qua nhieu dong."""
    cust = _make_customer("TOTAL")
    item1 = _make_item("TOTAL1")
    item2 = _make_item("TOTAL2")
    sfc = _make_sfc(cust.name, [
        {"item": item1.name, "contract_qty": 100, "unit_price": 1000},
        {"item": item2.name, "contract_qty": 50, "unit_price": 2000},
    ])
    try:
        sfc.insert()
        expected = 100 * 1000 + 50 * 2000
        ok = flt(sfc.total_value) == flt(expected)
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK total_value={sfc.total_value}"}
        return {"pass": False, "msg": f"X total_value={sfc.total_value} expected={expected}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:200]}"}


def run():
    tests = [
        test_create_submit_sfc,
        test_total_value_computed,
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
