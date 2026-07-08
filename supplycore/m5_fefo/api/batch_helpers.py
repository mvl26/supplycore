"""UC-15 — Batch helpers: generate_batch_id + lookup_batch_by_no."""

import frappe
from frappe import _
from frappe.utils import getdate

from supplycore.utils.permissions import block_portal


@frappe.whitelist()
def generate_batch_id(item: str, expiry_date) -> str:
    """UC-15 step 3: batch_id format `[ItemCode]-[YYYYMM]-[Seq]`.

    Seq tăng dần per (item, year-month) qua SQL count + 1. Atomic enough
    cho concurrency thấp; collision sẽ throw unique constraint nếu xảy ra.
    """
    block_portal()
    if not item or not expiry_date:
        frappe.throw(_("item và expiry_date required"))
    ym = getdate(expiry_date).strftime("%Y%m")
    prefix = f"{item}-{ym}-"
    cnt = frappe.db.sql("""
        SELECT COUNT(*) FROM `tabSC Batch`
        WHERE batch_id LIKE %s
    """, prefix + "%")[0][0]
    seq = (cnt or 0) + 1
    return f"{prefix}{seq:03d}"


@frappe.whitelist()
def lookup_batch_by_no(text: str, limit: int = 20) -> list:
    """UC-15 step 6: search batch_id OR supplier_batch_no LIKE (cross-item)."""
    block_portal()
    return frappe.db.sql("""
        SELECT b.name, b.batch_id, b.item, i.item_name,
               b.supplier_batch_no, b.manufacturer,
               b.expiry_date, b.manufacturing_date,
               b.qc_status, b.blocked, b.disabled
        FROM `tabSC Batch` b
        JOIN `tabSC Item` i ON i.name = b.item
        WHERE b.disabled = 0
          AND (b.batch_id LIKE %(t)s OR COALESCE(b.supplier_batch_no, '') LIKE %(t)s)
        ORDER BY b.expiry_date ASC
        LIMIT %(lim)s
    """, {"t": f"%{text}%", "lim": int(limit)}, as_dict=True)
