"""Test GD2 Task 7 -- SC Sales Invoice + SI Item (GL phai thu + COGS,
BRU-DEL-001/INVC-001/PAY-001).

Run individual: bench --site supplycore-miyano.local execute supplycore.tests.sc_sales_invoice_test.test_<name>
Run all:        bench --site supplycore-miyano.local execute supplycore.tests.sc_sales_invoice_test.run
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
        frappe.throw("sc_sales_invoice_test: cần seed SC Warehouse")
    return rows[0]


def _make_customer(suffix, credit_limit=0):
    c = frappe.new_doc("SC Customer")
    c.customer_name = f"KH SI test {suffix}"
    c.tax_code = f"TAX-SI-{random_string(8)}"
    c.credit_limit = flt(credit_limit)
    c.flags.ignore_permissions = True
    c.insert()
    return c


def _make_item(suffix):
    item = frappe.new_doc("SC Item")
    item.item_code = f"SI-{suffix}-{random_string(5)}"
    item.item_name = f"SI test item {suffix}"
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


def _seed_chain(suffix, qty=30, unit_price=1000, rate=1000, accept=True):
    """Xây customer->item->batch(stock)->SFC->SO(duyệt)->DN(submit)[->Acceptance]."""
    cust = _make_customer(suffix)
    item = _make_item(suffix)
    wh = _pick_warehouse()
    batch = _make_batch(item.name, add_days(today(), 200))
    _seed_stock(item.name, wh, batch.name, 100, rate=rate)
    dn, so = _make_delivered_dn(cust.name, item.name, wh, qty, unit_price=unit_price)
    if accept:
        _accept_dn(dn)
    return {"customer": cust, "item": item, "wh": wh, "dn": dn, "so": so, "qty": qty,
            "unit_price": unit_price}


def _make_si(ctx, items=None, **kwargs):
    si = frappe.new_doc("SC Sales Invoice")
    si.customer = ctx["customer"].name
    si.delivery_note = ctx["dn"].name
    si.invoice_date = today()
    for it in (items if items is not None else [{"item": ctx["item"].name, "qty": ctx["qty"],
                                                    "unit_price": ctx["unit_price"]}]):
        si.append("items", it)
    si.flags.ignore_permissions = True
    for k, v in kwargs.items():
        setattr(si, k, v)
    return si


# ---------- Tests ----------

def test_si_from_unaccepted_dn_blocked():
    """DN chi 'Da giao' (chua nghiem thu) -> SI validate throw BRU-DEL-001."""
    ctx = _seed_chain("UNACC", accept=False)
    si = _make_si(ctx)
    try:
        si.insert()
        frappe.db.rollback()
        return {"pass": False, "msg": "X did not throw"}
    except frappe.ValidationError as e:
        msg = str(e)
        frappe.db.rollback()
        if "BRU-DEL-001" in msg:
            return {"pass": True, "msg": "OK threw BRU-DEL-001"}
        return {"pass": False, "msg": f"X threw wrong msg: {msg[:150]}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw unexpected: {str(e)[:150]}"}


def test_si_mismatch_dn_blocked():
    """SI items qty khac DN Item -> throw BRU-INVC-001."""
    ctx = _seed_chain("MISM", qty=30)
    si = _make_si(ctx, items=[{"item": ctx["item"].name, "qty": 999, "unit_price": ctx["unit_price"]}])
    try:
        si.insert()
        frappe.db.rollback()
        return {"pass": False, "msg": "X did not throw"}
    except frappe.ValidationError as e:
        msg = str(e)
        frappe.db.rollback()
        if "BRU-INVC-001" in msg:
            return {"pass": True, "msg": "OK threw BRU-INVC-001"}
        return {"pass": False, "msg": f"X threw wrong msg: {msg[:150]}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw unexpected: {str(e)[:150]}"}


def test_si_posts_ar_gl():
    """Submit SI -> 131 balance (party=customer) tang grand_total; 511 credit ghi nhan."""
    ctx = _seed_chain("ARGL", qty=20, unit_price=1500)
    si = _make_si(ctx)
    si.tax_rate = 10
    try:
        before = SCGLEntry.get_balance("131", ctx["customer"].name)
        rev_before = SCGLEntry.get_balance("511")
        si.insert()
        si.submit()
        after = SCGLEntry.get_balance("131", ctx["customer"].name)
        rev_after = SCGLEntry.get_balance("511")
        expected_total = 20 * 1500
        expected_tax = expected_total * 0.10
        expected_grand = expected_total + expected_tax
        ok = (flt(after - before) == flt(expected_grand)
              and flt(rev_after - rev_before) == flt(-expected_total))  # income tang -> so du (debit-credit) giam
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK 131 delta={after-before} 511 delta={rev_after-rev_before}"}
        return {"pass": False, "msg": f"X 131 delta={after-before} exp={expected_grand}; 511 delta={rev_after-rev_before}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:250]}"}


def test_si_cogs_posted():
    """Submit SI -> 632 co debit == cogs (Sigma valuation cua DN SLE) > 0."""
    ctx = _seed_chain("COGS", qty=15, unit_price=2000, rate=800)
    si = _make_si(ctx)
    try:
        before_632 = SCGLEntry.get_balance("632")
        before_156 = SCGLEntry.get_balance("156")
        si.insert()
        si.submit()
        after_632 = SCGLEntry.get_balance("632")
        after_156 = SCGLEntry.get_balance("156")
        expected_cogs = 15 * 800
        ok = (flt(after_632 - before_632) == flt(expected_cogs)
              and flt(after_156 - before_156) == flt(-expected_cogs)
              and expected_cogs > 0)
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK 632 delta={after_632-before_632} 156 delta={after_156-before_156}"}
        return {"pass": False, "msg": f"X 632 delta={after_632-before_632} exp={expected_cogs}; 156 delta={after_156-before_156}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:250]}"}


def test_si_fiscal_lock_blocked():
    """Settings.fiscal_lock_date tuong lai, invoice_date <= lock -> submit throw BRU-PAY-001."""
    ctx = _seed_chain("LOCK", qty=10)
    si = _make_si(ctx)
    old_lock = frappe.db.get_single_value("SupplyCore Settings", "fiscal_lock_date")
    try:
        frappe.db.set_single_value("SupplyCore Settings", "fiscal_lock_date", add_days(today(), 30))
        si.insert()
        try:
            si.submit()
            frappe.db.rollback()
            return {"pass": False, "msg": "X did not throw"}
        except frappe.ValidationError as e:
            msg = str(e)
            if "BRU-PAY-001" in msg:
                return {"pass": True, "msg": "OK threw BRU-PAY-001"}
            return {"pass": False, "msg": f"X threw wrong msg: {msg[:150]}"}
    except Exception as e:
        return {"pass": False, "msg": f"X threw unexpected: {str(e)[:150]}"}
    finally:
        frappe.db.set_single_value("SupplyCore Settings", "fiscal_lock_date", old_lock)
        frappe.db.rollback()


def test_si_desk_price_override_ignored():
    """GD2 review I-1 (BRU-SFC-002 gia SI): Desk sua tay unit_price tren SI Item
    (vd 5000 thay vi gia SFC-lock 1000) -> sau save phai bi ghi de ve gia goc
    (tu SO Item qua delivery_note.sales_order), grand_total tinh theo gia goc."""
    ctx = _seed_chain("PRICEOVR", qty=30, unit_price=1000)
    si = _make_si(ctx, items=[{"item": ctx["item"].name, "qty": 30, "unit_price": 5000}])
    try:
        si.insert()
        ok = (flt(si.items[0].unit_price) == 1000 and flt(si.grand_total) == 30000)
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK unit_price={si.items[0].unit_price} grand_total={si.grand_total}"}
        return {"pass": False, "msg": f"X unit_price={si.items[0].unit_price} grand_total={si.grand_total}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:250]}"}


def test_si_cancel_reverses_gl():
    """Submit roi cancel -> 131 balance quay lai truoc submit."""
    ctx = _seed_chain("CANCEL", qty=25, unit_price=1200)
    si = _make_si(ctx)
    try:
        before = SCGLEntry.get_balance("131", ctx["customer"].name)
        si.insert()
        si.submit()
        si.cancel()
        after = SCGLEntry.get_balance("131", ctx["customer"].name)
        ok = flt(after) == flt(before)
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK before={before} after={after}"}
        return {"pass": False, "msg": f"X before={before} after={after}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:250]}"}


def run():
    tests = [
        test_si_from_unaccepted_dn_blocked,
        test_si_mismatch_dn_blocked,
        test_si_desk_price_override_ignored,
        test_si_posts_ar_gl,
        test_si_cogs_posted,
        test_si_fiscal_lock_blocked,
        test_si_cancel_reverses_gl,
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
