"""Test GĐ MVL — Workstream E: render Print Format TT99 (không lỗi Jinja + đủ yếu tố).

Kiểm mỗi chứng từ render được và chứa: tiêu đề, MST người bán, số tiền bằng chữ,
block chữ ký. Run: bench --site supplycore-miyano.local execute supplycore.tests.mvl_print_test.run
"""

import frappe
from frappe.utils import flt, today, add_days

from supplycore.tests.portal_api_test import (
    _seed_customer_with_contract, _make_approved_so, _pick_warehouse,
    _make_batch, _seed_stock, _get_uom,
)
from supplycore.api import sales


def _build_full_chain(suffix, qty=10, price=1000):
    cust, email, sfc, item = _seed_customer_with_contract(suffix, 100, price)
    frappe.db.set_value("SC Customer", cust, "credit_limit", 0)
    so = _make_approved_so(cust, sfc, item, qty)
    wh = _pick_warehouse()
    _seed_stock(item, wh, _make_batch(item, add_days(today(), 300)).name, qty * 3, rate=price)
    dn = sales.make_delivery(so.name, from_warehouse=wh)["name"]
    ar = sales.delivery_accept(dn, accepted_by="Trần Thị B")
    si = sales.sales_invoice_create(dn, tax_rate=0)["name"]
    rc = sales.receipt_collect(si, 4000)["name"] if hasattr(sales, "receipt_collect") else None
    return {"SFC": sfc, "SO": so.name, "DN": dn, "AR": ar, "SI": si, "RC": rc}


PRINT_MAP = [
    ("SC Sales Invoice", "SI", "TT99 - Hoá đơn bán hàng", "HOÁ ĐƠN"),
    ("SC Delivery Note", "DN", "TT99 - Phiếu giao hàng", "PHIẾU GIAO"),
    ("SC Acceptance Record", "AR", "TT99 - Biên bản nghiệm thu", "NGHIỆM THU"),
    ("SC Sales Framework Contract", "SFC", "TT99 - Hợp đồng khung bán hàng", "HỢP ĐỒNG KHUNG"),
    ("SC Sales Receipt", "RC", "TT99 - Phiếu thu", "PHIẾU THU"),
    ("SC Sales Order", "SO", "TT99 - Đơn gọi hàng", "ĐƠN GỌI HÀNG"),
]


def _render_pf(doctype, name, pf):
    """Render template Jinja của Print Format trên doc thật — độc lập web context
    (frappe.get_print cần frappe.local.request, không có trong bench console/batch;
    render_template dùng CÙNG jinja env + helper sc_seller_info/sc_dong_in_words)."""
    html = frappe.db.get_value("Print Format", pf, "html")
    doc = frappe.get_doc(doctype, name)
    return frappe.render_template(html, {"doc": doc})


def test_render_all_tt99():
    try:
        frappe.db.set_single_value("SupplyCore Settings", "seller_tax_code", "0100686209")
        docs = _build_full_chain("PRT")
        failed = []
        for doctype, key, pf, needle in PRINT_MAP:
            name = docs.get(key)
            if not name:
                failed.append(f"{pf}: thiếu doc"); continue
            try:
                html = _render_pf(doctype, name, pf)
            except Exception as e:
                failed.append(f"{pf}: render lỗi {repr(e)[:80]}"); continue
            if needle not in html:
                failed.append(f"{pf}: thiếu tiêu đề '{needle}'")
            if "0100686209" not in html:
                failed.append(f"{pf}: thiếu MST người bán")
            if "Ký" not in html:
                failed.append(f"{pf}: thiếu block chữ ký")
        if failed:
            return {"pass": False, "msg": "; ".join(failed)[:300]}
        return {"pass": True, "msg": "OK 6 print format TT99 render đủ tiêu đề+MST+chữ ký"}
    finally:
        frappe.db.rollback()


def test_invoice_amount_in_words():
    """Hoá đơn phải có 'Số tiền bằng chữ' khớp grand_total."""
    try:
        frappe.db.set_single_value("SupplyCore Settings", "seller_tax_code", "0100686209")
        docs = _build_full_chain("PRTW", qty=12, price=1000)
        html = _render_pf("SC Sales Invoice", docs["SI"], "TT99 - Hoá đơn bán hàng")
        from supplycore.utils.money import dong_in_words
        gt = flt(frappe.db.get_value("SC Sales Invoice", docs["SI"], "grand_total")) or 12000
        words = dong_in_words(gt)
        ok = "bằng chữ" in html and words in html
        return {"pass": ok, "msg": f"OK tiền bằng chữ '{words}'" if ok
                else f"X thiếu/sai tiền bằng chữ (cần '{words}')"}
    finally:
        frappe.db.rollback()


TESTS = [test_render_all_tt99, test_invoice_amount_in_words]


def run():
    results = []; passed = 0
    for t in TESTS:
        try:
            r = t()
        except Exception as e:
            r = {"pass": False, "msg": f"EXCEPTION: {repr(e)[:200]}"}
        results.append(r)
        if r.get("pass"):
            passed += 1
        print(f"  {'✓' if r.get('pass') else '✗'} {t.__name__}: {r.get('msg')}")
    print(f"mvl_print_test: {passed}/{len(TESTS)}")
    return {"passed": passed, "total": len(TESTS), "results": results}
