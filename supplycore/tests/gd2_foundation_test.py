"""Test GĐ2 Task 1 — nền tảng M7 Sales: module scaffold, GL account 511, Settings fields.

Run individual: bench --site supplycore-miyano.local execute supplycore.tests.gd2_foundation_test.test_<name>
Run all:        bench --site supplycore-miyano.local execute supplycore.tests.gd2_foundation_test.run
"""

import frappe


def test_revenue_account_exists():
    """Patch v0_8.seed_sales_gl_accounts phải tạo SC GL Account 511 (Doanh thu bán hàng)."""
    try:
        ok = bool(frappe.db.exists("SC GL Account", "511"))
        if ok:
            return {"pass": True, "msg": "OK SC GL Account 511 tồn tại"}
        return {"pass": False, "msg": "X SC GL Account 511 chưa tồn tại"}
    except Exception as e:
        return {"pass": False, "msg": f"X threw: {str(e)[:200]}"}


def test_settings_has_fiscal_lock():
    """SupplyCore Settings phải có field fiscal_lock_date (Section 'Bán hàng & Sổ cái')."""
    try:
        meta = frappe.get_meta("SupplyCore Settings")
        ok = meta.has_field("fiscal_lock_date")
        if ok:
            return {"pass": True, "msg": "OK field fiscal_lock_date tồn tại"}
        return {"pass": False, "msg": "X field fiscal_lock_date chưa tồn tại"}
    except Exception as e:
        return {"pass": False, "msg": f"X threw: {str(e)[:200]}"}


def test_m7_sales_module_registered():
    """modules.txt phải chứa dòng 'M7 Sales'."""
    try:
        path = frappe.get_app_path("supplycore", "modules.txt")
        with open(path, encoding="utf-8") as f:
            content = f.read()
        lines = [ln.strip() for ln in content.splitlines()]
        ok = "M7 Sales" in lines
        if ok:
            return {"pass": True, "msg": "OK 'M7 Sales' có trong modules.txt"}
        return {"pass": False, "msg": f"X 'M7 Sales' không có trong modules.txt (lines={lines})"}
    except Exception as e:
        return {"pass": False, "msg": f"X threw: {str(e)[:200]}"}


def run():
    tests = [
        test_revenue_account_exists,
        test_settings_has_fiscal_lock,
        test_m7_sales_module_registered,
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
