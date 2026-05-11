"""UC-13 — Quick stock entry API (no PDA, manual web form).

Mục tiêu: biết hàng nào / lô nào / số lượng / bin nào — qua form nhập tay
+ autocomplete search thay vì barcode scan.
"""

import frappe
from frappe.utils import flt, today


@frappe.whitelist()
def quick_putaway(item: str, qty, uom: str, warehouse: str,
                   bin_location: str, batch: str = None,
                   valuation_rate=0, remarks: str = None) -> dict:
    """Xếp hàng vào bin — tạo SC Stock Entry Material Receipt + submit."""
    se = frappe.new_doc("SC Stock Entry")
    se.entry_type = "Material Receipt"
    se.posting_date = today()
    se.to_warehouse = warehouse
    se.purpose = "Quick Putaway (UC-13)"
    se.remarks = remarks or "Putaway via quick form (UC-13)"
    se.append("items", {
        "item": item,
        "qty": flt(qty),
        "uom": uom,
        "valuation_rate": flt(valuation_rate),
        "batch": batch,
        "target_bin": bin_location,
    })
    se.flags.ignore_permissions = True
    se.insert()
    se.submit()
    return {"stock_entry": se.name, "status": "OK", "qty": flt(qty),
            "bin": bin_location, "warehouse": warehouse}


@frappe.whitelist()
def quick_picking(item: str, qty, uom: str, warehouse: str,
                   bin_location: str, batch: str = None,
                   remarks: str = None) -> dict:
    """Lấy hàng từ bin — tạo SC Stock Entry Material Issue + submit."""
    se = frappe.new_doc("SC Stock Entry")
    se.entry_type = "Material Issue"
    se.posting_date = today()
    se.from_warehouse = warehouse
    se.purpose = "Quick Picking (UC-13)"
    se.remarks = remarks or "Picking via quick form (UC-13)"
    se.append("items", {
        "item": item,
        "qty": flt(qty),
        "uom": uom,
        "batch": batch,
        "source_bin": bin_location,
    })
    se.flags.ignore_permissions = True
    se.insert()
    se.submit()
    return {"stock_entry": se.name, "status": "OK", "qty": flt(qty),
            "bin": bin_location, "warehouse": warehouse}


# ----------------------------------------------------------------------
# Lookup helpers — thay barcode scan bằng autocomplete search
# ----------------------------------------------------------------------

@frappe.whitelist()
def lookup_item(text: str, limit: int = 10) -> list:
    """Search SC Item theo item_code OR item_name LIKE."""
    return frappe.db.sql("""
        SELECT name AS item_code, item_name, uom, has_batch_no
        FROM `tabSC Item`
        WHERE disabled = 0 AND is_stock_item = 1
          AND (name LIKE %(t)s OR item_name LIKE %(t)s)
        ORDER BY item_name LIMIT %(lim)s
    """, {"t": f"%{text}%", "lim": int(limit)}, as_dict=True)


@frappe.whitelist()
def lookup_batch(item: str, text: str = "", limit: int = 10) -> list:
    """Search SC Batch của item theo batch_id OR supplier_batch_no LIKE.
    Sort theo expiry_date ASC (FEFO hint)."""
    return frappe.db.sql("""
        SELECT name AS batch_no, batch_id, expiry_date,
               manufacturing_date, supplier_batch_no, qc_status
        FROM `tabSC Batch`
        WHERE item = %(item)s AND disabled = 0 AND COALESCE(blocked, 0) = 0
          AND (batch_id LIKE %(t)s OR COALESCE(supplier_batch_no, '') LIKE %(t)s)
        ORDER BY COALESCE(expiry_date, '9999-12-31') ASC
        LIMIT %(lim)s
    """, {"item": item, "t": f"%{text}%", "lim": int(limit)}, as_dict=True)


@frappe.whitelist()
def lookup_bin(text: str, warehouse: str = None, limit: int = 10) -> list:
    """Search Bin Location theo bin_code OR barcode LIKE."""
    cond = "AND warehouse = %(warehouse)s" if warehouse else ""
    sql = f"""
        SELECT name, bin_code, warehouse, barcode, zone,
               COALESCE(current_qty, 0) AS current_qty,
               capacity_qty, status
        FROM `tabBin Location`
        WHERE enabled = 1 {cond}
          AND (bin_code LIKE %(t)s OR COALESCE(barcode, '') LIKE %(t)s)
        ORDER BY bin_code LIMIT %(lim)s
    """
    params = {"t": f"%{text}%", "lim": int(limit)}
    if warehouse:
        params["warehouse"] = warehouse
    return frappe.db.sql(sql, params, as_dict=True)


# ----------------------------------------------------------------------
# Query: "biết hàng / lô / qty / ở đâu"
# ----------------------------------------------------------------------

@frappe.whitelist()
def query_stock_position(item: str = None, warehouse: str = None,
                          bin_location: str = None, batch: str = None,
                          limit: int = 200) -> list:
    """UC-13 yêu cầu cốt lõi: biết hàng nào, lô nào, số lượng, ở bin nào.

    Group SC SLE theo (item, warehouse, bin_location, batch),
    HAVING qty > 0. Tất cả filter optional.

    Returns: list dict với keys
      item, item_name, uom, warehouse, bin_location, bin_code,
      batch, batch_id, expiry_date, qc_status, qty
    """
    where = ["sle.is_cancelled = 0"]
    params = {"lim": int(limit)}
    if item:
        where.append("sle.item = %(item)s"); params["item"] = item
    if warehouse:
        where.append("sle.warehouse = %(warehouse)s"); params["warehouse"] = warehouse
    if bin_location:
        where.append("sle.bin_location = %(bin)s"); params["bin"] = bin_location
    if batch:
        where.append("sle.batch = %(batch)s"); params["batch"] = batch

    sql = f"""
        SELECT sle.item, i.item_name, i.uom,
               sle.warehouse, sle.bin_location,
               COALESCE(bl.bin_code, '') AS bin_code,
               sle.batch,
               COALESCE(b.batch_id, '') AS batch_id,
               b.expiry_date,
               COALESCE(b.qc_status, '') AS qc_status,
               SUM(sle.qty_change) AS qty
        FROM `tabSC Stock Ledger Entry` sle
        JOIN `tabSC Item` i ON i.name = sle.item
        LEFT JOIN `tabBin Location` bl ON bl.name = sle.bin_location
        LEFT JOIN `tabSC Batch` b ON b.name = sle.batch
        WHERE {' AND '.join(where)}
        GROUP BY sle.item, sle.warehouse, sle.bin_location, sle.batch
        HAVING qty > 0
        ORDER BY i.item_name, sle.warehouse, bin_code, expiry_date
        LIMIT %(lim)s
    """
    return frappe.db.sql(sql, params, as_dict=True)
