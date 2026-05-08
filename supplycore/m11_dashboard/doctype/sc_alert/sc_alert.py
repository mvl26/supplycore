"""SC Alert — alert log + actionable workflow.

Mỗi alert có thể trigger 1 hành động cụ thể tuỳ alert_type:
- expiring_batch  → SE Material Transfer to "Kho Cách ly QC"
- low_stock       → SC Material Request draft (refill)
- overdue_payment → SC Payment Entry draft (auto-fill từ PI)

Sau action: action_taken=1, action_doctype/name link đến doc đã tạo,
resolved=1, resolution_action='Acted Upon'.
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now, today, flt, add_days


# Quarantine warehouse — đọc từ Settings hoặc fallback
DEFAULT_QUARANTINE_WAREHOUSE = "Kho Cách ly QC"


class SCAlert(Document):

    def validate(self):
        if self.resolved and not self.resolved_by:
            self.resolved_by = frappe.session.user
            self.resolved_at = now()

    # ------------------------------------------------------------------
    # Actions — whitelisted để gọi từ JS button trên Alert form
    # ------------------------------------------------------------------
    @frappe.whitelist()
    def action_quarantine_batch(self):
        """expiring_batch alert → tạo SE Material Transfer di chuyển batch
        từ warehouse hiện tại → Kho Cách ly QC.

        Returns: tên SE draft.
        """
        if self.alert_type != "expiring_batch":
            frappe.throw(_("Action chỉ áp dụng cho alert expiring_batch"),
                          title="SC-E-ALERT-ACTION")
        if self.action_taken:
            frappe.throw(_("Alert này đã có action: {0} {1}").format(
                self.action_doctype, self.action_name),
                title="SC-E-ALERT-ACTION")
        if self.reference_doctype != "SC Batch" or not self.reference_name:
            frappe.throw(_("Alert thiếu reference SC Batch"), title="SC-E-ALERT-ACTION")

        batch = frappe.db.get_value("SC Batch", self.reference_name,
                                      ["item", "expiry_date"], as_dict=True)
        if not batch:
            frappe.throw(_("Batch {0} không tồn tại").format(self.reference_name))

        quarantine = self._get_quarantine_warehouse()

        # Tìm warehouse có stock của batch này (lấy warehouse có qty cao nhất)
        rows = frappe.db.sql("""
            SELECT warehouse, SUM(qty_change) AS qty
            FROM `tabSC Stock Ledger Entry`
            WHERE batch = %s AND is_cancelled = 0 AND warehouse != %s
            GROUP BY warehouse
            HAVING qty > 0
            ORDER BY qty DESC LIMIT 1
        """, (self.reference_name, quarantine), as_dict=True)
        if not rows:
            frappe.throw(_("Batch {0} không còn stock ở kho nào (ngoại trừ quarantine)").format(
                self.reference_name), title="SC-E-NO-STOCK")
        from_wh, qty = rows[0]["warehouse"], flt(rows[0]["qty"])

        item_uom = frappe.db.get_value("SC Item", batch.item, "uom")
        valuation = self._get_avg_valuation(self.reference_name, from_wh)

        se = frappe.new_doc("SC Stock Entry")
        se.entry_type = "Material Transfer"
        se.posting_date = today()
        se.from_warehouse = from_wh
        se.to_warehouse = quarantine
        se.remarks = f"Auto từ Alert {self.name}: chuyển lô sắp hết hạn vào quarantine"
        se.append("items", {
            "item": batch.item,
            "qty": qty,
            "uom": item_uom,
            "batch": self.reference_name,
            "valuation_rate": valuation,
            "s_warehouse": from_wh,
            "t_warehouse": quarantine,
        })
        se.flags.ignore_permissions = True
        se.insert()

        self._mark_action("SC Stock Entry", se.name)
        return se.name

    @frappe.whitelist()
    def action_create_material_request(self):
        """low_stock alert → tạo SC Material Request draft với item này, qty = safety_stock × 2."""
        if self.alert_type != "low_stock":
            frappe.throw(_("Action chỉ áp dụng cho alert low_stock"),
                          title="SC-E-ALERT-ACTION")
        if self.action_taken:
            frappe.throw(_("Alert này đã có action: {0} {1}").format(
                self.action_doctype, self.action_name),
                title="SC-E-ALERT-ACTION")
        if self.reference_doctype != "SC Item" or not self.reference_name:
            frappe.throw(_("Alert thiếu reference SC Item"), title="SC-E-ALERT-ACTION")

        item = frappe.db.get_value("SC Item", self.reference_name,
                                     ["safety_stock", "uom", "item_name"], as_dict=True)
        if not item:
            frappe.throw(_("Item {0} không tồn tại").format(self.reference_name))

        # Default warehouse cho refill: dùng warehouse main đầu tiên (is_group=0, depth=1)
        wh = frappe.db.get_value("SC Warehouse",
                                   {"disabled": 0, "is_group": 0,
                                    "warehouse_type": "Main"}, "name")
        if not wh:
            wh = frappe.db.get_value("SC Warehouse", {"disabled": 0, "is_group": 0}, "name")

        suggested_qty = max(flt(item.safety_stock) * 2, 1)

        mr = frappe.new_doc("SC Material Request")
        mr.request_type = "Purchase"
        mr.transaction_date = today()
        mr.schedule_date = add_days(today(), 7)
        mr.warehouse = wh
        mr.remarks = f"Auto từ Alert {self.name}: refill {item.item_name} dưới safety stock"
        mr.append("items", {
            "item": self.reference_name,
            "qty": suggested_qty,
            "uom": item.uom,
            "schedule_date": add_days(today(), 7),
        })
        mr.flags.ignore_permissions = True
        mr.insert()

        self._mark_action("SC Material Request", mr.name)
        return mr.name

    @frappe.whitelist()
    def action_create_payment(self):
        """overdue_payment alert → tạo SC Payment Entry draft trỏ tới PI."""
        if self.alert_type != "overdue_payment":
            frappe.throw(_("Action chỉ áp dụng cho alert overdue_payment"),
                          title="SC-E-ALERT-ACTION")
        if self.action_taken:
            frappe.throw(_("Alert này đã có action: {0} {1}").format(
                self.action_doctype, self.action_name),
                title="SC-E-ALERT-ACTION")
        if self.reference_doctype != "SC Purchase Invoice" or not self.reference_name:
            frappe.throw(_("Alert thiếu reference SC Purchase Invoice"),
                          title="SC-E-ALERT-ACTION")

        pi = frappe.get_doc("SC Purchase Invoice", self.reference_name)

        pe = frappe.new_doc("SC Payment Entry")
        pe.payment_date = today()
        pe.supplier = pi.supplier
        pe.amount = flt(pi.outstanding_amount)
        pe.payment_method = "Bank Transfer"
        pe.remarks = f"Auto từ Alert {self.name}: thanh toán PI {pi.name} quá hạn"
        pe.append("references", {
            "purchase_invoice": pi.name,
            "allocated_amount": flt(pi.outstanding_amount),
        })
        pe.flags.ignore_permissions = True
        pe.insert()

        self._mark_action("SC Payment Entry", pe.name)
        return pe.name

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _mark_action(self, doctype: str, name: str):
        """Set action fields + auto-resolve alert."""
        self.db_set({
            "action_taken": 1,
            "action_doctype": doctype,
            "action_name": name,
            "resolved": 1,
            "resolution_action": "Acted Upon",
            "resolved_by": frappe.session.user
                if frappe.session.user not in (None, "", "Guest") else "Administrator",
            "resolved_at": now(),
        })

    def _get_quarantine_warehouse(self) -> str:
        wh = frappe.db.get_value("SC Warehouse",
                                   {"disabled": 0, "warehouse_type": "Quarantine"}, "name")
        if wh:
            return wh
        if frappe.db.exists("SC Warehouse", DEFAULT_QUARANTINE_WAREHOUSE):
            return DEFAULT_QUARANTINE_WAREHOUSE
        frappe.throw(_("Không có Kho Quarantine nào configured"),
                      title="SC-E-NO-QUARANTINE")

    def _get_avg_valuation(self, batch: str, warehouse: str) -> float:
        """Lấy valuation_rate trung bình từ SLE."""
        v = frappe.db.sql("""
            SELECT AVG(valuation_rate) FROM `tabSC Stock Ledger Entry`
            WHERE batch = %s AND warehouse = %s
              AND is_cancelled = 0 AND qty_change > 0
        """, (batch, warehouse))[0][0]
        return flt(v or 0)
