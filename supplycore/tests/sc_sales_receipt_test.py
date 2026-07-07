"""Test GD2 Task 8 -- SC Sales Receipt (thu tien tat toan phai thu).

Run individual: bench --site supplycore-miyano.local execute supplycore.tests.sc_sales_receipt_test.test_<name>
Run all:        bench --site supplycore-miyano.local execute supplycore.tests.sc_sales_receipt_test.run
"""

import frappe
from frappe.utils import today, add_days, random_string, flt

from supplycore.supplycore.doctype.sc_stock_ledger_entry.sc_stock_ledger_entry import SCStockLedgerEntry
from supplycore.supplycore.doctype.sc_gl_entry.sc_gl_entry import SCGLEntry


def _get_uom() -> str:
    return frappe.db.get_value("SC UOM", {}, "name")


def _pick_warehouse() -> str:
    rows = frappe.get_all("SC Warehouse", filters={"is_group": 0, "disabled": 0},
                           pluck="name", order_by="name", limit=1)
    if not rows:
        frappe.throw("sc_sales_receipt_test: cần seed SC Warehouse")
    return rows[0]


def _make_customer(suffix, credit_limit=0):
    c = frappe.new_doc("SC Customer")
    c.customer_name = f"KH SR test {suffix}"
    c.tax_code = f"TAX-SR-{random_string(8)}"
    c.credit_limit = flt(credit_limit)
    c.flags.ignore_permissions = True
    c.insert()
    return c


def _make_item(suffix):
    item = frappe.new_doc("SC Item")
    item.item_code = f"SR-{suffix}-{random_string(5)}"
    item.item_name = f"SR test item {suffix}"
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


def _make_delivered_dn(customer, item, wh, qty, unit_price=1000):
    so = _make_approved_so(customer, item, qty, unit_price=unit_price)
    dn = frappe.new_doc("SC Delivery Note")
    dn.sales_order = so.name
    dn.from_warehouse = wh
    dn.delivery_date = today()
    dn.append("items", {"item": item, "uom": _get_uom(), "qty": flt(qty)})
    dn.flags.ignore_permissions = True
    dn.insert()
    dn.submit()
    dn.reload()
    return dn, so


def _accept_dn(dn):
    ar = frappe.new_doc("SC Acceptance Record")
    ar.delivery_note = dn.name
    ar.acceptance_date = today()
    ar.accepted_by = "Nguyễn Văn A"
    ar.flags.ignore_permissions = True
    ar.insert()
    ar.submit()
    dn.reload()
    return ar


def _make_submitted_si(customer, item, wh, qty, unit_price=1000, rate=1000):
    batch = _make_batch(item, add_days(today(), 200))
    _seed_stock(item, wh, batch.name, 100, rate=rate)
    dn, so = _make_delivered_dn(customer, item, wh, qty, unit_price=unit_price)
    _accept_dn(dn)
    si = frappe.new_doc("SC Sales Invoice")
    si.customer = customer
    si.delivery_note = dn.name
    si.invoice_date = today()
    si.append("items", {"item": item, "qty": qty, "unit_price": unit_price})
    si.flags.ignore_permissions = True
    si.insert()
    si.submit()
    si.reload()
    return si


def _seed_chain(suffix, qty=10, unit_price=1000, rate=1000):
    """Xay Customer->Item->...->Sales Invoice (submitted)."""
    cust = _make_customer(suffix)
    item = _make_item(suffix)
    wh = _pick_warehouse()
    si = _make_submitted_si(cust.name, item.name, wh, qty, unit_price=unit_price, rate=rate)
    return {"customer": cust, "item": item, "wh": wh, "si": si}


def _make_receipt(ctx, amount, mode="Chuyển khoản", **kwargs):
    sr = frappe.new_doc("SC Sales Receipt")
    sr.customer = ctx["customer"].name
    sr.sales_invoice = ctx["si"].name
    sr.receipt_date = today()
    sr.amount = flt(amount)
    sr.mode = mode
    sr.flags.ignore_permissions = True
    for k, v in kwargs.items():
        setattr(sr, k, v)
    return sr


# ---------- Tests ----------

