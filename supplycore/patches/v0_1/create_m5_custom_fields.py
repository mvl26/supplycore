"""Patch: Custom Fields cho Batch + Stock Entry Detail (M5 FEFO)."""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    custom_fields = {
        "Batch": [
            {
                "fieldname": "sc_fefo_section",
                "label": "SupplyCore — FEFO / Recall",
                "fieldtype": "Section Break",
                "insert_after": "expiry_date",
                "collapsible": 1,
                "module": "M5 FEFO",
            },
            {
                "fieldname": "sc_blocked",
                "label": "Bị block",
                "fieldtype": "Check",
                "default": "0",
                "insert_after": "sc_fefo_section",
                "in_list_view": 1,
                "in_standard_filter": 1,
                "module": "M5 FEFO",
                "description": "1 = Block xuất kho (recall, QC fail, etc.)",
            },
            {
                "fieldname": "sc_block_reason",
                "label": "Lý do block",
                "fieldtype": "Small Text",
                "insert_after": "sc_blocked",
                "depends_on": "sc_blocked",
                "module": "M5 FEFO",
            },
        ],
        "Stock Entry Detail": [
            {
                "fieldname": "sc_fefo_section",
                "label": "SupplyCore — FEFO Override",
                "fieldtype": "Section Break",
                "insert_after": "batch_no",
                "collapsible": 1,
                "module": "M5 FEFO",
            },
            {
                "fieldname": "sc_fefo_override",
                "label": "FEFO Override",
                "fieldtype": "Check",
                "default": "0",
                "insert_after": "sc_fefo_section",
                "module": "M5 FEFO",
                "description": "Tick để bỏ qua FEFO — yêu cầu ghi lý do + Manager approval",
            },
            {
                "fieldname": "sc_fefo_override_reason",
                "label": "Lý do override FEFO",
                "fieldtype": "Small Text",
                "insert_after": "sc_fefo_override",
                "depends_on": "sc_fefo_override",
                "module": "M5 FEFO",
            },
        ],
    }
    create_custom_fields(custom_fields, update=True)
    frappe.db.commit()
