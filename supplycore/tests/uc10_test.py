"""Test UC-10 — Quality Inspection (QC) hàng nhập.

Run individual: bench --site supplycore execute supplycore.tests.uc10_test.test_<name>
Run all:        bench --site supplycore execute supplycore.tests.uc10_test.run
"""

import frappe
from frappe.utils import today, add_days, random_string, flt


def _pick_warehouse() -> str:
    rows = frappe.get_all("SC Warehouse", filters={"is_group": 0, "disabled": 0},
                           pluck="name", order_by="name", limit=1)
    if not rows:
        frappe.throw("uc10_test: cần seed SC Warehouse")
    return rows[0]


def _pick_supplier_with_email() -> str:
    rows = frappe.get_all("SC Supplier", filters={"disabled": 0},
                           fields=["name", "email_id"], order_by="name", limit=5)
    if not rows:
        frappe.throw("uc10_test: cần seed SC Supplier")
    for r in rows:
        if r.email_id:
            return r.name
    frappe.db.set_value("SC Supplier", rows[0].name, "email_id", "test-supplier@example.com")
    return rows[0].name


def _get_uom() -> str:
    uom = frappe.db.get_value("SC UOM", {}, "name")
    if not uom:
        frappe.throw("uc10_test: cần seed SC UOM")
    return uom


def _make_item(suffix: str, has_batch: int = 1, **kwargs):
    item = frappe.new_doc("SC Item")
    item.item_code = f"UC10-{suffix}-{random_string(5)}"
    item.item_name = f"UC-10 test {suffix}"
    item.uom = _get_uom()
    item.is_stock_item = 1
    item.is_purchase_item = 1
    item.has_batch_no = has_batch
    sup = frappe.db.get_value("SC Supplier", {"disabled": 0}, "name")
    if sup:
        item.default_supplier = sup
    item.flags.ignore_permissions = True
    for k, v in kwargs.items():
        setattr(item, k, v)
    item.insert()
    return item


def _make_pr_with_qi(item_code: str, supplier: str, qty: float = 10) -> "frappe.model.document.Document":
    """Create + submit a PR (no PO), auto-QI fires. Returns (PR, QI)."""
    pr = frappe.new_doc("SC Purchase Receipt")
    pr.supplier = supplier
    pr.posting_date = today()
    pr.to_warehouse = _pick_warehouse()
    pr.qc_required = 1
    pr.no_po_reason = "UC-10 test - không qua PO"
    pr.append("items", {
        "item": item_code, "qty": qty, "uom": _get_uom(),
        "rate": 5_000, "warehouse": _pick_warehouse(),
        "expiry_date": add_days(today(), 365),
        "manufacturing_date": today(),
    })
    pr.flags.ignore_permissions = True
    pr.insert()
    pr.submit()
    pr.reload()
    qi_name = frappe.db.get_value("SC Quality Inspection",
                                    {"purchase_receipt": pr.name}, "name")
    if not qi_name:
        return pr, None
    return pr, frappe.get_doc("SC Quality Inspection", qi_name)


# ---------- Tests ----------

def test_default_template_exists_after_migrate():
    """Patch seed → template 'Default Hospital Supply QC' tồn tại + 5 criteria."""
    name = frappe.db.get_value("QC Checklist Template", {"title": "Default Hospital Supply QC"}, "name")
    if not name:
        return {"pass": False, "msg": "X template chưa được seed"}
    tpl = frappe.get_doc("QC Checklist Template", name)
    if len(tpl.criteria) != 5:
        return {"pass": False, "msg": f"X expected 5 criteria, got {len(tpl.criteria)}"}
    names = [c.criterion_name for c in tpl.criteria]
    expected = {"Bao bì nguyên vẹn", "Nhãn mác đúng", "Hạn dùng ≥6 tháng",
                "Số lô khớp chứng từ", "Quy cách đúng hợp đồng"}
    missing = expected - set(names)
    if missing:
        return {"pass": False, "msg": f"X thiếu criteria: {missing}"}
    return {"pass": True, "msg": f"OK template {name} có 5 criteria"}


