"""SC Patient Dispensing — ghi nhận cấp phát BN + auto BHYT calc (M7, UC-22)."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class SCPatientDispensing(Document):

    def validate(self):
        self._calculate_bhyt()
        self._compute_totals()

    def on_submit(self):
        # Sync DR.status nếu link
        if self.dispensing_request and frappe.db.exists("SC Dispensing Request", self.dispensing_request):
            frappe.db.set_value("SC Dispensing Request", self.dispensing_request, "status", "Dispensed")

    def _calculate_bhyt(self):
        """Per-row BHYT calc — gọi supplycore.api.bhyt.get_active_config."""
        from supplycore.api.bhyt import get_active_config

        patient_rate = flt(self.bhyt_payment_rate) if self.bhyt_payment_rate else None
        for row in self.items:
            row.total_cost = flt(row.qty) * flt(row.unit_cost)

            cfg = get_active_config(row.item, on_date=self.dispensing_date)
            if not cfg:
                row.bhyt_code = None
                row.bhyt_group = None
                row.bhyt_rate = 0
                row.ceiling_price = 0
                row.bhyt_amount = 0
                row.ceiling_overage = 0
                row.patient_pays = row.total_cost
                continue

            row.bhyt_code = cfg.get("bhyt_code")
            row.bhyt_group = cfg.get("bhyt_group")
            cfg_rate = flt(cfg.get("payment_rate") or 0)
            # Patient rate có thể nhỏ hơn (nếu BN có loại BHYT giảm)
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

    def _compute_totals(self):
        self.total_cost = sum(flt(r.total_cost) for r in self.items)
        self.bhyt_covered = sum(flt(r.bhyt_amount) for r in self.items)
        self.patient_pays = sum(flt(r.patient_pays) for r in self.items)
        self.ceiling_overage = sum(flt(r.ceiling_overage) for r in self.items)


class SCPDItem(Document): pass
