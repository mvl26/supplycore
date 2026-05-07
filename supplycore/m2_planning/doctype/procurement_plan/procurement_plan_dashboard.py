"""Connections panel cho Procurement Plan: link sang MR và downstream PO."""

from frappe import _


def get_data():
    return {
        "fieldname": "procurement_plan",
        "non_standard_fieldnames": {
            "Material Request": "sc_procurement_plan",
        },
        "transactions": [
            {
                "label": _("Yêu cầu vật tư"),
                "items": ["Material Request"],
            },
        ],
    }
