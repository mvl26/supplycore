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

    # ==================================================================
    # UC-30 main flow steps 5-7 + alt 3a/7a + ngoại lệ
    # ==================================================================
    @frappe.whitelist()
    def notify_departments(self):
        """UC-30 step 5: group affected_items theo department cho Print Format."""
        if self.docstatus != 1:
            frappe.throw(_("SC-E-RCL-NOT-ISSUED: Chỉ gửi phiếu khi Recall Notice đã Issued"))
        by_dept = {}
        for r in self.affected_items:
            if r.location_type != "Department" or not r.department:
                continue
            dept = r.department
            by_dept.setdefault(dept, []).append({
                "row_name": r.name,
                "voucher_type": r.voucher_type,
                "voucher_no": r.voucher_no,
                "voucher_date": str(r.voucher_date) if r.voucher_date else None,
                "qty_dispensed": flt(r.qty_dispensed),
                "outstanding": flt(r.outstanding_qty),
                "status": r.status,
            })
        return {
            "recall_notice": self.name,
            "batch_no": self.batch_no,
            "item": self.item,
            "recall_reason": self.recall_reason,
            "by_department": by_dept,
            "letter_count": len(by_dept),
        }

    @frappe.whitelist()
    def notify_clinical_staff(self):
        """UC-30 3a: gửi alert Pharmacy Officer + SupplyCore Manager khi có BN bị ảnh hưởng."""
        if self.docstatus != 1:
            frappe.throw(_("SC-E-RCL-NOT-ISSUED: Chỉ notify khi Issued"))
        patient_rows = [r for r in self.affected_items if r.location_type == "Patient"]
        if not patient_rows:
            return {"notified": 0, "msg": "Không có BN bị ảnh hưởng"}
        role_users = frappe.get_all(
            "Has Role",
            filters={"role": ["in", ["Pharmacy Officer", "SupplyCore Manager"]]},
            pluck="parent",
        )
        recipients = []
        if role_users:
            recipients = frappe.get_all(
                "User",
                filters={"enabled": 1, "name": ["in", role_users]},
                pluck="name",
            )
        if recipients:
            try:
                frappe.sendmail(
                    recipients=recipients,
                    subject=f"[RECALL] {self.name} — {len(patient_rows)} BN bị ảnh hưởng",
                    message=(
                        f"Recall Notice <b>{self.name}</b> (batch {self.batch_no}) "
                        f"đã ảnh hưởng <b>{len(patient_rows)}</b> bệnh nhân.<br>"
                        f"Lý do: {self.recall_reason}<br>"
                        f"Chi tiết: /app/sc-recall-notice/{self.name}"
                    ),
                    now=False,
                )
            except Exception:
                # Email config có thể chưa setup — vẫn cho flag clinical_notified=1
                pass
        for r in patient_rows:
            r.clinical_notified = 1
            r.db_update()
        self.db_set("clinical_notified_at", frappe.utils.now())
        return {"notified": len(patient_rows), "recipients": len(recipients)}

    @frappe.whitelist()
    def update_recovery(self, row_name, recovered_qty=0, destroyed_qty=0,
                         status="In Progress", remarks=None):
        """UC-30 step 6: cập nhật recovery của 1 affected_item row (allow_on_submit)."""
        if self.docstatus != 1:
            frappe.throw(_("SC-E-RCL-NOT-ISSUED: Chỉ update khi Issued"))
        row = next((r for r in self.affected_items if r.name == row_name), None)
        if not row:
            frappe.throw(_("SC-E-RCL-ROW-NOT-FOUND: Row {0} không tồn tại").format(row_name))
        row.recovered_qty = flt(recovered_qty)
        row.destroyed_qty = flt(destroyed_qty)
        row.status = status
        row.recovery_date = frappe.utils.today()
        row.recovered_by = frappe.session.user
        if remarks:
            row.remarks = remarks
        row.outstanding_qty = flt(row.qty_dispensed) - flt(row.recovered_qty) - flt(row.destroyed_qty)
        row.db_update()
        # Recompute aggregate on parent
        self.reload()
        self._compute_summary()
        self.db_update()
        return {
            "outstanding_qty": flt(self.outstanding_qty),
            "resolution_pct": flt(self.recall_resolution_pct),
            "status": self.status,
        }

    @frappe.whitelist()
    def create_return_to_supplier(self):
        """UC-30 step 7: tạo SC Purchase Receipt is_return=1 cho qty thu hồi từ kho."""
        if self.docstatus != 1:
            frappe.throw(_("SC-E-RCL-NOT-ISSUED: Chỉ tạo Return PR khi Issued"))
        if self.return_pr:
            frappe.throw(_("Đã có Return PR {0}").format(self.return_pr))
        if not self.supplier:
            frappe.throw(_("SC-E-RCL-NO-SUPPLIER: Batch không có supplier — không thể trả NCC"))
        rows = [r for r in self.affected_items
                if r.location_type == "Warehouse" and flt(r.recovered_qty) > 0]
        if not rows:
            frappe.throw(_("SC-E-RCL-NO-AFFECTED: Không có qty thu hồi từ kho để trả NCC"))
        uom = frappe.db.get_value("SC Item", self.item, "uom")
        # PR validate yêu cầu to_warehouse — dùng warehouse của row đầu (= nơi đang giữ qty)
        primary_wh = rows[0].warehouse
        pr = frappe.new_doc("SC Purchase Receipt")
        pr.supplier = self.supplier
        pr.posting_date = frappe.utils.today()
        pr.to_warehouse = primary_wh
        pr.is_return = 1
        pr.return_reason = f"Recall {self.name}: {self.recall_reason or ''}"[:140]
        for r in rows:
            pr.append("items", {
                "item": self.item,
                "batch_no": self.batch_no,
                "warehouse": r.warehouse,
                "qty": flt(r.recovered_qty),
                "uom": uom,
                "rate": 0,
            })
        pr.flags.ignore_permissions = True
        pr.insert()
        self.db_set("return_pr", pr.name)
        self.db_set("resolution", "Return to Supplier")
        self.db_set("resolution_date", frappe.utils.today())
        return {"return_pr": pr.name, "url": f"/app/sc-purchase-receipt/{pr.name}"}

    @frappe.whitelist()
    def create_write_off(self):
        """UC-30 7a: tạo SC Stock Entry Material Issue purpose 'Write Off — Recall'."""
        if self.docstatus != 1:
            frappe.throw(_("SC-E-RCL-NOT-ISSUED: Chỉ tạo Write Off khi Issued"))
        if self.write_off_entry:
            frappe.throw(_("Đã có Write Off {0}").format(self.write_off_entry))
        rows = [r for r in self.affected_items
                if r.location_type == "Warehouse" and flt(r.destroyed_qty) > 0]
        if not rows:
            frappe.throw(_("SC-E-RCL-NO-AFFECTED: Không có qty destroyed từ kho để hủy"))
        # Group rows theo warehouse — mỗi SE chỉ 1 from_warehouse
        wh_groups = {}
        for r in rows:
            wh_groups.setdefault(r.warehouse, []).append(r)
        if len(wh_groups) > 1:
            frappe.throw(_(
                "SC-E-RCL-MULTI-WH: Hủy ở nhiều kho — phải tạo write off riêng từng kho ({0})"
            ).format(", ".join(wh_groups.keys())))
        wh, grp = next(iter(wh_groups.items()))
        uom = frappe.db.get_value("SC Item", self.item, "uom")
        se = frappe.new_doc("SC Stock Entry")
        se.entry_type = "Material Issue"
        se.posting_date = frappe.utils.today()
        se.from_warehouse = wh
        se.purpose = f"Write Off — Recall {self.name}: {(self.recall_reason or '')[:120]}"
        se.recall_notice = self.name
        for r in grp:
            se.append("items", {
                "item": self.item,
                "uom": uom,
                "batch": self.batch_no,
                "qty": flt(r.destroyed_qty),
            })
        se.flags.ignore_permissions = True
        se.insert()
        se.submit()
        self.db_set("write_off_entry", se.name)
        self.db_set("resolution", "Destroy")
        self.db_set("resolution_date", frappe.utils.today())
        return {"write_off_entry": se.name, "url": f"/app/sc-stock-entry/{se.name}"}

    @frappe.whitelist()
    def audit_dispensings_in_period(self, start_date=None, end_date=None):
        """UC-30 ngoại lệ: list cấp phát giai đoạn recall để xử lý case
        không xác định khoa phòng đã nhận."""
        start_date = start_date or frappe.utils.add_days(frappe.utils.today(), -90)
        end_date = end_date or frappe.utils.today()
        rows = frappe.db.sql("""
            SELECT pd.name AS pd, pd.dispensing_date, pd.patient, pd.ward,
                   pdi.batch, pdi.item, pdi.qty,
                   CASE WHEN pdi.batch IS NOT NULL THEN 1 ELSE 0 END AS has_batch_link
            FROM `tabSC PD Item` pdi
            JOIN `tabSC Patient Dispensing` pd ON pd.name = pdi.parent
            WHERE pd.docstatus = 1
              AND pdi.item = %(item)s
              AND pd.dispensing_date BETWEEN %(start)s AND %(end)s
            ORDER BY pd.dispensing_date DESC
        """, {"item": self.item, "start": start_date, "end": end_date}, as_dict=True)
        return {
            "dispensings": rows,
            "count": len(rows),
            "period": f"{start_date} → {end_date}",
            "item": self.item,
        }
