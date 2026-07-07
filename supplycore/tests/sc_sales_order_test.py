"""Test GD2 Task 4 -- SC Sales Order + SO Item (BRU-SFC-001/002, BRU-SO-001, BRU-AR-001).

Run individual: bench --site supplycore-miyano.local execute supplycore.tests.sc_sales_order_test.test_<name>
Run all:        bench --site supplycore-miyano.local execute supplycore.tests.sc_sales_order_test.run
"""

import frappe
from frappe.utils import today, add_days, random_string, flt


def _get_uom() -> str:
    return frappe.db.get_value("SC UOM", {}, "name")


def _make_customer(suffix, credit_limit=0):
    c = frappe.new_doc("SC Customer")
    c.customer_name = f"KH SO test {suffix}"
    c.tax_code = f"TAX-SO-{random_string(8)}"
    c.credit_limit = flt(credit_limit)
    c.flags.ignore_permissions = True
    c.insert()
    return c


def _make_item(suffix):
    item = frappe.new_doc("SC Item")
    item.item_code = f"SO-{suffix}-{random_string(5)}"
    item.item_name = f"SO test item {suffix}"
    item.uom = _get_uom()
    item.is_stock_item = 1
    item.flags.ignore_permissions = True
    item.insert()
    return item


def _make_submitted_sfc(customer, item, contract_qty, unit_price):
    sfc = frappe.new_doc("SC Sales Framework Contract")
    sfc.customer = customer
    sfc.valid_from = today()
    sfc.valid_to = add_days(today(), 365)
    sfc.append("items", {
        "item": item, "uom": _get_uom(),
        "contract_qty": flt(contract_qty),
        "unit_price": flt(unit_price),
    })
    sfc.flags.ignore_permissions = True
    sfc.insert()
    sfc.submit()
    return sfc


def _make_so(customer, framework_contract, items, **kwargs):
    so = frappe.new_doc("SC Sales Order")
    so.customer = customer
    so.framework_contract = framework_contract
    so.order_date = today()
    for it in items:
        row = {
            "item": it["item"], "uom": _get_uom(),
            "qty": flt(it["qty"]),
        }
        if "unit_price" in it:
            row["unit_price"] = flt(it["unit_price"])
        so.append("items", row)
    so.flags.ignore_permissions = True
    for k, v in kwargs.items():
        setattr(so, k, v)
    return so


# ---------- Tests ----------

def test_price_from_sfc_not_editable():
    """Set line unit_price=9999, qty=10 -> after save, unit_price==1000 (SFC), amount==10000."""
    cust = _make_customer("PRICE")
    item = _make_item("PRICE")
    sfc = _make_submitted_sfc(cust.name, item.name, 100, 1000)
    so = _make_so(cust.name, sfc.name, [{"item": item.name, "qty": 10, "unit_price": 9999}])
    try:
        so.insert()
        ok = (flt(so.items[0].unit_price) == 1000 and flt(so.items[0].amount) == 10000)
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK unit_price={so.items[0].unit_price} amount={so.items[0].amount}"}
        return {"pass": False, "msg": f"X unit_price={so.items[0].unit_price} amount={so.items[0].amount}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:200]}"}


def test_item_not_in_sfc_blocked():
    """SO voi item khong nam trong SFC -> throw BRU-SFC-001."""
    cust = _make_customer("NOTIN")
    item_in = _make_item("NOTIN-IN")
    item_out = _make_item("NOTIN-OUT")
    sfc = _make_submitted_sfc(cust.name, item_in.name, 100, 1000)
    so = _make_so(cust.name, sfc.name, [{"item": item_out.name, "qty": 5}])
    try:
        so.insert()
        frappe.db.rollback()
        return {"pass": False, "msg": "X did not throw"}
    except frappe.ValidationError as e:
        msg = str(e)
        frappe.db.rollback()
        if "BRU-SFC-001" in msg:
            return {"pass": True, "msg": "OK threw BRU-SFC-001"}
        return {"pass": False, "msg": f"X threw wrong msg: {msg[:150]}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw unexpected: {str(e)[:150]}"}


