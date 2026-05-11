"""Test UC-32 — Executive Dashboard.

Run individual: bench --site supplycore execute supplycore.tests.uc32_test.test_<name>
Run all:        bench --site supplycore execute supplycore.tests.uc32_test.run
"""

import frappe
from frappe.utils import today, add_days, random_string


def _pick_warehouse():
    return frappe.db.get_value("SC Warehouse",
        {"is_group": 0, "disabled": 0}, "name")


# ---------- Tests ----------

def test_get_executive_dashboard_returns_required_keys():
    """Trả KPIs + drill_down + last_updated_at + cached."""
    from supplycore.api.kpi import get_executive_dashboard
    try:
        res = get_executive_dashboard(period="this_month", force_refresh=1)
        required = {"period", "filters", "kpis", "top_items", "open_alerts",
                     "drill_down", "last_updated_at"}
        kpi_required = {"stock_value", "monthly_cost", "ap_outstanding",
                         "pending_pos", "expiring_soon", "low_stock_items",
                         "contract_expiring_30d", "po_overdue_count"}
        missing = required - set(res.keys())
        kpi_missing = kpi_required - set(res["kpis"].keys())
        if not missing and not kpi_missing:
            return {"pass": True, "msg": f"OK all keys present (kpis={len(res['kpis'])})"}
        return {"pass": False, "msg": f"X missing={missing} kpi_missing={kpi_missing}"}
    except Exception as e:
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_dashboard_cache_hit_returns_cached_true():
    """Gọi 2 lần → lần 2 cached=True."""
    from supplycore.api.kpi import get_executive_dashboard
    cache_key = f"uc32-test-cache-{random_string(6)}"
    try:
        first = get_executive_dashboard(period="this_month", force_refresh=1)
        second = get_executive_dashboard(period="this_month")
        if first.get("cached") is False and second.get("cached") is True:
            return {"pass": True, "msg": "OK 1st=False, 2nd=True"}
        return {"pass": False, "msg": f"X 1st={first.get('cached')} 2nd={second.get('cached')}"}
    except Exception as e:
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_dashboard_force_refresh_bypasses_cache():
    """force_refresh=1 → cached=False ngay cả khi đã cache."""
    from supplycore.api.kpi import get_executive_dashboard
    try:
        get_executive_dashboard(period="this_month")  # warm cache
        forced = get_executive_dashboard(period="this_month", force_refresh=1)
        if forced.get("cached") is False:
            return {"pass": True, "msg": "OK force_refresh bypassed cache"}
        return {"pass": False, "msg": f"X cached={forced.get('cached')}"}
    except Exception as e:
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_dashboard_filter_by_warehouse():
    """warehouse filter → KPI chỉ tính warehouse đó."""
    from supplycore.api.kpi import get_executive_dashboard
    wh = _pick_warehouse()
    if not wh:
        return {"pass": True, "msg": "OK (skipped: no warehouse)"}
    try:
        res = get_executive_dashboard(period="this_month", warehouse=wh,
                                        force_refresh=1)
        if res["filters"]["warehouse"] == wh:
            return {"pass": True, "msg": f"OK wh={wh}"}
        return {"pass": False, "msg": f"X filter={res['filters']}"}
    except Exception as e:
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_get_monthly_cost_trend_structure():
    """Trả rows với month + cost + invoice_count."""
    from supplycore.api.kpi import get_monthly_cost_trend
    try:
        rows = get_monthly_cost_trend(months=12)
        if isinstance(rows, list) and (not rows or {"month", "cost", "invoice_count"}.issubset(set(rows[0].keys()))):
            return {"pass": True, "msg": f"OK {len(rows)} months"}
        return {"pass": False, "msg": f"X structure: {rows[:1]}"}
    except Exception as e:
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_top_items_limit_10():
    """top_items ≤ 10."""
    from supplycore.api.kpi import get_executive_dashboard
    try:
        res = get_executive_dashboard(period="this_year", force_refresh=1)
        if len(res["top_items"]) <= 10:
            return {"pass": True, "msg": f"OK len={len(res['top_items'])}"}
        return {"pass": False, "msg": f"X len={len(res['top_items'])} > 10"}
    except Exception as e:
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_contract_expiring_30d_in_kpis():
    """KPI có key contract_expiring_30d và value là int."""
    from supplycore.api.kpi import get_executive_dashboard
    try:
        res = get_executive_dashboard(period="this_month", force_refresh=1)
        val = res["kpis"].get("contract_expiring_30d")
        if isinstance(val, int) and val >= 0:
            return {"pass": True, "msg": f"OK count={val}"}
        return {"pass": False, "msg": f"X val={val}"}
    except Exception as e:
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_get_dashboard_for_role_executive():
    """Role Executive → tất cả widgets."""
    from supplycore.api.kpi import get_dashboard_for_role
    try:
        res = get_dashboard_for_role(role="SupplyCore Executive")
        if (res["role"] == "SupplyCore Executive"
            and "stock_value" in res["kpis"]
            and "ap_outstanding" in res["kpis"]
            and len(res["widgets_enabled"]) >= 6):
            return {"pass": True, "msg": f"OK widgets={len(res['widgets_enabled'])}"}
        return {"pass": False, "msg": f"X kpis={list(res['kpis'].keys())}"}
    except Exception as e:
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_get_dashboard_for_role_accountant_filters():
    """Accountant → có ap_outstanding + monthly_cost, không có stock_value."""
    from supplycore.api.kpi import get_dashboard_for_role
    try:
        res = get_dashboard_for_role(role="SupplyCore Accountant")
        kpis = res["kpis"]
        if ("ap_outstanding" in kpis and "monthly_cost" in kpis
            and "stock_value" not in kpis):
            return {"pass": True, "msg": "OK accountant view"}
        return {"pass": False, "msg": f"X kpis={list(kpis.keys())}"}
    except Exception as e:
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_get_dashboard_for_role_storekeeper():
    """Storekeeper → stock-focused widgets, không có ap_outstanding."""
    from supplycore.api.kpi import get_dashboard_for_role
    try:
        res = get_dashboard_for_role(role="SupplyCore Storekeeper")
        kpis = res["kpis"]
        if "stock_value" in kpis and "ap_outstanding" not in kpis:
            return {"pass": True, "msg": "OK storekeeper view"}
        return {"pass": False, "msg": f"X kpis={list(kpis.keys())}"}
    except Exception as e:
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_invalid_period_throws():
    """period='bad' → throw SC-E-DSH-INVALID-PERIOD."""
    from supplycore.api.kpi import get_executive_dashboard
    try:
        get_executive_dashboard(period="invalid_period_xxx")
        return {"pass": False, "msg": "X accepted bad period"}
    except frappe.ValidationError as e:
        if "SC-E-DSH-INVALID-PERIOD" in str(e):
            return {"pass": True, "msg": "OK rejected"}
        return {"pass": False, "msg": f"X wrong: {str(e)[:120]}"}


