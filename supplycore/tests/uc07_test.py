"""Test UC-07 — Tạo Material Request (Phiếu Đề Nghị Mua Hàng).

Run individual: bench --site supplycore execute supplycore.tests.uc07_test.test_<name>
Run all:        bench --site supplycore execute supplycore.tests.uc07_test.run
"""

import frappe
from frappe.utils import today, add_days, random_string


def _pick_warehouse() -> str:
    rows = frappe.get_all("SC Warehouse", filters={"is_group": 0, "disabled": 0},
                           pluck="name", order_by="name", limit=1)
    if not rows:
        frappe.throw("uc07_test: cần seed SC Warehouse")
    return rows[0]


def _pick_supplier() -> str:
    rows = frappe.get_all(
        "SC Supplier",
        filters={"disabled": 0},
        pluck="name",
        order_by="name",
        limit=1,
    )
    if not rows:
        frappe.throw("uc07_test: cần seed SC Supplier")
    return rows[0]


def _get_uom() -> str:
    uom = frappe.db.get_value("SC UOM", {}, "name")
    if not uom:
        frappe.throw("uc07_test: cần seed SC UOM")
    return uom


def _make_item(suffix: str, with_supplier: bool = True, **kwargs):
    item = frappe.new_doc("SC Item")
    item.item_code = f"UC07-{suffix}-{random_string(5)}"
    item.item_name = f"UC-07 test {suffix}"
    item.uom = _get_uom()
    item.is_stock_item = 1
    item.is_purchase_item = 1
    if with_supplier:
        item.default_supplier = _pick_supplier()
    item.flags.ignore_permissions = True
    for k, v in kwargs.items():
        setattr(item, k, v)
    item.insert()
    return item


def _make_mr(items: list, request_type: str = "Purchase", **kwargs):
    mr = frappe.new_doc("SC Material Request")
    mr.request_type = request_type
    mr.transaction_date = today()
    mr.schedule_date = add_days(today(), 7)
    mr.warehouse = _pick_warehouse()
    for k, v in kwargs.items():
        setattr(mr, k, v)
    for it in items:
        mr.append("items", it)
    mr.flags.ignore_permissions = True
    return mr


# ---------- Tests ----------

def test_qty_zero_rejected():
    """row qty=0 → throw SC-E-QTY."""
    item = _make_item("QTY0")
    mr = _make_mr([{"item": item.name, "qty": 0, "uom": item.uom}])
    try:
        mr.insert()
        frappe.db.rollback()
        return {"pass": False, "msg": "X did not throw on qty=0"}
    except frappe.ValidationError as e:
        msg = str(e)
        frappe.db.rollback()
        if "SC-E-QTY" in msg:
            return {"pass": True, "msg": f"OK: {msg[:120]}"}
        return {"pass": False, "msg": f"Wrong error: {msg[:120]}"}


def test_schedule_before_transaction_rejected():
    """schedule_date < transaction → throw SC-E-DATE."""
    item = _make_item("DATE")
    mr = _make_mr(
        [{"item": item.name, "qty": 5, "uom": item.uom}],
        schedule_date=add_days(today(), -1),
        transaction_date=today(),
    )
    try:
        mr.insert()
        frappe.db.rollback()
        return {"pass": False, "msg": "X did not throw on schedule<transaction"}
    except frappe.ValidationError as e:
        msg = str(e)
        frappe.db.rollback()
        if "SC-E-DATE" in msg:
            return {"pass": True, "msg": f"OK: {msg[:120]}"}
        return {"pass": False, "msg": f"Wrong error: {msg[:120]}"}


def test_no_supplier_purchase_rejected():
    """Purchase + item không có NCC → throw SC-E-NO-SUPPLIER."""
    # Item không default_supplier + không item_group → _item_has_supplier trả False
    item = _make_item("NOSUP", with_supplier=False)
    mr = _make_mr([{"item": item.name, "qty": 5, "uom": item.uom}], request_type="Purchase")
    try:
        mr.insert()
        frappe.db.rollback()
        return {"pass": False, "msg": "X did not throw on missing supplier"}
    except frappe.ValidationError as e:
        msg = str(e)
        frappe.db.rollback()
        if "SC-E-NO-SUPPLIER" in msg:
            return {"pass": True, "msg": f"OK: {msg[:120]}"}
        return {"pass": False, "msg": f"Wrong error: {msg[:120]}"}


