"""Smoke test M3 — QC Checklist Template + SC Purchase Receipt + auto SC QI."""

import frappe
from frappe.utils import today, add_days, flt


TEMPLATE_TITLE = "Test M3 Template (Vật tư tiêu hao)"


def run():
    supplier = frappe.db.get_value("SC Supplier", {"supplier_name": "Công ty CP Dược Hậu Giang"}, "name")
    item_code = "VTTH-GLOVE-S"
    warehouse = "Kho Cách ly QC"
    if not all([supplier, frappe.db.exists("SC Item", item_code), frappe.db.exists("SC Warehouse", warehouse)]):
        return {"status": "skip", "reason": "Cần seed master data"}

    results = []

    # Cleanup
    for tpl in frappe.get_all("QC Checklist Template", filters={"title": TEMPLATE_TITLE}):
        frappe.delete_doc("QC Checklist Template", tpl.name, force=True, ignore_permissions=True)
    frappe.db.commit()

    # 1. QC Template
    tpl = frappe.new_doc("QC Checklist Template")
    tpl.title = TEMPLATE_TITLE
    tpl.enabled = 1
    for i, name in enumerate(["Bao bì nguyên vẹn", "Nhãn mác đúng", "Hạn dùng ≥ 6 tháng"]):
        tpl.append("criteria", {"criterion_name": name, "is_critical": 1, "sequence": i + 1})
    tpl.insert(ignore_permissions=True)
    results.append({"step": "Template", "tpl": tpl.name, "criteria": len(tpl.criteria)})

    # 2. SC Purchase Receipt
    item_uom = frappe.db.get_value("SC Item", item_code, "uom")
    pr = frappe.new_doc("SC Purchase Receipt")
    pr.supplier = supplier
    pr.posting_date = today()
    pr.to_warehouse = warehouse
    pr.qc_required = 1
    pr.append("items", {
        "item": item_code, "qty": 100, "uom": item_uom,
        "rate": 30000, "warehouse": warehouse,
        "expiry_date": add_days(today(), 365),
        "manufacturing_date": today(),
        "supplier_batch_no": "DHG-LOT-001",
    })
    pr.flags.ignore_permissions = True
    pr.insert(); pr.submit(); pr.reload()
    results.append({"step": "PR submitted", "pr": pr.name, "qc_status": pr.qc_status})

    # 3. Verify auto-create SC Batch + auto QI
    qis = frappe.get_all("SC Quality Inspection",
                          filters={"purchase_receipt": pr.name},
                          fields=["name", "item", "batch", "overall_status"])
    results.append({"step": "Auto-created", "qi_count": len(qis), "qis": qis})

    # Verify SC Batch tự sinh
    batch = frappe.db.get_value("SC Purchase Receipt Item",
                                  {"parent": pr.name}, "batch_no")
    results.append({"step": "Auto-batch", "batch": batch})

    # 4. Mark QI Pass và submit
    if qis:
        qi = frappe.get_doc("SC Quality Inspection", qis[0].name)
        for r in qi.readings:
            r.status = "Accepted"
        qi.overall_status = "Accepted"
        qi.action_taken = "Accept"
        qi.save(ignore_permissions=True)
        qi.submit()
        pr.reload()
        results.append({"step": "QI Accepted", "qi": qi.name, "pr_qc_status": pr.qc_status})
        # Verify Batch.qc_status update
        if batch:
            bs = frappe.db.get_value("SC Batch", batch, "qc_status")
            results.append({"step": "Batch QC sync", "batch": batch, "qc_status": bs})

    return {"status": "ok", "results": results}
