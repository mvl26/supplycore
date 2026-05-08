"""SC Purchase Order — replaces ERPNext PO. Hooks vào FC remaining_value (M1)."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, today


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
        from supplycore.utils.validators import validate_supplier
        s = validate_supplier(self.supplier)
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

    @frappe.whitelist()
    def make_purchase_receipt(self):
        """Wrapper instance method — gọi từ JS frm.call('make_purchase_receipt')."""
        return make_pr_from_po(self.name)


@frappe.whitelist()
def make_pr_from_po(po_name: str) -> str:
    """Tạo SC Purchase Receipt draft từ PO submitted, fetch info tự động.

    Quy tắc:
    - PO phải docstatus=1 (submitted)
    - PO chưa fully Received (status != "Received")
    - Mỗi PO item có (qty - received_qty) > 0 → append vào PR items với
      qty = remaining, rate/uom/warehouse fetch từ PO item
    - to_warehouse = warehouse của PO item đầu tiên còn chưa nhận
    - has_batch_no item: KHÔNG pre-fill batch — user nhập khi nhận thực tế

    Returns: tên SC Purchase Receipt draft.
    """
    po = frappe.get_doc("SC Purchase Order", po_name)
    if po.docstatus != 1:
        frappe.throw(_("PO chưa submit"), title="SC-E-PO")
    if po.status == "Received":
        frappe.throw(_("PO {0} đã nhận đủ — không tạo PR mới").format(po.name),
                      title="SC-E-PO-RECEIVED")

    pending = []
    for poi in po.items:
        remaining = flt(poi.qty) - flt(poi.received_qty or 0)
        if remaining > 0:
            pending.append((poi, remaining))
    if not pending:
        frappe.throw(_("Không còn item nào chưa nhận trên PO {0}").format(po.name),
                      title="SC-E-PO-RECEIVED")

    first_wh = pending[0][0].warehouse
    pr = frappe.new_doc("SC Purchase Receipt")
    pr.supplier = po.supplier
    pr.purchase_order = po.name
    pr.posting_date = today()
    pr.to_warehouse = first_wh
    pr.qc_required = 1  # default — user có thể tắt nếu không cần QC
    pr.remarks = f"Auto từ PO {po.name}"
    for poi, remaining in pending:
        pr.append("items", {
            "item": poi.item,
            "qty": remaining,
            "uom": poi.uom,
            "rate": flt(poi.rate),
            "warehouse": poi.warehouse or first_wh,
        })
    pr.flags.ignore_permissions = True
    pr.insert()
    return pr.name
