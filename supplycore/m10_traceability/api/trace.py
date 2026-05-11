"""UC-29 Truy xuất nguồn gốc batch (M10)."""

import frappe
from frappe.utils import flt


@frappe.whitelist()
def get_batch_trace(batch_no: str) -> dict:
    """UC-29: trả full vòng đời batch — header + origin + movements +
    dispensing + current_stock + data_quality."""
    if not batch_no or not frappe.db.exists("SC Batch", batch_no):
        return {"exists": False, "batch_no": batch_no}

    batch = frappe.get_doc("SC Batch", batch_no)

    header = {
        "name": batch.name, "batch_id": batch.batch_id,
        "item": batch.item, "item_name": batch.item_name,
        "manufacturer": batch.manufacturer,
        "supplier": batch.supplier,
        "supplier_batch_no": batch.supplier_batch_no,
        "country_of_origin": batch.country_of_origin,
        "manufacturing_date": str(batch.manufacturing_date) if batch.manufacturing_date else None,
        "expiry_date": str(batch.expiry_date) if batch.expiry_date else None,
        "qc_status": batch.qc_status,
        "blocked": bool(batch.blocked),
        "block_reason": batch.block_reason,
    }

    # Origin: PR → PO → QI
    pr_data = frappe.db.sql("""
        SELECT pri.parent AS pr, pr.posting_date, pr.supplier,
               pr.purchase_order, pr.qc_status
        FROM `tabSC Purchase Receipt Item` pri
        JOIN `tabSC Purchase Receipt` pr ON pr.name = pri.parent
        WHERE pri.batch_no = %s AND pr.docstatus = 1 AND pr.is_return = 0
        ORDER BY pr.posting_date ASC LIMIT 1
    """, batch_no, as_dict=True)
    origin = None
    if pr_data:
        p = pr_data[0]
        qi = frappe.db.get_value("SC Quality Inspection",
            {"purchase_receipt": p["pr"], "batch": batch_no},
            ["name", "overall_status", "inspection_date"], as_dict=True)
        origin = {
            "purchase_receipt": p["pr"],
            "received_date": str(p["posting_date"]),
            "supplier": p["supplier"],
            "purchase_order": p["purchase_order"],
            "pr_qc_status": p["qc_status"],
            "qc_inspection": qi.get("name") if qi else None,
            "qc_result": qi.get("overall_status") if qi else None,
            "qc_date": (str(qi.get("inspection_date"))
                         if qi and qi.get("inspection_date") else None),
        }

    # Movements: tất cả SLE
    movements_raw = frappe.db.sql("""
        SELECT posting_date, posting_time,
               warehouse, bin_location, qty_change,
               valuation_rate, voucher_type, voucher_no,
               remarks, is_cancelled
        FROM `tabSC Stock Ledger Entry`
        WHERE batch = %s
        ORDER BY posting_date ASC, posting_time ASC, creation ASC
    """, batch_no, as_dict=True)
    movements = []
    for m in movements_raw:
        movements.append({
            "posting_date": str(m["posting_date"]),
            "posting_time": str(m["posting_time"]) if m["posting_time"] else None,
            "warehouse": m["warehouse"],
            "bin_location": m["bin_location"],
            "qty_change": flt(m["qty_change"]),
            "valuation_rate": flt(m["valuation_rate"]),
            "voucher_type": m["voucher_type"],
            "voucher_no": m["voucher_no"],
            "remarks": m["remarks"],
            "is_cancelled": bool(m["is_cancelled"]),
        })

    # Dispensing: SC PD Item
    dispensing_raw = frappe.db.sql("""
        SELECT pdi.parent AS pd, pd.dispensing_date, pd.patient,
               p.patient_name, pd.ward, pdi.qty, pdi.unit_cost,
               pdi.bhyt_amount, pdi.patient_pays
        FROM `tabSC PD Item` pdi
        JOIN `tabSC Patient Dispensing` pd ON pd.name = pdi.parent
        LEFT JOIN `tabSC Patient` p ON p.name = pd.patient
        WHERE pdi.batch = %s AND pd.docstatus = 1
        ORDER BY pd.dispensing_date ASC
    """, batch_no, as_dict=True)
    dispensing = [{
        "pd": d["pd"],
        "dispensing_date": str(d["dispensing_date"]),
        "patient": d["patient"],
        "patient_name": d["patient_name"],
        "ward": d["ward"],
        "qty": flt(d["qty"]),
        "unit_cost": flt(d["unit_cost"]),
        "bhyt_amount": flt(d["bhyt_amount"]),
        "patient_pays": flt(d["patient_pays"]),
    } for d in dispensing_raw]

    # Current stock per warehouse
    by_wh_raw = frappe.db.sql("""
        SELECT warehouse, COALESCE(SUM(qty_change), 0) AS qty
        FROM `tabSC Stock Ledger Entry`
        WHERE batch = %s AND is_cancelled = 0
        GROUP BY warehouse
        HAVING qty > 0
    """, batch_no, as_dict=True)
    by_wh = [{"warehouse": r["warehouse"], "qty": flt(r["qty"])} for r in by_wh_raw]
    total_current = sum(r["qty"] for r in by_wh)
    current_stock = {"total_qty": total_current, "by_warehouse": by_wh}

    # Data quality
    missing = []
    if not batch.supplier:
        missing.append("supplier")
    if not batch.supplier_batch_no:
        missing.append("supplier_batch_no")
    if not batch.manufacturer:
        missing.append("manufacturer")
    if not batch.manufacturing_date:
        missing.append("manufacturing_date")
    if not origin:
        missing.append("purchase_receipt_origin")
    if batch.qc_status == "Pending":
        missing.append("qc_inspection_pending")
    data_quality = {
        "complete": len(missing) == 0,
        "missing": missing,
    }

    return {
        "exists": True,
        "header": header,
        "origin": origin,
        "movements": movements,
        "dispensing": dispensing,
        "current_stock": current_stock,
        "data_quality": data_quality,
    }


@frappe.whitelist()
def list_batches_for_item(item_code_or_name: str, limit: int = 20) -> list:
    """UC-29 luồng 2a: search batches by item code OR name LIKE."""
    if not item_code_or_name:
        return []
    items = frappe.db.sql_list("""
        SELECT name FROM `tabSC Item`
        WHERE name LIKE %(t)s OR item_name LIKE %(t)s
        LIMIT 10
    """, {"t": f"%{item_code_or_name}%"})
    if not items:
        return []
    placeholders = ", ".join(["%s"] * len(items))
    return frappe.db.sql(f"""
        SELECT b.name, b.batch_id, b.item, i.item_name,
               b.supplier, b.supplier_batch_no, b.manufacturer,
               b.expiry_date, b.qc_status, b.blocked, b.disabled
        FROM `tabSC Batch` b
        JOIN `tabSC Item` i ON i.name = b.item
        WHERE b.item IN ({placeholders})
        ORDER BY b.expiry_date DESC LIMIT {int(limit)}
    """, tuple(items), as_dict=True)
