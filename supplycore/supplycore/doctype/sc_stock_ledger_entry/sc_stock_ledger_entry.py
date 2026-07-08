"""SC Stock Ledger Entry — immutable transaction log.

KHÔNG sửa/xóa trực tiếp. Chỉ tạo qua submit của SC Stock Entry / SC Purchase Receipt.
Cancel được thực hiện bằng cách chèn row đối ứng (qty_change đảo dấu), APPEND-ONLY:
KHÔNG set is_cancelled trên dòng gốc. get_qty/get_available_qty SUM(qty_change)
WHERE is_cancelled=0 — nếu vừa loại dòng gốc vừa cộng dòng đối ứng sẽ đảo KÉP
(double-reversal bug). Giữ cả 2 dòng is_cancelled=0 để tự triệt tiêu về đúng số dư.
"""

import frappe
from frappe import _
from frappe.model.document import Document


class SCStockLedgerEntry(Document):

    def on_change(self):
        """Block sửa SLE — chỉ admin được phép qua flag.allow_sle_edit."""
        if not self.flags.allow_sle_edit and not self.is_new():
            frappe.throw(_("SC Stock Ledger Entry là immutable — không được sửa trực tiếp"))

    @staticmethod
    def post(item, warehouse, qty_change, voucher_type, voucher_no, *,
             batch=None, bin_location=None, valuation_rate=0,
             posting_date=None, posting_time=None, voucher_detail_no=None,
             remarks=None):
        """Helper: tạo SLE mới + tính balance_qty từ ledger trước đó."""
        from frappe.utils import flt, today, nowtime
        previous = frappe.db.sql("""
            SELECT COALESCE(SUM(qty_change), 0)
            FROM `tabSC Stock Ledger Entry`
            WHERE item = %s AND warehouse = %s
              AND COALESCE(batch, '') = COALESCE(%s, '')
              AND is_cancelled = 0
        """, (item, warehouse, batch))[0][0]
        new_balance = flt(previous) + flt(qty_change)

        sle = frappe.new_doc("SC Stock Ledger Entry")
        sle.posting_date = posting_date or today()
        sle.posting_time = posting_time or nowtime()
        sle.voucher_type = voucher_type
        sle.voucher_no = voucher_no
        sle.voucher_detail_no = voucher_detail_no
        sle.item = item
        sle.warehouse = warehouse
        sle.batch = batch
        sle.bin_location = bin_location
        sle.qty_change = flt(qty_change)
        sle.balance_qty = new_balance
        sle.valuation_rate = flt(valuation_rate)
        sle.stock_value = new_balance * flt(valuation_rate)
        sle.stock_value_difference = flt(qty_change) * flt(valuation_rate)
        sle.remarks = remarks
        sle.flags.allow_sle_edit = True
        sle.insert(ignore_permissions=True)
        # QAv3-BUG-BIN-05: update Bin Location.current_qty + status sau mỗi SLE
        if bin_location:
            _refresh_bin_status(bin_location)
        return sle.name

    @staticmethod
    def get_qty(item, warehouse, batch=None) -> float:
        """Query tồn kho TỔNG của item+warehouse (+ batch optional).

        TỔNG ở đây = mọi SLE (kể cả batch QC Pending). Dùng cho báo cáo
        kế toán / kiểm kê — cần đối chiếu vật lý. Để check "có xuất kho
        được không" → dùng get_available_qty() (loại trừ Pending/Rejected).
        """
        from frappe.utils import flt
        sql = """
            SELECT COALESCE(SUM(qty_change), 0)
            FROM `tabSC Stock Ledger Entry`
            WHERE item = %s AND warehouse = %s AND is_cancelled = 0
        """
        params = [item, warehouse]
        if batch is not None:
            sql += " AND batch = %s"
            params.append(batch)
        return flt(frappe.db.sql(sql, tuple(params))[0][0])

    @staticmethod
    def get_available_qty(item, warehouse, batch=None) -> float:
        """BUG-002: tồn kho KHẢ DỤNG — loại trừ batch QC Pending/Rejected.

        Dùng cho mọi nghiệp vụ xuất kho (Material Issue/Transfer).
        Lô chưa qua QC (Pending) hoặc fail QC (Rejected) KHÔNG được xuất kho.

        Logic: JOIN SC Batch on qc_status. SLE không có batch (item chưa
        track lô) coi như available luôn — vì chỉ batch-tracked item mới
        cần QC enforcement.
        """
        from frappe.utils import flt
        sql = """
            SELECT COALESCE(SUM(sle.qty_change), 0)
            FROM `tabSC Stock Ledger Entry` sle
            LEFT JOIN `tabSC Batch` b ON b.name = sle.batch
            WHERE sle.item = %s AND sle.warehouse = %s AND sle.is_cancelled = 0
              AND (sle.batch IS NULL OR sle.batch = ''
                   OR b.qc_status NOT IN ('Pending', 'Rejected'))
              AND (b.blocked IS NULL OR b.blocked = 0)
        """
        params = [item, warehouse]
        if batch is not None:
            sql += " AND sle.batch = %s"
            params.append(batch)
        return flt(frappe.db.sql(sql, tuple(params))[0][0])


def _refresh_bin_status(bin_location: str):
    """QAv3-BUG-BIN-05: tính lại current_qty + status của Bin Location.

    Gọi sau mỗi SLE post. current_qty = Σ qty_change của SLE tại bin này.
    status:
      - Empty:   current_qty <= 0
      - Full:    current_qty >= capacity_qty (nếu có capacity)
      - In Use:  > 0 và < capacity (hoặc capacity không set)
    """
    from frappe.utils import flt
    if not bin_location or not frappe.db.exists("Bin Location", bin_location):
        return
    current = flt(frappe.db.sql("""
        SELECT COALESCE(SUM(qty_change), 0)
        FROM `tabSC Stock Ledger Entry`
        WHERE bin_location = %s AND is_cancelled = 0
    """, bin_location)[0][0])
    capacity = flt(frappe.db.get_value("Bin Location", bin_location, "capacity_qty"))
    if current <= 0:
        status = "Empty"
    elif capacity > 0 and current >= capacity:
        status = "Full"
    else:
        status = "In Use"
    occupancy_pct = (current / capacity * 100) if capacity > 0 else 0
    frappe.db.set_value("Bin Location", bin_location, {
        "current_qty": current,
        "status": status,
        "occupancy_pct": occupancy_pct,
    }, update_modified=False)
