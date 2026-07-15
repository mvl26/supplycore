"""Test BRU-PAY-001 fiscal lock — chặn submit/cancel vào kỳ đã khóa sổ trên
CẢ 4 doctype kế toán (SC Sales Invoice, SC Sales Receipt, SC Purchase
Invoice, SC Payment Entry), bao gồm cả đường CANCEL (trước fix chỉ SI/SR
submit có check; PI/PE submit và MỌI đường cancel không hề chặn).

Run individual: bench --site supplycore-miyano.local execute supplycore.tests.fiscal_lock_test.test_<name>
Run all:        bench --site supplycore-miyano.local execute supplycore.tests.fiscal_lock_test.run
"""

import frappe
from frappe.utils import today, add_days, random_string, flt

from supplycore.tests import sc_sales_invoice_test as sit
from supplycore.tests import sc_sales_receipt_test as srt


# ---------------------------------------------------------------------------
# Helpers PI/PE — tự chứa (không phụ thuộc master data cụ thể của smoke_m8).
# ---------------------------------------------------------------------------
def _get_uom() -> str:
    uom = frappe.db.get_value("SC UOM", {}, "name")
    if not uom:
        frappe.throw("fiscal_lock_test: cần seed SC UOM")
    return uom


def _pick_warehouse() -> str:
    rows = frappe.get_all("SC Warehouse", filters={"is_group": 0, "disabled": 0},
                           pluck="name", order_by="name", limit=1)
    if not rows:
        frappe.throw("fiscal_lock_test: cần seed SC Warehouse")
    return rows[0]


def _make_supplier(suffix):
    sup = frappe.new_doc("SC Supplier")
    sup.supplier_name = f"NCC fiscal-lock test {suffix}"
    import random
    sup.tax_id = "".join(str(random.randint(0, 9)) for _ in range(10))
    sup.supplier_type = "Nhà phân phối"
    sup.email_id = f"fisclk-{random_string(6)}@example.com"
    sup.mobile_no = "0900000000"
    sup.address = "Test address"
    sup.flags.ignore_permissions = True
    sup.insert()
    return sup


def _make_item(suffix):
    item = frappe.new_doc("SC Item")
    item.item_code = f"FISCLK-{suffix}-{random_string(5)}"
    item.item_name = f"fiscal-lock test item {suffix}"
    item.uom = _get_uom()
    item.is_stock_item = 1
    item.is_purchase_item = 1
    item.flags.ignore_permissions = True
    item.insert()
    return item


def _make_pi(supplier, item, invoice_date=None):
    pi = frappe.new_doc("SC Purchase Invoice")
    pi.supplier = supplier
    pi.supplier_invoice_no = f"FL-{random_string(6)}"
    pi.invoice_date = invoice_date or today()
    pi.vat_rate = 0
    pi.append("items", {"item": item, "qty": 10, "uom": _get_uom(), "rate": 5000})
    pi.flags.ignore_permissions = True
    return pi


def _set_lock(date_value):
    frappe.db.set_single_value("SupplyCore Settings", "fiscal_lock_date", date_value)


def _get_lock():
    return frappe.db.get_single_value("SupplyCore Settings", "fiscal_lock_date")


# ---------- Tests ----------

def test_pi_submit_blocked_in_locked_period():
    """Settings.fiscal_lock_date >= invoice_date -> submit PI throw
    SC-E-FISCAL-LOCK; lock trong quá khứ -> submit thành công."""
    sup = _make_supplier("PISUB")
    item = _make_item("PISUB")
    old_lock = _get_lock()
    try:
        pi = _make_pi(sup.name, item.name)
        pi.insert()

        _set_lock(today())  # >= invoice_date=today() -> khóa
        try:
            pi.submit()
            frappe.db.rollback()
            return {"pass": False, "msg": "X submit did not throw while locked"}
        except frappe.ValidationError as e:
            msg = str(e)
            if "SC-E-FISCAL-LOCK" not in msg:
                frappe.db.rollback()
                return {"pass": False, "msg": f"X threw wrong msg: {msg[:150]}"}

        _set_lock(add_days(today(), -1))  # quá khứ -> mở khóa
        pi.reload()
        pi.submit()
        pi.reload()
        ok = pi.docstatus == 1
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": "OK blocked when locked, submit OK when unlocked"}
        return {"pass": False, "msg": f"X docstatus after unlock={pi.docstatus}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw unexpected: {str(e)[:250]}"}
    finally:
        _set_lock(old_lock)
        frappe.db.rollback()


def test_pe_submit_blocked_in_locked_period():
    """Settings.fiscal_lock_date >= payment_date -> submit PE throw
    SC-E-FISCAL-LOCK; lock trong quá khứ -> submit thành công."""
    sup = _make_supplier("PESUB")
    item = _make_item("PESUB")
    old_lock = _get_lock()
    try:
        pi = _make_pi(sup.name, item.name)
        pi.insert()
        pi.submit()
        pi.reload()

        pe = frappe.new_doc("SC Payment Entry")
        pe.supplier = sup.name
        pe.payment_date = today()
        pe.payment_method = "Bank Transfer"
        pe.bank_account = "Vietcombank 0123456"
        pe.reference_no = f"BANK-{random_string(6)}"
        pe.amount = flt(pi.outstanding_amount)
        pe.append("references", {
            "purchase_invoice": pi.name,
            "allocated_amount": flt(pi.outstanding_amount),
        })
        pe.flags.ignore_permissions = True
        pe.insert()

        _set_lock(today())  # >= payment_date -> khóa
        try:
            pe.submit()
            frappe.db.rollback()
            return {"pass": False, "msg": "X submit did not throw while locked"}
        except frappe.ValidationError as e:
            msg = str(e)
            if "SC-E-FISCAL-LOCK" not in msg:
                frappe.db.rollback()
                return {"pass": False, "msg": f"X threw wrong msg: {msg[:150]}"}

        _set_lock(add_days(today(), -1))  # quá khứ -> mở khóa
        pe.reload()
        pe.submit()
        pe.reload()
        ok = pe.docstatus == 1
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": "OK blocked when locked, submit OK when unlocked"}
        return {"pass": False, "msg": f"X docstatus after unlock={pe.docstatus}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw unexpected: {str(e)[:250]}"}
    finally:
        _set_lock(old_lock)
        frappe.db.rollback()


