"""Test BRU-REC-001 — Thu hồi/truy xuất lô đã bán ra theo KHÁCH HÀNG (M10 recall gap).

Run individual: bench --site supplycore-miyano.local execute supplycore.tests.recall_by_customer_test.test_<name>
Run all:        bench --site supplycore-miyano.local execute supplycore.tests.recall_by_customer_test.run
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
        frappe.throw("recall_by_customer_test: cần seed SC Warehouse")
    return rows[0]


def _make_customer(suffix, credit_limit=0):
    c = frappe.new_doc("SC Customer")
    c.customer_name = f"KH RCL test {suffix}"
    c.tax_code = f"TAX-RCL-{random_string(8)}"
    c.credit_limit = flt(credit_limit)
    c.flags.ignore_permissions = True
    c.insert()
    return c


def _make_item(suffix):
    item = frappe.new_doc("SC Item")
    item.item_code = f"RCL-{suffix}-{random_string(5)}"
    item.item_name = f"RCL test item {suffix}"
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


def _deliver_and_accept(customer, item, warehouse, batch, qty):
    """SO(duyệt) -> DN(submit, batch cố định) -> AR(submit) — trả về DN đã nghiệm thu."""
    so = _make_approved_so(customer, item, qty)
    dn = frappe.new_doc("SC Delivery Note")
    dn.sales_order = so.name
    dn.from_warehouse = warehouse
    dn.delivery_date = today()
    dn.append("items", {"item": item, "uom": _get_uom(), "qty": flt(qty),
                          "batch": batch, "warehouse": warehouse})
    dn.flags.ignore_permissions = True
    dn.insert()
    dn.submit()
    dn.reload()

    ar = frappe.new_doc("SC Acceptance Record")
    ar.delivery_note = dn.name
    ar.acceptance_date = today()
    ar.accepted_by = "Nguyễn Văn A"
    ar.flags.ignore_permissions = True
    ar.insert()
    ar.submit()
    dn.reload()
    return dn


def _make_recall_notice(item, batch_name, reason="QC failed"):
    rn = frappe.new_doc("SC Recall Notice")
    rn.recall_date = today()
    rn.recall_type = "Mandatory"
    rn.severity = "Class I (Critical)"
    rn.item = item
    rn.batch_no = batch_name
    rn.recall_reason = reason
    rn.flags.ignore_permissions = True
    rn.insert()
    return rn


# ---------- Tests ----------

def test_recall_populates_customer_rows():
    """Batch giao 1 phần cho khách hàng (còn lại trong kho) → populate_affected_items
    trả về 1 row location_type=Customer với đúng customer + qty."""
    item = _make_item("CUSTROW")
    cust = _make_customer("CUSTROW")
    wh = _pick_warehouse()
    batch = _make_batch(item.name, add_days(today(), 200))
    _seed_stock(item.name, wh, batch.name, 100)
    dn = _deliver_and_accept(cust.name, item.name, wh, batch.name, 30)

    rn = _make_recall_notice(item.name, batch.name)
    try:
        rn.populate_affected_items()
        cust_rows = [r for r in rn.affected_items if r.location_type == "Customer"]
        frappe.db.rollback()
        if len(cust_rows) != 1:
            return {"pass": False, "msg": f"X expected 1 customer row, got {len(cust_rows)}"}
        row = cust_rows[0]
        ok = (row.customer == cust.name and abs(flt(row.qty_issued) - 30) < 0.01
              and row.voucher_no == dn.name)
        if ok:
            return {"pass": True, "msg": f"OK customer={row.customer} qty={row.qty_issued} dn={row.voucher_no}"}
        return {"pass": False, "msg": f"X customer={row.customer} qty={row.qty_issued} voucher_no={row.voucher_no}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:200]}"}


def test_recall_soldout_batch_has_rows():
    """Giao TOÀN BỘ batch (0 tồn kho) → populate vẫn trả Customer rows (không rỗng),
    total_affected_qty > 0 và resolution % tính được (không lỗi/không rỗng)."""
    item = _make_item("SOLDOUT")
    cust = _make_customer("SOLDOUT")
    wh = _pick_warehouse()
    batch = _make_batch(item.name, add_days(today(), 200))
    _seed_stock(item.name, wh, batch.name, 50)
    _deliver_and_accept(cust.name, item.name, wh, batch.name, 50)

    avail = SCStockLedgerEntry.get_available_qty(item.name, wh, batch.name)

    rn = _make_recall_notice(item.name, batch.name)
    try:
        rn.populate_affected_items()
        wh_rows = [r for r in rn.affected_items if r.location_type == "Warehouse"]
        cust_rows = [r for r in rn.affected_items if r.location_type == "Customer"]
        total_affected = flt(rn.total_affected_qty)
        frappe.db.rollback()
        if avail != 0:
            return {"pass": False, "msg": f"X setup lỗi: avail={avail} (kỳ vọng 0)"}
        if len(wh_rows) != 0:
            return {"pass": False, "msg": f"X expected 0 warehouse rows, got {len(wh_rows)}"}
        if len(cust_rows) < 1:
            return {"pass": False, "msg": "X sold-out batch không có Customer rows nào (BRU-REC-001 gap)"}
        if total_affected <= 0:
            return {"pass": False, "msg": f"X total_affected_qty={total_affected} (kỳ vọng > 0)"}
        return {"pass": True, "msg": f"OK cust_rows={len(cust_rows)} total_affected={total_affected}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:200]}"}


def test_batch_trace_sold_to():
    """get_batch_trace(batch) trả về sold_to entry với đúng khách hàng + qty."""
    from supplycore.m10_traceability.api.trace import get_batch_trace

    item = _make_item("TRACESOLD")
    cust = _make_customer("TRACESOLD")
    wh = _pick_warehouse()
    batch = _make_batch(item.name, add_days(today(), 200))
    _seed_stock(item.name, wh, batch.name, 100)
    dn = _deliver_and_accept(cust.name, item.name, wh, batch.name, 40)

    try:
        res = get_batch_trace(batch.name)
        frappe.db.rollback()
        if "sold_to" not in res:
            return {"pass": False, "msg": "X get_batch_trace không có key sold_to"}
        sold_to = res["sold_to"]
        matching = [r for r in sold_to if r.get("customer") == cust.name]
        if not matching:
            return {"pass": False, "msg": f"X không tìm thấy customer {cust.name} trong sold_to={sold_to}"}
        if abs(flt(matching[0].get("qty")) - 40) > 0.01:
            return {"pass": False, "msg": f"X qty sai: {matching[0]}"}
        return {"pass": True, "msg": f"OK sold_to={matching[0]}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:200]}"}


def run():
    tests = [
        test_recall_populates_customer_rows,
        test_recall_soldout_batch_has_rows,
        test_batch_trace_sold_to,
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
