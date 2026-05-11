import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate


class SCBHYTCodeConfig(Document):

    def validate(self):
        if not self.item and not self.item_group:
            frappe.throw(_("Cần chọn `Item` hoặc `Item Group` (ít nhất 1)"))
        if self.payment_rate is not None and (
                flt(self.payment_rate) < 0 or flt(self.payment_rate) > 100):
            frappe.throw(_("SC-E-BHYT-RATE: Tỷ lệ thanh toán phải trong [0..100]"))
        if self.effective_to and getdate(self.effective_to) < getdate(self.effective_from):
            frappe.throw(_("Hết hiệu lực phải sau Hiệu lực từ"))
        self._validate_no_overlap()

    def _validate_no_overlap(self):
        """UC-23: prevent overlapping active configs cùng scope."""
        if not self.is_active:
            return
        if self.item:
            scope_filter = "item = %(item)s"
            params = {"item": self.item}
        else:
            scope_filter = "(item IS NULL OR item = '') AND item_group = %(ig)s"
            params = {"ig": self.item_group}

        eff_to = self.effective_to or "9999-12-31"
        params.update({
            "self_name": self.name or "",
            "ef": self.effective_from,
            "et": eff_to,
        })
        overlap = frappe.db.sql(f"""
            SELECT name, effective_from, effective_to
            FROM `tabSC BHYT Code Config`
            WHERE {scope_filter}
              AND is_active = 1
              AND name != %(self_name)s
              AND effective_from <= %(et)s
              AND COALESCE(effective_to, '9999-12-31') >= %(ef)s
            LIMIT 1
        """, params, as_dict=True)
        if overlap:
            o = overlap[0]
            frappe.throw(_(
                "SC-E-BHYT-OVERLAP: Config trùng scope với {0} ({1}–{2}). "
                "Close bản cũ trước (set effective_to)."
            ).format(o["name"], o["effective_from"], o["effective_to"] or "∞"))
