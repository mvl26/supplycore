"""UC-05: single source of truth for reorder thresholds.

Precedence per field: child row (SC Item Reorder) matching warehouse
with field > 0 → item-level field > 0 → 0.

Consumers: M11 _scan_low_stock, Procurement Plan auto_load_reorder_items.
"""

import frappe
from frappe.utils import flt

FIELDS = ("safety_stock", "reorder_level", "max_stock",
          "standard_order_qty", "lead_time_days")


def get_reorder_thresholds(item: str, warehouse: str = None) -> dict:
    """Return dict with FIELDS keys for given (item, warehouse).

    If warehouse=None → returns item-level only.
    Per-field fallback: row override field=0 → fallback item-level.
    lead_time_days never overrides per-warehouse (UC-05 decision 2).
    """
    item_doc = frappe.db.get_value(
        "SC Item", item,
        ["safety_stock", "reorder_level", "max_stock",
         "standard_order_qty", "lead_time_days"],
        as_dict=True,
    ) or {}
    result = {k: flt(item_doc.get(k) or 0) for k in FIELDS}

    if warehouse:
        row = frappe.db.get_value(
            "SC Item Reorder",
            {"parent": item, "parenttype": "SC Item", "warehouse": warehouse},
            ["safety_stock", "reorder_level", "max_stock", "standard_order_qty"],
            as_dict=True,
        )
        if row:
            for k in ("safety_stock", "reorder_level",
                      "max_stock", "standard_order_qty"):
                v = flt(row.get(k) or 0)
                if v > 0:
                    result[k] = v
    return result
