"""SC Payment Entry — thanh toán NCC + GL post + sync PI outstanding (M8, UC-25)."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, now


EXEC_THRESHOLD_DEFAULT = 50_000_000


class SCPaymentEntry(Document):

    def validate(self):
        from supplycore.utils.validators import validate_supplier
        validate_supplier(self.supplier)
        self._compute_allocated_total()
        self._validate_references()
        self._determine_approval_level()
        if self.docstatus == 0:
            self.status = "Draft"

    def before_submit(self):
        # UC-25 step 5/5a: enforce role theo approval_level
        user_roles = set(frappe.get_roles(frappe.session.user))
        if self.approval_level == "Executive":
            allowed = {"SupplyCore Executive", "System Manager"}
            if not (user_roles & allowed):
                frappe.throw(_(
                    "SC-E-PE-EXECUTIVE-REQUIRED: Submit PE ≥ ngưỡng yêu cầu role "
                    "SupplyCore Executive"
                ))
        elif self.approval_level == "Manager":
            allowed = {"SupplyCore Manager", "SupplyCore Executive", "System Manager"}
            if not (user_roles & allowed):
                frappe.throw(_(
                    "SC-E-PE-MANAGER-REQUIRED: Submit PE yêu cầu role SupplyCore Manager"
                ))
        # UC-25 ngoại lệ: bank balance warning (không block)
        self._check_bank_balance()

    def on_submit(self):
        self._post_gl_entries()
        self._update_invoices()
        self.db_set("status", "Approved")
        self.db_set("approved_by", frappe.session.user
                    if frappe.session.user not in (None, "", "Guest") else "Administrator")
        self.db_set("approved_at", now())

    def on_cancel(self):
        from supplycore.supplycore.doctype.sc_gl_entry.sc_gl_entry import SCGLEntry
        SCGLEntry.cancel_voucher("SC Payment Entry", self.name)
        # Revert PI outstanding
        for ref in self.references:
            from supplycore.m8_accounting.doctype.sc_purchase_invoice.sc_purchase_invoice import update_outstanding
            update_outstanding(ref.purchase_invoice)
        self.db_set("status", "Cancelled")

    # ------------------------------------------------------------------
    def _compute_allocated_total(self):
        self.allocated_total = sum(flt(r.allocated_amount) for r in self.references)
        if self.docstatus == 1 and abs(flt(self.amount) - flt(self.allocated_total)) > 0.01:
            frappe.throw(_("Tổng phân bổ ({0}) ≠ Số tiền thanh toán ({1})").format(
                self.allocated_total, self.amount))

    def _validate_references(self):
        """Verify mỗi PI thuộc đúng supplier + outstanding ≥ allocated + không hold."""
        for ref in self.references:
            pi = frappe.db.get_value("SC Purchase Invoice", ref.purchase_invoice,
                                       ["supplier", "grand_total", "outstanding_amount",
                                        "docstatus", "payment_hold"], as_dict=True)
            if not pi or pi.docstatus != 1:
                frappe.throw(_("PI {0} không tồn tại hoặc chưa submit").format(ref.purchase_invoice))
            if pi.supplier != self.supplier:
                frappe.throw(_("PI {0} thuộc NCC khác: {1}").format(ref.purchase_invoice, pi.supplier))
            # UC-25 carry from UC-24: PI hold → block
            if pi.payment_hold:
                frappe.throw(_(
                    "SC-E-PE-PAYMENT-HOLD: PI {0} đang hold thanh toán "
                    "(3-way mismatch chưa release)"
                ).format(ref.purchase_invoice))
            ref.invoice_total = flt(pi.grand_total)
            ref.outstanding_before = flt(pi.outstanding_amount)
            if flt(ref.allocated_amount) > flt(pi.outstanding_amount) + 0.01:
                frappe.throw(_("Phân bổ {0} cho PI {1} > còn phải trả {2}").format(
                    ref.allocated_amount, ref.purchase_invoice, pi.outstanding_amount))
            ref.outstanding_after = flt(pi.outstanding_amount) - flt(ref.allocated_amount)

    def _check_bank_balance(self):
        """UC-25 ngoại lệ: msgprint warn nếu bank balance < amount (KHÔNG block)."""
        if self.payment_method != "Bank Transfer":
            return
        acc = _resolve_account("1121")
        if not acc:
            return
        try:
            balance = flt(frappe.db.sql("""
                SELECT COALESCE(SUM(debit) - SUM(credit), 0)
                FROM `tabSC GL Entry`
                WHERE account = %s AND is_cancelled = 0
            """, acc)[0][0])
        except Exception:
            return
        if balance < flt(self.amount):
            frappe.msgprint(
                _("⚠ Số dư TK {0} hiện tại {1} thấp hơn số tiền PE ({2}). "
                  "Tiếp tục submit nhưng cần kiểm tra dòng tiền.").format(
                    acc,
                    frappe.format(balance, {"fieldtype": "Currency"}),
                    frappe.format(self.amount, {"fieldtype": "Currency"})),
                indicator="orange", alert=True,
            )

    def _determine_approval_level(self):
        threshold = _get_exec_threshold()
        self.approval_level = "Executive" if flt(self.amount) >= threshold else "Manager"

    # ------------------------------------------------------------------
    def _post_gl_entries(self):
        """Dr 331 Phải trả NCC (per PI)
              Cr 1121 Tiền gửi NH (Bank Transfer) hoặc 1111 (Cash)
        """
        from supplycore.supplycore.doctype.sc_gl_entry.sc_gl_entry import SCGLEntry
        acc_payable = _resolve_account("331")
        acc_bank = _resolve_account("1121") if self.payment_method == "Bank Transfer" else _resolve_account("1111")

        if not (acc_payable and acc_bank):
            frappe.msgprint(_("Chưa cấu hình SC GL Account 331 và 1111/1121 — bỏ qua GL post"),
                             indicator="orange", alert=True)
            return

        entries = []
        # Dr 331 — 1 entry per PI để tracking
        for ref in self.references:
            entries.append({
                "account": acc_payable, "debit": flt(ref.allocated_amount),
                "party_type": "SC Supplier", "party": self.supplier,
                "voucher_detail_no": ref.name,
                "remarks": f"PE {self.name} — clear PI {ref.purchase_invoice}",
            })
        # Cr bank/cash — 1 entry tổng
        entries.append({
            "account": acc_bank, "credit": flt(self.amount),
            "remarks": f"PE {self.name} — chi qua {self.payment_method}",
        })
        SCGLEntry.post_journal(
            entries=entries,
            voucher_type="SC Payment Entry", voucher_no=self.name,
            posting_date=self.payment_date,
        )

    def _update_invoices(self):
        from supplycore.m8_accounting.doctype.sc_purchase_invoice.sc_purchase_invoice import update_outstanding
        for ref in self.references:
            update_outstanding(ref.purchase_invoice)


def _get_exec_threshold() -> float:
    try:
        v = frappe.db.get_single_value("SupplyCore Settings", "po_approval_threshold")
        return flt(v) if v else EXEC_THRESHOLD_DEFAULT
    except Exception:
        return EXEC_THRESHOLD_DEFAULT


def _resolve_account(code: str) -> str:
    return frappe.db.get_value("SC GL Account", code, "name") or \
           frappe.db.get_value("SC GL Account", {"account_code": code}, "name")


@frappe.whitelist()
def auto_load_outstanding_invoices(supplier: str, limit: int = 50) -> list:
    """UC-25 step 2: list PI outstanding của supplier (sorted by due_date ASC).
    Loại bỏ PI có payment_hold=1."""
    rows = frappe.db.sql("""
        SELECT name, supplier_invoice_no, invoice_date, due_date,
               grand_total, paid_amount, outstanding_amount,
               three_way_match_status, payment_hold
        FROM `tabSC Purchase Invoice`
        WHERE supplier = %s
          AND docstatus = 1
          AND outstanding_amount > 0
          AND COALESCE(payment_hold, 0) = 0
        ORDER BY due_date ASC LIMIT %s
    """, (supplier, int(limit)), as_dict=True)
    return rows
