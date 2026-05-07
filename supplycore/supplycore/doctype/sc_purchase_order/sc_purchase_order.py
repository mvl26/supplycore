"""SC Purchase Order — replaces ERPNext PO. Hooks vào FC remaining_value (M1)."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class SCPurchaseOrder(Document):
    def validate(self):
        self._compute_totals()
        self._validate_supplier()
        self._validate_against_framework_contract()
        if self.docstatus == 0:
            self.status = "Draft"

    def on_submit(self):
        self.db_set("status", "Approved")
        self._update_framework_contract()

    def on_cancel(self):
        self.db_set("status", "Cancelled")
        self._update_framework_contract()

    def _compute_totals(self):
        total_qty = 0; total = 0
        for r in self.items:
            r.amount = flt(r.qty) * flt(r.rate)
            total_qty += flt(r.qty); total += flt(r.amount)
        self.total_qty = total_qty
        self.grand_total = total

    def _validate_supplier(self):
        s = frappe.db.get_value("SC Supplier", self.supplier, ["disabled", "blacklist_flag"], as_dict=True)
        if s and s.disabled:
            frappe.throw(_("NCC {0} đang disabled").format(self.supplier))
        if s and s.blacklist_flag and self.docstatus == 0:
            frappe.msgprint(_("⚠ NCC này trong blacklist — cần xác nhận lãnh đạo"),
                             indicator="orange", alert=True)

    def _validate_against_framework_contract(self):
        if not self.framework_contract:
            return
        fc = frappe.db.get_value("Framework Contract", self.framework_contract,
                                  ["docstatus", "status", "remaining_value", "valid_to"], as_dict=True)
        if not fc:
            return
        if fc.docstatus != 1 or fc.status != "Active":
            frappe.throw(_("HĐK {0} không Active").format(self.framework_contract),
                         title="SC-E002 FC_INACTIVE")
        if flt(self.grand_total) > flt(fc.remaining_value):
            frappe.throw(_("Tổng PO ({0}) vượt hạn mức HĐK còn lại ({1})").format(
                frappe.format(self.grand_total, {"fieldtype": "Currency"}),
                frappe.format(fc.remaining_value, {"fieldtype": "Currency"})),
                title="SC-E002 FC_EXCEEDED")

    def _update_framework_contract(self):
        if not self.framework_contract:
            return
        try:
            fc = frappe.get_doc("Framework Contract", self.framework_contract)
            fc.recalculate_used_value()
        except Exception:
            pass
        if self.release_order and frappe.db.exists("Release Order", self.release_order):
            new_status = "Converted" if self.docstatus == 1 else "Approved"
            frappe.db.set_value("Release Order", self.release_order, {
                "purchase_order": self.name if self.docstatus == 1 else None,
                "status": new_status,
            })
