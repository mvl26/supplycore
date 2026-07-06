"""Smoke test M11 — Executive Dashboard KPI + Alert Rule scan + SC Alert workflow."""

import frappe
from frappe.utils import today, add_days
from supplycore.api import kpi as kpi_api
from supplycore.m11_dashboard import tasks as m11_tasks


def run():
    if not frappe.db.exists("SC Item", "VTTH-MASK-3PLY"):
        return {"status": "skip", "reason": "Cần seed master data"}

    results = []

    # 1. Test get_executive_dashboard
    dash = kpi_api.get_executive_dashboard("this_month")
    kpis = dash["kpis"]
    results.append({"step": "Executive dashboard KPIs",
                    "stock_value": kpis["stock_value"],
                    "monthly_cost": kpis["monthly_cost"],
                    "ap_outstanding": kpis["ap_outstanding"],
                    "pending_pos": kpis["pending_pos"],
                    "expiring_soon": kpis["expiring_soon"],
                    "low_stock_items": kpis["low_stock_items"],
                    "top_items_count": len(dash["top_items"]),
                    "open_alerts_total": dash["open_alerts_total"]})

    # 2. Test get_warehouse_dashboard
    wh_dash = kpi_api.get_warehouse_dashboard("Kho Vật tư tiêu hao")
    results.append({"step": "Warehouse dashboard",
                    "stock_qty_total": wh_dash["stock_qty_total"],
                    "expiring_batches": wh_dash["expiring_batches"],
                    "pending_tr": wh_dash["pending_transfer_requests"]})

    # 3. Cleanup test rules + alerts
    for n in frappe.get_all("SC Alert", filters={"alert_rule": ["like", "SC-AR-M11SMK-%"]}):
        frappe.delete_doc("SC Alert", n.name, force=True, ignore_permissions=True)
    for n in frappe.get_all("SC Alert Rule", filters={"title": ["like", "M11-SMOKE-%"]}):
        # Xóa alert liên quan trước
        for a in frappe.get_all("SC Alert", filters={"alert_rule": n.name}):
            frappe.delete_doc("SC Alert", a.name, force=True, ignore_permissions=True)
        frappe.delete_doc("SC Alert Rule", n.name, force=True, ignore_permissions=True)
    frappe.db.commit()

    # 4. Tạo Alert Rule: expiring_batch (sẽ match nhiều batch test smoke trước)
    rule = frappe.new_doc("SC Alert Rule")
    rule.title = "M11-SMOKE-expiring-30"
    rule.alert_type = "expiring_batch"
    rule.severity = "Warning"
    rule.threshold_value = 30
    rule.threshold_unit = "days"
    rule.threshold_operator = "<="
    rule.enabled = 1
    rule.frequency = "Daily"
    rule.recipient_roles = "SupplyCore Manager,SupplyCore Storekeeper"
    rule.flags.ignore_permissions = True
    rule.insert()
    results.append({"step": "Alert Rule created", "rule": rule.name,
                    "type": rule.alert_type, "threshold": float(rule.threshold_value)})

    # 5. Tạo Alert Rule: contract_expiring
    rule2 = frappe.new_doc("SC Alert Rule")
    rule2.title = "M11-SMOKE-contract-90"
    rule2.alert_type = "contract_expiring"
    rule2.severity = "Critical"
    rule2.threshold_value = 90
    rule2.enabled = 1
    rule2.flags.ignore_permissions = True
    rule2.insert()

    # 6. Tạo batch sắp hết hạn để rule chắc chắn match
    from frappe.utils import random_string
    test_batch = frappe.new_doc("SC Batch")
    test_batch.batch_id = f"M11SMK-EXPIRE-{random_string(4)}"
    test_batch.item = "VTTH-MASK-3PLY"
    test_batch.expiry_date = add_days(today(), 15)  # 15 ngày → match rule 30
    test_batch.manufacturing_date = today()
    test_batch.flags.ignore_permissions = True
    test_batch.insert()
    item_uom = frappe.db.get_value("SC Item", "VTTH-MASK-3PLY", "uom")
    se_test = frappe.new_doc("SC Stock Entry")
    se_test.entry_type = "Material Receipt"
    se_test.posting_date = today()
    se_test.to_warehouse = "Kho Vật tư tiêu hao"
    se_test.append("items", {"item": "VTTH-MASK-3PLY", "qty": 50, "uom": item_uom,
                              "batch": test_batch.name, "valuation_rate": 1500})
    se_test.flags.ignore_permissions = True
    se_test.insert(); se_test.submit()
    results.append({"step": "Test batch", "batch": test_batch.name, "qty": 50})

    # 7. Run scan_alerts
    total_created = m11_tasks.scan_alerts()
    results.append({"step": "scan_alerts run", "total_created": total_created})

    # 8. Verify alerts created
    alerts_for_rule = frappe.db.count("SC Alert",
        {"alert_rule": rule.name, "resolved": 0})
    results.append({"step": "Alerts for expiring_batch rule",
                    "count": alerts_for_rule})
    assert alerts_for_rule >= 1, f"Phải có ≥1 alert cho rule expiring_batch"

    # 9. Test alert workflow: resolve
    open_alert = frappe.db.get_value("SC Alert",
        {"alert_rule": rule.name, "resolved": 0}, "name")
    if open_alert:
        a = frappe.get_doc("SC Alert", open_alert)
        a.resolved = 1
        a.resolution_action = "Acted Upon"
        a.save()
        a.reload()
        results.append({"step": "Alert resolved", "alert": a.name,
                        "resolved_by": a.resolved_by,
                        "resolved_at": str(a.resolved_at) if a.resolved_at else None})

    # 10. Run scan_alerts lần 2 → dedup, không tạo alert mới cho batch đã alert
    total_2nd = m11_tasks.scan_alerts()
    results.append({"step": "scan_alerts re-run (dedup)", "total_created": total_2nd})

    # 11. Cleanup test batch
    frappe.db.set_value("SC Batch", test_batch.name, "disabled", 1)
    frappe.db.commit()

    return {"status": "ok", "results": results}
