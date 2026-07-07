"""Override `erpnext.stock.doctype.batch.batch.get_batches` để sort theo FEFO (M5)."""

import frappe
from frappe.utils import flt

from supplycore.utils.permissions import block_portal


@frappe.whitelist()
def get_batches_fefo(item_code, warehouse, qty=0, throw=False, serial_no=None):
    """Wrapper của ERPNext get_batches: gọi gốc, lọc bỏ block/expired, sort expiry ASC.

    GĐ4 Task 5 (security sweep, defense-in-depth cuối): hàm module-level nên
    KHÔNG qua `run_doc_method` (chỉ instance method mới tự động được kiểm
    `has_permission("read")`) — bản thân decorator `@frappe.whitelist()` không
    kiểm quyền gì, chỉ đánh dấu network-reachable. Lộ tồn kho theo batch/FEFO
    xuyên kho, mirror `api/fefo.py::get_suggested_batches` (đã gate).
    """
    block_portal()
    try:
        from erpnext.stock.doctype.batch.batch import get_batches as _erpnext_get_batches
        batches = _erpnext_get_batches(item_code, warehouse, qty, throw, serial_no) or []
    except Exception:
        # Fallback nếu ERPNext API thay đổi: query trực tiếp
        batches = _query_batches_direct(item_code, warehouse)

    # Loại expired + blocked
    today_d = frappe.utils.getdate(frappe.utils.today())
    filtered = []
    for b in batches:
        batch_no = b.get("batch_no") or b.get("name")
        if not batch_no:
            continue
        meta = frappe.db.get_value("Batch", batch_no,
                                    ["expiry_date", "sc_blocked"], as_dict=True)
        if not meta:
            filtered.append(b)
            continue
        if meta.sc_blocked:
            continue
        if meta.expiry_date and frappe.utils.getdate(meta.expiry_date) < today_d:
            continue
        b["expiry_date"] = meta.expiry_date
        filtered.append(b)

    # Sort FEFO: expiry ASC, NULL cuối
    filtered.sort(key=lambda x: (x.get("expiry_date") or "9999-12-31"))
    return filtered


def _query_batches_direct(item_code, warehouse):
    rows = frappe.db.sql("""
        SELECT b.name AS batch_no, b.expiry_date,
               COALESCE(SUM(sle.actual_qty), 0) AS qty
        FROM `tabBatch` b
        LEFT JOIN `tabStock Ledger Entry` sle
            ON sle.batch_no = b.name AND sle.warehouse = %s AND sle.is_cancelled = 0
        WHERE b.item = %s AND b.disabled = 0
          AND COALESCE(b.sc_blocked, 0) = 0
        GROUP BY b.name, b.expiry_date
        HAVING qty > 0
        ORDER BY COALESCE(b.expiry_date, '9999-12-31') ASC
    """, (warehouse, item_code), as_dict=True)
    return rows
