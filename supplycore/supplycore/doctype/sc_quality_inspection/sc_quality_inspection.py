"""SC Quality Inspection — replaces ERPNext QI."""

import frappe
from frappe import _
from frappe.model.document import Document


class SCQualityInspection(Document):
    def validate(self):
        # Auto-derive overall_status from readings if not set manually
        if self.readings:
            statuses = [r.status for r in self.readings if r.status]
            if statuses and not self.overall_status or self.overall_status == "Pending":
                if any(s == "Rejected" for s in statuses):
                    self.overall_status = "Rejected"
                elif all(s == "Accepted" for s in statuses) and len(statuses) == len(self.readings):
                    self.overall_status = "Accepted"

    def on_submit(self):
        # Update SC Batch.qc_status
        if self.batch:
            new_qc = "Accepted" if self.overall_status == "Accepted" else (
                "Rejected" if self.overall_status == "Rejected" else "Conditional")
            frappe.db.set_value("SC Batch", self.batch, "qc_status", new_qc)

        # Update PR.qc_status rollup
        if self.purchase_receipt and frappe.db.exists("SC Purchase Receipt", self.purchase_receipt):
            self._rollup_pr_status()
            if self.overall_status == "Rejected":
                self._handle_rejected()

    def _rollup_pr_status(self):
        pr = frappe.get_doc("SC Purchase Receipt", self.purchase_receipt)
        qis = frappe.get_all("SC Quality Inspection",
                              filters={"purchase_receipt": pr.name},
                              fields=["name", "overall_status", "docstatus"])
        submitted = [q for q in qis if q.docstatus == 1]
        if len(submitted) < len(pr.items):
            new_status = "Pending"
        elif all(q.overall_status == "Accepted" for q in submitted):
            new_status = "Pass"
        elif all(q.overall_status == "Rejected" for q in submitted):
            new_status = "Fail"
        else:
            new_status = "Partial Pass"
        frappe.db.set_value("SC Purchase Receipt", pr.name, "qc_status", new_status)

    def _handle_rejected(self):
        # Auto block batch nếu reject
        if self.batch:
            frappe.db.set_value("SC Batch", self.batch, {
                "blocked": 1,
                "block_reason": f"QC Rejected by {self.name}: {self.failure_reason or '—'}",
            })
        # TODO: tạo SC Purchase Receipt is_return=1 draft (defer)


class SCQIReading(Document): pass
