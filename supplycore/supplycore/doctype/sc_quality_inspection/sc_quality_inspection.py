"""SC Quality Inspection — UC-10: equipment unavailable + Conditional + Request Replacement."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now


class SCQualityInspection(Document):

    def validate(self):
        # UC-10: equipment unavailable → On Hold
        if self.equipment_unavailable:
            if not (self.equipment_note and str(self.equipment_note).strip()):
                frappe.throw(_(
                    "SC-E-QI-ONHOLD: Phải nhập 'Ghi chú thiết bị' khi đánh dấu thiếu thiết bị"
                ))
            self.overall_status = "On Hold"
            return

        # Auto-derive overall_status từ readings
        if self.readings:
            statuses = [r.status for r in self.readings if r.status]
            if statuses and (not self.overall_status or self.overall_status == "Pending"):
                if any(s == "Rejected" for s in statuses):
                    self.overall_status = "Rejected"
                elif all(s == "Accepted" for s in statuses) and len(statuses) == len(self.readings):
                    self.overall_status = "Accepted"

    def before_submit(self):
        if self.equipment_unavailable:
            return  # On Hold submit OK
        if not self.readings:
            frappe.throw(_("SC-E-QI-READINGS: Phải nhập kết quả cho ít nhất 1 tiêu chí trước khi submit"))
        set_count = sum(1 for r in self.readings if r.status)
        if set_count == 0:
            frappe.throw(_("SC-E-QI-READINGS: Phải nhập kết quả cho ít nhất 1 tiêu chí trước khi submit"))

    def on_submit(self):
        # UC-10: On Hold → skip mọi rollup
        if self.overall_status == "On Hold":
            return

        # Update SC Batch.qc_status
        if self.batch:
            new_qc = "Accepted" if self.overall_status == "Accepted" else (
                "Rejected" if self.overall_status == "Rejected" else "Conditional")
            # Conditional Accept action → override sang Conditional dù overall=Accepted
            if self.overall_status == "Accepted" and self.action_taken == "Conditional Accept":
                new_qc = "Conditional"
            frappe.db.set_value("SC Batch", self.batch, "qc_status", new_qc)

        # Rollup PR.qc_status
        if self.purchase_receipt and frappe.db.exists("SC Purchase Receipt", self.purchase_receipt):
            self._rollup_pr_status()
            if self.overall_status == "Rejected":
                self._handle_rejected()

        # UC-10: Request Replacement → block batch + log
        if self.action_taken == "Request Replacement" and self.batch:
            frappe.db.set_value("SC Batch", self.batch, {
                "blocked": 1,
                "block_reason": f"QI {self.name} Request Replacement: {self.failure_reason or '—'}",
            })

    def _rollup_pr_status(self):
        pr = frappe.get_doc("SC Purchase Receipt", self.purchase_receipt)
        qis = frappe.get_all("SC Quality Inspection",
                              filters={"purchase_receipt": pr.name},
                              fields=["name", "overall_status", "docstatus"])
        # On Hold không tính vào rollup
        submitted = [q for q in qis if q.docstatus == 1 and q.overall_status != "On Hold"]
        expected = len(pr.items)
        if len(submitted) < expected:
            new_status = "Pending"
        elif all(q.overall_status == "Accepted" for q in submitted):
            new_status = "Pass"
        elif all(q.overall_status == "Rejected" for q in submitted):
            new_status = "Fail"
        else:
            new_status = "Partial Pass"
        frappe.db.set_value("SC Purchase Receipt", pr.name, "qc_status", new_status)
        if new_status == "Pass":
            frappe.db.set_value("SC Purchase Receipt", pr.name,
                                 "officially_received_at", now())

    def _handle_rejected(self):
        # 1. Auto block batch
        if self.batch:
            frappe.db.set_value("SC Batch", self.batch, {
                "blocked": 1,
                "block_reason": f"QC Rejected by {self.name}: {self.failure_reason or '—'}",
            })
        # 2. Auto-tạo Return PR draft cho ACC review
        if self.purchase_receipt:
            self._create_return_pr()

    def _create_return_pr(self):
        from frappe.utils import today
        existing = frappe.db.exists("SC Purchase Receipt", {
            "is_return": 1,
            "remarks": ["like", f"%QI {self.name}%"],
            "docstatus": ["!=", 2],
        })
        if existing:
            return
        try:
            orig = frappe.get_doc("SC Purchase Receipt", self.purchase_receipt)
            ret_pr = frappe.new_doc("SC Purchase Receipt")
            ret_pr.supplier = orig.supplier
            ret_pr.purchase_order = orig.purchase_order
            ret_pr.posting_date = today()
            ret_pr.is_return = 1
            ret_pr.to_warehouse = orig.to_warehouse
            ret_pr.qc_required = 0
            ret_pr.remarks = (f"Auto từ QI {self.name} Rejected. "
                              f"Lý do: {self.failure_reason or 'QC Reject'}. "
                              f"Original PR: {orig.name}")
            for it in orig.items:
                if self.pr_item_ref and it.name != self.pr_item_ref:
                    continue
                if it.item != self.item:
                    continue
                ret_pr.append("items", {
                    "item": it.item,
                    "qty": float(self.received_qty or it.qty),
                    "uom": it.uom,
                    "rate": it.rate,
                    "warehouse": it.warehouse or orig.to_warehouse,
                    "batch_no": self.batch,
                })
            if ret_pr.items:
                ret_pr.flags.ignore_permissions = True
                ret_pr.insert()
                frappe.msgprint(
                    frappe._("Đã tạo PR Return draft {0} — ACC review + submit để trả NCC").format(
                        f'<a href="/app/sc-purchase-receipt/{ret_pr.name}">{ret_pr.name}</a>'),
                    indicator="orange", alert=True)
        except Exception as e:
            frappe.log_error(message=str(e)[:1000], title="QI auto-Return PR")


class SCQIReading(Document):
    pass
