"""Release Order — Lệnh gọi hàng từ Framework Contract (M1)."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, today, flt


class ReleaseOrder(Document):

    def validate(self):
        self._auto_fill_items_from_fc_if_empty()
        self._validate_dates()
        self._validate_against_contract()
        self._fill_unit_prices_and_amounts()
        self._compute_total()
        if self.docstatus == 0:
            self.status = "Draft"

    def _auto_fill_items_from_fc_if_empty(self):
        """Nếu chưa có items mà đã chọn FC → tự nạp tất cả FC Item còn qty (qty=0)."""
        if self.items or not self.framework_contract:
            return
        fc = frappe.get_doc("Framework Contract", self.framework_contract)
        for fci in fc.items:
            if flt(fci.remaining_qty) <= 0:
                continue
            self.append("items", {
                "fc_item":       fci.name,
                "item_code":     fci.item_code,
                "uom":           fci.uom,
                "qty":           0,
                "unit_price":    fci.unit_price,
                "available_qty": fci.remaining_qty,
            })

    def on_submit(self):
        self.db_set("status", "Approved")
        # Snapshot remaining HĐK lúc submit phục vụ audit
        fc = frappe.get_doc("Framework Contract", self.framework_contract)
        self.db_set("remaining_value_at_release", flt(fc.remaining_value))
        # Recalc FC: committed_value tăng theo total_amount của RO này
        fc.recalculate_used_value()

    def on_cancel(self):
        self.db_set("status", "Cancelled")
        # Recalc FC: committed_value giảm
        fc = frappe.get_doc("Framework Contract", self.framework_contract)
        fc.recalculate_used_value()

    # ------------------------------------------------------------------
    def _validate_dates(self):
        if getdate(self.required_by) < getdate(self.release_date):
            frappe.throw(_("Ngày cần giao không được trước ngày lệnh"))

    def _validate_against_contract(self):
        fc = frappe.get_doc("Framework Contract", self.framework_contract)
        # HĐK phải còn hiệu lực
        if fc.docstatus != 1:
            frappe.throw(_("Hợp đồng khung {0} chưa được phê duyệt").format(fc.name),
                         title="SC-E002 FC_INACTIVE")
        if fc.status != "Active":
            frappe.throw(_("Hợp đồng khung {0} không ở trạng thái Active (hiện: {1})").format(
                fc.name, fc.status), title="SC-E002 FC_INACTIVE")
        if getdate(today()) > getdate(fc.valid_to):
            frappe.throw(_("Hợp đồng khung {0} đã hết hạn ngày {1}").format(
                fc.name, fc.valid_to), title="SC-E002 FC_EXPIRED")
        # Mỗi item phải nằm trong HĐK + không vượt remaining_qty
        for row in self.items:
            fc_item = self._find_fc_item(fc, row.item_code)
            if not fc_item:
                frappe.throw(_("Vật tư {0} không có trong hợp đồng khung").format(row.item_code),
                             title="SC-E002 FC_ITEM_NOT_FOUND")
            if flt(row.qty) > flt(fc_item.remaining_qty):
                frappe.throw(_("SL gọi {0} cho {1} vượt SL còn lại trong HĐK ({2})").format(
                    row.qty, row.item_code, fc_item.remaining_qty),
                    title="SC-E002 FC_EXCEEDED")

    def _fill_unit_prices_and_amounts(self):
        fc = frappe.get_doc("Framework Contract", self.framework_contract)
        for row in self.items:
            fc_item = self._find_fc_item(fc, row.item_code)
            if fc_item:
                row.fc_item = fc_item.name
                row.unit_price = flt(fc_item.unit_price)
                row.available_qty = flt(fc_item.remaining_qty)
            row.amount = flt(row.qty) * flt(row.unit_price)

    def _compute_total(self):
        self.total_amount = sum(flt(r.amount) for r in self.items)
        # Submit time phải có giá trị > 0
        if self.docstatus == 1 and flt(self.total_amount) <= 0:
            frappe.throw(_("RO không có vật tư nào có SL > 0 — không thể submit"))
        # Cảnh báo nếu vượt remaining_value của FC
        fc_remaining = frappe.db.get_value("Framework Contract", self.framework_contract, "remaining_value") or 0
        if flt(self.total_amount) > flt(fc_remaining):
            frappe.throw(_("Tổng giá trị RO ({0}) vượt hạn mức HĐK còn lại ({1})").format(
                frappe.format(self.total_amount, {"fieldtype": "Currency"}),
                frappe.format(fc_remaining, {"fieldtype": "Currency"})),
                title="SC-E002 FC_EXCEEDED")

    @staticmethod
    def _find_fc_item(fc_doc, item_code):
        for r in fc_doc.items:
            if r.item_code == item_code:
                return r
        return None

    # ------------------------------------------------------------------
    # Action — convert sang Purchase Order
    # ------------------------------------------------------------------
    @frappe.whitelist()
    def make_purchase_order(self):
        """Tạo PO ERPNext từ RO này (chỉ khi RO đã Approved)."""
        if self.status != "Approved":
            frappe.throw(_("Chỉ tạo PO khi RO ở trạng thái Approved"))
        if self.purchase_order:
            frappe.throw(_("RO này đã tạo PO {0}").format(self.purchase_order))

        # Lấy default warehouse từ SupplyCore Settings, fallback first non-group warehouse
        default_wh = None
        try:
            default_wh = frappe.db.get_single_value("SupplyCore Settings", "default_warehouse")
        except Exception:
            pass  # Field chưa tồn tại — sẽ fallback
        if not default_wh:
            default_wh = frappe.db.get_value("SC Warehouse",
                                              {"is_group": 0, "disabled": 0},
                                              "name")
        if not default_wh:
            frappe.throw(_("Cần ít nhất 1 Warehouse active. Cấu hình tại SupplyCore Settings → default_warehouse"))

        po = frappe.new_doc("SC Purchase Order")
        po.supplier = self.supplier
        po.transaction_date = today()
        po.schedule_date = self.required_by
        po.to_warehouse = default_wh
        po.framework_contract = self.framework_contract
        po.release_order = self.name
        for row in self.items:
            po.append("items", {
                "item": row.item_code,
                "qty": row.qty,
                "uom": row.uom,
                "rate": row.unit_price,
                "schedule_date": self.required_by,
                "warehouse": default_wh,
            })
        po.insert(ignore_permissions=False)
        self.db_set("purchase_order", po.name)
        self.db_set("status", "Converted")
        # Recalc FC: status RO chuyển từ Approved → Converted, committed_value giảm
        fc = frappe.get_doc("Framework Contract", self.framework_contract)
        fc.recalculate_used_value()
        return po.name
