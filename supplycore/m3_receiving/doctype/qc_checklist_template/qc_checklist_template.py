import frappe
from frappe import _
from frappe.model.document import Document


class QCChecklistTemplate(Document):

    def validate(self):
        if self.is_default_for_group and not self.item_group:
            frappe.throw(_("Phải chọn Item Group nếu đặt 'Mặc định cho nhóm'"))
        # Chỉ 1 template default mỗi item_group
        if self.is_default_for_group and self.item_group:
            existing = frappe.db.get_value(
                "QC Checklist Template",
                {
                    "item_group": self.item_group,
                    "is_default_for_group": 1,
                    "enabled": 1,
                    "name": ["!=", self.name],
                },
                "name",
            )
            if existing:
                frappe.throw(_("Đã có template default cho nhóm {0}: {1}").format(
                    self.item_group, existing))
