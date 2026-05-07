"""SC Purchase Invoice — hóa đơn NCC + 3-way match (M8, UC-24)."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, today, now, add_days, getdate


# Tolerance & threshold (sẽ đọc từ SupplyCore Settings)
DEFAULT_MATCH_TOLERANCE_PCT = 1.0
DEFAULT_PO_OVERAGE_HARD_CAP_PCT = 5.0
DEFAULT_EXEC_THRESHOLD = 50_000_000


class SCPurchaseInvoice(Document):

    def validate(self):
        from supplycore.utils.validators import validate_supplier
        validate_supplier(self.supplier)
        self._compute_totals()
        self._auto_due_date()
        self._three_way_match()
        self._determine_approval_level()
        if self.docstatus == 0:
            self.status = "Draft"

    def on_submit(self):
        self._post_gl_entries()
        self.db_set("status", "Approved")
        self.db_set("approved_by", frappe.session.user
                    if frappe.session.user not in (None, "", "Guest") else "Administrator")
        self.db_set("approved_at", now())

    def on_cancel(self):
        from supplycore.supplycore.doctype.sc_gl_entry.sc_gl_entry import SCGLEntry
        SCGLEntry.cancel_voucher("SC Purchase Invoice", self.name)
        self.db_set("status", "Cancelled")

    # ------------------------------------------------------------------
    def _compute_totals(self):
        subtotal = 0
        for r in self.items:
            r.amount = flt(r.qty) * flt(r.rate)
            subtotal += flt(r.amount)
        self.subtotal = subtotal
        self.vat_amount = flt(subtotal) * flt(self.vat_rate or 0) / 100
        self.grand_total = self.subtotal + self.vat_amount
        # outstanding = grand_total - paid_amount
        self.outstanding_amount = flt(self.grand_total) - flt(self.paid_amount or 0)

    def _auto_due_date(self):
        if not self.due_date:
            # default 30 ngày
            self.due_date = add_days(self.invoice_date, 30)

    # ------------------------------------------------------------------
    # 3-way match: PO ↔ PR ↔ PI
    # ------------------------------------------------------------------
    def _three_way_match(self):
        if not self.purchase_order:
            self.three_way_match_status = "Not Applicable"
            self.match_variance_amount = 0
            return

        po = frappe.db.get_value("SC Purchase Order", self.purchase_order,
                                   ["grand_total", "supplier", "docstatus"], as_dict=True)
        if not po or po.docstatus != 1:
            frappe.throw(_("Purchase Order {0} không tồn tại hoặc chưa submit").format(self.purchase_order),
                         title="SC-E009")

        if po.supplier != self.supplier:
            frappe.throw(_("PO supplier ({0}) khác PI supplier ({1})").format(po.supplier, self.supplier),
                         title="SC-E009 SUPPLIER_MISMATCH")

        po_total = flt(po.grand_total)
        pi_total = flt(self.subtotal)  # so sánh trước thuế

        # PR total: cộng tất cả PR đã submit liên kết với PO này (trừ is_return)
        pr_total = flt(frappe.db.sql("""
            SELECT COALESCE(SUM(total_value), 0)
            FROM `tabSC Purchase Receipt`
            WHERE purchase_order = %s AND docstatus = 1 AND is_return = 0
        """, self.purchase_order)[0][0])

        tolerance = _get_tolerance_pct()
        po_var_pct = abs(pi_total - po_total) / po_total * 100 if po_total else 0
        pr_var_pct = abs(pi_total - pr_total) / pr_total * 100 if pr_total else 0

        self.match_variance_amount = round(max(abs(pi_total - po_total),
                                                 abs(pi_total - pr_total)), 2)

        # Hard cap: PI > PO + 5% → throw
        if pi_total > po_total * (1 + DEFAULT_PO_OVERAGE_HARD_CAP_PCT / 100):
            frappe.throw(
                _("PI subtotal ({0}) vượt PO ({1}) quá {2}%")
                .format(frappe.format(pi_total, {"fieldtype": "Currency"}),
                        frappe.format(po_total, {"fieldtype": "Currency"}),
                        DEFAULT_PO_OVERAGE_HARD_CAP_PCT),
                title="SC-E009 THREE_WAY_MISMATCH")

        if po_var_pct <= tolerance and (pr_total == 0 or pr_var_pct <= tolerance):
            self.three_way_match_status = "Match"
        else:
            self.three_way_match_status = "Mismatch"
            frappe.msgprint(
                _("3-Way mismatch: PI={0}, PO={1} ({2}%), PR={3} ({4}%)").format(
                    frappe.format(pi_total, {"fieldtype": "Currency"}),
                    frappe.format(po_total, {"fieldtype": "Currency"}),
                    round(po_var_pct, 2),
                    frappe.format(pr_total, {"fieldtype": "Currency"}),
                    round(pr_var_pct, 2),
                ), indicator="orange", alert=True)

    # ------------------------------------------------------------------
    def _determine_approval_level(self):
        threshold = _get_exec_threshold()
        if self.three_way_match_status == "Mismatch":
            self.approval_required_by = "Executive"
        elif flt(self.grand_total) >= threshold:
            self.approval_required_by = "Executive"
        elif self.three_way_match_status in ("Match", "Not Applicable"):
            self.approval_required_by = "Manager"
        else:
            self.approval_required_by = "Auto"

    # ------------------------------------------------------------------
    # GL Entry posting (VAS pattern)
    # ------------------------------------------------------------------
    def _post_gl_entries(self):
        """
          Dr 152  Hàng tồn kho       subtotal
          Dr 1331 Thuế GTGT khấu trừ vat_amount  (nếu vat>0)
             Cr 331 Phải trả NCC      grand_total
        """
        from supplycore.supplycore.doctype.sc_gl_entry.sc_gl_entry import SCGLEntry

        acc_inventory = _resolve_account("152")
        acc_vat = _resolve_account("1331")
        acc_payable = _resolve_account("331")

        if not (acc_inventory and acc_payable):
            frappe.msgprint(_("Chưa cấu hình SC GL Account 152 và 331 — bỏ qua GL post"),
                             indicator="orange", alert=True)
            return

        entries = [
            {"account": acc_inventory, "debit": flt(self.subtotal),
             "remarks": f"PI {self.name} — hàng tồn kho"},
        ]
        if flt(self.vat_amount) > 0 and acc_vat:
            entries.append({"account": acc_vat, "debit": flt(self.vat_amount),
                             "remarks": f"PI {self.name} — VAT khấu trừ"})
        entries.append({
            "account": acc_payable, "credit": flt(self.grand_total),
            "party_type": "SC Supplier", "party": self.supplier,
            "remarks": f"PI {self.name} — phải trả NCC",
        })

        SCGLEntry.post_journal(
            entries=entries,
            voucher_type="SC Purchase Invoice", voucher_no=self.name,
            posting_date=self.invoice_date,
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _get_tolerance_pct() -> float:
    return DEFAULT_MATCH_TOLERANCE_PCT


def _get_exec_threshold() -> float:
    try:
        v = frappe.db.get_single_value("SupplyCore Settings", "po_approval_threshold")
        return flt(v) if v else DEFAULT_EXEC_THRESHOLD
    except Exception:
        return DEFAULT_EXEC_THRESHOLD


def _resolve_account(code: str) -> str:
    """Tìm SC GL Account theo account_code, fallback None."""
    return frappe.db.get_value("SC GL Account", code, "name") or \
           frappe.db.get_value("SC GL Account", {"account_code": code}, "name")


# ---------------------------------------------------------------------------
# Update outstanding khi Payment Entry sync (gọi từ SC Payment Entry)
# ---------------------------------------------------------------------------
def update_outstanding(invoice_name: str):
    """Recalc paid_amount + outstanding_amount + status."""
    paid = flt(frappe.db.sql("""
        SELECT COALESCE(SUM(pr.allocated_amount), 0)
        FROM `tabSC Payment Reference` pr
        JOIN `tabSC Payment Entry` pe ON pe.name = pr.parent
        WHERE pr.purchase_invoice = %s AND pe.docstatus = 1
    """, invoice_name)[0][0])
    pi = frappe.get_doc("SC Purchase Invoice", invoice_name)
    grand = flt(pi.grand_total)
    outstanding = grand - paid
    new_status = pi.status
    if outstanding <= 0.01:
        new_status = "Paid"
    elif paid > 0:
        new_status = "Partly Paid"
    elif pi.status == "Approved" and pi.due_date and getdate(pi.due_date) < getdate(today()):
        new_status = "Overdue"
    frappe.db.set_value("SC Purchase Invoice", invoice_name, {
        "paid_amount": paid,
        "outstanding_amount": outstanding,
        "status": new_status,
    }, update_modified=False)
