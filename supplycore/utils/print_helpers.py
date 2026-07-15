"""Helper cho Print Format TT99 — đăng ký vào Jinja (hooks.py::jinja).

Dùng trong template: {{ sc_seller_info() }}, {{ sc_dong_in_words(doc.grand_total) }}.
"""

import frappe


def sc_seller_info() -> dict:
    """Thông tin đơn vị bán để in header chứng từ TT99 (đọc từ SupplyCore Settings).

    Trả {name, address, tax_code}. Rỗng → chuỗi rỗng (template tự xử lý)."""
    s = frappe.get_cached_doc("SupplyCore Settings")
    return {
        "name": s.get("site_name") or "",
        "address": s.get("site_address") or "",
        "tax_code": s.get("seller_tax_code") or "",
    }


def sc_dong_in_words(amount) -> str:
    from supplycore.utils.money import dong_in_words
    return dong_in_words(amount)


def sc_vnd(amount) -> str:
    """Định dạng số tiền kiểu Việt Nam (dấu CHẤM phân tách nghìn) — khớp hiển thị
    trên màn hình portal (fmtVND). Vd 40000 -> '40.000'."""
    from frappe.utils import flt
    return "{:,.0f}".format(flt(amount)).replace(",", ".")
