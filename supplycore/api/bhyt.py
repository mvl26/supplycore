"""BHYT API — supplycore.api.bhyt.* (M7).

Endpoint canonical theo Phase 2 API §4.2:
  POST /api/method/supplycore.api.bhyt.calculate_cost
"""

import frappe
from frappe import _
from frappe.utils import flt, getdate, today


@frappe.whitelist()
def get_active_config(item_code: str, on_date: str = None) -> dict:
    """Tìm BHYT Code Config hiệu lực cho item tại ngày on_date.

    Lookup priority:
        1. Config có item = X (specific)
        2. Config có item_group = item.item_group (group-level)
        3. Fallback SC Item.has_bhyt + bhyt_code/group/payment_rate

    Returns dict hoặc None.
    """
    on_date = on_date or today()
    # 1. Item-specific (priority cao nhất)
    cfg = frappe.db.sql("""
        SELECT name, bhyt_code, bhyt_name, bhyt_group, payment_rate, ceiling_price
        FROM `tabSC BHYT Code Config`
        WHERE item = %(item)s
          AND is_active = 1
          AND effective_from <= %(d)s
          AND (effective_to IS NULL OR effective_to >= %(d)s)
        ORDER BY effective_from DESC LIMIT 1
    """, {"item": item_code, "d": on_date}, as_dict=True)

    # 2. Group-level
    if not cfg:
        item_group = frappe.db.get_value("SC Item", item_code, "item_group")
        if item_group:
            cfg = frappe.db.sql("""
                SELECT name, bhyt_code, bhyt_name, bhyt_group, payment_rate, ceiling_price
                FROM `tabSC BHYT Code Config`
                WHERE item_group = %(g)s
                  AND (item IS NULL OR item = '')
                  AND is_active = 1
                  AND effective_from <= %(d)s
                  AND (effective_to IS NULL OR effective_to >= %(d)s)
                ORDER BY effective_from DESC LIMIT 1
            """, {"g": item_group, "d": on_date}, as_dict=True)

    if cfg:
        return cfg[0]

    # 3. Fallback từ SC Item field
    item = frappe.db.get_value("SC Item", item_code,
                                ["has_bhyt", "bhyt_code", "bhyt_group", "bhyt_payment_rate"],
                                as_dict=True)
    if item and item.has_bhyt:
        return {
            "name": None,
            "bhyt_code": item.bhyt_code,
            "bhyt_name": item.bhyt_code,
            "bhyt_group": item.bhyt_group,
            "payment_rate": flt(item.bhyt_payment_rate or 80),
            "ceiling_price": None,
        }

    return None


@frappe.whitelist()
def calculate_cost(items, bhyt_card: str = None, patient: str = None) -> dict:
    """Tính chi phí BHYT cho list items.

    items: list[{item_code, qty, unit_cost, uom?}]
    Trả: {items: [...], total_cost, bhyt_covered, patient_pays, ceiling_overage}
    """
    if isinstance(items, str):
        import json
        items = json.loads(items)

    # Lấy patient BHYT rate nếu có
    patient_rate = None
    if patient and frappe.db.exists("SC Patient", patient):
        patient_rate = frappe.db.get_value("SC Patient", patient, "bhyt_payment_rate")

    rows = []
    total_cost = total_bhyt = total_pay = total_overage = 0
    for it in items:
        qty = flt(it.get("qty"))
        unit_cost = flt(it.get("unit_cost"))
        cost = qty * unit_cost

        cfg = get_active_config(it.get("item_code"))
        bhyt_amount = 0
        ceiling_overage = 0
        bhyt_code = bhyt_group = None
        rate = 0

        if cfg:
            bhyt_code = cfg.get("bhyt_code")
            bhyt_group = cfg.get("bhyt_group")
            rate = flt(cfg.get("payment_rate") or 0)
            # Patient BHYT rate có thể override (vd 95%, 100%) nếu thấp hơn rate config
            if patient_rate is not None:
                rate = min(rate, flt(patient_rate))
            ceiling = flt(cfg.get("ceiling_price")) if cfg.get("ceiling_price") else None
            cap_unit = unit_cost
            if ceiling and unit_cost > ceiling:
                cap_unit = ceiling
                ceiling_overage = qty * (unit_cost - ceiling)
            bhyt_eligible = qty * cap_unit
            bhyt_amount = bhyt_eligible * rate / 100.0

        patient_pays = cost - bhyt_amount

        rows.append({
            "item_code":      it.get("item_code"),
            "qty":            qty,
            "unit_cost":      unit_cost,
            "total_cost":     cost,
            "bhyt_code":      bhyt_code,
            "bhyt_group":     bhyt_group,
            "bhyt_rate":      rate,
            "ceiling_price":  cfg.get("ceiling_price") if cfg else None,
            "bhyt_amount":    round(bhyt_amount, 2),
            "ceiling_overage": round(ceiling_overage, 2),
            "patient_pays":   round(patient_pays, 2),
        })
        total_cost += cost
        total_bhyt += bhyt_amount
        total_pay += patient_pays
        total_overage += ceiling_overage

    return {
        "items":          rows,
        "total_cost":     round(total_cost, 2),
        "bhyt_covered":   round(total_bhyt, 2),
        "patient_pays":   round(total_pay, 2),
        "ceiling_overage": round(total_overage, 2),
    }


# ----------------------------------------------------------------------
# UC-23 — BHYT Code Config management helpers
# ----------------------------------------------------------------------

@frappe.whitelist()
def list_bhyt_configs_for_item(item_code: str) -> dict:
    """UC-23 step 3: list tất cả configs (active + expired) của item.

    Bao gồm:
      - Configs cụ thể (item=X)
      - Configs theo item_group của item

    Returns: {item, item_group, count, configs: [...]}
    """
    item_group = frappe.db.get_value("SC Item", item_code, "item_group")
    rows = frappe.db.sql("""
        SELECT name, bhyt_code, bhyt_name, bhyt_group,
               payment_rate, ceiling_price,
               item, item_group, is_active,
               effective_from, effective_to,
               legal_basis, modified
        FROM `tabSC BHYT Code Config`
        WHERE item = %(item)s
           OR (
               (item IS NULL OR item = '')
               AND item_group = %(ig)s
           )
        ORDER BY effective_from DESC, modified DESC
    """, {"item": item_code, "ig": item_group}, as_dict=True)
    return {
        "item": item_code,
        "item_group": item_group,
        "count": len(rows),
        "configs": rows,
    }


@frappe.whitelist()
def get_bhyt_history(item_code: str) -> dict:
    """UC-23 step 5: alias cho list_bhyt_configs_for_item (audit view)."""
    return list_bhyt_configs_for_item(item_code)
