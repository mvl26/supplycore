"""Patch: Custom Field cho Purchase Receipt + Quality Inspection (M3)."""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    custom_fields = {
        "Purchase Receipt": [
            {
                "fieldname": "sc_qc_section",
                "label": "SupplyCore — QC",
                "fieldtype": "Section Break",
                "insert_after": "is_return",
                "collapsible": 1,
                "module": "M3 Receiving",
            },
            {
                "fieldname": "sc_qc_required",
                "label": "Bắt buộc QC",
                "fieldtype": "Check",
                "default": "1",
                "insert_after": "sc_qc_section",
                "module": "M3 Receiving",
            },
            {
                "fieldname": "sc_qc_status",
                "label": "Trạng thái QC tổng",
                "fieldtype": "Select",
                "options": "\nPending\nPass\nFail\nPartial Pass",
                "default": "Pending",
                "insert_after": "sc_qc_required",
                "in_list_view": 1,
                "in_standard_filter": 1,
                "read_only": 1,
                "module": "M3 Receiving",
            },
            {
                "fieldname": "sc_backorder_for",
                "label": "Backorder cho PR",
                "fieldtype": "Link",
                "options": "Purchase Receipt",
                "insert_after": "sc_qc_status",
                "read_only": 1,
                "module": "M3 Receiving",
                "description": "PR này là backorder của 1 PR trước nhận thiếu",
            },
        ],
        "Quality Inspection": [
            {
                "fieldname": "sc_supplycore_section",
                "label": "SupplyCore — Checklist",
                "fieldtype": "Section Break",
                "insert_after": "readings",
                "collapsible": 1,
                "module": "M3 Receiving",
            },
            {
                "fieldname": "sc_checklist_template",
                "label": "Mẫu checklist",
                "fieldtype": "Link",
                "options": "QC Checklist Template",
                "insert_after": "sc_supplycore_section",
                "module": "M3 Receiving",
                "description": "Auto-fill khi tạo từ Purchase Receipt",
            },
            {
                "fieldname": "sc_action_taken",
                "label": "Hành động xử lý",
                "fieldtype": "Select",
                "options": "\nPending\nAccept\nConditional Accept\nReturn to Supplier",
                "default": "Pending",
                "insert_after": "sc_checklist_template",
                "in_list_view": 1,
                "in_standard_filter": 1,
                "module": "M3 Receiving",
            },
            {
                "fieldname": "sc_failure_reason",
                "label": "Lý do không đạt",
                "fieldtype": "Small Text",
                "insert_after": "sc_action_taken",
                "depends_on": "eval:doc.status=='Rejected' || doc.sc_action_taken=='Return to Supplier'",
                "module": "M3 Receiving",
            },
        ],
    }
    create_custom_fields(custom_fields, update=True)
    frappe.db.commit()
