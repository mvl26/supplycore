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
from frappe.utils import random_string, add_days, today, flt

from supplycore.tests.portal_api_test import (
    _make_portal_customer, _make_manager_user, _make_item, _make_batch, _get_uom,
)


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


def test_data_io_export_denied():
    """RSK-01 Critical (task-5 completeness sweep): api/data_io.py whitelisted
    functions chi kiem `frappe.has_permission(doctype, "read")` (doctype-level,
    khong theo tung doc) roi doc du lieu qua `frappe.get_all(doctype, ...)` --
    ham nay CO ignore_permissions=True mac dinh va bo qua ca
    `permission_query_conditions` lan `has_permission` per-doc dung de co lap
    khach hang (xem `portal_doc_permission`/`sales_invoice_portal_query` trong
    utils/permissions.py). `doctype` la tham so tu do do caller truyen, khong
    co allowlist. Vi role "SC Customer Portal" co doctype-level read=1 tren 5
    doctype ban hang, portal user co the goi thang:
      export_data(doctype="SC Sales Invoice", fields=[...], filters={})
    va lay duoc hoa don cua MOI khach hang (khong chi cua minh) -- bulk-export
    cheo khach xuyen suot toan bo module ban hang (SO/DN/SI/Receipt/FC).
    RED (truoc fix): khong throw PermissionError -> ro ri toan bo. GREEN (sau
    fix, gate bang `block_portal()`): portal -> PermissionError; internal
    Manager (SupplyCore Manager) van goi binh thuong tren doctype minh co
    quyen -- khong hoi quy."""
    from supplycore.api.data_io import export_data, export_list, get_template

    checks = [
        ("export_data", export_data, {
            "doctype": "SC Sales Invoice",
            "fields": ["name", "customer", "grand_total", "outstanding_amount"],
            "filters": {},
        }),
        ("export_list", export_list, {"doctype": "SC Sales Invoice", "filters": {}}),
        ("get_template", get_template, {"doctype": "SC Sales Invoice", "with_data": 1}),
    ]

    fails = []
    for label, fn, kwargs in checks:
        r = _call_denied_for_portal_ok_for_manager(fn, kwargs)
        if not r.get("pass"):
            fails.append(f"{label}: {r.get('msg')}")

    if fails:
        return {"pass": False, "msg": " | ".join(fails)}
    return {"pass": True, "msg": (
        "OK data_io.export_data/export_list/get_template: portal -> "
        "PermissionError, Manager noi bo khong bi chan")}


def test_frontend_list_docs_denied():
    """RSK-01 Critical (task-5 completeness sweep, sibling gap phat hien qua
    audit doc dong voi data_io.py): `api/frontend.py::list_docs` truyen
    `ignore_permissions=False` vao `frappe.db.get_all(doctype, **kwargs)`,
    nhung `frappe.get_all()` (frappe/__init__.py) LUON ghi de
    `kwargs["ignore_permissions"] = True` truoc khi goi `get_list` -- nghia la
    `permission_query_conditions` (co che co lap khach hang cho 5 doctype ban
    hang) khong bao gio duoc ap dung o day, bat ke tham so truyen vao. Chi con
    lai `frappe.has_permission(doctype, "read")` doctype-level -- ma role
    "SC Customer Portal" co read=1 tren ca 5 doctype do. Sibling `count_docs`
    trong cung file DA duoc gate tu GD4 Task 5 (docstring tu giai thich chinh
    ly do nay) nhung `list_docs` -- ro ri NANG HON vi tra ca hang du lieu chu
    khong chi tong so -- lai bi bo sot. RED (truoc fix): portal user goi
    list_docs(doctype="SC Sales Invoice", ...) khong throw, nhan duoc hang
    hoa don CUA MOI khach hang. GREEN (sau fix, gate bang `block_portal()`
    giong het `count_docs`): portal -> PermissionError; internal Manager van
    goi binh thuong -- khong hoi quy."""
    from supplycore.api.frontend import list_docs
    return _call_denied_for_portal_ok_for_manager(
        list_docs,
        {"doctype": "SC Sales Invoice", "fields": ["name", "customer"], "filters": {}},
    )


def test_related_docs_denied():
    """Defense-in-depth (commit dc0dd6d): `api/frontend.py::related_docs` dung
    `frappe.db.get_all` (= `frappe.get_all`, luon ignore_permissions=True) cho
    cac truy van "related" lien ket (vd PO -> PR/PI/MR) sau khi da qua
    `has_permission(doctype, "read", doc=name)` tren doc goc -- doc-level check
    da chan Portal (khong co DocPerm tren cac doctype procurement ma ham nay xu
    ly), nhung them `block_portal()` dau ham de nhat quan voi thiet ke "Portal
    chi duoc goi api/portal.py, khong bao gio goi frontend.py" (khong phu thuoc
    vao viec ram tuong lai co them nhanh doctype ban hang moi vao ham nay)."""
    from supplycore.api.frontend import related_docs
    item = _make_item(f"IAPIREL{random_string(4)}")
    return _call_denied_for_portal_ok_for_manager(related_docs, {"doctype": "SC Item", "name": item.name})


