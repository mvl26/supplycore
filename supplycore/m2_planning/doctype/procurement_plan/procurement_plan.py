"""Procurement Plan — Kế hoạch mua sắm định kỳ (M2, UC-06).

Tự suggest số lượng cần mua dựa trên:
- avg_monthly_consumption (Stock Ledger Entry trong N tháng gần nhất)
- lead_time_days của Item
- safety_stock_factor (% bổ sung)
- current_stock hiện tại

Sau khi approve → tạo Material Request draft (1 MR gom tất cả items).
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, today, add_days, add_months, getdate


class ProcurementPlan(Document):

    def validate(self):
        self._validate_dates()
        self._compute_amounts()
        if self.docstatus == 0:
            self.status = "Draft"

    def on_submit(self):
        self.db_set("status", "Approved")

    def on_cancel(self):
        self.db_set("status", "Cancelled")

    # ------------------------------------------------------------------
    def _validate_dates(self):
        if getdate(self.from_date) > getdate(self.to_date):
            frappe.throw(_("Từ ngày phải trước Đến ngày"))
        if self.required_by and getdate(self.required_by) < getdate(self.plan_date):
            frappe.throw(_("Ngày cần hàng phải sau ngày lập kế hoạch"))

    def _compute_amounts(self):
        for row in self.items:
            row.estimated_amount = flt(row.planned_qty) * flt(row.estimated_unit_cost)
        self.total_estimated_cost = sum(flt(r.estimated_amount) for r in self.items)

    # ------------------------------------------------------------------
    # Action: tự nạp items với suggested qty từ consumption history
    # ------------------------------------------------------------------
    @frappe.whitelist()
    def auto_load_items(self, item_filter: str = None):
        """Tự nạp items có ROP < tồn kho hoặc avg consumption > 0.

        item_filter: optional, lọc theo Item Group name.
        """
        if self.docstatus != 0:
            frappe.throw(_("Chỉ load items khi Plan ở Draft"))
        if not self.warehouse:
            frappe.throw(_("Chọn Warehouse trước"))

        lookback = int(self.consumption_lookback_months or 3)
        safety_factor = 1 + flt(self.safety_stock_factor or 20) / 100

        # Lấy tất cả items active có giao dịch xuất kho trong window HOẶC có reorder_levels cho warehouse này
        items = frappe.db.sql("""
            SELECT DISTINCT i.name AS item_code, i.item_name, i.uom AS stock_uom,
                   COALESCE(i.lead_time_days, 30) AS lead_time_days,
                   COALESCE(i.safety_stock, 0) AS item_safety_stock
            FROM `tabSC Item` i
            WHERE i.disabled = 0
              AND i.is_stock_item = 1
              AND i.is_purchase_item = 1
              {item_group_filter}
              AND EXISTS (
                  SELECT 1 FROM `tabSC Stock Ledger Entry` sle
                  WHERE sle.item = i.name AND sle.warehouse = %(warehouse)s
                        AND sle.posting_date >= %(from_date)s AND sle.qty_change < 0
              )
            ORDER BY i.item_code
            LIMIT 500
        """.format(
            item_group_filter="AND i.item_group = %(item_group)s" if item_filter else ""
        ), {
            "warehouse": self.warehouse,
            "from_date": add_months(today(), -lookback),
            "item_group": item_filter,
        }, as_dict=True)

        # Clear existing rows
        self.items = []
        added = 0
        for it in items:
            current_stock = self._get_current_stock(it.item_code, self.warehouse)
            avg_monthly = self._get_avg_monthly_consumption(it.item_code, self.warehouse, lookback)

            # Suggested = avg_monthly × (lead_time/30) × safety_factor − current_stock
            lead_months = flt(it.lead_time_days) / 30.0
            base_demand = avg_monthly * lead_months
            target_stock = base_demand * safety_factor + flt(it.item_safety_stock)
            suggested = max(0, target_stock - current_stock)

            if suggested <= 0 and not avg_monthly:
                continue  # đủ hàng VÀ không có lịch sử tiêu thụ → bỏ qua

            self.append("items", {
                "item_code": it.item_code,
                "item_name": it.item_name,
                "uom": it.stock_uom,
                "current_stock": current_stock,
                "avg_monthly_consumption": round(avg_monthly, 2),
                "lead_time_days": it.lead_time_days,
                "safety_stock_qty": round(it.item_safety_stock + (base_demand * (safety_factor - 1)), 2),
                "planned_qty": round(suggested, 2) or 0,
                "estimated_unit_cost": self._get_last_purchase_rate(it.item_code),
                "preferred_supplier": self._get_preferred_supplier(it.item_code),
            })
            added += 1

        self._compute_amounts()
        self.save(ignore_permissions=False)
        return {"items_loaded": added, "total_estimated_cost": self.total_estimated_cost}

    # ------------------------------------------------------------------
    # Action: tự nạp items theo reorder level (UC-05/UC-06)
    # ------------------------------------------------------------------
    @frappe.whitelist()
    def auto_load_reorder_items(self):
        """UC-05/UC-06 hybrid: load items whose current_qty <= reorder_level
        (threshold-based, complements consumption-based auto_load_items)."""
        from supplycore.m2_planning.reorder import get_reorder_thresholds

        if self.docstatus != 0:
            frappe.throw(_("Chỉ load items khi Plan ở Draft"))
        if not self.warehouse:
            frappe.throw(_("Chọn Warehouse trước"))

        candidates = frappe.db.sql("""
            SELECT i.name AS item_code, i.item_name, i.uom AS stock_uom,
                   COALESCE(i.lead_time_days, 30) AS lead_time_days
            FROM `tabSC Item` i
            WHERE i.disabled = 0
              AND i.is_stock_item = 1
              AND i.is_purchase_item = 1
              AND (
                  i.reorder_level > 0
                  OR EXISTS (
                      SELECT 1 FROM `tabSC Item Reorder` r
                      WHERE r.parent = i.name AND r.parenttype = 'SC Item'
                        AND r.warehouse = %(warehouse)s AND r.reorder_level > 0
                  )
              )
            ORDER BY i.item_code
            LIMIT 500
        """, {"warehouse": self.warehouse}, as_dict=True)

        self.items = []
        added = 0
        for it in candidates:
            th = get_reorder_thresholds(it.item_code, self.warehouse)
            reorder = th["reorder_level"]
            if reorder <= 0:
                continue
            current = self._get_current_stock(it.item_code, self.warehouse)
            if current > reorder:
                continue

            if th["standard_order_qty"] > 0:
                qty = th["standard_order_qty"]
            elif th["max_stock"] > 0:
                qty = max(0.0, th["max_stock"] - current)
            else:
                qty = max(0.0, reorder * 2 - current)

            self.append("items", {
                "item_code": it.item_code,
                "item_name": it.item_name,
                "uom": it.stock_uom,
                "current_stock": current,
                "avg_monthly_consumption": 0,
                "lead_time_days": it.lead_time_days,
                "safety_stock_qty": th["safety_stock"],
                "planned_qty": round(qty, 2),
                "estimated_unit_cost": self._get_last_purchase_rate(it.item_code),
                "preferred_supplier": self._get_preferred_supplier(it.item_code),
            })
            added += 1

        self._compute_amounts()
        self.save(ignore_permissions=False)
        return {"items_loaded": added, "total_estimated_cost": self.total_estimated_cost}

    # ------------------------------------------------------------------
    # Action: tạo Material Request draft từ items đã approve
    # ------------------------------------------------------------------
    @frappe.whitelist()
    def make_material_request(self):
        if self.docstatus != 1:
            frappe.throw(_("Plan phải được Submit (Approved) trước khi tạo MR"))
        if self.material_request:
            frappe.throw(_("Plan đã tạo MR: {0}").format(self.material_request))

        valid_items = [r for r in self.items if flt(r.planned_qty) > 0]
        if not valid_items:
            frappe.throw(_("Không có item nào có planned_qty > 0"))

        required_date = self.required_by or add_days(today(), 7)

        mr = frappe.new_doc("SC Material Request")
        mr.request_type = "Purchase"
        mr.transaction_date = today()
        mr.schedule_date = required_date
        mr.warehouse = self.warehouse
        mr.procurement_plan = self.name
        mr.auto_generated = 1
        mr.requested_by = (frappe.session.user
                           if frappe.session.user not in (None, "", "Guest")
                           else "Administrator")

        for row in valid_items:
            mr.append("items", {
                "item": row.item_code,
                "qty": row.planned_qty,
                "uom": row.uom,
                "warehouse": self.warehouse,
                "schedule_date": required_date,
                "estimated_unit_cost": flt(row.estimated_unit_cost),
            })

        mr.insert(ignore_permissions=False)
        self.db_set("material_request", mr.name)
        self.db_set("status", "Generated")
        return mr.name

    # ------------------------------------------------------------------
    # Helpers — query Stock Ledger / Bin / PO
    # ------------------------------------------------------------------
    @staticmethod
    def _get_current_stock(item_code, warehouse) -> float:
        # Query SC Stock Ledger Entry (không còn tabBin của ERPNext)
        return flt(frappe.db.sql("""
            SELECT COALESCE(SUM(qty_change), 0)
            FROM `tabSC Stock Ledger Entry`
            WHERE item = %s AND warehouse = %s AND is_cancelled = 0
        """, (item_code, warehouse))[0][0])

    @staticmethod
    def _get_avg_monthly_consumption(item_code, warehouse, months: int = 3) -> float:
        result = frappe.db.sql("""
            SELECT COALESCE(SUM(ABS(qty_change)), 0) AS total
            FROM `tabSC Stock Ledger Entry`
            WHERE item = %s
              AND warehouse = %s
              AND posting_date >= %s
              AND qty_change < 0
              AND is_cancelled = 0
        """, (item_code, warehouse, add_months(today(), -months)))
        total = flt(result[0][0]) if result else 0
        return total / months if months > 0 else 0

    @staticmethod
    def _get_last_purchase_rate(item_code) -> float:
        rate = frappe.db.sql("""
            SELECT poi.rate
            FROM `tabSC Purchase Order Item` poi
            JOIN `tabSC Purchase Order` po ON po.name = poi.parent
            WHERE poi.item = %s AND po.docstatus = 1
            ORDER BY po.transaction_date DESC LIMIT 1
        """, item_code)
        return flt(rate[0][0]) if rate else 0

    @staticmethod
    def _get_preferred_supplier(item_code) -> str:
        result = frappe.db.sql("""
            SELECT po.supplier, COUNT(*) AS cnt
            FROM `tabSC Purchase Order Item` poi
            JOIN `tabSC Purchase Order` po ON po.name = poi.parent
            WHERE poi.item = %s
              AND po.docstatus = 1
              AND po.transaction_date >= %s
            GROUP BY po.supplier
            ORDER BY cnt DESC LIMIT 1
        """, (item_code, add_months(today(), -12)))
        return result[0][0] if result else None
