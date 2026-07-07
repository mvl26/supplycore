"""Test GD2 Task 6 -- SC Acceptance Record (nghiệm thu).

Run individual: bench --site supplycore-miyano.local execute supplycore.tests.sc_acceptance_test.test_<name>
Run all:        bench --site supplycore-miyano.local execute supplycore.tests.sc_acceptance_test.run
"""

import frappe
from frappe.utils import today, add_days, random_string, flt

from supplycore.supplycore.doctype.sc_stock_ledger_entry.sc_stock_ledger_entry import SCStockLedgerEntry


def _get_uom() -> str:
    return frappe.db.get_value("SC UOM", {}, "name")


def _pick_warehouse() -> str:
    rows = frappe.get_all("SC Warehouse", filters={"is_group": 0, "disabled": 0},
                           pluck="name", order_by="name", limit=1)
    if not rows:
        frappe.throw("sc_acceptance_test: cần seed SC Warehouse")
    return rows[0]


def _make_customer(suffix, credit_limit=0):
    c = frappe.new_doc("SC Customer")
    c.customer_name = f"KH AR test {suffix}"
    c.tax_code = f"TAX-AR-{random_string(8)}"
    c.credit_limit = flt(credit_limit)
    c.flags.ignore_permissions = True
    c.insert()
    return c


def _make_item(suffix):
    item = frappe.new_doc("SC Item")
    item.item_code = f"AR-{suffix}-{random_string(5)}"
    item.item_name = f"AR test item {suffix}"
    item.uom = _get_uom()
    item.is_stock_item = 1
    item.has_batch_no = 1
    item.flags.ignore_permissions = True
    item.insert()
    return item


def _make_batch(item, expiry_date, qc_status="Accepted"):
    b = frappe.new_doc("SC Batch")
    b.batch_id = f"{item}-{random_string(6)}"
    b.item = item
    b.expiry_date = expiry_date
    b.manufacturing_date = add_days(expiry_date, -365)
    b.qc_status = qc_status
    b.flags.ignore_permissions = True
    b.flags.ignore_short_expiry = True
    b.insert()
    return b


def _seed_stock(item, warehouse, batch, qty, rate=1000):
    SCStockLedgerEntry.post(
        item=item, warehouse=warehouse, qty_change=flt(qty),
        voucher_type="SC Purchase Receipt", voucher_no=f"TEST-IN-{random_string(6)}",
        batch=batch, valuation_rate=rate,
    )


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


def _make_approved_so(customer, item, qty, unit_price=1000, contract_qty=1000):
    sfc = _make_submitted_sfc(customer, item, contract_qty, unit_price)
    so = frappe.new_doc("SC Sales Order")
    so.customer = customer
    so.framework_contract = sfc.name
    so.order_date = today()
    so.append("items", {"item": item, "uom": _get_uom(), "qty": flt(qty)})
    so.flags.ignore_permissions = True
    so.insert()
    so.submit()
    so.approve()
    so.reload()
    return so


def _make_delivered_dn(suffix, qty=30):
    """Xây chuỗi customer→SFC→SO(duyệt)→DN(submit) -> trả về DN đã 'Đã giao'."""
    cust = _make_customer(suffix)
    item = _make_item(suffix)
    wh = _pick_warehouse()
    batch = _make_batch(item.name, add_days(today(), 200))
    _seed_stock(item.name, wh, batch.name, 100)
    so = _make_approved_so(cust.name, item.name, qty)
    dn = frappe.new_doc("SC Delivery Note")
    dn.sales_order = so.name
    dn.from_warehouse = wh
    dn.delivery_date = today()
    dn.append("items", {"item": item.name, "uom": _get_uom(), "qty": flt(qty)})
    dn.flags.ignore_permissions = True
    dn.insert()
    dn.submit()
    dn.reload()
    return dn


def _make_ar(delivery_note, **kwargs):
    ar = frappe.new_doc("SC Acceptance Record")
    ar.delivery_note = delivery_note
    ar.acceptance_date = today()
    ar.accepted_by = "Nguyễn Văn A"
    ar.flags.ignore_permissions = True
    for k, v in kwargs.items():
        setattr(ar, k, v)
    return ar


# ---------- Tests ----------

def test_acceptance_marks_dn():
    """Submit AR cho DN đã giao -> DN.status 'Đã nghiệm thu', acceptance_ref=AR.name, AR.status 'Đã nghiệm thu'."""
    dn = _make_delivered_dn("MARK")
    ar = _make_ar(dn.name)
    try:
        ar.insert()
        ar.submit()
        dn.reload()
        ok = (
            dn.status == "Đã nghiệm thu"
            and dn.acceptance_ref == ar.name
            and ar.status == "Đã nghiệm thu"
        )
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK dn.status={dn.status} acceptance_ref={dn.acceptance_ref} ar.status={ar.status}"}
        return {"pass": False, "msg": f"X dn.status={dn.status} acceptance_ref={dn.acceptance_ref} ar.status={ar.status}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:200]}"}


def test_accept_undelivered_dn_blocked():
    """DN còn 'Nháp' (chưa submit) -> AR validate throw."""
    cust = _make_customer("UNDEL")
    item = _make_item("UNDEL")
    wh = _pick_warehouse()
    batch = _make_batch(item.name, add_days(today(), 200))
    _seed_stock(item.name, wh, batch.name, 100)
    so = _make_approved_so(cust.name, item.name, 10)
    dn = frappe.new_doc("SC Delivery Note")
    dn.sales_order = so.name
    dn.from_warehouse = wh
    dn.delivery_date = today()
    dn.append("items", {"item": item.name, "uom": _get_uom(), "qty": 10})
    dn.flags.ignore_permissions = True
    dn.insert()
    # NOT submitted -> stays "Nháp"
    ar = _make_ar(dn.name)
    try:
        ar.insert()
        frappe.db.rollback()
        return {"pass": False, "msg": "X did not throw"}
    except frappe.ValidationError as e:
        msg = str(e)
        frappe.db.rollback()
        return {"pass": True, "msg": f"OK threw: {msg[:150]}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw unexpected: {str(e)[:150]}"}


def run():
    tests = [
        test_acceptance_marks_dn,
        test_accept_undelivered_dn_blocked,
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
