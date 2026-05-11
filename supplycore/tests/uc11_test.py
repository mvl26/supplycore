"""Test UC-11 — Xử lý hàng trả lại NCC.

Run individual: bench --site supplycore execute supplycore.tests.uc11_test.test_<name>
Run all:        bench --site supplycore execute supplycore.tests.uc11_test.run
"""

import frappe
from frappe.utils import today, add_days, random_string, flt, add_to_date


def _pick_warehouse() -> str:
    rows = frappe.get_all("SC Warehouse", filters={"is_group": 0, "disabled": 0},
                           pluck="name", order_by="name", limit=1)
    if not rows:
        frappe.throw("uc11_test: cần seed SC Warehouse")
    return rows[0]


def _pick_supplier_with_email() -> str:
    rows = frappe.get_all("SC Supplier", filters={"disabled": 0},
                           fields=["name", "email_id"], order_by="name", limit=5)
    if not rows:
        frappe.throw("uc11_test: cần seed SC Supplier")
    for r in rows:
        if r.email_id:
            return r.name
    frappe.db.set_value("SC Supplier", rows[0].name, "email_id", "test-supplier@example.com")
    return rows[0].name


def _get_uom() -> str:
    uom = frappe.db.get_value("SC UOM", {}, "name")
    if not uom:
        frappe.throw("uc11_test: cần seed SC UOM")
    return uom


def _make_item(suffix: str, **kwargs):
    item = frappe.new_doc("SC Item")
    item.item_code = f"UC11-{suffix}-{random_string(5)}"
    item.item_name = f"UC-11 test {suffix}"
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


def _make_return_pr(item_code: str, supplier: str, return_reason: str = None, qty: float = 5):
    """Create a Return PR draft."""
    pr = frappe.new_doc("SC Purchase Receipt")
    pr.supplier = supplier
    pr.posting_date = today()
    pr.to_warehouse = _pick_warehouse()
    pr.is_return = 1
    pr.qc_required = 0
    pr.no_po_reason = "UC-11 return test"
    if return_reason:
        pr.return_reason = return_reason
    pr.append("items", {
        "item": item_code, "qty": qty, "uom": _get_uom(),
        "rate": 10_000, "warehouse": _pick_warehouse(),
    })
    pr.flags.ignore_permissions = True
    return pr


# ---------- Tests ----------

def test_return_pr_requires_reason():
    """Submit Return PR không reason → SC-E-RETURN-REASON."""
    sup = _pick_supplier_with_email()
    item = _make_item("NOR")
    pr = _make_return_pr(item.name, sup)
    try:
        pr.insert()
        pr.submit()
        frappe.db.rollback()
        return {"pass": False, "msg": "X submit không bị block"}
    except frappe.ValidationError as e:
        msg = str(e)
        frappe.db.rollback()
        if "SC-E-RETURN-REASON" in msg:
            return {"pass": True, "msg": f"OK: {msg[:120]}"}
        return {"pass": False, "msg": f"Wrong error: {msg[:120]}"}


