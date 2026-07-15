"""SC Sales Framework Contract — Hợp đồng khung bán hàng (M7 Sales, GĐ2 Task 3)."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, today, flt


class SCSalesFrameworkContract(Document):

    def validate(self):
        self._default_contract_fields()
        self._check_validity_dates()
        self._compute_items()
        self._compute_totals()
        self._derive_status()

    def _default_contract_fields(self):
        # contract_number / contract_date là bắt buộc (giống HĐ khung mua) — nhân
        # viên nhập trên form. Với caller lập trình (seed/API/test) không truyền,
        # tự điền để không vỡ luồng: số HĐ = tên phiếu, ngày ký = ngày hiệu lực.
        if not self.contract_number:
            self.contract_number = self.name
        if not self.contract_date:
            self.contract_date = self.valid_from or today()

    def _check_validity_dates(self):
        # valid_from/valid_to là reqd (schema) — chốt thêm thứ tự ngày để không
        # tạo HĐ khung có khoảng hiệu lực âm (BRU-SFC-001 dựa trên 2 ngày này).
        if self.valid_from and self.valid_to and getdate(self.valid_to) < getdate(self.valid_from):
            frappe.throw(_(
                "Ngày hết hạn ({0}) phải >= ngày hiệu lực ({1})."
            ).format(self.valid_to, self.valid_from), title="BRU-SFC-001")

    def on_submit(self):
        self.db_set("status", "Hiệu lực")
        if not self.approved_by:
            self.db_set("approved_by", frappe.session.user)

    def on_cancel(self):
        self.db_set("status", "Thanh lý")

    # ------------------------------------------------------------------
    # Computations
    # ------------------------------------------------------------------
    def _compute_items(self):
        for row in self.items:
            row.remaining_qty = flt(row.contract_qty) - flt(row.sold_qty or 0)

    def _compute_totals(self):
        self.total_value = sum(flt(r.contract_qty) * flt(r.unit_price) for r in self.items)
        # Theo dõi giá trị (song song HĐ khung mua):
        #  - used_value  = Đã bán  = Σ SL đã bán × đơn giá (sold_qty do recalculate_sold_qty duy trì)
        #  - committed_value = Đang gọi = Σ SL trên SO 'Chờ duyệt' × đơn giá (chưa chốt)
        #  - remaining_value = Còn lại khả dụng = tổng − đã bán − đang gọi
        self.used_value = sum(flt(r.sold_qty) * flt(r.unit_price) for r in self.items)
        self.committed_value = self._compute_committed_value()
        self.remaining_value = flt(self.total_value) - flt(self.used_value) - flt(self.committed_value)

    def _compute_committed_value(self):
        """Giá trị đang gọi = các SO tham chiếu HĐ này, còn 'Chờ duyệt' (chưa chốt bán)."""
        if not self.name or not frappe.db.table_exists("SC Sales Order"):
            return 0
        price = {r.item: flt(r.unit_price) for r in self.items}
        if not price:
            return 0
        rows = frappe.db.sql("""
            SELECT soi.item AS item, COALESCE(SUM(soi.qty), 0) AS qty
            FROM `tabSO Item` soi
            JOIN `tabSC Sales Order` so ON so.name = soi.parent
            WHERE so.framework_contract = %s
              AND so.docstatus = 0
              AND so.status = 'Chờ duyệt'
            GROUP BY soi.item
        """, (self.name,), as_dict=True)
        return sum(flt(r.qty) * price.get(r.item, 0) for r in rows)

    def _derive_status(self):
        if self.docstatus == 0:
            self.status = "Nháp"
            return
        if self.docstatus == 2:
            return  # on_cancel đã db_set "Thanh lý"
        # docstatus == 1 (đã submit): chỉ chuyển "Hiệu lực" -> "Hết hạn" khi quá hạn
        if self.status == "Hiệu lực" and self.valid_to and getdate(today()) > getdate(self.valid_to):
            self.status = "Hết hạn"

    # ------------------------------------------------------------------
    # Public API — gọi từ SC Sales Order khi submit/cancel (Task 4)
    # ------------------------------------------------------------------
    @frappe.whitelist()
    def recalculate_sold_qty(self):
        """Tính lại sold_qty/remaining_qty theo SC Sales Order đã submit.

        SC Sales Order chưa tồn tại ở Task 3 — guard bằng table_exists để
        no-op an toàn (Task 4 sẽ wire lại reduction thật khi SO ra đời).
        """
        # Chặn portal gọi trực tiếp qua run_doc_method (chỉ check read) — nhất
        # quán với SC Sales Order.approve/reject. Caller nội bộ (SO submit/cancel)
        # chạy dưới session nhân viên nên không bị chặn.
        from supplycore.utils.permissions import block_portal
        block_portal()
        has_so = frappe.db.table_exists("SC Sales Order")
        used = 0
        for row in self.items:
            sold = 0
            if has_so:
                sold = frappe.db.sql("""
                    SELECT COALESCE(SUM(soi.qty), 0)
                    FROM `tabSO Item` soi
                    JOIN `tabSC Sales Order` so ON so.name = soi.parent
                    WHERE so.framework_contract = %s
                      AND so.docstatus = 1
                      AND so.status != 'Từ chối'
                      AND soi.item = %s
                """, (self.name, row.item))[0][0]
            sold = flt(sold)
            frappe.db.set_value("SFC Item", row.name, {
                "sold_qty": sold,
                "remaining_qty": flt(row.contract_qty) - sold,
            })
            used += sold * flt(row.unit_price)
        # Đồng bộ giá trị theo dõi ở HĐ cha (used/committed/remaining) sau khi cập
        # nhật sold_qty — dùng db.set_value nên không đụng docstatus/validate.
        committed = self._compute_committed_value()
        frappe.db.set_value("SC Sales Framework Contract", self.name, {
            "used_value": used,
            "committed_value": committed,
            "remaining_value": flt(self.total_value) - used - committed,
        }, update_modified=False)
