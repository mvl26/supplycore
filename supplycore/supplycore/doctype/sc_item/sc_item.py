import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


_THRESHOLD_FIELDS = ("safety_stock", "reorder_level", "max_stock",
                     "standard_order_qty", "lead_time_days")


class SCItem(Document):

    def validate(self):
        self._validate_uom_conversions()
        # Auto-fill use_uom = stock UOM nếu chưa nhập
        if not self.use_uom:
            self.use_uom = self.uom
        if not self.buy_uom:
            self.buy_uom = self.uom

        self._validate_thresholds()
        self._validate_lead_time()
        self._validate_reorder_rows()

    def _validate_uom_conversions(self):
        """Bảng quy đổi đơn vị kép: mỗi dòng {uom, conversion_factor} nghĩa
        1 uom = conversion_factor đơn vị tồn kho (uom gốc). Kiểm: hệ số > 0,
        không trùng đơn vị, không trùng chính đơn vị tồn kho (base đã = 1)."""
        seen = set()
        for row in (self.uom_conversions or []):
            if flt(row.conversion_factor) <= 0:
                frappe.throw(_("Hệ số quy đổi của đơn vị {0} phải > 0").format(row.uom or "?"))
            if row.uom == self.uom:
                frappe.throw(_(
                    "Đơn vị {0} trùng đơn vị tồn kho — không cần khai quy đổi (mặc định = 1)."
                ).format(row.uom))
            if row.uom in seen:
                frappe.throw(_("Đơn vị {0} bị khai quy đổi trùng lặp.").format(row.uom))
            seen.add(row.uom)

    def _validate_thresholds(self):
        """UC-05: 5 trường ngưỡng không âm; max_stock>0 → safety ≤ reorder ≤ max."""
        meta = self.meta
        for fld in _THRESHOLD_FIELDS:
            val = self.get(fld) or 0
            if val < 0:
                label = meta.get_label(fld) or fld
                frappe.throw(_("SC-E-NEGATIVE: {0} không được âm").format(label))

        safety = self.safety_stock or 0
        reorder = self.reorder_level or 0
        max_s = self.max_stock or 0
        if max_s > 0 and not (safety <= reorder <= max_s):
            frappe.throw(_(
                "SC-E-MIN-MAX: Phải thỏa Tồn kho an toàn ({0}) ≤ Mức tái đặt hàng ({1}) ≤ Tồn kho tối đa ({2})"
            ).format(safety, reorder, max_s))

    def _validate_lead_time(self):
        """UC-05: lead_time=0 → msgprint warning màu cam, không throw."""
        if self.lead_time_days is not None and self.lead_time_days == 0:
            frappe.msgprint(
                _("Lead time = 0 — nên cập nhật giá trị > 0"),
                indicator="orange", alert=True,
            )

    def _validate_reorder_rows(self):
        """UC-05: per-warehouse override rows. Warehouse unique trong table;
        mỗi row có max_stock>0 phải thỏa safety ≤ reorder ≤ max."""
        seen = set()
        for row in (self.get("reorder_levels") or []):
            if not row.warehouse:
                continue
            if row.warehouse in seen:
                frappe.throw(_(
                    "SC-E-DUPLICATE-WAREHOUSE: Kho {0} đã có override — không trùng"
                ).format(row.warehouse))
            seen.add(row.warehouse)

            for fld in ("safety_stock", "reorder_level",
                        "max_stock", "standard_order_qty"):
                val = row.get(fld) or 0
                if val < 0:
                    frappe.throw(_(
                        "SC-E-NEGATIVE: row {0}.{1} không được âm"
                    ).format(row.warehouse, fld))

            safety = row.safety_stock or 0
            reorder = row.reorder_level or 0
            max_s = row.max_stock or 0
            if max_s > 0 and not (safety <= reorder <= max_s):
                frappe.throw(_(
                    "SC-E-MIN-MAX: Row kho {0} — Safety ({1}) ≤ Reorder ({2}) ≤ Max ({3})"
                ).format(row.warehouse, safety, reorder, max_s))