def test_invalid_warehouse_throws():
    """warehouse='NONEXIST' → throw SC-E-DSH-INVALID-WAREHOUSE."""
    from supplycore.api.kpi import get_executive_dashboard
    try:
        get_executive_dashboard(period="this_month", warehouse="UC32-NONEXIST")
        return {"pass": False, "msg": "X accepted bad wh"}
    except frappe.ValidationError as e:
        if "SC-E-DSH-INVALID-WAREHOUSE" in str(e):
            return {"pass": True, "msg": "OK rejected"}
        return {"pass": False, "msg": f"X wrong: {str(e)[:120]}"}


def test_pdf_snapshot_structure():
    """get_dashboard_snapshot_pdf_data trả đủ keys cho Print Format."""
    from supplycore.api.kpi import get_dashboard_snapshot_pdf_data
    try:
        res = get_dashboard_snapshot_pdf_data(period="this_month")
        required = {"title", "generated_at", "generated_by", "period",
                     "kpis", "top_items", "monthly_trend",
                     "open_alerts", "signatures"}
        missing = required - set(res.keys())
        if not missing:
            return {"pass": True, "msg": "OK pdf structure"}
        return {"pass": False, "msg": f"X missing: {missing}"}
    except Exception as e:
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_drill_down_urls_provided():
    """drill_down có URL cho mỗi KPI key."""
    from supplycore.api.kpi import get_executive_dashboard
    try:
        res = get_executive_dashboard(period="this_month", force_refresh=1)
        drill = res["drill_down"]
        expected = {"stock_value", "monthly_cost", "ap_outstanding",
                     "pending_pos", "expiring_soon", "low_stock_items",
                     "contract_expiring_30d", "po_overdue_count"}
        missing = expected - set(drill.keys())
        if not missing and all(v.startswith("/app/") for v in drill.values()):
            return {"pass": True, "msg": f"OK {len(drill)} URLs"}
        return {"pass": False, "msg": f"X missing={missing}"}
    except Exception as e:
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def run():
    tests = [
        test_get_executive_dashboard_returns_required_keys,
        test_dashboard_cache_hit_returns_cached_true,
        test_dashboard_force_refresh_bypasses_cache,
        test_dashboard_filter_by_warehouse,
        test_get_monthly_cost_trend_structure,
        test_top_items_limit_10,
        test_contract_expiring_30d_in_kpis,
        test_get_dashboard_for_role_executive,
        test_get_dashboard_for_role_accountant_filters,
        test_get_dashboard_for_role_storekeeper,
        test_invalid_period_throws,
        test_invalid_warehouse_throws,
        test_pdf_snapshot_structure,
        test_drill_down_urls_provided,
    ]
    results = []
    for t in tests:
        try:
            r = t()
            r["test"] = t.__name__
        except Exception as e:
            r = {"test": t.__name__, "pass": False, "msg": f"EXCEPTION: {str(e)[:200]}"}
        results.append(r)
    passed = sum(1 for r in results if r.get("pass"))
    return {"passed": passed, "total": len(results), "results": results}
