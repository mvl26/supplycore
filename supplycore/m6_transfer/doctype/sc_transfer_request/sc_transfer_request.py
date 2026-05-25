"""SC Transfer Request — Phiếu yêu cầu luân chuyển nội bộ (M6, UC-18).

Luồng:
  Draft → submit → Approved → make_stock_entry → SE Material Transfer draft
  → SE submit → TR.status = Received (tồn kho đã chuyển thực sự)
  → SE cancel → TR.status revert → Approved
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate, today, now


class SCTransferRequest(Document):

    def validate(self):
        self._validate_warehouses()
        self._validate_dates()
        self._fill_available_qty()
        self._compute_total()
        self._detect_cross_tier()
        if self.docstatus == 0:
            self.status = "Draft"

    def on_submit(self):
        # UC-18 step 5: cross-tier → enforce Manager role
        if self.requires_manager_approval:
            user_roles = set(frappe.get_roles(frappe.session.user))
            if not (user_roles & {"SupplyCore Manager", "System Manager"}):
                frappe.throw(_(
                    "SC-E-TRANSFER-MANAGER-REQUIRED: TR cross-tier yêu cầu role "
                    "SupplyCore Manager để submit"
                ))
        self.db_set("status", "Approved")
        self.db_set("approved_by", frappe.session.user
                    if frappe.session.user not in (None, "", "Guest") else "Administrator")
        self.db_set("approved_at", now())

    def on_cancel(self):
        self.db_set("status", "Cancelled")
        # Nếu có Stock Entry liên kết và chưa cancel — block
        if self.stock_entry and frappe.db.exists("SC Stock Entry", self.stock_entry):
            se_doc = frappe.db.get_value("SC Stock Entry", self.stock_entry, "docstatus")
            if se_doc == 1:
                frappe.throw(_("Phải cancel SC Stock Entry {0} trước").format(self.stock_entry))

    # ------------------------------------------------------------------
    def _validate_warehouses(self):
        # QAv3-BUG-M6-01: hard-stop khi from=to. Tester báo có thể tạo TR
        # với cùng kho — backend đã có check nhưng error code không rõ.
        if not self.from_warehouse:
            frappe.throw(_("Phải chọn kho nguồn"))
        if not self.to_warehouse:
            frappe.throw(_("Phải chọn kho đích"))
        if self.from_warehouse == self.to_warehouse:
            frappe.throw(_(
                "SC-E024 SAME_WAREHOUSE: Kho nguồn ({0}) và kho đích phải KHÁC "
                "nhau. Chuyển trong cùng 1 kho tạo bút toán ảo làm sai số liệu."
            ).format(self.from_warehouse),
                title="SC-E024 SAME_WAREHOUSE")
        for wh_field, wh_name in [("from_warehouse", self.from_warehouse),
                                    ("to_warehouse", self.to_warehouse)]:
            wh = frappe.db.get_value("SC Warehouse", wh_name,
                                       ["disabled", "is_group"], as_dict=True)
            if not wh:
                continue
            if wh.disabled:
                frappe.throw(_("{0} {1} đang disabled").format(wh_field, wh_name))
            if wh.is_group:
                frappe.throw(_("{0} {1} là group warehouse — không thể chứa stock")
                             .format(wh_field, wh_name))

    def _validate_dates(self):
        if getdate(self.required_by) < getdate(self.request_date):
            frappe.throw(_("Ngày cần phải sau hoặc bằng ngày yêu cầu"))

    def _fill_available_qty(self):
        """Snapshot tồn kho item ở source warehouse vào available_at_source."""
        for row in self.items:
            if not row.item or not self.from_warehouse:
                continue
            available = flt(frappe.db.sql("""
                SELECT COALESCE(SUM(qty_change), 0)
                FROM `tabSC Stock Ledger Entry`
                WHERE item = %s AND warehouse = %s AND is_cancelled = 0
            """, (row.item, self.from_warehouse))[0][0])
            row.available_at_source = available
            # Auto-set approved_qty = requested nếu chưa nhập
            if not row.approved_qty:
                row.approved_qty = row.requested_qty
            # Validate qty không vượt available (chỉ khi submit)
            if self.docstatus == 1 and flt(row.approved_qty) > available:
                frappe.throw(_(
                    "SC-E-TRANSFER-INSUFFICIENT: Item {0}: SL duyệt {1} > "
                    "tồn kho nguồn {2}. Tối đa có thể chuyển: {2}"
                ).format(row.item, row.approved_qty, available))

    def _compute_total(self):
        self.total_qty = sum(flt(r.requested_qty) for r in self.items)

    def _detect_cross_tier(self):
        """Cross-tier transfer (Sub→Department, Main→Department) → require Manager approval."""
        if not (self.from_warehouse and self.to_warehouse):
            return
        from_type = frappe.db.get_value("SC Warehouse", self.from_warehouse, "warehouse_type")
        to_type = frappe.db.get_value("SC Warehouse", self.to_warehouse, "warehouse_type")
        # Logic: bất kỳ transfer nào tới Department warehouse → require Manager approval
        cross_tier = (to_type == "Department" or from_type == "Department")
        if cross_tier:
            self.requires_manager_approval = 1

    # ------------------------------------------------------------------
    # Action — chuyển TR Approved → SC Stock Entry Material Transfer draft
    # ------------------------------------------------------------------
    @frappe.whitelist()
    def make_stock_entry(self):
        if self.docstatus != 1:
            frappe.throw(_("TR phải submit trước khi tạo Stock Entry"))
        if self.status not in ("Approved",):
            frappe.throw(_("TR phải ở status Approved (hiện: {0})").format(self.status))
        if self.stock_entry:
            frappe.throw(_("TR đã có Stock Entry: {0}").format(self.stock_entry))

        valid_items = [r for r in self.items if flt(r.approved_qty) > 0]
        if not valid_items:
            frappe.throw(_("Không có item nào có approved_qty > 0"))

        from supplycore.api.fefo import auto_pick_fefo

        se = frappe.new_doc("SC Stock Entry")
        se.entry_type = "Material Transfer"
        se.posting_date = today()
        se.from_warehouse = self.from_warehouse
        se.to_warehouse = self.to_warehouse
        se.transfer_request = self.name
        se.purpose = f"Transfer Request {self.name}"

        for row in valid_items:
            qty_left = flt(row.approved_qty)
            has_batch = frappe.db.get_value("SC Item", row.item, "has_batch_no")
            # TH1: row đã chỉ định batch → dùng nguyên 1 dòng SE
            if row.batch or not has_batch:
                se.append("items", {
                    "item": row.item, "qty": qty_left, "uom": row.uom,
                    "batch": row.batch or None, "valuation_rate": 0,
                })
                continue
            # TH2: item quản lý lô nhưng TR không chỉ định batch → FEFO auto-pick
            #  tồn ĐÃ gắn lô; phần còn thiếu lấy từ tồn CHƯA gắn lô (hàng tồn cũ
            #  nhập trước khi item bật quản lý lô — vẫn cho chuyển nguyên trạng).
            pick = auto_pick_fefo(row.item, self.from_warehouse, qty_left)
            for b in (pick.get("picked") or []):
                se.append("items", {
                    "item": row.item, "qty": flt(b["suggested_qty"]), "uom": row.uom,
                    "batch": b["batch_no"], "valuation_rate": 0,
                })
            shortfall = flt(pick.get("shortfall", 0))
            if shortfall > 0:
                move = min(shortfall, _batchless_stock(row.item, self.from_warehouse))
                if move > 0:
                    se.append("items", {
                        "item": row.item, "qty": move, "uom": row.uom,
                        "batch": None, "valuation_rate": 0,
                    })
                    shortfall -= move
            if shortfall > 0:
                frappe.throw(_(
                    "SC-E-TRANSFER-SHORTAGE: Item {0} — kho nguồn không đủ tồn để "
                    "chuyển (còn thiếu {1})."
                ).format(row.item, shortfall))

        se.flags.ignore_permissions = True
        se.insert()
        self.db_set("stock_entry", se.name)
        self.db_set("status", "In Transit")
        return se.name

    @frappe.whitelist()
    def get_transfer_slip_data(self):
        """UC-18 step 7: data cho in phiếu chuyển kho qua Frappe Print Format."""
        items = [{
            "item": r.item, "uom": r.uom, "batch": r.batch,
            "requested_qty": flt(r.requested_qty),
            "approved_qty": flt(r.approved_qty),
            "transferred_qty": flt(r.transferred_qty or 0),
            "available_at_source": flt(r.available_at_source or 0),
        } for r in self.items]
        return {
            "name": self.name,
            "request_date": str(self.request_date) if self.request_date else "",
            "transfer_type": self.transfer_type,
            "required_by": str(self.required_by) if self.required_by else "",
            "from_warehouse": self.from_warehouse,
            "to_warehouse": self.to_warehouse,
            "requested_by": self.requested_by,
            "approved_by": self.approved_by,
            "approved_at": str(self.approved_at) if self.approved_at else "",
            "stock_entry": self.stock_entry,
            "status": self.status,
            "items": items,
            "total_qty": flt(self.total_qty),
            "url": f"/app/sc-transfer-request/{self.name}",
        }


def _batchless_stock(item, warehouse):
    """Tồn CHƯA gắn lô của 1 item tại 1 kho — hàng nhập trước khi item bật
    quản lý lô. Cho phép chuyển/xuất nguyên trạng (không ép gán lô ngược)."""
    v = frappe.db.sql("""
        SELECT COALESCE(SUM(qty_change), 0) FROM `tabSC Stock Ledger Entry`
        WHERE item = %s AND warehouse = %s AND is_cancelled = 0
          AND (batch IS NULL OR batch = '')
    """, (item, warehouse))
    return flt(v[0][0]) if v else 0.0


# ---------------------------------------------------------------------------
# Hook gọi từ SC Stock Entry on_submit/cancel để update TR status
# ---------------------------------------------------------------------------
def update_tr_on_se_submit(se_doc):
    if not se_doc.get("transfer_request"):
        return
    if not frappe.db.exists("SC Transfer Request", se_doc.transfer_request):
        return
    # Update transferred_qty cho từng row
    tr = frappe.get_doc("SC Transfer Request", se_doc.transfer_request)
    se_qty_per_item = {}
    for row in se_doc.items:
        se_qty_per_item.setdefault(row.item, 0)
        se_qty_per_item[row.item] += flt(row.qty)
    for tr_row in tr.items:
        if tr_row.item in se_qty_per_item:
            tr_row.db_set("transferred_qty", flt(se_qty_per_item[tr_row.item]),
                           update_modified=False)
    tr.db_set("status", "Received")


def update_tr_on_se_cancel(se_doc):
    if not se_doc.get("transfer_request"):
        return
    if not frappe.db.exists("SC Transfer Request", se_doc.transfer_request):
        return
    tr = frappe.get_doc("SC Transfer Request", se_doc.transfer_request)
    for tr_row in tr.items:
        tr_row.db_set("transferred_qty", 0, update_modified=False)
    if tr.docstatus == 1:
        tr.db_set("status", "Approved")
    frappe.db.set_value("SC Transfer Request", tr.name, "stock_entry", None)
