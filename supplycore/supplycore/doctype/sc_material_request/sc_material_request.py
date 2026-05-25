import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate


class SCMaterialRequest(Document):

    def validate(self):
        total_qty = 0
        total = 0
        for r in self.items:
            if flt(r.qty) <= 0:
                frappe.throw(_("SC-E-QTY: Số lượng phải > 0 (item {0})").format(r.item))
            if r.framework_contract:
                fc_price = self._get_fc_price(r.framework_contract, r.item)
                if fc_price > 0:
                    r.estimated_unit_cost = fc_price
            r.estimated_amount = flt(r.qty) * flt(r.estimated_unit_cost)
            total_qty += flt(r.qty)
            total += flt(r.estimated_amount)
        self.total_qty = total_qty
        self.total_estimated_cost = total

        if self.schedule_date and self.transaction_date:
            if getdate(self.schedule_date) < getdate(self.transaction_date):
                frappe.throw(_("SC-E-DATE: Ngày cần phải ≥ ngày yêu cầu"))

        if self.request_type in ("Purchase", "Urgent"):
            self._validate_suppliers()

        if self.docstatus == 0:
            self.status = "Draft"

    def before_submit(self):
        """QAv3-BUG-M2-06: Block submit MR có total_estimated_cost <= 0.

        MR loại Purchase / Urgent phải có giá trị ước tính > 0 — không
        chấp nhận duyệt MR 'không có cơ sở giá'. Material Transfer Request
        nội bộ không cần price → exempt.
        """
        if self.request_type in ("Purchase", "Urgent") and flt(self.total_estimated_cost) <= 0:
            frappe.throw(_(
                "SC-E023 ZERO_MR_COST: MR {0} có tổng ước tính = {1}. "
                "MR loại {2} phải có đơn giá > 0 ở mọi dòng. "
                "Kiểm tra HĐ khung hoặc nhập 'Đơn giá ước tính' từng dòng."
            ).format(self.name, self.total_estimated_cost, self.request_type),
                title="SC-E023 ZERO_MR_COST")

    def on_submit(self):
        """UC-07: submit → Pending (chờ duyệt). KHÔNG auto-approve."""
        self.db_set("status", "Pending")
        self._notify_managers()

    def on_cancel(self):
        self.db_set("status", "Cancelled")

    @frappe.whitelist()
    def approve(self):
        if self.docstatus != 1:
            frappe.throw(_("Phải submit trước khi duyệt"))
        if self.status != "Pending":
            frappe.throw(_("MR không ở trạng thái Pending (hiện: {0})").format(self.status))
        self.db_set("status", "Approved")
        self._notify_owner("Approved")
        return {"status": "Approved"}

    @frappe.whitelist()
    def reject(self, reason: str = None):
        if not reason or not str(reason).strip():
            frappe.throw(_("SC-E-REJECT-REASON: Phải nhập lý do từ chối"))
        if self.docstatus != 1:
            frappe.throw(_("Phải submit trước khi reject"))
        if self.status != "Pending":
            frappe.throw(_("MR không ở trạng thái Pending (hiện: {0})").format(self.status))
        self.db_set("status", "Rejected")
        self.db_set("rejection_reason", reason)
        self._notify_owner("Rejected", reason=reason)
        return {"status": "Rejected"}

    @frappe.whitelist()
    def get_po_suggestion(self):
        from supplycore.m2_planning.api.po_suggest import suggest_po_from_mr
        return suggest_po_from_mr(self.name, auto_create=0)

    @frappe.whitelist()
    def create_purchase_orders(self):
        if self.status != "Approved":
            frappe.throw(_(
                "SC-E-MR-NOT-APPROVED: MR phải Approved trước khi tạo PO (hiện: {0})"
            ).format(self.status))
        from supplycore.m2_planning.api.po_suggest import suggest_po_from_mr
        return suggest_po_from_mr(self.name, auto_create=1)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _get_fc_price(fc_name: str, item_code: str) -> float:
        result = frappe.db.sql("""
            SELECT unit_price FROM `tabFC Item`
            WHERE parent = %s AND item_code = %s
            LIMIT 1
        """, (fc_name, item_code))
        return flt(result[0][0]) if result else 0.0

    def _validate_suppliers(self):
        for r in self.items:
            if not self._item_has_supplier(r.item):
                frappe.throw(_(
                    "SC-E-NO-SUPPLIER: Vật tư {0} chưa có NCC. "
                    "Vui lòng cấu hình NCC trước khi đề nghị mua."
                ).format(r.item))

    @staticmethod
    def _item_has_supplier(item_code: str) -> bool:
        if frappe.db.get_value("SC Item", item_code, "default_supplier"):
            return True
        fc_exists = frappe.db.sql("""
            SELECT 1 FROM `tabFC Item` fci
            JOIN `tabFramework Contract` fc ON fc.name = fci.parent
            WHERE fci.item_code = %s AND fc.docstatus = 1 AND fc.status = 'Active'
            LIMIT 1
        """, item_code)
        if fc_exists:
            return True
        item_group = frappe.db.get_value("SC Item", item_code, "item_group")
        if item_group:
            sg = frappe.db.sql("""
                SELECT 1 FROM `tabSC Supplier Item Group` sg
                JOIN `tabSC Supplier` s ON s.name = sg.parent
                WHERE sg.item_group = %s AND s.disabled = 0
                  AND (s.blacklist_flag = 0 OR s.blacklist_flag IS NULL)
                LIMIT 1
            """, item_group)
            if sg:
                return True
        return False

    def _notify_managers(self):
        recipients = self._get_recipients_by_role("SupplyCore Manager")
        if not recipients:
            return
        try:
            frappe.sendmail(
                recipients=recipients,
                subject=f"[SupplyCore] MR {self.name} chờ duyệt",
                message=(f"<p>MR <a href='/app/sc-material-request/{self.name}'>{self.name}</a> "
                         f"({self.request_type}) chờ phê duyệt.</p>"
                         f"<p>Tổng: {frappe.format(self.total_estimated_cost, {'fieldtype':'Currency'})}</p>"),
                delayed=True,
            )
        except Exception as e:
            frappe.log_error(message=str(e)[:1000], title="UC-07 _notify_managers")

    def _notify_owner(self, status: str, reason: str = None):
        if not self.owner or self.owner in ("Administrator", "Guest"):
            return
        body = f"<p>MR <a href='/app/sc-material-request/{self.name}'>{self.name}</a> đã được <b>{status}</b>.</p>"
        if reason:
            body += f"<p><b>Lý do:</b> {frappe.utils.escape_html(reason)}</p>"
        try:
            frappe.sendmail(
                recipients=[self.owner],
                subject=f"[SupplyCore] MR {self.name} {status}",
                message=body,
                delayed=True,
            )
        except Exception as e:
            frappe.log_error(message=str(e)[:1000], title="UC-07 _notify_owner")

    @staticmethod
    def _get_recipients_by_role(role: str) -> list:
        return frappe.db.sql_list("""
            SELECT DISTINCT u.email FROM `tabUser` u
            JOIN `tabHas Role` r ON r.parent = u.name
            WHERE r.role = %s AND u.enabled = 1 AND u.email IS NOT NULL AND u.email != ''
        """, role) or []


class SCMaterialRequestItem(Document):
    pass
