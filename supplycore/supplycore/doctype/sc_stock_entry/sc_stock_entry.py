"""SC Stock Entry — chứng từ di chuyển kho.

Submit → ghi SC Stock Ledger Entry (1 entry per item-warehouse-batch-bin).
Material Receipt: tạo +qty ở to_warehouse.
Material Issue: tạo -qty ở from_warehouse.
Material Transfer: tạo cả -qty (from) và +qty (to).
Cancel → tạo SLE đối ứng + đánh dấu is_cancelled.
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate, today


def _source_valuation(item, warehouse, batch=None):
    """Đơn giá tồn kho nguồn của 1 item/lô — Moving Average từ SLE.

    BUG-003: Chuyển/Xuất kho phải kế thừa đơn giá đúng. Thứ tự fallback:
      1. SLE gần nhất của item+warehouse(+batch) với valuation > 0
      2. SLE gần nhất của item bất kỳ warehouse khác (cùng item, val > 0)
      3. SC Item.standard_rate (giá chuẩn)
      4. 0 (cuối cùng — caller phải kiểm tra)
    """
    if not item or not warehouse:
        return 0.0
    # Bước 1: SLE cùng item+warehouse(+batch)
    conds = ["item = %(i)s", "warehouse = %(w)s", "is_cancelled = 0", "valuation_rate > 0"]
    params = {"i": item, "w": warehouse}
    if batch:
        conds.append("batch = %(b)s")
        params["b"] = batch
    v = frappe.db.sql(f"""
        SELECT valuation_rate FROM `tabSC Stock Ledger Entry`
        WHERE {' AND '.join(conds)}
        ORDER BY posting_date DESC, creation DESC LIMIT 1
    """, params)
    if v and flt(v[0][0]) > 0:
        return flt(v[0][0])

    # Bước 2: SLE cùng item ở warehouse khác — Moving Average toàn hệ thống
    v2 = frappe.db.sql("""
        SELECT valuation_rate FROM `tabSC Stock Ledger Entry`
        WHERE item = %s AND is_cancelled = 0 AND valuation_rate > 0
        ORDER BY posting_date DESC, creation DESC LIMIT 1
    """, item)
    if v2 and flt(v2[0][0]) > 0:
        return flt(v2[0][0])

    # Bước 3: PR rate gần nhất (đơn giá mua thực tế)
    pr = frappe.db.sql("""
        SELECT pri.rate FROM `tabSC Purchase Receipt Item` pri
        JOIN `tabSC Purchase Receipt` pr ON pr.name = pri.parent
        WHERE pri.item = %s AND pr.docstatus = 1 AND pri.rate > 0
        ORDER BY pr.posting_date DESC LIMIT 1
    """, item)
    if pr and flt(pr[0][0]) > 0:
        return flt(pr[0][0])

    # Bước 4: PO rate gần nhất
    po = frappe.db.sql("""
        SELECT poi.rate FROM `tabSC Purchase Order Item` poi
        JOIN `tabSC Purchase Order` po ON po.name = poi.parent
        WHERE poi.item = %s AND po.docstatus = 1 AND poi.rate > 0
        ORDER BY po.transaction_date DESC LIMIT 1
    """, item)
    if po and flt(po[0][0]) > 0:
        return flt(po[0][0])

    return 0.0


ISSUE_TYPES = ("Material Issue", "Material Transfer")


class SCStockEntry(Document):

    def validate(self):
        self._validate_warehouses()
        self._validate_items_and_compute()
        self._validate_bin_consistency()
        self._enforce_fefo_rules()
        self._enforce_no_negative_stock()

    def on_submit(self):
        self._post_stock_ledger()
        self._notify_linked_transfer_request("submit")
        self._log_fefo_override_audit()

    def on_cancel(self):
        self._reverse_stock_ledger()
        self._notify_linked_transfer_request("cancel")

    def _notify_linked_transfer_request(self, event: str):
        """Update linked SC Transfer Request status (M6 luân chuyển nội bộ)."""
        if not self.get("transfer_request"):
            return
        try:
            from supplycore.m6_transfer.doctype.sc_transfer_request.sc_transfer_request import (
                update_tr_on_se_submit, update_tr_on_se_cancel,
            )
            if event == "submit":
                update_tr_on_se_submit(self)
            elif event == "cancel":
                update_tr_on_se_cancel(self)
        except Exception as e:
            frappe.log_error(message=f"M6 TR sync failed SE={self.name}: {e}",
                              title="M6 TR sync")

    # ------------------------------------------------------------------
    def _validate_warehouses(self):
        if self.entry_type in ("Material Issue", "Material Transfer") and not self.from_warehouse:
            frappe.throw(_("Cần from_warehouse cho {0}").format(self.entry_type))
        if self.entry_type in ("Material Receipt", "Material Transfer") and not self.to_warehouse:
            frappe.throw(_("Cần to_warehouse cho {0}").format(self.entry_type))
        if self.from_warehouse == self.to_warehouse and self.entry_type == "Material Transfer":
            frappe.throw(_("Material Transfer phải có from_warehouse khác to_warehouse"))

    def _validate_items_and_compute(self):
        total_qty = 0
        total_value = 0
        for row in self.items:
            # Đơn giá theo tồn kho nguồn của lô — Chuyển/Xuất kho không nhập tay
            if (flt(row.valuation_rate) <= 0
                    and self.entry_type in ("Material Transfer", "Material Issue")):
                row.valuation_rate = _source_valuation(row.item, self.from_warehouse, row.batch)
            row.amount = flt(row.qty) * flt(row.valuation_rate)
            total_qty += flt(row.qty)
            total_value += flt(row.amount)
            # Batch phải thuộc đúng item
            if row.batch:
                batch_item = frappe.db.get_value("SC Batch", row.batch, "item")
                if batch_item and batch_item != row.item:
                    frappe.throw(_("Row {0}: batch {1} không thuộc item {2}")
                                 .format(row.idx, row.batch, row.item))
            # has_batch_no = 1 → bắt buộc nhập batch khi NHẬP MỚI hàng.
            # Chuyển/Xuất kho di chuyển tồn sẵn có → tồn cũ chưa gắn lô vẫn cho đi.
            has_batch = frappe.db.get_value("SC Item", row.item, "has_batch_no")
            if (has_batch and not row.batch
                    and self.entry_type not in ("Material Transfer", "Material Issue")):
                frappe.throw(_("Row {0}: item {1} bắt buộc có batch").format(row.idx, row.item))
        self.total_qty = total_qty
        self.total_value = total_value

    def _validate_bin_consistency(self):
        for row in self.items:
            for fld, wh_fld in (("source_bin", "from_warehouse"), ("target_bin", "to_warehouse")):
                bin_name = row.get(fld)
                if not bin_name:
                    continue
                bin_data = frappe.db.get_value("Bin Location", bin_name,
                                                ["warehouse", "enabled", "is_quarantine"], as_dict=True)
                if not bin_data:
                    continue
                wh = self.get(wh_fld)
                if wh and bin_data.warehouse != wh:
                    frappe.throw(_("Row {0}: {1} {2} không thuộc kho {3}")
                                 .format(row.idx, fld, bin_name, wh))
                if not bin_data.enabled:
                    frappe.throw(_("Row {0}: bin {1} đã disable").format(row.idx, bin_name))
                if fld == "source_bin" and bin_data.is_quarantine:
                    frappe.msgprint(_("Row {0}: source_bin {1} là quarantine — chỉ xuất sau QC")
                                     .format(row.idx, bin_name), indicator="orange", alert=True)

    # ------------------------------------------------------------------
    # M5 FEFO enforcement
    # ------------------------------------------------------------------
    def _enforce_fefo_rules(self):
        if self.docstatus != 0:
            return
        if self.entry_type not in ISSUE_TYPES:
            return

        today_d = getdate(today())
        selected = {}
        for row in self.items:
            if row.batch and row.item and self.from_warehouse:
                key = (row.item, self.from_warehouse)
                selected.setdefault(key, set()).add(row.batch)

        for row in self.items:
            if not (row.batch and row.item and self.from_warehouse):
                continue
            batch = frappe.db.get_value("SC Batch", row.batch,
                                         ["expiry_date", "blocked", "block_reason"], as_dict=True)
            if not batch:
                continue
            if batch.expiry_date and getdate(batch.expiry_date) < today_d:
                frappe.throw(_("Batch {0} đã hết hạn ({1})").format(row.batch, batch.expiry_date),
                             title="SC-E003 EXPIRY_TOO_CLOSE")
            if batch.blocked and not self.recall_notice:
                frappe.throw(_("Batch {0} bị block: {1}").format(row.batch, batch.block_reason or ""),
                             title="SC-E008 BATCH_RECALLED")
            if not batch.expiry_date:
                continue

            used = selected.get((row.item, self.from_warehouse), set())
            earlier = frappe.db.sql("""
                SELECT b.name AS batch, b.expiry_date,
                       COALESCE(SUM(sle.qty_change), 0) AS qty
                FROM `tabSC Batch` b
                LEFT JOIN `tabSC Stock Ledger Entry` sle
                    ON sle.batch = b.name AND sle.warehouse = %(wh)s AND sle.is_cancelled = 0
                WHERE b.item = %(item)s
                  AND b.disabled = 0
                  AND COALESCE(b.blocked, 0) = 0
                  AND b.name != %(curr)s
                  AND b.expiry_date IS NOT NULL
                  AND b.expiry_date < %(curr_exp)s
                  AND b.expiry_date >= CURDATE()
                GROUP BY b.name, b.expiry_date
                HAVING qty > 0
                ORDER BY b.expiry_date ASC LIMIT 5
            """, {"wh": self.from_warehouse, "item": row.item,
                  "curr": row.batch, "curr_exp": batch.expiry_date}, as_dict=True)

            unused_earlier = [b for b in earlier if b.batch not in used]
            if not unused_earlier:
                continue

            if not row.fefo_override:
                strict = _is_fefo_strict()
                msg = _("Row {0} item {1} batch {2}: còn lô gần hết hạn hơn — {3}").format(
                    row.idx, row.item, row.batch,
                    ", ".join(f"{b.batch}({b.expiry_date})" for b in unused_earlier[:3])
                )
                if strict:
                    frappe.throw(msg + "\n" + _("Tick FEFO Override + ghi lý do"),
                                 title="SC-E001 FEFO_OVERRIDE")
                else:
                    frappe.msgprint(msg, indicator="orange", alert=True)
            elif not row.fefo_override_reason:
                frappe.throw(_("FEFO Override row {0} cần ghi lý do").format(row.idx),
                             title="SC-E001 FEFO_OVERRIDE")

        # UC-16 4a: Manager role bắt buộc khi có override
        has_override = any(r.fefo_override and r.batch for r in self.items)
        if has_override:
            user_roles = set(frappe.get_roles(frappe.session.user))
            allowed = {"SupplyCore Manager", "System Manager"}
            if not (user_roles & allowed):
                frappe.throw(_(
                    "SC-E-FEFO-MANAGER-REQUIRED: FEFO Override yêu cầu xác nhận Quản lý — "
                    "user phải có role SupplyCore Manager để submit"
                ))

    # ------------------------------------------------------------------
    # SLE posting
    # ------------------------------------------------------------------
    def _post_stock_ledger(self):
        from supplycore.supplycore.doctype.sc_stock_ledger_entry.sc_stock_ledger_entry import SCStockLedgerEntry
        for row in self.items:
            if self.entry_type == "Material Receipt":
                SCStockLedgerEntry.post(
                    item=row.item, warehouse=self.to_warehouse,
                    qty_change=flt(row.qty), valuation_rate=flt(row.valuation_rate),
                    voucher_type="SC Stock Entry", voucher_no=self.name, voucher_detail_no=row.name,
                    batch=row.batch, bin_location=row.target_bin,
                    posting_date=self.posting_date, posting_time=self.posting_time,
                )
            elif self.entry_type == "Material Issue":
                SCStockLedgerEntry.post(
                    item=row.item, warehouse=self.from_warehouse,
                    qty_change=-flt(row.qty), valuation_rate=flt(row.valuation_rate),
                    voucher_type="SC Stock Entry", voucher_no=self.name, voucher_detail_no=row.name,
                    batch=row.batch, bin_location=row.source_bin,
                    posting_date=self.posting_date, posting_time=self.posting_time,
                )
            elif self.entry_type == "Material Transfer":
                SCStockLedgerEntry.post(
                    item=row.item, warehouse=self.from_warehouse,
                    qty_change=-flt(row.qty), valuation_rate=flt(row.valuation_rate),
                    voucher_type="SC Stock Entry", voucher_no=self.name, voucher_detail_no=row.name,
                    batch=row.batch, bin_location=row.source_bin,
                    posting_date=self.posting_date, posting_time=self.posting_time,
                )
                SCStockLedgerEntry.post(
                    item=row.item, warehouse=self.to_warehouse,
                    qty_change=flt(row.qty), valuation_rate=flt(row.valuation_rate),
                    voucher_type="SC Stock Entry", voucher_no=self.name, voucher_detail_no=row.name,
                    batch=row.batch, bin_location=row.target_bin,
                    posting_date=self.posting_date, posting_time=self.posting_time,
                )

    def _reverse_stock_ledger(self):
        """Cancel: insert SLE đối ứng + đánh dấu original is_cancelled."""
        sles = frappe.get_all(
            "SC Stock Ledger Entry",
            filters={"voucher_type": "SC Stock Entry", "voucher_no": self.name, "is_cancelled": 0},
            fields=["name", "item", "warehouse", "batch", "bin_location",
                    "qty_change", "valuation_rate"],
        )
        from supplycore.supplycore.doctype.sc_stock_ledger_entry.sc_stock_ledger_entry import SCStockLedgerEntry
        for s in sles:
            SCStockLedgerEntry.post(
                item=s.item, warehouse=s.warehouse, qty_change=-flt(s.qty_change),
                valuation_rate=flt(s.valuation_rate),
                voucher_type="SC Stock Entry", voucher_no=self.name,
                voucher_detail_no=s.name + "-CANCEL",
                batch=s.batch, bin_location=s.bin_location,
                remarks=f"Cancel của SLE {s.name}",
            )
            frappe.db.set_value("SC Stock Ledger Entry", s.name, "is_cancelled", 1)


    # ------------------------------------------------------------------
    # BUG-001: chặn tồn kho âm + BUG-002: dùng available_qty
    # ------------------------------------------------------------------
    def _enforce_no_negative_stock(self):
        """Block submit nếu sau giao dịch xuất kho tồn khả dụng < 0.

        Áp dụng cho Material Issue + Material Transfer (only from_warehouse).
        Cộng dồn qty theo item+batch trong cùng SE để tránh double-debit khi
        có nhiều dòng cùng item.
        """
        if self.docstatus != 0:  # chỉ check khi đang draft → trước submit
            return
        if self.entry_type not in ISSUE_TYPES:
            return
        if not self.from_warehouse:
            return

        from supplycore.supplycore.doctype.sc_stock_ledger_entry.sc_stock_ledger_entry import SCStockLedgerEntry

        # Gộp qty theo (item, batch) trong cùng SE
        demand = {}
        for row in self.items:
            key = (row.item, row.batch or None)
            demand[key] = demand.get(key, 0) + flt(row.qty)

        for (item, batch), need in demand.items():
            avail = SCStockLedgerEntry.get_available_qty(item, self.from_warehouse, batch)
            if need > avail:
                batch_label = f" lô {batch}" if batch else ""
                frappe.throw(
                    _("Không đủ tồn khả dụng cho {0}{1} tại kho {2}: "
                      "cần {3}, còn {4} (loại trừ QC Pending/Rejected/Blocked).")
                    .format(item, batch_label, self.from_warehouse, need, avail),
                    title="SC-E010 NEGATIVE_STOCK",
                )

    def _log_fefo_override_audit(self):
        """UC-16 4a: record approver + insert Frappe Comment để audit override."""
        for row in self.items:
            if row.fefo_override and row.batch:
                row.db_set("fefo_override_approved_by", frappe.session.user)
                row.db_set("fefo_override_approved_at", frappe.utils.now())
                try:
                    self.add_comment(
                        "Comment",
                        text=(f"<b>FEFO Override</b> — row {row.idx} batch {row.batch}: "
                              f"{frappe.utils.escape_html(row.fefo_override_reason or '')}"),
                    )
                except Exception as e:
                    frappe.log_error(message=str(e)[:500], title="UC-16 fefo_override audit")


def _is_fefo_strict():
    """Resolve FEFO strict mode từ SupplyCore Settings."""
    for fname in ("fefo_strict_mode", "enforce_fefo"):
        try:
            v = frappe.db.get_single_value("SupplyCore Settings", fname)
            if v is not None:
                return bool(v)
        except Exception:
            pass
    return True  # Default strict
