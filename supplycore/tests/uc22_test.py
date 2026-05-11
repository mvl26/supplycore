"""Test UC-22 — Patient Dispensing + BHYT calculation.

Run individual: bench --site supplycore execute supplycore.tests.uc22_test.test_<name>
Run all:        bench --site supplycore execute supplycore.tests.uc22_test.run
"""

import frappe
from frappe.utils import today, random_string, flt


def _pick_warehouse() -> str:
    rows = frappe.get_all("SC Warehouse", filters={"is_group": 0, "disabled": 0},
                           pluck="name", order_by="name", limit=1)
    if not rows:
        frappe.throw("uc22_test: cần seed SC Warehouse")
    return rows[0]


def _pick_department() -> str:
    rows = frappe.get_all("SC Department", filters={"disabled": 0},
                           pluck="name", order_by="name", limit=1)
    if not rows:
        d = frappe.new_doc("SC Department")
        d.department_name = f"UC22-Dept-{random_string(4)}"
        d.department_type = "Clinical"
        d.flags.ignore_permissions = True
        d.insert()
        return d.name
    return rows[0]


def _get_uom() -> str:
    return frappe.db.get_value("SC UOM", {}, "name")


def _make_patient(suffix: str, with_bhyt: bool = True):
    p = frappe.new_doc("SC Patient")
    p.patient_id = f"UC22-{suffix}-{random_string(5)}"
    p.patient_name = f"UC-22 BN {suffix}"
    p.dob = "1980-01-01"
    p.gender = "Nam"
    if with_bhyt:
        p.bhyt_card_no = f"HC4{random_string(13)}"
        p.bhyt_payment_rate = 80
    p.flags.ignore_permissions = True
    p.insert()
    return p


def _make_item(suffix: str, has_bhyt: bool = False, bhyt_rate: int = 80):
    item = frappe.new_doc("SC Item")
    item.item_code = f"UC22-{suffix}-{random_string(5)}"
    item.item_name = f"UC-22 test {suffix}"
    item.uom = _get_uom()
    item.is_stock_item = 1
    item.is_medical_supply = 1
    if has_bhyt:
        item.has_bhyt = 1
        item.bhyt_code = f"BHYT-{random_string(6)}"
        item.bhyt_group = "N01"
        item.bhyt_payment_rate = bhyt_rate
    item.flags.ignore_permissions = True
    item.insert()
    return item


def _make_pd(patient, items: list):
    pd = frappe.new_doc("SC Patient Dispensing")
    pd.patient = patient
    pd.dispensing_date = today()
    pd.ward = _pick_department()
    for it in items:
        pd.append("items", {
            "item": it["item"], "uom": _get_uom(),
            "qty": flt(it["qty"]),
            "unit_cost": flt(it.get("unit_cost", 1000)),
            "batch": it.get("batch"),
        })
    pd.flags.ignore_permissions = True
    return pd


# ---------- Tests ----------

