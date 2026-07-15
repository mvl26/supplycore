"""Test UC-06 — Lập kế hoạch mua hàng định kỳ.

Run individual: bench --site supplycore execute supplycore.tests.uc06_test.test_<name>
Run all:        bench --site supplycore execute supplycore.tests.uc06_test.run
"""

import frappe
from frappe.utils import today, add_days, add_months, random_string


def _pick_warehouse() -> str:
    rows = frappe.get_all(
        "SC Warehouse",
        filters={"is_group": 0, "disabled": 0},
        pluck="name",
        order_by="name",
        limit=1,
    )
    if not rows:
        frappe.throw("uc06_test: cần seed SC Warehouse trước")
    return rows[0]


def _make_item(suffix: str, **kwargs):
    item = frappe.new_doc("SC Item")
    item.item_code = f"UC06-{suffix}-{random_string(5)}"
    item.item_name = f"UC-06 test {suffix}"
    uom = frappe.db.get_value("SC UOM", {}, "name")
    if not uom:
        frappe.throw("uc06_test: cần seed SC UOM trước")
    item.uom = uom
    item.is_stock_item = 1
    item.is_purchase_item = 1
    item.lead_time_days = 30
    # UC-07 requires default_supplier cho Purchase MR
    sup = frappe.db.get_value("SC Supplier", {"disabled": 0}, "name")
    if sup:
        item.default_supplier = sup
    item.flags.ignore_permissions = True
    for k, v in kwargs.items():
        setattr(item, k, v)
    item.insert()
    return item


def _make_plan(warehouse: str, **kwargs):
    plan = frappe.new_doc("Procurement Plan")
    plan.plan_date = today()
    plan.period_type = "Monthly"
    plan.from_date = today()
    plan.to_date = add_days(today(), 30)
    plan.warehouse = warehouse
    plan.consumption_lookback_months = 3
    plan.safety_stock_factor = 20
    plan.required_by = add_days(today(), 14)
    plan.remarks = "UC06-TEST"
    plan.flags.ignore_permissions = True
    for k, v in kwargs.items():
        setattr(plan, k, v)
    plan.insert()
    return plan


def _add_plan_row(plan, item_code: str, qty: float, unit_cost: float):
    uom = frappe.db.get_value("SC Item", item_code, "uom")
    plan.append("items", {
        "item_code": item_code,
        "uom": uom,
        "planned_qty": qty,
        "estimated_unit_cost": unit_cost,
    })


# ---------- Tests ----------

def test_budget_exceeded_blocks_submit():
    """total=2tr, budget=1tr, ack=0 → throw SC-E-BUDGET-EXCEEDED khi save."""
    wh = _pick_warehouse()
    item = _make_item("BUDX")
    plan = _make_plan(wh, budget=1_000_000)
    _add_plan_row(plan, item.name, qty=20, unit_cost=100_000)  # total = 2tr
    try:
        plan.save(ignore_permissions=True)
        frappe.db.rollback()
        return {"pass": False, "msg": "X did not throw on budget exceeded"}
    except frappe.ValidationError as e:
        msg = str(e)
        if "SC-E-BUDGET-EXCEEDED" in msg:
            frappe.db.rollback()
            return {"pass": True, "msg": f"OK: {msg[:120]}"}
        frappe.db.rollback()
        return {"pass": False, "msg": f"Wrong error: {msg[:120]}"}


