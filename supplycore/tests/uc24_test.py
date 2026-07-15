"""Test UC-24 — Purchase Invoice 3-way match.

Run individual: bench --site supplycore execute supplycore.tests.uc24_test.test_<name>
Run all:        bench --site supplycore execute supplycore.tests.uc24_test.run
"""

import frappe
from frappe.utils import today, add_days, random_string, flt


def _pick_warehouse() -> str:
    rows = frappe.get_all("SC Warehouse", filters={"is_group": 0, "disabled": 0},
                           pluck="name", order_by="name", limit=1)
    if not rows:
        frappe.throw("uc24_test: cần seed SC Warehouse")
    return rows[0]


def _pick_supplier_with_email() -> str:
    rows = frappe.get_all("SC Supplier", filters={"disabled": 0},
                           fields=["name", "email_id"], order_by="name", limit=5)
    for r in rows:
        if r.email_id:
            return r.name
    frappe.db.set_value("SC Supplier", rows[0].name, "email_id", "uc24@example.com")
    return rows[0].name


def _get_uom() -> str:
    return frappe.db.get_value("SC UOM", {}, "name")


def _make_item(suffix: str):
    item = frappe.new_doc("SC Item")
    item.item_code = f"UC24-{suffix}-{random_string(5)}"
    item.item_name = f"UC-24 test {suffix}"
    item.uom = _get_uom()
    item.is_stock_item = 1
    sup = frappe.db.get_value("SC Supplier", {"disabled": 0}, "name")
    if sup:
        item.default_supplier = sup
    item.flags.ignore_permissions = True
    item.insert()
    return item


def _make_pi(supplier, supplier_invoice_no, items, **kwargs):
    pi = frappe.new_doc("SC Purchase Invoice")
    pi.supplier = supplier
    pi.supplier_invoice_no = supplier_invoice_no
    pi.invoice_date = today()
    pi.due_date = add_days(today(), 30)
    pi.vat_rate = 10
    for it in items:
        pi.append("items", {
            "item": it["item"], "uom": _get_uom(),
            "qty": flt(it["qty"]), "rate": flt(it["rate"]),
        })
    pi.flags.ignore_permissions = True
    for k, v in kwargs.items():
        setattr(pi, k, v)
    return pi


# ---------- Tests ----------

