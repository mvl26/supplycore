"""UC-12 bin helpers: suggest_bin + get_alternative_bin."""

import frappe
from frappe import _
from frappe.utils import flt


@frappe.whitelist()
def suggest_bin(item: str, warehouse: str, qty: float = 0) -> dict:
    """UC-12: trả bin gợi ý theo precedence:
    1. Putaway Rule match (item, warehouse) — priority cao nhất
    2. SC Item.default_bin_location (cùng warehouse)
    3. Putaway Rule match (item_group, warehouse)
    4. Putaway Rule match (item_group, global = warehouse NULL)

    Mỗi bước check capacity còn nhận được qty hay không.
    """
    qty = flt(qty)

    # 1. Rule (item, warehouse)
    rule = frappe.db.sql("""
        SELECT target_bin FROM `tabPutaway Rule`
        WHERE enabled = 1 AND item = %s AND warehouse = %s
        ORDER BY priority DESC LIMIT 1
    """, (item, warehouse))
    if rule:
        bin_name = rule[0][0]
        if _bin_has_capacity(bin_name, qty):
            return {"bin": bin_name, "source": "rule_item_wh"}

    # 2. SC Item.default_bin_location
    default_bin = frappe.db.get_value("SC Item", item, "default_bin_location")
    if default_bin:
        b_wh = frappe.db.get_value("Bin Location", default_bin, "warehouse")
        if b_wh == warehouse and _bin_has_capacity(default_bin, qty):
            return {"bin": default_bin, "source": "item_default"}

    # 3+4. Item Group rules
    item_group = frappe.db.get_value("SC Item", item, "item_group")
    if item_group:
        rule = frappe.db.sql("""
            SELECT target_bin FROM `tabPutaway Rule`
            WHERE enabled = 1 AND item_group = %s AND warehouse = %s
            ORDER BY priority DESC LIMIT 1
        """, (item_group, warehouse))
        if rule:
            bin_name = rule[0][0]
            if _bin_has_capacity(bin_name, qty):
                return {"bin": bin_name, "source": "rule_group_wh"}

        rule = frappe.db.sql("""
            SELECT target_bin FROM `tabPutaway Rule`
            WHERE enabled = 1 AND item_group = %s
              AND (warehouse IS NULL OR warehouse = '')
            ORDER BY priority DESC LIMIT 1
        """, item_group)
        if rule:
            bin_name = rule[0][0]
            b_wh = frappe.db.get_value("Bin Location", bin_name, "warehouse")
            if b_wh == warehouse and _bin_has_capacity(bin_name, qty):
                return {"bin": bin_name, "source": "rule_group_global"}

    return {"bin": None, "source": "no_match"}


def _bin_has_capacity(bin_name: str, qty: float) -> bool:
    b = frappe.db.get_value("Bin Location", bin_name,
                              ["capacity_qty", "current_qty", "enabled"], as_dict=True)
    if not b or not b.enabled:
        return False
    if not b.capacity_qty:
        return True  # 0 = unlimited
    return (flt(b.current_qty) + flt(qty)) <= flt(b.capacity_qty)


@frappe.whitelist()
def get_alternative_bin(bin_name: str, qty: float = 0) -> dict:
    """UC-12 3a: bin đầy → tìm bin thay thế gần nhất (cùng warehouse, cùng zone)."""
    qty = flt(qty)
    b = frappe.db.get_value("Bin Location", bin_name,
                              ["warehouse", "zone", "aisle"], as_dict=True)
    if not b:
        frappe.throw(_("Bin {0} không tồn tại").format(bin_name))

    candidates = frappe.db.sql("""
        SELECT name, bin_code, zone, aisle, capacity_qty,
               COALESCE(current_qty, 0) AS current_qty
        FROM `tabBin Location`
        WHERE name != %(self_name)s
          AND warehouse = %(warehouse)s
          AND enabled = 1
          AND (capacity_qty = 0 OR capacity_qty IS NULL
               OR (COALESCE(current_qty, 0) + %(qty)s) <= capacity_qty)
        ORDER BY
          CASE WHEN zone = %(zone)s OR (zone IS NULL AND %(zone)s IS NULL) THEN 0 ELSE 1 END,
          CASE WHEN aisle = %(aisle)s OR (aisle IS NULL AND %(aisle)s IS NULL) THEN 0 ELSE 1 END,
          bin_code
        LIMIT 5
    """, {"self_name": bin_name, "warehouse": b.warehouse,
           "zone": b.zone, "aisle": b.aisle, "qty": qty}, as_dict=True)
    return {"alternatives": candidates}
