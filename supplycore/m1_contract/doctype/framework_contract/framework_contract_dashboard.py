"""Dashboard config — Connections panel ở cuối form Framework Contract.

Hiện count + click-through filter cho RO và PO liên kết.
"""

from frappe import _


def get_data():
    return {
        "fieldname": "framework_contract",
        "non_standard_fieldnames": {
            "Purchase Order": "sc_framework_contract",
        },
        "transactions": [
            {
                "label": _("Lệnh gọi hàng"),
                "items": ["Release Order"],
            },
            {
                "label": _("Đặt hàng"),
                "items": ["Purchase Order"],
            },
        ],
    }
