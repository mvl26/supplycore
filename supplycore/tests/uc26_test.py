"""Test UC-26 — Financial reports.

Run individual: bench --site supplycore execute supplycore.tests.uc26_test.test_<name>
Run all:        bench --site supplycore execute supplycore.tests.uc26_test.run
"""

import frappe
from frappe.utils import today, add_days, random_string, flt


def _pick_warehouse() -> str:
    rows = frappe.get_all("SC Warehouse", filters={"is_group": 0, "disabled": 0},
                           pluck="name", order_by="name", limit=1)
    return rows[0] if rows else None


def _get_uom() -> str:
    return frappe.db.get_value("SC UOM", {}, "name")


def _make_item(suffix: str, item_group: str = None):
    item = frappe.new_doc("SC Item")
    item.item_code = f"UC26-{suffix}-{random_string(5)}"
    item.item_name = f"UC-26 test {suffix}"
    item.uom = _get_uom()
    item.is_stock_item = 1
    if item_group:
        item.item_group = item_group
    sup = frappe.db.get_value("SC Supplier", {"disabled": 0}, "name")
    if sup:
        item.default_supplier = sup
    item.flags.ignore_permissions = True
    item.insert()
    return item


def _seed_stock(item, warehouse, qty, rate=1000):
    from supplycore.supplycore.doctype.sc_stock_ledger_entry.sc_stock_ledger_entry import SCStockLedgerEntry
    return SCStockLedgerEntry.post(
        item=item, warehouse=warehouse, qty_change=flt(qty),
        valuation_rate=flt(rate),
        voucher_type="Manual", voucher_no=f"UC26-{random_string(6)}",
        posting_date=today(),
    )


# ---------- Tests ----------

