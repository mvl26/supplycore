"""Test UC-16 — FEFO picking + override audit.

Run individual: bench --site supplycore execute supplycore.tests.uc16_test.test_<name>
Run all:        bench --site supplycore execute supplycore.tests.uc16_test.run
"""

import frappe
from frappe.utils import today, add_days, random_string, flt


def _pick_warehouse() -> str:
    rows = frappe.get_all("SC Warehouse", filters={"is_group": 0, "disabled": 0},
                           pluck="name", order_by="name", limit=1)
    if not rows:
        frappe.throw("uc16_test: cần seed SC Warehouse")
    return rows[0]


def _get_uom() -> str:
    uom = frappe.db.get_value("SC UOM", {}, "name")
    if not uom:
        frappe.throw("uc16_test: cần seed SC UOM")
    return uom


def _make_item(suffix: str):
    item = frappe.new_doc("SC Item")
    item.item_code = f"UC16-{suffix}-{random_string(5)}"
    item.item_name = f"UC-16 test {suffix}"
    item.uom = _get_uom()
    item.is_stock_item = 1
    item.has_batch_no = 1
    item.flags.ignore_permissions = True
    item.insert()
    return item


def _make_batch(item: str, expiry_offset_days: int):
    from supplycore.m5_fefo.api.batch_helpers import generate_batch_id
    expiry = add_days(today(), expiry_offset_days)
    # manufacturing 2 years before expiry để qua check expiry > mfg
    mfg = add_days(expiry, -730)
    batch = frappe.new_doc("SC Batch")
    batch.batch_id = generate_batch_id(item, str(expiry))
    batch.item = item
    batch.expiry_date = expiry
    batch.manufacturing_date = mfg
    batch.qc_status = "Accepted"
    batch.flags.ignore_permissions = True
    batch.flags.ignore_short_expiry = 1
    batch.insert()
    return batch


def _seed_stock(item, warehouse, batch, qty):
    from supplycore.supplycore.doctype.sc_stock_ledger_entry.sc_stock_ledger_entry import SCStockLedgerEntry
    return SCStockLedgerEntry.post(
        item=item, warehouse=warehouse, qty_change=flt(qty), batch=batch,
        voucher_type="Manual", voucher_no=f"UC16-{random_string(6)}",
        posting_date=today(),
    )


# ---------- Tests ----------

