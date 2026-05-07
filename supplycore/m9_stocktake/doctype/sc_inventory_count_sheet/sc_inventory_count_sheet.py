"""SC Inventory Count Sheet — phiếu kiểm kê (M9, UC-27)."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, today, now


class SCInventoryCountSheet(Document):

    def validate(self):
        self._snapshot_system_qty_if_new()
        self._compute_variances()
        self._compute_summary()
        if self.docstatus == 0 and not self.status:
            self.status = "Draft"

    def on_submit(self):
        # Submit = đã đếm xong, đợi reconcile
        self.db_set("status", "Counted")

    def on_cancel(self):
        self.db_set("status", "Cancelled")

    # ------------------------------------------------------------------
    def _snapshot_system_qty_if_new(self):
        """Lần đầu save: snapshot system_qty + valuation_rate từ SC SLE."""
        for row in self.items:
            if row.system_qty is None:  # chưa snapshot
                row.system_qty = self._get_system_qty(row.item, self.warehouse, row.batch)
            if not row.valuation_rate:
                row.valuation_rate = self._get_last_valuation(row.item, self.warehouse)

    def _compute_variances(self):
        threshold = flt(self.recount_threshold_pct or 5)
        for row in self.items:
            actual = flt(row.actual_qty if row.actual_qty is not None else 0)
            # Nếu có recount → ưu tiên giá trị recount
            if row.recount_actual_qty:
                actual = flt(row.recount_actual_qty)
            row.difference = actual - flt(row.system_qty or 0)
            if flt(row.system_qty or 0) > 0:
                row.variance_pct = abs(row.difference) / flt(row.system_qty) * 100
            else:
                row.variance_pct = 100 if row.difference else 0
            row.needs_recount = 1 if flt(row.variance_pct) > threshold else 0
            row.variance_value = flt(row.difference) * flt(row.valuation_rate or 0)

    def _compute_summary(self):
        self.total_items = len(self.items)
        self.mismatched_items = sum(1 for r in self.items if abs(flt(r.difference or 0)) > 0.01)
        self.total_variance_qty = sum(flt(r.difference or 0) for r in self.items)
        self.total_variance_value = sum(flt(r.variance_value or 0) for r in self.items)

    @staticmethod
    def _get_system_qty(item, warehouse, batch=None) -> float:
        sql = """
            SELECT COALESCE(SUM(qty_change), 0)
            FROM `tabSC Stock Ledger Entry`
            WHERE item = %s AND warehouse = %s AND is_cancelled = 0
        """
        params = [item, warehouse]
        if batch:
            sql += " AND batch = %s"
            params.append(batch)
        return flt(frappe.db.sql(sql, tuple(params))[0][0])

    @staticmethod
    def _get_last_valuation(item, warehouse) -> float:
        rate = frappe.db.sql("""
            SELECT valuation_rate FROM `tabSC Stock Ledger Entry`
            WHERE item = %s AND warehouse = %s AND is_cancelled = 0
              AND valuation_rate > 0
            ORDER BY posting_date DESC, creation DESC LIMIT 1
        """, (item, warehouse))
        return flt(rate[0][0]) if rate else 0

    # ------------------------------------------------------------------
    # Action: auto-load items theo scope
    # ------------------------------------------------------------------
    @frappe.whitelist()
    def auto_load_items(self):
        """Tự nạp items đang có tồn kho > 0 ở warehouse, theo scope."""
        if self.docstatus != 0:
            frappe.throw(_("Chỉ load khi Draft"))

        params = {"wh": self.warehouse}
        scope_filter = ""
        if self.count_scope == "By Item Group" and self.item_group:
            scope_filter = "AND i.item_group = %(grp)s"
            params["grp"] = self.item_group

        rows = frappe.db.sql(f"""
            SELECT sle.item, i.item_name, sle.batch, i.uom,
                   SUM(sle.qty_change) AS qty
            FROM `tabSC Stock Ledger Entry` sle
            JOIN `tabSC Item` i ON i.name = sle.item
            WHERE sle.warehouse = %(wh)s AND sle.is_cancelled = 0
              {scope_filter}
            GROUP BY sle.item, sle.batch
            HAVING qty > 0
            ORDER BY sle.item, sle.batch
        """, params, as_dict=True)

        # Filter zone nếu count_scope=By Zone
        if self.count_scope == "By Zone" and self.bin_zone:
            zone_bins = frappe.get_all("Bin Location",
                {"warehouse": self.warehouse, "zone": self.bin_zone}, ["name"])
            if not zone_bins:
                frappe.throw(_("Không có bin nào ở zone {0}").format(self.bin_zone))

        self.items = []
        for r in rows:
            row_data = {
                "item": r.item, "item_name": r.item_name,
                "uom": r.uom, "batch": r.batch,
                "system_qty": flt(r.qty),
                "valuation_rate": self._get_last_valuation(r.item, self.warehouse),
            }
            self.append("items", row_data)
        self.save(ignore_permissions=True)
        return {"items_loaded": len(self.items)}

    # ------------------------------------------------------------------
    # Action: tạo SC Stock Reconciliation từ ICS đã Counted
    # ------------------------------------------------------------------
    @frappe.whitelist()
    def make_stock_reconciliation(self):
        if self.docstatus != 1:
            frappe.throw(_("ICS phải submit (Counted) trước"))
        if self.status == "Reconciled" or self.stock_reconciliation:
            frappe.throw(_("ICS đã reconcile: {0}").format(self.stock_reconciliation))

        diff_rows = [r for r in self.items if abs(flt(r.difference or 0)) > 0.01]
        if not diff_rows:
            frappe.throw(_("Không có item nào có chênh lệch — không cần reconcile"))

        sr = frappe.new_doc("SC Stock Reconciliation")
        sr.posting_date = today()
        sr.count_sheet = self.name
        sr.warehouse = self.warehouse
        for r in diff_rows:
            sr.append("items", {
                "item": r.item, "uom": r.uom, "batch": r.batch,
                "bin_location": r.bin_location,
                "system_qty": flt(r.system_qty),
                "actual_qty": flt(r.actual_qty) + (flt(r.recount_actual_qty) if r.recount_actual_qty else 0)
                              if not r.recount_actual_qty else flt(r.recount_actual_qty),
                "difference": flt(r.difference),
                "valuation_rate": flt(r.valuation_rate),
                "amount_change": flt(r.variance_value),
                "reason": r.reason,
                "remarks": r.remarks,
            })
        sr.flags.ignore_permissions = True
        sr.insert()
        self.db_set("stock_reconciliation", sr.name)
        return sr.name
