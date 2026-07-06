import frappe

# Các DocType nghiệp vụ bệnh viện bị loại khỏi bản MVL (0 bản ghi — an toàn drop).
HOSPITAL_DOCTYPES = [
    "SC Dispensing Request", "SC DR Item",
    "SC Patient Dispensing", "SC PD Item",
    "SC Patient", "SC BHYT Code Config", "SC HIS Warehouse Map",
    # stub legacy (có thể không tồn tại như DocType — bỏ qua nếu thiếu)
    "BHYT Claim", "Dispensing Request", "Dispensing Request Item",
    "Patient Dispensing", "BHYT Config",
]

# Cột mồ côi còn sót lại trên các bảng KHÔNG bị xóa (doctype vẫn tồn tại)
# sau khi field tương ứng đã bị gỡ khỏi doctype JSON (GĐ1 gỡ nghiệp vụ bệnh viện).
STALE_COLUMNS = {
    "SC Item": [
        "his_code", "has_bhyt", "bhyt_code", "bhyt_group", "bhyt_payment_rate",
    ],
    "SC Recall Affected Item": [
        "qty_dispensed",  # đã đổi tên thành qty_issued (Task 1)
        "patient",  # gỡ nghiệp vụ bệnh nhân (Task 6 phần A)
    ],
}


def execute():
    for dt in HOSPITAL_DOCTYPES:
        if frappe.db.exists("DocType", dt):
            try:
                frappe.delete_doc("DocType", dt, force=True, ignore_missing=True)
                frappe.db.commit()
            except Exception:
                frappe.log_error(f"remove_hospital_domain: không xóa được {dt}",
                                 "MVL GĐ1")
        # dọn bảng mồ côi nếu còn
        # LƯU Ý: frappe.db.table_exists() nhận DOCTYPE (không phải tên bảng
        # đã có tiền tố "tab" — hàm tự thêm "tab" bên trong).
        table = f"tab{dt}"
        if frappe.db.table_exists(dt, cached=False):
            frappe.db.sql_ddl(f"DROP TABLE IF EXISTS `{table}`")

    # Dọn cột mồ côi trên các bảng vẫn còn tồn tại (không bị xóa ở trên).
    for doctype, columns in STALE_COLUMNS.items():
        table = f"tab{doctype}"
        if not frappe.db.table_exists(doctype, cached=False):
            continue
        existing_columns = set(frappe.db.get_table_columns(doctype))
        for column in columns:
            if column in existing_columns:
                try:
                    frappe.db.sql_ddl(
                        f"ALTER TABLE `{table}` DROP COLUMN `{column}`"
                    )
                except Exception:
                    frappe.log_error(
                        f"remove_hospital_domain: không xóa được cột {column} "
                        f"trên {table}",
                        "MVL GĐ1",
                    )
    frappe.db.commit()
