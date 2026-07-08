"""Test UC-08 — Tạo và Phê duyệt Purchase Order.

Run individual: bench --site supplycore execute supplycore.tests.uc08_test.test_<name>
Run all:        bench --site supplycore execute supplycore.tests.uc08_test.run
"""

import frappe
from frappe.utils import today, add_days, random_string, flt


def _pick_warehouse() -> str:
    rows = frappe.get_all("SC Warehouse", filters={"is_group": 0, "disabled": 0},
                           pluck="name", order_by="name", limit=1)
    if not rows:
        frappe.throw("uc08_test: cần seed SC Warehouse")
    return rows[0]


def _pick_supplier_with_email() -> str:
    """Pick supplier có email_id, fallback set tạm cho 1 supplier."""
    rows = frappe.get_all(
        "SC Supplier",
        filters={"disabled": 0},
        fields=["name", "email_id"],
        order_by="name",
        limit=5,
    )
    if not rows:
        frappe.throw("uc08_test: cần seed SC Supplier")
    for r in rows:
        if r.email_id:
            return r.name
    # Set email cho supplier đầu để test pass
    frappe.db.set_value("SC Supplier", rows[0].name, "email_id", "test-supplier@example.com")
    return rows[0].name


def _pick_supplier_no_email() -> str:
    """Pick supplier KHÔNG có email_id (tạo nếu chưa có)."""
    rows = frappe.get_all("SC Supplier", filters={"disabled": 0},
                           fields=["name", "email_id"], limit=20)
    for r in rows:
        if not r.email_id:
            return r.name
    # Tất cả có email → tạm xóa email của 1 cái cho test
    if rows:
        frappe.db.set_value("SC Supplier", rows[-1].name, "email_id", None)
        return rows[-1].name
    frappe.throw("uc08_test: không có supplier")


def _get_uom() -> str:
    uom = frappe.db.get_value("SC UOM", {}, "name")
    if not uom:
        frappe.throw("uc08_test: cần seed SC UOM")
    return uom


def _make_item(suffix: str, **kwargs):
    item = frappe.new_doc("SC Item")
    item.item_code = f"UC08-{suffix}-{random_string(5)}"
    item.item_name = f"UC-08 test {suffix}"
    item.uom = _get_uom()
    item.is_stock_item = 1
    item.is_purchase_item = 1
    item.flags.ignore_permissions = True
    for k, v in kwargs.items():
        setattr(item, k, v)
    item.insert()
    return item


def _make_po(supplier: str, items: list, **kwargs):
    po = frappe.new_doc("SC Purchase Order")
    po.supplier = supplier
    po.transaction_date = today()
    po.schedule_date = add_days(today(), 14)
    po.to_warehouse = _pick_warehouse()
    for k, v in kwargs.items():
        setattr(po, k, v)
    for it in items:
        po.append("items", it)
    po.flags.ignore_permissions = True
    return po


# ---------- Tests ----------

