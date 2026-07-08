"""SC Sales Invoice -- hóa đơn bán hàng MVL, ghi sổ cái phải thu + COGS (M7 Sales,
GĐ2 Task 7).

Business rules:
- BRU-DEL-001: chỉ được lập hóa đơn cho Phiếu giao hàng (SC Delivery Note) đã
  ở trạng thái "Đã nghiệm thu" -- nếu chưa, validate() throw.
- BRU-INVC-001: danh mục vật tư trên hóa đơn phải khớp CHÍNH XÁC (item + qty)
  với danh mục trên Phiếu giao hàng -- lệch (thiếu/thừa/khác SL) → throw.
- BRU-SFC-002 (giá SI): unit_price của SI Item KHÔNG được tin theo giá trị Desk
  nhập -- luôn ghi đè bằng đơn giá gốc lấy từ SO Item (qua delivery_note.sales_order)
  của cùng item -- chặn Accountant sửa tay unit_price trực tiếp trên hóa đơn.
- BRU-PAY-001: không được submit hóa đơn có invoice_date <= Settings.fiscal_lock_date
  (khóa sổ kỳ kế toán trước).

Submit: ghi 2 bút toán độc lập (mỗi bút toán tự cân Nợ=Có):
  1. Bút toán phải thu: Dr 131 (party=customer) grand_total / Cr 511 total_amount
     / Cr 3331 tax_amount (nếu > 0).
  2. Bút toán giá vốn (COGS): Dr 632 cogs / Cr 156 cogs -- cogs = Σ(|qty_change| ×
     valuation_rate) của các dòng SC Stock Ledger Entry mà Phiếu giao hàng đã ghi.
Set status "Đã phát hành"; delivery_note.status = "Đã xuất HĐ".
Cancel: `SCGLEntry.cancel_voucher("SC Sales Invoice", name)` (đảo cả 2 bút toán vì
cùng voucher_type/voucher_no); trả delivery_note.status về "Đã nghiệm thu"; status "Hủy".
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class SCSalesInvoice(Document):

    def validate(self):
        self._check_dn_status()
        self._check_items_match_dn()
        self._derive_prices_from_so()
        self._compute_totals()

    def on_submit(self):
        self._check_fiscal_lock()
        self._post_ar_gl()
        self._post_cogs_gl()
        self.db_set("status", "Đã phát hành")
        if self.delivery_note:
            frappe.db.set_value("SC Delivery Note", self.delivery_note, "status", "Đã xuất HĐ")

    def before_cancel(self):
        # BRU-PAY-001: chặn TRƯỚC KHI docstatus bị ghi (before_cancel chạy
        # trước db_update, trước cả on_cancel/cancel_voucher) — nếu chặn ở
        # on_cancel thì docstatus=2 đã được ghi xuống DB rồi mới throw, để
        # lại chứng từ "Hủy" nhưng GL gốc không được đảo (không nhất quán).
        # Đặt ở đây để hủy hóa đơn không thể ghi bút toán đảo vào kỳ đã khóa
        # sổ (vd. kỳ bị khóa SAU khi đã submit) MÀ KHÔNG để lại cửa sổ
        # inconsistency nào, kể cả khi không có rollback ở tầng request.
        from supplycore.utils.fiscal import check_fiscal_lock

        check_fiscal_lock(self.invoice_date)

    def on_cancel(self):
        from supplycore.supplycore.doctype.sc_gl_entry.sc_gl_entry import SCGLEntry

        SCGLEntry.cancel_voucher("SC Sales Invoice", self.name)
        if self.delivery_note:
            frappe.db.set_value("SC Delivery Note", self.delivery_note, "status", "Đã nghiệm thu")
        self.db_set("status", "Hủy")

    # ------------------------------------------------------------------
    # BRU-DEL-001
    # ------------------------------------------------------------------
    def _check_dn_status(self):
        if not self.delivery_note:
            return
        dn_status = frappe.db.get_value("SC Delivery Note", self.delivery_note, "status")
        if dn_status != "Đã nghiệm thu":
            frappe.throw(_(
                "BRU-DEL-001: Phiếu giao hàng {0} chưa được nghiệm thu (trạng thái "
                "hiện tại: {1}) — không thể lập hóa đơn bán hàng."
            ).format(self.delivery_note, dn_status), title="BRU-DEL-001")

    # ------------------------------------------------------------------
    # BRU-INVC-001
    # ------------------------------------------------------------------
    def _check_items_match_dn(self):
        if not self.delivery_note:
            return
        dn_qty = {}
        for r in frappe.get_all("DN Item", filters={"parent": self.delivery_note},
                                  fields=["item", "qty"]):
            dn_qty[r.item] = flt(dn_qty.get(r.item, 0)) + flt(r.qty)

        si_qty = {}
        for r in self.items:
            si_qty[r.item] = flt(si_qty.get(r.item, 0)) + flt(r.qty)

        if not _qty_dicts_equal(si_qty, dn_qty):
            frappe.throw(_(
                "BRU-INVC-001: Danh mục vật tư hóa đơn không khớp với Phiếu giao "
                "hàng {0}. Hóa đơn: {1}; Phiếu giao hàng: {2}."
            ).format(self.delivery_note, si_qty, dn_qty), title="BRU-INVC-001")

    # ------------------------------------------------------------------
    # BRU-SFC-002 (giá SI) — unit_price KHÔNG được tin theo Desk, luôn derive
    # từ SO Item (giá SFC-lock) qua delivery_note.sales_order.
    # ------------------------------------------------------------------
    def _derive_prices_from_so(self):
        if not self.delivery_note:
            return
        sales_order = frappe.db.get_value("SC Delivery Note", self.delivery_note, "sales_order")
        if not sales_order:
            return
        so_price_by_item = {}
        for r in frappe.get_all("SO Item", filters={"parent": sales_order},
                                  fields=["item", "unit_price"]):
            so_price_by_item[r.item] = flt(r.unit_price)

        for row in self.items:
            if row.item not in so_price_by_item:
                frappe.throw(_(
                    "BRU-SFC-002: Vật tư {0} không có trong Đơn hàng bán {1} — không thể "
                    "xác định đơn giá gốc để lập hóa đơn."
                ).format(row.item, sales_order), title="BRU-SFC-002")
            # Ghi đè bất kể giá trị Desk đã nhập — giá luôn lấy từ SO (đã bị SFC khoá).
            row.unit_price = so_price_by_item[row.item]

    # ------------------------------------------------------------------
    def _compute_totals(self):
        """Lam tron VND (precision 0) NGAY TAI DAY -- moi Currency field VND
        (total_amount/tax_amount/grand_total/SI Item.amount) lam tron DOC LAP
        khi Frappe ghi xuong DB (vd qty=7.5 le -> total=2497.5 lam tron 2498,
        grand=2747.25 lam tron 2747 -> 2498+250 != 2747, lech 1 VND voi GL).
        Lam tron tung so hang VE SO NGUYEN truoc, roi cong don cac so nguyen
        (total_amount + tax_amount == grand_total LUON dung vi ca 2 da la so
        nguyen) -- dam bao header tu nhat quan va _post_ar_gl (doc lai chinh
        cac field da lam tron nay, khong tinh lai tu raw) post GL Dr131 =
        Cr511 + Cr3331 CHINH XAC, khong drift."""
        total = 0
        for r in self.items:
            r.amount = flt(flt(r.qty) * flt(r.unit_price), 0)
            total += flt(r.amount)
        self.total_amount = flt(total, 0)
        self.tax_amount = flt(flt(self.total_amount) * flt(self.tax_rate or 0) / 100, 0)
        self.grand_total = flt(self.total_amount) + flt(self.tax_amount)
        self.outstanding_amount = flt(self.grand_total)

    # ------------------------------------------------------------------
    # BRU-PAY-001 — dùng chung supplycore.utils.fiscal.check_fiscal_lock
    # (cùng helper với SC Sales Receipt/SC Purchase Invoice/SC Payment Entry).
    # ------------------------------------------------------------------
    def _check_fiscal_lock(self):
        from supplycore.utils.fiscal import check_fiscal_lock

        check_fiscal_lock(self.invoice_date)

    # ------------------------------------------------------------------
    # GL posting (VAS pattern)
    # ------------------------------------------------------------------
    def _post_ar_gl(self):
        """
          Dr 131 Phải thu KH (party=customer)  grand_total
             Cr 511 Doanh thu bán hàng           total_amount
             Cr 3331 Thuế GTGT phải nộp           tax_amount  (nếu > 0)
        """
        from supplycore.supplycore.doctype.sc_gl_entry.sc_gl_entry import SCGLEntry

        acc_receivable = _resolve_account("default_receivable_account", "131")
        acc_revenue = _resolve_account("default_revenue_account", "511")
        acc_tax = _resolve_account("default_tax_output_account", "3331")

        if not (acc_receivable and acc_revenue):
            frappe.msgprint(_("Chưa cấu hình SC GL Account 131 và 511 — bỏ qua GL post"),
                             indicator="orange", alert=True)
            return

        entries = [
            {"account": acc_receivable, "debit": flt(self.grand_total),
             "party_type": "SC Customer", "party": self.customer,
             "remarks": f"SI {self.name} — phải thu KH"},
            {"account": acc_revenue, "credit": flt(self.total_amount),
             "remarks": f"SI {self.name} — doanh thu bán hàng"},
        ]
        if flt(self.tax_amount) > 0 and acc_tax:
            entries.append({"account": acc_tax, "credit": flt(self.tax_amount),
                             "remarks": f"SI {self.name} — thuế GTGT đầu ra"})

        SCGLEntry.post_journal(
            entries=entries,
            voucher_type="SC Sales Invoice", voucher_no=self.name,
            posting_date=self.invoice_date,
        )

    def _post_cogs_gl(self):
        """
          Dr 632 Giá vốn hàng bán   cogs
             Cr 156 Hàng hóa          cogs
        cogs = Σ(|qty_change| × valuation_rate) của SLE mà DN đã ghi khi xuất kho.
        """
        from supplycore.supplycore.doctype.sc_gl_entry.sc_gl_entry import SCGLEntry

        cogs = self._compute_cogs()
        if flt(cogs) <= 0:
            return

        acc_cogs = _resolve_account(None, "632")
        acc_inventory = _resolve_account(None, "156")
        if not (acc_cogs and acc_inventory):
            frappe.msgprint(_("Chưa cấu hình SC GL Account 632 và 156 — bỏ qua GL post COGS"),
                             indicator="orange", alert=True)
            return

        entries = [
            {"account": acc_cogs, "debit": flt(cogs), "remarks": f"SI {self.name} — giá vốn hàng bán"},
            {"account": acc_inventory, "credit": flt(cogs), "remarks": f"SI {self.name} — xuất kho theo giá vốn"},
        ]
        SCGLEntry.post_journal(
            entries=entries,
            voucher_type="SC Sales Invoice", voucher_no=self.name,
            posting_date=self.invoice_date,
        )

    def _compute_cogs(self) -> float:
        """Σ(|qty_change| × valuation_rate) chỉ tính dòng XUẤT (qty_change < 0).

        Mirror lưu ý SC Delivery Note._reverse_stock_ledger: dòng đối ứng khi
        hủy DN vẫn giữ is_cancelled=0 (để tự triệt tiêu số lượng qua SUM), nên
        lọc thêm qty_change<0 tránh cộng luôn dòng đối ứng nhập ngược (+qty)
        nếu DN từng bị hủy trước khi lập hóa đơn (không xảy ra trên luồng bình
        thường accept→invoice vì DN phải "Đã nghiệm thu", nhưng an toàn hơn).
        """
        if not self.delivery_note:
            return 0.0
        rows = frappe.get_all(
            "SC Stock Ledger Entry",
            filters={"voucher_type": "SC Delivery Note", "voucher_no": self.delivery_note,
                     "is_cancelled": 0, "qty_change": ["<", 0]},
            fields=["qty_change", "valuation_rate"],
        )
        # Lam tron ve so nguyen VND (precision 0, giong total/tax/grand o
        # _compute_totals) -- gia tri nay tu can (Dr632=Cr156 cung 1 so vo
        # huong) nen lam tron chi de nhat quan don vi tien te, khong anh
        # huong can bang GL.
        return flt(sum(abs(flt(r.qty_change)) * flt(r.valuation_rate) for r in rows), 0)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _qty_dicts_equal(a: dict, b: dict) -> bool:
    keys = set(a.keys()) | set(b.keys())
    return all(abs(flt(a.get(k, 0)) - flt(b.get(k, 0))) < 0.0001 for k in keys)


def _resolve_account(settings_field: str, fallback_code: str) -> str:
    """Ưu tiên SupplyCore Settings mapping, fallback theo account_code."""
    if settings_field:
        mapped = frappe.db.get_single_value("SupplyCore Settings", settings_field)
        if mapped:
            return mapped
    return frappe.db.get_value("SC GL Account", fallback_code, "name") or \
        frappe.db.get_value("SC GL Account", {"account_code": fallback_code}, "name")
