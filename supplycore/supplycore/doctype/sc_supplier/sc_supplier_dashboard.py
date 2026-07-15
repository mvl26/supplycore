"""Frappe dashboard_data — Connections panel cho SC Supplier."""

from frappe import _


def get_data():
    return {
        "fieldname": "supplier",
        "non_standard_fieldnames": {
            "Framework Contract": "supplier",
        },
        "transactions": [
            {"label": _("Hợp đồng & Đặt hàng"),
             "items": ["Framework Contract", "Release Order", "SC Purchase Order"]},
            {"label": _("Nhận hàng & QC"),
             "items": ["SC Purchase Receipt"]},
            {"label": _("Tồn kho theo lô"),
             "items": ["SC Batch"]},
            {"label": _("Kế toán"),
             "items": ["SC Purchase Invoice", "SC Payment Entry"]},
            {"label": _("Truy xuất"),
             "items": ["SC Recall Notice"]},
        ],
    }
