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
        # 1. Auto block batch
        if self.batch:
            frappe.db.set_value("SC Batch", self.batch, {
                "blocked": 1,
                "block_reason": f"QC Rejected by {self.name}: {self.failure_reason or '—'}",
            })
        # 2. Auto-tạo SC Purchase Receipt Return (draft) cho ACC review + gửi NCC (UC-11)
        if self.purchase_receipt:
            self._create_return_pr()

    def _create_return_pr(self):
        """Tạo PR Return draft (is_return=1) khi QI Reject — implement UC-11."""
        from frappe.utils import today
        # Skip nếu đã có PR Return draft cho QI này
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
            ret_pr.to_warehouse = orig.to_warehouse  # kho gốc — sẽ -qty
            ret_pr.qc_required = 0  # return không cần QC lại
            ret_pr.remarks = (f"Auto từ QI {self.name} Rejected. "
                              f"Lý do: {self.failure_reason or 'QC Reject'}. "
                              f"Original PR: {orig.name}")
            # Append item rejected: chỉ row tương ứng pr_item_ref nếu có, else cả row
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


class SCQIReading(Document): pass
