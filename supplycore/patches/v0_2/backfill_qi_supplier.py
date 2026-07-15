"""Patch: backfill supplier cho SC Quality Inspection đã tồn tại.

Field `supplier` mới thêm vào QI (UC-10) — các QI tạo trước đó có supplier NULL.
Lấy supplier từ Phiếu nhập (purchase_receipt) tương ứng để phần kiểm tra QC
hiển thị đúng nhà cung cấp.
"""

import frappe


def execute():
    # Đảm bảo column đã tồn tại (phòng schema sync chưa add kịp)
    if not frappe.db.has_column("SC Quality Inspection", "supplier"):
        frappe.reload_doctype("SC Quality Inspection", force=True)

    frappe.db.sql("""
        UPDATE `tabSC Quality Inspection` qi
        JOIN `tabSC Purchase Receipt` pr ON pr.name = qi.purchase_receipt
        SET qi.supplier = pr.supplier
        WHERE COALESCE(qi.supplier, '') = '' AND pr.supplier IS NOT NULL
    """)
    frappe.db.commit()
