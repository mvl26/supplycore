import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate


class SCBHYTCodeConfig(Document):
    def validate(self):
        if not self.item and not self.item_group:
            frappe.throw(_("Cần chọn `Item` hoặc `Item Group` (ít nhất 1)"))
        if self.payment_rate is not None and (flt(self.payment_rate) < 0 or flt(self.payment_rate) > 100):
            frappe.throw(_("Tỷ lệ thanh toán phải trong [0..100]"))
        if self.effective_to and getdate(self.effective_to) < getdate(self.effective_from):
            frappe.throw(_("Hết hiệu lực phải sau Hiệu lực từ"))