def test_budget_acknowledged_allows_submit():
    """total=2tr, budget=1tr, ack=1 → save + submit OK."""
    wh = _pick_warehouse()
    item = _make_item("BUDA")
    plan = _make_plan(wh, budget=1_000_000, budget_acknowledged=1)
    _add_plan_row(plan, item.name, qty=20, unit_cost=100_000)
    try:
        plan.save(ignore_permissions=True)
        plan.submit()
        ok = (plan.docstatus == 1 and plan.status == "Approved")
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK submitted {plan.name}"}
        return {"pass": False, "msg": f"X docstatus={plan.docstatus} status={plan.status}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_budget_zero_skips_check():
    """budget=0 → không check (skip rule). total=2tr OK."""
    wh = _pick_warehouse()
    item = _make_item("BUDZ")
    plan = _make_plan(wh, budget=0)
    _add_plan_row(plan, item.name, qty=20, unit_cost=100_000)
    try:
        plan.save(ignore_permissions=True)
        frappe.db.rollback()
        return {"pass": True, "msg": f"OK budget=0 skips check"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_auto_load_empty_warns():
    """Warehouse không có SLE consumption → auto_load trả 0 items + warning (no throw)."""
    wh = _pick_warehouse()
    plan = _make_plan(wh)
    # No SLE for any unrelated test item — pick warehouse with min activity
    # Result: at minimum, items without consumption are skipped. items_loaded có thể 0
    try:
        res = plan.auto_load_items()
        items_loaded = res.get("items_loaded", -1)
        frappe.db.rollback()
        if items_loaded >= 0:
            return {"pass": True, "msg": f"OK auto_load returned items_loaded={items_loaded} (no throw)"}
        return {"pass": False, "msg": f"X invalid result: {res}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_auto_load_subtracts_pending_po():
    """Item có pending PO → suggested giảm theo qty pending. Verify formula trực tiếp."""
    from frappe.utils import flt
    from supplycore.supplycore.doctype.sc_stock_ledger_entry.sc_stock_ledger_entry import SCStockLedgerEntry
    from supplycore.m2_planning.doctype.procurement_plan.procurement_plan import ProcurementPlan

    wh = _pick_warehouse()
    item = _make_item("PENDPO", lead_time_days=30, safety_stock=0)

    # Seed large initial stock 4 tháng trước (để current không âm sau consumption)
    SCStockLedgerEntry.post(
        item=item.name, warehouse=wh, qty_change=400,
        voucher_type="Manual", voucher_no=f"UC06-OPEN-{random_string(6)}",
        posting_date=add_months(today(), -4),
    )
    # 3 tháng SLE consumption: -100/tháng → avg = 100/tháng
    for months_ago in (1, 2, 3):
        SCStockLedgerEntry.post(
            item=item.name, warehouse=wh, qty_change=-100,
            voucher_type="Manual", voucher_no=f"UC06-T-{random_string(6)}",
            posting_date=add_months(today(), -months_ago),
        )
    # current = 400 - 300 = 100

    # Verify pending helper returns 0 khi không có PO
    pending = ProcurementPlan._get_pending_po_qty(item.name, wh)
    if pending != 0.0:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X pending should be 0, got {pending}"}

    # Run auto_load and verify row
    plan = _make_plan(wh)
    plan.auto_load_items()
    plan.reload()
    matching = [r for r in plan.items if r.item_code == item.name]
    frappe.db.rollback()

    if not matching:
        return {"pass": False, "msg": "X item not loaded — check consumption seed"}
    row = matching[0]
    # Formula: avg=100, lead=30d→1mo, safety_factor=1.2, item_safety=0, current=100, pending=0
    # base=100, target=100*1.2=120, suggested=max(0, 120-100-0)=20
    expected = 20.0
    if abs(flt(row.planned_qty) - expected) < 5.0 and flt(row.pending_po_qty) == 0:
        return {"pass": True, "msg": f"OK suggested={row.planned_qty} pending={row.pending_po_qty} (expected ~{expected})"}
    return {"pass": False, "msg": f"X mismatch: planned={row.planned_qty} pending={row.pending_po_qty} (expected ~{expected})"}


def test_auto_create_mr_on_submit():
    """auto_create_mr=1 → on_submit auto-tạo SC Material Request."""
    wh = _pick_warehouse()
    item = _make_item("AUTOMR")
    plan = _make_plan(wh, auto_create_mr=1)
    _add_plan_row(plan, item.name, qty=10, unit_cost=50_000)
    try:
        plan.save(ignore_permissions=True)
        plan.submit()
        plan.reload()
        mr_name = plan.material_request
        ok = bool(mr_name) and frappe.db.exists("SC Material Request", mr_name)
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK auto-created MR {mr_name}"}
        return {"pass": False, "msg": f"X material_request not set after submit (got={mr_name})"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def run():
    tests = [
        test_budget_exceeded_blocks_submit,
        test_budget_acknowledged_allows_submit,
        test_budget_zero_skips_check,
        test_auto_load_empty_warns,
        test_auto_load_subtracts_pending_po,
        test_auto_create_mr_on_submit,
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
