"""Patch: Custom Fields cho Item + Stock Entry Detail (M4 WMS)."""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    custom_fields = {
        "Item": [
            {
                "fieldname": "sc_wms_section",
                "label": "SupplyCore — WMS",
                "fieldtype": "Section Break",
                "insert_after": "stock_uom",
                "collapsible": 1,
                "module": "M4 WMS",
            },
            {
                "fieldname": "sc_default_bin_location",
                "label": "Bin mặc định",
                "fieldtype": "Link",
                "options": "Bin Location",
                "insert_after": "sc_wms_section",
                "module": "M4 WMS",
                "description": "Bin gợi ý khi nhập kho — dùng cho Putaway suggestion",
            },
        ],
        "Stock Entry Detail": [
            {
                "fieldname": "sc_source_bin",
                "label": "Source Bin",
                "fieldtype": "Link",
                "options": "Bin Location",
                "insert_after": "s_warehouse",
                "module": "M4 WMS",
            },
            {
                "fieldname": "sc_target_bin",
                "label": "Target Bin",
                "fieldtype": "Link",
                "options": "Bin Location",
                "insert_after": "t_warehouse",
                "module": "M4 WMS",
            },
        ],
        "Stock Entry": [
            {
                "fieldname": "sc_pda_session_id",
                "label": "PDA Session ID",
                "fieldtype": "Data",
                "insert_after": "remarks",
                "module": "M4 WMS",
                "read_only": 1,
                "description": "Session quét barcode trên PDA (nếu có)",
            },
        ],
    }
    create_custom_fields(custom_fields, update=True)
    frappe.db.commit()
