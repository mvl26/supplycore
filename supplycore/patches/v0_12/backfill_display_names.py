"""GĐ MVL — rà soát list view: thêm field TÊN (fetch_from) cho các chứng từ còn
thiếu để bảng hiển thị tên nghiệp vụ thay vì mã. Patch này:
  1. reload_doc để tạo cột mới trong DB.
  2. Backfill tên cho bản ghi cũ bằng 1 UPDATE...JOIN mỗi doctype (không N+1).

Idempotent (chỉ backfill dòng còn trống). Rollback: xoá cột (thường không cần).
"""

import frappe

# (module, doctype_dir, doctype, name_field, link_field, link_doctype, link_name_field)
JOBS = [
    ("m7_sales", "sc_sales_order",       "SC Sales Order",       "customer_name", "customer", "SC Customer", "customer_name"),
    ("m7_sales", "sc_delivery_note",     "SC Delivery Note",     "customer_name", "customer", "SC Customer", "customer_name"),
    ("m7_sales", "sc_sales_invoice",     "SC Sales Invoice",     "customer_name", "customer", "SC Customer", "customer_name"),
    ("m7_sales", "sc_acceptance_record", "SC Acceptance Record", "customer_name", "customer", "SC Customer", "customer_name"),
    ("m7_sales", "sc_sales_receipt",     "SC Sales Receipt",     "customer_name", "customer", "SC Customer", "customer_name"),
    ("supplycore", "sc_quality_inspection", "SC Quality Inspection", "supplier_name", "supplier", "SC Supplier", "supplier_name"),
    ("supplycore", "sc_stock_ledger_entry",    "SC Stock Ledger Entry",    "item_name", "item", "SC Item", "item_name"),
    ("m10_traceability", "sc_recall_notice",        "SC Recall Notice",        "item_name", "item", "SC Item", "item_name"),
    ("m10_traceability", "sc_investigation_report", "SC Investigation Report", "item_name", "item", "SC Item", "item_name"),
]


def execute():
    for module, ddir, dt, namef, linkf, ldt, lnamef in JOBS:
        frappe.reload_doc(module, "doctype", ddir)
        n = frappe.db.sql(f"""
            UPDATE `tab{dt}` t
            JOIN `tab{ldt}` s ON s.name = t.`{linkf}`
            SET t.`{namef}` = s.`{lnamef}`
            WHERE (t.`{namef}` IS NULL OR t.`{namef}` = '')
              AND t.`{linkf}` IS NOT NULL AND t.`{linkf}` != ''
        """)
        cnt = frappe.db.sql(f"SELECT COUNT(*) FROM `tab{dt}` WHERE `{namef}` IS NOT NULL AND `{namef}` != ''")[0][0]
        print(f"  ✓ {dt}.{namef}: backfilled (rows có tên = {cnt})")
    frappe.db.commit()
