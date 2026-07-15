"""GĐ MVL — backfill trạng thái nhập kho cho SC Purchase Receipt cũ (2 bước).

Trước thay đổi: PR submit ghi SLE ngay. Nay tách 2 bước (Đã tiếp nhận → Đã nhập
kho). Mọi PR đã submit TRƯỚC thay đổi đã có SLE = coi như ĐÃ NHẬP KHO.

Backfill (idempotent, chỉ set khi receipt_status trống):
- phiếu THƯỜNG đã submit (docstatus=1, is_return=0) → receipt_status="Đã nhập kho",
  confirmed_by=Administrator, warehouse_in_date=officially_received_at=posting_date cũ.
- phiếu TRẢ (is_return=1): không thuộc luồng 2 bước, bỏ qua.

TUYỆT ĐỐI KHÔNG post/đụng SC Stock Ledger Entry — tồn hiện tại giữ nguyên từng số.
Rollback: đặt receipt_status/confirmed_by/warehouse_in_date về NULL cho các phiếu này
(không đụng SLE). Xem CHANGELOG.
"""

import frappe


def execute():
    # Đảm bảo cột mới (receipt_status/confirmed_by/warehouse_in_date) đã có trong
    # DB trước khi query — patch có thể chạy trước bước sync doctype.
    frappe.reload_doctype("SC Purchase Receipt")

    rows = frappe.db.sql("""
        SELECT name, posting_date, officially_received_at
        FROM `tabSC Purchase Receipt`
        WHERE docstatus = 1 AND IFNULL(is_return,0) = 0
          AND (receipt_status IS NULL OR receipt_status = '')
    """, as_dict=True)
    n = 0
    for r in rows:
        frappe.db.set_value("SC Purchase Receipt", r.name, {
            "receipt_status": "Đã nhập kho",
            "confirmed_by": "Administrator",
            "warehouse_in_date": r.posting_date,
            "officially_received_at": r.officially_received_at or r.posting_date,
        }, update_modified=False)
        n += 1
    if n:
        frappe.db.commit()
    print(f"  ✓ backfill PR warehouse-in: {n} phiếu tiếp nhận (đã có SLE) -> 'Đã nhập kho' (KHÔNG đụng tồn)")
