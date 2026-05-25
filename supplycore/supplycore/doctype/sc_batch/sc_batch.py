import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, today, now, date_diff, flt


class SCBatch(Document):

    def validate(self):
        self._validate_batch_id_chars()
        self._ensure_barcode()
        if self.expiry_date and self.manufacturing_date:
            if getdate(self.expiry_date) <= getdate(self.manufacturing_date):
                frappe.throw(_("Hạn dùng phải sau ngày sản xuất"))
        if self.blocked and not self.block_reason:
            frappe.throw(_("Phải ghi lý do khi block batch"))
        if self.blocked and not self.blocked_by:
            self.blocked_by = frappe.session.user
            self.blocked_at = now()
        if not self.blocked:
            self.blocked_by = None
            self.blocked_at = None

        # UC-15
        self._compute_short_expiry()
        self._warn_duplicate_supplier_batch_no()
        self._enforce_short_expiry_ack()

    def _validate_batch_id_chars(self):
        """QA-BUG-M5-02/03: batch_id không được chứa ký tự đặc biệt URL.

        '/', '\\', '?', '#', '%' gây lỗi routing khi mở /doc/SC Batch/<id>.
        Cho phép letters/digits/dash/underscore/dot.
        """
        if not self.batch_id:
            return
        import re
        if re.search(r"[/\\?#%]", self.batch_id):
            frappe.throw(_(
                "SC-E020 BATCH_ID_INVALID_CHAR: Batch ID '{0}' chứa ký tự "
                "đặc biệt (/, \\, ?, #, %%) — gây lỗi URL routing. "
                "Chỉ dùng chữ, số, dấu '-', '_', '.'"
            ).format(self.batch_id), title="SC-E020 BATCH_ID_INVALID_CHAR")

    def _ensure_barcode(self):
        """Tự sinh barcode = batch_id khi tạo lô (nếu chưa có).

        Áp dụng cho mọi đường tạo lô: thủ công trên form, hoặc tự động khi
        tiếp nhận (SC Purchase Receipt._create_batches_if_needed gọi b.insert()
        → validate này chạy). User vẫn có thể đè bằng mã GS1 riêng.
        """
        if not self.barcode and self.batch_id:
            self.barcode = self.batch_id

    def _enforce_short_expiry_ack(self):
        """UC-15 4a: block insert nếu short expiry chưa ack."""
        if not self.is_short_expiry:
            return
        if not self.is_new():
            return
        if self.flags.get("ignore_short_expiry"):
            return
        if self.expiry_warning_ack:
            if not self.acknowledged_by:
                self.acknowledged_by = frappe.session.user
                self.acknowledged_at = now()
            return
        frappe.throw(_(
            "SC-E-BATCH-SHORT-EXPIRY: Hạn dùng còn <6 tháng — "
            "Manager xác nhận (tick 'Xác nhận nhập lô hạn ngắn') trước khi tạo"
        ))

    def _compute_short_expiry(self):
        if not self.expiry_date:
            self.is_short_expiry = 0
            return
        days = date_diff(self.expiry_date, today())
        self.is_short_expiry = 1 if days < 180 else 0
        if self.is_short_expiry and self.is_new():
            frappe.msgprint(
                _("⚠ Hạn dùng còn {0} ngày (<6 tháng) — cần Manager xác nhận").format(days),
                indicator="red", alert=True,
            )

    def _warn_duplicate_supplier_batch_no(self):
        if not self.supplier_batch_no or not self.item:
            return
        if not self.is_new():
            return
        existing = frappe.db.sql("""
            SELECT name, batch_id, expiry_date, qc_status
            FROM `tabSC Batch`
            WHERE item = %s AND supplier_batch_no = %s
              AND disabled = 0 AND name != %s
            LIMIT 5
        """, (self.item, self.supplier_batch_no, self.name or ""), as_dict=True)
        if existing:
            names = ", ".join(b.batch_id for b in existing)
            frappe.msgprint(
                _("⚠ Số lô NCC '{0}' đã tồn tại với batch: {1}. "
                  "Cân nhắc dùng lô cũ thay vì tạo mới.").format(
                    self.supplier_batch_no, names),
                indicator="orange", alert=True,
            )

    def get_qty_at_warehouse(self, warehouse: str) -> float:
        """Trả tồn kho lô tại warehouse từ SC Stock Ledger Entry."""
        return flt(frappe.db.sql("""
            SELECT COALESCE(SUM(qty_change), 0)
            FROM `tabSC Stock Ledger Entry`
            WHERE batch = %s AND warehouse = %s AND is_cancelled = 0
        """, (self.name, warehouse))[0][0])

    @frappe.whitelist()
    def get_batch_label_data(self):
        """UC-15 step 4: return label data for printing."""
        return {
            "batch_id": self.batch_id,
            "barcode": self.barcode or self.batch_id,
            "item": self.item,
            "item_name": self.item_name,
            "manufacturer": self.manufacturer,
            "supplier_batch_no": self.supplier_batch_no,
            "manufacturing_date": str(self.manufacturing_date) if self.manufacturing_date else "",
            "expiry_date": str(self.expiry_date) if self.expiry_date else "",
            "qc_status": self.qc_status,
            "url": f"/app/sc-batch/{self.name}",
        }
