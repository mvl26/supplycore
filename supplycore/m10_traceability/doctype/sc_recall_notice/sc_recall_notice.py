"""SC Recall Notice — quy trình thu hồi lô vật tư (M10, UC-30)."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, now


class SCRecallNotice(Document):

    def validate(self):
        # batch + item phải khớp
        batch_item = frappe.db.get_value("SC Batch", self.batch_no, "item")
        if batch_item and batch_item != self.item:
            frappe.throw(_("Item {0} không khớp item của batch {1} ({2})")
                         .format(self.item, self.batch_no, batch_item))
        self._compute_summary()
        if self.docstatus == 0:
            self.status = "Draft"

    def on_submit(self):
        # Block batch — đẩy thông tin sang SC Batch
        frappe.db.set_value("SC Batch", self.batch_no, {
            "blocked": 1,
            "block_reason": f"Recall {self.name}: {self.recall_reason or ''}",
            "blocked_by": frappe.session.user
                if frappe.session.user not in (None, "", "Guest") else "Administrator",
            "blocked_at": now(),
        })
        self.db_set("status", "Issued")
        self.db_set("approved_by", frappe.session.user
            if frappe.session.user not in (None, "", "Guest") else "Administrator")
        self.db_set("approved_at", now())

    def on_cancel(self):
        # Unblock batch
        frappe.db.set_value("SC Batch", self.batch_no, {
            "blocked": 0,
            "block_reason": None,
        })
        self.db_set("status", "Cancelled")

    # ------------------------------------------------------------------
    def _compute_summary(self):
        recovered = sum(flt(r.recovered_qty) for r in self.affected_items)
        destroyed = sum(flt(r.destroyed_qty) for r in self.affected_items)
        # Compute outstanding per row + total
        total_affected = 0
        outstanding = 0
        for r in self.affected_items:
            r.outstanding_qty = flt(r.qty_dispensed) - flt(r.recovered_qty or 0) - flt(r.destroyed_qty or 0)
            total_affected += flt(r.qty_dispensed)
            outstanding += flt(r.outstanding_qty)
        self.total_affected_qty = total_affected
        self.recovered_qty = recovered
        self.destroyed_qty = destroyed
        self.outstanding_qty = outstanding
        if total_affected > 0:
            self.recall_resolution_pct = round((recovered + destroyed) / total_affected * 100, 2)
        else:
            self.recall_resolution_pct = 0

        # Auto status nếu fully resolved
        if self.docstatus == 1 and outstanding <= 0.01 and total_affected > 0:
            self.status = "Completed"
        elif self.docstatus == 1 and (recovered + destroyed) > 0:
            self.status = "In Progress"

    # ------------------------------------------------------------------
    @frappe.whitelist()
    def populate_affected_items(self):
        """Auto-load affected items từ batch trace.

        Query SC SLE để tìm tất cả vị trí batch đã đến:
          - Còn ở warehouse → tồn kho hiện tại
          - Đã cấp phát qua SC Patient Dispensing → BN-specific
          - Đã chuyển qua SC Stock Entry Material Transfer → khoa khác
        """
        if self.docstatus != 0:
            frappe.throw(_("Chỉ populate khi Draft"))
        if not self.batch_no:
            frappe.throw(_("Chọn batch trước"))

        self.affected_items = []

        # 1. Tồn kho hiện tại theo warehouse
        wh_qty = frappe.db.sql("""
            SELECT warehouse, SUM(qty_change) AS qty
            FROM `tabSC Stock Ledger Entry`
            WHERE batch = %s AND is_cancelled = 0
            GROUP BY warehouse
            HAVING qty > 0
        """, self.batch_no, as_dict=True)
        for row in wh_qty:
            self.append("affected_items", {
                "location_type": "Warehouse",
                "warehouse": row.warehouse,
                "voucher_type": "Stock Balance",
                "voucher_no": "—",
                "qty_dispensed": flt(row.qty),
                "recovered_qty": 0,
                "status": "Notified",
            })

        # 2. Đã cấp phát cho BN qua SC Patient Dispensing
        patient_dispensings = frappe.db.sql("""
            SELECT pd.name AS pd_name, pd.patient, pd.dispensing_date,
                   pd.ward, pdi.qty
            FROM `tabSC PD Item` pdi
            JOIN `tabSC Patient Dispensing` pd ON pd.name = pdi.parent
            WHERE pdi.batch = %s AND pd.docstatus = 1
        """, self.batch_no, as_dict=True)
        for pd in patient_dispensings:
            self.append("affected_items", {
                "location_type": "Patient",
                "patient": pd.patient,
                "department": pd.ward,
                "voucher_type": "SC Patient Dispensing",
                "voucher_no": pd.pd_name,
                "voucher_date": pd.dispensing_date,
                "qty_dispensed": flt(pd.qty),
                "recovered_qty": 0,
                "status": "Notified",
            })

        self._compute_summary()
        self.save(ignore_permissions=True)
        return {"affected_items_loaded": len(self.affected_items)}
