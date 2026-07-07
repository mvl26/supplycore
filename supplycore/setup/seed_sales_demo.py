"""Seed demo tối thiểu cho M7 Sales (Order-to-Cash) — bản phân phối MVL.

Mục đích: tạo nhanh 1 KH phân phối demo + 1 Hợp đồng khung bán hàng (SFC) đã
submit (status "Hiệu lực") với vài mặt hàng, để khảo sát Desk hoặc chạy tay
chuỗi SO -> DN -> Acceptance -> SI -> Receipt mà không cần tạo lại master data.
Idempotent: chạy lại không tạo trùng (dò theo tax_code / contract_no đã seed).

KHÔNG tự chạy trong patch — chỉ gọi thủ công khi cần demo:
    bench --site supplycore-miyano.local execute supplycore.setup.seed_sales_demo.run
"""

import frappe
from frappe.utils import today, add_days, flt


DEMO_CUSTOMER_NAME = "Công ty TNHH Thương mại ABC"
DEMO_CUSTOMER_TAX_CODE = "0101888999-DEMO-ABC"

# Mặt hàng mẫu (đã có sẵn từ seed_master_data) — bán buôn phân phối B2B,
# format: (item_code, contract_qty, unit_price)
DEMO_SFC_ITEMS = [
    ("DTRC-NACL09", 500, 32000),
    ("VTTH-IV-SET", 300, 13000),
]


def _get_or_create_customer() -> str:
    existing = frappe.db.get_value("SC Customer", {"tax_code": DEMO_CUSTOMER_TAX_CODE}, "name")
    if existing:
        return existing
    c = frappe.new_doc("SC Customer")
    c.customer_name = DEMO_CUSTOMER_NAME
    c.tax_code = DEMO_CUSTOMER_TAX_CODE
    c.billing_address = "Số 12 Đường Láng, Đống Đa, Hà Nội"
    c.shipping_address = "Kho phân phối 3, KCN Quang Minh, Mê Linh, Hà Nội"
    c.credit_limit = 500_000_000
    c.payment_terms = "Net 30"
    c.flags.ignore_permissions = True
    c.insert()
    return c.name


def _get_or_create_demo_sfc(customer: str) -> str:
    # SFC không có field remarks/free-text để đánh dấu nguồn seed — dò idempotency
    # bằng: đã tồn tại BẤT KỲ SFC nào cho đúng KH demo này (1 KH demo chỉ nên có
    # 1 SFC demo, tạo bằng script này duy nhất).
    existing = frappe.db.get_value(
        "SC Sales Framework Contract", {"customer": customer}, "name",
        order_by="creation asc",
    )
    if existing:
        return existing

    sfc = frappe.new_doc("SC Sales Framework Contract")
    sfc.customer = customer
    sfc.valid_from = today()
    sfc.valid_to = add_days(today(), 365)

    for item_code, qty, price in DEMO_SFC_ITEMS:
        if not frappe.db.exists("SC Item", item_code):
            continue
        uom = frappe.db.get_value("SC Item", item_code, "uom")
        sfc.append("items", {
            "item": item_code, "uom": uom,
            "contract_qty": flt(qty), "unit_price": flt(price),
        })

    if not sfc.items:
        frappe.throw(
            "seed_sales_demo: không tìm thấy item mẫu nào trong DEMO_SFC_ITEMS — "
            "chạy supplycore.setup.seed_master_data.run trước."
        )

    sfc.flags.ignore_permissions = True
    sfc.insert()
    sfc.submit()
    return sfc.name


def run() -> dict:
    """Tạo demo KH phân phối + SFC submitted (Hiệu lực). Idempotent.

    Returns: {customer, sfc, created: bool}
    """
    already_had_customer = bool(
        frappe.db.get_value("SC Customer", {"tax_code": DEMO_CUSTOMER_TAX_CODE}, "name")
    )
    customer = _get_or_create_customer()
    already_had_sfc = bool(frappe.db.get_value(
        "SC Sales Framework Contract", {"customer": customer}, "name",
    ))
    sfc = _get_or_create_demo_sfc(customer)
    frappe.db.commit()
    return {
        "customer": customer,
        "sfc": sfc,
        "customer_created": not already_had_customer,
        "sfc_created": not already_had_sfc,
    }