def test_qi_auto_created_from_pr():
    """PR submit qc_required=1 → QI auto-tạo."""
    sup = _pick_supplier_with_email()
    item = _make_item("AUTOC")
    pr, qi = _make_pr_with_qi(item.name, sup)
    frappe.db.rollback()
    if qi is None:
        return {"pass": False, "msg": f"X không có QI cho PR {pr.name}"}
    return {"pass": True, "msg": f"OK QI {qi.name} auto-created from PR {pr.name}"}


def test_qi_all_accepted_sets_pr_pass():
    """QI all Accepted → submit → PR.qc_status=Pass + officially_received_at set."""
    sup = _pick_supplier_with_email()
    item = _make_item("ALLOK")
    pr, qi = _make_pr_with_qi(item.name, sup)
    if not qi:
        frappe.db.rollback()
        return {"pass": False, "msg": "X no QI"}
    for r in qi.readings:
        r.status = "Accepted"
    qi.save()
    qi.submit()
    qi.reload()
    pr.reload()
    ok = (qi.overall_status == "Accepted"
          and pr.qc_status == "Pass"
          and pr.officially_received_at is not None)
    frappe.db.rollback()
    if ok:
        return {"pass": True, "msg": f"OK QC Pass, officially_received_at set"}
    return {"pass": False, "msg": f"X qi={qi.overall_status} pr.qc={pr.qc_status} off_at={pr.officially_received_at}"}


def test_qi_any_rejected_sets_pr_fail():
    """QI 1 row Rejected → submit → PR.qc_status=Fail + batch.blocked + Return PR auto-tạo."""
    sup = _pick_supplier_with_email()
    item = _make_item("REJEC")
    pr, qi = _make_pr_with_qi(item.name, sup)
    if not qi:
        frappe.db.rollback()
        return {"pass": False, "msg": "X no QI"}
    # All except first Accepted
    if not qi.readings:
        # No template applied → seed minimal readings manually
        qi.append("readings", {"specification": "Bao bì", "status": "Rejected"})
        qi.append("readings", {"specification": "Nhãn", "status": "Accepted"})
    else:
        qi.readings[0].status = "Rejected"
        for r in qi.readings[1:]:
            r.status = "Accepted"
    qi.failure_reason = "Bao bì hỏng"
    qi.save()
    qi.submit()
    qi.reload()
    pr.reload()
    batch_blocked = 0
    if qi.batch:
        batch_blocked = frappe.db.get_value("SC Batch", qi.batch, "blocked")
    return_pr = frappe.db.exists("SC Purchase Receipt",
                                   {"is_return": 1, "remarks": ["like", f"%QI {qi.name}%"]})
    ok = (qi.overall_status == "Rejected"
          and pr.qc_status in ("Fail", "Partial Pass")
          and batch_blocked == 1
          and return_pr)
    frappe.db.rollback()
    if ok:
        return {"pass": True, "msg": f"OK Rejected + batch blocked + Return PR {return_pr}"}
    return {"pass": False, "msg": f"X qi={qi.overall_status} pr.qc={pr.qc_status} batch_blocked={batch_blocked} return={return_pr}"}


def test_qi_equipment_unavailable_onhold():
    """tick equipment + note → submit → overall=On Hold, PR.qc_status không đổi."""
    sup = _pick_supplier_with_email()
    item = _make_item("EQOH")
    pr, qi = _make_pr_with_qi(item.name, sup)
    if not qi:
        frappe.db.rollback()
        return {"pass": False, "msg": "X no QI"}
    qi.equipment_unavailable = 1
    qi.equipment_note = "Máy đo đường kính bị hỏng, chờ sửa"
    qi.save()
    qi.submit()
    qi.reload()
    pr.reload()
    ok = (qi.overall_status == "On Hold"
          and pr.qc_status == "Pending")
    frappe.db.rollback()
    if ok:
        return {"pass": True, "msg": f"OK On Hold, PR not updated"}
    return {"pass": False, "msg": f"X qi={qi.overall_status} pr.qc={pr.qc_status}"}


