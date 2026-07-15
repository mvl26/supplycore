"""SC Purchase Invoice — hóa đơn NCC + 3-way match (M8, UC-24)."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, today, now, add_days, getdate

from supplycore.utils.permissions import block_portal


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
        self._set_payment_hold()
        self._determine_approval_level()
        self._validate_duplicate_invoice()
        if self.docstatus == 0:
            self.status = "Draft"

    def before_submit(self):
        # BRU-PAY-001: không được submit hóa đơn mua có invoice_date nằm
        # trong kỳ đã khóa sổ (mirror SC Sales Invoice/SC Sales Receipt —
        # trước fix này PI KHÔNG có check này, chỉ SI/SR có).
        from supplycore.utils.fiscal import check_fiscal_lock
        check_fiscal_lock(self.invoice_date)

        # UC-24 step 6: mismatch/force approved → require explanation
        if self.three_way_match_status in ("Mismatch", "Force Approved"):
            if not (self.mismatch_explanation and str(self.mismatch_explanation).strip()):
                frappe.throw(_(
                    "SC-E-PI-MISMATCH-EXPLANATION: Phải nhập 'Giải trình chênh lệch' "
                    "khi 3-way match không khớp"
                ))
        # BUG-006: chặn submit Hóa đơn mua có grand_total = 0 (trừ debit/credit note
        # trả hàng). Hóa đơn 0đ tạo dữ liệu rác trong báo cáo công nợ NCC.
        # (SC Purchase Invoice không có field is_return — cờ trả hàng là
        #  is_debit_note / is_credit_note.)
        is_return_note = bool(self.get("is_debit_note") or self.get("is_credit_note"))
        if not is_return_note and flt(self.grand_total) <= 0:
            frappe.throw(_(
                "SC-E015 ZERO_INVOICE_TOTAL: Hóa đơn mua phải có Tổng > 0 "
                "(hiện {0}). Kiểm tra lại các dòng vật tư + đơn giá. "
                "Nếu là phiếu trả hàng, đánh dấu 'Debit Note' hoặc 'Credit Note'."
            ).format(self.grand_total), title="SC-E015 ZERO_INVOICE_TOTAL")

    def _validate_duplicate_invoice(self):
        """UC-24 ngoại lệ: unique (supplier, supplier_invoice_no)."""
        if not (self.supplier and self.supplier_invoice_no):
            return
        existing = frappe.db.sql("""
            SELECT name FROM `tabSC Purchase Invoice`
            WHERE supplier = %s AND supplier_invoice_no = %s
              AND name != %s AND docstatus != 2
            LIMIT 1
        """, (self.supplier, self.supplier_invoice_no, self.name or ""))
        if existing:
            frappe.throw(_(
                "SC-E-PI-DUPLICATE: HĐ NCC số '{0}' của NCC {1} đã có trong PI {2}"
            ).format(self.supplier_invoice_no, self.supplier, existing[0][0]))

    def _set_payment_hold(self):
        """UC-24 6a: auto payment_hold khi Mismatch."""
        if self.three_way_match_status == "Mismatch":
            self.payment_hold = 1
        elif self.three_way_match_status not in ("Force Approved",):
            self.payment_hold = 0

    def on_submit(self):
        self._post_gl_entries()
        self.db_set("status", "Approved")
        self.db_set("approved_by", frappe.session.user
                    if frappe.session.user not in (None, "", "Guest") else "Administrator")
        self.db_set("approved_at", now())

    def before_cancel(self):
        # BRU-PAY-001: chặn TRƯỚC KHI docstatus bị ghi (before_cancel chạy
        # trước db_update/on_cancel — xem lý do trong SC Sales Invoice.before_cancel).
        from supplycore.utils.fiscal import check_fiscal_lock
        check_fiscal_lock(self.invoice_date)

    def on_cancel(self):
        from supplycore.supplycore.doctype.sc_gl_entry.sc_gl_entry import SCGLEntry
        SCGLEntry.cancel_voucher("SC Purchase Invoice", self.name)
        self.db_set("status", "Cancelled")

    # ------------------------------------------------------------------
    def _compute_totals(self):
        # Làm tròn VND (precision 0) NGAY tại tính toán để field lưu DB và GL
        # nhất quán từ 1 nguồn — tránh lệch 1 VND do mỗi Currency field làm tròn
        # độc lập khi qty lẻ (mirror SC Sales Invoice._compute_totals).
        subtotal = 0
        for r in self.items:
            r.amount = flt(flt(r.qty) * flt(r.rate), 0)
            subtotal += flt(r.amount)
        self.subtotal = flt(subtotal, 0)
        self.vat_amount = flt(flt(self.subtotal) * flt(self.vat_rate or 0) / 100, 0)
        self.grand_total = flt(self.subtotal) + flt(self.vat_amount)
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
        elif self.three_way_match_status == "Match":
            # UC-24 step 5: Match → Auto (kế toán submit không cần thêm duyệt)
            self.approval_required_by = "Auto"
        elif self.three_way_match_status == "Not Applicable":
            self.approval_required_by = "Manager"
        else:
            self.approval_required_by = "Auto"

    # ------------------------------------------------------------------
    # GL Entry posting (VAS pattern)
    # ------------------------------------------------------------------
    def _post_gl_entries(self):
        """
          Hóa đơn mua thường:
            Dr 152  Hàng tồn kho       subtotal
            Dr 1331 Thuế GTGT khấu trừ vat_amount  (nếu vat>0)
               Cr 331 Phải trả NCC      grand_total

          Debit/Credit Note trả hàng NCC (is_debit_note/is_credit_note=1):
          hàng đi NGƯỢC trở lại NCC → GL đảo chiều so với hóa đơn mua thường:
            Dr 331 Phải trả NCC        grand_total  (giảm công nợ phải trả)
               Cr 152 Hàng tồn kho       subtotal      (giảm tồn kho)
               Cr 1331 Thuế GTGT khấu trừ vat_amount (nếu vat>0, giảm khấu trừ)
        """
        from supplycore.supplycore.doctype.sc_gl_entry.sc_gl_entry import SCGLEntry

        acc_inventory = _resolve_account("152")
        acc_vat = _resolve_account("1331")
        acc_payable = _resolve_account("331")

        if not (acc_inventory and acc_payable):
            frappe.msgprint(_("Chưa cấu hình SC GL Account 152 và 331 — bỏ qua GL post"),
                             indicator="orange", alert=True)
            return

        is_return_note = bool(self.get("is_debit_note") or self.get("is_credit_note"))

        if is_return_note:
            # Trả hàng NCC: đảo ngược bút toán mua hàng thường — payable
            # GIẢM (Dr 331), tồn kho GIẢM (Cr 152), VAT khấu trừ GIẢM (Cr 1331).
            entries = [
                {"account": acc_payable, "debit": flt(self.grand_total),
                 "party_type": "SC Supplier", "party": self.supplier,
                 "remarks": f"PI {self.name} — trả hàng NCC, giảm phải trả"},
                {"account": acc_inventory, "credit": flt(self.subtotal),
                 "remarks": f"PI {self.name} — giảm hàng tồn kho (trả hàng)"},
            ]
            if flt(self.vat_amount) > 0 and acc_vat:
                entries.append({"account": acc_vat, "credit": flt(self.vat_amount),
                                 "remarks": f"PI {self.name} — giảm VAT khấu trừ (trả hàng)"})
        else:
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
# Helper: tạo PI draft từ 1 SC Purchase Receipt (M3 → M8 wiring)
# ---------------------------------------------------------------------------
@frappe.whitelist()
def make_invoice_from_pr(pr_name: str) -> str:
    """Tạo SC Purchase Invoice draft từ PR đã submit + accepted QC.

    Auto-fetch:
      - Parent: supplier, supplier_name, purchase_order, purchase_receipt
      - Per item: item_name, warehouse, batch_no (từ PR Item)
      - pr_item_ref (=PR Item.name), po_item_ref (=PR Item.po_item_ref)

    Returns: tên PI draft (chưa submit — user review rồi submit để post GL).

    GĐ4 Task 5 (security sweep): hàm module-level WRITE (tạo PI draft với
    `ignore_permissions=True`) — KHÔNG qua `run_doc_method` nên không tự động
    check permission gì. Không gate thì bất kỳ user đăng nhập nào (kể cả
    Portal) truyền `pr_name` bất kỳ sẽ đọc được PR nội bộ + TẠO ĐƯỢC hóa đơn
    NCC thật trong hệ thống — vừa lộ dữ liệu vừa ghi dữ liệu trái phép.
    """
    block_portal()
    pr = frappe.get_doc("SC Purchase Receipt", pr_name)
    if pr.docstatus != 1:
        frappe.throw(_("PR {0} chưa submit").format(pr_name), title="SC-E-PR")
    # Hỏng TOÀN BỘ (PR.qc_status = "Fail") -> không tạo hoá đơn (mọi dòng trả NCC).
    # (Trước đây check "Rejected" là giá trị PR không bao giờ có -> check chết.)
    if pr.qc_status == "Fail":
        frappe.throw(_("PR {0} bị QC Từ chối toàn bộ — không tạo hoá đơn (xử lý bằng Trả NCC).")
                      .format(pr_name), title="SC-E007 QC_REJECTED")
    # Check duplicate
    existing = frappe.db.get_value("SC Purchase Invoice",
                                     {"purchase_receipt": pr_name, "docstatus": ["!=", 2]}, "name")
    if existing:
        frappe.throw(_("PI đã tồn tại cho PR này: {0}").format(existing),
                      title="SC-E007 PI_DUPLICATE")

    pi = frappe.new_doc("SC Purchase Invoice")
    pi.supplier = pr.supplier
    pi.supplier_name = frappe.db.get_value("SC Supplier", pr.supplier, "supplier_name")
    pi.purchase_order = pr.purchase_order
    pi.purchase_receipt = pr_name
    pi.supplier_invoice_no = f"AUTO-{pr_name}"  # placeholder, user sửa lại
    pi.invoice_date = today()
    pi.due_date = add_days(today(), 30)
    pi.vat_rate = 10  # default VAT VN
    pi.remarks = _("Tự tạo từ PR {0} (kho nhập: {1})").format(
        pr_name, pr.to_warehouse or "—")
    skipped = []
    for r in pr.items:
        # LOẠI dòng có lô bị QC Từ chối (Rejected) — hàng này đã/đang TRẢ NCC nên
        # KHÔNG đưa vào hoá đơn mua (không trả tiền hàng đã trả lại). Chỉ lập hoá
        # đơn cho phần ĐẠT (Accepted/Conditional) hoặc dòng không có lô/không QC.
        if r.batch_no and frappe.db.get_value("SC Batch", r.batch_no, "qc_status") == "Rejected":
            skipped.append(r.item)
            continue
        pi.append("items", {
            "item": r.item,
            "item_name": getattr(r, "item_name", None) or
                          frappe.db.get_value("SC Item", r.item, "item_name"),
            "qty": r.qty,
            "uom": r.uom,
            "rate": r.rate,
            "amount": flt(r.qty) * flt(r.rate),
            "warehouse": r.warehouse or pr.to_warehouse,
            "batch_no": r.batch_no,
            "po_item_ref": r.po_item_ref,
            "pr_item_ref": r.name,
        })
    if not pi.items:
        frappe.throw(_("Không có dòng vật tư ĐẠT để lập hoá đơn (mọi dòng đã bị QC từ chối / trả NCC)."),
                      title="SC-E007 QC_REJECTED")
    if skipped:
        pi.remarks += _(" · Đã LOẠI khỏi hoá đơn (QC từ chối, trả NCC): {0}").format(", ".join(skipped))
    pi.flags.ignore_permissions = True
    pi.insert()
    return pi.name


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