def test_no_supplier_internal_transfer_ok():
    """Internal Transfer + không có NCC → save OK (chỉ check NCC cho Purchase/Urgent)."""
    item = _make_item("ITNOSUP", with_supplier=False)
    mr = _make_mr([{"item": item.name, "qty": 5, "uom": item.uom}], request_type="Internal Transfer")
    try:
        mr.insert()
        frappe.db.rollback()
        return {"pass": True, "msg": f"OK Internal Transfer saved {mr.name}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_submit_goes_to_pending():
    """submit MR → status=Pending (UC-07 reverts auto-Approved behavior)."""
    item = _make_item("SUBP")
    mr = _make_mr([{"item": item.name, "qty": 5, "uom": item.uom}])
    try:
        mr.insert()
        mr.submit()
        status = frappe.db.get_value("SC Material Request", mr.name, "status")
        frappe.db.rollback()
        if status == "Pending":
            return {"pass": True, "msg": f"OK status=Pending after submit"}
        return {"pass": False, "msg": f"X status={status} (expected Pending)"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_approve_changes_status():
    """approve() Pending → Approved."""
    item = _make_item("APPR")
    mr = _make_mr([{"item": item.name, "qty": 5, "uom": item.uom}])
    try:
        mr.insert()
        mr.submit()
        mr.reload()
        mr.approve()
        mr.reload()
        ok = (mr.status == "Approved")
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK approve() → status=Approved"}
        return {"pass": False, "msg": f"X status={mr.status}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_reject_requires_reason():
    """reject() không reason → SC-E-REJECT-REASON."""
    item = _make_item("REJR")
    mr = _make_mr([{"item": item.name, "qty": 5, "uom": item.uom}])
    try:
        mr.insert()
        mr.submit()
        mr.reload()
        try:
            mr.reject(reason="")
            frappe.db.rollback()
            return {"pass": False, "msg": "X did not throw on empty reason"}
        except frappe.ValidationError as e:
            msg = str(e)
            frappe.db.rollback()
            if "SC-E-REJECT-REASON" in msg:
                return {"pass": True, "msg": f"OK: {msg[:120]}"}
            return {"pass": False, "msg": f"Wrong error: {msg[:120]}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X setup threw: {str(e)[:120]}"}


def test_reject_with_reason_ok():
    """reject('lý do') → status=Rejected + rejection_reason populated."""
    item = _make_item("REJOK")
    mr = _make_mr([{"item": item.name, "qty": 5, "uom": item.uom}])
    try:
        mr.insert()
        mr.submit()
        mr.reload()
        mr.reject(reason="Hết ngân sách quý")
        mr.reload()
        ok = (mr.status == "Rejected" and mr.rejection_reason == "Hết ngân sách quý")
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK rejected with reason"}
        return {"pass": False, "msg": f"X status={mr.status} reason={mr.rejection_reason}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_create_po_blocked_when_pending():
    """submit (Pending) + create_purchase_orders → SC-E-MR-NOT-APPROVED."""
    item = _make_item("POBLOCK")
    mr = _make_mr([{"item": item.name, "qty": 5, "uom": item.uom}])
    try:
        mr.insert()
        mr.submit()
        mr.reload()
        try:
            mr.create_purchase_orders()
            frappe.db.rollback()
            return {"pass": False, "msg": "X did not throw — PO allowed in Pending"}
        except frappe.ValidationError as e:
            msg = str(e)
            frappe.db.rollback()
            if "SC-E-MR-NOT-APPROVED" in msg:
                return {"pass": True, "msg": f"OK: {msg[:120]}"}
            return {"pass": False, "msg": f"Wrong error: {msg[:120]}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X setup threw: {str(e)[:120]}"}


def test_auto_create_mr_when_below_reorder():
    """UC-07 luồng 1a: tồn ≤ reorder_level → scheduler auto-tạo Draft MR."""
    from frappe.utils import flt
    from supplycore.m2_planning.tasks import check_reorder_levels
    from supplycore.supplycore.doctype.sc_stock_ledger_entry.sc_stock_ledger_entry import SCStockLedgerEntry

    wh = _pick_warehouse()
    item = _make_item("AUTORE", reorder_level=20, max_stock=100, standard_order_qty=50)

    # Seed current stock = 5 (below reorder 20)
    SCStockLedgerEntry.post(
        item=item.name, warehouse=wh, qty_change=5,
        voucher_type="Manual", voucher_no=f"UC07-AUTO-{random_string(6)}",
        posting_date=today(),
    )

    # Clear any existing auto-generated MR for this warehouse today
    existing = frappe.get_all("SC Material Request", filters={
        "warehouse": wh, "auto_generated": 1, "docstatus": 0,
        "transaction_date": today(),
    }, pluck="name")
    for n in existing:
        frappe.delete_doc("SC Material Request", n, force=True, ignore_permissions=True)

    res = check_reorder_levels()
    # Find created MR
    mrs = frappe.get_all("SC Material Request", filters={
        "warehouse": wh, "auto_generated": 1, "docstatus": 0,
        "transaction_date": today(),
    }, fields=["name"])
    matching_mr = None
    for mr_row in mrs:
        items = frappe.get_all("SC Material Request Item",
            filters={"parent": mr_row.name, "item": item.name},
            fields=["item", "qty"])
        if items:
            matching_mr = (mr_row.name, items[0])
            break

    frappe.db.rollback()

    if not matching_mr:
        return {"pass": False, "msg": f"X no Draft MR created for item {item.name}. result={res}"}
    mr_name, mr_item = matching_mr
    # Expected qty = standard_order_qty = 50
    if abs(flt(mr_item.qty) - 50) < 0.01:
        return {"pass": True, "msg": f"OK Draft MR {mr_name} created with qty=50 (EOQ)"}
    return {"pass": False, "msg": f"X qty mismatch: expected 50, got {mr_item.qty}"}


def test_fc_price_auto_fetched():
    """row.framework_contract set → estimated_unit_cost = FC unit_price."""
    from frappe.utils import flt
    item = _make_item("FCPRICE")
    sup = _pick_supplier()

    fc = frappe.new_doc("Framework Contract")
    fc.supplier = sup
    fc.contract_number = f"UC07-FC-{random_string(6)}"
    fc.contract_date = add_days(today(), -10)
    fc.valid_from = add_days(today(), -5)
    fc.valid_to = add_days(today(), 365)
    fc.total_value = 10_000_000
    fc.append("items", {
        "item_code": item.name, "uom": item.uom,
        "contract_qty": 100, "unit_price": 75_000,
    })
    fc.flags.ignore_permissions = True
    fc.insert()

    mr = _make_mr([{
        "item": item.name, "qty": 5, "uom": item.uom,
        "framework_contract": fc.name,
        "estimated_unit_cost": 1,  # should be overridden by FC price
    }])
    try:
        mr.insert()
        row = mr.items[0]
        fetched = flt(row.estimated_unit_cost)
        frappe.db.rollback()
        if abs(fetched - 75_000) < 0.01:
            return {"pass": True, "msg": f"OK FC price fetched: {fetched}"}
        return {"pass": False, "msg": f"X expected 75000, got {fetched}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def run():
    tests = [
        test_qty_zero_rejected,
        test_schedule_before_transaction_rejected,
        test_no_supplier_purchase_rejected,
        test_no_supplier_internal_transfer_ok,
        test_submit_goes_to_pending,
        test_approve_changes_status,
        test_reject_requires_reason,
        test_reject_with_reason_ok,
        test_create_po_blocked_when_pending,
        test_auto_create_mr_when_below_reorder,
        test_fc_price_auto_fetched,
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
