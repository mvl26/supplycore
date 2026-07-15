"""Test UC-25 — Payment Entry.

Run individual: bench --site supplycore execute supplycore.tests.uc25_test.test_<name>
Run all:        bench --site supplycore execute supplycore.tests.uc25_test.run
"""

import frappe
from frappe.utils import today, add_days, random_string, flt


def _pick_warehouse() -> str:
    rows = frappe.get_all("SC Warehouse", filters={"is_group": 0, "disabled": 0},
                           pluck="name", order_by="name", limit=1)
    if not rows:
        frappe.throw("uc25_test: cần seed SC Warehouse")
    return rows[0]


def _pick_supplier_with_email() -> str:
    rows = frappe.get_all("SC Supplier", filters={"disabled": 0},
                           fields=["name", "email_id"], order_by="name", limit=5)
    for r in rows:
        if r.email_id:
            return r.name
    frappe.db.set_value("SC Supplier", rows[0].name, "email_id", "uc25@example.com")
    return rows[0].name


def _get_uom() -> str:
    return frappe.db.get_value("SC UOM", {}, "name")


def _make_item(suffix: str):
    item = frappe.new_doc("SC Item")
    item.item_code = f"UC25-{suffix}-{random_string(5)}"
    item.item_name = f"UC-25 test {suffix}"
    item.uom = _get_uom()
    item.is_stock_item = 1
    sup = frappe.db.get_value("SC Supplier", {"disabled": 0}, "name")
    if sup:
        item.default_supplier = sup
    item.flags.ignore_permissions = True
    item.insert()
    return item


def _make_submitted_pi(supplier, item, qty=10, rate=1000):
    """Helper: PO → PR → PI submitted (3-way Match)."""
    wh = _pick_warehouse()
    po = frappe.new_doc("SC Purchase Order")
    po.supplier = supplier
    po.transaction_date = today()
    po.schedule_date = add_days(today(), 7)
    po.to_warehouse = wh
    po.append("items", {"item": item.name, "qty": qty, "uom": _get_uom(),
                          "rate": rate, "warehouse": wh})
    po.flags.ignore_permissions = True
    po.insert()
    po.submit_for_review(); po.reload()
    po.approve_as_manager(); po.reload()
    if po.approval_stage == "Executive Review":
        po.approve_as_executive(); po.reload()
    po.submit(); po.reload()

    pr = frappe.new_doc("SC Purchase Receipt")
    pr.supplier = supplier
    pr.purchase_order = po.name
    pr.posting_date = today()
    pr.to_warehouse = wh
    pr.qc_required = 0
    pr.append("items", {"item": item.name, "qty": qty, "uom": _get_uom(),
                          "rate": rate, "warehouse": wh, "po_qty": qty,
                          "expiry_date": add_days(today(), 365)})
    pr.flags.ignore_permissions = True
    pr.insert()
    pr.submit()

    pi = frappe.new_doc("SC Purchase Invoice")
    pi.supplier = supplier
    pi.supplier_invoice_no = f"PI-{random_string(6)}"
    pi.invoice_date = today()
    pi.due_date = add_days(today(), 30)
    pi.purchase_order = po.name
    pi.purchase_receipt = pr.name
    pi.vat_rate = 10
    pi.append("items", {"item": item.name, "qty": qty, "uom": _get_uom(),
                          "rate": rate})
    pi.flags.ignore_permissions = True
    pi.insert()
    pi.submit()
    return pi


def _make_pe(supplier, refs: list, amount: float = None, **kwargs):
    """refs = list {pi_name, allocated_amount}."""
    pe = frappe.new_doc("SC Payment Entry")
    pe.supplier = supplier
    pe.payment_date = today()
    pe.payment_method = "Bank Transfer"
    pe.bank_account = "BIDV-1234567"
    pe.reference_no = f"BANK-{random_string(8)}"
    pe.reference_date = today()
    total = 0
    for r in refs:
        pe.append("references", {
            "purchase_invoice": r["pi_name"],
            "allocated_amount": flt(r["allocated_amount"]),
        })
        total += flt(r["allocated_amount"])
    pe.amount = amount if amount is not None else total
    pe.flags.ignore_permissions = True
    for k, v in kwargs.items():
        setattr(pe, k, v)
    return pe


