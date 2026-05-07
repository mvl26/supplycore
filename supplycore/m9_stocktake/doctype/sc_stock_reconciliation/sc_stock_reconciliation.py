"""SC Stock Reconciliation — đối soát tồn kho + ghi SLE adjustment + GL (M9, UC-19/28)."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class SCStockReconciliation(Document):

    def validate(self):
        self._compute_per_row()
        self._compute_totals()
        if self.docstatus == 0:
            self.status = "Draft"

    def on_submit(self):
        self._post_stock_ledger()
        self._post_gl_entries()
        self.db_set("status", "Approved")
        # Update ICS link nếu có
        if self.count_sheet and frappe.db.exists("SC Inventory Count Sheet", self.count_sheet):
            frappe.db.set_value("SC Inventory Count Sheet", self.count_sheet,
                                 "status", "Reconciled")

    def on_cancel(self):
        from supplycore.supplycore.doctype.sc_gl_entry.sc_gl_entry import SCGLEntry
        self._reverse_stock_ledger()
        SCGLEntry.cancel_voucher("SC Stock Reconciliation", self.name)
        self.db_set("status", "Cancelled")
        if self.count_sheet:
            frappe.db.set_value("SC Inventory Count Sheet", self.count_sheet, "status", "Counted")

    # ------------------------------------------------------------------
    def _compute_per_row(self):
        for r in self.items:
            r.difference = flt(r.actual_qty) - flt(r.system_qty)
            r.amount_change = flt(r.difference) * flt(r.valuation_rate)

    def _compute_totals(self):
        self.total_difference_qty = sum(flt(r.difference) for r in self.items)
        self.total_difference_value = sum(flt(r.amount_change) for r in self.items)

    # ------------------------------------------------------------------
    def _post_stock_ledger(self):
        from supplycore.supplycore.doctype.sc_stock_ledger_entry.sc_stock_ledger_entry import SCStockLedgerEntry
        for r in self.items:
            if abs(flt(r.difference)) < 0.01:
                continue
            SCStockLedgerEntry.post(
                item=r.item, warehouse=self.warehouse,
                qty_change=flt(r.difference), valuation_rate=flt(r.valuation_rate),
                voucher_type="SC Stock Reconciliation",
                voucher_no=self.name, voucher_detail_no=r.name,
                batch=r.batch, bin_location=r.bin_location,
                posting_date=self.posting_date, posting_time=self.posting_time,
                remarks=f"Stocktake adjustment: {r.reason or 'unspecified'}",
            )

    def _reverse_stock_ledger(self):
        sles = frappe.get_all("SC Stock Ledger Entry",
            filters={"voucher_type": "SC Stock Reconciliation",
                     "voucher_no": self.name, "is_cancelled": 0},
            fields=["name", "item", "warehouse", "batch", "bin_location",
                    "qty_change", "valuation_rate"])
        from supplycore.supplycore.doctype.sc_stock_ledger_entry.sc_stock_ledger_entry import SCStockLedgerEntry
        for s in sles:
            SCStockLedgerEntry.post(
                item=s.item, warehouse=s.warehouse,
                qty_change=-flt(s.qty_change), valuation_rate=flt(s.valuation_rate),
                voucher_type="SC Stock Reconciliation", voucher_no=self.name,
                voucher_detail_no=s.name + "-CANCEL",
                batch=s.batch, bin_location=s.bin_location,
                remarks=f"Cancel SLE {s.name}",
            )
            frappe.db.set_value("SC Stock Ledger Entry", s.name, "is_cancelled", 1)

    # ------------------------------------------------------------------
    def _post_gl_entries(self):
        """
        Tổng Δ giá trị > 0 (thừa kho):
            Dr 152 Hàng tồn kho       |total|
                Cr 642 CP QLDN (hoặc 711 TN khác)
        Tổng Δ giá trị < 0 (thiếu kho):
            Dr 642 CP QLDN            |total|
                Cr 152 Hàng tồn kho
        """
        from supplycore.supplycore.doctype.sc_gl_entry.sc_gl_entry import SCGLEntry

        delta = flt(self.total_difference_value)
        if abs(delta) < 0.01:
            return

        acc_inventory = _resolve_account("152")
        acc_expense = self.expense_account or _resolve_account("642")

        if not (acc_inventory and acc_expense):
            frappe.msgprint(_("Chưa cấu hình SC GL Account 152/642 — bỏ qua GL post"),
                             indicator="orange", alert=True)
            return

        if delta > 0:
            entries = [
                {"account": acc_inventory, "debit": abs(delta),
                 "remarks": f"SR {self.name} — thừa tồn kho"},
                {"account": acc_expense, "credit": abs(delta),
                 "remarks": f"SR {self.name} — ghi nhận TN bất thường"},
            ]
        else:
            entries = [
                {"account": acc_expense, "debit": abs(delta),
                 "remarks": f"SR {self.name} — thiếu tồn kho"},
                {"account": acc_inventory, "credit": abs(delta),
                 "remarks": f"SR {self.name} — giảm tồn kho thiếu hụt"},
            ]
        SCGLEntry.post_journal(
            entries=entries,
            voucher_type="SC Stock Reconciliation", voucher_no=self.name,
            posting_date=self.posting_date,
        )


def _resolve_account(code: str) -> str:
    return frappe.db.get_value("SC GL Account", code, "name") or \
           frappe.db.get_value("SC GL Account", {"account_code": code}, "name")
