"""Patch: xoá 4 role bệnh viện mồ côi khỏi DB (idempotent — chạy lại được).

Task 3 đã gỡ 4 role này khỏi install.py + hooks fixtures, nhưng Role record
tạo ra trước đó (qua v0_1.create_supplycore_roles hoặc thao tác thủ công)
vẫn còn tồn tại trong DB nếu site đã migrate trước khi Task 3 chạy. Patch
này dọn nốt — không phụ thuộc site nào đã/chưa có role.
"""

import frappe

HOSPITAL_ROLES = ["BHYT Officer", "Pharmacy Officer", "Department Requester", "SupplyCore Ward Staff"]


def execute():
    for role in HOSPITAL_ROLES:
        if frappe.db.exists("Role", role):
            frappe.delete_doc("Role", role, force=True, ignore_missing=True)
            frappe.db.commit()
