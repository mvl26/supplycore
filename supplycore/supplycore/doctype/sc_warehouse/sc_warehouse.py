import frappe
from frappe import _
from frappe.utils.nestedset import NestedSet


class SCWarehouse(NestedSet):
    nsm_parent_field = "parent_warehouse"

    def validate(self):
        # Department type bắt buộc có department link
        if self.warehouse_type == "Department" and not self.department:
            frappe.throw(_("Kho khoa phòng phải có liên kết SC Department"))
        # Group warehouse không được có stock — kiểm tra ở SLE
        if self.is_group and not self.flags.allow_group_with_stock:
            stock_exists = frappe.db.exists("SC Stock Ledger Entry", {"warehouse": self.name})
            if stock_exists:
                frappe.throw(_("Kho {0} đã có giao dịch SLE — không thể đặt là is_group").format(self.name))