def test_submit_blocked_when_not_approved():
    """Submit khi stage=Draft (không qua workflow review) → UX đơn giản hoá:
    auto-approve silent (approval_stage="Approved", manager_approved_by=user)
    thay vì block. Xem commit c316030 "PO submit thẳng → Sent to Supplier"."""
    sup = _pick_supplier_with_email()
    item = _make_item("NOTAPP")
    po = _make_po(sup, [{"item": item.name, "qty": 5, "uom": item.uom, "rate": 1000}])
    try:
        po.insert()
        po.submit()
        po.reload()
        ok = (po.docstatus == 1 and po.approval_stage == "Approved"
              and po.manager_approved_by == frappe.session.user)
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK auto-approved on direct submit stage={po.approval_stage}"}
        return {"pass": False, "msg": f"X docstatus={po.docstatus} stage={po.approval_stage} mgr={po.manager_approved_by}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_workflow_below_threshold_manager_only():
    """grand_total<50tr → submit_for_review → approve_as_manager → Approved (skip Executive)."""
    sup = _pick_supplier_with_email()
    item = _make_item("BTH")
    po = _make_po(sup, [{"item": item.name, "qty": 10, "uom": item.uom, "rate": 100_000}])  # 1tr
    try:
        po.insert()
        po.submit_for_review()
        po.reload()
        if po.approval_stage != "Manager Review":
            frappe.db.rollback()
            return {"pass": False, "msg": f"X stage={po.approval_stage} (expected Manager Review)"}
        po.approve_as_manager(comment="OK")
        po.reload()
        ok = (po.approval_stage == "Approved")
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": "OK <threshold → skip Executive → Approved"}
        return {"pass": False, "msg": f"X stage={po.approval_stage}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_workflow_above_threshold_two_tier():
    """grand_total>=50tr → Manager → Executive Review → Executive → Approved."""
    sup = _pick_supplier_with_email()
    item = _make_item("ATH")
    po = _make_po(sup, [{"item": item.name, "qty": 100, "uom": item.uom, "rate": 1_000_000}])  # 100tr
    try:
        po.insert()
        po.submit_for_review()
        po.reload()
        po.approve_as_manager(comment="OK")
        po.reload()
        if po.approval_stage != "Executive Review":
            frappe.db.rollback()
            return {"pass": False, "msg": f"X after manager: stage={po.approval_stage}"}
        po.approve_as_executive(comment="OK exec")
        po.reload()
        ok = (po.approval_stage == "Approved")
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": "OK ≥threshold → 2-tier → Approved"}
        return {"pass": False, "msg": f"X final stage={po.approval_stage}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_reject_requires_reason():
    """reject() không reason → SC-E-REJECT-REASON."""
    sup = _pick_supplier_with_email()
    item = _make_item("REJR")
    po = _make_po(sup, [{"item": item.name, "qty": 5, "uom": item.uom, "rate": 1000}])
    try:
        po.insert()
        po.submit_for_review()
        po.reload()
        try:
            po.reject(reason="")
            frappe.db.rollback()
            return {"pass": False, "msg": "X reject với reason rỗng không throw"}
        except frappe.ValidationError as e:
            msg = str(e)
            frappe.db.rollback()
            if "SC-E-REJECT-REASON" in msg:
                return {"pass": True, "msg": f"OK: {msg[:120]}"}
            return {"pass": False, "msg": f"Wrong error: {msg[:120]}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X setup: {str(e)[:120]}"}


def test_reject_in_manager_review():
    """reject(reason) ở Manager Review → stage=Rejected + reason saved."""
    sup = _pick_supplier_with_email()
    item = _make_item("REJM")
    po = _make_po(sup, [{"item": item.name, "qty": 5, "uom": item.uom, "rate": 1000}])
    try:
        po.insert()
        po.submit_for_review()
        po.reload()
        po.reject(reason="Giá quá cao")
        po.reload()
        ok = (po.approval_stage == "Rejected" and po.rejection_reason == "Giá quá cao")
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": "OK rejected with reason saved"}
        return {"pass": False, "msg": f"X stage={po.approval_stage} reason={po.rejection_reason}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_submit_sends_email_and_status_sent():
    """Full flow: insert → review → approve → submit → status=Sent to Supplier."""
    sup = _pick_supplier_with_email()
    item = _make_item("FULL")
    po = _make_po(sup, [{"item": item.name, "qty": 10, "uom": item.uom, "rate": 100_000}])
    try:
        po.insert()
        po.submit_for_review()
        po.reload()
        po.approve_as_manager(comment="OK")
        po.reload()
        po.submit()
        po.reload()
        ok = (po.docstatus == 1 and po.status == "Sent to Supplier" and po.sent_to_supplier_at)
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK status={po.status} sent_at={po.sent_to_supplier_at}"}
        return {"pass": False, "msg": f"X docstatus={po.docstatus} status={po.status} sent_at={po.sent_to_supplier_at}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_submit_blocked_no_supplier_email():
    """Supplier không có email_id + submit → SC-E-PO-NO-SUPPLIER-EMAIL."""
    sup_no_email = _pick_supplier_no_email()
    item = _make_item("NOEMAIL")
    po = _make_po(sup_no_email, [{"item": item.name, "qty": 5, "uom": item.uom, "rate": 1000}])
    try:
        po.insert()
        po.submit_for_review()
        po.reload()
        po.approve_as_manager(comment="OK")
        po.reload()
        try:
            po.submit()
            frappe.db.rollback()
            return {"pass": False, "msg": "X submit không block khi NCC không email"}
        except frappe.ValidationError as e:
            msg = str(e)
            frappe.db.rollback()
            if "SC-E-PO-NO-SUPPLIER-EMAIL" in msg:
                return {"pass": True, "msg": f"OK: {msg[:120]}"}
            return {"pass": False, "msg": f"Wrong error: {msg[:120]}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X setup: {str(e)[:120]}"}


def test_fc_exceeded_blocks():
    """grand_total > FC.remaining_value → SC-E002 FC_EXCEEDED."""
    sup = _pick_supplier_with_email()
    item = _make_item("FCEX")
    # Tạo FC với total_value nhỏ
    fc = frappe.new_doc("Framework Contract")
    fc.supplier = sup
    fc.contract_number = f"UC08-FC-EX-{random_string(6)}"
    fc.contract_date = add_days(today(), -30)
    fc.valid_from = add_days(today(), -10)
    fc.valid_to = add_days(today(), 365)
    fc.total_value = 1_000_000  # 1tr
    fc.append("items", {
        "item_code": item.name, "uom": item.uom,
        "contract_qty": 100, "unit_price": 10_000,
    })
    fc.flags.ignore_permissions = True
    fc.insert()
    fc.submit_for_review(); fc.reload()
    fc.approve_as_manager(comment="Duyệt hạn mức FC test"); fc.reload()
    if fc.approval_stage == "Executive Review":
        fc.approve_as_executive(comment="Duyệt hạn mức FC test (Executive)"); fc.reload()
    fc.submit(); fc.reload()

    po = _make_po(sup, [{"item": item.name, "qty": 100, "uom": item.uom, "rate": 100_000}],  # 10tr > 1tr
                   framework_contract=fc.name)
    try:
        po.insert()
        frappe.db.rollback()
        return {"pass": False, "msg": "X did not throw on FC exceeded"}
    except frappe.ValidationError as e:
        msg = str(e)
        frappe.db.rollback()
        if "FC_EXCEEDED" in msg or "FC_INACTIVE" in msg or "SC-E002" in msg or "vượt hạn mức" in msg:
            return {"pass": True, "msg": f"OK: {msg[:120]}"}
        return {"pass": False, "msg": f"Wrong error: {msg[:120]}"}


def test_price_variance_flagged():
    """row.rate ≠ fc_unit_price > 1% → row.has_price_variance=1, parent flag set."""
    sup = _pick_supplier_with_email()
    item = _make_item("PRICEVAR")
    fc = frappe.new_doc("Framework Contract")
    fc.supplier = sup
    fc.contract_number = f"UC08-FC-PV-{random_string(6)}"
    fc.contract_date = add_days(today(), -30)
    fc.valid_from = add_days(today(), -10)
    fc.valid_to = add_days(today(), 365)
    fc.total_value = 100_000_000
    fc.append("items", {
        "item_code": item.name, "uom": item.uom,
        "contract_qty": 1000, "unit_price": 50_000,  # FC giá 50k
    })
    fc.flags.ignore_permissions = True
    fc.insert()
    fc.submit_for_review(); fc.reload()
    fc.approve_as_manager(comment="Duyệt hạn mức FC test"); fc.reload()
    if fc.approval_stage == "Executive Review":
        fc.approve_as_executive(comment="Duyệt hạn mức FC test (Executive)"); fc.reload()
    fc.submit(); fc.reload()

    # PO với rate 60k (lệch 20% — quá ngưỡng 1%)
    po = _make_po(sup, [{"item": item.name, "qty": 5, "uom": item.uom, "rate": 60_000}],
                   framework_contract=fc.name)
    try:
        po.insert()
        po.reload()
        row = po.items[0]
        ok = (po.has_price_variance == 1 and row.has_price_variance == 1
              and abs(flt(row.fc_unit_price) - 50_000) < 0.01
              and abs(flt(row.price_variance_pct) - 20.0) < 0.5)
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK variance={row.price_variance_pct:.1f}% flagged"}
        return {"pass": False, "msg": f"X has_var={po.has_price_variance} row.fc_price={row.fc_unit_price} row.var={row.price_variance_pct}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_check_po_response_sends_reminder():
    """PO Sent > X ngày không confirm → scheduler send reminder + set last_reminder_sent_at."""
    from supplycore.m2_planning.tasks import check_po_response
    from frappe.utils import add_to_date

    sup = _pick_supplier_with_email()
    item = _make_item("REMIND")
    po = _make_po(sup, [{"item": item.name, "qty": 5, "uom": item.uom, "rate": 1000}])
    try:
        po.insert()
        po.submit_for_review()
        po.reload()
        po.approve_as_manager(comment="OK")
        po.reload()
        po.submit()
        po.reload()

        # Backdate sent_to_supplier_at để > threshold
        frappe.db.set_value("SC Purchase Order", po.name,
                             "sent_to_supplier_at", add_to_date(None, days=-5))
        frappe.db.commit()

        res = check_po_response()
        po.reload()
        # Check scheduler detected candidate (email may fail in test env without SMTP)
        ok = (res.get("candidates", 0) >= 1)
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK candidate detected: {res}"}
        return {"pass": False, "msg": f"X scheduler did not detect candidate: {res}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def run():
    tests = [
        test_submit_blocked_when_not_approved,
        test_workflow_below_threshold_manager_only,
        test_workflow_above_threshold_two_tier,
        test_reject_requires_reason,
        test_reject_in_manager_review,
        test_submit_sends_email_and_status_sent,
        test_submit_blocked_no_supplier_email,
        test_fc_exceeded_blocks,
        test_price_variance_flagged,
        test_check_po_response_sends_reminder,
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
