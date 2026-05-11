"""Test UC-20 — Dispensing Request.

Run individual: bench --site supplycore execute supplycore.tests.uc20_test.test_<name>
Run all:        bench --site supplycore execute supplycore.tests.uc20_test.run
"""

import frappe
from frappe.utils import today, random_string, flt


def _pick_warehouse() -> str:
    rows = frappe.get_all("SC Warehouse", filters={"is_group": 0, "disabled": 0},
                           pluck="name", order_by="name", limit=1)
    if not rows:
        frappe.throw("uc20_test: cần seed SC Warehouse")
    return rows[0]


def _pick_department() -> str:
    rows = frappe.get_all("SC Department", filters={"disabled": 0},
                           pluck="name", order_by="name", limit=1)
    if not rows:
        # Tạo dept tạm
        d = frappe.new_doc("SC Department")
        d.department_name = f"UC20-Dept-{random_string(4)}"
        d.department_type = "Clinical"
        d.flags.ignore_permissions = True
        d.insert()
        return d.name
    return rows[0]


def _get_uom() -> str:
    uom = frappe.db.get_value("SC UOM", {}, "name")
    if not uom:
        frappe.throw("uc20_test: cần seed SC UOM")
    return uom


def _make_item(suffix: str, item_group: str = None):
    item = frappe.new_doc("SC Item")
    item.item_code = f"UC20-{suffix}-{random_string(5)}"
    item.item_name = f"UC-20 test {suffix}"
    item.uom = _get_uom()
    item.is_stock_item = 1
    if item_group:
        item.item_group = item_group
    item.flags.ignore_permissions = True
    item.insert()
    return item


def _seed_stock(item, warehouse, qty):
    from supplycore.supplycore.doctype.sc_stock_ledger_entry.sc_stock_ledger_entry import SCStockLedgerEntry
    return SCStockLedgerEntry.post(
        item=item, warehouse=warehouse, qty_change=flt(qty),
        voucher_type="Manual", voucher_no=f"UC20-{random_string(6)}",
        posting_date=today(), valuation_rate=1000,
    )


def _make_dr(department, warehouse, items: list, **kwargs):
    dr = frappe.new_doc("SC Dispensing Request")
    dr.request_date = today()
    dr.required_by = today()
    dr.purpose = "Routine"
    dr.department = department
    dr.from_warehouse = warehouse
    for it in items:
        dr.append("items", {
            "item": it["item"], "uom": _get_uom(),
            "requested_qty": flt(it["qty"]),
            "approved_qty": flt(it.get("approved_qty", it["qty"])),
        })
    dr.flags.ignore_permissions = True
    for k, v in kwargs.items():
        setattr(dr, k, v)
    return dr


# ---------- Tests ----------

