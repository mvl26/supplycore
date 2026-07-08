"""Test BUG-FIX: SC Purchase Invoice debit/credit note (tra hang NCC) GL dao chieu.

Adversarial audit finding: _post_gl_entries() luon post chieu MUA HANG THUONG
(Dr 152 / Dr 1331 / Cr 331) ke ca khi PI la debit/credit note tra hang cho
NCC (is_debit_note=1 hoac is_credit_note=1). Tra hang phai GIAM cong no phai
tra (Dr 331) va GIAM ton kho (Cr 152) -- nguoc lai voi chieu mua hang thuong.

Note ve get_balance(): SCGLEntry.get_balance = RAW SUM(debit) - SUM(credit),
KHONG dao dau theo loai TK (xem docstring vs code trong sc_gl_entry.py -- comment
noi "Liability dao dau" nhung code khong lam vay). Vi vay:
  - PI thuong:      Cr 331 grand_total -> get_balance("331") GIAM (delta = -grand_total)
  - Debit/Credit Note (dao chieu): Dr 331 grand_total -> get_balance("331") TANG
    (delta = +grand_total) -- day la bang chung GL da dao chieu dung.
  - 152: PI thuong Dr subtotal (delta +subtotal); return note Cr subtotal (delta -subtotal).

Run individual: bench --site supplycore-miyano.local execute supplycore.tests.pi_return_gl_test.test_<name>
Run all:        bench --site supplycore-miyano.local execute supplycore.tests.pi_return_gl_test.run
"""

import frappe
from frappe.utils import today, add_days, random_string, flt

from supplycore.supplycore.doctype.sc_gl_entry.sc_gl_entry import SCGLEntry


def _gl_seeded() -> bool:
    return bool(
        frappe.db.exists("SC GL Account", "152")
        and frappe.db.exists("SC GL Account", "331")
    )


def _pick_warehouse() -> str:
    rows = frappe.get_all("SC Warehouse", filters={"is_group": 0, "disabled": 0},
                           pluck="name", order_by="name", limit=1)
    if not rows:
        frappe.throw("pi_return_gl_test: cần seed SC Warehouse")
    return rows[0]


def _get_uom() -> str:
    uom = frappe.db.get_value("SC UOM", {}, "name")
    if not uom:
        frappe.throw("pi_return_gl_test: cần seed SC UOM")
    return uom


def _make_supplier(suffix):
    sup = frappe.new_doc("SC Supplier")
    sup.supplier_name = f"NCC PI-GL test {suffix}"
    import random
    sup.tax_id = "".join(str(random.randint(0, 9)) for _ in range(10))
    sup.supplier_type = "Nhà phân phối"
    sup.email_id = f"pigl-{random_string(6)}@example.com"
    sup.mobile_no = "0900000000"
    sup.address = "Test address"
    sup.flags.ignore_permissions = True
    sup.insert()
    return sup


def _make_item(suffix):
    item = frappe.new_doc("SC Item")
    item.item_code = f"PIGL-{suffix}-{random_string(5)}"
    item.item_name = f"PI-GL test item {suffix}"
    item.uom = _get_uom()
    item.is_stock_item = 1
    item.is_purchase_item = 1
    item.flags.ignore_permissions = True
    item.insert()
    return item


# ---------- Tests ----------

def test_normal_pi_gl_direction():
    """Regression guard: PI thường (không phải return note) vẫn post
    Dr 152 / Cr 331 — get_balance('331', supplier) GIẢM đúng bằng grand_total."""
    if not _gl_seeded():
        return {"pass": True, "msg": "SKIP: chưa seed SC GL Account 152/331"}
    sup = _make_supplier("NORMAL")
    item = _make_item("NORMAL")
    try:
        before_331 = SCGLEntry.get_balance("331", sup.name)
        before_152 = SCGLEntry.get_balance("152")

        pi = frappe.new_doc("SC Purchase Invoice")
        pi.supplier = sup.name
        pi.supplier_invoice_no = f"NORM-{random_string(6)}"
        pi.invoice_date = today()
        pi.vat_rate = 0
        pi.append("items", {"item": item.name, "qty": 10, "uom": _get_uom(), "rate": 5000})
        pi.flags.ignore_permissions = True
        pi.insert()
        pi.submit()
        pi.reload()

        after_331 = SCGLEntry.get_balance("331", sup.name)
        after_152 = SCGLEntry.get_balance("152")
        delta_331 = flt(after_331 - before_331)
        delta_152 = flt(after_152 - before_152)

        ok = (delta_331 == -flt(pi.grand_total)) and (delta_152 == flt(pi.subtotal))
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK delta_331={delta_331} delta_152={delta_152} grand_total={pi.grand_total}"}
        return {"pass": False, "msg": f"X delta_331={delta_331} (exp {-flt(pi.grand_total)}) delta_152={delta_152} (exp {flt(pi.subtotal)})"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:250]}"}


