"""SC Alert Rule — cấu hình + dispatch alert notification (UC-33)."""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now


class SCAlertRule(Document):

    def before_insert(self):
        # UC-33: spec "Hàng ngày 8h sáng" — Frappe Time field default
        # không giữ "08:00:00" mà fallback nowtime(). Override ở đây.
        from frappe.utils import get_time
        if not self.scheduled_time or str(self.scheduled_time)[:5] != "08:00":
            try:
                self.scheduled_time = get_time("08:00:00")
            except Exception:
                self.scheduled_time = "08:00:00"
        if self.frequency == "Weekly" and not self.day_of_week:
            self.day_of_week = "Mon"

    def validate(self):
        self._validate_channels()
        self._validate_recipients()

    def _validate_channels(self):
        if not (self.channel_email or self.channel_inapp or self.channel_sms):
            frappe.throw(_(
                "SC-E-AR-NO-CHANNEL: Phải chọn ít nhất 1 kênh "
                "(Email / In-app / SMS)"
            ))
        if self.channel_sms and not (self.sms_phones and str(self.sms_phones).strip()):
            frappe.throw(_(
                "SC-E-AR-SMS-NO-PHONES: SMS bật nhưng chưa nhập sms_phones"
            ))

    def _validate_recipients(self):
        has_role = bool(self.recipient_roles and str(self.recipient_roles).strip())
        has_email = bool(self.extra_emails and str(self.extra_emails).strip())
        has_phone = bool(self.channel_sms
                          and self.sms_phones
                          and str(self.sms_phones).strip())
        if not (has_role or has_email or has_phone):
            frappe.throw(_(
                "SC-E-AR-NO-RECIPIENT: Phải có ít nhất 1 recipient "
                "(roles / emails / sms_phones)"
            ))

    # ------------------------------------------------------------------
    # UC-33 step 7: test
    # ------------------------------------------------------------------
    @frappe.whitelist()
    def test_alert_rule(self):
        """Gửi test notification qua từng channel enabled. Persist outcome."""
        results = {"email": None, "inapp": None, "sms": None}
        errors = []

        if self.channel_email:
            try:
                recipients = self._resolve_email_recipients()
                if not recipients:
                    raise Exception("Không có recipient email khả dụng")
                from supplycore.utils.emailer import send_email
                send_email(
                    recipients=recipients,
                    subject=f"[SupplyCore][TEST] {self.title}",
                    title="Email test quy tắc cảnh báo",
                    intro="Đây là email TEST — không phải cảnh báo thật.",
                    info_rows=[("Quy tắc", f"{self.name} — {self.title}"),
                               ("Loại", self.alert_type), ("Mức độ", self.severity)],
                    delayed=True,
                )
                results["email"] = {"status": "OK", "recipients": len(recipients)}
            except Exception as e:
                results["email"] = {"status": "Failed", "error": str(e)[:200]}
                errors.append(f"Email: {str(e)[:100]}")

        if self.channel_inapp:
            try:
                a = frappe.new_doc("SC Alert")
                a.alert_date = now()
                a.alert_rule = self.name
                a.alert_type = self.alert_type
                a.severity = self.severity or "Info"
                a.title = f"[TEST] {self.title}"
                a.message = (
                    f"Test in-app notification từ rule {self.name}. "
                    f"Đây là cảnh báo test."
                )
                a.flags.ignore_permissions = True
                a.insert()
                results["inapp"] = {"status": "OK", "alert": a.name}
            except Exception as e:
                results["inapp"] = {"status": "Failed", "error": str(e)[:200]}
                errors.append(f"In-app: {str(e)[:100]}")

        if self.channel_sms:
            try:
                phones = [p.strip() for p in (self.sms_phones or "").split(",")
                           if p.strip()]
                if not phones:
                    raise Exception("sms_phones rỗng")
                count = _send_sms_batch(phones, f"[TEST] {self.title}")
                results["sms"] = {"status": "OK", "count": count}
            except Exception as e:
                results["sms"] = {"status": "Failed", "error": str(e)[:200]}
                errors.append(f"SMS: {str(e)[:100]}")

        successes = sum(1 for v in results.values()
                         if v and v["status"] == "OK")
        if not errors:
            status = "Success"
        elif successes > 0:
            status = "Partial"
        else:
            status = "Failed"

        self.db_set({
            "last_test_at": now(),
            "last_test_status": status,
            "last_test_error": "; ".join(errors)[:200] if errors else None,
        })
        return {"status": status, "results": results, "errors": errors}

    # ------------------------------------------------------------------
    # UC-33 dispatch — hooked from scan_alerts
    # ------------------------------------------------------------------
    def dispatch_alert_notifications(self, alert_doc):
        """Gửi notification thật qua các channel khi alert mới được tạo."""
        # In-app channel: SC Alert đã được tạo bởi scan_alerts; skip
        if self.channel_email:
            recipients = self._resolve_email_recipients()
            if recipients:
                try:
                    from supplycore.utils.emailer import send_doc_email
                    _ref = f"{alert_doc.reference_doctype or ''} {alert_doc.reference_name or ''}".strip()
                    send_doc_email(
                        doctype="SC Alert", name=alert_doc.name, recipients=recipients,
                        subject=f"[SupplyCore][{self.severity}] {alert_doc.title}",
                        title=alert_doc.title,
                        intro=alert_doc.message or "",
                        info_rows=[("Loại cảnh báo", self.alert_type),
                                   ("Mức độ", self.severity),
                                   ("Đối tượng liên quan", _ref)],
                        note_kind=("crit" if self.severity == "Critical" else "warn"),
                        cta_label="Xem cảnh báo", delayed=True)
                except Exception as e:
                    frappe.log_error(
                        message=str(e)[:1000],
                        title=f"UC-33 dispatch email {self.name}",
                    )
        if self.channel_sms:
            phones = [p.strip() for p in (self.sms_phones or "").split(",")
                       if p.strip()]
            if phones:
                try:
                    _send_sms_batch(
                        phones,
                        f"[{self.severity}] {alert_doc.title[:120]}",
                    )
                except Exception as e:
                    frappe.log_error(
                        message=str(e)[:1000],
                        title=f"UC-33 dispatch sms {self.name}",
                    )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _resolve_email_recipients(self) -> list:
        emails = set()
        for role in (self.recipient_roles or "").split(","):
            role = role.strip()
            if not role:
                continue
            users = frappe.db.sql_list("""
                SELECT u.email FROM `tabUser` u
                JOIN `tabHas Role` r ON r.parent = u.name
                WHERE r.role = %s AND u.enabled = 1
                  AND u.email IS NOT NULL AND u.email != ''
            """, role)
            emails.update(users)
        for e in (self.extra_emails or "").split(","):
            e = e.strip()
            if "@" in e:
                emails.add(e)
        return list(emails)


def _send_sms_batch(phones: list, message: str) -> int:
    """UC-33: SMS placeholder.
    Real impl plug vào HTTP POST to SupplyCore Settings.sms_gateway_endpoint.
    Hiện log + count; throw nếu gateway chưa configure."""
    endpoint = frappe.db.get_single_value(
        "SupplyCore Settings", "sms_gateway_endpoint")
    if not endpoint:
        raise Exception("SMS gateway chưa cấu hình trong SupplyCore Settings")
    for p in phones:
        frappe.logger().info(f"SMS to {p}: {message[:140]}")
    return len(phones)
