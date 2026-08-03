"""SC Investigation Report — điều tra thất thoát / sai lệch tồn kho (UC-31)."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, now, getdate


ADMIN_USERS = {"Administrator", "Guest"}
PROTECTED_ROLES = {"System Manager"}


class SCInvestigationReport(Document):

    def validate(self):
        self._validate_scope()
        self._compute_variance()
        self._set_triggered_metadata()
        self.anomalies_detected = len(self.findings or [])
        if self.docstatus == 0:
            self.status = "Investigating" if self.findings else "Draft"

    def _validate_scope(self):
        if not (self.item or self.warehouse or self.batch):
            frappe.throw(_(
                "SC-E-INV-NO-SCOPE: Phải có ít nhất 1 trong: Vật tư / Kho / Batch"
            ))
        if self.period_start and self.period_end \
           and getdate(self.period_start) > getdate(self.period_end):
            frappe.throw(_("period_start phải ≤ period_end"))

    def _set_triggered_metadata(self):
        if not self.triggered_by:
            user = frappe.session.user
            if user not in (None, "", "Guest"):
                self.triggered_by = user
        if not self.triggered_at:
            self.triggered_at = now()

    def _compute_variance(self):
        actual = flt(self.actual_qty)
        theo = flt(self.theoretical_qty)
        self.variance_qty = actual - theo
        # Best-effort valuation rate từ SLE gần nhất của item+warehouse
        rate = 0
        if self.item:
            conds = ["item = %(item)s", "is_cancelled = 0", "valuation_rate > 0"]
            params = {"item": self.item}
            if self.warehouse:
                conds.append("warehouse = %(wh)s"); params["wh"] = self.warehouse
            row = frappe.db.sql(f"""
                SELECT valuation_rate FROM `tabSC Stock Ledger Entry`
                WHERE {' AND '.join(conds)}
                ORDER BY posting_date DESC, creation DESC LIMIT 1
            """, params)
            rate = flt(row[0][0]) if row else 0
        self.variance_value = self.variance_qty * rate

    def on_submit(self):
        self.db_set("status", "Resolved")
        self.db_set("approved_by", frappe.session.user
                     if frappe.session.user not in (None, "", "Guest") else "Administrator")
        self.db_set("approved_at", now())

    def on_cancel(self):
        self.db_set("status", "Draft")

    # ==================================================================
    # UC-31 step 3: audit trail (delegate to api/investigation.py)
    # ==================================================================
    @frappe.whitelist()
    def run_audit_trail(self, limit=500):
        from supplycore.m10_traceability.api.investigation import get_audit_trail
        return get_audit_trail(
            item=self.item, warehouse=self.warehouse,
            start_date=self.period_start, end_date=self.period_end,
            user=self.filter_user, limit=limit,
        )

    # ==================================================================
    # UC-31 step 4: so sánh
    # ==================================================================
    @frappe.whitelist()
    def compare_stock(self):
        from supplycore.m10_traceability.api.investigation import compare_theoretical_vs_actual
        if not self.item:
            frappe.throw(_("SC-E-INV-NO-SCOPE: Phải có item để so sánh tồn kho"))
        res = compare_theoretical_vs_actual(self.item, self.warehouse, self.batch)
        self.db_set("theoretical_qty", flt(res["theoretical_qty"]))
        self.reload()
        self._compute_variance()
        self.db_update()
        return {
            "theoretical_qty": flt(self.theoretical_qty),
            "actual_qty": flt(self.actual_qty),
            "variance_qty": flt(self.variance_qty),
            "variance_value": flt(self.variance_value),
        }

    # ==================================================================
    # UC-31 step 5: detect anomalies
    # ==================================================================
    @frappe.whitelist()
    def detect_anomalies(self, large_qty_threshold=1000):
        from supplycore.m10_traceability.api.investigation import detect_anomalies as _detect
        findings = _detect(
            item=self.item, warehouse=self.warehouse,
            start_date=self.period_start, end_date=self.period_end,
            user=self.filter_user, large_qty_threshold=flt(large_qty_threshold),
        )
        if self.docstatus != 0:
            frappe.throw(_("SC-E-INV-NOT-DRAFT: Chỉ detect anomalies khi Draft"))
        self.findings = []
        for f in findings:
            self.append("findings", f)
        self.anomalies_detected = len(self.findings)
        self.save(ignore_permissions=True)
        return {"anomalies_detected": self.anomalies_detected,
                "by_severity": _group_severity(self.findings)}

    # ==================================================================
    # UC-31 5a: lock user (fraud)
    # ==================================================================
    @frappe.whitelist()
    def lock_user(self, user, reason):
        if not user or not frappe.db.exists("User", user):
            frappe.throw(_("SC-E-INV-USER-NOT-FOUND: User {0} không tồn tại").format(user))
        if user in ADMIN_USERS:
            frappe.throw(_(
                "SC-E-INV-USER-IS-ADMIN: Không thể khóa user hệ thống {0}"
            ).format(user))
        # Check role protection
        user_roles = set(frappe.get_roles(user))
        if user_roles & PROTECTED_ROLES:
            frappe.throw(_(
                "SC-E-INV-USER-IS-ADMIN: User {0} có role System Manager — không thể khóa qua investigation"
            ).format(user))
        if not reason or not str(reason).strip():
            frappe.throw(_("Phải nhập lý do khóa user"))
        frappe.db.set_value("User", user, "enabled", 0)
        log_line = (
            f"[{now()}] LOCKED user={user} by={frappe.session.user} "
            f"reason={reason.strip()[:200]}"
        )
        new_log = (self.suspended_users_log or "") + "\n" + log_line
        self.db_set("suspended_users_log", new_log.strip())
        # Escalation email best-effort
        try:
            sm_users = frappe.get_all(
                "Has Role",
                filters={"role": ["in", ["SupplyCore Manager", "System Manager"]]},
                pluck="parent",
            )
            recipients = frappe.get_all("User",
                filters={"enabled": 1, "name": ["in", sm_users]},
                pluck="name") if sm_users else []
            if recipients:
                from supplycore.utils.emailer import send_doc_email
                send_doc_email(
                    doctype="SC Investigation Report", name=self.name, recipients=recipients,
                    subject=f"[SupplyCore][GIAN LẬN] Điều tra {self.name}: đã khóa tài khoản {user}",
                    title="Cảnh báo gian lận — đã khóa tài khoản",
                    intro=f"Trong quá trình điều tra <b>{self.name}</b>, tài khoản <b>{user}</b> đã bị khóa.",
                    info_rows=[("Mã điều tra", self.name), ("Tài khoản bị khóa", user)],
                    note=f"Lý do: {reason}", note_kind="crit", cta_label="Xem điều tra")
        except Exception:
            pass
        return {"user": user, "locked": True}

    # ==================================================================
    # UC-31 4a: tạo phiếu điều chỉnh System Error
    # ==================================================================
    @frappe.whitelist()
    def create_system_error_adjustment(self, actual_qty=None, valuation_rate=0):
        if self.system_error_adjustment:
            frappe.throw(_("Đã có phiếu điều chỉnh {0}").format(self.system_error_adjustment))
        if not self.item or not self.warehouse:
            frappe.throw(_(
                "SC-E-INV-NO-SCOPE: Phải có item + warehouse để tạo SR"
            ))
        if actual_qty is not None:
            self.actual_qty = flt(actual_qty)
            self.db_set("actual_qty", flt(actual_qty))
        self.compare_stock()
        if abs(flt(self.variance_qty)) < 0.01:
            frappe.throw(_(
                "SC-E-INV-NO-VARIANCE: Không có chênh lệch — không cần điều chỉnh"
            ))
        sr = frappe.new_doc("SC Stock Reconciliation")
        sr.posting_date = frappe.utils.today()
        sr.warehouse = self.warehouse
        sr.investigation_notes = (
            f"System Error — Investigation {self.name}\n"
            f"{(self.description or '')[:500]}"
        )
        sr.requires_investigation = 1
        sr.investigated_by = frappe.session.user
        sr.investigated_at = now()
        sr.append("items", {
            "item": self.item,
            "uom": frappe.db.get_value("SC Item", self.item, "uom"),
            "batch": self.batch,
            "valuation_rate": flt(valuation_rate),
            "actual_qty": flt(self.actual_qty),
            "system_qty": flt(self.theoretical_qty),
            "reason": "System Error",
            "remarks": f"Auto from {self.name}",
        })
        sr.remarks = f"Auto từ điều tra {self.name}"
        sr.flags.ignore_permissions = True
        sr.insert()
        self.db_set("system_error_adjustment", sr.name)
        return {"stock_reconciliation": sr.name,
                "url": f"/app/sc-stock-reconciliation/{sr.name}"}

    # ==================================================================
    # UC-31 step 6: Print Format data
    # ==================================================================
    @frappe.whitelist()
    def get_investigation_minutes_data(self):
        return {
            "name": self.name,
            "investigation_date": str(self.investigation_date) if self.investigation_date else "",
            "investigation_type": self.investigation_type,
            "scope": {
                "item": self.item, "warehouse": self.warehouse, "batch": self.batch,
                "period": f"{self.period_start} → {self.period_end}",
                "filter_user": self.filter_user,
            },
            "description": self.description,
            "theoretical_qty": flt(self.theoretical_qty),
            "actual_qty": flt(self.actual_qty),
            "variance_qty": flt(self.variance_qty),
            "variance_value": flt(self.variance_value),
            "anomalies_detected": int(self.anomalies_detected or 0),
            "findings": [{
                "type": f.finding_type, "severity": f.severity,
                "voucher": f"{f.voucher_type} {f.voucher_no}",
                "voucher_date": str(f.voucher_date) if f.voucher_date else "",
                "user": f.user_suspected,
                "qty_change": flt(f.qty_change),
                "ip": f.ip_address,
                "action": f.action_taken,
                "evidence": f.evidence,
            } for f in self.findings],
            "recommendation": self.recommendation,
            "conclusion": self.conclusion,
            "system_error_adjustment": self.system_error_adjustment,
            "suspended_users_log": self.suspended_users_log,
            "approved_by": self.approved_by,
            "approved_at": str(self.approved_at) if self.approved_at else "",
            "signatures": {
                "investigator": "_____________________",
                "manager": "_____________________",
                "accountant": "_____________________",
            },
            "url": f"/app/sc-investigation-report/{self.name}",
        }


def _group_severity(findings):
    g = {"Low": 0, "Medium": 0, "High": 0, "Critical": 0}
    for f in findings:
        sev = f.severity or "Medium"
        if sev in g:
            g[sev] += 1
    return g
