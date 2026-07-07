"""SC Purchase Order — UC-08: 2-tier approval + email NCC + price variance."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, today, now, getdate


class SCPurchaseOrder(Document):

    def validate(self):
        self._compute_totals()
        self._validate_line_quantities()
        self._validate_delivery_date()
        self._validate_supplier()
        self._check_price_variance()
        self._validate_against_framework_contract()
        if self.docstatus == 0:
            if not self.approval_stage:
                self.approval_stage = "Draft"
            self.status = "Draft"

    def before_submit(self):
        self._validate_rates_before_submit()
        # UX đơn giản hoá: nếu user submit thẳng (không qua workflow review),
        # auto-approve. Workflow review vẫn dùng được optionally qua action buttons.
        if self.approval_stage != "Approved":
            self.approval_stage = "Approved"
            if not self.manager_approved_by:
                self.manager_approved_by = frappe.session.user
                self.manager_approved_at = now()
        supplier_email = frappe.db.get_value("SC Supplier", self.supplier, "email_id")
        if not supplier_email:
            frappe.throw(_(
                "SC-E-PO-NO-SUPPLIER-EMAIL: NCC {0} không có email_id — không thể gửi PO"
            ).format(self.supplier))

    def on_submit(self):
        self.db_set("status", "Approved")
        self._update_framework_contract()
        self._send_po_to_supplier()
        self.db_set("status", "Sent to Supplier")
        self.db_set("sent_to_supplier_at", now())

    def on_cancel(self):
        self.db_set("status", "Cancelled")
        self._update_framework_contract()

    # ------------------------------------------------------------------
    # Workflow methods
    # ------------------------------------------------------------------
    @frappe.whitelist()
    def submit_for_review(self):
        if self.docstatus != 0:
            frappe.throw(_("Phải Draft (chưa submit)"))
        if self.approval_stage not in ("Draft", "Rejected"):
            frappe.throw(_("Chỉ submit_for_review khi Draft/Rejected (hiện: {0})")
                         .format(self.approval_stage))
        self.db_set("approval_stage", "Manager Review")
        self.db_set("rejection_reason", None)
        return {"stage": "Manager Review"}

    @frappe.whitelist()
    def approve_as_manager(self, comment: str = None):
        if self.approval_stage != "Manager Review":
            frappe.throw(_(
                "SC-E-PO-WRONG-STAGE: PO không ở Manager Review (hiện: {0})"
            ).format(self.approval_stage))
        threshold = flt(frappe.db.get_single_value("SupplyCore Settings", "po_approval_threshold") or 50_000_000)
        self.db_set("manager_approved_by", frappe.session.user)
        self.db_set("manager_approved_at", now())
        if flt(self.grand_total) < threshold:
            self.db_set("approval_stage", "Approved")
        else:
            self.db_set("approval_stage", "Executive Review")
        return {"stage": self.approval_stage, "comment": comment}

    @frappe.whitelist()
    def approve_as_executive(self, comment: str = None):
        if self.approval_stage != "Executive Review":
            frappe.throw(_(
                "SC-E-PO-WRONG-STAGE-EXEC: PO không ở Executive Review (hiện: {0})"
            ).format(self.approval_stage))
        self.db_set("executive_approved_by", frappe.session.user)
        self.db_set("executive_approved_at", now())
        self.db_set("approval_stage", "Approved")
        return {"stage": "Approved", "comment": comment}

    @frappe.whitelist()
    def reject(self, reason: str = None):
        if not reason or not str(reason).strip():
            frappe.throw(_("SC-E-REJECT-REASON: Phải nhập lý do từ chối"))
        if self.approval_stage not in ("Manager Review", "Executive Review"):
            frappe.throw(_("Chỉ reject khi đang review (hiện: {0})").format(self.approval_stage))
        self.db_set("approval_stage", "Rejected")
        self.db_set("rejection_reason", reason)
        self._notify_creator_rejected(reason)
        return {"stage": "Rejected"}

    # ------------------------------------------------------------------
    # Existing logic (preserved)
    # ------------------------------------------------------------------
    def _compute_totals(self):
        total_qty = 0
        total = 0
        for r in self.items:
            r.amount = flt(r.qty) * flt(r.rate)
            total_qty += flt(r.qty)
            total += flt(r.amount)
        self.total_qty = total_qty
        self.grand_total = total

    def _validate_line_quantities(self):
        """T12: SL phải > 0 ở mọi lần lưu (kể cả Draft) — tránh lưu im lặng
        với SL = 0 / âm. Đơn giá > 0 kiểm ở before_submit (cho phép Draft tạo
        sẵn để điền giá sau, vd auto-PO từ Alert)."""
        for r in self.items:
            if flt(r.qty) <= 0:
                frappe.throw(_(
                    "SC-E-QTY: Số lượng phải > 0 (dòng {0}, vật tư {1}). "
                    "Không chấp nhận 0 hoặc số âm."
                ).format(r.idx, r.item or "—"), title="SC-E-QTY")

    def _validate_rates_before_submit(self):
        """T12: không cho chốt/gửi PO với đơn giá ≤ 0."""
        for r in self.items:
            if flt(r.rate) <= 0:
                frappe.throw(_(
                    "SC-E-RATE: Đơn giá phải > 0 trước khi gửi PO "
                    "(dòng {0}, vật tư {1})."
                ).format(r.idx, r.item or "—"), title="SC-E-RATE")

    def _validate_delivery_date(self):
        """L13: ngày giao yêu cầu không được trước ngày tạo PO."""
        if self.schedule_date and self.transaction_date:
            if getdate(self.schedule_date) < getdate(self.transaction_date):
                frappe.throw(_(
                    "SC-E030 PO_DELIVERY_BEFORE_ORDER: Ngày giao yêu cầu ({0}) "
                    "không được trước ngày tạo PO ({1})."
                ).format(self.schedule_date, self.transaction_date),
                    title="SC-E030 PO_DELIVERY_BEFORE_ORDER")

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
                                  ["docstatus", "status", "remaining_value", "valid_to", "supplier"], as_dict=True)
        if not fc:
            return
        if fc.docstatus != 1 or fc.status != "Active":
            frappe.throw(_("HĐK {0} không Active").format(self.framework_contract),
                         title="SC-E002 FC_INACTIVE")
        # L12: NCC của PO phải trùng NCC đã ký trên HĐ khung
        if fc.supplier and self.supplier and self.supplier != fc.supplier:
            frappe.throw(_(
                "SC-E027 FC_SUPPLIER_MISMATCH: NCC của PO ({0}) khác NCC của HĐ khung ({1}). "
                "PO theo HĐ khung phải đặt đúng NCC đã ký."
            ).format(self.supplier, fc.supplier), title="SC-E027 FC_SUPPLIER_MISMATCH")
        # L12 + L14: chỉ cho đặt vật tư trong HĐK và SL không vượt phần còn lại
        fc_items = {r.item_code: r for r in frappe.get_all(
            "FC Item", filters={"parent": self.framework_contract},
            fields=["item_code", "remaining_qty", "contract_qty"])}
        for r in self.items:
            if r.item not in fc_items:
                frappe.throw(_(
                    "SC-E028 ITEM_NOT_IN_FC: Vật tư {0} không nằm trong HĐ khung {1}. "
                    "PO theo HĐ khung chỉ được đặt vật tư đã ký."
                ).format(r.item, self.framework_contract), title="SC-E028 ITEM_NOT_IN_FC")
        # L14: gộp SL theo item trong PO rồi so với remaining_qty của HĐK
        po_qty = {}
        for r in self.items:
            po_qty[r.item] = po_qty.get(r.item, 0) + flt(r.qty)
        for item_code, qty in po_qty.items():
            remaining = flt(fc_items[item_code].remaining_qty)
            if qty > remaining:
                frappe.throw(_(
                    "SC-E029 FC_QTY_EXCEEDED: Vật tư {0} đặt {1} vượt số lượng còn lại "
                    "của HĐ khung ({2})."
                ).format(item_code, qty, remaining), title="SC-E029 FC_QTY_EXCEEDED")
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

    # ------------------------------------------------------------------
    # UC-08 helpers
    # ------------------------------------------------------------------
    def _check_price_variance(self):
        """UC-08: flag rows có rate ≠ FC unit_price ±1%."""
        if not self.framework_contract:
            for r in self.items:
                r.fc_unit_price = 0
                r.price_variance_pct = 0
                r.has_price_variance = 0
            self.has_price_variance = 0
            return
        has_any = False
        for r in self.items:
            fc_price = self._get_fc_unit_price(self.framework_contract, r.item)
            r.fc_unit_price = fc_price
            if fc_price > 0:
                r.price_variance_pct = (flt(r.rate) - fc_price) / fc_price * 100
                r.has_price_variance = 1 if abs(r.price_variance_pct) > 1.0 else 0
                if r.has_price_variance:
                    has_any = True
            else:
                r.price_variance_pct = 0
                r.has_price_variance = 0
        self.has_price_variance = 1 if has_any else 0
        if has_any and self.docstatus == 0:
            frappe.msgprint(
                _("⚠ Một số item có giá lệch FC > 1% — cần xem xét"),
                indicator="orange", alert=True,
            )

    @staticmethod
    def _get_fc_unit_price(fc_name: str, item_code: str) -> float:
        r = frappe.db.sql("""
            SELECT unit_price FROM `tabFC Item`
            WHERE parent = %s AND item_code = %s LIMIT 1
        """, (fc_name, item_code))
        return flt(r[0][0]) if r else 0.0

    def _send_po_to_supplier(self):
        email = frappe.db.get_value("SC Supplier", self.supplier, "email_id")
        if not email:
            return
        items_html = "".join(
            f"<tr><td>{r.item}</td><td>{r.qty}</td><td>{r.uom}</td>"
            f"<td>{frappe.format(r.rate, {'fieldtype':'Currency'})}</td>"
            f"<td>{frappe.format(r.amount, {'fieldtype':'Currency'})}</td></tr>"
            for r in self.items
        )
        msg = f"""
            <p>Kính gửi {self.supplier_name or self.supplier},</p>
            <p>Công ty Miyano Việt Nam đặt hàng theo PO <b>{self.name}</b>:</p>
            <table border="1" cellpadding="6" cellspacing="0">
                <tr><th>Mã VT</th><th>SL</th><th>UOM</th><th>Đơn giá</th><th>Thành tiền</th></tr>
                {items_html}
            </table>
            <p><b>Tổng:</b> {frappe.format(self.grand_total, {'fieldtype':'Currency'})}</p>
            <p><b>Ngày giao dự kiến:</b> {self.schedule_date}</p>
            <p><b>Điều khoản giao hàng:</b> {self.delivery_terms or '—'}</p>
            <p><b>Điều khoản thanh toán:</b> {self.payment_terms or '—'}</p>
            <p>Vui lòng xác nhận đơn hàng trong vòng 3 ngày làm việc.</p>
        """
        try:
            frappe.sendmail(
                recipients=[email],
                subject=f"[SupplyCore] Purchase Order {self.name}",
                message=msg,
                delayed=True,
            )
        except Exception as e:
            frappe.log_error(message=str(e)[:1000], title="UC-08 _send_po_to_supplier")

    def _notify_creator_rejected(self, reason: str):
        if not self.owner or self.owner in ("Administrator", "Guest"):
            return
        body = (f"<p>PO <a href='/app/sc-purchase-order/{self.name}'>{self.name}</a> "
                f"đã bị <b>từ chối</b>.</p>"
                f"<p><b>Lý do:</b> {frappe.utils.escape_html(reason)}</p>")
        try:
            frappe.sendmail(
                recipients=[self.owner],
                subject=f"[SupplyCore] PO {self.name} bị từ chối",
                message=body, delayed=True,
            )
        except Exception as e:
            frappe.log_error(message=str(e)[:1000], title="UC-08 _notify_creator_rejected")

    @frappe.whitelist()
    def make_purchase_receipt(self):
        """Tạo Draft PR pre-fill từ PO items + warehouse + rate.
        Trả {message: <pr_name>, url} để ActionPanel auto-navigate."""
        pr_name = make_pr_from_po(self.name)
        return {
            "message": pr_name,
            "purchase_receipt": pr_name,
            "url": f"/supplycore/doc/SC Purchase Receipt/{pr_name}",
        }


# ----------------------------------------------------------------------
# Existing make_pr_from_po (preserved)
# ----------------------------------------------------------------------
@frappe.whitelist()
def make_pr_from_po(po_name: str) -> str:
    po = frappe.get_doc("SC Purchase Order", po_name)
    if po.docstatus != 1:
        frappe.throw(_("PO chưa submit"), title="SC-E-PO")
    if po.status == "Received":
        frappe.throw(_("PO {0} đã nhận đủ — không tạo PR mới").format(po.name),
                      title="SC-E-PO-RECEIVED")
    if po.status == "Cancelled":
        frappe.throw(_("PO {0} đã Cancelled").format(po.name), title="SC-E-PO")

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
    pr.qc_required = 1
    pr.remarks = f"Auto từ PO {po.name}"
    for poi, remaining in pending:
        pr.append("items", {
            "item": poi.item,
            "qty": remaining,
            "uom": poi.uom,
            "rate": flt(poi.rate),
            "warehouse": poi.warehouse or first_wh,
            "po_qty": flt(poi.qty),
            "po_item_ref": poi.name,
        })
    pr.flags.ignore_permissions = True
    pr.insert()
    return pr.name
