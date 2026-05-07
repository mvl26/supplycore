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
        if self.from_warehouse == self.to_warehouse:
            frappe.throw(_("Kho nguồn và kho đích phải khác nhau"))
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
                frappe.throw(_("Item {0}: SL duyệt {1} > tồn kho nguồn {2}").format(
                    row.item, row.approved_qty, available),
                    title="SC-E005 STOCK_INSUFFICIENT")

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

        se = frappe.new_doc("SC Stock Entry")
        se.entry_type = "Material Transfer"
        se.posting_date = today()
        se.from_warehouse = self.from_warehouse
        se.to_warehouse = self.to_warehouse
        se.transfer_request = self.name  # link ngược về TR
        se.purpose = f"Transfer Request {self.name}"
        for row in valid_items:
            se.append("items", {
                "item": row.item,
                "qty": flt(row.approved_qty),
                "uom": row.uom,
                "batch": row.batch,
                "valuation_rate": 0,  # SE controller sẽ tính từ SLE legacy hoặc 0
            })
        se.flags.ignore_permissions = True
        se.insert()
        self.db_set("stock_entry", se.name)
        self.db_set("status", "In Transit")
        return se.name


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
