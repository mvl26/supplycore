"""Test UC-09 — Tiếp nhận hàng và tạo Purchase Receipt.

Run individual: bench --site supplycore execute supplycore.tests.uc09_test.test_<name>
Run all:        bench --site supplycore execute supplycore.tests.uc09_test.run
"""

import frappe
from frappe.utils import today, add_days, random_string, flt


def _pick_warehouse() -> str:
    rows = frappe.get_all("SC Warehouse", filters={"is_group": 0, "disabled": 0},
                           pluck="name", order_by="name", limit=1)
    if not rows:
        frappe.throw("uc09_test: cần seed SC Warehouse")
    return rows[0]


def _pick_supplier_with_email() -> str:
    rows = frappe.get_all("SC Supplier", filters={"disabled": 0},
                           fields=["name", "email_id"], order_by="name", limit=5)
    if not rows:
        frappe.throw("uc09_test: cần seed SC Supplier")
    for r in rows:
        if r.email_id:
            return r.name
    frappe.db.set_value("SC Supplier", rows[0].name, "email_id", "test-supplier@example.com")
    return rows[0].name


def _get_uom() -> str:
    uom = frappe.db.get_value("SC UOM", {}, "name")
    if not uom:
        frappe.throw("uc09_test: cần seed SC UOM")
    return uom


def _make_item(suffix: str, **kwargs):
    item = frappe.new_doc("SC Item")
    item.item_code = f"UC09-{suffix}-{random_string(5)}"
    item.item_name = f"UC-09 test {suffix}"
    item.uom = _get_uom()
    item.is_stock_item = 1
    item.is_purchase_item = 1
    sup = frappe.db.get_value("SC Supplier", {"disabled": 0}, "name")
    if sup:
        item.default_supplier = sup
    item.flags.ignore_permissions = True
    for k, v in kwargs.items():
        setattr(item, k, v)
    item.insert()
    return item


def _make_submitted_po(supplier: str, item_code: str, qty: float, rate: float):
    """Helper: tạo PO Draft → workflow → submit (Sent to Supplier)."""
    from supplycore.supplycore.doctype.sc_purchase_order.sc_purchase_order import SCPurchaseOrder

    po = frappe.new_doc("SC Purchase Order")
    po.supplier = supplier
    po.transaction_date = today()
    po.schedule_date = add_days(today(), 7)
    po.to_warehouse = _pick_warehouse()
    po.append("items", {
        "item": item_code, "qty": qty, "uom": frappe.db.get_value("SC Item", item_code, "uom"),
        "rate": rate, "warehouse": _pick_warehouse(),
    })
    po.flags.ignore_permissions = True
    po.insert()
    po.submit_for_review(); po.reload()
    po.approve_as_manager(); po.reload()
    if po.approval_stage == "Executive Review":
        po.approve_as_executive(); po.reload()
    po.submit(); po.reload()
    return po


# ---------- Tests ----------

def test_make_pr_sets_po_qty():
    """make_pr_from_po → row.po_qty = PO Item.qty."""
    from supplycore.supplycore.doctype.sc_purchase_order.sc_purchase_order import make_pr_from_po

    sup = _pick_supplier_with_email()
    item = _make_item("MAKEPR")
    po = _make_submitted_po(sup, item.name, 50, 10_000)

    pr_name = make_pr_from_po(po.name)
    pr = frappe.get_doc("SC Purchase Receipt", pr_name)
    row = pr.items[0]
    frappe.db.rollback()
    if abs(flt(row.po_qty) - 50.0) < 0.01:
        return {"pass": True, "msg": f"OK po_qty={row.po_qty}"}
    return {"pass": False, "msg": f"X po_qty={row.po_qty} (expected 50)"}