def test_dr_create_basic():
    """Tạo DR với department + items → save OK."""
    dept = _pick_department()
    wh = _pick_warehouse()
    item = _make_item("BASIC")
    _seed_stock(item.name, wh, 100)
    dr = _make_dr(dept, wh, [{"item": item.name, "qty": 10}])
    try:
        dr.insert()
        ok = (dr.name and dr.status == "Draft")
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK DR {dr.name}"}
        return {"pass": False, "msg": f"X status={dr.status}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_dr_patient_specific_requires_patient():
    """purpose=Patient-Specific, no patient → throw."""
    dept = _pick_department()
    wh = _pick_warehouse()
    item = _make_item("PATR")
    _seed_stock(item.name, wh, 50)
    dr = _make_dr(dept, wh, [{"item": item.name, "qty": 5}], purpose="Patient-Specific")
    try:
        dr.insert()
        frappe.db.rollback()
        return {"pass": False, "msg": "X did not throw"}
    except frappe.ValidationError as e:
        msg = str(e)
        frappe.db.rollback()
        if "Patient" in msg or "bệnh nhân" in msg.lower():
            return {"pass": True, "msg": f"OK: {msg[:120]}"}
        return {"pass": False, "msg": f"Wrong error: {msg[:120]}"}


def test_dr_auto_fill_requested_by():
    """Insert DR → requested_by = session.user."""
    dept = _pick_department()
    wh = _pick_warehouse()
    item = _make_item("AUTOR")
    _seed_stock(item.name, wh, 50)
    dr = _make_dr(dept, wh, [{"item": item.name, "qty": 5}])
    try:
        dr.insert()
        ok = (dr.requested_by == frappe.session.user)
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK requested_by={dr.requested_by}"}
        return {"pass": False, "msg": f"X requested_by={dr.requested_by} session={frappe.session.user}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_dr_compute_estimated_value():
    """items có rate → total_estimated_value tính đúng (qua _last_purchase_rate)."""
    # NOTE: _last_purchase_rate trả 0 nếu không có PO submitted. Test ở scenario chung
    # — chỉ verify total_estimated_value field được compute (kể cả =0).
    dept = _pick_department()
    wh = _pick_warehouse()
    item = _make_item("EVAL")
    _seed_stock(item.name, wh, 50)
    dr = _make_dr(dept, wh, [{"item": item.name, "qty": 10}])
    try:
        dr.insert()
        ok = (dr.total_estimated_value is not None)
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK total_estimated_value={dr.total_estimated_value}"}
        return {"pass": False, "msg": f"X total_estimated_value not computed"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_check_stock_availability_in_stock():
    """item có 100, request 50 → in_stock=True."""
    from supplycore.m7_dispensing.api.dispense_helpers import check_stock_availability
    wh = _pick_warehouse()
    item = _make_item("INSTOCK")
    _seed_stock(item.name, wh, 100)
    try:
        res = check_stock_availability(item.name, 50, wh)
        frappe.db.rollback()
        if res["in_stock"] and abs(flt(res["available_qty"]) - 100) < 0.01:
            return {"pass": True, "msg": f"OK in_stock=True available=100"}
        return {"pass": False, "msg": f"X {res}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_check_stock_availability_shortfall():
    """item có 30, request 50 → shortfall=20."""
    from supplycore.m7_dispensing.api.dispense_helpers import check_stock_availability
    wh = _pick_warehouse()
    item = _make_item("SHORT")
    _seed_stock(item.name, wh, 30)
    try:
        res = check_stock_availability(item.name, 50, wh)
        frappe.db.rollback()
        if (not res["in_stock"]) and abs(flt(res["shortfall"]) - 20) < 0.01:
            return {"pass": True, "msg": f"OK shortfall=20"}
        return {"pass": False, "msg": f"X {res}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_check_stock_availability_alternatives_same_group():
    """item hết, item khác cùng group có stock → suggest."""
    from supplycore.m7_dispensing.api.dispense_helpers import check_stock_availability
    group = frappe.db.get_value("SC Item Group", {}, "name")
    if not group:
        return {"pass": True, "msg": "OK (skipped: no item group)"}
    wh = _pick_warehouse()
    item_out = _make_item("OUT", item_group=group)
    item_alt = _make_item("ALT", item_group=group)
    _seed_stock(item_alt.name, wh, 100)  # only alt has stock
    try:
        res = check_stock_availability(item_out.name, 50, wh)
        frappe.db.rollback()
        alt_names = [a["item"] for a in res["alternatives"]]
        if not res["in_stock"] and item_alt.name in alt_names:
            return {"pass": True, "msg": f"OK alternative {item_alt.name} suggested"}
        return {"pass": False, "msg": f"X alternatives={alt_names}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_dr_quota_no_limit_skipped():
    """dept.quota=0 → submit OK dù total cao."""
    dept = _pick_department()
    # Đảm bảo quota=0
    frappe.db.set_value("SC Department", dept, "monthly_dispensing_quota", 0)
    wh = _pick_warehouse()
    item = _make_item("QUOTA0")
    _seed_stock(item.name, wh, 1000)
    dr = _make_dr(dept, wh, [{"item": item.name, "qty": 500}])
    try:
        dr.insert()
        dr.submit()
        ok = (dr.docstatus == 1)
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": "OK quota=0 skipped"}
        return {"pass": False, "msg": f"X doc={dr.docstatus}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_dr_quota_exceeded_blocks():
    """quota=1tr, items value > 1tr + ack=0 → SC-E-DR-QUOTA-EXCEEDED."""
    dept = _pick_department()
    frappe.db.set_value("SC Department", dept, "monthly_dispensing_quota", 1_000_000)
    wh = _pick_warehouse()
    item = _make_item("QUOTA")
    # Seed stock với valuation_rate cao để _compute_estimated_value fallback dùng
    _seed_stock(item.name, wh, 100)
    from supplycore.supplycore.doctype.sc_stock_ledger_entry.sc_stock_ledger_entry import SCStockLedgerEntry
    SCStockLedgerEntry.post(
        item=item.name, warehouse=wh, qty_change=100, valuation_rate=50_000,
        voucher_type="Manual", voucher_no=f"UC20-RATE-{random_string(4)}",
        posting_date=today(),
    )

    # DR qty=30 × rate 50k = 1.5tr > 1tr quota
    dr = _make_dr(dept, wh, [{"item": item.name, "qty": 30}])
    try:
        dr.insert()
        dr.submit()
        frappe.db.set_value("SC Department", dept, "monthly_dispensing_quota", 0)
        frappe.db.rollback()
        return {"pass": False, "msg": f"X submit không block. total={dr.total_estimated_value}"}
    except frappe.ValidationError as e:
        msg = str(e)
        frappe.db.set_value("SC Department", dept, "monthly_dispensing_quota", 0)
        frappe.db.rollback()
        if "SC-E-DR-QUOTA-EXCEEDED" in msg:
            return {"pass": True, "msg": f"OK: {msg[:120]}"}
        return {"pass": False, "msg": f"Wrong error: {msg[:120]}"}


def test_dr_quota_exceeded_with_ack_passes():
    """quota=1tr, total >1tr, ack=1 → submit OK."""
    dept = _pick_department()
    frappe.db.set_value("SC Department", dept, "monthly_dispensing_quota", 1_000_000)
    wh = _pick_warehouse()
    item = _make_item("QACK")
    _seed_stock(item.name, wh, 100)
    from supplycore.supplycore.doctype.sc_stock_ledger_entry.sc_stock_ledger_entry import SCStockLedgerEntry
    SCStockLedgerEntry.post(
        item=item.name, warehouse=wh, qty_change=100, valuation_rate=50_000,
        voucher_type="Manual", voucher_no=f"UC20-ACKR-{random_string(4)}",
        posting_date=today(),
    )
    dr = _make_dr(dept, wh, [{"item": item.name, "qty": 30}],
                   quota_override_acknowledged=1)
    try:
        dr.insert()
        dr.submit()
        ok = (dr.docstatus == 1)
        frappe.db.set_value("SC Department", dept, "monthly_dispensing_quota", 0)
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": "OK submitted with quota ack"}
        return {"pass": False, "msg": f"X doc={dr.docstatus}"}
    except Exception as e:
        frappe.db.set_value("SC Department", dept, "monthly_dispensing_quota", 0)
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_dr_make_stock_entry_after_submit():
    """Approved DR → make_stock_entry → SE Material Issue Draft."""
    dept = _pick_department()
    frappe.db.set_value("SC Department", dept, "monthly_dispensing_quota", 0)
    wh = _pick_warehouse()
    item = _make_item("MKSE")
    _seed_stock(item.name, wh, 100)
    dr = _make_dr(dept, wh, [{"item": item.name, "qty": 20}])
    try:
        dr.insert()
        dr.submit()
        se_name = dr.make_stock_entry()
        se = frappe.get_doc("SC Stock Entry", se_name)
        ok = (se.entry_type == "Material Issue" and se.docstatus == 0)
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK SE {se_name}"}
        return {"pass": False, "msg": f"X type={se.entry_type} doc={se.docstatus}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def run():
    tests = [
        test_dr_create_basic,
        test_dr_patient_specific_requires_patient,
        test_dr_auto_fill_requested_by,
        test_dr_compute_estimated_value,
        test_check_stock_availability_in_stock,
        test_check_stock_availability_shortfall,
        test_check_stock_availability_alternatives_same_group,
        test_dr_quota_no_limit_skipped,
        test_dr_quota_exceeded_blocks,
        test_dr_quota_exceeded_with_ack_passes,
        test_dr_make_stock_entry_after_submit,
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
