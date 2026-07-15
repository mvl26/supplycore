"""Test GD2 Task 5 -- SC Delivery Note + DN Item (xuất kho SLE, FEFO, BRU-SO-002/INV-001/EXP-001).

Run individual: bench --site supplycore-miyano.local execute supplycore.tests.sc_delivery_note_test.test_<name>
Run all:        bench --site supplycore-miyano.local execute supplycore.tests.sc_delivery_note_test.run
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
        frappe.throw("sc_delivery_note_test: cần seed SC Warehouse")
    return rows[0]


def _make_customer(suffix, credit_limit=0):
    c = frappe.new_doc("SC Customer")
    c.customer_name = f"KH DN test {suffix}"
    c.tax_code = f"TAX-DN-{random_string(8)}"
    c.credit_limit = flt(credit_limit)
    c.flags.ignore_permissions = True
    c.insert()
    return c


def _make_item(suffix):
    item = frappe.new_doc("SC Item")
    item.item_code = f"DN-{suffix}-{random_string(5)}"
    item.item_name = f"DN test item {suffix}"
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


def _make_dn(sales_order, from_warehouse, items, **kwargs):
    dn = frappe.new_doc("SC Delivery Note")
    dn.sales_order = sales_order
    dn.from_warehouse = from_warehouse
    dn.delivery_date = today()
    for it in items:
        row = {"item": it["item"], "uom": _get_uom(), "qty": flt(it["qty"])}
        if it.get("batch"):
            row["batch"] = it["batch"]
        if it.get("warehouse"):
            row["warehouse"] = it["warehouse"]
        dn.append("items", row)
    dn.flags.ignore_permissions = True
    for k, v in kwargs.items():
        setattr(dn, k, v)
    return dn


# ---------- Tests ----------

def test_dn_from_unapproved_so_blocked():
    """SO chưa duyệt (status mặc định 'Chờ duyệt') -> DN validate throw BRU-SO-002."""
    cust = _make_customer("UNAPP")
    item = _make_item("UNAPP")
    sfc = _make_submitted_sfc(cust.name, item.name, 1000, 1000)
    so = frappe.new_doc("SC Sales Order")
    so.customer = cust.name
    so.framework_contract = sfc.name
    so.order_date = today()
    so.append("items", {"item": item.name, "uom": _get_uom(), "qty": 10})
    so.flags.ignore_permissions = True
    so.insert()
    so.submit()  # status stays "Chờ duyệt" (not approved)
    wh = _pick_warehouse()
    dn = _make_dn(so.name, wh, [{"item": item.name, "qty": 5}])
    try:
        dn.insert()
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


def test_dn_submit_posts_negative_sle():
    """Approved SO, stock=100, DN qty=30 -> submit; available=70; SO.status Da ban giao."""
    cust = _make_customer("SUBMIT")
    item = _make_item("SUBMIT")
    wh = _pick_warehouse()
    batch = _make_batch(item.name, add_days(today(), 200))
    _seed_stock(item.name, wh, batch.name, 100)
    so = _make_approved_so(cust.name, item.name, 30)
    dn = _make_dn(so.name, wh, [{"item": item.name, "qty": 30}])
    try:
        dn.insert()
        dn.submit()
        avail = SCStockLedgerEntry.get_available_qty(item.name, wh)
        so.reload()
        ok = (flt(avail) == 70 and so.status == "Đã bàn giao")
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK avail={avail} so.status={so.status}"}
        return {"pass": False, "msg": f"X avail={avail} so.status={so.status}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:200]}"}


def test_dn_insufficient_stock_blocked():
    """DN qty=999 > available(100) -> throw BRU-INV-001."""
    cust = _make_customer("INSUFF")
    item = _make_item("INSUFF")
    wh = _pick_warehouse()
    batch = _make_batch(item.name, add_days(today(), 200))
    _seed_stock(item.name, wh, batch.name, 100)
    so = _make_approved_so(cust.name, item.name, 999, contract_qty=2000)
    dn = _make_dn(so.name, wh, [{"item": item.name, "qty": 999}])
    try:
        dn.insert()
        frappe.db.rollback()
        return {"pass": False, "msg": "X did not throw"}
    except frappe.ValidationError as e:
        msg = str(e)
        frappe.db.rollback()
        if "BRU-INV-001" in msg:
            return {"pass": True, "msg": "OK threw BRU-INV-001"}
        return {"pass": False, "msg": f"X threw wrong msg: {msg[:150]}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw unexpected: {str(e)[:150]}"}


def test_dn_expired_batch_blocked():
    """Batch hết hạn (đã gán trực tiếp) -> before_submit throw BRU-EXP-001."""
    cust = _make_customer("EXP")
    item = _make_item("EXP")
    wh = _pick_warehouse()
    batch = _make_batch(item.name, add_days(today(), -10))  # đã hết hạn
    _seed_stock(item.name, wh, batch.name, 100)
    so = _make_approved_so(cust.name, item.name, 10)
    dn = _make_dn(so.name, wh, [{"item": item.name, "qty": 10, "batch": batch.name}])
    try:
        dn.insert()
        dn.submit()
        frappe.db.rollback()
        return {"pass": False, "msg": "X did not throw"}
    except frappe.ValidationError as e:
        msg = str(e)
        frappe.db.rollback()
        if "BRU-EXP-001" in msg:
            return {"pass": True, "msg": "OK threw BRU-EXP-001"}
        return {"pass": False, "msg": f"X threw wrong msg: {msg[:150]}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw unexpected: {str(e)[:150]}"}


def test_dn_cancel_reverses_sle():
    """Submit rồi cancel -> available quay lại 100."""
    cust = _make_customer("CANCEL")
    item = _make_item("CANCEL")
    wh = _pick_warehouse()
    batch = _make_batch(item.name, add_days(today(), 200))
    _seed_stock(item.name, wh, batch.name, 100)
    so = _make_approved_so(cust.name, item.name, 40)
    dn = _make_dn(so.name, wh, [{"item": item.name, "qty": 40}])
    try:
        dn.insert()
        dn.submit()
        dn.cancel()
        avail = SCStockLedgerEntry.get_available_qty(item.name, wh)
        so.reload()
        ok = (flt(avail) == 100 and so.status == "Đã duyệt")
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK avail={avail} so.status={so.status}"}
        return {"pass": False, "msg": f"X avail={avail} so.status={so.status}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:200]}"}


def run():
    tests = [
        test_dn_from_unapproved_so_blocked,
        test_dn_submit_posts_negative_sle,
        test_dn_insufficient_stock_blocked,
        test_dn_expired_batch_blocked,
        test_dn_cancel_reverses_sle,
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
