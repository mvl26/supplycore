"""Bin Location — vị trí vật lý chi tiết trong Warehouse (M4 / UC-12)."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, now


class BinLocation(Document):

    def validate(self):
        self._ensure_barcode()
        if self.temperature_controlled:
            if self.min_temperature is not None and self.max_temperature is not None:
                if self.max_temperature <= self.min_temperature:
                    frappe.throw(_("Nhiệt độ max phải lớn hơn min"))

    def _ensure_barcode(self):
        """Tự sinh barcode = bin_code khi tạo vị trí (nếu chưa có).

        User vẫn có thể đè bằng mã GS1 riêng.
        """
        if not self.barcode and self.bin_code:
            self.barcode = self.bin_code

    def on_trash(self):
        """UC-12 ngoại lệ: không cho xóa bin đang có hàng."""
        qty = flt(frappe.db.sql("""
            SELECT COALESCE(SUM(qty_change), 0)
            FROM `tabSC Stock Ledger Entry`
            WHERE bin_location = %s AND is_cancelled = 0
        """, self.name)[0][0])
        if qty > 0.001:
            frappe.throw(_(
                "SC-E-BIN-NOT-EMPTY: Bin {0} đang có {1} đơn vị — chuyển hàng trước khi xóa"
            ).format(self.bin_code, qty))

    @frappe.whitelist()
    def recompute_occupancy(self):
        """UC-12 bước 5: tính current_qty + occupancy_pct + status."""
        qty = flt(frappe.db.sql("""
            SELECT COALESCE(SUM(qty_change), 0)
            FROM `tabSC Stock Ledger Entry`
            WHERE bin_location = %s AND is_cancelled = 0
        """, self.name)[0][0])
        cap = flt(self.capacity_qty)
        pct = (qty / cap * 100) if cap > 0 else 0
        if qty <= 0.001:
            st = "Empty"
        elif cap > 0 and pct >= 95:
            st = "Full"
        else:
            st = "In Use"
        self.db_set("current_qty", qty)
        self.db_set("occupancy_pct", pct)
        self.db_set("status", st)
        self.db_set("last_recomputed_at", now())
        return {"current_qty": qty, "occupancy_pct": pct, "status": st}

    @frappe.whitelist()
    def get_barcode_label_data(self):
        """UC-12 bước 6: trả data để in nhãn barcode qua Frappe Print Format."""
        return {
            "barcode": self.barcode or self.name,
            "bin_code": self.bin_code,
            "warehouse": self.warehouse,
            "zone": self.zone,
            "rack": self.rack,
            "shelf": self.shelf,
            "level": self.level,
            "capacity_qty": self.capacity_qty,
            "capacity_uom": self.capacity_uom,
            "url": f"/app/bin-location/{self.name}",
        }

    @frappe.whitelist()
    def get_current_inventory(self):
        """Trả về items hiện ở bin này từ SC SLE (recompute kèm)."""
        return frappe.db.sql("""
            SELECT sle.item, i.item_name, sle.batch,
                   SUM(sle.qty_change) AS net_qty
            FROM `tabSC Stock Ledger Entry` sle
            JOIN `tabSC Item` i ON i.name = sle.item
            WHERE sle.bin_location = %s AND sle.is_cancelled = 0
            GROUP BY sle.item, sle.batch
            HAVING net_qty > 0
            ORDER BY sle.item
        """, self.name, as_dict=True)
