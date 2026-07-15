"""Smoke test M2 — SC Stock Entry seed + Procurement Plan auto-load + SC MR."""

import frappe
from frappe.utils import today, add_days, add_months, random_string


def run():
    item_code = "VTTH-GLOVE-S"
    warehouse = "Kho Vật tư tiêu hao"
    if not (frappe.db.exists("SC Item", item_code) and frappe.db.exists("SC Warehouse", warehouse)):
        return {"status": "skip", "reason": "Cần seed master data"}

    item_uom = frappe.db.get_value("SC Item", item_code, "uom")
    has_batch = frappe.db.get_value("SC Item", item_code, "has_batch_no")
    results = []

    for p in frappe.get_all("Procurement Plan", filters={"remarks": "M2-SMOKE"},
                             fields=["name", "material_request"]):
        if p.material_request and frappe.db.exists("SC Material Request", p.material_request):
            frappe.db.set_value("SC Material Request", p.material_request, "procurement_plan", None)
            frappe.db.set_value("Procurement Plan", p.name, "material_request", None)
            mr = frappe.get_doc("SC Material Request", p.material_request)
            if mr.docstatus == 1: mr.cancel()
            frappe.delete_doc("SC Material Request", mr.name, force=True, ignore_permissions=True)
        d = frappe.get_doc("Procurement Plan", p.name)
        if d.docstatus == 1: d.cancel()
        frappe.delete_doc("Procurement Plan", p.name, force=True, ignore_permissions=True)
    frappe.db.commit()

    # Tạo batch nếu item has_batch
    batch_name = None
    if has_batch:
        batch = frappe.new_doc("SC Batch")
        batch.batch_id = f"{item_code}-M2SMK-{random_string(5)}"
        batch.item = item_code
        batch.expiry_date = add_days(today(), 180)
        batch.manufacturing_date = today()
        batch.flags.ignore_permissions = True
        batch.insert()
        batch_name = batch.name

    se_in = frappe.new_doc("SC Stock Entry")
    se_in.entry_type = "Material Receipt"
    se_in.posting_date = add_months(today(), -2)
    se_in.to_warehouse = warehouse
    se_in.append("items", {"item": item_code, "qty": 200, "uom": item_uom,
                            "valuation_rate": 30000, "batch": batch_name})
    se_in.flags.ignore_permissions = True
    se_in.insert(); se_in.submit()

    se_out = frappe.new_doc("SC Stock Entry")
    se_out.entry_type = "Material Issue"
    se_out.posting_date = add_months(today(), -1)
    se_out.from_warehouse = warehouse
    se_out.append("items", {"item": item_code, "qty": 60, "uom": item_uom,
                             "valuation_rate": 30000, "batch": batch_name})
    se_out.flags.ignore_permissions = True
    se_out.insert(); se_out.submit()
    results.append({"step": "Setup stock", "in": se_in.name, "out": se_out.name, "batch": batch_name})

    plan = frappe.new_doc("Procurement Plan")
    plan.plan_date = today()
    plan.period_type = "Monthly"
    plan.from_date = today()
    plan.to_date = add_days(today(), 30)
    plan.warehouse = warehouse
    plan.consumption_lookback_months = 3
    plan.safety_stock_factor = 20
    plan.required_by = add_days(today(), 14)
    plan.remarks = "M2-SMOKE"
    plan.flags.ignore_permissions = True
    plan.insert()

    res = plan.auto_load_items()
    plan.reload()
    results.append({"step": "Auto-load", "items_loaded": res.get("items_loaded", 0),
                    "total_estimated": float(plan.total_estimated_cost or 0)})

    if not plan.items:
        plan.append("items", {
            "item_code": item_code, "uom": item_uom,
            "current_stock": 100, "avg_monthly_consumption": 60,
            "lead_time_days": 14, "safety_stock_qty": 12,
            "planned_qty": 100, "estimated_unit_cost": 30000,
        })
    # Bump planned_qty > 0 nếu auto_load suggest 0 (do current_stock đủ)
    for row in plan.items:
        if not row.planned_qty or row.planned_qty <= 0:
            row.planned_qty = 50
        if not row.estimated_unit_cost:
            row.estimated_unit_cost = 30000
    plan.save(ignore_permissions=True); plan.reload()
    results.append({"step": "Items prepared", "count": len(plan.items),
                    "total_qty": sum(float(r.planned_qty) for r in plan.items)})

    plan.submit(); plan.reload()
    mr_name = plan.make_material_request()
    plan.reload()
    mr = frappe.get_doc("SC Material Request", mr_name)
    results.append({"step": "MR", "mr": mr_name, "items": len(mr.items),
                    "total": float(mr.total_estimated_cost),
                    "auto_generated": bool(mr.auto_generated)})

    return {"status": "ok", "results": results}
