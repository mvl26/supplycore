"""SC Sales Receipt -- phieu thu tien tat toan cong no phai thu (M7 Sales,
GĐ2 Task 8).

Business rules:
- amount phải > 0 và không được vượt quá sales_invoice.outstanding_amount
  (cộng dung sai epsilon để tránh lỗi làm tròn số thực).
- BRU-PAY-001: không được submit phiếu thu có receipt_date <= Settings.fiscal_lock_date
  (khóa sổ kỳ kế toán trước).

Submit: ghi 1 bút toán tự cân (post_journal):
  Dr <TK tiền mặt/ngân hàng theo mode>   amount
     Cr 131 Phải thu KH (party=customer)  amount
Giảm sales_invoice.outstanding_amount theo amount; cập nhật status:
  outstanding <= 0 (trong epsilon) -> "Đã thu đủ"
  outstanding > 0 và < grand_total -> "Đã thu một phần"
Cancel: `SCGLEntry.cancel_voucher("SC Sales Receipt", name)`; cộng lại amount vào
sales_invoice.outstanding_amount; tính lại status.
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate

EPSILON = 0.01


class SCSalesReceipt(Document):

    def validate(self):
        self._load_sales_invoice_defaults()
        self._check_amount()
        self._check_fiscal_lock()

    def on_submit(self):
        self._post_gl()
        self._settle_invoice(flt(self.amount))

    def on_cancel(self):
        from supplycore.supplycore.doctype.sc_gl_entry.sc_gl_entry import SCGLEntry

        SCGLEntry.cancel_voucher("SC Sales Receipt", self.name)
        self._settle_invoice(-flt(self.amount))

    # ------------------------------------------------------------------
    def _load_sales_invoice_defaults(self):
        if not self.sales_invoice:
            return
        si = frappe.get_doc("SC Sales Invoice", self.sales_invoice)
        if not self.customer:
            self.customer = si.customer

    # ------------------------------------------------------------------
    def _check_amount(self):
        if flt(self.amount) <= 0:
            frappe.throw(_("Số tiền thu phải lớn hơn 0."))
        if not self.sales_invoice:
            return
        si_docstatus = frappe.db.get_value("SC Sales Invoice", self.sales_invoice, "docstatus")
        if si_docstatus != 1:
            frappe.throw(_(
                "SC-E-SR-SI-NOT-SUBMITTED: Hóa đơn bán {0} chưa phát hành (chưa submit) "
                "— không thể thu tiền."
            ).format(self.sales_invoice), title="SC-E-SR-SI-NOT-SUBMITTED")
        outstanding = flt(frappe.db.get_value("SC Sales Invoice", self.sales_invoice, "outstanding_amount"))
        if flt(self.amount) > outstanding + EPSILON:
            frappe.throw(_(
                "Số tiền thu {0} vượt công nợ còn lại {1} của hóa đơn {2}."
            ).format(self.amount, outstanding, self.sales_invoice))

    # ------------------------------------------------------------------
    # BRU-PAY-001
    # ------------------------------------------------------------------
    def _check_fiscal_lock(self):
        lock = frappe.db.get_single_value("SupplyCore Settings", "fiscal_lock_date")
        if lock and self.receipt_date and getdate(self.receipt_date) <= getdate(lock):
            frappe.throw(_(
                "BRU-PAY-001: Ngày thu {0} nằm trong kỳ đã khóa sổ (khóa đến {1}) "
                "— không thể lập phiếu thu."
            ).format(self.receipt_date, lock), title="BRU-PAY-001")

    # ------------------------------------------------------------------
    def _post_gl(self):
        """
          Dr <TK tiền mặt/ngân hàng theo mode>   amount
             Cr 131 Phải thu KH (party=customer)  amount
        """
        from supplycore.supplycore.doctype.sc_gl_entry.sc_gl_entry import SCGLEntry

        acc_debit = self._resolve_debit_account()
        acc_receivable = _resolve_account("default_receivable_account", "131")
        if not (acc_debit and acc_receivable):
            frappe.msgprint(_("Chưa cấu hình tài khoản tiền/phải thu — bỏ qua GL post"),
                             indicator="orange", alert=True)
            return

        entries = [
            {"account": acc_debit, "debit": flt(self.amount),
             "remarks": f"SR {self.name} — thu tiền {self.mode}"},
            {"account": acc_receivable, "credit": flt(self.amount),
             "party_type": "SC Customer", "party": self.customer,
             "remarks": f"SR {self.name} — tất toán phải thu KH"},
        ]
        SCGLEntry.post_journal(
            entries=entries,
            voucher_type="SC Sales Receipt", voucher_no=self.name,
            posting_date=self.receipt_date,
        )

    def _resolve_debit_account(self) -> str:
        if self.mode == "Tiền mặt":
            return _resolve_account("default_cash_account", "1111")
        return _resolve_account("default_bank_account", "1121")

    # ------------------------------------------------------------------
    def _settle_invoice(self, amount_delta: float):
        """Cộng/trừ amount_delta vào outstanding_amount của sales_invoice; cập nhật status."""
        if not self.sales_invoice:
            return
        si = frappe.get_doc("SC Sales Invoice", self.sales_invoice)
        new_outstanding = flt(si.outstanding_amount) - flt(amount_delta)
        if new_outstanding < 0 and abs(new_outstanding) < EPSILON:
            new_outstanding = 0
        frappe.db.set_value("SC Sales Invoice", self.sales_invoice, "outstanding_amount", new_outstanding)

        if new_outstanding <= EPSILON:
            new_status = "Đã thu đủ"
        elif new_outstanding < flt(si.grand_total):
            new_status = "Đã thu một phần"
        else:
            new_status = "Đã phát hành"
        frappe.db.set_value("SC Sales Invoice", self.sales_invoice, "status", new_status)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _resolve_account(settings_field: str, fallback_code: str) -> str:
    """Ưu tiên SupplyCore Settings mapping, fallback theo account_code."""
    if settings_field:
        mapped = frappe.db.get_single_value("SupplyCore Settings", settings_field)
        if mapped:
            return mapped
    return frappe.db.get_value("SC GL Account", fallback_code, "name") or \
        frappe.db.get_value("SC GL Account", {"account_code": fallback_code}, "name")
