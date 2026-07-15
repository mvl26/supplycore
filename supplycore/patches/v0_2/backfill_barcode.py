"""Patch: backfill barcode cho SC Batch + Bin Location đã tồn tại.

Field barcode mới thêm — các lô/vị trí tạo trước đó có barcode NULL.
Set barcode = batch_id / bin_code để mọi bản ghi đều có barcode tra cứu.
"""

import frappe


def execute():
    # Đảm bảo column đã tồn tại (phòng trường hợp schema sync chưa add kịp)
    if not frappe.db.has_column("SC Batch", "barcode"):
        frappe.reload_doctype("SC Batch", force=True)
    if not frappe.db.has_column("Bin Location", "barcode"):
        frappe.reload_doctype("Bin Location", force=True)

    frappe.db.sql("""
        UPDATE `tabSC Batch`
        SET barcode = batch_id
        WHERE (barcode IS NULL OR barcode = '') AND batch_id IS NOT NULL
    """)
    frappe.db.sql("""
        UPDATE `tabBin Location`
        SET barcode = bin_code
        WHERE (barcode IS NULL OR barcode = '') AND bin_code IS NOT NULL
    """)
    frappe.db.commit()
