"""Test GD2 Task 9 -- API scm.* ban hang (supplycore.api.sales.*).

Run individual: bench --site supplycore-miyano.local execute supplycore.tests.sales_api_test.test_<name>
Run all:        bench --site supplycore-miyano.local execute supplycore.tests.sales_api_test.run
"""

import frappe
from frappe.utils import today, add_days, random_string, flt

from supplycore.api import sales


def _get_uom() -> str:
    return frappe.db.get_value("SC UOM", {}, "name")


def _pick_warehouse() -> str:
    rows = frappe.get_all("SC Warehouse", filters={"is_group": 0, "disabled": 0},
                           pluck="name", order_by="name", limit=1)
    if not rows:
        frappe.throw("sales_api_test: cần seed SC Warehouse")
    return rows[0]


def _make_customer(suffix, credit_limit=0):
    c = frappe.new_doc("SC Customer")
    c.customer_name = f"KH API test {suffix}"
    c.tax_code = f"TAX-API-{random_string(8)}"
    c.credit_limit = flt(credit_limit)
    c.flags.ignore_permissions = True
    c.insert()
    return c


def _make_item(suffix):
    item = frappe.new_doc("SC Item")
    item.item_code = f"API-{suffix}-{random_string(5)}"
    item.item_name = f"API test item {suffix}"
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
    from supplycore.supplycore.doctype.sc_stock_ledger_entry.sc_stock_ledger_entry import (
        SCStockLedgerEntry,
    )

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


def _make_so(customer, framework_contract, item, qty, submit=False):
    so = frappe.new_doc("SC Sales Order")
    so.customer = customer
    so.framework_contract = framework_contract
    so.order_date = today()
    so.append("items", {"item": item, "uom": _get_uom(), "qty": flt(qty)})
    so.flags.ignore_permissions = True
    so.insert()
    if submit:
        so.submit()
    return so


def _full_chain(suffix, qty=10, unit_price=1000, rate=1000):
    """Customer -> Item -> SFC(submit) -> SO(submit+approve), warehouse co ton."""
    cust = _make_customer(suffix)
    item = _make_item(suffix)
    wh = _pick_warehouse()
    batch = _make_batch(item.name, add_days(today(), 200))
    _seed_stock(item.name, wh, batch.name, 100, rate=rate)
    sfc = _make_submitted_sfc(cust.name, item.name, 1000, unit_price)
    so = _make_so(cust.name, sfc.name, item.name, qty, submit=True)
    so.approve()
    so.reload()
    return {"customer": cust, "item": item, "wh": wh, "sfc": sfc, "so": so}


# ---------- Tests ----------

def test_customer_upsert():
    """Tao moi tra ve name; goi lai voi name -> cap nhat credit_limit."""
    data = {"customer_name": f"KH Upsert {random_string(5)}",
            "tax_code": f"TAX-UP-{random_string(8)}", "credit_limit": 1000}
    try:
        name = sales.customer_upsert(data)
        ok1 = bool(name) and frappe.db.exists("SC Customer", name)
        data2 = {"name": name, "credit_limit": 5000}
        name2 = sales.customer_upsert(data2)
        credit = frappe.db.get_value("SC Customer", name2, "credit_limit")
        ok = ok1 and name2 == name and flt(credit) == 5000
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK name={name} credit={credit}"}
        return {"pass": False, "msg": f"X name={name} name2={name2} credit={credit}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:200]}"}


def test_sales_framework_create():
    """Tao SFC voi items qua API, submit=1 -> status Hieu luc."""
    cust = _make_customer("SFCAPI")
    item = _make_item("SFCAPI")
    data = {
        "customer": cust.name,
        "valid_from": today(),
        "valid_to": add_days(today(), 365),
        "items": [{"item": item.name, "uom": _get_uom(),
                    "contract_qty": 100, "unit_price": 500}],
        "submit": 1,
    }
    try:
        name = sales.sales_framework_create(data)
        status = frappe.db.get_value("SC Sales Framework Contract", name, "status")
        ok = bool(name) and status == "Hiệu lực"
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK name={name} status={status}"}
        return {"pass": False, "msg": f"X name={name} status={status}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:200]}"}


