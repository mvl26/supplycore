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

    # ==================================================================
    # UC-34 step 5: mark resolved + ghi chú
    # ==================================================================
    @frappe.whitelist()
    def mark_resolved(self, action: str = "Acknowledged", remarks: str = None):
        """Đánh dấu alert đã xử lý kèm ghi chú hành động."""
        if self.resolved:
            frappe.throw(_("SC-E-ALERT-RESOLVED: Alert đã được xử lý"))
        if action not in ("Acknowledged", "Acted Upon", "Dismissed", "Escalated"):
            action = "Acknowledged"
        new_remarks = self.remarks or ""
        if remarks:
            new_remarks = (new_remarks + f"\n[{now()}] {remarks}").strip()
        self.db_set({
            "resolved": 1,
            "resolution_action": action,
            "resolved_by": frappe.session.user
                if frappe.session.user not in (None, "", "Guest") else "Administrator",
            "resolved_at": now(),
            "remarks": new_remarks,
        })
        return {"resolved": True, "resolution_action": action}

    # ==================================================================
    # UC-34 5a: snooze với lý do
    # ==================================================================
    @frappe.whitelist()
    def snooze_alert(self, hours, reason: str = None):
        """Tạm ẩn alert X giờ kèm lý do."""
        if self.resolved:
            frappe.throw(_("SC-E-ALERT-RESOLVED: Không thể snooze alert đã resolved"))
        try:
            hrs = int(hours)
        except (TypeError, ValueError):
            hrs = 0
        if hrs <= 0:
            frappe.throw(_("SC-E-ALERT-SNOOZE-HOURS: hours phải > 0"))
        snooze_until = frappe.utils.add_to_date(now(), hours=hrs)
        self.db_set({
            "snooze_until": snooze_until,
            "snooze_reason": (reason or "(không lý do)")[:280],
        })
        return {"snooze_until": str(snooze_until), "hours": hrs}

    # ==================================================================
    # UC-34 4a: assign cho user khác
    # ==================================================================
    @frappe.whitelist()
    def assign_alert(self, user: str, note: str = None):
        if not user or not frappe.db.exists("User", user):
            frappe.throw(_(
                "SC-E-ALERT-NO-USER: User {0} không tồn tại"
            ).format(user))
        if self.resolved:
            frappe.throw(_("SC-E-ALERT-RESOLVED: Alert đã resolved"))
        self.db_set("assigned_to", user)
        # Tạo Frappe ToDo (built-in assignment)
        try:
            from frappe.desk.form.assign_to import add as _assign_add
            _assign_add({
                "assign_to": [user],
                "doctype": "SC Alert",
                "name": self.name,
                "description": f"Alert {self.title}\n{note or ''}",
            })
        except Exception:
            pass
        return {"assigned_to": user}

    # ==================================================================
    # UC-34 step 4 actions
    # ==================================================================
    @frappe.whitelist()
    def action_create_purchase_order(self):
        """Tạo SC Purchase Order draft khi alert là low_stock có MR linked."""
        if self.alert_type != "low_stock":
            frappe.throw(_("Action chỉ áp dụng cho low_stock"))
        if self.action_taken and self.action_doctype != "SC Material Request":
            frappe.throw(_("Alert đã có action: {0} {1}").format(
                self.action_doctype, self.action_name))
        if self.action_doctype == "SC Material Request" and self.action_name:
            mr_name = self.action_name
        else:
            # No MR yet - cần tạo MR trước
            frappe.throw(_(
                "Trước tiên gọi action_create_material_request để có MR, "
                "sau đó tạo PO từ MR đó"
            ))
        mr = frappe.get_doc("SC Material Request", mr_name)
        # Find item supplier (best-effort)
        item_code = self.reference_name
        supplier = frappe.db.get_value("SC Item", item_code, "preferred_supplier") \
            or frappe.db.get_value("SC Supplier", {"disabled": 0}, "name")
        if not supplier:
            frappe.throw(_("Không có supplier để tạo PO"))
        po = frappe.new_doc("SC Purchase Order")
        po.supplier = supplier
        po.transaction_date = today()
        po.schedule_date = add_days(today(), 7)
        for r in mr.items:
            po.append("items", {
                "item": r.item, "uom": r.uom,
                "qty": flt(r.qty),
                "rate": 0,
                "warehouse": mr.warehouse,
                "schedule_date": r.schedule_date or add_days(today(), 7),
            })
        po.remarks = f"Auto từ Alert {self.name}: tạo PO từ MR {mr.name}"
        po.flags.ignore_permissions = True
        po.insert()
        # Update action link to PO
        self.db_set({
            "action_taken": 1,
            "action_doctype": "SC Purchase Order",
            "action_name": po.name,
            "resolved": 1,
            "resolution_action": "Acted Upon",
            "resolved_by": frappe.session.user
                if frappe.session.user not in (None, "", "Guest") else "Administrator",
            "resolved_at": now(),
        })
        return {"po": po.name, "url": f"/app/sc-purchase-order/{po.name}"}

    @frappe.whitelist()
    def action_priority_dispense(self, note: str = None):
        """expiring_batch → đánh dấu batch cần ưu tiên cấp phát.
        Hiện tại: ghi vào remarks + resolution_action=Acted Upon.
        Future: set batch.priority_pickup=1 khi field tồn tại."""
        if self.alert_type != "expiring_batch":
            frappe.throw(_("Action chỉ áp dụng cho expiring_batch"))
        if self.resolved:
            frappe.throw(_("SC-E-ALERT-RESOLVED"))
        remark = f"Đã đánh dấu ưu tiên cấp phát batch {self.reference_name}"
        if note:
            remark += f": {note}"
        new_remarks = (self.remarks or "") + f"\n[{now()}] {remark}"
        self.db_set({
            "remarks": new_remarks.strip(),
            "resolved": 1,
            "resolution_action": "Acted Upon",
            "resolved_by": frappe.session.user
                if frappe.session.user not in (None, "", "Guest") else "Administrator",
            "resolved_at": now(),
        })
        return {"batch": self.reference_name, "priority": True}

    @frappe.whitelist()
    def action_contact_supplier(self, message: str = None):
        """Gửi email contact tới supplier liên quan."""
        # Resolve supplier theo reference type
        supplier = None
        if self.reference_doctype == "SC Batch":
            supplier = frappe.db.get_value("SC Batch", self.reference_name, "supplier")
        elif self.reference_doctype == "SC Purchase Receipt":
            supplier = frappe.db.get_value("SC Purchase Receipt", self.reference_name, "supplier")
        elif self.reference_doctype == "SC Purchase Invoice":
            supplier = frappe.db.get_value("SC Purchase Invoice", self.reference_name, "supplier")
        elif self.reference_doctype == "Framework Contract":
            supplier = frappe.db.get_value("Framework Contract", self.reference_name, "supplier")
        if not supplier:
            frappe.throw(_(
                "Không xác định được NCC từ reference {0} {1}"
            ).format(self.reference_doctype, self.reference_name))
        supplier_email = frappe.db.get_value("SC Supplier", supplier, "email_id")
        if not supplier_email:
            frappe.throw(_("NCC {0} không có email").format(supplier))
        try:
            frappe.sendmail(
                recipients=[supplier_email],
                subject=f"[SupplyCore] {self.title}",
                message=(
                    f"<p>Kính gửi {supplier},</p>"
                    f"<p>{message or self.message or self.title}</p>"
                    f"<p>Reference: {self.reference_doctype} {self.reference_name}</p>"
                    f"<p>Vui lòng phản hồi sớm.</p>"
                ),
                queue=True, now=False,
            )
        except Exception as e:
            frappe.log_error(message=str(e)[:1000],
                              title=f"UC-34 contact_supplier {self.name}")
        new_remarks = (self.remarks or "") + (
            f"\n[{now()}] Đã gửi email cho NCC {supplier} ({supplier_email})"
        )
        self.db_set("remarks", new_remarks.strip())
        return {"supplier": supplier, "email": supplier_email}

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