# ---------- Tests ----------

def test_pe_create_basic():
    """Tạo PE + ref PI outstanding → save OK."""
    sup = _pick_supplier_with_email()
    item = _make_item("BASIC")
    pi = _make_submitted_pi(sup, item, qty=5, rate=1000)
    pe = _make_pe(sup, [{"pi_name": pi.name, "allocated_amount": pi.outstanding_amount}])
    try:
        pe.insert()
        ok = (pe.name and pe.docstatus == 0)
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK PE {pe.name}"}
        return {"pass": False, "msg": f"X doc={pe.docstatus}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_pe_ref_pi_payment_hold_blocked():
    """Ref PI có payment_hold=1 → SC-E-PE-PAYMENT-HOLD."""
    sup = _pick_supplier_with_email()
    item = _make_item("HOLD")
    pi = _make_submitted_pi(sup, item, qty=5, rate=1000)
    # Set hold manual
    frappe.db.set_value("SC Purchase Invoice", pi.name, "payment_hold", 1)
    pe = _make_pe(sup, [{"pi_name": pi.name, "allocated_amount": pi.outstanding_amount}])
    try:
        pe.insert()
        frappe.db.rollback()
        return {"pass": False, "msg": "X did not throw"}
    except frappe.ValidationError as e:
        msg = str(e)
        frappe.db.rollback()
        if "SC-E-PE-PAYMENT-HOLD" in msg:
            return {"pass": True, "msg": f"OK: {msg[:120]}"}
        return {"pass": False, "msg": f"Wrong error: {msg[:120]}"}


def test_pe_allocated_exceeds_outstanding_blocked():
    """allocated > PI.outstanding → throw."""
    sup = _pick_supplier_with_email()
    item = _make_item("EXCEED")
    pi = _make_submitted_pi(sup, item, qty=5, rate=1000)
    pe = _make_pe(sup, [{"pi_name": pi.name,
                          "allocated_amount": flt(pi.outstanding_amount) + 10_000}])
    try:
        pe.insert()
        frappe.db.rollback()
        return {"pass": False, "msg": "X did not throw"}
    except frappe.ValidationError as e:
        msg = str(e)
        frappe.db.rollback()
        if "Phân bổ" in msg or "outstanding" in msg.lower():
            return {"pass": True, "msg": f"OK: {msg[:120]}"}
        return {"pass": False, "msg": f"Wrong error: {msg[:120]}"}


def test_pe_allocated_total_must_equal_amount():
    """Submit với allocated_total ≠ amount → throw."""
    sup = _pick_supplier_with_email()
    item = _make_item("MISMA")
    pi = _make_submitted_pi(sup, item, qty=5, rate=1000)
    pe = _make_pe(sup, [{"pi_name": pi.name,
                          "allocated_amount": flt(pi.outstanding_amount)}],
                   amount=flt(pi.outstanding_amount) + 100)  # amount > allocated
    try:
        pe.insert()
        pe.submit()
        frappe.db.rollback()
        return {"pass": False, "msg": "X submit không throw"}
    except frappe.ValidationError as e:
        msg = str(e)
        frappe.db.rollback()
        if "Tổng phân bổ" in msg or "≠ Số tiền" in msg:
            return {"pass": True, "msg": f"OK: {msg[:120]}"}
        return {"pass": False, "msg": f"Wrong error: {msg[:120]}"}


def test_pe_manager_below_threshold():
    """amount<50tr → approval_level=Manager."""
    sup = _pick_supplier_with_email()
    item = _make_item("MGR")
    pi = _make_submitted_pi(sup, item, qty=5, rate=1000)  # ~5500 < 50tr
    pe = _make_pe(sup, [{"pi_name": pi.name, "allocated_amount": pi.outstanding_amount}])
    try:
        pe.insert()
        ok = (pe.approval_level == "Manager")
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": "OK Manager level"}
        return {"pass": False, "msg": f"X level={pe.approval_level}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_pe_executive_above_threshold():
    """amount≥50tr → approval_level=Executive."""
    sup = _pick_supplier_with_email()
    item = _make_item("EXEC")
    pi = _make_submitted_pi(sup, item, qty=100, rate=500_000)  # 50tr
    pe = _make_pe(sup, [{"pi_name": pi.name, "allocated_amount": pi.outstanding_amount}])
    try:
        pe.insert()
        ok = (pe.approval_level == "Executive")
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": "OK Executive level"}
        return {"pass": False, "msg": f"X level={pe.approval_level} amount={pe.amount}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_pe_submit_updates_pi_to_paid():
    """PE full amount → PI.status=Paid + outstanding=0."""
    sup = _pick_supplier_with_email()
    item = _make_item("PAID")
    pi = _make_submitted_pi(sup, item, qty=5, rate=1000)
    pe = _make_pe(sup, [{"pi_name": pi.name, "allocated_amount": pi.outstanding_amount}])
    try:
        pe.insert()
        pe.submit()
        pi.reload()
        ok = (pi.status == "Paid" and abs(flt(pi.outstanding_amount)) < 0.01)
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": "OK PI Paid"}
        return {"pass": False, "msg": f"X status={pi.status} outstanding={pi.outstanding_amount}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_pe_partial_keeps_pi_partly_paid():
    """PE half → PI status=Partly Paid."""
    sup = _pick_supplier_with_email()
    item = _make_item("PARTIAL")
    pi = _make_submitted_pi(sup, item, qty=10, rate=1000)
    half = flt(pi.outstanding_amount) / 2
    pe = _make_pe(sup, [{"pi_name": pi.name, "allocated_amount": half}])
    try:
        pe.insert()
        pe.submit()
        pi.reload()
        ok = (pi.status == "Partly Paid")
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": "OK PI Partly Paid"}
        return {"pass": False, "msg": f"X status={pi.status}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_auto_load_outstanding_invoices():
    """Supplier có 2 PI outstanding → API trả 2."""
    from supplycore.m8_accounting.doctype.sc_payment_entry.sc_payment_entry import auto_load_outstanding_invoices
    sup = _pick_supplier_with_email()
    item = _make_item("AUTOL")
    pi1 = _make_submitted_pi(sup, item, qty=5, rate=1000)
    pi2 = _make_submitted_pi(sup, item, qty=3, rate=2000)
    try:
        res = auto_load_outstanding_invoices(sup)
        names = [r["name"] for r in res]
        frappe.db.rollback()
        if pi1.name in names and pi2.name in names:
            return {"pass": True, "msg": f"OK auto-loaded {len(res)} PIs"}
        return {"pass": False, "msg": f"X names={names[:5]}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_pe_cancel_reverts_pi_outstanding():
    """Cancel PE → PI.outstanding restore."""
    sup = _pick_supplier_with_email()
    item = _make_item("CANC")
    pi = _make_submitted_pi(sup, item, qty=5, rate=1000)
    original_outstanding = flt(pi.outstanding_amount)
    pe = _make_pe(sup, [{"pi_name": pi.name, "allocated_amount": original_outstanding}])
    try:
        pe.insert()
        pe.submit()
        pe.cancel()
        pi.reload()
        restored = (abs(flt(pi.outstanding_amount) - original_outstanding) < 0.01)
        frappe.db.rollback()
        if restored:
            return {"pass": True, "msg": f"OK outstanding restored to {original_outstanding}"}
        return {"pass": False, "msg": f"X outstanding={pi.outstanding_amount} expected={original_outstanding}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def run():
    tests = [
        test_pe_create_basic,
        test_pe_ref_pi_payment_hold_blocked,
        test_pe_allocated_exceeds_outstanding_blocked,
        test_pe_allocated_total_must_equal_amount,
        test_pe_manager_below_threshold,
        test_pe_executive_above_threshold,
        test_pe_submit_updates_pi_to_paid,
        test_pe_partial_keeps_pi_partly_paid,
        test_auto_load_outstanding_invoices,
        test_pe_cancel_reverts_pi_outstanding,
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
