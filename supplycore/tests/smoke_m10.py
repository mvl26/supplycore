"""Smoke test M10 — SC Recall Notice + batch trace + audit trail."""

import frappe
from frappe.utils import today, add_days, random_string, flt
from supplycore.api import trace as trace_api


def run():
    item_code = "VTTH-MASK-3PLY"
    warehouse = "Kho Vật tư tiêu hao"
    if not (frappe.db.exists("SC Item", item_code) and frappe.db.exists("SC Warehouse", warehouse)):
        return {"status": "skip", "reason": "Cần seed master data"}

    item_uom = frappe.db.get_value("SC Item", item_code, "uom")
    results = []

    # Cleanup
    for n in frappe.get_all("SC Recall Notice", filters={"remarks": "M10-SMOKE"}, fields=["name", "batch_no"]):
        if n.batch_no:
            frappe.db.set_value("SC Batch", n.batch_no, "blocked", 0)
        d = frappe.get_doc("SC Recall Notice", n.name)
        if d.docstatus == 1: d.cancel()
        frappe.delete_doc("SC Recall Notice", n.name, force=True, ignore_permissions=True)
    frappe.db.commit()

    # 1. Tạo batch + receipt
    batch = frappe.new_doc("SC Batch")
    batch.batch_id = f"{item_code}-M10-{random_string(5)}"
    batch.item = item_code
    batch.expiry_date = add_days(today(), 365)
    batch.manufacturing_date = today()
    batch.flags.ignore_permissions = True
    batch.insert()

    se_in = frappe.new_doc("SC Stock Entry")
    se_in.entry_type = "Material Receipt"
    se_in.posting_date = today()
    se_in.to_warehouse = warehouse
    se_in.append("items", {"item": item_code, "qty": 100, "uom": item_uom,
                            "batch": batch.name, "valuation_rate": 1500})
    se_in.flags.ignore_permissions = True
    se_in.insert(); se_in.submit()
    results.append({"step": "Setup", "batch": batch.name, "receipt": se_in.name})

    # 2. Test API get_batch_trace
    trace = trace_api.get_batch_trace(batch.name)
    results.append({"step": "Batch trace API", "movements": trace["total_movements"],
                    "remaining": trace["remaining_qty"], "blocked": trace["blocked"],
                    "warehouses": len(trace["current_qty_per_warehouse"])})
    assert trace["remaining_qty"] == 100
    assert not trace["blocked"]

    # 3. Tạo SC Recall Notice
    rcl = frappe.new_doc("SC Recall Notice")
    rcl.recall_date = today()
    rcl.recall_type = "Voluntary"
    rcl.severity = "Class II (High)"
    rcl.item = item_code
    rcl.batch_no = batch.name
    rcl.recall_reason = "Smoke test recall — phát hiện lỗi đóng gói"
    rcl.regulatory_reference = "CV BYT số TEST-2026"
    rcl.remarks = "M10-SMOKE"
    rcl.flags.ignore_permissions = True
    rcl.insert()
    results.append({"step": "Recall created", "rcl": rcl.name, "status": rcl.status})

    # 4. Populate affected items
    res = rcl.populate_affected_items()
    rcl.reload()
    results.append({"step": "Populate affected", "loaded": res["affected_items_loaded"],
                    "total_affected_qty": float(rcl.total_affected_qty)})
    assert res["affected_items_loaded"] >= 1

    # 5. Submit Recall → batch blocked
    rcl.submit()
    rcl.reload()
    batch_after = frappe.db.get_value("SC Batch", batch.name,
                                        ["blocked", "block_reason"], as_dict=True)
    results.append({"step": "Recall submitted", "rcl_status": rcl.status,
                    "batch_blocked": bool(batch_after.blocked),
                    "block_reason": batch_after.block_reason[:80] if batch_after.block_reason else None,
                    "approved_by": rcl.approved_by})
    assert batch_after.blocked == 1, "Batch phải bị block sau recall submit"

    # 6. Verify block enforced — try Issue → throw SC-E008
    se_test = frappe.new_doc("SC Stock Entry")
    se_test.entry_type = "Material Issue"
    se_test.posting_date = today()
    se_test.from_warehouse = warehouse
    se_test.append("items", {"item": item_code, "qty": 5, "uom": item_uom,
                              "batch": batch.name, "valuation_rate": 1500})
    se_test.flags.ignore_permissions = True
    block_threw = False
    try:
        se_test.insert()
    except Exception as e:
        block_threw = "BATCH_RECALLED" in str(e) or "block" in str(e).lower()
    results.append({"step": "Block enforce on Issue", "threw": block_threw})

    # 7. Update affected_items: nhập recovered_qty
    rcl.affected_items[0].recovered_qty = flt(rcl.affected_items[0].qty_issued) / 2
    rcl.affected_items[0].destroyed_qty = flt(rcl.affected_items[0].qty_issued) / 2
    rcl.affected_items[0].status = "Recovered"
    rcl.save()
    rcl.reload()
    results.append({"step": "Recovery progress",
                    "recovered": float(rcl.recovered_qty),
                    "destroyed": float(rcl.destroyed_qty),
                    "outstanding": float(rcl.outstanding_qty),
                    "resolution_pct": float(rcl.recall_resolution_pct),
                    "status": rcl.status})

    # 8. Audit trail API
    audit = trace_api.get_audit_trail(item=item_code, warehouse=warehouse,
                                        from_date=add_days(today(), -7),
                                        to_date=today())
    results.append({"step": "Audit trail API",
                    "transactions": audit["total_transactions"],
                    "total_in": audit["total_in"],
                    "total_out": audit["total_out"]})

    # Cleanup batch flag
    frappe.db.set_value("SC Batch", batch.name, "blocked", 0)

    return {"status": "ok", "results": results}
