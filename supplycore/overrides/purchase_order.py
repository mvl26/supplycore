"""Hook lifecycle vào ERPNext Purchase Order — tích hợp với M1 Framework Contract."""

import frappe
from frappe import _
from frappe.utils import flt


def validate(doc, method=None):
    """validate: nếu PO link Framework Contract thì kiểm tra hạn mức + giá trùng HĐK."""
    fc_name = doc.get("sc_framework_contract")
    if not fc_name:
        return

    fc = frappe.get_doc("Framework Contract", fc_name)

    if fc.docstatus != 1 or fc.status != "Active":
        frappe.throw(_("Hợp đồng khung {0} không ở trạng thái Active").format(fc_name),
                     title="SC-E002 FC_INACTIVE")

    # Kiểm tra hạn mức tổng
    fc_remaining = flt(fc.remaining_value)
    if flt(doc.grand_total) > fc_remaining:
        frappe.throw(
            _("Tổng PO ({0}) vượt hạn mức còn lại của HĐK ({1})").format(
                frappe.format(doc.grand_total, {"fieldtype": "Currency"}),
                frappe.format(fc_remaining, {"fieldtype": "Currency"})),
            title="SC-E002 FC_EXCEEDED")

    # Kiểm tra giá từng item khớp HĐK (cảnh báo nếu lệch)
    fc_prices = {r.item_code: flt(r.unit_price) for r in fc.items}
    for row in doc.items:
        if row.item_code in fc_prices:
            fc_price = fc_prices[row.item_code]
            if abs(flt(row.rate) - fc_price) > 1:  # tolerance 1 VND
                frappe.msgprint(
                    _("Giá {0} ({1}) khác giá HĐK ({2})").format(
                        row.item_code, row.rate, fc_price),
                    indicator="orange", alert=True)


def on_submit(doc, method=None):
    """on_submit: cập nhật used_value của HĐK + status của RO liên quan."""
    fc_name = doc.get("sc_framework_contract")
    if fc_name:
        fc = frappe.get_doc("Framework Contract", fc_name)
        fc.recalculate_used_value()

    ro_name = doc.get("sc_release_order")
    if ro_name and frappe.db.exists("Release Order", ro_name):
        frappe.db.set_value("Release Order", ro_name, {
            "purchase_order": doc.name,
            "status": "Converted",
        })


def on_cancel(doc, method=None):
    """on_cancel: trừ ngược used_value + revert RO status nếu có."""
    fc_name = doc.get("sc_framework_contract")
    if fc_name:
        fc = frappe.get_doc("Framework Contract", fc_name)
        fc.recalculate_used_value()

    ro_name = doc.get("sc_release_order")
    if ro_name and frappe.db.exists("Release Order", ro_name):
        frappe.db.set_value("Release Order", ro_name, {
            "purchase_order": None,
            "status": "Approved",
        })
