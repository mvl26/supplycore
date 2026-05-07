"""Dashboard config cho Release Order — link ngược sang PO + tham chiếu HĐK."""

from frappe import _


def get_data():
    return {
        "fieldname": "release_order",
        "non_standard_fieldnames": {
            "Purchase Order": "sc_release_order",
        },
        "transactions": [
            {
                "label": _("Đặt hàng phát sinh"),
                "items": ["Purchase Order"],
            },
        ],
    }
