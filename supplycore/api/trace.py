"""Truy xuất nguồn gốc API — supplycore.api.trace.* (M10).

Endpoint canonical theo Phase 2 API §4.3:
  GET /api/method/supplycore.api.trace.get_batch_trace?batch_no=X
"""

import frappe
from frappe import _
from frappe.utils import flt, getdate


@frappe.whitelist()
def get_batch_trace(batch_no: str) -> dict:
    """Truy xuất full lifecycle của 1 batch.

    Returns:
        {
          batch_no, item_code, item_name, expiry_date, blocked,
          source: {supplier, purchase_receipt, received_date, qc_status},
          movements: [{type, voucher_type, voucher_no, date, qty,
                       from_warehouse, to_warehouse, party}],
          current_qty_per_warehouse: [{warehouse, qty}],
          remaining_qty: total
        }

    # TODO GĐ2: bổ sung trace/recall theo SC Delivery Note → SC Customer (chuỗi bán)
    """
    if not frappe.db.exists("SC Batch", batch_no):
        frappe.throw(_("Batch {0} không tồn tại").format(batch_no))

    batch = frappe.db.get_value("SC Batch", batch_no,
        ["name", "item", "item_name", "expiry_date", "manufacturing_date",
         "supplier", "supplier_batch_no", "manufacturer", "qc_status",
         "blocked", "block_reason"], as_dict=True)

    # Source: Purchase Receipt that created this batch
    source = frappe.db.sql("""
        SELECT pr.name AS purchase_receipt, pr.posting_date AS received_date,
               pr.supplier, pr.qc_status
        FROM `tabSC Purchase Receipt Item` pri
        JOIN `tabSC Purchase Receipt` pr ON pr.name = pri.parent
        WHERE pri.batch_no = %s AND pr.docstatus = 1
        ORDER BY pr.posting_date ASC LIMIT 1
    """, batch_no, as_dict=True)

    # All Stock Ledger Entries — chronological
    movements = frappe.db.sql("""
        SELECT posting_date, posting_time,
               voucher_type, voucher_no,
               warehouse, qty_change,
               valuation_rate, remarks
        FROM `tabSC Stock Ledger Entry`
        WHERE batch = %s AND is_cancelled = 0
        ORDER BY posting_date ASC, posting_time ASC
    """, batch_no, as_dict=True)

    # Current qty per warehouse
    qty_wh = frappe.db.sql("""
        SELECT warehouse, SUM(qty_change) AS qty
        FROM `tabSC Stock Ledger Entry`
        WHERE batch = %s AND is_cancelled = 0
        GROUP BY warehouse
        HAVING qty != 0
    """, batch_no, as_dict=True)
    remaining = sum(flt(r.qty) for r in qty_wh)

    return {
        "batch_no": batch.name,
        "item_code": batch.item,
        "item_name": batch.item_name,
        "expiry_date": str(batch.expiry_date) if batch.expiry_date else None,
        "manufacturing_date": str(batch.manufacturing_date) if batch.manufacturing_date else None,
        "supplier": batch.supplier,
        "supplier_batch_no": batch.supplier_batch_no,
        "manufacturer": batch.manufacturer,
        "qc_status": batch.qc_status,
        "blocked": bool(batch.blocked),
        "block_reason": batch.block_reason,
        "source": source[0] if source else None,
        "movements": [_serialize_row(m) for m in movements],
        "current_qty_per_warehouse": [_serialize_row(q) for q in qty_wh],
        "remaining_qty": flt(remaining),
        "total_movements": len(movements),
    }


@frappe.whitelist()
def get_audit_trail(item: str, warehouse: str = None,
                     from_date: str = None, to_date: str = None) -> dict:
    """Audit trail giao dịch SC SLE cho điều tra thất thoát (UC-31).

    Returns full transaction history with user, voucher, qty change.
    """
    if not frappe.db.exists("SC Item", item):
        frappe.throw(_("Item {0} không tồn tại").format(item))

    sql = """
        SELECT sle.posting_date, sle.posting_time, sle.voucher_type, sle.voucher_no,
               sle.warehouse, sle.batch, sle.qty_change, sle.balance_qty,
               sle.valuation_rate, sle.remarks,
               sle.creation, sle.owner, sle.modified_by
        FROM `tabSC Stock Ledger Entry` sle
        WHERE sle.item = %(item)s
    """
    params = {"item": item}
    if warehouse:
        sql += " AND sle.warehouse = %(warehouse)s"
        params["warehouse"] = warehouse
    if from_date:
        sql += " AND sle.posting_date >= %(from_date)s"
        params["from_date"] = from_date
    if to_date:
        sql += " AND sle.posting_date <= %(to_date)s"
        params["to_date"] = to_date
    sql += " ORDER BY sle.posting_date ASC, sle.posting_time ASC"

    rows = frappe.db.sql(sql, params, as_dict=True)
    total_in = sum(flt(r.qty_change) for r in rows if flt(r.qty_change) > 0)
    total_out = abs(sum(flt(r.qty_change) for r in rows if flt(r.qty_change) < 0))
    net = total_in - total_out
    cancelled = sum(1 for r in rows
                     if frappe.db.get_value("SC Stock Ledger Entry",
                                              {"voucher_no": r.voucher_no, "is_cancelled": 1}))

    return {
        "item": item,
        "warehouse": warehouse,
        "period": {"from": from_date, "to": to_date},
        "total_transactions": len(rows),
        "total_in": flt(total_in),
        "total_out": flt(total_out),
        "net_movement": flt(net),
        "cancelled_count": cancelled,
        "rows": [_serialize_row(r) for r in rows],
    }


def _serialize_row(row):
    """Convert dict row có Date/Datetime → string."""
    out = {}
    for k, v in row.items():
        if hasattr(v, "isoformat"):
            out[k] = v.isoformat()
        else:
            out[k] = flt(v) if isinstance(v, (int, float)) else v
    return out
