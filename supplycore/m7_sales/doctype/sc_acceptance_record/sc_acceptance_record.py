"""SC Acceptance Record -- biên bản nghiệm thu giao hàng (M7 Sales, GĐ2 Task 6).

Business rule: chỉ được lập nghiệm thu cho Phiếu giao hàng (SC Delivery Note) đã
ở trạng thái "Đã giao" (đã submit) -- nếu chưa, validate() throw.

Submit: đặt status "Đã nghiệm thu"; cập nhật delivery_note.status = "Đã nghiệm
thu" và delivery_note.acceptance_ref = tên biên bản này -- mở khóa cho phép xuất
hóa đơn bán hàng (SC Sales Invoice).
Cancel: trả delivery_note.status về "Đã giao" và xóa acceptance_ref.
"""

import frappe
from frappe import _
from frappe.model.document import Document


class SCAcceptanceRecord(Document):

    def validate(self):
        self._check_dn_status()

    def on_submit(self):
        self.db_set("status", "Đã nghiệm thu")
        if self.delivery_note:
            frappe.db.set_value("SC Delivery Note", self.delivery_note, {
                "status": "Đã nghiệm thu",
                "acceptance_ref": self.name,
            })

    def on_cancel(self):
        if self.delivery_note:
            frappe.db.set_value("SC Delivery Note", self.delivery_note, {
                "status": "Đã giao",
                "acceptance_ref": None,
            })

    # ------------------------------------------------------------------
    def _check_dn_status(self):
        if not self.delivery_note:
            return
        dn_status, dn_acceptance_ref = frappe.db.get_value(
            "SC Delivery Note", self.delivery_note, ["status", "acceptance_ref"]
        )
        if dn_status == "Đã giao":
            return
        # Cho phép re-validate khi chính biên bản này đã là acceptance_ref của DN
        # (vd. DN đã ở "Đã nghiệm thu" do chính AR này submit trước đó).
        if dn_acceptance_ref and dn_acceptance_ref == self.name:
            return
        frappe.throw(_(
            "Phiếu giao hàng {0} chưa ở trạng thái 'Đã giao' (hiện tại: {1}) — "
            "chỉ có thể lập biên bản nghiệm thu cho phiếu giao hàng đã giao."
        ).format(self.delivery_note, dn_status), title="Nghiệm thu không hợp lệ")
