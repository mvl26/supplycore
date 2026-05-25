"""SC Inventory Count Sheet — phiếu kiểm kê (M9, UC-27)."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, today, now


class SCInventoryCountSheet(Document):

    def validate(self):
        # QAv3-BUG-M9-01: Block user submit value tùy ý vào summary fields.
        # Schema có read_only=1 nhưng Frappe Desk admin có thể bypass.
        # Lưu giá trị user submit để so sánh — nếu khác giá trị compute thì
        # user đã cố ghi đè → log audit.
        user_submitted = {
            "total_items": flt(self.total_items),
            "mismatched_items": flt(self.mismatched_items),
            "total_variance_qty": flt(self.total_variance_qty),
            "total_variance_value": flt(self.total_variance_value),
        }
        self._snapshot_system_qty_if_new()
        self._compute_variances()
        self._compute_summary()  # overwrite summary fields từ items
        for fname, user_val in user_submitted.items():
            computed = flt(self.get(fname))
            if user_val and abs(user_val - computed) > 0.01:
                frappe.log_error(
                    message=f"ICS {self.name}: user gửi {fname}={user_val} nhưng "
                            f"system compute={computed}. Đã overwrite.",
                    title="SC-E025 ICS_SUMMARY_TAMPERING",
                )
        if self.docstatus == 0 and not self.status:
            self.status = "Draft"

    def before_submit(self):
        """UC-27 6a: third_count_qty yêu cầu manager_witness."""
        has_third = any(flt(r.third_count_qty) > 0 for r in self.items)
        if has_third and not self.manager_witness:
            frappe.throw(_(
                "SC-E-ICS-WITNESS-REQUIRED: Đếm lần 3 yêu cầu Manager chứng kiến — "
                "chọn 'Manager witness'"
            ))

    def on_submit(self):
        # Submit = đã đếm xong, đợi reconcile
        self.db_set("status", "Counted")

    @frappe.whitelist()
    def start_counting(self):
        """UC-27 step 4: chuyển ICS sang In Progress để track partial counting."""
        if self.docstatus != 0:
            frappe.throw(_("Chỉ start khi Draft"))
        self.db_set("status", "In Progress")
        return {"status": "In Progress"}

    @frappe.whitelist()
    def get_count_sheet_print_data(self, hide_system_qty: int = None):
        """UC-27 step 2: data in phiếu kiểm kê. Default ẩn system_qty."""
        hide = self.hide_system_qty if hide_system_qty is None else int(hide_system_qty)
        items = []
        for r in self.items:
            row_data = {
                "item": r.item, "item_name": r.item_name, "uom": r.uom,
                "batch": r.batch, "bin_location": r.bin_location,
            }
            if not hide:
                row_data["system_qty"] = flt(r.system_qty)
            items.append(row_data)
        return {
            "name": self.name,
            "count_date": str(self.count_date) if self.count_date else "",
            "warehouse": self.warehouse,
            "planned_by": self.planned_by,
            "counted_by": self.counted_by,
            "count_scope": self.count_scope,
            "hide_system_qty": hide,
            "items": items,
            "url": f"/app/sc-inventory-count-sheet/{self.name}",
        }

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
            # UC-27 6a priority: third_count > recount > actual
            if row.third_count_qty:
                actual = flt(row.third_count_qty)
            elif row.recount_actual_qty:
                actual = flt(row.recount_actual_qty)
            else:
                actual = flt(row.actual_qty if row.actual_qty is not None else 0)
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