def test_pi_create_basic():
    """Tạo PI với supplier + items → save OK."""
    sup = _pick_supplier_with_email()
    item = _make_item("BASIC")
    pi = _make_pi(sup, f"INV-{random_string(6)}",
                   [{"item": item.name, "qty": 10, "rate": 1000}])
    try:
        pi.insert()
        ok = (pi.name and pi.docstatus == 0)
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK PI {pi.name}"}
        return {"pass": False, "msg": f"X doc={pi.docstatus}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_pi_duplicate_invoice_no_blocked():
    """2 PI cùng (supplier, invoice_no) → SC-E-PI-DUPLICATE."""
    sup = _pick_supplier_with_email()
    item = _make_item("DUP")
    inv_no = f"INV-DUP-{random_string(6)}"
    pi1 = _make_pi(sup, inv_no, [{"item": item.name, "qty": 5, "rate": 1000}])
    pi1.insert()
    pi2 = _make_pi(sup, inv_no, [{"item": item.name, "qty": 5, "rate": 1000}])
    try:
        pi2.insert()
        frappe.db.rollback()
        return {"pass": False, "msg": "X did not throw"}
    except frappe.ValidationError as e:
        msg = str(e)
        frappe.db.rollback()
        if "SC-E-PI-DUPLICATE" in msg:
            return {"pass": True, "msg": f"OK: {msg[:120]}"}
        return {"pass": False, "msg": f"Wrong error: {msg[:120]}"}


def test_pi_3way_match_no_po_na():
    """PI không có PO → status=Not Applicable."""
    sup = _pick_supplier_with_email()
    item = _make_item("NOPO")
    pi = _make_pi(sup, f"INV-NOPO-{random_string(6)}",
                   [{"item": item.name, "qty": 5, "rate": 1000}])
    try:
        pi.insert()
        ok = (pi.three_way_match_status == "Not Applicable")
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": "OK NA without PO"}
        return {"pass": False, "msg": f"X status={pi.three_way_match_status}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def _make_submitted_po_and_pr(sup, item, qty, rate):
    """Helper: tạo PO submitted + PR submitted để test 3-way."""
    from supplycore.supplycore.doctype.sc_purchase_order.sc_purchase_order import SCPurchaseOrder
    wh = _pick_warehouse()
    po = frappe.new_doc("SC Purchase Order")
    po.supplier = sup
    po.transaction_date = today()
    po.schedule_date = add_days(today(), 7)
    po.to_warehouse = wh
    po.append("items", {
        "item": item, "qty": qty, "uom": _get_uom(),
        "rate": rate, "warehouse": wh,
    })
    po.flags.ignore_permissions = True
    po.insert()
    po.submit_for_review(); po.reload()
    po.approve_as_manager(); po.reload()
    if po.approval_stage == "Executive Review":
        po.approve_as_executive(); po.reload()
    po.submit(); po.reload()

    pr = frappe.new_doc("SC Purchase Receipt")
    pr.supplier = sup
    pr.purchase_order = po.name
    pr.posting_date = today()
    pr.to_warehouse = wh
    pr.qc_required = 0
    pr.append("items", {
        "item": item, "qty": qty, "uom": _get_uom(),
        "rate": rate, "warehouse": wh, "po_qty": qty,
        "expiry_date": add_days(today(), 365),
    })
    pr.flags.ignore_permissions = True
    pr.insert()
    pr.submit()
    return po, pr


def test_pi_3way_match_exact():
    """PI subtotal = PO grand_total = PR total → status=Match."""
    sup = _pick_supplier_with_email()
    item = _make_item("EXACT")
    po, pr = _make_submitted_po_and_pr(sup, item.name, 10, 1000)
    pi = _make_pi(sup, f"INV-EX-{random_string(6)}",
                   [{"item": item.name, "qty": 10, "rate": 1000}],
                   purchase_order=po.name, purchase_receipt=pr.name)
    try:
        pi.insert()
        ok = (pi.three_way_match_status == "Match")
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": "OK Match exact"}
        return {"pass": False, "msg": f"X status={pi.three_way_match_status} var={pi.match_variance_amount}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_pi_3way_match_within_tolerance():
    """Chênh 0.5% → status=Match (tolerance 1%)."""
    sup = _pick_supplier_with_email()
    item = _make_item("TOLER")
    po, pr = _make_submitted_po_and_pr(sup, item.name, 10, 1000)  # PO=10000
    # PI 10050 = +0.5%
    pi = _make_pi(sup, f"INV-TOL-{random_string(6)}",
                   [{"item": item.name, "qty": 10, "rate": 1005}],
                   purchase_order=po.name, purchase_receipt=pr.name)
    try:
        pi.insert()
        ok = (pi.three_way_match_status == "Match")
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": "OK within tolerance"}
        return {"pass": False, "msg": f"X status={pi.three_way_match_status}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_pi_3way_match_mismatch():
    """Chênh 3% → status=Mismatch + payment_hold=1."""
    sup = _pick_supplier_with_email()
    item = _make_item("MISM")
    po, pr = _make_submitted_po_and_pr(sup, item.name, 10, 1000)  # PO=10000
    # PI 10300 = +3% > tolerance 1%
    pi = _make_pi(sup, f"INV-MM-{random_string(6)}",
                   [{"item": item.name, "qty": 10, "rate": 1030}],
                   purchase_order=po.name, purchase_receipt=pr.name)
    try:
        pi.insert()
        ok = (pi.three_way_match_status == "Mismatch" and pi.payment_hold == 1)
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": "OK Mismatch + hold"}
        return {"pass": False, "msg": f"X status={pi.three_way_match_status} hold={pi.payment_hold}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_pi_submit_blocked_without_explanation_on_mismatch():
    """Mismatch + no explanation + submit → SC-E-PI-MISMATCH-EXPLANATION."""
    sup = _pick_supplier_with_email()
    item = _make_item("BLKEXP")
    po, pr = _make_submitted_po_and_pr(sup, item.name, 10, 1000)
    pi = _make_pi(sup, f"INV-BE-{random_string(6)}",
                   [{"item": item.name, "qty": 10, "rate": 1030}],
                   purchase_order=po.name, purchase_receipt=pr.name)
    try:
        pi.insert()
        try:
            pi.submit()
            frappe.db.rollback()
            return {"pass": False, "msg": "X submit không block"}
        except frappe.ValidationError as e:
            msg = str(e)
            frappe.db.rollback()
            if "SC-E-PI-MISMATCH-EXPLANATION" in msg:
                return {"pass": True, "msg": f"OK: {msg[:120]}"}
            return {"pass": False, "msg": f"Wrong error: {msg[:120]}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X setup: {str(e)[:120]}"}


def test_pi_submit_with_explanation_on_mismatch():
    """Mismatch + explanation + submit → OK."""
    sup = _pick_supplier_with_email()
    item = _make_item("OKEXP")
    po, pr = _make_submitted_po_and_pr(sup, item.name, 10, 1000)
    pi = _make_pi(sup, f"INV-OE-{random_string(6)}",
                   [{"item": item.name, "qty": 10, "rate": 1030}],
                   purchase_order=po.name, purchase_receipt=pr.name,
                   mismatch_explanation="Phụ phí vận chuyển NCC điều chỉnh giá")
    try:
        pi.insert()
        pi.submit()
        ok = (pi.docstatus == 1 and pi.status == "Approved")
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": "OK submitted with explanation"}
        return {"pass": False, "msg": f"X doc={pi.docstatus} status={pi.status}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_pi_auto_approval_when_match_below_threshold():
    """Match + below threshold (50tr) → approval_required_by=Auto."""
    sup = _pick_supplier_with_email()
    item = _make_item("AUTO")
    po, pr = _make_submitted_po_and_pr(sup, item.name, 10, 1000)  # 10000 << 50tr
    pi = _make_pi(sup, f"INV-AUTO-{random_string(6)}",
                   [{"item": item.name, "qty": 10, "rate": 1000}],
                   purchase_order=po.name, purchase_receipt=pr.name)
    try:
        pi.insert()
        ok = (pi.three_way_match_status == "Match" and pi.approval_required_by == "Auto")
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": "OK Auto approval"}
        return {"pass": False, "msg": f"X match={pi.three_way_match_status} approval={pi.approval_required_by}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_pi_executive_required_above_threshold():
    """grand_total ≥ 50tr → Executive."""
    sup = _pick_supplier_with_email()
    item = _make_item("EXEC")
    po, pr = _make_submitted_po_and_pr(sup, item.name, 100, 500_000)  # 50tr
    pi = _make_pi(sup, f"INV-EX-{random_string(6)}",
                   [{"item": item.name, "qty": 100, "rate": 500_000}],
                   purchase_order=po.name, purchase_receipt=pr.name)
    try:
        pi.insert()
        ok = (pi.approval_required_by == "Executive")
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": "OK Executive required"}
        return {"pass": False, "msg": f"X approval={pi.approval_required_by} total={pi.grand_total}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def run():
    tests = [
        test_pi_create_basic,
        test_pi_duplicate_invoice_no_blocked,
        test_pi_3way_match_no_po_na,
        test_pi_3way_match_exact,
        test_pi_3way_match_within_tolerance,
        test_pi_3way_match_mismatch,
        test_pi_submit_blocked_without_explanation_on_mismatch,
        test_pi_submit_with_explanation_on_mismatch,
        test_pi_auto_approval_when_match_below_threshold,
        test_pi_executive_required_above_threshold,
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