def test_qty_exceeds_remaining_blocked():
    """SO qty=200 (>100 contract_qty) -> throw BRU-SO-001."""
    cust = _make_customer("QTYEXC")
    item = _make_item("QTYEXC")
    sfc = _make_submitted_sfc(cust.name, item.name, 100, 1000)
    so = _make_so(cust.name, sfc.name, [{"item": item.name, "qty": 200}])
    try:
        so.insert()
        frappe.db.rollback()
        return {"pass": False, "msg": "X did not throw"}
    except frappe.ValidationError as e:
        msg = str(e)
        frappe.db.rollback()
        if "BRU-SO-001" in msg:
            return {"pass": True, "msg": "OK threw BRU-SO-001"}
        return {"pass": False, "msg": f"X threw wrong msg: {msg[:150]}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw unexpected: {str(e)[:150]}"}


def test_approve_reduces_remaining():
    """Submit + approve -> SFC Item.remaining_qty == 100-qty; SO status Da duyet."""
    cust = _make_customer("APPROVE")
    item = _make_item("APPROVE")
    sfc = _make_submitted_sfc(cust.name, item.name, 100, 1000)
    so = _make_so(cust.name, sfc.name, [{"item": item.name, "qty": 30}])
    try:
        so.insert()
        so.submit()
        so.approve()
        so.reload()
        sfc.reload()
        remaining = flt(sfc.items[0].remaining_qty)
        ok = (so.status == "Đã duyệt" and remaining == 70)
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK status={so.status} remaining={remaining}"}
        return {"pass": False, "msg": f"X status={so.status} remaining={remaining}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:200]}"}


def test_two_orders_cannot_overcommit_sfc():
    """GD2 review I-2 (BRU-SO-001 TOCTOU): SFC contract_qty=100. Submit SO-A
    qty=70 (ok, remaining_qty van la 100 vi chi cap nhat luc approve()). Submit
    SO-B qty=70 -> phai THROW BRU-SO-001 vi live committed (70 tu A da submit)
    + 70 (B) = 140 > 100, du remaining_qty luu con nguyen la 100."""
    cust = _make_customer("OVERCOMMIT")
    item = _make_item("OVERCOMMIT")
    sfc = _make_submitted_sfc(cust.name, item.name, 100, 1000)
    so_a = _make_so(cust.name, sfc.name, [{"item": item.name, "qty": 70}])
    try:
        so_a.insert()
        so_a.submit()

        so_b = _make_so(cust.name, sfc.name, [{"item": item.name, "qty": 70}])
        try:
            so_b.insert()
            so_b.submit()
            frappe.db.rollback()
            return {"pass": False, "msg": "X SO-B did not throw (over-commit slipped through)"}
        except frappe.ValidationError as e:
            msg = str(e)
            frappe.db.rollback()
            if "BRU-SO-001" in msg:
                return {"pass": True, "msg": "OK SO-B threw BRU-SO-001"}
            return {"pass": False, "msg": f"X threw wrong msg: {msg[:150]}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw unexpected: {str(e)[:200]}"}


def test_credit_limit_exceeded_holds():
    """customer credit_limit=5000, SO total 10000 -> on_submit throws + credit_hold set."""
    cust = _make_customer("CREDIT", credit_limit=5000)
    item = _make_item("CREDIT")
    sfc = _make_submitted_sfc(cust.name, item.name, 100, 1000)
    so = _make_so(cust.name, sfc.name, [{"item": item.name, "qty": 10}])  # total = 10000
    try:
        so.insert()
        so.submit()
        so.reload()
        frappe.db.rollback()
        return {"pass": False, "msg": f"X did not throw, credit_hold={so.credit_hold}"}
    except frappe.ValidationError as e:
        credit_hold_set = flt(so.credit_hold) == 1
        frappe.db.rollback()
        if credit_hold_set:
            return {"pass": True, "msg": f"OK threw + credit_hold set: {str(e)[:120]}"}
        return {"pass": False, "msg": f"X threw but credit_hold not set: {str(e)[:120]}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw unexpected: {str(e)[:150]}"}


def run():
    tests = [
        test_price_from_sfc_not_editable,
        test_item_not_in_sfc_blocked,
        test_qty_exceeds_remaining_blocked,
        test_two_orders_cannot_overcommit_sfc,
        test_approve_reduces_remaining,
        test_credit_limit_exceeded_holds,
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
