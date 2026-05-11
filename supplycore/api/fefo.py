"""FEFO API — supplycore.api.fefo.* (M5).

Endpoint canonical theo Phase 2 API doc §4.1:
    POST /api/method/supplycore.api.fefo.get_suggested_batches
"""

import frappe
from frappe import _
from frappe.utils import flt, getdate, today, date_diff


@frappe.whitelist()
def get_suggested_batches(item_code: str, warehouse: str, qty: float = 0, uom: str = None) -> dict:
    """Trả batch theo FEFO — gần hết hạn trước, kèm cumulative suggested_qty.

    Bỏ qua: batch hết hạn, batch sc_blocked=1, batch không có expiry_date (xếp cuối).

    Returns:
        {
          "batches": [
            {"batch_no", "expiry_date", "manufacturing_date",
             "available_qty", "suggested_qty", "days_to_expiry"},
            ...
          ],
          "total_available": float,
          "fully_satisfied": bool,
          "shortfall": float
        }
    """
    if not item_code or not warehouse:
        frappe.throw(_("item_code và warehouse bắt buộc"))

    qty = flt(qty)

    # SC v0.2: Stock Ledger duy nhất là SC Stock Ledger Entry với field `batch` + `qty_change`.
    rows = frappe.db.sql("""
        SELECT b.name AS batch_no,
               b.expiry_date,
               b.manufacturing_date,
               COALESCE(sle.qty, 0) AS available_qty
        FROM `tabSC Batch` b
        LEFT JOIN (
            SELECT batch, SUM(qty_change) AS qty
            FROM `tabSC Stock Ledger Entry`
            WHERE warehouse = %(warehouse)s
              AND is_cancelled = 0
              AND batch IS NOT NULL
            GROUP BY batch
        ) sle ON sle.batch = b.name
        WHERE b.item = %(item)s
          AND b.disabled = 0
          AND COALESCE(b.blocked, 0) = 0
          AND (b.expiry_date IS NULL OR b.expiry_date >= CURDATE())
          AND (b.qc_status IS NULL OR b.qc_status = '' OR b.qc_status IN ('Accepted', 'Conditional'))
        HAVING available_qty > 0
        ORDER BY COALESCE(b.expiry_date, '9999-12-31') ASC, b.creation ASC
    """, {"warehouse": warehouse, "item": item_code}, as_dict=True)

    today_d = getdate(today())
    suggested = []
    remaining = qty
    for r in rows:
        days_left = date_diff(r.expiry_date, today_d) if r.expiry_date else None
        take = min(remaining, flt(r.available_qty)) if qty > 0 else 0
        suggested.append({
            "batch_no":           r.batch_no,
            "expiry_date":        str(r.expiry_date) if r.expiry_date else None,
            "manufacturing_date": str(r.manufacturing_date) if r.manufacturing_date else None,
            "available_qty":      flt(r.available_qty),
            "suggested_qty":      flt(take),
            "days_to_expiry":     days_left,
            "severity":           _severity(days_left),
        })
        remaining -= take
        if qty > 0 and remaining <= 0 and len(suggested) >= 1:
            # Vẫn trả thêm 1-2 batch nữa cho user xem alternate
            if len(suggested) >= 5:
                break

    total_available = sum(b["available_qty"] for b in suggested)
    return {
        "batches":          suggested,
        "total_available":  total_available,
        "fully_satisfied":  qty == 0 or remaining <= 0,
        "shortfall":        max(0, remaining) if qty > 0 else 0,
    }


@frappe.whitelist()
def check_batch_status(batch_no: str) -> dict:
    """Trả thông tin nhanh về 1 batch — phục vụ UI validate trước khi submit."""
    b = frappe.db.get_value("SC Batch", batch_no,
                             ["name", "item", "expiry_date", "blocked", "block_reason"],
                             as_dict=True)
    if not b:
        return {"exists": False}
    today_d = getdate(today())
    days_left = date_diff(b.expiry_date, today_d) if b.expiry_date else None
    return {
        "exists":           True,
        "batch_no":         b.name,
        "item_code":        b.item,
        "expiry_date":      str(b.expiry_date) if b.expiry_date else None,
        "days_to_expiry":   days_left,
        "is_expired":       days_left is not None and days_left < 0,
        "is_blocked":       bool(b.blocked),
        "block_reason":     b.block_reason,
        "severity":         _severity(days_left),
    }


def _severity(days_left):
    if days_left is None:
        return "NoExpiry"
    if days_left < 0:
        return "Expired"
    if days_left < 30:
        return "Critical"
    if days_left < 90:
        return "Warning"
    return "OK"