def test_over_receipt_flagged():
    """qty > po_qty → has_over_receipt=1."""
    sup = _pick_supplier_with_email()
    item = _make_item("OVRFL")
    po = _make_submitted_po(sup, item.name, 50, 10_000)

    pr = frappe.new_doc("SC Purchase Receipt")
    pr.supplier = sup
    pr.purchase_order = po.name
    pr.posting_date = today()
    pr.to_warehouse = _pick_warehouse()
    pr.qc_required = 0  # skip QI for simplicity
    pr.append("items", {
        "item": item.name, "qty": 60, "uom": item.uom,  # over 50
        "rate": 10_000, "warehouse": _pick_warehouse(),
        "po_qty": 50,
    })
    pr.flags.ignore_permissions = True
    try:
        pr.insert()
        pr.reload()
        ok = (pr.has_over_receipt == 1 and flt(pr.items[0].over_received_qty) == 10.0)
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK has_over_receipt=1 over_qty=10"}
        return {"pass": False, "msg": f"X has_over={pr.has_over_receipt} over_qty={pr.items[0].over_received_qty}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_over_receipt_blocks_submit_without_ack():
    """over + ack=0 → submit throw SC-E-OVER-RECEIPT."""
    sup = _pick_supplier_with_email()
    item = _make_item("OVRBLK")
    po = _make_submitted_po(sup, item.name, 50, 10_000)

    pr = frappe.new_doc("SC Purchase Receipt")
    pr.supplier = sup
    pr.purchase_order = po.name
    pr.posting_date = today()
    pr.to_warehouse = _pick_warehouse()
    pr.qc_required = 0
    pr.append("items", {
        "item": item.name, "qty": 60, "uom": item.uom,
        "rate": 10_000, "warehouse": _pick_warehouse(), "po_qty": 50,
    })
    pr.flags.ignore_permissions = True
    pr.insert()
    try:
        pr.submit()
        frappe.db.rollback()
        return {"pass": False, "msg": "X submit không bị block"}
    except frappe.ValidationError as e:
        msg = str(e)
        frappe.db.rollback()
        if "SC-E-OVER-RECEIPT" in msg:
            return {"pass": True, "msg": f"OK: {msg[:120]}"}
        return {"pass": False, "msg": f"Wrong error: {msg[:120]}"}


def test_over_receipt_allowed_with_ack():
    """over + ack=1 → submit OK."""
    sup = _pick_supplier_with_email()
    item = _make_item("OVRACK")
    po = _make_submitted_po(sup, item.name, 50, 10_000)

    pr = frappe.new_doc("SC Purchase Receipt")
    pr.supplier = sup
    pr.purchase_order = po.name
    pr.posting_date = today()
    pr.to_warehouse = _pick_warehouse()
    pr.qc_required = 0
    pr.over_receipt_acknowledged = 1
    pr.append("items", {
        "item": item.name, "qty": 60, "uom": item.uom,
        "rate": 10_000, "warehouse": _pick_warehouse(), "po_qty": 50,
        "expiry_date": add_days(today(), 365),
    })
    pr.flags.ignore_permissions = True
    try:
        pr.insert()
        pr.submit()
        pr.reload()
        ok = (pr.docstatus == 1)
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK submitted {pr.name} with over-receipt ack"}
        return {"pass": False, "msg": f"X docstatus={pr.docstatus}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_no_po_requires_reason():
    """PR không PO + không reason → submit throw SC-E-NO-PO-REASON."""
    sup = _pick_supplier_with_email()
    item = _make_item("NOPO")

    pr = frappe.new_doc("SC Purchase Receipt")
    pr.supplier = sup
    pr.posting_date = today()
    pr.to_warehouse = _pick_warehouse()
    pr.qc_required = 0
    pr.append("items", {
        "item": item.name, "qty": 5, "uom": item.uom,
        "rate": 1000, "warehouse": _pick_warehouse(),
    })
    pr.flags.ignore_permissions = True
    pr.insert()
    try:
        pr.submit()
        frappe.db.rollback()
        return {"pass": False, "msg": "X submit không block khi no PO + no reason"}
    except frappe.ValidationError as e:
        msg = str(e)
        frappe.db.rollback()
        if "SC-E-NO-PO-REASON" in msg:
            return {"pass": True, "msg": f"OK: {msg[:120]}"}
        return {"pass": False, "msg": f"Wrong error: {msg[:120]}"}


def test_no_po_with_reason_ok():
    """PR không PO + có reason → submit OK."""
    sup = _pick_supplier_with_email()
    item = _make_item("NOPOR")

    pr = frappe.new_doc("SC Purchase Receipt")
    pr.supplier = sup
    pr.posting_date = today()
    pr.to_warehouse = _pick_warehouse()
    pr.qc_required = 0
    pr.no_po_reason = "Hàng tài trợ khẩn cấp, không qua PO chính thức"
    pr.append("items", {
        "item": item.name, "qty": 5, "uom": item.uom,
        "rate": 1000, "warehouse": _pick_warehouse(),
        "expiry_date": add_days(today(), 365),
    })
    pr.flags.ignore_permissions = True
    try:
        pr.insert()
        pr.submit()
        pr.reload()
        ok = (pr.docstatus == 1)
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK PR no-PO submitted with reason"}
        return {"pass": False, "msg": f"X docstatus={pr.docstatus}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_under_receipt_create_backorder():
    """PR submitted với qty < po_qty → create_backorder() tạo Draft PR với qty=remaining."""
    sup = _pick_supplier_with_email()
    item = _make_item("BACK")
    po = _make_submitted_po(sup, item.name, 100, 10_000)

    pr = frappe.new_doc("SC Purchase Receipt")
    pr.supplier = sup
    pr.purchase_order = po.name
    pr.posting_date = today()
    pr.to_warehouse = _pick_warehouse()
    pr.qc_required = 0
    pr.append("items", {
        "item": item.name, "qty": 60, "uom": item.uom,  # received 60, short 40
        "rate": 10_000, "warehouse": _pick_warehouse(), "po_qty": 100,
        "expiry_date": add_days(today(), 365),
    })
    pr.flags.ignore_permissions = True
    try:
        pr.insert()
        pr.submit()
        pr.reload()
        bo_name = pr.create_backorder()
        bo = frappe.get_doc("SC Purchase Receipt", bo_name)
        row = bo.items[0]
        ok = (bo.backorder_for == pr.name
              and abs(flt(row.qty) - 40.0) < 0.01
              and bo.docstatus == 0)
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK backorder {bo_name} qty=40"}
        return {"pass": False, "msg": f"X backorder qty={row.qty}, for={bo.backorder_for}, doc={bo.docstatus}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_full_receipt_no_backorder():
    """PR submitted nhận đủ → create_backorder() throw SC-E-BACKORDER-NOTHING."""
    sup = _pick_supplier_with_email()
    item = _make_item("FULL")
    po = _make_submitted_po(sup, item.name, 50, 10_000)

    pr = frappe.new_doc("SC Purchase Receipt")
    pr.supplier = sup
    pr.purchase_order = po.name
    pr.posting_date = today()
    pr.to_warehouse = _pick_warehouse()
    pr.qc_required = 0
    pr.append("items", {
        "item": item.name, "qty": 50, "uom": item.uom,
        "rate": 10_000, "warehouse": _pick_warehouse(), "po_qty": 50,
        "expiry_date": add_days(today(), 365),
    })
    pr.flags.ignore_permissions = True
    try:
        pr.insert()
        pr.submit()
        pr.reload()
        try:
            pr.create_backorder()
            frappe.db.rollback()
            return {"pass": False, "msg": "X did not throw on full receipt"}
        except frappe.ValidationError as e:
            msg = str(e)
            frappe.db.rollback()
            if "SC-E-BACKORDER-NOTHING" in msg:
                return {"pass": True, "msg": f"OK: {msg[:120]}"}
            return {"pass": False, "msg": f"Wrong error: {msg[:120]}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X setup: {str(e)[:120]}"}


def test_po_status_received_when_full():
    """PR submitted nhận đủ → PO status=Received (UC 8a)."""
    sup = _pick_supplier_with_email()
    item = _make_item("PSTAT")
    po = _make_submitted_po(sup, item.name, 30, 5_000)

    pr = frappe.new_doc("SC Purchase Receipt")
    pr.supplier = sup
    pr.purchase_order = po.name
    pr.posting_date = today()
    pr.to_warehouse = _pick_warehouse()
    pr.qc_required = 0
    pr.append("items", {
        "item": item.name, "qty": 30, "uom": item.uom,
        "rate": 5_000, "warehouse": _pick_warehouse(), "po_qty": 30,
        "expiry_date": add_days(today(), 365),
    })
    pr.flags.ignore_permissions = True
    try:
        pr.insert()
        pr.submit()
        po.reload()
        ok = (po.status == "Received")
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK PO {po.name} status=Received"}
        return {"pass": False, "msg": f"X PO status={po.status}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def run():
    tests = [
        test_make_pr_sets_po_qty,
        test_over_receipt_flagged,
        test_over_receipt_blocks_submit_without_ack,
        test_over_receipt_allowed_with_ack,
        test_no_po_requires_reason,
        test_no_po_with_reason_ok,
        test_under_receipt_create_backorder,
        test_full_receipt_no_backorder,
        test_po_status_received_when_full,
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