def test_sales_order_approve():
    """SO da submit -> approve() qua API -> status Da duyet."""
    cust = _make_customer("SOAPI")
    item = _make_item("SOAPI")
    sfc = _make_submitted_sfc(cust.name, item.name, 100, 1000)
    so = _make_so(cust.name, sfc.name, item.name, 10, submit=True)
    try:
        result = sales.sales_order_approve(so.name)
        so.reload()
        ok = so.status == "Đã duyệt" and result.get("status") == "Đã duyệt"
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK status={so.status} result={result}"}
        return {"pass": False, "msg": f"X status={so.status} result={result}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:200]}"}


def test_delivery_create_and_accept():
    """delivery_create() khong truyen items -> tu suy tu SO; submit; delivery_accept() -> DN Da nghiem thu."""
    ctx = _full_chain("DNAPI", qty=10)
    try:
        dn_name = sales.delivery_create({
            "sales_order": ctx["so"].name,
            "from_warehouse": ctx["wh"],
        })
        dn_status = frappe.db.get_value("SC Delivery Note", dn_name, "status")
        sle_qty = flt(frappe.db.sql("""
            SELECT COALESCE(SUM(qty_change), 0) FROM `tabSC Stock Ledger Entry`
            WHERE voucher_type='SC Delivery Note' AND voucher_no=%s AND is_cancelled=0
        """, dn_name)[0][0])
        ar_name = sales.delivery_accept(dn_name, accepted_by="Nguyễn Văn A", note="OK")
        dn_status2 = frappe.db.get_value("SC Delivery Note", dn_name, "status")
        ok = (dn_status == "Đã giao" and sle_qty == -10
              and bool(ar_name) and dn_status2 == "Đã nghiệm thu")
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK dn={dn_name} sle={sle_qty} ar={ar_name} status2={dn_status2}"}
        return {"pass": False, "msg": f"X dn_status={dn_status} sle_qty={sle_qty} ar={ar_name} status2={dn_status2}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:250]}"}


def test_sales_invoice_and_receipt():
    """Full path via API: ... -> delivery -> accept -> invoice -> receipt full -> Da thu du."""
    ctx = _full_chain("FULLAPI", qty=10, unit_price=1000)  # grand_total = 10000
    try:
        dn_name = sales.delivery_create({
            "sales_order": ctx["so"].name,
            "from_warehouse": ctx["wh"],
        })
        sales.delivery_accept(dn_name, accepted_by="Nguyễn Văn B")

        si_result = sales.sales_invoice_create(dn_name, tax_rate=0)
        si_name = si_result["name"]
        grand_total = flt(si_result["grand_total"])

        sr_result = sales.receipt_collect(si_name, grand_total, mode="Chuyển khoản")
        si_status = frappe.db.get_value("SC Sales Invoice", si_name, "status")
        outstanding = flt(frappe.db.get_value("SC Sales Invoice", si_name, "outstanding_amount"))

        ok = (grand_total == 10000 and si_status == "Đã thu đủ"
              and outstanding == 0 and flt(sr_result.get("outstanding", -1)) == 0)
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK si={si_name} grand_total={grand_total} status={si_status}"}
        return {"pass": False, "msg": f"X grand_total={grand_total} status={si_status} outstanding={outstanding} sr={sr_result}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:250]}"}


def test_delivery_create_from_unapproved_so_raises():
    """SO chua duyet (chi submit, khong approve) -> delivery_create() throw BRU-SO-002."""
    cust = _make_customer("UNAPPR")
    item = _make_item("UNAPPR")
    wh = _pick_warehouse()
    sfc = _make_submitted_sfc(cust.name, item.name, 100, 1000)
    so = _make_so(cust.name, sfc.name, item.name, 10, submit=True)  # NOT approved
    try:
        sales.delivery_create({"sales_order": so.name, "from_warehouse": wh})
        frappe.db.rollback()
        return {"pass": False, "msg": "X did not throw"}
    except frappe.ValidationError as e:
        msg = str(e)
        frappe.db.rollback()
        if "BRU-SO-002" in msg:
            return {"pass": True, "msg": "OK threw BRU-SO-002"}
        return {"pass": False, "msg": f"X threw wrong msg: {msg[:150]}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw unexpected: {str(e)[:150]}"}


def run():
    tests = [
        test_customer_upsert,
        test_sales_framework_create,
        test_sales_order_approve,
        test_delivery_create_and_accept,
        test_sales_invoice_and_receipt,
        test_delivery_create_from_unapproved_so_raises,
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
