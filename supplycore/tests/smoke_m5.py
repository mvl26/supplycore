"""Smoke test M5 — SC Batch FEFO + block expired + scan_expiring_batches."""

import frappe
from frappe.utils import today, add_days, flt
from supplycore.api import fefo as fefo_api


def run():
    item_code = "DTRC-NACL09"  # NaCl 0.9% — has_batch_no=1 từ seed
    warehouse = "Kho Dịch truyền"
    if not (frappe.db.exists("SC Item", item_code) and frappe.db.exists("SC Warehouse", warehouse)):
        return {"status": "skip", "reason": "Cần seed master data"}

    item_uom = frappe.db.get_value("SC Item", item_code, "uom")
    results = []

    # Cleanup batches cũ
    for b in frappe.get_all("SC Batch", filters={"item": item_code, "supplier_batch_no": ["like", "M5-SMOKE-%"]}):
        frappe.db.set_value("SC Batch", b.name, "disabled", 1)
    frappe.db.commit()

    # 1. Tạo 3 batches A(20d) / B(60d) / C(180d) qua SC Stock Entry Material Receipt
    batches_created = []
    for tag, days in [("A", 20), ("B", 60), ("C", 180)]:
        bid = f"{item_code}-M5-SMOKE-{tag}-{frappe.utils.random_string(4)}"
        b = frappe.new_doc("SC Batch")
        b.batch_id = bid
        b.item = item_code
        b.expiry_date = add_days(today(), days)
        b.manufacturing_date = today()
        b.supplier_batch_no = f"M5-SMOKE-{tag}"
        b.flags.ignore_permissions = True
        b.insert()
        # Receipt 100 đơn vị vào warehouse
        se = frappe.new_doc("SC Stock Entry")
        se.entry_type = "Material Receipt"
        se.posting_date = today()
        se.to_warehouse = warehouse
        se.append("items", {"item": item_code, "qty": 100, "uom": item_uom,
                             "batch": b.name, "valuation_rate": 50000})
        se.flags.ignore_permissions = True
        se.insert(); se.submit()
        batches_created.append({"batch": b.name, "days": days})
    results.append({"step": "Setup", "batches": [b["batch"] for b in batches_created]})

    # 2. FEFO query
    r = fefo_api.get_suggested_batches(item_code, warehouse, qty=50)
    bn = [b["batch_no"] for b in r["batches"]]
    sev = [b["severity"] for b in r["batches"]]
    results.append({"step": "FEFO order", "batches": bn, "severities": sev,
                    "fully_satisfied": r["fully_satisfied"]})
    assert len(bn) >= 2, f"Expected ≥2 batches, got {bn}"
    # Batch gần hết hạn nhất phải đứng đầu
    assert bn[0] == batches_created[0]["batch"], f"FEFO order sai: {bn}"

    # 3. Block batch A → loại trừ
    frappe.db.set_value("SC Batch", batches_created[0]["batch"],
                        {"blocked": 1, "block_reason": "Smoke test recall",
                         "blocked_by": "Administrator"})
    frappe.db.commit()
    r2 = fefo_api.get_suggested_batches(item_code, warehouse, qty=50)
    bn2 = [b["batch_no"] for b in r2["batches"]]
    assert batches_created[0]["batch"] not in bn2, f"Blocked vẫn xuất hiện: {bn2}"
    results.append({"step": "After block A", "batches": bn2})

    # 4. check_batch_status
    s = fefo_api.check_batch_status(batches_created[0]["batch"])
    results.append({"step": "check_status(blocked A)", "is_blocked": s["is_blocked"],
                    "severity": s["severity"]})

    # 5. Unblock + thử FEFO violation
    frappe.db.set_value("SC Batch", batches_created[0]["batch"], "blocked", 0)
    frappe.db.commit()

    se_violate = frappe.new_doc("SC Stock Entry")
    se_violate.entry_type = "Material Issue"
    se_violate.posting_date = today()
    se_violate.from_warehouse = warehouse
    se_violate.append("items", {
        "item": item_code, "qty": 10, "uom": item_uom,
        "batch": batches_created[2]["batch"],  # C — xa hạn nhất
        "valuation_rate": 50000,
    })
    se_violate.flags.ignore_permissions = True
    threw = False
    try:
        se_violate.insert()
    except frappe.exceptions.ValidationError as e:
        threw = "FEFO" in str(e) or "SC-E001" in str(e)
    results.append({"step": "FEFO violation", "threw": threw})

    # 6. Override + reason → accept
    se_ok = frappe.new_doc("SC Stock Entry")
    se_ok.entry_type = "Material Issue"
    se_ok.posting_date = today()
    se_ok.from_warehouse = warehouse
    se_ok.append("items", {
        "item": item_code, "qty": 10, "uom": item_uom,
        "batch": batches_created[2]["batch"], "valuation_rate": 50000,
        "fefo_override": 1, "fefo_override_reason": "QA smoke test override",
    })
    se_ok.flags.ignore_permissions = True
    try:
        se_ok.insert()
        results.append({"step": "Override accepted", "se": se_ok.name})
        frappe.delete_doc("SC Stock Entry", se_ok.name, force=True, ignore_permissions=True)
    except Exception as e:
        results.append({"step": "Override FAILED", "err": str(e)[:200]})

    # 7. scan_expiring_batches
    from supplycore.m5_fefo.api import fefo_picker
    fefo_picker.scan_expiring_batches()
    alerts = frappe.db.count("Batch Expiry Alert",
                              {"batch_no": ["in", [b["batch"] for b in batches_created]]})
    results.append({"step": "scan_expiring_batches", "alerts": alerts})

    # Cleanup
    for bc in batches_created:
        try:
            frappe.db.set_value("SC Batch", bc["batch"], "disabled", 1)
        except Exception:
            pass
    frappe.db.commit()

    return {"status": "ok", "results": results}
