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
        self._check_expiry_and_stock()

    def on_submit(self):
        self._post_stock_ledger()
        self.db_set("status", "Đã giao")
        if self.sales_order:
            frappe.db.set_value("SC Sales Order", self.sales_order, "status", "Đã bàn giao")

    def on_cancel(self):
        self._reverse_stock_ledger()
        if self.sales_order:
            frappe.db.set_value("SC Sales Order", self.sales_order, "status", "Đã duyệt")

    # ------------------------------------------------------------------
    # BRU-SO-002
    # ------------------------------------------------------------------
    def _check_so_status(self):
        if not self.sales_order:
            return
        so_status = frappe.db.get_value("SC Sales Order", self.sales_order, "status")
        if so_status != "Đã duyệt":
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
