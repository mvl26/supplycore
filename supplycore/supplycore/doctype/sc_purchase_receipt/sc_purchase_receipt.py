"""SC Purchase Receipt — replaces ERPNext PR.

Submit:
  1. Tự tạo SC Batch nếu row có expiry_date + chưa có batch_no
  2. Ghi SC Stock Ledger Entry (+qty)
  3. Auto-tạo SC Quality Inspection cho mọi item nếu qc_required=1 (M3)
  4. Cập nhật received_qty cho SC Purchase Order Item
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, today, getdate

# 5 tiêu chí QC nhập kho mẫu — seed sẵn cho mỗi SC Quality Inspection auto-tạo (KCS thêm/bớt được).
# Giữ ĐỒNG BỘ với frontend schemas.js → 'SC Quality Inspection'.items.defaultRows
_DEFAULT_QI_CRITERIA = [
    "Bao bì, nhãn mác nguyên vẹn, đầy đủ thông tin",
    "Số lô khớp chứng từ",
    "Hạn sử dụng còn đủ theo quy định",
    "Quy cách, số lượng đúng đặt hàng",
    "Cảm quan đạt (màu sắc, hình thức, không hư hỏng/biến chất)",
]


class SCPurchaseReceipt(Document):

    def validate(self):
        from supplycore.utils.validators import validate_supplier, validate_warehouse
        validate_supplier(self.supplier)
        validate_warehouse(self.to_warehouse, label=_("Kho đích"))
        self._compute_totals()
        self._validate_expiry()
        self._compute_over_receipt()
        self._warn_no_po()
        if self.docstatus == 0 and not self.qc_status:
            self.qc_status = "Pending"

    def _warn_no_po(self):
        """QAv3-BUG-M3-11: cảnh báo (không block) khi tạo PR không có PO.

        Kiểm soát nội bộ 3 chiều (PO-GR-Invoice) yêu cầu PO tham chiếu.
        Trường hợp đặc biệt (mua khẩn cấp, mẫu thử) phải nhập no_po_reason
        — đã có before_submit check. Đây là msgprint cảnh báo sớm.
        """
        if self.docstatus != 0:
            return
        if self.is_return:
            return
        if not self.purchase_order:
            frappe.msgprint(
                _("⚠ PR chưa có PO tham chiếu. Mua sắm có PO là chuẩn kiểm "
                  "soát nội bộ 3 chiều (PO ↔ GR ↔ Invoice). Nếu mua khẩn cấp "
                  "/ không có PO, vui lòng nhập 'Lý do không có PO' trước khi submit."),
                indicator="orange", alert=True,
            )

    def before_submit(self):
        if self.has_over_receipt and not self.over_receipt_acknowledged:
            frappe.throw(_(
                "SC-E-OVER-RECEIPT: Một số item nhận vượt SL PO. "
                "Tick 'Xác nhận over-receipt' (cần Manager) để tiếp tục."
            ))
        if not self.purchase_order and not self.is_return:
            if not (self.no_po_reason and str(self.no_po_reason).strip()):
                frappe.throw(_(
                    "SC-E-NO-PO-REASON: PR không có PO — vui lòng nhập 'Lý do không có PO'"
                ))
        if self.is_return:
            if not (self.return_reason and str(self.return_reason).strip()):
                frappe.throw(_("SC-E-RETURN-REASON: Phải nhập 'Lý do trả hàng'"))
        # Mỗi dòng vật tư phải có Hạn dùng — phiếu nhập sinh 1 lô / 1 dòng item
        # (đơn N item → N lô). SC Batch bắt buộc expiry_date nên đây là tiền đề.
        # BUG-005: item có quản lý lô (has_batch_no=1) bắt buộc supplier_batch_no
        # để truy xuất nguồn gốc (Thông tư 22/2011/TT-BYT). Manufacturer là
        # thông tin nên có nhưng không bắt buộc — capture vào batch nếu nhập.
        missing_expiry, missing_supplier_batch = [], []
        for r in self.items:
            if r.batch_no:
                continue  # đã có lô — info đã ở batch, OK
            if not r.expiry_date:
                missing_expiry.append(r.idx)
            has_batch = frappe.db.get_value("SC Item", r.item, "has_batch_no")
            if has_batch:
                if not (r.supplier_batch_no and str(r.supplier_batch_no).strip()):
                    missing_supplier_batch.append(r.idx)
        if missing_expiry and not self.is_return:
            frappe.throw(_(
                "SC-E-PR-MISSING-EXPIRY: Các dòng {0} chưa nhập Hạn dùng. "
                "Mỗi dòng vật tư cần Hạn dùng để hệ thống tự sinh lô tương ứng "
                "khi nhập kho."
            ).format(missing_expiry))
        if missing_supplier_batch and not self.is_return:
            frappe.throw(_(
                "SC-E014 SUPPLIER_BATCH_REQUIRED: Các dòng {0} thiếu 'Số lô NCC'. "
                "Item có quản lý lô bắt buộc nhập Số lô NCC để truy xuất nguồn gốc "
                "(Thông tư 22/2011/TT-BYT)."
            ).format(missing_supplier_batch), title="SC-E014 SUPPLIER_BATCH_REQUIRED")

    def on_submit(self):
        self._create_batches_if_needed()
        # Audit: đảm bảo mọi item có has_batch_no=1 + expiry_date đều có batch_no
        # (sau khi _create_batches_if_needed chạy). Nếu thiếu → fail submit
        # để tránh stock entry không có batch reference.
        self.reload()
        missing_batch = []
        for r in self.items:
            if not r.expiry_date:
                continue
            if not r.batch_no:
                missing_batch.append(r.idx)
        if missing_batch:
            frappe.throw(_(
                "SC-E-PR-BATCH-MISSING: Các dòng {0} chưa được gán lô tự động. "
                "Đây là lỗi hệ thống, vui lòng liên hệ admin."
            ).format(missing_batch), title="SC-E-PR-BATCH-MISSING")
        self._post_stock_ledger()
        if self.qc_required and not self.is_return:
            self._auto_create_qi()
        self._update_po_received_qty()
        if self.is_return:
            if not self.return_status:
                self.db_set("return_status", "Pending Supplier Response")
            self._send_return_notification()
            # Auto-tạo Debit Note (skip nếu đã có)
            if not self.debit_note:
                try:
                    self.make_debit_note()
                except Exception as e:
                    frappe.log_error(message=str(e)[:1000], title="UC-11 auto make_debit_note")

    def on_cancel(self):
        self._reverse_stock_ledger()
        self._update_po_received_qty()

    def _compute_totals(self):
        total_qty = 0; total_value = 0
        for r in self.items:
            r.amount = flt(r.qty) * flt(r.rate)
            total_qty += flt(r.qty); total_value += flt(r.amount)
        self.total_qty = total_qty
        self.total_value = total_value

    def _compute_over_receipt(self):
        """UC-09 3a: flag per-row qty > po_qty, set parent has_over_receipt."""
        has_any = False
        for r in self.items:
            po_qty = flt(r.po_qty)
            qty = flt(r.qty)
            over = max(0.0, qty - po_qty) if po_qty > 0 else 0.0
            r.over_received_qty = over
            if over > 0:
                has_any = True
        self.has_over_receipt = 1 if has_any else 0
        if has_any and self.docstatus == 0:
            frappe.msgprint(
                _("⚠ Một số item nhận vượt SL PO — cần Manager xác nhận trước khi submit"),
                indicator="orange", alert=True,
            )

    # ------------------------------------------------------------------
    # UC-11 — Return handling
    # ------------------------------------------------------------------
    @frappe.whitelist()
    def make_debit_note(self):
        if self.docstatus != 1:
            frappe.throw(_("SC-E-RETURN-NOT-SUBMITTED: Return PR phải submitted"))
        if not self.is_return:
            frappe.throw(_("Chỉ Return PR (is_return=1) tạo được Debit Note"))
        if self.debit_note:
            frappe.throw(_("SC-E-RETURN-DN-EXISTS: Đã có Debit Note: {0}").format(self.debit_note))
        pi = frappe.new_doc("SC Purchase Invoice")
        pi.supplier = self.supplier
        pi.supplier_invoice_no = f"DN-{self.name}"
        pi.invoice_date = today()
        pi.due_date = today()
        pi.purchase_receipt = self.name
        pi.is_debit_note = 1
        pi.return_against_pr = self.name
        for r in self.items:
            pi.append("items", {
                "item": r.item, "qty": flt(r.qty), "uom": r.uom,
                "rate": flt(r.rate), "amount": flt(r.qty) * flt(r.rate),
            })
        pi.remarks = f"Debit Note for Return {self.name} — {self.return_reason or ''}"
        pi.flags.ignore_permissions = True
        pi.insert()
        self.db_set("debit_note", pi.name)
        return pi.name

    @frappe.whitelist()
    def make_credit_note(self):
        if self.docstatus != 1:
            frappe.throw(_("SC-E-RETURN-NOT-SUBMITTED: Return PR phải submitted"))
        if not self.is_return:
            frappe.throw(_("Chỉ Return PR (is_return=1) tạo được Credit Note"))
        if self.credit_note:
            frappe.throw(_("SC-E-RETURN-CN-EXISTS: Đã có Credit Note: {0}").format(self.credit_note))
        pi = frappe.new_doc("SC Purchase Invoice")
        pi.supplier = self.supplier
        pi.supplier_invoice_no = f"CN-{self.name}"
        pi.invoice_date = today()
        pi.due_date = today()
        pi.purchase_receipt = self.name
        pi.is_credit_note = 1
        pi.return_against_pr = self.name
        for r in self.items:
            pi.append("items", {
                "item": r.item, "qty": flt(r.qty), "uom": r.uom,
                "rate": flt(r.rate), "amount": flt(r.qty) * flt(r.rate),
            })
        pi.remarks = f"Credit Note (refund) for Return {self.name}"
        pi.flags.ignore_permissions = True
        pi.insert()
        self.db_set("credit_note", pi.name)
        self.db_set("return_status", "Refunded")
        return pi.name

    @frappe.whitelist()
    def link_replacement(self, replacement_pr_name: str):
        if self.docstatus != 1:
            frappe.throw(_("Return PR phải submitted"))
        if not self.is_return:
            frappe.throw(_("Chỉ Return PR mới link replacement"))
        rep = frappe.get_doc("SC Purchase Receipt", replacement_pr_name)
        if rep.is_return:
            frappe.throw(_(
                "SC-E-RETURN-REPLACE-INVALID: PR đổi hàng phải là PR thường (is_return=0)"
            ))
        self.db_set("replacement_pr", replacement_pr_name)
        self.db_set("return_status", "Replaced")
        return {"replacement_pr": replacement_pr_name, "return_status": "Replaced"}

    @frappe.whitelist()
    def send_return_notification(self):
        self._send_return_notification(force=1)
        return {"sent_to": frappe.db.get_value("SC Supplier", self.supplier, "email_id")}

    def _send_return_notification(self, force: int = 0):
        if not self.is_return:
            return
        if self.notification_sent_at and not force:
            return
        email = frappe.db.get_value("SC Supplier", self.supplier, "email_id")
        if not email:
            return
        items_html = "".join(
            f"<tr><td>{r.item}</td><td>{r.qty}</td><td>{r.uom}</td></tr>"
            for r in self.items
        )
        sup_name = frappe.db.get_value("SC Supplier", self.supplier, "supplier_name") or self.supplier
        msg = (f"<p>Kính gửi {sup_name},</p>"
               f"<p>Công ty Miyano Việt Nam trả hàng theo Phiếu trả <b>{self.name}</b>:</p>"
               f"<table border='1' cellpadding='6'>"
               f"<tr><th>Mã VT</th><th>SL</th><th>UOM</th></tr>{items_html}</table>"
               f"<p><b>Lý do:</b> {frappe.utils.escape_html(self.return_reason or '—')}</p>"
               f"<p>Tổng giá trị hoàn trả: {frappe.format(self.total_value, {'fieldtype':'Currency'})}</p>"
               f"<p>Vui lòng xác nhận đổi hàng / hoàn tiền trong 7 ngày làm việc.</p>")
        # Set timestamp trước để track intent — sendmail có thể fail trong env không SMTP
        self.db_set("notification_sent_at", frappe.utils.now())
        try:
            frappe.sendmail(
                recipients=[email],
                subject=f"[SupplyCore] Phiếu trả hàng {self.name}",
                message=msg, delayed=True,
            )
        except Exception as e:
            frappe.log_error(message=str(e)[:1000], title="UC-11 _send_return_notification")

    # ------------------------------------------------------------------
    @frappe.whitelist()
    def make_quality_inspection(self):
        """UC-12 luồng 3: tạo QI Draft cho items chưa có QI (manual trigger).

        Auto được gọi qua _auto_create_qi trong on_submit, nhưng button này
        để user gọi lại nếu cần (vd: thêm item sau khi PR submit, hoặc auto failed).
        Idempotent: skip items đã có QI.
        """
        if self.docstatus != 1:
            frappe.throw(_("PR phải submitted để tạo QI"))
        self._auto_create_qi()
        # Trả danh sách QI vừa tạo
        qis = frappe.get_all("SC Quality Inspection",
            filters={"purchase_receipt": self.name},
            fields=["name", "item", "batch", "overall_status", "docstatus"])
        return {"quality_inspections": qis, "count": len(qis)}

    @frappe.whitelist()
    def list_batches(self):
        """Trả danh sách lô đã tạo từ PR này."""
        batches = []
        for r in self.items:
            if r.batch_no:
                b = frappe.db.get_value("SC Batch", r.batch_no,
                    ["name", "item", "supplier_batch_no", "expiry_date", "qc_status", "blocked"],
                    as_dict=True)
                if b:
                    batches.append(b)
        return {"batches": batches, "count": len(batches)}

    @frappe.whitelist()
    def create_backorder(self):
        """UC-09 bước 8: tạo Draft PR mới cho phần còn thiếu."""
        if self.docstatus != 1:
            frappe.throw(_("PR phải submitted để tạo backorder"))
        if self.is_return:
            frappe.throw(_("Phiếu trả không tạo backorder"))
        if not self.purchase_order:
            frappe.throw(_("PR không có PO — không thể tạo backorder"))

        short_rows = []
        for r in self.items:
            po_qty = flt(r.po_qty)
            recv_qty = flt(r.qty)
            if po_qty > 0 and recv_qty < po_qty:
                short_rows.append({
                    "item": r.item, "uom": r.uom, "rate": flt(r.rate),
                    "warehouse": r.warehouse or self.to_warehouse,
                    "remaining_qty": po_qty - recv_qty,
                    "po_qty": po_qty - recv_qty,  # backorder's po_qty = remaining
                })
        if not short_rows:
            frappe.throw(_("SC-E-BACKORDER-NOTHING: Không có item nào nhận thiếu trên PR này"))

        bo = frappe.new_doc("SC Purchase Receipt")
        bo.supplier = self.supplier
        bo.purchase_order = self.purchase_order
        bo.backorder_for = self.name
        bo.posting_date = today()
        bo.to_warehouse = self.to_warehouse
        bo.qc_required = self.qc_required
        bo.remarks = f"Backorder cho PR {self.name}"
        for r in short_rows:
            bo.append("items", {
                "item": r["item"],
                "qty": r["remaining_qty"],
                "uom": r["uom"],
                "rate": r["rate"],
                "warehouse": r["warehouse"],
                "po_qty": r["po_qty"],
            })
        bo.flags.ignore_permissions = True
        bo.insert()
        return bo.name

    def _validate_expiry(self):
        from frappe.utils import date_diff
        try:
            min_shelf = int(frappe.db.get_single_value("SupplyCore Settings", "fefo_min_shelf_life_days") or 30)
        except Exception:
            min_shelf = 30
        for r in self.items:
            if r.expiry_date:
                days = date_diff(r.expiry_date, today())
                if days < 0:
                    frappe.throw(_("Row {0}: hạn dùng đã qua ({1})").format(r.idx, r.expiry_date),
                                 title="SC-E003 EXPIRY_TOO_CLOSE")
                if days < min_shelf:
                    frappe.msgprint(_("Row {0}: hạn dùng còn {1} ngày (< {2}). Cần xác nhận.")
                                     .format(r.idx, days, min_shelf), indicator="orange", alert=True)

    @frappe.whitelist()
    def create_batches(self):
        """Public wrapper: tạo SC Batch cho các row có expiry mà chưa có lô.
        Trả về list batch đã tạo."""
        before = {r.batch_no for r in self.items if r.batch_no}
        self._create_batches_if_needed()
        self.reload()
        after = {r.batch_no for r in self.items if r.batch_no}
        created = sorted(after - before)
        return {"created": created, "count": len(created)}

    def _create_batches_if_needed(self):
        """Sinh SC Batch cho MỌI dòng vật tư có expiry_date + chưa có batch_no
        (đơn N item → N lô). batch_id format `[item]-[YYYYMM]-[Seq]` (UC-15 step 3).

        Dùng seq cache local để tránh race condition khi nhiều row cùng
        (item, year-month): COUNT-based seq trong cùng transaction có thể
        không thấy uncommitted insert → duplicate batch_id → INSERT fail
        → row sau bị skip không gán lô.
        """
        from frappe.utils import getdate
        # seq_cache: key=(item, YYYYMM), value=next seq để dùng
        seq_cache = {}
        skipped_no_expiry = []

        for r in self.items:
            # Sinh lô cho MỌI dòng vật tư — đơn N item → N lô tương ứng.
            if r.batch_no:
                continue  # đã có lô, skip
            if not r.expiry_date:
                # Item bắt buộc batch nhưng thiếu expiry → ghi nhận để báo cho user
                skipped_no_expiry.append(r.idx)
                continue

            ym = getdate(r.expiry_date).strftime("%Y%m")
            key = (r.item, ym)
            if key not in seq_cache:
                cnt = frappe.db.sql("""
                    SELECT COUNT(*) FROM `tabSC Batch`
                    WHERE batch_id LIKE %s
                """, f"{r.item}-{ym}-%")[0][0]
                seq_cache[key] = int(cnt or 0)
            seq_cache[key] += 1
            bid = f"{r.item}-{ym}-{seq_cache[key]:03d}"

            b = frappe.new_doc("SC Batch")
            b.batch_id = bid
            b.item = r.item
            b.expiry_date = r.expiry_date
            b.manufacturing_date = r.manufacturing_date
            b.supplier = self.supplier
            b.supplier_batch_no = r.supplier_batch_no
            # BUG-004: truy xuất nguồn gốc — manufacturer + country_of_origin
            b.manufacturer = r.get("manufacturer") or None
            b.country_of_origin = r.get("country_of_origin") or None
            b.flags.ignore_permissions = True
            b.flags.ignore_short_expiry = 1
            try:
                b.insert()
            except frappe.DuplicateEntryError:
                # Edge case: race với PR khác. Retry với seq cao hơn.
                seq_cache[key] += 1
                bid = f"{r.item}-{ym}-{seq_cache[key]:03d}"
                b.batch_id = bid
                b.insert()
            r.db_set("batch_no", b.name, update_modified=False)

        if skipped_no_expiry:
            frappe.msgprint(
                _("⚠ Các dòng {0} có vật tư yêu cầu lô nhưng thiếu Hạn dùng → "
                  "không tạo lô tự động. Vui lòng kiểm tra.").format(skipped_no_expiry),
                indicator="orange", alert=True, title="SC-W-PR-MISSING-EXPIRY",
            )

    def _post_stock_ledger(self):
        from supplycore.supplycore.doctype.sc_stock_ledger_entry.sc_stock_ledger_entry import SCStockLedgerEntry
        for r in self.items:
            qty_sign = -1 if self.is_return else 1
            SCStockLedgerEntry.post(
                item=r.item, warehouse=r.warehouse or self.to_warehouse,
                qty_change=qty_sign * flt(r.qty), valuation_rate=flt(r.rate),
                voucher_type="SC Purchase Receipt", voucher_no=self.name, voucher_detail_no=r.name,
                batch=r.batch_no, bin_location=r.target_bin,
                posting_date=self.posting_date,
            )

    def _reverse_stock_ledger(self):
        sles = frappe.get_all("SC Stock Ledger Entry",
            filters={"voucher_type": "SC Purchase Receipt", "voucher_no": self.name, "is_cancelled": 0},
            fields=["name", "item", "warehouse", "batch", "bin_location", "qty_change", "valuation_rate"])
        from supplycore.supplycore.doctype.sc_stock_ledger_entry.sc_stock_ledger_entry import SCStockLedgerEntry
        for s in sles:
            SCStockLedgerEntry.post(
                item=s.item, warehouse=s.warehouse, qty_change=-flt(s.qty_change),
                valuation_rate=flt(s.valuation_rate),
                voucher_type="SC Purchase Receipt", voucher_no=self.name,
                voucher_detail_no=s.name + "-CANCEL",
                batch=s.batch, bin_location=s.bin_location,
                remarks=f"Cancel SLE {s.name}",
            )
            # NB: KHÔNG set is_cancelled trên dòng gốc. get_qty/get_available_qty
            # tính SUM(qty_change) WHERE is_cancelled=0, nên dòng gốc (+qty) và
            # dòng đối ứng (-qty) tự triệt tiêu → tồn trả về đúng. Nếu vừa set
            # is_cancelled vừa post đối ứng sẽ đảo KÉP (bug — đã sửa, mirror
            # SC Delivery Note._reverse_stock_ledger).

    def _auto_create_qi(self):
        for r in self.items:
            existing = frappe.db.exists("SC Quality Inspection",
                                         {"purchase_receipt": self.name, "item": r.item, "pr_item_ref": r.name})
            if existing:
                continue
            qi = frappe.new_doc("SC Quality Inspection")
            qi.inspection_date = today()
            qi.purchase_receipt = self.name
            qi.pr_item_ref = r.name
            qi.item = r.item
            qi.supplier = self.supplier
            qi.batch = r.batch_no
            qi.received_qty = r.qty
            qi.inspected_by = frappe.session.user if frappe.session.user not in (None, "Guest") else "Administrator"
            # Bỏ QC Checklist Template: seed sẵn 5 tiêu chí QC nhập kho mẫu để KCS tick (thêm/bớt được).
            # Giữ ĐỒNG BỘ với frontend schemas.js → 'SC Quality Inspection'.items.defaultRows
            for spec in _DEFAULT_QI_CRITERIA:
                qi.append("readings", {"specification": spec, "status": ""})
            qi.flags.ignore_permissions = True
            try:
                qi.insert()
            except Exception as e:
                frappe.log_error(message=f"PR={self.name} item={r.item} QI auto failed: {e}",
                                  title="SC PR auto QI")

    def _update_po_received_qty(self):
        if not self.purchase_order:
            return
        po = frappe.get_doc("SC Purchase Order", self.purchase_order)
        # received_qty per PO Item = SUM(qty) across all submitted PR linked
        for poi in po.items:
            received = frappe.db.sql("""
                SELECT COALESCE(SUM(pri.qty), 0)
                FROM `tabSC Purchase Receipt Item` pri
                JOIN `tabSC Purchase Receipt` pr ON pr.name = pri.parent
                WHERE pr.purchase_order = %s AND pri.item = %s
                  AND pr.docstatus = 1 AND pr.is_return = 0
            """, (self.purchase_order, poi.item))[0][0]
            frappe.db.set_value("SC Purchase Order Item", poi.name,
                                  "received_qty", flt(received), update_modified=False)
            # Cập nhật in-memory để compute status đúng
            poi.received_qty = flt(received)
        # Auto status — dùng giá trị received_qty vừa update
        all_received = all(flt(p.received_qty) >= flt(p.qty) for p in po.items)
        partial = any(flt(p.received_qty) > 0 for p in po.items)
        new_status = "Received" if all_received else ("Partially Received" if partial else po.status)
        if po.status != new_status and po.docstatus == 1:
            frappe.db.set_value("SC Purchase Order", po.name, "status", new_status)


def _find_checklist_template(item_code):
    item_group = frappe.db.get_value("SC Item", item_code, "item_group")
    if item_group:
        tpl = frappe.db.get_value("QC Checklist Template",
                                    {"item_group": item_group, "is_default_for_group": 1, "enabled": 1}, "name")
        if tpl: return tpl
    # Fallback: global template (item_group IS NULL or empty)
    rows = frappe.db.sql("""
        SELECT name FROM `tabQC Checklist Template`
        WHERE enabled = 1
          AND (item_group IS NULL OR item_group = '')
        ORDER BY creation DESC LIMIT 1
    """)
    return rows[0][0] if rows else None
