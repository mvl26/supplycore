"""SC Quality Inspection — UC-10: equipment unavailable + Conditional + Request Replacement."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now


# Kết quả "đã kết luận" — áp hiệu lực KCS (block lô / rollup PR / Return PR).
# On Hold & Pending KHÔNG nằm đây (chỉ lưu, chưa áp).
FINALIZED_STATUSES = ("Accepted", "Rejected", "Conditional")


class SCQualityInspection(Document):

    def validate(self):
        # Bỏ bước "Gửi duyệt" (submit) — phiếu QC chỉ Lưu là áp kết quả. Vì không
        # còn immutability của submit, khoá phiếu sau khi đã kết luận (mirror
        # FrameworkContract._guard_locked_after_approval) để không thể sửa kết quả
        # đã áp → tránh lô kẹt 'blocked' + Return PR mồ côi.
        self._guard_locked_after_finalize()
        # L20/T06: QC KHÔNG được sửa dữ liệu phiếu nhập. Khoá UI (read_only) chỉ
        # là gợi ý client; ở đây ép lại item/lô/SL nhận theo đúng dòng phiếu nhập
        # gốc (pr_item_ref) — defense-in-depth, dù POST thẳng cũng snap về nguồn.
        self._sync_from_receipt()
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

        # Khi đã kết luận (terminal) → ràng buộc đầy đủ như before_submit cũ
        if self.overall_status in FINALIZED_STATUSES:
            self._validate_finalize()

    def _guard_locked_after_finalize(self):
        """Khoá sửa khi QC đã kết luận (overall_status terminal đã lưu).

        Bypass: is_new() (đang tạo) hoặc flags.allow_edit_after_finalize (code nội bộ).
        """
        if self.is_new():
            return
        stored = frappe.db.get_value("SC Quality Inspection", self.name, "overall_status")
        if stored in FINALIZED_STATUSES and not self.flags.get("allow_edit_after_finalize"):
            frappe.throw(_(
                "SC-E034 QC_LOCKED: Phiếu QC đã kết luận ({0}) — không cho sửa. "
                "Kết quả KCS đã được áp vào lô/phiếu nhập."
            ).format(stored), title="SC-E034 QC_LOCKED")

    def _validate_finalize(self):
        """Ràng buộc khi kết luận QC (trước đây ở before_submit)."""
        # L19: người KẾT LUẬN QC chính là 'người kiểm' — ghi đè theo tài khoản
        # đang lưu, không cho gán hộ người khác (field cũng read-only ở UI).
        if frappe.session.user not in (None, "Guest"):
            self.inspected_by = frappe.session.user
        # Đã bỏ QC Checklist Template: KCS điền trực tiếp ≥1 tiêu chí có kết quả.
        if not self.readings or sum(1 for r in self.readings if r.status) == 0:
            frappe.throw(_(
                "SC-E-QI-READINGS: Phải nhập kết quả cho ít nhất 1 tiêu chí trước khi kết luận QC"))
        self._validate_result_action()

    def _sync_from_receipt(self):
        """L20/T06: ép item / lô / SL nhận theo dòng phiếu nhập gốc (read-only thật
        ở backend). Bỏ qua nếu là phiếu QC tạo tay không gắn dòng PR."""
        if not (self.purchase_receipt and self.pr_item_ref):
            return
        pri = frappe.db.get_value(
            "SC Purchase Receipt Item", self.pr_item_ref,
            ["item", "batch_no", "qty", "parent"], as_dict=True)
        if not pri or pri.parent != self.purchase_receipt:
            return
        self.item = pri.item
        if pri.batch_no:
            self.batch = pri.batch_no
        self.received_qty = pri.qty
        # F10: gắn mắt xích truy xuất PO/HĐK/YCMH (read-only) từ phiếu nhập
        po = frappe.db.get_value("SC Purchase Receipt", self.purchase_receipt, "purchase_order")
        if po:
            self.purchase_order = po
            fc, mr = frappe.db.get_value(
                "SC Purchase Order", po, ["framework_contract", "material_request"]) or (None, None)
            self.framework_contract = fc
            self.material_request = mr

    def _validate_result_action(self):
        """L17: chặn cặp Kết quả ↔ Hành động mâu thuẫn.
        Cho phép Conditional Accept khi Đạt (luồng có điều kiện), nhưng:
        - Đạt KHÔNG được Trả NCC / Yêu cầu thay thế.
        - Không đạt KHÔNG được Chấp nhận / Chấp nhận có điều kiện."""
        action = self.action_taken
        if not action or action == "Pending":
            return
        accept_actions = ("Accept", "Conditional Accept")
        reject_actions = ("Return to Supplier", "Request Replacement")
        conflict = (
            (self.overall_status == "Accepted" and action in reject_actions) or
            (self.overall_status == "Rejected" and action in accept_actions)
        )
        if conflict:
            frappe.throw(_(
                "SC-E032 QC_RESULT_ACTION_CONFLICT: Kết quả '{0}' mâu thuẫn với "
                "hành động '{1}'. Đạt → chỉ Chấp nhận / Chấp nhận có điều kiện; "
                "Không đạt → chỉ Trả NCC / Yêu cầu thay thế."
            ).format(self.overall_status, action), title="SC-E032 QC_RESULT_ACTION_CONFLICT")

    def on_update(self):
        # "Gửi duyệt" đã bỏ — Lưu phiếu QC là áp kết quả KCS (thay cho on_submit cũ).
        # Chỉ áp khi ĐÃ kết luận (terminal); Pending/On Hold chỉ lưu, chưa áp.
        # Doc bị khoá sau khi terminal (_guard_locked_after_finalize) nên thực tế
        # _apply_qc_result chạy đúng 1 lần — ở lần lưu kết luận.
        if self.overall_status not in FINALIZED_STATUSES:
            return
        self._apply_qc_result()

    def _apply_qc_result(self):
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
                              fields=["name", "overall_status"])
        # Chỉ tính QC đã KẾT LUẬN (Pending/On Hold không vào rollup)
        finalized = [q for q in qis if q.overall_status in FINALIZED_STATUSES]
        expected = len(pr.items)
        if len(finalized) < expected:
            new_status = "Pending"
        elif all(q.overall_status == "Accepted" for q in finalized):
            new_status = "Pass"
        elif all(q.overall_status == "Rejected" for q in finalized):
            new_status = "Fail"
        else:
            new_status = "Partial Pass"
        frappe.db.set_value("SC Purchase Receipt", pr.name, "qc_status", new_status)
        if new_status == "Pass" and not pr.officially_received_at:
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
