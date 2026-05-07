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


class SCPurchaseReceipt(Document):

    def validate(self):
        from supplycore.utils.validators import validate_supplier, validate_warehouse
        validate_supplier(self.supplier)
        validate_warehouse(self.to_warehouse, label=_("Kho đích"))
        self._compute_totals()
        self._validate_expiry()
        if self.docstatus == 0 and not self.qc_status:
            self.qc_status = "Pending"

    def on_submit(self):
        self._create_batches_if_needed()
        self._post_stock_ledger()
        if self.qc_required and not self.is_return:
            self._auto_create_qi()
        self._update_po_received_qty()

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

    def _create_batches_if_needed(self):
        """Nếu row có expiry_date + chưa có batch_no → tạo SC Batch tự động."""
        for r in self.items:
            has_batch = frappe.db.get_value("SC Item", r.item, "has_batch_no")
            if not has_batch:
                continue
            if not r.batch_no and r.expiry_date:
                # Auto generate batch_id
                from frappe.utils import random_string
                bid = f"{r.item}-{getdate(r.expiry_date).strftime('%Y%m')}-{random_string(4)}"
                b = frappe.new_doc("SC Batch")
                b.batch_id = bid
                b.item = r.item
                b.expiry_date = r.expiry_date
                b.manufacturing_date = r.manufacturing_date
                b.supplier = self.supplier
                b.supplier_batch_no = r.supplier_batch_no
                b.flags.ignore_permissions = True
                b.insert()
                r.db_set("batch_no", b.name, update_modified=False)

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
            frappe.db.set_value("SC Stock Ledger Entry", s.name, "is_cancelled", 1)

    def _auto_create_qi(self):
        for r in self.items:
            existing = frappe.db.exists("SC Quality Inspection",
                                         {"purchase_receipt": self.name, "item": r.item, "pr_item_ref": r.name})
            if existing:
                continue
            template = _find_checklist_template(r.item)
            qi = frappe.new_doc("SC Quality Inspection")
            qi.inspection_date = today()
            qi.purchase_receipt = self.name
            qi.pr_item_ref = r.name
            qi.item = r.item
            qi.batch = r.batch_no
            qi.received_qty = r.qty
            qi.checklist_template = template
            qi.inspected_by = frappe.session.user if frappe.session.user not in (None, "Guest") else "Administrator"
            if template:
                tpl = frappe.get_doc("QC Checklist Template", template)
                for crit in sorted(tpl.criteria, key=lambda c: c.sequence or 0):
                    qi.append("readings", {"specification": crit.criterion_name, "status": ""})
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
        for poi in po.items:
            received = frappe.db.sql("""
                SELECT COALESCE(SUM(pri.qty), 0)
                FROM `tabSC Purchase Receipt Item` pri
                JOIN `tabSC Purchase Receipt` pr ON pr.name = pri.parent
                WHERE pr.purchase_order = %s AND pri.item = %s
                  AND pr.docstatus = 1 AND pr.is_return = 0
            """, (self.purchase_order, poi.item))[0][0]
            frappe.db.set_value("SC Purchase Order Item", poi.name, "received_qty", flt(received))
        # Auto status
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
    return frappe.db.get_value("QC Checklist Template",
                                {"item_group": ["in", [None, ""]], "enabled": 1}, "name")