def test_return_note_gl_reversed():
    """Return PR -> make_debit_note() -> submit PI (is_debit_note=1) -> GL phải
    ĐẢO CHIỀU: Dr 331 (payable giảm, get_balance TĂNG) / Cr 152 (tồn kho giảm,
    get_balance GIẢM). Đây là test RED trước fix (code cũ post Cr 331/Dr 152 —
    giống PI thường — nên delta_331 sẽ âm thay vì dương)."""
    if not _gl_seeded():
        return {"pass": True, "msg": "SKIP: chưa seed SC GL Account 152/331"}
    sup = _make_supplier("RETURN")
    item = _make_item("RETURN")
    try:
        # Return PR (không cần PO — is_return=1 bypass no_po_reason requirement)
        pr = frappe.new_doc("SC Purchase Receipt")
        pr.supplier = sup.name
        pr.posting_date = today()
        pr.to_warehouse = _pick_warehouse()
        pr.is_return = 1
        pr.qc_required = 0
        pr.return_reason = "PI-GL test — hàng lỗi trả NCC"
        pr.append("items", {
            "item": item.name, "qty": 5, "uom": _get_uom(),
            "rate": 5000, "warehouse": _pick_warehouse(),
        })
        pr.flags.ignore_permissions = True
        pr.insert()
        pr.submit()
        pr.reload()

        dn_name = pr.debit_note
        if not dn_name:
            dn_name = pr.make_debit_note()
        pi = frappe.get_doc("SC Purchase Invoice", dn_name)
        ok_flags = (pi.is_debit_note == 1 and pi.docstatus == 0)
        if not ok_flags:
            frappe.db.rollback()
            return {"pass": False, "msg": f"X debit note draft sai: is_debit_note={pi.is_debit_note} docstatus={pi.docstatus}"}

        # PI draft từ make_debit_note không set vat_rate -> mặc định 0 => grand_total == subtotal
        before_331 = SCGLEntry.get_balance("331", sup.name)
        before_152 = SCGLEntry.get_balance("152")

        pi.flags.ignore_permissions = True
        pi.submit()
        pi.reload()

        after_331 = SCGLEntry.get_balance("331", sup.name)
        after_152 = SCGLEntry.get_balance("152")
        delta_331 = flt(after_331 - before_331)
        delta_152 = flt(after_152 - before_152)

        # Bằng chứng trực tiếp trên GL rows của voucher này (không phụ thuộc suy luận dấu)
        rows = frappe.get_all("SC GL Entry",
            filters={"voucher_type": "SC Purchase Invoice", "voucher_no": pi.name, "is_cancelled": 0},
            fields=["account", "debit", "credit"])
        acc_331 = frappe.db.get_value("SC GL Account", "331", "name") or \
            frappe.db.get_value("SC GL Account", {"account_code": "331"}, "name")
        acc_152 = frappe.db.get_value("SC GL Account", "152", "name") or \
            frappe.db.get_value("SC GL Account", {"account_code": "152"}, "name")
        row_331 = next((r for r in rows if r.account == acc_331), None)
        row_152 = next((r for r in rows if r.account == acc_152), None)

        row_ok = (row_331 and flt(row_331.debit) == flt(pi.grand_total) and flt(row_331.credit) == 0
                  and row_152 and flt(row_152.credit) == flt(pi.subtotal) and flt(row_152.debit) == 0)

        # get_balance là RAW debit - credit (không đảo dấu theo loại TK) — xem module docstring.
        # Dr 331 (return note) => get_balance TĂNG; Cr 152 => get_balance GIẢM.
        balance_ok = (delta_331 == flt(pi.grand_total)) and (delta_152 == -flt(pi.subtotal))

        ok = row_ok and balance_ok
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK reversed: delta_331={delta_331} (+grand_total) delta_152={delta_152} (-subtotal); rows={rows}"}
        return {"pass": False, "msg": f"X delta_331={delta_331} (exp +{flt(pi.grand_total)}) delta_152={delta_152} (exp -{flt(pi.subtotal)}); row_331={row_331} row_152={row_152}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:250]}"}


def run():
    tests = [
        test_normal_pi_gl_direction,
        test_return_note_gl_reversed,
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
