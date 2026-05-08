"""Integration smoke — Alert → Action (M11 actionable).

Tests:
1. expiring_batch alert → action_quarantine_batch → SE Material Transfer to quarantine
2. low_stock alert → action_create_material_request → SC MR draft
3. (Skip overdue_payment vì cần PI quá hạn — tốn setup, defer to UAT)

Asserts:
- Action tạo đúng doctype
- Alert.action_taken=1, action_doctype/name khớp
- Alert.resolved=1, resolution_action='Acted Upon'
"""

import frappe
from frappe.utils import today, add_days, flt, random_string


def run():
    if not frappe.db.exists("SC Item", "VTTH-MASK-3PLY"):
        return {"status": "skip", "reason": "Cần seed master data"}

    item = "VTTH-MASK-3PLY"
    item_uom = frappe.db.get_value("SC Item", item, "uom")
    wh = "Kho Vật tư tiêu hao"
    quarantine = frappe.db.get_value("SC Warehouse",
        {"warehouse_type": "Quarantine", "disabled": 0}, "name")
    if not quarantine:
        return {"status": "skip", "reason": "Cần Kho Quarantine"}

    ts = random_string(6)
    results = []

    # === Cleanup: xoá alerts test trước đây ===
    for a in frappe.get_all("SC Alert", filters={"title": ["like", "%ALRTACT-TEST%"]}):
        frappe.delete_doc("SC Alert", a.name, force=True, ignore_permissions=True)
    frappe.db.commit()

    # ============================================================
    # TEST 1: expiring_batch → quarantine
    # ============================================================
    # Setup: tạo batch sắp hết hạn + receive 30 hộp
    batch = frappe.new_doc("SC Batch")
    batch.batch_id = f"ALRTACT-EXP-{ts}"
    batch.item = item
    batch.expiry_date = add_days(today(), 10)  # < 30 ngày
    batch.manufacturing_date = today()
    batch.flags.ignore_permissions = True
    batch.insert()

    se_in = frappe.new_doc("SC Stock Entry")
    se_in.entry_type = "Material Receipt"
    se_in.posting_date = today()
    se_in.to_warehouse = wh
    se_in.append("items", {"item": item, "qty": 30, "uom": item_uom,
                            "valuation_rate": 1500, "batch": batch.name,
                            "t_warehouse": wh})
    se_in.flags.ignore_permissions = True
    se_in.insert(); se_in.submit()
    results.append({"step": "1a. Setup batch + nhập kho",
                    "batch": batch.name, "qty": 30})

    # Tạo alert thủ công cho batch này
    alert = frappe.new_doc("SC Alert")
    alert.alert_date = today()
    alert.alert_type = "expiring_batch"
    alert.severity = "Warning"
    alert.title = f"ALRTACT-TEST-EXP {ts}"
    alert.message = "Test alert"
    alert.reference_doctype = "SC Batch"
    alert.reference_name = batch.name
    alert.flags.ignore_permissions = True
    alert.insert()
    results.append({"step": "1b. Tạo expiring_batch alert", "alert": alert.name})

    # Trigger action
    se_quar = alert.action_quarantine_batch()
    alert.reload()
    se_doc = frappe.get_doc("SC Stock Entry", se_quar)
    results.append({
        "step": "1c. action_quarantine_batch",
        "se": se_quar,
        "se_type": se_doc.entry_type,
        "from_wh": se_doc.from_warehouse,
        "to_wh": se_doc.to_warehouse,
        "alert_resolved": int(alert.resolved),
        "action_doctype": alert.action_doctype,
    })
    assert se_doc.entry_type == "Material Transfer"
    assert se_doc.to_warehouse == quarantine
    assert se_doc.from_warehouse == wh
    assert alert.action_taken == 1
    assert alert.action_doctype == "SC Stock Entry"
    assert alert.action_name == se_quar
    assert alert.resolved == 1
    assert alert.resolution_action == "Acted Upon"

    # ============================================================
    # TEST 2: low_stock → MR draft
    # ============================================================
    alert2 = frappe.new_doc("SC Alert")
    alert2.alert_date = today()
    alert2.alert_type = "low_stock"
    alert2.severity = "Critical"
    alert2.title = f"ALRTACT-TEST-LOW {ts}"
    alert2.message = "Test low_stock"
    alert2.reference_doctype = "SC Item"
    alert2.reference_name = item
    alert2.flags.ignore_permissions = True
    alert2.insert()
    results.append({"step": "2a. Tạo low_stock alert", "alert": alert2.name})

    mr_name = alert2.action_create_material_request()
    alert2.reload()
    mr = frappe.get_doc("SC Material Request", mr_name)
    results.append({
        "step": "2b. action_create_material_request",
        "mr": mr_name,
        "items": len(mr.items),
        "first_item": mr.items[0].item if mr.items else None,
        "first_qty": flt(mr.items[0].qty) if mr.items else 0,
        "alert_resolved": int(alert2.resolved),
    })
    assert mr.items[0].item == item
    assert flt(mr.items[0].qty) > 0
    assert alert2.action_doctype == "SC Material Request"
    assert alert2.action_name == mr_name
    assert alert2.resolved == 1

    # ============================================================
    # TEST 3: idempotent — 2nd action call should fail
    # ============================================================
    try:
        alert.action_quarantine_batch()
        assert False, "Phải throw vì đã có action"
    except frappe.ValidationError as e:
        results.append({"step": "3. Idempotent guard",
                        "error_msg": str(e)[:100]})

    return {"status": "ok", "results": results}
