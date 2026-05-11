"""SC Stock Reconciliation — đối soát tồn kho + ghi SLE adjustment + GL (M9, UC-19/28)."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class SCStockReconciliation(Document):

    def validate(self):
        self._auto_fill_system_qty()
        self._compute_per_row()
        self._compute_totals()
        self._validate_reason_per_row()
        if self.docstatus == 0 and self.status not in ("Rejected",):
            self.status = "Draft"

    def before_submit(self):
        # UC-19 step 6: Manager / Accountant role bắt buộc
        user_roles = set(frappe.get_roles(frappe.session.user))
        allowed = {"SupplyCore Manager", "SupplyCore Accountant", "System Manager"}
        if not (user_roles & allowed):
            frappe.throw(_(
                "SC-E-SR-MANAGER-REQUIRED: Submit SR yêu cầu role "
                "SupplyCore Manager / Accountant"
            ))
        # UC-19 ngoại lệ: actual_qty âm
        for r in self.items:
            if flt(r.actual_qty) < 0:
                frappe.throw(_(
                    "SC-E-SR-NEGATIVE: Item {0}: actual_qty không thể âm"
                ).format(r.item))

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

    @frappe.whitelist()
    def reject(self, reason: str = None):
        """UC-19 6a: Manager reject SR Draft kèm lý do."""
        if not reason or not str(reason).strip():
            frappe.throw(_("SC-E-SR-REJECT-REASON: Phải nhập lý do từ chối"))
        if self.docstatus != 0:
            frappe.throw(_("Chỉ reject SR ở Draft"))
        self.db_set("status", "Rejected")
        self.db_set("rejection_reason", reason)
        return {"status": "Rejected"}

    @frappe.whitelist()
    def load_from_count_sheet(self):
        """UC-19 3a: copy items từ SC Inventory Count Sheet vào SR.items."""
        if not self.count_sheet:
            frappe.throw(_("Phải set count_sheet trước"))
        if self.docstatus != 0:
            frappe.throw(_("Chỉ load khi Draft"))
        cs = frappe.get_doc("SC Inventory Count Sheet", self.count_sheet)
        self.items = []
        for ci in cs.items:
            self.append("items", {
                "item": ci.item,
                "uom": ci.uom,
                "batch": ci.batch,
                "bin_location": getattr(ci, "bin_location", None),
                "actual_qty": flt(ci.counted_qty),
                "valuation_rate": flt(getattr(ci, "valuation_rate", 0)),
            })
        self._auto_fill_system_qty()
        self._compute_per_row()
        self._compute_totals()
        self.save(ignore_permissions=False)
        return {"items_loaded": len(self.items)}

    # ------------------------------------------------------------------
    def _auto_fill_system_qty(self):
        """UC-19 step 3: auto-fill system_qty từ SC SLE."""
        for r in self.items:
            if not (r.item and self.warehouse):
                continue
            qty = flt(frappe.db.sql("""
                SELECT COALESCE(SUM(qty_change), 0)
                FROM `tabSC Stock Ledger Entry`
                WHERE item = %(item)s AND warehouse = %(wh)s AND is_cancelled = 0
                  AND (%(batch)s IS NULL OR batch = %(batch)s)
                  AND (%(bin)s IS NULL OR bin_location = %(bin)s)
            """, {"item": r.item, "wh": self.warehouse,
                   "batch": r.batch, "bin": r.bin_location})[0][0])
            r.system_qty = qty

    def _validate_reason_per_row(self):
        """UC-19 step 5: row có difference≠0 phải có reason (chỉ enforce ở submit)."""
        if self.docstatus == 0:
            return
        for r in self.items:
            if abs(flt(r.difference)) > 0.01 and not r.reason:
                frappe.throw(_(
                    "SC-E-SR-REASON-REQUIRED: Row {0} (item {1}): "
                    "phải nhập 'Lý do điều chỉnh' khi có chênh lệch"
                ).format(r.idx, r.item))

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