def test_inventory_value_basic():
    """SLE +100 × 1000 → inventory report trả qty=100, value=100000."""
    from supplycore.m8_accounting.api.financial_reports import inventory_value_report
    wh = _pick_warehouse()
    item = _make_item("INV")
    _seed_stock(item.name, wh, 100, 1000)
    try:
        res = inventory_value_report(warehouse=wh)
        matching = [r for r in res["rows"] if r["item"] == item.name]
        frappe.db.rollback()
        if matching and abs(flt(matching[0]["qty"]) - 100) < 0.01 \
           and abs(flt(matching[0]["value"]) - 100_000) < 0.01:
            return {"pass": True, "msg": f"OK qty=100 value=100000"}
        return {"pass": False, "msg": f"X {matching}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_inventory_value_filter_warehouse():
    """Filter warehouse → chỉ trả rows của warehouse đó."""
    from supplycore.m8_accounting.api.financial_reports import inventory_value_report
    whs = frappe.get_all("SC Warehouse", filters={"is_group": 0, "disabled": 0},
                          pluck="name", order_by="name", limit=2)
    if len(whs) < 2:
        return {"pass": True, "msg": "OK (skipped: <2 warehouses)"}
    item = _make_item("FILTW")
    _seed_stock(item.name, whs[0], 50)
    _seed_stock(item.name, whs[1], 30)
    try:
        res = inventory_value_report(warehouse=whs[0])
        wh_set = {r["warehouse"] for r in res["rows"]}
        frappe.db.rollback()
        if wh_set == {whs[0]}:
            return {"pass": True, "msg": "OK filter warehouse"}
        return {"pass": False, "msg": f"X wh_set={wh_set}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_ap_aging_buckets():
    """PI overdue khác → bucket đúng."""
    from supplycore.m8_accounting.api.financial_reports import ap_aging_report

    sup = frappe.db.get_value("SC Supplier", {"disabled": 0}, "name")
    if not sup:
        return {"pass": True, "msg": "OK (skipped: no supplier)"}

    # Create PI directly với due_date trong quá khứ
    inv_no = f"UC26-AGE-{random_string(5)}"
    pi = frappe.new_doc("SC Purchase Invoice")
    pi.supplier = sup
    pi.supplier_invoice_no = inv_no
    pi.invoice_date = add_days(today(), -100)
    pi.due_date = add_days(today(), -75)  # 75 days overdue → 61_90 bucket
    pi.vat_rate = 0
    item = _make_item("AGE")
    pi.append("items", {"item": item.name, "qty": 1, "uom": _get_uom(),
                          "rate": 100_000})
    pi.flags.ignore_permissions = True
    pi.insert()
    pi.submit()

    try:
        res = ap_aging_report(supplier=sup)
        matching = [r for r in res["rows"] if r["name"] == pi.name]
        frappe.db.rollback()
        if matching and matching[0]["bucket"] == "61_90":
            return {"pass": True, "msg": f"OK bucket=61_90"}
        return {"pass": False, "msg": f"X bucket={matching[0]['bucket'] if matching else None}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_period_cost_summary():
    """2 PI trong kỳ → total cost = sum."""
    from supplycore.m8_accounting.api.financial_reports import period_cost_report

    sup = frappe.db.get_value("SC Supplier", {"disabled": 0}, "name")
    if not sup:
        return {"pass": True, "msg": "OK (skipped: no supplier)"}
    item = _make_item("PERC")
    pi1 = frappe.new_doc("SC Purchase Invoice")
    pi1.supplier = sup
    pi1.supplier_invoice_no = f"UC26-PC1-{random_string(5)}"
    pi1.invoice_date = today()
    pi1.due_date = add_days(today(), 30)
    pi1.vat_rate = 0
    pi1.append("items", {"item": item.name, "qty": 5, "uom": _get_uom(),
                           "rate": 10_000})
    pi1.flags.ignore_permissions = True
    pi1.insert(); pi1.submit()

    pi2 = frappe.new_doc("SC Purchase Invoice")
    pi2.supplier = sup
    pi2.supplier_invoice_no = f"UC26-PC2-{random_string(5)}"
    pi2.invoice_date = today()
    pi2.due_date = add_days(today(), 30)
    pi2.vat_rate = 0
    pi2.append("items", {"item": item.name, "qty": 3, "uom": _get_uom(),
                           "rate": 20_000})
    pi2.flags.ignore_permissions = True
    pi2.insert(); pi2.submit()

    try:
        res = period_cost_report(from_date=today(), to_date=today())
        total = flt(res["total_cost"])
        frappe.db.rollback()
        if total >= (50_000 + 60_000):  # at least 110k from our 2 PIs
            return {"pass": True, "msg": f"OK total≥110k actual={total}"}
        return {"pass": False, "msg": f"X total={total}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_bhyt_settlement_aggregates_by_group():
    """2 PD với BHYT khác group → settlement có 2 rows."""
    from supplycore.m8_accounting.api.financial_reports import bhyt_settlement_report

    # Tạo 2 patients có BHYT
    patients = []
    for i, group in enumerate(["N01", "N02"]):
        p = frappe.new_doc("SC Patient")
        p.patient_id = f"UC26-PAT-{i}-{random_string(4)}"
        p.patient_name = f"UC-26 BN {i}"
        p.bhyt_card_no = f"UC26{random_string(13)}"
        p.bhyt_payment_rate = 80
        p.flags.ignore_permissions = True
        p.insert()
        patients.append((p, group))

    rows_created = 0
    for p, group in patients:
        item = _make_item(f"BHYT{group}")
        pd = frappe.new_doc("SC Patient Dispensing")
        pd.patient = p.name
        pd.dispensing_date = today()
        # Force bhyt_group via SC BHYT Code Config
        cfg = frappe.new_doc("SC BHYT Code Config")
        cfg.bhyt_code = f"UC26-{group}-{random_string(4)}"
        cfg.bhyt_name = f"UC26 {group}"
        cfg.bhyt_group = group
        cfg.payment_rate = 80
        cfg.item = item.name
        cfg.effective_from = today()
        cfg.is_active = 1
        cfg.flags.ignore_permissions = True
        cfg.insert()

        pd.append("items", {"item": item.name, "uom": _get_uom(),
                              "qty": 5, "unit_cost": 10_000})
        pd.flags.ignore_permissions = True
        pd.insert()
        pd.submit()
        rows_created += 1

    try:
        res = bhyt_settlement_report(from_date=today(), to_date=today())
        groups = {r["bhyt_group"] for r in res["rows"]}
        frappe.db.rollback()
        if "N01" in groups and "N02" in groups:
            return {"pass": True, "msg": f"OK groups: {groups}"}
        return {"pass": False, "msg": f"X groups={groups}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_get_voucher_details_pi():
    """PI submitted → drill returns header + items."""
    from supplycore.m8_accounting.api.financial_reports import get_voucher_details
    sup = frappe.db.get_value("SC Supplier", {"disabled": 0}, "name")
    if not sup:
        return {"pass": True, "msg": "OK (skipped: no supplier)"}
    item = _make_item("DRILL")
    pi = frappe.new_doc("SC Purchase Invoice")
    pi.supplier = sup
    pi.supplier_invoice_no = f"UC26-DR-{random_string(5)}"
    pi.invoice_date = today()
    pi.due_date = add_days(today(), 30)
    pi.append("items", {"item": item.name, "qty": 5, "uom": _get_uom(),
                          "rate": 1000})
    pi.flags.ignore_permissions = True
    pi.insert()
    try:
        res = get_voucher_details("SC Purchase Invoice", pi.name)
        frappe.db.rollback()
        if res["exists"] and "header" in res and "items" in res \
           and any(it["table"] == "items" for it in res["items"]):
            return {"pass": True, "msg": "OK drill-down complete"}
        return {"pass": False, "msg": f"X {res.keys()}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_check_period_finalized_draft_present():
    """Draft PI → finalized=False."""
    from supplycore.m8_accounting.api.financial_reports import check_period_finalized
    sup = frappe.db.get_value("SC Supplier", {"disabled": 0}, "name")
    item = _make_item("DRFT")
    pi = frappe.new_doc("SC Purchase Invoice")
    pi.supplier = sup
    pi.supplier_invoice_no = f"UC26-DRA-{random_string(5)}"
    pi.invoice_date = today()
    pi.due_date = add_days(today(), 30)
    pi.append("items", {"item": item.name, "qty": 1, "uom": _get_uom(),
                          "rate": 1000})
    pi.flags.ignore_permissions = True
    pi.insert()  # NOT submitted

    try:
        res = check_period_finalized(today(), today())
        frappe.db.rollback()
        if not res["finalized"] and res["pending"]["total"] >= 1:
            return {"pass": True, "msg": f"OK finalized=False pending={res['pending']}"}
        return {"pass": False, "msg": f"X {res}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_inventory_value_zero_for_empty():
    """No SLE → empty rows."""
    from supplycore.m8_accounting.api.financial_reports import inventory_value_report
    item = _make_item("ZERO")
    try:
        res = inventory_value_report(warehouse=_pick_warehouse())
        # Item just created with no SLE — should not appear
        matching = [r for r in res["rows"] if r["item"] == item.name]
        frappe.db.rollback()
        if not matching:
            return {"pass": True, "msg": "OK no-stock item excluded"}
        return {"pass": False, "msg": f"X found {matching}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_ap_aging_current_bucket():
    """PI due_date in future → bucket=current."""
    from supplycore.m8_accounting.api.financial_reports import ap_aging_report
    sup = frappe.db.get_value("SC Supplier", {"disabled": 0}, "name")
    item = _make_item("AGEC")
    pi = frappe.new_doc("SC Purchase Invoice")
    pi.supplier = sup
    pi.supplier_invoice_no = f"UC26-CUR-{random_string(5)}"
    pi.invoice_date = today()
    pi.due_date = add_days(today(), 15)  # future
    pi.append("items", {"item": item.name, "qty": 1, "uom": _get_uom(), "rate": 1000})
    pi.flags.ignore_permissions = True
    pi.insert()
    pi.submit()
    try:
        res = ap_aging_report(supplier=sup)
        matching = [r for r in res["rows"] if r["name"] == pi.name]
        frappe.db.rollback()
        if matching and matching[0]["bucket"] == "current":
            return {"pass": True, "msg": "OK bucket=current"}
        return {"pass": False, "msg": f"X bucket={matching[0]['bucket'] if matching else None}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def run():
    tests = [
        test_inventory_value_basic,
        test_inventory_value_filter_warehouse,
        test_inventory_value_zero_for_empty,
        test_ap_aging_buckets,
        test_ap_aging_current_bucket,
        test_period_cost_summary,
        test_bhyt_settlement_aggregates_by_group,
        test_get_voucher_details_pi,
        test_check_period_finalized_draft_present,
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