def test_qi_equipment_unavailable_requires_note():
    """tick equipment_unavailable không note → validate throw SC-E-QI-ONHOLD."""
    sup = _pick_supplier_with_email()
    item = _make_item("EQNO")
    pr, qi = _make_pr_with_qi(item.name, sup)
    if not qi:
        frappe.db.rollback()
        return {"pass": False, "msg": "X no QI"}
    qi.equipment_unavailable = 1
    qi.equipment_note = ""
    try:
        qi.save()
        frappe.db.rollback()
        return {"pass": False, "msg": "X did not throw on missing note"}
    except frappe.ValidationError as e:
        msg = str(e)
        frappe.db.rollback()
        if "SC-E-QI-ONHOLD" in msg:
            return {"pass": True, "msg": f"OK: {msg[:120]}"}
        return {"pass": False, "msg": f"Wrong error: {msg[:120]}"}


def test_qi_empty_readings_blocks_submit():
    """Submit không có reading nào set → SC-E-QI-READINGS."""
    sup = _pick_supplier_with_email()
    item = _make_item("EMPTYR")
    pr, qi = _make_pr_with_qi(item.name, sup)
    if not qi:
        frappe.db.rollback()
        return {"pass": False, "msg": "X no QI"}
    # Clear all readings status
    for r in qi.readings:
        r.status = None
    qi.save()
    try:
        qi.submit()
        frappe.db.rollback()
        return {"pass": False, "msg": "X submit không bị block"}
    except frappe.ValidationError as e:
        msg = str(e)
        frappe.db.rollback()
        if "SC-E-QI-READINGS" in msg:
            return {"pass": True, "msg": f"OK: {msg[:120]}"}
        return {"pass": False, "msg": f"Wrong error: {msg[:120]}"}


def test_qi_conditional_accept_batch_conditional():
    """overall=Accepted + action=Conditional Accept → batch.qc_status=Conditional."""
    sup = _pick_supplier_with_email()
    item = _make_item("COND")
    pr, qi = _make_pr_with_qi(item.name, sup)
    if not qi:
        frappe.db.rollback()
        return {"pass": False, "msg": "X no QI"}
    if not qi.batch:
        frappe.db.rollback()
        return {"pass": False, "msg": "X QI không có batch"}
    for r in qi.readings:
        r.status = "Accepted"
    qi.action_taken = "Conditional Accept"
    qi.save()
    qi.submit()
    batch_status = frappe.db.get_value("SC Batch", qi.batch, "qc_status")
    frappe.db.rollback()
    if batch_status == "Conditional":
        return {"pass": True, "msg": "OK batch.qc_status=Conditional"}
    return {"pass": False, "msg": f"X batch.qc_status={batch_status}"}


def test_qi_request_replacement_blocks_batch():
    """action=Request Replacement → batch.blocked=1."""
    sup = _pick_supplier_with_email()
    item = _make_item("REPLA")
    pr, qi = _make_pr_with_qi(item.name, sup)
    if not qi:
        frappe.db.rollback()
        return {"pass": False, "msg": "X no QI"}
    if not qi.batch:
        frappe.db.rollback()
        return {"pass": False, "msg": "X QI không có batch"}
    for r in qi.readings:
        r.status = "Accepted"  # all OK nhưng action vẫn Replace
    qi.action_taken = "Request Replacement"
    qi.failure_reason = "Yêu cầu đổi lô khác chất lượng tốt hơn"
    qi.save()
    qi.submit()
    blocked = frappe.db.get_value("SC Batch", qi.batch, "blocked")
    frappe.db.rollback()
    if blocked == 1:
        return {"pass": True, "msg": "OK batch.blocked=1 với reason Request Replacement"}
    return {"pass": False, "msg": f"X batch.blocked={blocked}"}


def test_fefo_skips_pending_qc_batch():
    """Batch.qc_status=Pending → get_suggested_batches không trả batch đó."""
    from supplycore.api.fefo import get_suggested_batches
    from supplycore.supplycore.doctype.sc_stock_ledger_entry.sc_stock_ledger_entry import SCStockLedgerEntry

    sup = _pick_supplier_with_email()
    item = _make_item("FEFO_PEND", has_batch=1)
    wh = _pick_warehouse()

    # Tạo Batch Pending qc_status manual
    batch = frappe.new_doc("SC Batch")
    batch.batch_id = f"UC10-PEND-{random_string(5)}"
    batch.item = item.name
    batch.expiry_date = add_days(today(), 365)
    batch.manufacturing_date = today()
    batch.qc_status = "Pending"
    batch.flags.ignore_permissions = True
    batch.insert()
    SCStockLedgerEntry.post(
        item=item.name, warehouse=wh, qty_change=50, batch=batch.name,
        voucher_type="Manual", voucher_no=f"UC10-FEFO-{random_string(6)}",
        posting_date=today(),
    )

    res = get_suggested_batches(item.name, wh, qty=10)
    batches = res.get("batches", []) if isinstance(res, dict) else []
    batch_names = [b.get("batch_no") for b in batches]
    frappe.db.rollback()
    if batch.name not in batch_names:
        return {"pass": True, "msg": f"OK FEFO skip Pending batch {batch.name}"}
    return {"pass": False, "msg": f"X FEFO included Pending batch: {batch_names}"}


