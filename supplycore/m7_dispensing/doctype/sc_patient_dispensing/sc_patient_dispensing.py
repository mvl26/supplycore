"""SC Patient Dispensing — UC-22 ghi nhận sử dụng VT cho BN + BHYT calc."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class SCPatientDispensing(Document):

    def validate(self):
        self._enforce_no_blocked_batch()
        self._enforce_no_negative_stock()
        self._calculate_bhyt()
        self._compute_totals()

    def _enforce_no_blocked_batch(self):
        """UC-30 step 4: PD không được dùng batch đang bị recall (blocked)."""
        for row in self.items:
            if not row.batch:
                continue
            b = frappe.db.get_value("SC Batch", row.batch,
                                     ["blocked", "block_reason"], as_dict=True)
            if b and b.blocked:
                frappe.throw(_(
                    "SC-E-RCL-BATCH-RECALLED: Batch {0} đang bị recall/block — {1}. "
                    "Không thể cấp phát cho BN."
                ).format(row.batch, b.block_reason or ""))

    def _enforce_no_negative_stock(self):
        """BUG-001: Chặn cấp phát vượt tồn khả dụng (loại QC Pending/Rejected)."""
        if self.docstatus != 0:
            return
        from supplycore.supplycore.doctype.sc_stock_ledger_entry.sc_stock_ledger_entry import SCStockLedgerEntry
        demand = {}
        for r in self.items:
            if not (r.item and r.qty and r.warehouse):
                continue
            key = (r.item, r.warehouse, r.batch or None)
            demand[key] = demand.get(key, 0) + flt(r.qty)
        for (item, warehouse, batch), need in demand.items():
            avail = SCStockLedgerEntry.get_available_qty(item, warehouse, batch)
            if need > avail:
                batch_label = f" lô {batch}" if batch else ""
                frappe.throw(_(
                    "Không đủ tồn khả dụng cho {0}{1} tại kho {2}: "
                    "cần {3}, còn {4} (loại trừ QC Pending/Rejected/Blocked)."
                ).format(item, batch_label, warehouse, need, avail),
                    title="SC-E010 NEGATIVE_STOCK")

    def on_submit(self):
        self._post_stock_ledger()
        if self.dispensing_request and frappe.db.exists("SC Dispensing Request", self.dispensing_request):
            frappe.db.set_value("SC Dispensing Request", self.dispensing_request,
                                 "status", "Dispensed")

    def on_cancel(self):
        self._reverse_stock_ledger()

    def _post_stock_ledger(self):
        """UC-22: PD submit → SLE âm để giảm tồn kho per item+batch+warehouse."""
        from supplycore.supplycore.doctype.sc_stock_ledger_entry.sc_stock_ledger_entry import SCStockLedgerEntry
        for r in self.items:
            if not (r.item and r.qty and r.warehouse):
                continue
            SCStockLedgerEntry.post(
                item=r.item, warehouse=r.warehouse,
                qty_change=-flt(r.qty),
                valuation_rate=flt(r.unit_cost),
                voucher_type="SC Patient Dispensing",
                voucher_no=self.name, voucher_detail_no=r.name,
                batch=r.batch,
                posting_date=self.dispensing_date,
                remarks=f"Cấp phát BN {self.patient}",
            )

    def _reverse_stock_ledger(self):
        """Cancel PD → post SLE đảo dấu."""
        from supplycore.supplycore.doctype.sc_stock_ledger_entry.sc_stock_ledger_entry import SCStockLedgerEntry
        sles = frappe.get_all("SC Stock Ledger Entry",
            filters={"voucher_type": "SC Patient Dispensing", "voucher_no": self.name,
                      "is_cancelled": 0},
            fields=["name", "item", "warehouse", "batch", "qty_change", "valuation_rate"])
        for s in sles:
            SCStockLedgerEntry.post(
                item=s.item, warehouse=s.warehouse,
                qty_change=-flt(s.qty_change),
                valuation_rate=flt(s.valuation_rate),
                voucher_type="SC Patient Dispensing", voucher_no=self.name,
                voucher_detail_no=s.name + "-CANCEL",
                batch=s.batch,
                remarks=f"Cancel PD {self.name}",
            )
            frappe.db.set_value("SC Stock Ledger Entry", s.name, "is_cancelled", 1)

    def _calculate_bhyt(self):
        """Per-row BHYT calc với UC-22 luồng 2a + ngoại lệ config thay đổi."""
        from supplycore.api.bhyt import get_active_config

        patient_rate = flt(self.bhyt_payment_rate) if self.bhyt_payment_rate else None
        no_bhyt_card = not (self.bhyt_card_no and str(self.bhyt_card_no).strip())

        any_config_changed = False

        for row in self.items:
            row.total_cost = flt(row.qty) * flt(row.unit_cost)

            # UC-22 2a: BN không thẻ BHYT → tự trả 100%
            if no_bhyt_card:
                row.bhyt_code = None
                row.bhyt_group = None
                row.bhyt_rate = 0
                row.ceiling_price = 0
                row.bhyt_amount = 0
                row.ceiling_overage = 0
                row.patient_pays = row.total_cost
                row.bhyt_config_changed = 0
                continue

            cfg = get_active_config(row.item, on_date=str(self.dispensing_date) if self.dispensing_date else None)
            if not cfg:
                # UC-22 3a: VT không có BHYT config → BN trả 100%
                row.bhyt_code = None
                row.bhyt_group = None
                row.bhyt_rate = 0
                row.ceiling_price = 0
                row.bhyt_amount = 0
                row.ceiling_overage = 0
                row.patient_pays = row.total_cost
                row.bhyt_config_changed = 0
                continue

            row.bhyt_code = cfg.get("bhyt_code")
            row.bhyt_group = cfg.get("bhyt_group")
            cfg_rate = flt(cfg.get("payment_rate") or 0)
            effective_rate = cfg_rate
            if patient_rate is not None and patient_rate < cfg_rate:
                effective_rate = patient_rate
            row.bhyt_rate = effective_rate

            ceiling = flt(cfg.get("ceiling_price") or 0)
            row.ceiling_price = ceiling
            cap_unit = flt(row.unit_cost)
            ceiling_overage = 0
            if ceiling and flt(row.unit_cost) > ceiling:
                cap_unit = ceiling
                ceiling_overage = flt(row.qty) * (flt(row.unit_cost) - ceiling)

            bhyt_eligible = flt(row.qty) * cap_unit
            bhyt_amount = bhyt_eligible * effective_rate / 100.0
            row.bhyt_amount = round(bhyt_amount, 2)
            row.ceiling_overage = round(ceiling_overage, 2)
            row.patient_pays = round(flt(row.total_cost) - bhyt_amount, 2)

            # UC-22 ngoại lệ: detect config change
            last = frappe.db.sql("""
                SELECT bhyt_rate, ceiling_price FROM `tabSC PD Item`
                WHERE item = %s AND parent != %s
                ORDER BY creation DESC LIMIT 1
            """, (row.item, self.name or ""), as_dict=True)
            row.bhyt_config_changed = 0
            if last:
                prev_rate = flt(last[0]["bhyt_rate"])
                prev_ceiling = flt(last[0]["ceiling_price"])
                if (prev_rate and prev_rate != cfg_rate) or \
                   (prev_ceiling and prev_ceiling != ceiling):
                    row.bhyt_config_changed = 1
                    any_config_changed = True

        # Warnings
        if no_bhyt_card and self.is_new():
            frappe.msgprint(
                _("⚠ BN không có thẻ BHYT — chi phí tự trả 100%"),
                indicator="orange", alert=True,
            )
        if any_config_changed and self.is_new():
            frappe.msgprint(
                _("⚠ Mã BHYT có thay đổi quy định — kiểm tra cấu hình trước khi tiếp tục"),
                indicator="orange", alert=True,
            )

    def _compute_totals(self):
        self.total_cost = sum(flt(r.total_cost) for r in self.items)
        self.bhyt_covered = sum(flt(r.bhyt_amount) for r in self.items)
        self.patient_pays = sum(flt(r.patient_pays) for r in self.items)
        self.ceiling_overage = sum(flt(r.ceiling_overage) for r in self.items)


class SCPDItem(Document):
    pass


# ----------------------------------------------------------------------
# UC-22 helpers (whitelisted)
# ----------------------------------------------------------------------

@frappe.whitelist()
def lookup_patient_by_bhyt(card_no: str) -> dict:
    """UC-22 step 2: search SC Patient by bhyt_card_no LIKE."""
    if not card_no:
        return {"patients": []}
    rows = frappe.db.sql("""
        SELECT name, patient_id, patient_name, bhyt_card_no,
               bhyt_type, bhyt_payment_rate
        FROM `tabSC Patient`
        WHERE disabled = 0 AND bhyt_card_no LIKE %s
        LIMIT 10
    """, f"%{card_no}%", as_dict=True)
    return {"patients": rows}


@frappe.whitelist()
def get_dispensed_items_for_dr(dr_name: str) -> list:
    """UC-22 step 3: list items đã cấp từ DR (qua SE linked)."""
    dr = frappe.db.get_value("SC Dispensing Request", dr_name,
                               ["stock_entry"], as_dict=True)
    if not dr or not dr.stock_entry:
        return []
    return frappe.db.sql("""
        SELECT sei.item, i.item_name, sei.uom,
               sei.qty AS dispensed_qty, sei.batch,
               sei.valuation_rate AS unit_cost
        FROM `tabSC Stock Entry Item` sei
        JOIN `tabSC Item` i ON i.name = sei.item
        WHERE sei.parent = %s
    """, dr.stock_entry, as_dict=True)


@frappe.whitelist()
def get_patient_dispense_history(patient: str, from_date: str = None,
                                   to_date: str = None) -> dict:
    """UC-22 step 7: summary chi phí của BN per period."""
    cond = []
    params = {"patient": patient}
    if from_date:
        cond.append("pd.dispensing_date >= %(fd)s")
        params["fd"] = from_date
    if to_date:
        cond.append("pd.dispensing_date <= %(td)s")
        params["td"] = to_date
    where = "AND " + " AND ".join(cond) if cond else ""
    rows = frappe.db.sql(f"""
        SELECT pd.name, pd.dispensing_date,
               pd.total_cost, pd.bhyt_covered, pd.patient_pays,
               pd.docstatus
        FROM `tabSC Patient Dispensing` pd
        WHERE pd.patient = %(patient)s AND pd.docstatus != 2 {where}
        ORDER BY pd.dispensing_date DESC
    """, params, as_dict=True)
    return {
        "patient": patient,
        "count": len(rows),
        "total_cost": sum(flt(r["total_cost"]) for r in rows),
        "bhyt_covered": sum(flt(r["bhyt_covered"]) for r in rows),
        "patient_pays": sum(flt(r["patient_pays"]) for r in rows),
        "records": rows,
    }
