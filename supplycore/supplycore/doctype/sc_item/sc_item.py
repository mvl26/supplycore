import frappe
from frappe import _
from frappe.model.document import Document


_THRESHOLD_FIELDS = ("safety_stock", "reorder_level", "max_stock",
                     "standard_order_qty", "lead_time_days")


class SCItem(Document):

    def validate(self):
        if self.has_bhyt and not self.bhyt_code:
            frappe.throw(_("Vật tư có BHYT phải nhập mã BHYT"))
        if self.uom_conversion_factor and self.uom_conversion_factor <= 0:
            frappe.throw(_("uom_conversion_factor phải > 0"))
        # Auto-fill use_uom = stock UOM nếu chưa nhập
        if not self.use_uom:
            self.use_uom = self.uom
        if not self.buy_uom:
            self.buy_uom = self.uom

        self._validate_thresholds()
        self._validate_lead_time()
        self._validate_reorder_rows()

    def _validate_thresholds(self):
        """UC-05: 5 trường ngưỡng và lead_time không được âm."""
        meta = self.meta
        for fld in _THRESHOLD_FIELDS:
            val = self.get(fld) or 0
            if val < 0:
                label = meta.get_label(fld) or fld
                frappe.throw(_("SC-E-NEGATIVE: {0} không được âm").format(label))

    def _validate_lead_time(self):
        # lead_time=0 → warning only (Task 6)
        pass

    def _validate_reorder_rows(self):
        # Per-warehouse rows — Task 5 implements
        pass
