"""Patch: thêm Custom Field cho Material Request phục vụ M2."""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    custom_fields = {
        "Material Request": [
            {
                "fieldname": "sc_supplycore_section",
                "label": "SupplyCore",
                "fieldtype": "Section Break",
                "insert_after": "schedule_date",
                "collapsible": 1,
                "module": "M2 Planning",
            },
            {
                "fieldname": "sc_procurement_plan",
                "label": "Procurement Plan",
                "fieldtype": "Link",
                "options": "Procurement Plan",
                "insert_after": "sc_supplycore_section",
                "in_standard_filter": 1,
                "module": "M2 Planning",
                "description": "MR sinh từ Procurement Plan SupplyCore",
            },
            {
                "fieldname": "sc_auto_generated",
                "label": "Auto-generated",
                "fieldtype": "Check",
                "default": "0",
                "insert_after": "sc_procurement_plan",
                "module": "M2 Planning",
            },
        ],
    }
    create_custom_fields(custom_fields, update=True)
    frappe.db.commit()
