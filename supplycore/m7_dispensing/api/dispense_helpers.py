"""UC-20 helpers: stock availability check + alternative suggestion."""

import frappe
from frappe.utils import flt


@frappe.whitelist()
def check_stock_availability(item: str, qty: float, warehouse: str) -> dict:
    """UC-20 luồng 3a: check stock available + suggest alternatives cùng item_group.

    Returns:
      {
        item, warehouse, requested_qty, available_qty,
        in_stock: bool, shortfall: float,
        alternatives: [{item, item_name, available_qty}, ...]
      }
    """
    qty = flt(qty)
    available = flt(frappe.db.sql("""
        SELECT COALESCE(SUM(qty_change), 0)
        FROM `tabSC Stock Ledger Entry`
        WHERE item = %s AND warehouse = %s AND is_cancelled = 0
    """, (item, warehouse))[0][0])

    in_stock = available >= qty
    alternatives = []
    if not in_stock:
        item_group = frappe.db.get_value("SC Item", item, "item_group")
        if item_group:
            alternatives = frappe.db.sql("""
                SELECT i.name AS item, i.item_name,
                       COALESCE(SUM(sle.qty_change), 0) AS available_qty
                FROM `tabSC Item` i
                LEFT JOIN `tabSC Stock Ledger Entry` sle
                    ON sle.item = i.name AND sle.warehouse = %(wh)s AND sle.is_cancelled = 0
                WHERE i.disabled = 0
                  AND i.item_group = %(ig)s
                  AND i.name != %(item)s
                GROUP BY i.name
                HAVING available_qty > 0
                ORDER BY available_qty DESC LIMIT 5
            """, {"wh": warehouse, "ig": item_group, "item": item}, as_dict=True)

    return {
        "item": item,
        "warehouse": warehouse,
        "requested_qty": qty,
        "available_qty": available,
        "in_stock": in_stock,
        "shortfall": max(0.0, qty - available),
        "alternatives": alternatives,
    }