def test_pi_cancel_blocked_in_locked_period():
    """PI đã submit (lock chưa cấu hình) -> khóa sổ (>= invoice_date) SAU ĐÓ
    -> cancel phải throw SC-E-FISCAL-LOCK (không cho cancel_voucher đảo GL
    ngược vào kỳ đã khóa); mở khóa lại (quá khứ) -> cancel thành công."""
    sup = _make_supplier("PICANCEL")
    item = _make_item("PICANCEL")
    old_lock = _get_lock()
    try:
        pi = _make_pi(sup.name, item.name)
        pi.insert()
        pi.submit()
        pi.reload()

        _set_lock(today())  # khóa SAU khi đã submit
        try:
            pi.cancel()
            frappe.db.rollback()
            return {"pass": False, "msg": "X cancel did not throw while locked"}
        except frappe.ValidationError as e:
            msg = str(e)
            if "SC-E-FISCAL-LOCK" not in msg:
                frappe.db.rollback()
                return {"pass": False, "msg": f"X threw wrong msg: {msg[:150]}"}

        pi.reload()
        if pi.docstatus != 1:
            frappe.db.rollback()
            return {"pass": False, "msg": f"X PI docstatus changed despite blocked cancel: {pi.docstatus}"}

        _set_lock(add_days(today(), -1))  # mở khóa
        pi.cancel()
        pi.reload()
        ok = pi.docstatus == 2
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": "OK cancel blocked when locked, OK when unlocked"}
        return {"pass": False, "msg": f"X docstatus after unlock cancel={pi.docstatus}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw unexpected: {str(e)[:250]}"}
    finally:
        _set_lock(old_lock)
        frappe.db.rollback()


def test_si_cancel_blocked_in_locked_period():
    """SI đã submit (lock chưa cấu hình) -> khóa sổ (>= invoice_date) SAU ĐÓ
    -> cancel phải throw SC-E-FISCAL-LOCK; mở khóa lại (quá khứ) -> cancel OK."""
    old_lock = _get_lock()
    try:
        ctx = sit._seed_chain("FLKCANCEL", qty=10)
        si = sit._make_si(ctx)
        si.insert()
        si.submit()
        si.reload()

        _set_lock(today())
        try:
            si.cancel()
            frappe.db.rollback()
            return {"pass": False, "msg": "X cancel did not throw while locked"}
        except frappe.ValidationError as e:
            msg = str(e)
            if "SC-E-FISCAL-LOCK" not in msg:
                frappe.db.rollback()
                return {"pass": False, "msg": f"X threw wrong msg: {msg[:150]}"}

        si.reload()
        if si.docstatus != 1:
            frappe.db.rollback()
            return {"pass": False, "msg": f"X SI docstatus changed despite blocked cancel: {si.docstatus}"}

        _set_lock(add_days(today(), -1))
        si.cancel()
        si.reload()
        ok = si.docstatus == 2
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": "OK cancel blocked when locked, OK when unlocked"}
        return {"pass": False, "msg": f"X docstatus after unlock cancel={si.docstatus}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw unexpected: {str(e)[:250]}"}
    finally:
        _set_lock(old_lock)
        frappe.db.rollback()


def test_sr_cancel_blocked_in_locked_period():
    """SR đã submit (lock chưa cấu hình) -> khóa sổ (>= receipt_date) SAU ĐÓ
    -> cancel phải throw SC-E-FISCAL-LOCK; mở khóa lại (quá khứ) -> cancel OK."""
    old_lock = _get_lock()
    try:
        ctx = srt._seed_chain("FLKCANCEL", qty=10, unit_price=1000)
        sr = srt._make_receipt(ctx, 4000)
        sr.insert()
        sr.submit()
        sr.reload()

        _set_lock(today())
        try:
            sr.cancel()
            frappe.db.rollback()
            return {"pass": False, "msg": "X cancel did not throw while locked"}
        except frappe.ValidationError as e:
            msg = str(e)
            if "SC-E-FISCAL-LOCK" not in msg:
                frappe.db.rollback()
                return {"pass": False, "msg": f"X threw wrong msg: {msg[:150]}"}

        sr.reload()
        if sr.docstatus != 1:
            frappe.db.rollback()
            return {"pass": False, "msg": f"X SR docstatus changed despite blocked cancel: {sr.docstatus}"}

        _set_lock(add_days(today(), -1))
        sr.cancel()
        sr.reload()
        ok = sr.docstatus == 2
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": "OK cancel blocked when locked, OK when unlocked"}
        return {"pass": False, "msg": f"X docstatus after unlock cancel={sr.docstatus}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw unexpected: {str(e)[:250]}"}
    finally:
        _set_lock(old_lock)
        frappe.db.rollback()


def run():
    tests = [
        test_pi_submit_blocked_in_locked_period,
        test_pe_submit_blocked_in_locked_period,
        test_pi_cancel_blocked_in_locked_period,
        test_si_cancel_blocked_in_locked_period,
        test_sr_cancel_blocked_in_locked_period,
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