def test_fefo_includes_accepted_batch():
    """Batch.qc_status=Accepted → batch xuất hiện trong FEFO."""
    from supplycore.api.fefo import get_suggested_batches
    from supplycore.supplycore.doctype.sc_stock_ledger_entry.sc_stock_ledger_entry import SCStockLedgerEntry

    sup = _pick_supplier_with_email()
    item = _make_item("FEFO_ACC", has_batch=1)
    wh = _pick_warehouse()

    batch = frappe.new_doc("SC Batch")
    batch.batch_id = f"UC10-ACC-{random_string(5)}"
    batch.item = item.name
    batch.expiry_date = add_days(today(), 365)
    batch.manufacturing_date = today()
    batch.qc_status = "Accepted"
    batch.flags.ignore_permissions = True
    batch.insert()
    SCStockLedgerEntry.post(
        item=item.name, warehouse=wh, qty_change=50, batch=batch.name,
        voucher_type="Manual", voucher_no=f"UC10-FEFOA-{random_string(6)}",
        posting_date=today(),
    )

    res = get_suggested_batches(item.name, wh, qty=10)
    batches = res.get("batches", []) if isinstance(res, dict) else []
    batch_names = [b.get("batch_no") for b in batches]
    frappe.db.rollback()
    if batch.name in batch_names:
        return {"pass": True, "msg": f"OK FEFO include Accepted batch {batch.name}"}
    return {"pass": False, "msg": f"X FEFO not found Accepted batch: {batch_names}"}


def test_fefo_includes_conditional_batch():
    """Batch.qc_status=Conditional → batch xuất hiện trong FEFO."""
    from supplycore.api.fefo import get_suggested_batches
    from supplycore.supplycore.doctype.sc_stock_ledger_entry.sc_stock_ledger_entry import SCStockLedgerEntry

    sup = _pick_supplier_with_email()
    item = _make_item("FEFO_CON", has_batch=1)
    wh = _pick_warehouse()

    batch = frappe.new_doc("SC Batch")
    batch.batch_id = f"UC10-CON-{random_string(5)}"
    batch.item = item.name
    batch.expiry_date = add_days(today(), 365)
    batch.manufacturing_date = today()
    batch.qc_status = "Conditional"
    batch.flags.ignore_permissions = True
    batch.insert()
    SCStockLedgerEntry.post(
        item=item.name, warehouse=wh, qty_change=50, batch=batch.name,
        voucher_type="Manual", voucher_no=f"UC10-FEFOC-{random_string(6)}",
        posting_date=today(),
    )

    res = get_suggested_batches(item.name, wh, qty=10)
    batches = res.get("batches", []) if isinstance(res, dict) else []
    batch_names = [b.get("batch_no") for b in batches]
    frappe.db.rollback()
    if batch.name in batch_names:
        return {"pass": True, "msg": f"OK FEFO include Conditional batch {batch.name}"}
    return {"pass": False, "msg": f"X FEFO not found Conditional batch: {batch_names}"}


def run():
    tests = [
        test_default_template_exists_after_migrate,
        test_qi_auto_created_from_pr,
        test_qi_all_accepted_sets_pr_pass,
        test_qi_any_rejected_sets_pr_fail,
        test_qi_equipment_unavailable_onhold,
        test_qi_equipment_unavailable_requires_note,
        test_qi_empty_readings_blocks_submit,
        test_qi_conditional_accept_batch_conditional,
        test_qi_request_replacement_blocks_batch,
        test_fefo_skips_pending_qc_batch,
        test_fefo_includes_accepted_batch,
        test_fefo_includes_conditional_batch,
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