def test_get_doc_versions_denied():
    """Defense-in-depth (commit dc0dd6d): `get_doc_versions` tra lich su sua
    (tabVersion) cho bat ky doctype/docname nao caller co quyen "read" -- gate
    them `block_portal()` de Portal khong bao gio goi duoc ham SPA nội bộ nay,
    dong bo voi nguyen tac thiet ke portal chi qua api/portal.py."""
    from supplycore.api.frontend import get_doc_versions
    item = _make_item(f"IAPIVER{random_string(4)}")
    return _call_denied_for_portal_ok_for_manager(get_doc_versions, {"doctype": "SC Item", "name": item.name})


def test_sales_order_approve_reject_denied():
    """Privilege escalation (khong phai RSK-01 ro ri cheo khach, ma la bypass
    quy trinh duyet noi bo): `run_doc_method` (duong goi whitelisted instance
    method qua HTTP) chi kiem `doc.has_permission("read")` truoc khi invoke
    method -- KHONG kiem gi them cho tung hanh dong. Role "SC Customer
    Portal" co read=1 tren CHINH don hang cua khach (da scope dung qua
    portal_doc_permission), nen neu `SC Sales Order.approve()`/`reject()`
    khong tu gate rieng, khach hang co the tu goi approve() DUYET LUON don
    hang cua chinh minh -- bo qua buoc duyet noi bo (approval_by bi ghi la
    chinh email cua khach, khong phai nguoi duyet that). Da xac nhan bang
    thuc nghiem (goi truc tiep doc.approve() duoi session portal) -- thanh
    cong, khong throw gi -- TRUOC khi them `block_portal()`. Da fix bang
    `block_portal()` dau ca hai method (mirror pattern block-list dung cho
    moi API noi bo khac trong sweep nay)."""
    cust, portal_email = _make_portal_customer(f"SOAPR{random_string(5)}")
    item = _make_item(f"SOAPR{random_string(4)}")
    uom = _get_uom()

    sfc = frappe.new_doc("SC Sales Framework Contract")
    sfc.customer = cust.name
    sfc.valid_from = today()
    sfc.valid_to = add_days(today(), 365)
    sfc.append("items", {"item": item.name, "uom": uom, "contract_qty": flt(100), "unit_price": flt(1000)})
    sfc.flags.ignore_permissions = True
    sfc.insert()
    sfc.submit()

    so = frappe.new_doc("SC Sales Order")
    so.customer = cust.name
    so.framework_contract = sfc.name
    so.order_date = today()
    so.append("items", {"item": item.name, "uom": uom, "qty": flt(10), "unit_price": flt(1000)})
    so.flags.ignore_permissions = True
    so.insert()
    so.submit()

    orig_user = frappe.session.user
    try:
        manager_email = _make_manager_user()

        frappe.set_user(portal_email)
        doc = frappe.get_doc("SC Sales Order", so.name)
        try:
            doc.approve()
            return {"pass": False, "msg": (
                "X portal user tu goi approve() DUYET DUOC don hang cua chinh minh "
                "(khong throw PermissionError) -- BYPASS quy trinh duyet noi bo"
            )}
        except frappe.PermissionError:
            pass
        except Exception as e:
            return {"pass": False, "msg": f"X approve() throw sai loai {type(e).__name__}: {str(e)[:150]}"}

        doc2 = frappe.get_doc("SC Sales Order", so.name)
        try:
            doc2.reject()
            return {"pass": False, "msg": "X portal user tu goi reject() thanh cong -- khong bi chan"}
        except frappe.PermissionError:
            pass
        except Exception as e:
            return {"pass": False, "msg": f"X reject() throw sai loai {type(e).__name__}: {str(e)[:150]}"}

        frappe.set_user(manager_email)
        doc3 = frappe.get_doc("SC Sales Order", so.name)
        try:
            doc3.approve()
        except frappe.PermissionError as e:
            return {"pass": False, "msg": f"X internal Manager BI CHAN NHAM khi approve(): {str(e)[:150]}"}
        except Exception:
            pass

        return {"pass": True, "msg": (
            "OK SC Sales Order.approve()/reject(): portal -> PermissionError ca hai, "
            "Manager noi bo van approve() duoc"
        )}
    except Exception as e:
        return {"pass": False, "msg": f"X threw setup error: {str(e)[:200]}"}
    finally:
        frappe.set_user(orig_user)
        frappe.db.rollback()


def run():
    tests = [
        test_ap_aging_report_denied,
        test_inventory_value_report_denied,
        test_get_executive_dashboard_denied,
        test_get_batch_trace_denied,
        test_stock_balance_denied,
        test_investigation_audit_trail_denied,
        test_data_io_export_denied,
        test_frontend_list_docs_denied,
        test_related_docs_denied,
        test_get_doc_versions_denied,
        test_sales_order_approve_reject_denied,
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
