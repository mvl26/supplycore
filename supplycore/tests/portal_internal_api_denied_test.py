"""Test GD4 Task 5 -- Security sweep: portal reachability cua API noi bo
(bao cao tai chinh/ton kho/KPI/truy xuat/audit).

Boi canh: audit toan bo @frappe.whitelist() trong supplycore/api/*.py va
supplycore/m*/api/*.py phat hien nhieu ham KHONG co bat ky permission check
nao (chi kiem business logic) -- 1 user dang nhap CO role "SC Customer
Portal" (chi duoc cap read/report/print/email tren 5 doctype ban hang) van
goi thang duoc qua /api/method/... va doc du lieu NOI BO (cong no NCC/khach,
gia tri ton kho, KPI dashboard toan cong ty, truy xuat lo/batch xuyen kho,
audit trail kem IP). Vi du dien hinh phat hien dau tien:
`m8_accounting.api.financial_reports.ap_aging_report` (cong no phai tra NCC)
hoan toan khong gate. Sweep them va bit bang `block_portal()`
(`supplycore.utils.permissions.block_portal` -- block-list, chi chan role
Portal, khong dung allow-list de tranh hoi quy role noi bo khac) hoac
`_require_finance_report_role()` (allow-list rieng cho bao cao tai chinh).

RED (truoc khi gate, xem git log truoc commit nay): tat ca ham duoi day
khong throw PermissionError cho portal user. GREEN (sau khi gate): portal
user -> frappe.PermissionError; user noi bo (SupplyCore Manager) van goi
duoc binh thuong (khong regress).

Run individual: bench --site supplycore-miyano.local execute supplycore.tests.portal_internal_api_denied_test.test_<name>
Run all:        bench --site supplycore-miyano.local execute supplycore.tests.portal_internal_api_denied_test.run
"""

import frappe
from frappe.utils import random_string, add_days, today

from supplycore.tests.portal_api_test import _make_portal_customer, _make_manager_user, _make_item, _make_batch


def _call_denied_for_portal_ok_for_manager(fn, kwargs):
    """Goi fn(**kwargs) nhu 1 user Portal (ky vong frappe.PermissionError),
    roi nhu 1 user noi bo SupplyCore Manager (KHONG duoc la PermissionError
    -- loi nghiep vu khac vi thieu du lieu la chap nhan duoc, mien la
    permission check khong chan nham nguoi noi bo)."""
    orig_user = frappe.session.user
    try:
        _cust, portal_email = _make_portal_customer(f"IAPI{random_string(5)}")
        manager_email = _make_manager_user()

        frappe.set_user(portal_email)
        try:
            fn(**kwargs)
            return {"pass": False, "msg": (
                f"X portal user goi {fn.__module__}.{fn.__name__} KHONG bi chan "
                f"(khong throw PermissionError) -- RO RI du lieu noi bo"
            )}
        except frappe.PermissionError:
            pass
        except Exception as e:
            return {"pass": False, "msg": (
                f"X portal user goi {fn.__name__} throw SAI loai "
                f"{type(e).__name__}: {str(e)[:150]} (ky vong frappe.PermissionError)"
            )}

        frappe.set_user(manager_email)
        try:
            fn(**kwargs)
        except frappe.PermissionError as e:
            return {"pass": False, "msg": (
                f"X internal Manager (SupplyCore Manager) BI CHAN NHAM (regression) "
                f"khi goi {fn.__name__}: {str(e)[:150]}"
            )}
        except Exception:
            # Loi nghiep vu khac (vd thieu du lieu seed) chap nhan duoc -- chi
            # can KHONG phai PermissionError la du de xac nhan khong hoi quy.
            pass

        return {"pass": True, "msg": (
            f"OK {fn.__module__}.{fn.__name__}: portal -> PermissionError, "
            f"Manager noi bo khong bi chan"
        )}
    except Exception as e:
        return {"pass": False, "msg": f"X threw setup error: {str(e)[:200]}"}
    finally:
        frappe.set_user(orig_user)
        frappe.db.rollback()


# ---------- Tests ----------

def test_ap_aging_report_denied():
    """Phat hien goc (task-4 report): cong no phai tra NCC -- ban dau KHONG
    gate gi ca, portal user doc duoc toan bo payables noi bo."""
    from supplycore.m8_accounting.api.financial_reports import ap_aging_report
    return _call_denied_for_portal_ok_for_manager(ap_aging_report, {})


def test_inventory_value_report_denied():
    """Gia tri ton kho toan he thong theo warehouse/item_group."""
    from supplycore.m8_accounting.api.financial_reports import inventory_value_report
    return _call_denied_for_portal_ok_for_manager(inventory_value_report, {})


def test_get_executive_dashboard_denied():
    """KPI dashboard dieu hanh toan cong ty (M11)."""
    from supplycore.api.kpi import get_executive_dashboard
    return _call_denied_for_portal_ok_for_manager(get_executive_dashboard, {"period": "this_month"})


def test_get_batch_trace_denied():
    """Truy xuat nguon goc lo (M10) -- NCC, gia von, ton kho xuyen kho."""
    from supplycore.api.trace import get_batch_trace
    item = _make_item(f"IAPIBATCH{random_string(4)}")
    batch = _make_batch(item.name, add_days(today(), 200))
    return _call_denied_for_portal_ok_for_manager(get_batch_trace, {"batch_no": batch.name})


def test_stock_balance_denied():
    """Ton kho realtime theo item/warehouse/batch (SPA nội bộ, api/frontend.py)."""
    from supplycore.api.frontend import stock_balance
    return _call_denied_for_portal_ok_for_manager(stock_balance, {})


def test_investigation_audit_trail_denied():
    """Audit trail SLE kem IP nguoi thao tac (UC-31, m10_traceability)."""
    from supplycore.m10_traceability.api.investigation import get_audit_trail
    return _call_denied_for_portal_ok_for_manager(get_audit_trail, {})


def run():
    tests = [
        test_ap_aging_report_denied,
        test_inventory_value_report_denied,
        test_get_executive_dashboard_denied,
        test_get_batch_trace_denied,
        test_stock_balance_denied,
        test_investigation_audit_trail_denied,
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
