"""SC Stock Ledger Entry — immutable transaction log.

KHÔNG sửa/xóa trực tiếp. Chỉ tạo qua submit của SC Stock Entry / SC Purchase Receipt.
Cancel được thực hiện bằng cách chèn row đối ứng (qty_change đảo dấu) + set is_cancelled.
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
        return sle.name

    @staticmethod
    def get_qty(item, warehouse, batch=None) -> float:
        """Query tồn kho hiện tại của item+warehouse (+ batch optional)."""
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