def test_return_pr_with_reason_submits():
    """Return PR submit + reason → OK, return_status=Pending Supplier Response."""
    sup = _pick_supplier_with_email()
    item = _make_item("OKR")
    pr = _make_return_pr(item.name, sup, return_reason="QC Fail batch hỏng")
    try:
        pr.insert()
        pr.submit()
        pr.reload()
        ok = (pr.docstatus == 1 and pr.return_status == "Pending Supplier Response")
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK return_status={pr.return_status}"}
        return {"pass": False, "msg": f"X status={pr.return_status} doc={pr.docstatus}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_return_pr_auto_creates_debit_note():
    """Submit Return PR → auto-tạo PI is_debit_note=1, link debit_note."""
    sup = _pick_supplier_with_email()
    item = _make_item("AUTOD")
    pr = _make_return_pr(item.name, sup, return_reason="Test auto DN")
    try:
        pr.insert()
        pr.submit()
        pr.reload()
        dn = pr.debit_note
        if not dn:
            frappe.db.rollback()
            return {"pass": False, "msg": "X debit_note not set after submit"}
        pi = frappe.get_doc("SC Purchase Invoice", dn)
        ok = (pi.is_debit_note == 1 and pi.return_against_pr == pr.name)
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK Debit Note {dn} linked"}
        return {"pass": False, "msg": f"X PI is_debit={pi.is_debit_note} against={pi.return_against_pr}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_make_credit_note_sets_refunded():
    """submit + make_credit_note() → PI is_credit_note=1, return_status=Refunded."""
    sup = _pick_supplier_with_email()
    item = _make_item("CN")
    pr = _make_return_pr(item.name, sup, return_reason="Hoàn tiền")
    try:
        pr.insert()
        pr.submit()
        pr.reload()
        cn_name = pr.make_credit_note()
        pr.reload()
        pi = frappe.get_doc("SC Purchase Invoice", cn_name)
        ok = (pi.is_credit_note == 1 and pr.return_status == "Refunded"
              and pr.credit_note == cn_name)
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK Credit Note {cn_name}, status=Refunded"}
        return {"pass": False, "msg": f"X pi.is_credit={pi.is_credit_note} status={pr.return_status}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_make_debit_note_idempotent():
    """Gọi make_debit_note 2 lần → SC-E-RETURN-DN-EXISTS."""
    sup = _pick_supplier_with_email()
    item = _make_item("IDEM")
    pr = _make_return_pr(item.name, sup, return_reason="Idempotent test")
    try:
        pr.insert()
        pr.submit()
        pr.reload()
        # First call may already exist (auto), second call should throw
        try:
            pr.make_debit_note()
            frappe.db.rollback()
            return {"pass": False, "msg": "X 2nd call did not throw"}
        except frappe.ValidationError as e:
            msg = str(e)
            frappe.db.rollback()
            if "SC-E-RETURN-DN-EXISTS" in msg:
                return {"pass": True, "msg": f"OK: {msg[:120]}"}
            return {"pass": False, "msg": f"Wrong error: {msg[:120]}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X setup: {str(e)[:120]}"}


def test_link_replacement_sets_replaced():
    """link PR thường (is_return=0) → replacement_pr set, return_status=Replaced."""
    sup = _pick_supplier_with_email()
    item = _make_item("LREP")
    # Return PR
    pr = _make_return_pr(item.name, sup, return_reason="Đổi hàng")
    pr.insert(); pr.submit(); pr.reload()
    # Replacement PR (regular)
    rep = frappe.new_doc("SC Purchase Receipt")
    rep.supplier = sup
    rep.posting_date = today()
    rep.to_warehouse = _pick_warehouse()
    rep.qc_required = 0
    rep.no_po_reason = "Replacement for UC-11 test"
    rep.append("items", {
        "item": item.name, "qty": 5, "uom": _get_uom(),
        "rate": 10_000, "warehouse": _pick_warehouse(),
    })
    rep.flags.ignore_permissions = True
    rep.insert(); rep.submit()
    try:
        pr.link_replacement(rep.name)
        pr.reload()
        ok = (pr.replacement_pr == rep.name and pr.return_status == "Replaced")
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK replacement_pr={rep.name} status=Replaced"}
        return {"pass": False, "msg": f"X rep={pr.replacement_pr} status={pr.return_status}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_link_replacement_rejects_return_pr():
    """link PR is_return=1 → SC-E-RETURN-REPLACE-INVALID."""
    sup = _pick_supplier_with_email()
    item = _make_item("LREJ")
    pr = _make_return_pr(item.name, sup, return_reason="Test invalid replacement")
    pr.insert(); pr.submit(); pr.reload()

    # Tạo Return PR thứ 2
    pr2 = _make_return_pr(item.name, sup, return_reason="Other return")
    pr2.insert(); pr2.submit(); pr2.reload()
    try:
        pr.link_replacement(pr2.name)
        frappe.db.rollback()
        return {"pass": False, "msg": "X did not throw"}
    except frappe.ValidationError as e:
        msg = str(e)
        frappe.db.rollback()
        if "SC-E-RETURN-REPLACE-INVALID" in msg:
            return {"pass": True, "msg": f"OK: {msg[:120]}"}
        return {"pass": False, "msg": f"Wrong error: {msg[:120]}"}


def test_send_notification_sets_timestamp():
    """Submit Return PR → notification_sent_at populated."""
    sup = _pick_supplier_with_email()
    item = _make_item("NOTI")
    pr = _make_return_pr(item.name, sup, return_reason="Test notification")
    try:
        pr.insert()
        pr.submit()
        pr.reload()
        ok = (pr.notification_sent_at is not None)
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK notification_sent_at={pr.notification_sent_at}"}
        return {"pass": False, "msg": f"X notification_sent_at not set"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_check_return_responses_escalates_over_7d():
    """Return PR posting >7d → scheduler escalate, escalated_at set."""
    from supplycore.m3_receiving.tasks import check_return_responses

    sup = _pick_supplier_with_email()
    item = _make_item("ESC")
    pr = _make_return_pr(item.name, sup, return_reason="Escalation test")
    try:
        pr.insert()
        pr.submit()
        pr.reload()
        # Backdate posting_date to 10 days ago
        frappe.db.set_value("SC Purchase Receipt", pr.name,
                             "posting_date", add_days(today(), -10))
        frappe.db.set_value("SC Purchase Receipt", pr.name, "escalated_at", None)
        frappe.db.commit()
        res = check_return_responses()
        pr.reload()
        ok = (pr.escalated_at is not None and res.get("escalated", 0) >= 1)
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK escalated={res.get('escalated')} at={pr.escalated_at}"}
        return {"pass": False, "msg": f"X escalated_at={pr.escalated_at} res={res}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def run():
    tests = [
        test_return_pr_requires_reason,
        test_return_pr_with_reason_submits,
        test_return_pr_auto_creates_debit_note,
        test_make_credit_note_sets_refunded,
        test_make_debit_note_idempotent,
        test_link_replacement_sets_replaced,
        test_link_replacement_rejects_return_pr,
        test_send_notification_sets_timestamp,
        test_check_return_responses_escalates_over_7d,
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
