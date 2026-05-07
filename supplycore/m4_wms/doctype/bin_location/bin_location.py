"""Bin Location — vị trí vật lý chi tiết trong Warehouse (M4)."""

import frappe
from frappe import _
from frappe.model.document import Document


class BinLocation(Document):

    def validate(self):
        if self.temperature_controlled:
            if self.min_temperature is not None and self.max_temperature is not None:
                if self.max_temperature <= self.min_temperature:
                    frappe.throw(_("Nhiệt độ max phải lớn hơn min"))

    def on_trash(self):
        """Không cho xóa bin đang có hàng (TechSpec §M4)."""
        used = frappe.db.count("Stock Entry Detail",
                               filters={"sc_target_bin": self.name})
        if used:
            frappe.throw(_("Bin {0} đang có {1} giao dịch — không thể xóa")
                         .format(self.name, used))

    @frappe.whitelist()
    def get_current_inventory(self):
        """Trả về items hiện ở bin này (best-effort từ Stock Entry Detail submitted)."""
        return frappe.db.sql("""
            SELECT sed.item_code, i.item_name,
                   SUM(CASE WHEN sed.sc_target_bin = %(bin)s THEN sed.qty ELSE 0 END)
                   - SUM(CASE WHEN sed.sc_source_bin = %(bin)s THEN sed.qty ELSE 0 END) AS net_qty,
                   sed.uom, sed.batch_no
            FROM `tabSC Stock Entry Item` sed
            JOIN `tabSC Stock Entry` se ON se.name = sed.parent
            JOIN `tabSC Item` i ON i.name = sed.item_code
            WHERE (sed.sc_target_bin = %(bin)s OR sed.sc_source_bin = %(bin)s)
              AND se.docstatus = 1
            GROUP BY sed.item_code, sed.uom, sed.batch_no
            HAVING net_qty > 0
            ORDER BY sed.item_code
        """, {"bin": self.name}, as_dict=True)
