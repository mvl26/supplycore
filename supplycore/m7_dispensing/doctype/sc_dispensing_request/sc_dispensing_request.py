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
        """Tạo SC Stock Entry Material Issue từ DR Approved."""
        if self.docstatus != 1:
            frappe.throw(_("DR phải submit trước"))
        if self.stock_entry:
            frappe.throw(_("DR đã có Stock Entry: {0}").format(self.stock_entry))
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
        return se.name

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
