"""Connections panel cho Bin Location — link sang Stock Entry."""

from frappe import _


def get_data():
    return {
        "fieldname": "bin_location",
        "non_standard_fieldnames": {
            "Stock Entry": "sc_target_bin",
        },
        "transactions": [
            {
                "label": _("Giao dịch kho"),
                "items": ["Stock Entry"],
            },
        ],
    }
