"""SC Dispensing Request — yêu cầu cấp phát từ khoa (M7, UC-20)."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, today


class SCDispensingRequest(Document):

    def validate(self):
        if self.purpose == "Patient-Specific" and not self.patient:
            frappe.throw(_("Mục đích Patient-Specific phải gắn bệnh nhân"))
        for r in self.items:
            if not r.approved_qty:
                r.approved_qty = r.requested_qty
        self.total_qty = sum(flt(r.requested_qty) for r in self.items)
        self._compute_estimated_value()
        if not self.requested_by and frappe.session.user not in (None, "", "Guest"):
            self.requested_by = frappe.session.user
        if self.docstatus == 0:
            self.status = "Draft"

    def before_submit(self):
        # UC-20 ngoại lệ: quota check
        self._validate_quota()
        # BUG-009: chặn approved_qty vượt tồn khả dụng tại thời điểm duyệt
        self._validate_approved_qty_vs_stock()

    def _validate_approved_qty_vs_stock(self):
        """BUG-009: Khi DR submit (approve), kiểm tra approved_qty <= tồn khả
        dụng tại from_warehouse (loại Pending/Rejected QC + blocked batch).
        Cộng dồn theo item nếu nhiều dòng.
        """
        if not self.from_warehouse:
            return
        from supplycore.supplycore.doctype.sc_stock_ledger_entry.sc_stock_ledger_entry import SCStockLedgerEntry
        demand = {}
        for r in self.items:
            qty = flt(r.approved_qty) or flt(r.requested_qty)
            if not (r.item and qty):
                continue
            demand[r.item] = demand.get(r.item, 0) + qty
        for item, need in demand.items():
            avail = SCStockLedgerEntry.get_available_qty(item, self.from_warehouse)
            if need > avail:
                frappe.throw(_(
                    "Không đủ tồn khả dụng cho {0} tại kho {1}: "
                    "duyệt {2}, còn {3} (loại trừ QC Pending/Rejected/Blocked). "
                    "Giảm SL DUYỆT hoặc tạo Stock Reconciliation."
                ).format(item, self.from_warehouse, need, avail),
                    title="SC-E010 NEGATIVE_STOCK")

    def on_submit(self):
        self.db_set("status", "Approved")

    def _compute_estimated_value(self):
        total = 0
        for r in self.items:
            rate = _last_purchase_rate(r.item)
            if not rate:
                # Fallback: SLE valuation_rate gần nhất (Material Receipt)
                rate_row = frappe.db.sql("""
                    SELECT valuation_rate FROM `tabSC Stock Ledger Entry`
                    WHERE item = %s AND valuation_rate > 0 AND is_cancelled = 0
                    ORDER BY posting_date DESC, creation DESC LIMIT 1
                """, r.item)
                rate = flt(rate_row[0][0]) if rate_row else 0
            total += flt(r.approved_qty or r.requested_qty) * rate
        self.total_estimated_value = total

    def _validate_quota(self):
        if not self.department:
            return
        quota = flt(frappe.db.get_value(
            "SC Department", self.department, "monthly_dispensing_quota"))
        if quota <= 0:
            return
        if self.quota_override_acknowledged:
            return
        from frappe.utils import get_first_day, get_last_day
        month_start = get_first_day(self.request_date or today())
        month_end = get_last_day(self.request_date or today())
        consumed = flt(frappe.db.sql("""
            SELECT COALESCE(SUM(total_estimated_value), 0)
            FROM `tabSC Dispensing Request`
            WHERE department = %s
              AND request_date BETWEEN %s AND %s
              AND docstatus = 1
              AND status != 'Cancelled'
              AND name != %s
        """, (self.department, month_start, month_end, self.name or ""))[0][0])
        projected = consumed + flt(self.total_estimated_value)
        if projected > quota:
            frappe.throw(_(
                "SC-E-DR-QUOTA-EXCEEDED: Khoa {0} vượt hạn mức cấp phát tháng "
                "(đã dùng {1}, DR này {2}, quota {3}). "
                "Cần Manager tick 'Xác nhận vượt hạn mức' để submit."
            ).format(
                self.department,
                frappe.format(consumed, {"fieldtype": "Currency"}),
                frappe.format(self.total_estimated_value, {"fieldtype": "Currency"}),
                frappe.format(quota, {"fieldtype": "Currency"}),
            ))

    def on_cancel(self):
        self.db_set("status", "Cancelled")

    @frappe.whitelist()
    def make_stock_entry(self):
        """Tạo SC Stock Entry Material Issue từ DR Approved (UC-21)."""
        if self.docstatus != 1:
            frappe.throw(_("DR phải submit trước"))
        if self.stock_entry:
            frappe.throw(_("DR đã có Stock Entry: {0}").format(self.stock_entry))

        # UC-21 ngoại lệ: block khi tồn hệ thống ≠ thực
        check = self.check_stock_match_for_dr()
        if check["mismatches"]:
            details = ", ".join(
                f"{m['item']} (deficit {m['deficit']:.1f})"
                for m in check["mismatches"][:3]
            )
            frappe.throw(_(
                "SC-E-DR-STOCK-MISMATCH: Tồn kho hệ thống không khớp ({0}). "
                "Tạo SC Stock Reconciliation trước khi cấp phát."
            ).format(details))

        valid = [r for r in self.items if flt(r.approved_qty) > 0]
        if not valid:
            frappe.throw(_("Không có item nào có approved_qty > 0"))

        se = frappe.new_doc("SC Stock Entry")
        se.entry_type = "Material Issue"
        se.posting_date = today()
        se.from_warehouse = self.from_warehouse
        se.purpose = f"Dispensing Request {self.name}"
        for row in valid:
            se.append("items", {
                "item": row.item, "qty": flt(row.approved_qty),
                "uom": row.uom, "batch": row.batch,
                "valuation_rate": _last_purchase_rate(row.item),
            })
        se.flags.ignore_permissions = True
        se.insert()
        self.db_set("stock_entry", se.name)
        self.db_set("status", "Issued")
        self._notify_department()
        return se.name

    @frappe.whitelist()
    def auto_pick_fefo_for_dr(self):
        """UC-21 step 3: auto-fill batch theo FEFO + adjust approved_qty."""
        from supplycore.api.fefo import get_suggested_batches
        if self.docstatus != 0:
            frappe.throw(_("Chỉ auto-pick khi DR ở Draft"))
        if not self.from_warehouse:
            frappe.throw(_("Chọn from_warehouse trước"))

        picked = []
        for r in self.items:
            res = get_suggested_batches(r.item, self.from_warehouse, flt(r.requested_qty))
            if res["batches"]:
                first = res["batches"][0]
                r.batch = first["batch_no"]
                r.approved_qty = flt(first["suggested_qty"])
                if res["shortfall"] > 0:
                    r.shortage_note = (
                        f"Thiếu {res['shortfall']:.1f} so với yêu cầu — "
                        f"chỉ cấp {r.approved_qty:.1f}"
                    )
                picked.append({"item": r.item, "batch": r.batch,
                                "approved_qty": flt(r.approved_qty)})
            else:
                r.shortage_note = "Không có batch khả dụng (hết hàng / hết hạn / blocked)"
                r.approved_qty = 0
        self.save(ignore_permissions=False)
        return {"picked": picked, "rows": len(self.items)}

    @frappe.whitelist()
    def check_stock_match_for_dr(self):
        """UC-21 ngoại lệ: phát hiện tồn hệ thống ≠ thực tế."""
        mismatches = []
        for r in self.items:
            if not (r.item and self.from_warehouse):
                continue
            if flt(r.approved_qty) <= 0:
                continue
            params = {"item": r.item, "wh": self.from_warehouse}
            cond = ""
            if r.batch:
                cond = "AND batch = %(batch)s"
                params["batch"] = r.batch
            sql = f"""
                SELECT COALESCE(SUM(qty_change), 0)
                FROM `tabSC Stock Ledger Entry`
                WHERE item = %(item)s AND warehouse = %(wh)s AND is_cancelled = 0
                  {cond}
            """
            actual = flt(frappe.db.sql(sql, params)[0][0])
            if flt(r.approved_qty) > actual:
                mismatches.append({
                    "row_idx": r.idx, "item": r.item, "batch": r.batch,
                    "approved_qty": flt(r.approved_qty),
                    "actual_qty": actual,
                    "deficit": flt(r.approved_qty) - actual,
                })
        return {"mismatches": mismatches, "ok": len(mismatches) == 0}

    @frappe.whitelist()
    def get_dispensing_slip_data(self):
        """UC-21 step 6: data in phiếu cấp phát có barcode."""
        return {
            "name": self.name,
            "barcode": self.name,
            "request_date": str(self.request_date) if self.request_date else "",
            "department": self.department,
            "from_warehouse": self.from_warehouse,
            "patient": self.patient,
            "requested_by": self.requested_by,
            "purpose": self.purpose,
            "items": [{
                "item": r.item, "item_name": r.item_name, "uom": r.uom,
                "requested_qty": flt(r.requested_qty),
                "approved_qty": flt(r.approved_qty),
                "batch": r.batch,
                "shortage_note": r.shortage_note,
            } for r in self.items],
            "stock_entry": self.stock_entry,
            "status": self.status,
            "url": f"/app/sc-dispensing-request/{self.name}",
        }

    def _notify_department(self):
        """UC-21 step 8: email department head khi DR Issued."""
        if not self.department:
            return
        head = frappe.db.get_value("SC Department", self.department, "head_user")
        if not head:
            return
        email = frappe.db.get_value("User", head, "email")
        if not email:
            return
        try:
            frappe.sendmail(
                recipients=[email],
                subject=f"[SupplyCore] DR {self.name} — vật tư sẵn sàng",
                message=(f"<p>Phiếu cấp phát <b>{self.name}</b> đã được xử lý.</p>"
                         f"<p>Stock Entry: {self.stock_entry}</p>"
                         f"<p>Khoa: {self.department}</p>"
                         f"<p><a href='/app/sc-dispensing-request/{self.name}'>Mở phiếu</a></p>"),
                delayed=True,
            )
        except Exception as e:
            frappe.log_error(message=str(e)[:1000], title="UC-21 _notify_department")

    @frappe.whitelist()
    def make_patient_dispensing(self):
        """Tạo SC Patient Dispensing draft (chỉ khi purpose=Patient-Specific)."""
        if self.purpose != "Patient-Specific" or not self.patient:
            frappe.throw(_("Chỉ áp dụng cho DR Patient-Specific gắn bệnh nhân"))
        if self.patient_dispensing:
            frappe.throw(_("DR đã có Patient Dispensing: {0}").format(self.patient_dispensing))
        if not self.stock_entry:
            frappe.throw(_("Tạo Stock Entry trước"))

        pd = frappe.new_doc("SC Patient Dispensing")
        pd.patient = self.patient
        pd.dispensing_date = today()
        pd.dispensing_request = self.name
        pd.stock_entry = self.stock_entry
        pd.ward = self.department
        for row in self.items:
            if flt(row.approved_qty) <= 0:
                continue
            pd.append("items", {
                "item": row.item,
                "qty": flt(row.approved_qty),
                "uom": row.uom,
                "batch": row.batch,
                "unit_cost": _last_purchase_rate(row.item),
            })
        pd.flags.ignore_permissions = True
        pd.insert()
        self.db_set("patient_dispensing", pd.name)
        self.db_set("status", "Dispensed")
        return pd.name


def _last_purchase_rate(item_code) -> float:
    rate = frappe.db.sql("""
        SELECT poi.rate
        FROM `tabSC Purchase Order Item` poi
        JOIN `tabSC Purchase Order` po ON po.name = poi.parent
        WHERE poi.item = %s AND po.docstatus = 1
        ORDER BY po.transaction_date DESC LIMIT 1
    """, item_code)
    return flt(rate[0][0]) if rate else 0
