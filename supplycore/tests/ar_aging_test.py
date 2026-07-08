"""Test GD4 Task 4 -- Dashboard cong no phai thu (AR aging theo khach hang,
BRU-AR-001: canh bao vuot han muc tin dung).

Run individual: bench --site supplycore-miyano.local execute supplycore.tests.ar_aging_test.test_<name>
Run all:        bench --site supplycore-miyano.local execute supplycore.tests.ar_aging_test.run
"""

import frappe
from frappe.utils import today, flt, random_string

from supplycore.tests.sc_sales_invoice_test import _seed_chain, _make_si
from supplycore.tests.portal_api_test import _make_portal_customer


def _make_receipt(customer, sales_invoice, amount, mode="Chuyển khoản"):
    sr = frappe.new_doc("SC Sales Receipt")
    sr.customer = customer
    sr.sales_invoice = sales_invoice
    sr.receipt_date = today()
    sr.amount = flt(amount)
    sr.mode = mode
    sr.flags.ignore_permissions = True
    return sr


# ---------- Tests ----------

def test_ar_aging_by_customer():
    """SI submit chua thu -> khach xuat hien voi total_outstanding + bucket 0_30
    dung; sau thu mot phan -> total_outstanding giam tuong ung."""
    from supplycore.m8_accounting.api.financial_reports import ar_aging_by_customer

    ctx = _seed_chain("ARAGE", qty=30, unit_price=1000)  # grand_total = 30000
    si = _make_si(ctx)
    try:
        si.insert()
        si.submit()

        res = ar_aging_by_customer(customer=ctx["customer"].name)
        rows = [r for r in res["rows"] if r["customer"] == ctx["customer"].name]
        if not rows:
            frappe.db.rollback()
            return {"pass": False, "msg": f"X khach khong xuat hien trong AR aging: {res}"}
        row = rows[0]
        ok1 = (flt(row["total_outstanding"]) == 30000
               and flt(row["buckets"]["0_30"]) == 30000
               and flt(row["buckets"]["31_60"]) == 0
               and flt(row["buckets"]["61_90"]) == 0
               and flt(row["buckets"]["over_90"]) == 0)
        if not ok1:
            frappe.db.rollback()
            return {"pass": False, "msg": f"X row ban dau: {row}"}

        # Thu mot phan 10000 -> outstanding con 20000
        sr = _make_receipt(ctx["customer"].name, si.name, 10000)
        sr.insert()
        sr.submit()

        res2 = ar_aging_by_customer(customer=ctx["customer"].name)
        rows2 = [r for r in res2["rows"] if r["customer"] == ctx["customer"].name]
        frappe.db.rollback()
        if not rows2:
            return {"pass": False, "msg": "X khach bien mat khoi AR aging sau thu mot phan"}
        row2 = rows2[0]
        if flt(row2["total_outstanding"]) == 20000:
            return {"pass": True, "msg": f"OK ban dau=30000 sau thu 10000 -> {row2['total_outstanding']}"}
        return {"pass": False, "msg": f"X outstanding sau thu = {row2['total_outstanding']} (ky vong 20000)"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:250]}"}


def test_ar_aging_over_limit_flag():
    """credit_limit < total_outstanding -> over_limit True."""
    from supplycore.m8_accounting.api.financial_reports import ar_aging_by_customer

    ctx = _seed_chain("ARLIM", qty=10, unit_price=5000)  # grand_total = 50000
    si = _make_si(ctx)
    try:
        si.insert()
        si.submit()

        frappe.db.set_value("SC Customer", ctx["customer"].name, "credit_limit", 10000)

        res = ar_aging_by_customer(customer=ctx["customer"].name)
        rows = [r for r in res["rows"] if r["customer"] == ctx["customer"].name]
        frappe.db.rollback()
        if not rows:
            return {"pass": False, "msg": "X khach khong xuat hien trong AR aging"}
        row = rows[0]
        if row["over_limit"] is True and flt(row["credit_limit"]) == 10000:
            return {"pass": True, "msg": f"OK over_limit=True credit_limit=10000 outstanding={row['total_outstanding']}"}
        return {"pass": False, "msg": f"X row={row}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:250]}"}


def test_ar_aging_portal_denied():
    """User Portal (SC Customer Portal) goi ar_aging_by_customer -> PermissionError."""
    from supplycore.m8_accounting.api.financial_reports import ar_aging_by_customer

    orig_user = frappe.session.user
    try:
        cust, portal_email = _make_portal_customer(f"ARDENY{random_string(4)}")

        frappe.set_user(portal_email)
        try:
            ar_aging_by_customer()
            return {"pass": False, "msg": "X portal user goi ar_aging_by_customer khong throw"}
        except frappe.PermissionError:
            return {"pass": True, "msg": "OK PermissionError cho user Portal"}
    except Exception as e:
        return {"pass": False, "msg": f"X threw wrong exception: {str(e)[:200]}"}
    finally:
        frappe.set_user(orig_user)
        frappe.db.rollback()


def run():
    tests = [
        test_ar_aging_by_customer,
        test_ar_aging_over_limit_flag,
        test_ar_aging_portal_denied,
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