def test_receipt_reduces_outstanding():
    """SI grand_total 10000, thu 4000 -> outstanding 6000, status Da thu mot phan."""
    ctx = _seed_chain("REDUCE", qty=10, unit_price=1000)  # grand_total = 10000
    sr = _make_receipt(ctx, 4000)
    try:
        sr.insert()
        sr.submit()
        ctx["si"].reload()
        ok = (flt(ctx["si"].outstanding_amount) == 6000
              and ctx["si"].status == "Đã thu một phần")
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK outstanding={ctx['si'].outstanding_amount} status={ctx['si'].status}"}
        return {"pass": False, "msg": f"X outstanding={ctx['si'].outstanding_amount} status={ctx['si'].status}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:200]}"}


def test_receipt_full_sets_paid():
    """Thu du outstanding -> outstanding=0, status Da thu du."""
    ctx = _seed_chain("FULL", qty=10, unit_price=1000)  # grand_total = 10000
    sr = _make_receipt(ctx, 10000)
    try:
        sr.insert()
        sr.submit()
        ctx["si"].reload()
        ok = (flt(ctx["si"].outstanding_amount) == 0
              and ctx["si"].status == "Đã thu đủ")
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK outstanding={ctx['si'].outstanding_amount} status={ctx['si'].status}"}
        return {"pass": False, "msg": f"X outstanding={ctx['si'].outstanding_amount} status={ctx['si'].status}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:200]}"}


def test_receipt_over_outstanding_blocked():
    """amount > outstanding -> throw."""
    ctx = _seed_chain("OVER", qty=10, unit_price=1000)  # grand_total = 10000
    sr = _make_receipt(ctx, 20000)
    try:
        sr.insert()
        frappe.db.rollback()
        return {"pass": False, "msg": "X did not throw"}
    except frappe.ValidationError as e:
        msg = str(e)
        frappe.db.rollback()
        return {"pass": True, "msg": f"OK threw: {msg[:120]}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw unexpected: {str(e)[:150]}"}


def test_receipt_posts_gl():
    """Submit SR -> 131 (party=customer) giam amount; cash/bank tang amount."""
    ctx = _seed_chain("GL", qty=10, unit_price=1000)  # grand_total = 10000
    sr = _make_receipt(ctx, 4000, mode="Tiền mặt")
    try:
        before_131 = SCGLEntry.get_balance("131", ctx["customer"].name)
        before_cash = SCGLEntry.get_balance("1111")
        sr.insert()
        sr.submit()
        after_131 = SCGLEntry.get_balance("131", ctx["customer"].name)
        after_cash = SCGLEntry.get_balance("1111")
        ok = (flt(after_131 - before_131) == -4000
              and flt(after_cash - before_cash) == 4000)
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK 131 delta={after_131-before_131} cash delta={after_cash-before_cash}"}
        return {"pass": False, "msg": f"X 131 delta={after_131-before_131} cash delta={after_cash-before_cash}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:250]}"}


def test_receipt_cancel_restores():
    """Submit roi cancel -> outstanding va 131 quay ve truoc submit."""
    ctx = _seed_chain("CANCEL", qty=10, unit_price=1000)  # grand_total = 10000
    sr = _make_receipt(ctx, 4000)
    try:
        before_131 = SCGLEntry.get_balance("131", ctx["customer"].name)
        before_outstanding = flt(ctx["si"].outstanding_amount)
        sr.insert()
        sr.submit()
        sr.cancel()
        ctx["si"].reload()
        after_131 = SCGLEntry.get_balance("131", ctx["customer"].name)
        ok = (flt(after_131) == flt(before_131)
              and flt(ctx["si"].outstanding_amount) == flt(before_outstanding))
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK 131={after_131} outstanding={ctx['si'].outstanding_amount}"}
        return {"pass": False, "msg": f"X 131={after_131} exp={before_131}; outstanding={ctx['si'].outstanding_amount} exp={before_outstanding}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:250]}"}


def run():
    tests = [
        test_receipt_reduces_outstanding,
        test_receipt_full_sets_paid,
        test_receipt_over_outstanding_blocked,
        test_receipt_posts_gl,
        test_receipt_cancel_restores,
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