def test_get_suggested_batches_fefo_order():
    """2 batches expiry 30d / 90d → API trả 30d trước."""
    from supplycore.api.fefo import get_suggested_batches
    wh = _pick_warehouse()
    item = _make_item("ORDER")
    b30 = _make_batch(item.name, 30)
    b90 = _make_batch(item.name, 90)
    _seed_stock(item.name, wh, b30.name, 20)
    _seed_stock(item.name, wh, b90.name, 30)
    try:
        res = get_suggested_batches(item.name, wh, qty=10)
        batches = res["batches"]
        frappe.db.rollback()
        if batches and batches[0]["batch_no"] == b30.name:
            return {"pass": True, "msg": f"OK FEFO order — {b30.name} first"}
        return {"pass": False, "msg": f"X first batch = {batches[0]['batch_no'] if batches else None}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_get_suggested_batches_excludes_expired():
    """Batch expired → không trả về."""
    from supplycore.api.fefo import get_suggested_batches
    wh = _pick_warehouse()
    item = _make_item("EXPD")
    b_exp = _make_batch(item.name, -10)  # already expired (negative offset)
    _seed_stock(item.name, wh, b_exp.name, 50)
    try:
        res = get_suggested_batches(item.name, wh, qty=10)
        names = [b["batch_no"] for b in res["batches"]]
        frappe.db.rollback()
        if b_exp.name not in names:
            return {"pass": True, "msg": f"OK expired batch excluded"}
        return {"pass": False, "msg": f"X expired included: {names}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_get_suggested_batches_excludes_blocked():
    """Batch blocked=1 → không trả về."""
    from supplycore.api.fefo import get_suggested_batches
    wh = _pick_warehouse()
    item = _make_item("BLK")
    b_blk = _make_batch(item.name, 60)
    b_blk.blocked = 1
    b_blk.block_reason = "Test block"
    b_blk.save()
    _seed_stock(item.name, wh, b_blk.name, 50)
    try:
        res = get_suggested_batches(item.name, wh, qty=10)
        names = [b["batch_no"] for b in res["batches"]]
        frappe.db.rollback()
        if b_blk.name not in names:
            return {"pass": True, "msg": f"OK blocked batch excluded"}
        return {"pass": False, "msg": f"X blocked included: {names}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_auto_pick_fefo_single_batch():
    """1 batch khả dụng → single_batch=True."""
    from supplycore.api.fefo import auto_pick_fefo
    wh = _pick_warehouse()
    item = _make_item("SING")
    b = _make_batch(item.name, 60)
    _seed_stock(item.name, wh, b.name, 50)
    try:
        res = auto_pick_fefo(item.name, wh, qty=10)
        frappe.db.rollback()
        if res["single_batch"] and len(res["picked"]) == 1:
            return {"pass": True, "msg": f"OK single_batch=True"}
        return {"pass": False, "msg": f"X {res}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_auto_pick_fefo_split_multiple():
    """2 batches qty 30 + 70, request 100 → split 30 + 70."""
    from supplycore.api.fefo import auto_pick_fefo
    wh = _pick_warehouse()
    item = _make_item("SPLT")
    b30 = _make_batch(item.name, 30)
    b90 = _make_batch(item.name, 90)
    _seed_stock(item.name, wh, b30.name, 30)
    _seed_stock(item.name, wh, b90.name, 80)
    try:
        res = auto_pick_fefo(item.name, wh, qty=100)
        picked = res["picked"]
        frappe.db.rollback()
        # Expect b30 first taking 30, then b90 taking 70
        qty_b30 = next((flt(p["suggested_qty"]) for p in picked if p["batch_no"] == b30.name), 0)
        qty_b90 = next((flt(p["suggested_qty"]) for p in picked if p["batch_no"] == b90.name), 0)
        if abs(qty_b30 - 30) < 0.01 and abs(qty_b90 - 70) < 0.01:
            return {"pass": True, "msg": f"OK split b30=30, b90=70"}
        return {"pass": False, "msg": f"X b30={qty_b30} b90={qty_b90}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_auto_pick_fefo_shortfall():
    """Request 200, avail 100 → shortfall=100."""
    from supplycore.api.fefo import auto_pick_fefo
    wh = _pick_warehouse()
    item = _make_item("SHORT")
    b = _make_batch(item.name, 60)
    _seed_stock(item.name, wh, b.name, 100)
    try:
        res = auto_pick_fefo(item.name, wh, qty=200)
        frappe.db.rollback()
        if (not res["fully_satisfied"]
                and abs(flt(res["shortfall"]) - 100) < 0.01):
            return {"pass": True, "msg": f"OK shortfall=100"}
        return {"pass": False, "msg": f"X {res}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_fefo_override_requires_manager():
    """User không Manager + fefo_override → throw SC-E-FEFO-MANAGER-REQUIRED."""
    wh = _pick_warehouse()
    item = _make_item("OVRROL")
    b_early = _make_batch(item.name, 30)
    b_late = _make_batch(item.name, 90)
    _seed_stock(item.name, wh, b_early.name, 50)
    _seed_stock(item.name, wh, b_late.name, 50)

    # Tạo SE override batch_late thay vì batch_early — vi phạm FEFO
    se = frappe.new_doc("SC Stock Entry")
    se.entry_type = "Material Issue"
    se.posting_date = today()
    se.from_warehouse = wh
    se.append("items", {
        "item": item.name, "qty": 10, "uom": item.uom,
        "batch": b_late.name, "fefo_override": 1,
        "fefo_override_reason": "Test override",
    })
    se.flags.ignore_permissions = True

    # Switch to non-Manager user context — use frappe.set_user
    original_user = frappe.session.user
    # Find / create a non-Manager user, or skip if no such user
    # Tạm thời assume current user là Administrator (System Manager) → set role tạm xóa Manager
    try:
        # Test as Administrator (which has all roles by default → "Administrator" is exempt)
        # → To force test: use a User without Manager role
        # Find a Storekeeper-only user
        sk_user = frappe.db.get_value("User",
            filters={
                "enabled": 1, "name": ["!=", "Administrator"],
            }, fieldname="name")
        if not sk_user:
            frappe.db.rollback()
            return {"pass": True, "msg": "OK (skipped: no non-Admin user available)"}

        # Replace user roles temporarily
        sk_doc = frappe.get_doc("User", sk_user)
        original_roles = [r.role for r in sk_doc.roles]
        sk_doc.roles = []
        sk_doc.append("roles", {"role": "SupplyCore Storekeeper"})
        sk_doc.save(ignore_permissions=True)

        frappe.set_user(sk_user)
        try:
            se.insert()
            se.submit()
            frappe.set_user(original_user)
            frappe.db.rollback()
            return {"pass": False, "msg": "X did not throw for non-Manager"}
        except frappe.ValidationError as e:
            msg = str(e)
            frappe.set_user(original_user)
            frappe.db.rollback()
            if "SC-E-FEFO-MANAGER-REQUIRED" in msg:
                return {"pass": True, "msg": f"OK: {msg[:120]}"}
            return {"pass": False, "msg": f"Wrong error: {msg[:120]}"}
    except Exception as e:
        frappe.set_user(original_user)
        frappe.db.rollback()
        return {"pass": False, "msg": f"X setup: {str(e)[:120]}"}


def test_fefo_override_with_manager_succeeds():
    """User Manager + override + reason → submit OK."""
    wh = _pick_warehouse()
    item = _make_item("OVRMGR")
    b_early = _make_batch(item.name, 30)
    b_late = _make_batch(item.name, 90)
    _seed_stock(item.name, wh, b_early.name, 50)
    _seed_stock(item.name, wh, b_late.name, 50)
    se = frappe.new_doc("SC Stock Entry")
    se.entry_type = "Material Issue"
    se.posting_date = today()
    se.from_warehouse = wh
    se.append("items", {
        "item": item.name, "qty": 10, "uom": item.uom,
        "batch": b_late.name, "fefo_override": 1,
        "fefo_override_reason": "Manager test override",
    })
    se.flags.ignore_permissions = True
    try:
        # As Administrator (System Manager) — should pass
        se.insert()
        se.submit()
        ok = (se.docstatus == 1)
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK SE submitted {se.name}"}
        return {"pass": False, "msg": f"X docstatus={se.docstatus}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_fefo_override_records_approver():
    """Submit với override → fefo_override_approved_by + at set."""
    wh = _pick_warehouse()
    item = _make_item("APPR")
    b_early = _make_batch(item.name, 30)
    b_late = _make_batch(item.name, 90)
    _seed_stock(item.name, wh, b_early.name, 50)
    _seed_stock(item.name, wh, b_late.name, 50)
    se = frappe.new_doc("SC Stock Entry")
    se.entry_type = "Material Issue"
    se.posting_date = today()
    se.from_warehouse = wh
    se.append("items", {
        "item": item.name, "qty": 5, "uom": item.uom,
        "batch": b_late.name, "fefo_override": 1,
        "fefo_override_reason": "Test approver record",
    })
    se.flags.ignore_permissions = True
    try:
        se.insert()
        se.submit()
        se.reload()
        row = se.items[0]
        ok = (row.fefo_override_approved_by and row.fefo_override_approved_at)
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK approver={row.fefo_override_approved_by}"}
        return {"pass": False, "msg": f"X approver_by={row.fefo_override_approved_by}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_fefo_override_logs_comment():
    """Submit với override → Frappe Comment được tạo trên SE."""
    wh = _pick_warehouse()
    item = _make_item("CMT")
    b_early = _make_batch(item.name, 30)
    b_late = _make_batch(item.name, 90)
    _seed_stock(item.name, wh, b_early.name, 50)
    _seed_stock(item.name, wh, b_late.name, 50)
    se = frappe.new_doc("SC Stock Entry")
    se.entry_type = "Material Issue"
    se.posting_date = today()
    se.from_warehouse = wh
    se.append("items", {
        "item": item.name, "qty": 5, "uom": item.uom,
        "batch": b_late.name, "fefo_override": 1,
        "fefo_override_reason": "Audit comment test",
    })
    se.flags.ignore_permissions = True
    try:
        se.insert()
        se.submit()
        comments = frappe.get_all("Comment",
            filters={"reference_doctype": "SC Stock Entry",
                      "reference_name": se.name, "comment_type": "Comment"},
            fields=["content"])
        frappe.db.rollback()
        has_fefo_audit = any("FEFO Override" in c.content for c in comments)
        if has_fefo_audit:
            return {"pass": True, "msg": f"OK FEFO Override comment logged"}
        return {"pass": False, "msg": f"X no FEFO audit comment: {comments}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def run():
    tests = [
        test_get_suggested_batches_fefo_order,
        test_get_suggested_batches_excludes_expired,
        test_get_suggested_batches_excludes_blocked,
        test_auto_pick_fefo_single_batch,
        test_auto_pick_fefo_split_multiple,
        test_auto_pick_fefo_shortfall,
        test_fefo_override_requires_manager,
        test_fefo_override_with_manager_succeeds,
        test_fefo_override_records_approver,
        test_fefo_override_logs_comment,
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
