"""Patch: thêm Custom Field cho Supplier + Purchase Order phục vụ M1.

Tất cả field đều prefix `sc_` để tránh đụng độ với core ERPNext trong tương lai.
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    custom_fields = {
        "Supplier": [
            {
                "fieldname": "sc_supplycore_section",
                "label": "SupplyCore",
                "fieldtype": "Section Break",
                "insert_after": "supplier_group",
                "collapsible": 1,
                "module": "M1 Contract",
            },
            {
                "fieldname": "sc_ncc_type",
                "label": "Loại NCC",
                "fieldtype": "Select",
                "options": "\nNhà sản xuất\nNhà phân phối\nĐại lý\nKhác",
                "insert_after": "sc_supplycore_section",
                "module": "M1 Contract",
            },
            {
                "fieldname": "sc_blacklist_flag",
                "label": "Blacklist",
                "fieldtype": "Check",
                "default": "0",
                "insert_after": "sc_ncc_type",
                "description": "Đánh dấu NCC vào danh sách đen — block tạo PO mới",
                "module": "M1 Contract",
            },
            {
                "fieldname": "sc_rating",
                "label": "Điểm đánh giá NCC (0–5)",
                "fieldtype": "Float",
                "precision": "2",
                "insert_after": "sc_blacklist_flag",
                "read_only": 1,
                "description": "Tự động cập nhật từ lịch sử giao hàng/QC",
                "module": "M1 Contract",
            },
        ],
        "Purchase Order": [
            {
                "fieldname": "sc_supplycore_section",
                "label": "SupplyCore — Hợp đồng khung",
                "fieldtype": "Section Break",
                "insert_after": "supplier_address",
                "collapsible": 0,
                "module": "M1 Contract",
            },
            {
                "fieldname": "sc_framework_contract",
                "label": "Hợp đồng khung",
                "fieldtype": "Link",
                "options": "Framework Contract",
                "insert_after": "sc_supplycore_section",
                "in_standard_filter": 1,
                "module": "M1 Contract",
            },
            {
                "fieldname": "sc_release_order",
                "label": "Release Order",
                "fieldtype": "Link",
                "options": "Release Order",
                "insert_after": "sc_framework_contract",
                "in_standard_filter": 1,
                "module": "M1 Contract",
            },
        ],
    }
    create_custom_fields(custom_fields, update=True)
    frappe.db.commit()
