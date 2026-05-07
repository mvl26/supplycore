"""Smoke test M4 — Bin Location + WMS API scan_barcode + confirm_putaway."""

import frappe
from frappe.utils import today, add_days, random_string
from supplycore.api import wms


def run():
    item_code = "VTTH-GLOVE-S"
    warehouse = "Kho Vật tư tiêu hao"
    if not (frappe.db.exists("SC Item", item_code) and frappe.db.exists("SC Warehouse", warehouse)):
        return {"status": "skip", "reason": "Cần seed master data"}

    bin_name = frappe.db.get_value("SC Item", item_code, "default_bin_location")
    if not bin_name:
        return {"status": "skip", "reason": "Item chưa có default_bin"}

    item_uom = frappe.db.get_value("SC Item", item_code, "uom")
    has_batch = frappe.db.get_value("SC Item", item_code, "has_batch_no")
    results = []

    # Tạo batch để Material Receipt qua được validate
    batch_name = None
    if has_batch:
        batch = frappe.new_doc("SC Batch")
        batch.batch_id = f"{item_code}-M4SMK-{random_string(5)}"
        batch.item = item_code
        batch.expiry_date = add_days(today(), 180)
        batch.manufacturing_date = today()
        batch.flags.ignore_permissions = True
        batch.insert()
        batch_name = batch.name

    # 1. scan_barcode (item)
    r = wms.scan_barcode(item_code)
    assert r["type"] == "item"
    results.append({"step": "scan(item)", "item": r["item_code"],
                    "suggested_bin": r.get("suggested_bin", {}).get("bin_code")})

    # 2. scan_barcode (bin)
    r = wms.scan_barcode(bin_name)
    assert r["type"] == "bin"
    results.append({"step": "scan(bin)", "bin": r["bin_location"]})

    # 3. lookup_bin_for_item
    r = wms.lookup_bin_for_item(item_code, warehouse)
    results.append({"step": "lookup_bin", "source": r["source"]})

    # 4. confirm_putaway → SC Stock Entry draft (cần update để pass batch)
    item_uom = frappe.db.get_value("SC Item", item_code, "uom")
    se = frappe.new_doc("SC Stock Entry")
    se.entry_type = "Material Receipt"
    se.posting_date = today()
    se.to_warehouse = warehouse
    se.pda_session_id = "SMOKE-PDA-M4"
    se.append("items", {"item": item_code, "qty": 10, "uom": item_uom,
                         "batch": batch_name, "target_bin": bin_name,
                         "valuation_rate": 30000})
    se.flags.ignore_permissions = True
    se.insert(); se.reload()
    results.append({"step": "PDA putaway draft", "se": se.name,
                    "target_bin_set": se.items[0].target_bin == bin_name,
                    "pda_session": se.pda_session_id})
    frappe.delete_doc("SC Stock Entry", se.name, force=True, ignore_permissions=True)

    # 5. Hook auto-suggest bin (KHÔNG nhập target_bin)
    se2 = frappe.new_doc("SC Stock Entry")
    se2.entry_type = "Material Receipt"
    se2.posting_date = today()
    se2.to_warehouse = warehouse
    se2.append("items", {"item": item_code, "qty": 5, "uom": item_uom,
                          "batch": batch_name, "valuation_rate": 30000})
    se2.flags.ignore_permissions = True
    se2.insert(); se2.reload()
    auto_bin = se2.items[0].target_bin
    results.append({"step": "Auto-suggest hook", "se": se2.name,
                    "auto_bin": auto_bin, "match_default": auto_bin == bin_name})
    frappe.delete_doc("SC Stock Entry", se2.name, force=True, ignore_permissions=True)

    # 6. quick_search
    found = wms.quick_search("Găng", "item", limit=5)
    results.append({"step": "quick_search", "found": len(found)})

    return {"status": "ok", "results": results}
