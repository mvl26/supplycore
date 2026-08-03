"""SC Delivery Note -- giao hàng bán MVL, xuất kho FEFO (M7 Sales, GĐ2 Task 5).

Business rules:
- BRU-SO-002: sales_order phải ở trạng thái "Đã duyệt" hoặc "Đang xử lý" mới tạo
  được DN, nếu không → throw.
- FEFO: dòng chưa gán batch → tự động chọn lô theo auto_pick_fefo (gần hết hạn
  trước). Nếu cần chia nhiều lô để đủ SL → tự tách thành nhiều dòng DN Item.
- BRU-EXP-001: trước khi submit, mọi lô đã gán không được hết hạn.
- BRU-INV-001: trước khi submit (và khi auto-pick), tồn khả dụng phải >= SL cần
  xuất — nếu không đủ → throw, không cho phép xuất âm kho ngoài kiểm soát.

Submit: ghi SC Stock Ledger Entry (-qty) cho từng dòng; set status "Đã giao";
cập nhật sales_order.status = "Đã bàn giao".
Cancel: chèn SLE đối ứng (+qty), append-only — KHÔNG đánh dấu is_cancelled
trên dòng gốc (xem _reverse_stock_ledger; mirror sang SC Purchase Receipt /
SC Stock Entry / SC Stock Reconciliation); trả sales_order.status về "Đã duyệt".
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate, today


class SCDeliveryNote(Document):

    def validate(self):
        self._check_so_status()
        self._resolve_batches()

    def before_submit(self):
        self._check_scan_confirmed()
        self._check_expiry_and_stock()

    def on_submit(self):
        self._post_stock_ledger()
        self.db_set("status", "Đã giao")
        if self.sales_order:
            frappe.db.set_value("SC Sales Order", self.sales_order, "status", "Đã bàn giao")

    def before_cancel(self):
        # Hủy phiếu giao (soạn hàng) phải nêu lý do — set cancellation_reason
        # TRƯỚC khi cancel (frontend gán vào doc rồi mới gọi cancel).
        if self.picking_required and not (self.cancellation_reason or "").strip():
            frappe.throw(_(
                "SC-E-DN-CANCEL-REASON: Phải nhập lý do hủy phiếu giao hàng."
            ), title="Thiếu lý do hủy")

    def on_cancel(self):
        self._reverse_stock_ledger()   # hoàn tồn kho về như cũ (append-only +qty)
        if self.sales_order:
            frappe.db.set_value("SC Sales Order", self.sales_order, "status", "Đã duyệt")

    def on_trash(self):
        # Xóa phiếu giao NHÁP đang soạn → trả SO về "Đã duyệt" để hiện lại nút
        # "Tạo phiếu giao" (tránh SO kẹt ở "Đang xử lý" khi bỏ phiếu nháp).
        if self.docstatus == 0 and self.picking_required and self.sales_order:
            if frappe.db.get_value("SC Sales Order", self.sales_order, "status") == "Đang xử lý":
                frappe.db.set_value("SC Sales Order", self.sales_order, "status", "Đã duyệt")

    # ------------------------------------------------------------------
    # Luồng soạn hàng: chỉ cho submit khi MỌI dòng đã quét xác nhận đúng lô/SL.
    # ------------------------------------------------------------------
    def _check_scan_confirmed(self):
        if not self.picking_required:
            return   # phiếu tạo tự động (không qua soạn hàng) — giữ hành vi cũ
        chua = [r for r in self.items if not r.scan_confirmed]
        if chua:
            ten = ", ".join(sorted({(r.item or "?") for r in chua}))
            frappe.throw(_(
                "SC-E-DN-NOT-SCANNED: Còn {0} dòng chưa quét xác nhận ({1}). "
                "Phải quét đủ lô & số lượng mới được submit."
            ).format(len(chua), ten), title="Chưa quét xác nhận")

    # ------------------------------------------------------------------
    # BRU-SO-002
    # ------------------------------------------------------------------
    def _check_so_status(self):
        if not self.sales_order:
            return
        so_status = frappe.db.get_value("SC Sales Order", self.sales_order, "status")
        # "Đang xử lý" = đã có phiếu giao nháp đang soạn hàng cho SO này (đặt ở
        # delivery_create khi submit=0). Vẫn cho lưu/soạn phiếu nháp đó tiếp.
        if so_status not in ("Đã duyệt", "Đang xử lý"):
            frappe.throw(_(
                "BRU-SO-002: Đơn hàng bán {0} chưa được duyệt (trạng thái hiện tại: "
                "{1}) — không thể tạo Phiếu giao hàng."
            ).format(self.sales_order, so_status), title="BRU-SO-002")

    # ------------------------------------------------------------------
    # FEFO auto-pick + BRU-INV-001 (tại thời điểm chọn lô)
    # ------------------------------------------------------------------
    def _resolve_batches(self):
        from supplycore.api.fefo import get_suggested_batches

        # Cấp phát FEFO có "reserved": theo dõi SL đã giữ theo (item, warehouse,
        # batch) trên TOÀN phiếu. Bản cũ gọi auto_pick_fefo cho TỪNG dòng, mỗi
        # dòng đọc CÙNG số dư DB (chưa post SLE nào) nên 2 dòng cùng item/lô đều
        # thấy đủ tồn rồi cùng chọn 1 lô → tồn âm khi on_submit post tuần tự
        # (BRU-INV-001). Trừ phần đã reserved đảm bảo FEFO trải đúng qua nhiều lô
        # và không cấp vượt tồn thật.
        reserved = {}
        # (1) Ghi nhận trước các dòng đã gán lô thủ công.
        for row in self.items:
            row.warehouse = row.warehouse or self.from_warehouse
            if row.batch:
                key = (row.item, row.warehouse, row.batch)
                reserved[key] = flt(reserved.get(key, 0)) + flt(row.qty)

        # (2) Auto-pick FEFO cho các dòng chưa có lô, trừ phần đã reserved.
        for row in list(self.items):
            if row.batch:
                continue
            need = flt(row.qty)
            # qty=0 → get_suggested_batches trả TẤT CẢ lô khả dụng (đã loại hết
            # hạn/blocked/QC fail) theo thứ tự FEFO; ta tự cấp phát trừ reserved.
            batches = get_suggested_batches(row.item, row.warehouse, 0)["batches"]
            picks = []
            for b in batches:
                key = (row.item, row.warehouse, b["batch_no"])
                avail = flt(b["available_qty"]) - flt(reserved.get(key, 0))
                if avail <= 0:
                    continue
                take = min(need, avail)
                if take <= 0:
                    continue
                picks.append((b["batch_no"], take))
                reserved[key] = flt(reserved.get(key, 0)) + take
                need -= take
                if need <= 0:
                    break
            if need > 0:
                frappe.throw(_(
                    "BRU-INV-001: Không đủ tồn kho khả dụng cho vật tư {0} tại kho "
                    "{1} — cần {2}, thiếu {3}."
                ).format(row.item, row.warehouse, row.qty, need), title="BRU-INV-001")
            # Lô đầu gán vào dòng hiện tại; các lô còn lại tách thành dòng mới.
            row.batch = picks[0][0]
            row.qty = picks[0][1]
            for extra_batch, extra_qty in picks[1:]:
                self.append("items", {
                    "item": row.item, "uom": row.uom, "warehouse": row.warehouse,
                    "batch": extra_batch, "qty": extra_qty,
                })

    # ------------------------------------------------------------------
    # BRU-EXP-001 / BRU-INV-001 (tại thời điểm submit)
    # ------------------------------------------------------------------
    def _check_expiry_and_stock(self):
        from supplycore.supplycore.doctype.sc_stock_ledger_entry.sc_stock_ledger_entry import (
            SCStockLedgerEntry,
        )

        today_d = getdate(today())
        # Gộp SL cần xuất theo (item, warehouse, batch) trên TOÀN phiếu rồi so
        # MỘT LẦN với tồn khả dụng. Kiểm per-row của bản cũ để lọt tồn âm khi
        # NHIỀU dòng cùng dùng chung 1 lô (mỗi dòng thấy đủ tồn độc lập nhưng
        # tổng vượt tồn thật) → BRU-INV-001. Đây là chốt chặn cuối cùng, đúng
        # bất kể _resolve_batches cấp phát thế nào.
        need_by_key = {}
        for row in self.items:
            wh = row.warehouse or self.from_warehouse
            if row.batch:
                expiry = frappe.db.get_value("SC Batch", row.batch, "expiry_date")
                if expiry and getdate(expiry) < today_d:
                    frappe.throw(_(
                        "BRU-EXP-001: Lô {0} (vật tư {1}) đã hết hạn ({2}) — không thể "
                        "xuất kho."
                    ).format(row.batch, row.item, expiry), title="BRU-EXP-001")
            key = (row.item, wh, row.batch)
            need_by_key[key] = flt(need_by_key.get(key, 0)) + flt(row.qty)

        for (item, wh, batch), need in need_by_key.items():
            avail = SCStockLedgerEntry.get_available_qty(item, wh, batch)
            if flt(need) > flt(avail):
                frappe.throw(_(
                    "BRU-INV-001: Không đủ tồn kho khả dụng cho vật tư {0}{1} tại kho "
                    "{2}: cần {3}, còn {4}."
                ).format(item, f" lô {batch}" if batch else "", wh,
                          need, avail), title="BRU-INV-001")

    # ------------------------------------------------------------------
    # SLE posting / reversal
    # ------------------------------------------------------------------
    def _post_stock_ledger(self):
        from supplycore.supplycore.doctype.sc_stock_ledger_entry.sc_stock_ledger_entry import (
            SCStockLedgerEntry,
        )

        for row in self.items:
            wh = row.warehouse or self.from_warehouse
            SCStockLedgerEntry.post(
                item=row.item, warehouse=wh, qty_change=-flt(row.qty),
                valuation_rate=_get_valuation(row.item, wh, row.batch),
                voucher_type="SC Delivery Note", voucher_no=self.name,
                voucher_detail_no=row.name, batch=row.batch,
                posting_date=self.delivery_date,
            )

    def _reverse_stock_ledger(self):
        from supplycore.supplycore.doctype.sc_stock_ledger_entry.sc_stock_ledger_entry import (
            SCStockLedgerEntry,
        )

        sles = frappe.get_all(
            "SC Stock Ledger Entry",
            filters={"voucher_type": "SC Delivery Note", "voucher_no": self.name, "is_cancelled": 0},
            fields=["name", "item", "warehouse", "batch", "bin_location",
                     "qty_change", "valuation_rate"],
        )
        for s in sles:
            SCStockLedgerEntry.post(
                item=s.item, warehouse=s.warehouse, qty_change=-flt(s.qty_change),
                valuation_rate=flt(s.valuation_rate),
                voucher_type="SC Delivery Note", voucher_no=self.name,
                voucher_detail_no=s.name + "-CANCEL",
                batch=s.batch, bin_location=s.bin_location,
                remarks=f"Cancel SLE {s.name}",
            )
            # NB: KHÔNG set is_cancelled trên dòng gốc. get_available_qty tính
            # SUM(qty_change) WHERE is_cancelled=0, nên dòng gốc (-qty) và dòng
            # đối ứng (+qty) tự triệt tiêu → tồn trả về đúng. Nếu vừa set
            # is_cancelled vừa post đối ứng sẽ đảo KÉP (bug — pattern này đã
            # được mirror sang SC Purchase Receipt / SC Stock Entry /
            # SC Stock Reconciliation._reverse_stock_ledger).


def _get_valuation(item, warehouse, batch=None):
    """Đơn giá xuất kho -- lấy từ SLE nhập gần nhất của item+warehouse(+batch).

    Mirror _source_valuation (SC Stock Entry) rút gọn theo brief GĐ2 Task 5:
    ưu tiên SLE cùng batch, fallback SLE cùng item/warehouse bất kỳ batch,
    cuối cùng 0 (giá vốn = 0 nếu hệ thống chưa có giá tham chiếu).
    """
    conds = ["item = %(i)s", "warehouse = %(w)s", "is_cancelled = 0", "valuation_rate > 0"]
    params = {"i": item, "w": warehouse}
    if batch:
        conds.append("batch = %(b)s")
        params["b"] = batch
    rows = frappe.db.sql(f"""
        SELECT valuation_rate FROM `tabSC Stock Ledger Entry`
        WHERE {' AND '.join(conds)}
        ORDER BY posting_date DESC, creation DESC LIMIT 1
    """, params)
    if rows and flt(rows[0][0]) > 0:
        return flt(rows[0][0])
    if batch:
        return _get_valuation(item, warehouse, batch=None)
    return 0.0


@frappe.whitelist()
def confirm_pick_line(delivery_note, row, scanned_batch, scanned_bin=None, qty=None):
    """Quét xác nhận 1 dòng soạn hàng của Phiếu giao hàng (nháp).

    - scanned_batch: mã/barcode lô nhân viên quét trên hàng thực tế. CHO PHÉP
      chọn LÔ KHÁC với lô gợi ý — server validate hợp lệ rồi cập nhật dòng.
    - scanned_bin: (tùy chọn) mã/barcode vị trí (bin) đã quét — phải thuộc kho xuất.
    - qty: SL thực lấy (mặc định = SL dòng).

    Validate server-side (KHÔNG tin client): lô đúng vật tư, chưa hết hạn, chưa
    khóa/QC đạt, tồn khả dụng đủ (get_available_qty đã loại Pending/Rejected/
    blocked), bin thuộc kho. Đạt → set batch/bin_location/qty + scan_confirmed=1.
    Trả tiến độ còn lại (để UI biết khi nào cho submit).
    """
    from supplycore.supplycore.doctype.sc_stock_ledger_entry.sc_stock_ledger_entry import (
        SCStockLedgerEntry,
    )

    doc = frappe.get_doc("SC Delivery Note", delivery_note)
    if not frappe.has_permission("SC Delivery Note", "write", doc=doc):
        frappe.throw(_("Không có quyền soạn phiếu giao hàng"), frappe.PermissionError)
    if doc.docstatus != 0:
        frappe.throw(_("Phiếu đã submit/hủy — không soạn được nữa"))

    line = next((r for r in doc.items if r.name == row), None)
    if not line:
        frappe.throw(_("Không tìm thấy dòng {0} trên phiếu").format(row))

    # 1) Nhận dạng lô đã quét (theo barcode hoặc mã lô)
    bcode = (scanned_batch or "").strip()
    batch_name = frappe.db.get_value("SC Batch", {"barcode": bcode}, "name") \
        or frappe.db.get_value("SC Batch", bcode, "name")
    if not batch_name:
        frappe.throw(_("SC-E-PICK-BATCH: Không nhận dạng được lô đã quét: {0}").format(bcode))
    bt = frappe.db.get_value("SC Batch", batch_name,
                             ["item", "expiry_date", "blocked", "qc_status"], as_dict=True)
    if bt.item != line.item:
        frappe.throw(_(
            "SC-E-PICK-ITEM: Lô {0} thuộc vật tư {1}, không khớp dòng ({2})."
        ).format(batch_name, bt.item, line.item))
    if bt.blocked:
        frappe.throw(_("SC-E-PICK-BLOCKED: Lô {0} đang bị khóa.").format(batch_name))
    if bt.qc_status in ("Pending", "Rejected"):
        frappe.throw(_("SC-E-PICK-QC: Lô {0} chưa đạt QC ({1}).").format(batch_name, bt.qc_status))
    if bt.expiry_date and getdate(bt.expiry_date) < getdate(today()):
        frappe.throw(_("SC-E-PICK-EXPIRED: Lô {0} đã hết hạn ({1}).").format(batch_name, bt.expiry_date))

    # 2) SL cần lấy
    need = flt(qty) if flt(qty) > 0 else flt(line.qty)
    if need <= 0:
        frappe.throw(_("SC-E-PICK-QTY: Số lượng phải lớn hơn 0."))

    # 3) Tồn khả dụng của lô tại kho xuất (authoritative)
    wh = line.warehouse or doc.from_warehouse
    avail = flt(SCStockLedgerEntry.get_available_qty(line.item, wh, batch_name))
    if need > avail + 0.001:
        frappe.throw(_(
            "SC-E-PICK-STOCK: Lô {0} tại kho {1} chỉ còn {2}, không đủ để lấy {3}."
        ).format(batch_name, wh, avail, need))

    # 4) Vị trí (bin) — tùy chọn, phải thuộc kho xuất
    bin_name = None
    if scanned_bin and str(scanned_bin).strip():
        bc = str(scanned_bin).strip()
        bin_name = frappe.db.get_value("Bin Location", {"barcode": bc}, "name") \
            or frappe.db.get_value("Bin Location", bc, "name")
        if not bin_name:
            frappe.throw(_("SC-E-PICK-BIN: Không nhận dạng được vị trí đã quét: {0}").format(bc))
        bin_wh = frappe.db.get_value("Bin Location", bin_name, "warehouse")
        if bin_wh and wh and bin_wh != wh:
            frappe.throw(_(
                "SC-E-PICK-BIN-WH: Vị trí {0} thuộc kho {1}, không phải kho xuất {2}."
            ).format(bin_name, bin_wh, wh))

    # 5) Ghi nhận dòng đã soạn
    line.batch = batch_name
    line.qty = need
    line.warehouse = wh
    if bin_name:
        line.bin_location = bin_name
    line.scan_confirmed = 1
    doc.save(ignore_permissions=True)

    remaining = len([r for r in doc.items if not r.scan_confirmed])
    return {
        "ok": True,
        "row": line.name,
        "batch": batch_name,
        "qty": need,
        "bin_location": bin_name,
        "remaining_unconfirmed": remaining,
        "all_confirmed": remaining == 0,
    }


@frappe.whitelist()
def cancel_delivery(delivery_note, reason):
    """Hủy Phiếu giao hàng đã submit + ghi lý do + hoàn tồn kho.

    reason bắt buộc. Dùng db_set để ghi cancellation_reason lên phiếu đã submit
    (field thường không cho sửa sau submit → UpdateAfterSubmitError); sau đó
    doc.cancel() chạy on_cancel → _reverse_stock_ledger hoàn tồn về như cũ.
    """
    reason = (reason or "").strip()
    if not reason:
        frappe.throw(_("SC-E-DN-CANCEL-REASON: Phải nhập lý do hủy."), title="Thiếu lý do hủy")
    doc = frappe.get_doc("SC Delivery Note", delivery_note)
    if not frappe.has_permission("SC Delivery Note", "cancel", doc=doc):
        frappe.throw(_("Không có quyền hủy phiếu giao hàng"), frappe.PermissionError)
    if doc.docstatus != 1:
        frappe.throw(_("Chỉ hủy được phiếu đã submit"))
    doc.db_set("cancellation_reason", reason)   # ghi trước, tránh UpdateAfterSubmit
    doc.cancel()
    return {"ok": True, "name": doc.name, "status": doc.status}