def test_pd_calculate_bhyt_with_card():
    """BN có thẻ + item BHYT → bhyt_amount > 0."""
    p = _make_patient("BHYT")
    item = _make_item("BHYT", has_bhyt=True, bhyt_rate=80)
    pd = _make_pd(p.name, [{"item": item.name, "qty": 5, "unit_cost": 10_000}])
    try:
        pd.insert()
        row = pd.items[0]
        ok = (flt(row.bhyt_amount) > 0 and flt(row.patient_pays) < flt(row.total_cost))
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK bhyt={row.bhyt_amount} pays={row.patient_pays}"}
        return {"pass": False, "msg": f"X bhyt={row.bhyt_amount} pays={row.patient_pays}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_pd_no_bhyt_card_pays_100():
    """BN không thẻ → patient_pays = total_cost."""
    p = _make_patient("NOCARD", with_bhyt=False)
    item = _make_item("BHYTITM", has_bhyt=True)
    pd = _make_pd(p.name, [{"item": item.name, "qty": 5, "unit_cost": 10_000}])
    try:
        pd.insert()
        row = pd.items[0]
        ok = (flt(row.bhyt_amount) == 0
              and abs(flt(row.patient_pays) - flt(row.total_cost)) < 0.01)
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK no-card pays 100% = {row.patient_pays}"}
        return {"pass": False, "msg": f"X bhyt={row.bhyt_amount} pays={row.patient_pays} total={row.total_cost}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_pd_item_no_bhyt_config():
    """Item không BHYT → patient_pays = total_cost."""
    p = _make_patient("CARDNOBHYT")
    item = _make_item("NOITEMBHYT", has_bhyt=False)
    pd = _make_pd(p.name, [{"item": item.name, "qty": 3, "unit_cost": 5_000}])
    try:
        pd.insert()
        row = pd.items[0]
        ok = (flt(row.bhyt_amount) == 0
              and abs(flt(row.patient_pays) - 15_000) < 0.01)
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": "OK no item BHYT cfg, pays=15000"}
        return {"pass": False, "msg": f"X bhyt={row.bhyt_amount} pays={row.patient_pays}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_pd_compute_totals():
    """2 items → total_cost = sum."""
    p = _make_patient("TOT", with_bhyt=False)
    item1 = _make_item("T1")
    item2 = _make_item("T2")
    pd = _make_pd(p.name, [
        {"item": item1.name, "qty": 2, "unit_cost": 1000},
        {"item": item2.name, "qty": 3, "unit_cost": 2000},
    ])
    try:
        pd.insert()
        ok = (abs(flt(pd.total_cost) - (2 * 1000 + 3 * 2000)) < 0.01)
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK total_cost={pd.total_cost}"}
        return {"pass": False, "msg": f"X total_cost={pd.total_cost}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_lookup_patient_by_bhyt():
    """search by bhyt_card_no LIKE → trả patient."""
    from supplycore.m7_dispensing.doctype.sc_patient_dispensing.sc_patient_dispensing import lookup_patient_by_bhyt
    p = _make_patient("LOOKUP")
    try:
        res = lookup_patient_by_bhyt(p.bhyt_card_no[:5])
        names = [r["name"] for r in res["patients"]]
        frappe.db.rollback()
        if p.name in names:
            return {"pass": True, "msg": f"OK found {p.name}"}
        return {"pass": False, "msg": f"X not found: {names[:5]}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_get_patient_dispense_history():
    """2 PD → history trả 2 records + sum."""
    from supplycore.m7_dispensing.doctype.sc_patient_dispensing.sc_patient_dispensing import get_patient_dispense_history
    p = _make_patient("HIST", with_bhyt=False)
    item = _make_item("HIST")
    for _ in range(2):
        pd = _make_pd(p.name, [{"item": item.name, "qty": 5, "unit_cost": 1000}])
        pd.insert()
        pd.submit()
    try:
        res = get_patient_dispense_history(p.name)
        frappe.db.rollback()
        if res["count"] == 2 and abs(flt(res["total_cost"]) - 10_000) < 0.01:
            return {"pass": True, "msg": f"OK history count=2 total=10000"}
        return {"pass": False, "msg": f"X {res}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_pd_compute_total_no_bhyt():
    """Patient không BHYT card: total_cost trùng patient_pays."""
    p = _make_patient("NOBHYT2", with_bhyt=False)
    item = _make_item("TC")
    pd = _make_pd(p.name, [{"item": item.name, "qty": 10, "unit_cost": 500}])
    try:
        pd.insert()
        ok = (abs(flt(pd.total_cost) - 5000) < 0.01
              and abs(flt(pd.patient_pays) - 5000) < 0.01
              and flt(pd.bhyt_covered) == 0)
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": "OK no-bhyt total=patient_pays=5000"}
        return {"pass": False, "msg": f"X total={pd.total_cost} pays={pd.patient_pays}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_get_dispensed_items_for_dr_empty():
    """DR không SE → trả []."""
    from supplycore.m7_dispensing.doctype.sc_patient_dispensing.sc_patient_dispensing import get_dispensed_items_for_dr
    # Test with non-existent DR (should return [])
    try:
        res = get_dispensed_items_for_dr("SC-DR-NONEXISTENT-XXX")
        frappe.db.rollback()
        if res == []:
            return {"pass": True, "msg": "OK empty for non-existent DR"}
        return {"pass": False, "msg": f"X {res}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def run():
    tests = [
        test_pd_calculate_bhyt_with_card,
        test_pd_no_bhyt_card_pays_100,
        test_pd_item_no_bhyt_config,
        test_pd_compute_totals,
        test_pd_compute_total_no_bhyt,
        test_lookup_patient_by_bhyt,
        test_get_patient_dispense_history,
        test_get_dispensed_items_for_dr_empty,
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
