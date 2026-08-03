"""Framework Contract — Hợp đồng khung NCC (M1) + UC-03 3-tier approval workflow."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, today, flt, date_diff, now


# Default threshold nếu Settings chưa cấu hình
DEFAULT_FC_EXECUTIVE_THRESHOLD = 100_000_000


class FrameworkContract(Document):

    def validate(self):
        self._guard_locked_after_approval()
        self._default_dates()
        self._validate_dates()
        self._validate_supplier_active()
        self._compute_items()
        self._compute_totals()
        self._derive_status()

    def _guard_locked_after_approval(self):
        """Khoá sửa khi HĐ đã duyệt 3-tier (stage=Approved & docstatus=0).

        Lý do: HĐ đã qua đủ Manager + Executive nhưng chưa Submit kích hoạt —
        chỉ cho phép 2 action: Submit (kích hoạt) hoặc Reject (gửi lại Kế toán).
        Sửa nội dung sau khi duyệt = phá vỡ audit trail của 3-tier approval.

        Bypass:
        - is_new() → đang tạo mới, không có gì để khoá.
        - docstatus != 0 → docstatus=1 đã được Frappe khoá tự nhiên (chỉ db_set
          đi qua được); docstatus=2 (Cancelled) thì cũng không sửa được.
        - flags.allow_edit_after_approval → cho phép code nội bộ bypass (vd
          reset_to_draft sau khi Reject).
        """
        if self.is_new():
            return
        if (self.docstatus or 0) != 0:
            return
        if (self.approval_stage or "") != "Approved":
            return
        if self.flags.get("allow_edit_after_approval"):
            return
        frappe.throw(
            _("Hợp đồng đã được duyệt (Approved) — không cho phép sửa. "
              "Hãy bấm Submit để kích hoạt HĐ, hoặc Reject để gửi lại Kế toán."),
            title="SC-E-FC-LOCKED",
        )

    def before_submit(self):
        """UC-03 step 6-7: chỉ cho submit khi đã Approved qua 3-tier."""
        if self.approval_stage != "Approved":
            frappe.throw(
                _("HĐ chưa được duyệt qua 3-tier (Kế toán → Quản lý → Lãnh đạo). "
                  "Hiện đang ở stage: {0}. Click 'Gửi duyệt' để bắt đầu workflow.").format(
                    self.approval_stage or "Draft"),
                title="SC-E-FC-NOT-APPROVED")

    def on_submit(self):
        self.db_set("status", self._compute_active_or_expired())

    def on_cancel(self):
        self.db_set("status", "Terminated")
        # Block các Release Order đang draft tham chiếu HĐ này
        for ro in frappe.get_all("Release Order",
                                  filters={"framework_contract": self.name, "docstatus": 0},
                                  fields=["name"]):
            frappe.db.set_value("Release Order", ro.name, "status", "Cancelled")

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    def _default_dates(self):
        """L04: mặc định Hiệu lực từ = Ngày ký; Hết hạn = Ngày ký + 1 năm khi
        chưa nhập (vẫn cho sửa). Backstop cho luồng API/import (UI đã tự điền)."""
        if not self.contract_date:
            return
        if not self.valid_from:
            self.valid_from = self.contract_date
        if not self.valid_to:
            from frappe.utils import add_years
            self.valid_to = add_years(getdate(self.contract_date), 1)

    def _validate_dates(self):
        if getdate(self.valid_to) <= getdate(self.valid_from):
            frappe.throw(_("Ngày hết hạn phải sau ngày hiệu lực"), title="SC-E-DATE")
        if getdate(self.contract_date) > getdate(self.valid_from):
            frappe.throw(_("Ngày ký không được sau ngày hiệu lực"), title="SC-E-DATE")

    def _validate_supplier_active(self):
        from supplycore.utils.validators import validate_supplier
        sup = validate_supplier(self.supplier)
        if sup and sup.blacklist_flag:
            # UC-03 ngoại lệ: NCC blacklist → require Executive override
            if not self.executive_override_blacklist:
                msg = _("NCC {0} đang trong BLACKLIST. Cần Lãnh đạo bật cờ "
                         "'Executive override blacklist' để tiếp tục.").format(self.supplier)
                if self.docstatus == 0 and self.approval_stage in (None, "", "Draft"):
                    # Cho draft nhưng warning
                    frappe.msgprint(msg, indicator="orange", alert=True)
                else:
                    frappe.throw(msg, title="SC-E-FC-BLACKLIST")

    # ------------------------------------------------------------------
    # Computations
    # ------------------------------------------------------------------
    def _compute_items(self):
        for row in self.items:
            row.total_amount = flt(row.contract_qty) * flt(row.unit_price)
            row.remaining_qty = flt(row.contract_qty) - flt(row.ordered_qty or 0)

    def _compute_totals(self):
        # Tổng giá trị HĐ luôn = Σ thành tiền items (read-only đối với user)
        self.total_value = sum(flt(r.total_amount) for r in self.items)
        used = flt(self.used_value or 0)
        committed = flt(self.committed_value or 0)
        self.remaining_value = flt(self.total_value) - used - committed

    def _derive_status(self):
        if self.docstatus == 0:
            self.status = "Draft"
        elif self.docstatus == 2:
            self.status = "Terminated"
        else:
            self.status = self._compute_active_or_expired()
        # Cờ sắp hết hạn
        days_left = date_diff(self.valid_to, today())
        self.expiring_soon = 1 if 0 <= days_left <= 30 else 0

    def _compute_active_or_expired(self) -> str:
        """Đã submit (docstatus=1) → Exhausted/Expired/Active tùy state.

        QA-BUG-M1-02: HĐ remaining_value <= 0 → Exhausted (đã dùng hết
        hạn mức) — KHÔNG được cho tạo PO mới dù chưa đến valid_to.

        Thứ tự ưu tiên:
          - Exhausted: remaining_value <= 0 (đã dùng hết)
          - Expired:   today > valid_to (quá hạn)
          - Active:    còn hạn + còn hạn mức
        """
        today_d = getdate(today())
        if flt(self.remaining_value) <= 0 and flt(self.total_value) > 0:
            return "Exhausted"
        if today_d > getdate(self.valid_to):
            return "Expired"
        return "Active"

    # ------------------------------------------------------------------
    # UC-03 Approval Workflow — 3-tier (Kế toán → Quản lý → Lãnh đạo)
    # ------------------------------------------------------------------
    @frappe.whitelist()
    def submit_for_review(self):
        """Bước 6 start: Draft → Manager Review.

        Bất kỳ user có quyền create FC đều submit được (Kế toán/SK).
        """
        # Đọc từ DB (tránh stale in-memory docstatus sau failed submit())
        db = frappe.db.get_value("Framework Contract", self.name,
                                   ["docstatus", "approval_stage"], as_dict=True) or {}
        if (db.docstatus or 0) != 0:
            frappe.throw(_("Chỉ submit review khi FC đang Draft (docstatus=0)"),
                          title="SC-E-FC-STAGE")
        if (db.approval_stage or "Draft") not in ("Draft", "Rejected"):
            frappe.throw(_("FC đã ở stage {0} — không thể gửi review lại").format(db.approval_stage),
                          title="SC-E-FC-STAGE")
        # Reset rejection nếu re-submit
        self.db_set({
            "approval_stage": "Manager Review",
            "rejection_reason": None,
        })
        from supplycore.utils.emailer import role_emails
        self._notify_stage(
            recipients=role_emails("SupplyCore Manager"),
            subject=f"[SupplyCore] HĐ khung {self.name} chờ Quản lý duyệt",
            title="Hợp đồng khung chờ duyệt — cấp Quản lý",
            intro=f"Hợp đồng khung <b>{self.name}</b> vừa được gửi và đang chờ Quản lý phê duyệt.",
            actor=frappe.session.user, action="Gửi duyệt")
        return {"stage": "Manager Review"}

    @frappe.whitelist()
    def approve_as_manager(self, comment: str = None):
        """Bước 6 mid: Manager Review → Executive Review (nếu ≥ threshold) | Approved (nếu < threshold)."""
        _require_role("SupplyCore Manager")
        if self.approval_stage != "Manager Review":
            frappe.throw(_("FC chưa ở stage Manager Review (hiện: {0})").format(self.approval_stage),
                          title="SC-E-FC-STAGE")
        threshold = _get_executive_threshold()
        next_stage = "Executive Review" if flt(self.total_value) >= threshold else "Approved"
        self.db_set({
            "approval_stage": next_stage,
            "manager_approved_by": frappe.session.user,
            "manager_approved_at": now(),
            "manager_comment": (comment or "").strip() or self.manager_comment,
        })
        from supplycore.utils.emailer import role_emails
        if next_stage == "Executive Review":
            self._notify_stage(
                recipients=role_emails("SupplyCore Executive"),
                subject=f"[SupplyCore] HĐ khung {self.name} chờ Lãnh đạo duyệt",
                title="Hợp đồng khung chờ duyệt — cấp Lãnh đạo",
                intro=f"Hợp đồng khung <b>{self.name}</b> (giá trị lớn) đã qua Quản lý, "
                      "đang chờ Lãnh đạo phê duyệt cấp cao.",
                actor=frappe.session.user, action="Quản lý duyệt")
        else:  # Approved thẳng (dưới ngưỡng)
            self._notify_stage(
                recipients=[self.owner],
                subject=f"[SupplyCore] HĐ khung {self.name} đã được duyệt",
                title="Hợp đồng khung đã được duyệt",
                intro=f"Hợp đồng khung <b>{self.name}</b> của bạn đã được duyệt và sẵn sàng kích hoạt.",
                actor=frappe.session.user, action="Duyệt (Quản lý)")
        return {"stage": next_stage, "threshold": threshold}

    @frappe.whitelist()
    def approve_as_executive(self, comment: str = None):
        """Bước 6 final: Executive Review → Approved."""
        _require_role("SupplyCore Executive")
        if self.approval_stage != "Executive Review":
            frappe.throw(_("FC chưa ở stage Executive Review (hiện: {0})").format(self.approval_stage),
                          title="SC-E-FC-STAGE")
        self.db_set({
            "approval_stage": "Approved",
            "executive_approved_by": frappe.session.user,
            "executive_approved_at": now(),
            "executive_comment": (comment or "").strip() or self.executive_comment,
        })
        self._notify_stage(
            recipients=[self.owner],
            subject=f"[SupplyCore] HĐ khung {self.name} đã được duyệt",
            title="Hợp đồng khung đã được duyệt — cấp Lãnh đạo",
            intro=f"Hợp đồng khung <b>{self.name}</b> đã được Lãnh đạo phê duyệt và sẵn sàng kích hoạt.",
            actor=frappe.session.user, action="Duyệt (Lãnh đạo)")
        return {"stage": "Approved"}

    @frappe.whitelist()
    def reject_approval(self, reason: str):
        """Bước 6a: Reject ở bất kỳ stage Manager/Executive Review.

        Quyền: Manager hoặc Executive.
        """
        if not reason or not reason.strip():
            frappe.throw(_("Bắt buộc nhập lý do từ chối"), title="SC-E-FC-REJECT")
        if self.approval_stage not in ("Manager Review", "Executive Review"):
            frappe.throw(_("FC chưa ở stage Review (hiện: {0})").format(self.approval_stage),
                          title="SC-E-FC-STAGE")
        # Manager có thể reject ở Manager Review; Executive ở Executive Review
        if self.approval_stage == "Manager Review":
            _require_role("SupplyCore Manager")
        else:
            _require_role("SupplyCore Executive")
        self.db_set({
            "approval_stage": "Rejected",
            "rejection_reason": reason.strip(),
        })
        self._notify_stage(
            recipients=[self.owner],
            subject=f"[SupplyCore] HĐ khung {self.name} bị từ chối",
            title="Hợp đồng khung bị từ chối",
            intro=f"Hợp đồng khung <b>{self.name}</b> đã bị từ chối. "
                  "Vui lòng chỉnh sửa và gửi duyệt lại.",
            actor=frappe.session.user, action="Từ chối",
            note=f"Lý do từ chối: {reason.strip()}", note_kind="crit")
        return {"stage": "Rejected"}

    # ------------------------------------------------------------------
    # Email thông báo chi tiết theo luồng duyệt (người duyệt + thông tin phiếu + link)
    # ------------------------------------------------------------------
    def _fc_info_rows(self):
        cur = {"fieldtype": "Currency"}
        dt = {"fieldtype": "Date"}
        return [
            ("Mã hợp đồng", self.name),
            ("Nhà cung cấp", self.supplier_name or self.supplier),
            ("Giá trị HĐ", frappe.format(self.total_value, cur)),
            ("Hạn mức còn lại", frappe.format(self.remaining_value, cur)),
            ("Hiệu lực", f"{frappe.format(self.valid_from, dt)} → {frappe.format(self.valid_to, dt)}"),
            ("Giai đoạn duyệt", self.approval_stage),
        ]

    def _notify_stage(self, *, recipients, subject, title, intro,
                      actor=None, action=None, note=None, note_kind="info"):
        # Duyệt hàng loạt → chặn email từng phiếu, gửi 1 email tổng kết ở cuối.
        if frappe.flags.get("suppress_fc_notify"):
            return
        from supplycore.utils.emailer import send_doc_email
        try:
            send_doc_email(
                doctype="Framework Contract", name=self.name, recipients=recipients,
                subject=subject, title=title, intro=intro, info_rows=self._fc_info_rows(),
                actor=actor, action=action, note=note, note_kind=note_kind, delayed=True)
        except Exception as e:
            frappe.log_error(str(e)[:1000], "FC notify email")

    # ------------------------------------------------------------------
    # UC-04 Renewal & Termination
    # ------------------------------------------------------------------
    @frappe.whitelist()
    def request_renewal(self, new_valid_to: str, reason: str):
        """Bước 5: Gia hạn HĐ — append row Pending vào renewal_history.

        Quyền: Accountant/Manager (FC create permission).
        Validate: new_valid_to > valid_to + chưa hết hạn quá 90 ngày.
        """
        if self.docstatus != 1:
            frappe.throw(_("Chỉ gia hạn FC đã submit"), title="SC-E-FC-STAGE")
        if self.status == "Terminated":
            frappe.throw(_("HĐ đã thanh lý — không thể gia hạn"), title="SC-E-FC-TERMINATED")
        if not reason or not reason.strip():
            frappe.throw(_("Bắt buộc nhập lý do gia hạn"), title="SC-E-FC-RENEWAL")
        if not new_valid_to:
            frappe.throw(_("Bắt buộc nhập ngày hết hạn mới"), title="SC-E-FC-RENEWAL")

        # Ngoại lệ: hết hạn quá 90 ngày → không gia hạn retroactively
        days_expired = date_diff(today(), self.valid_to)
        if days_expired > 90:
            frappe.throw(
                _("HĐ đã hết hạn quá 90 ngày ({0} ngày) — không thể gia hạn retroactively. "
                  "Vui lòng tạo FC mới.").format(days_expired),
                title="SC-E-FC-EXPIRED-90D")

        if getdate(new_valid_to) <= getdate(self.valid_to):
            frappe.throw(
                _("Ngày hết hạn mới ({0}) phải SAU ngày hết hạn hiện tại ({1})").format(
                    new_valid_to, self.valid_to),
                title="SC-E-FC-RENEWAL")

        row = self.append("renewal_history", {
            "request_date": now(),
            "old_valid_to": self.valid_to,
            "new_valid_to": new_valid_to,
            "renewed_by": frappe.session.user,
            "approval_status": "Pending",
            "reason": reason.strip(),
        })
        self.flags.ignore_permissions = True
        self.flags.ignore_validate_update_after_submit = True
        self.save()
        return {"row_idx": row.idx, "approval_status": "Pending"}

    @frappe.whitelist()
    def approve_renewal(self, row_idx: int, comment: str = None):
        """Manager (hoặc Executive nếu ≥ threshold) duyệt 1 renewal request Pending."""
        idx = int(row_idx)
        target = None
        for r in (self.renewal_history or []):
            if r.idx == idx:
                target = r; break
        if not target:
            frappe.throw(_("Không tìm thấy renewal row idx={0}").format(idx),
                          title="SC-E-FC-RENEWAL")
        if target.approval_status != "Pending":
            frappe.throw(_("Renewal đã ở trạng thái {0}").format(target.approval_status),
                          title="SC-E-FC-RENEWAL")
        # Role gating — Executive nếu FC ≥ threshold, ngược lại Manager đủ
        threshold = _get_executive_threshold()
        if flt(self.total_value) >= threshold:
            _require_role("SupplyCore Executive")
        else:
            _require_role("SupplyCore Manager")

        new_valid_to = target.new_valid_to
        target.approval_status = "Approved"
        target.approved_by = frappe.session.user
        target.approved_at = now()
        if comment:
            target.reason = (target.reason or "") + f"\n[Duyệt] {comment}"
        # Update FC.valid_to
        self.valid_to = new_valid_to
        self.flags.ignore_permissions = True
        self.flags.ignore_validate_update_after_submit = True
        self.save()
        # Recompute status (Active nếu trong hạn mới)
        self.db_set("status", self._compute_active_or_expired())
        # Reset expiring_soon
        days_left = date_diff(self.valid_to, today())
        self.db_set("expiring_soon", 1 if 0 <= days_left <= 30 else 0)
        return {"row_idx": idx, "new_valid_to": new_valid_to,
                "fc_status": self.status}

    @frappe.whitelist()
    def reject_renewal(self, row_idx: int, comment: str = None):
        """Reject renewal Pending. Quyền: Manager hoặc Executive."""
        idx = int(row_idx)
        target = None
        for r in (self.renewal_history or []):
            if r.idx == idx:
                target = r; break
        if not target:
            frappe.throw(_("Không tìm thấy renewal row idx={0}").format(idx),
                          title="SC-E-FC-RENEWAL")
        if target.approval_status != "Pending":
            frappe.throw(_("Renewal đã ở trạng thái {0}").format(target.approval_status),
                          title="SC-E-FC-RENEWAL")
        # Manager hoặc Executive đều reject được
        roles = frappe.get_roles(frappe.session.user)
        if not any(r in roles for r in ("SupplyCore Manager", "SupplyCore Executive", "System Manager")):
            frappe.throw(_("Cần role Manager hoặc Executive để reject"),
                          frappe.PermissionError, title="SC-E-FC-ROLE")
        target.approval_status = "Rejected"
        target.approved_by = frappe.session.user
        target.approved_at = now()
        if comment:
            target.reason = (target.reason or "") + f"\n[Reject] {comment}"
        self.flags.ignore_permissions = True
        self.flags.ignore_validate_update_after_submit = True
        self.save()
        return {"row_idx": idx, "approval_status": "Rejected"}

    @frappe.whitelist()
    def terminate_contract(self, reason: str, attachment_url: str = None):
        """Bước 5a: Thanh lý HĐ — set status=Terminated + ghi biên bản.

        Quyền: Manager. Block tất cả RO draft tham chiếu (đã có ở on_cancel).
        """
        _require_role("SupplyCore Manager")
        if self.docstatus != 1:
            frappe.throw(_("Chỉ thanh lý FC đã submit"), title="SC-E-FC-STAGE")
        if self.status == "Terminated":
            frappe.throw(_("HĐ đã thanh lý"), title="SC-E-FC-TERMINATED")
        if not reason or not reason.strip():
            frappe.throw(_("Bắt buộc nhập lý do thanh lý"), title="SC-E-FC-TERMINATE")
        self.db_set({
            "status": "Terminated",
            "termination_date": today(),
            "termination_reason": reason.strip(),
            "termination_minutes": attachment_url or self.termination_minutes,
        })
        # Block RO draft
        for ro in frappe.get_all("Release Order",
                                  filters={"framework_contract": self.name, "docstatus": 0},
                                  fields=["name"]):
            frappe.db.set_value("Release Order", ro.name, "status", "Cancelled")
        return {"status": "Terminated", "termination_date": today()}

    # ------------------------------------------------------------------
    # Public API — gọi từ Release Order / Purchase Order
    # ------------------------------------------------------------------
    @frappe.whitelist()
    def recalculate_used_value(self):
        """Tính lại used_value (PO submit) + committed_value (RO Approved chưa convert)."""
        used = frappe.db.sql("""
            SELECT COALESCE(SUM(grand_total), 0)
            FROM `tabSC Purchase Order`
            WHERE framework_contract = %s AND docstatus = 1
        """, self.name)[0][0]

        committed = frappe.db.sql("""
            SELECT COALESCE(SUM(total_amount), 0)
            FROM `tabRelease Order`
            WHERE framework_contract = %s
              AND docstatus = 1
              AND status = 'Approved'
        """, self.name)[0][0]

        self.db_set("used_value", flt(used))
        self.db_set("committed_value", flt(committed))
        self.db_set("remaining_value", flt(self.total_value) - flt(used) - flt(committed))

        # Per-item: ordered_qty = SL từ PO submit + SL từ RO Approved chưa convert
        for row in self.items:
            po_qty = frappe.db.sql("""
                SELECT COALESCE(SUM(poi.qty), 0)
                FROM `tabSC Purchase Order Item` poi
                JOIN `tabSC Purchase Order` po ON po.name = poi.parent
                WHERE po.framework_contract = %s
                  AND po.docstatus = 1
                  AND poi.item = %s
            """, (self.name, row.item_code))[0][0]
            ro_qty = frappe.db.sql("""
                SELECT COALESCE(SUM(roi.qty), 0)
                FROM `tabRO Item` roi
                JOIN `tabRelease Order` ro ON ro.name = roi.parent
                WHERE ro.framework_contract = %s
                  AND ro.docstatus = 1
                  AND ro.status = 'Approved'
                  AND roi.item_code = %s
            """, (self.name, row.item_code))[0][0]
            committed_qty = flt(po_qty) + flt(ro_qty)
            frappe.db.set_value("FC Item", row.name, {
                "ordered_qty": committed_qty,
                "remaining_qty": flt(row.contract_qty) - committed_qty,
            })

    def get_item_unit_price(self, item_code: str) -> float:
        """Tra đơn giá HĐK cho 1 item — gọi từ Release Order."""
        for row in self.items:
            if row.item_code == item_code:
                return flt(row.unit_price)
        frappe.throw(_("Vật tư {0} không có trong hợp đồng khung {1}").format(item_code, self.name))

    def get_item_remaining_qty(self, item_code: str) -> float:
        for row in self.items:
            if row.item_code == item_code:
                return flt(row.remaining_qty)
        return 0

    @frappe.whitelist()
    def make_material_request(self, items=None, schedule_date=None, warehouse=None):
        """Tạo SC Material Request từ FC items (UC-07 luồng 2: gọi hàng theo HĐ).

        Args:
          items: list [{item_code, qty}] — None → dùng tất cả items với remaining_qty
          schedule_date: ngày cần (default: today+14)
          warehouse: kho nhận (default: from Settings hoặc kho đầu tiên)
        """
        import json
        if self.docstatus != 1 or self.status != "Active":
            frappe.throw(_("Chỉ tạo MR từ HĐ Active (hiện: {0})").format(self.status),
                          title="SC-E-FC-MR-NOT-ACTIVE")

        if isinstance(items, str):
            items = json.loads(items)
        # Default: lấy items từ FC với remaining > 0
        if not items:
            items = [{"item_code": r.item_code, "qty": flt(r.remaining_qty)}
                      for r in self.items if flt(r.remaining_qty) > 0]
        if not items:
            frappe.throw(_("Không có item nào còn remaining_qty > 0"))

        if not warehouse:
            warehouse = frappe.db.get_single_value("SupplyCore Settings", "default_warehouse")
            if not warehouse:
                warehouse = frappe.db.get_value("SC Warehouse",
                    {"is_group": 0, "disabled": 0}, "name")
        if not warehouse:
            frappe.throw(_("Cần chọn warehouse"))

        sched = schedule_date or frappe.utils.add_days(today(), 14)
        mr = frappe.new_doc("SC Material Request")
        mr.request_type = "Purchase"
        mr.transaction_date = today()
        mr.schedule_date = sched
        mr.warehouse = warehouse
        mr.remarks = f"Auto từ HĐ khung {self.name} (NCC: {self.supplier_name or self.supplier})"
        mr.framework_contract = self.name if frappe.db.has_column("SC Material Request", "framework_contract") else None
        # Map item_code → dòng FC Item, để lấy đơn giá / ĐVT / tên vật tư
        # ngay từ hợp đồng khung — user KHÔNG phải chọn lại HĐ khung ở bảng chi tiết.
        fc_rows = {r.item_code: r for r in self.items}
        for it in items:
            item_code = it.get("item_code") or it.get("item")
            qty = flt(it.get("qty"))
            if not item_code or qty <= 0:
                continue
            fc_row = fc_rows.get(item_code)
            uom = (fc_row.uom if fc_row else None) \
                or frappe.db.get_value("SC Item", item_code, "uom")
            unit_price = flt(fc_row.unit_price) if fc_row else 0.0
            item_name = (fc_row.item_name if fc_row else None) \
                or frappe.db.get_value("SC Item", item_code, "item_name")
            mr.append("items", {
                "item": item_code,
                "item_name": item_name,
                "uom": uom,
                "qty": qty,
                "schedule_date": sched,
                # UC-07 luồng 2: gắn sẵn HĐ khung + đơn giá vào từng dòng
                "framework_contract": self.name,
                "estimated_unit_cost": unit_price,
                "estimated_amount": qty * unit_price,
            })
        mr.flags.ignore_permissions = True
        mr.insert()
        return {"material_request": mr.name, "url": f"/supplycore/doc/SC Material Request/{mr.name}"}


# ============================================================
# Helpers cho UC-03 approval workflow
# ============================================================
def _require_role(role: str):
    """Throw nếu user hiện tại không có role được yêu cầu (System Manager bypass)."""
    user_roles = frappe.get_roles(frappe.session.user)
    if role not in user_roles and "System Manager" not in user_roles:
        frappe.throw(_("Cần role '{0}' để thực hiện thao tác này").format(role),
                      frappe.PermissionError, title="SC-E-FC-ROLE")


def _get_executive_threshold() -> float:
    try:
        v = frappe.db.get_single_value("SupplyCore Settings", "fc_executive_threshold")
        return flt(v) if v else DEFAULT_FC_EXECUTIVE_THRESHOLD
    except Exception:
        return DEFAULT_FC_EXECUTIVE_THRESHOLD


# QAv3-BUG-M1-07 (đã gỡ theo yêu cầu): trước đây bắt comment duyệt Manager/
# Executive tối thiểu 10 ký tự (SC-E026). Nay comment là TÙY CHỌN — vẫn được
# lưu vào manager_comment/executive_comment nếu người duyệt có nhập.


@frappe.whitelist()
def bulk_approve_submit(names):
    """Duyệt & Submit HÀNG LOẠT Hợp đồng khung (dùng khi import loạt HĐ nháp).

    Quyền: CHỈ SupplyCore Manager / System Manager (phân quyền cao).
    Với mỗi HĐ đang Draft/Rejected: submit_for_review → approve_as_manager →
    - nếu Approved (giá trị < ngưỡng Executive) → submit (Active);
    - nếu ≥ ngưỡng → dừng ở 'Chờ Lãnh đạo duyệt' (Manager không đủ quyền submit).
    Chặn email từng phiếu, gửi 1 EMAIL TỔNG KẾT cho chính người thực hiện.
    """
    import json
    roles = frappe.get_roles(frappe.session.user)
    if not any(r in roles for r in ("SupplyCore Manager", "System Manager")):
        frappe.throw(
            _("Chỉ Quản lý (SupplyCore Manager) mới được duyệt & submit hàng loạt"),
            title="SC-E-FC-BULK-ROLE")
    if isinstance(names, str):
        names = json.loads(names)
    names = [n for n in (names or []) if n]

    submitted, pending_exec, skipped, errors = [], [], [], []
    frappe.flags.suppress_fc_notify = True   # chặn email từng phiếu
    try:
        for name in names:
            try:
                doc = frappe.get_doc("Framework Contract", name)
                if doc.docstatus != 0:
                    skipped.append({"name": name, "reason": "Đã submit/hủy"}); continue
                if (doc.approval_stage or "Draft") in ("Draft", "Rejected"):
                    doc.submit_for_review(); doc.reload()
                if doc.approval_stage == "Manager Review":
                    doc.approve_as_manager(comment="Duyệt hàng loạt"); doc.reload()
                if doc.approval_stage == "Approved":
                    doc.submit()
                    submitted.append(name)
                elif doc.approval_stage == "Executive Review":
                    pending_exec.append(name)
                else:
                    skipped.append({"name": name, "reason": f"Giai đoạn {doc.approval_stage}"})
                frappe.db.commit()       # giữ thành công của phiếu này
            except Exception as e:
                frappe.db.rollback()     # chỉ hoàn tác phiếu lỗi (về commit gần nhất)
                errors.append({"name": name, "error": str(e)[:150]})
    finally:
        frappe.flags.suppress_fc_notify = False

    _bulk_notify_result(submitted, pending_exec, errors)
    return {"submitted": submitted, "pending_executive": pending_exec,
            "skipped": skipped, "errors": errors,
            "counts": {"submitted": len(submitted), "pending_executive": len(pending_exec),
                       "skipped": len(skipped), "errors": len(errors)}}


def _bulk_notify_result(submitted, pending_exec, errors):
    """Gửi 1 email tổng kết duyệt hàng loạt cho chính người thực hiện."""
    try:
        from supplycore.utils.emailer import send_email, sc_list_url
        me = frappe.session.user
        email = frappe.db.get_value("User", me, "email") or me
        if not email or email in ("Administrator", "Guest"):
            return

        def _ul(rows):
            return "".join(f"<li>{r}</li>" for r in rows) or "<li>—</li>"

        body = (
            f"<p style='font-weight:600;color:#1B7A4E'>Đã duyệt & kích hoạt ({len(submitted)}):</p>"
            f"<ul>{_ul(submitted)}</ul>"
            f"<p style='font-weight:600;color:#9C6511'>Chờ Lãnh đạo duyệt ({len(pending_exec)}):</p>"
            f"<ul>{_ul(pending_exec)}</ul>"
        )
        if errors:
            body += ("<p style='font-weight:600;color:#BE3A3A'>Lỗi ({}):</p><ul>".format(len(errors))
                     + "".join(f"<li>{e['name']}: {e['error']}</li>" for e in errors) + "</ul>")
        total = len(submitted) + len(pending_exec) + len(errors)
        send_email(
            recipients=[email],
            subject=f"[SupplyCore] Kết quả duyệt hàng loạt HĐ khung — {len(submitted)} đã kích hoạt",
            title="Kết quả duyệt & submit hàng loạt Hợp đồng khung",
            intro=f"Bạn vừa thao tác duyệt hàng loạt {total} hợp đồng khung. Kết quả:",
            body_html=body,
            cta_url=sc_list_url("Framework Contract"), cta_label="Mở danh sách HĐ khung")
    except Exception as e:
        frappe.log_error(str(e)[:1000], "FC bulk notify email")
