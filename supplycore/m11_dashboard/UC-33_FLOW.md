# UC-33 — Cấu hình & Quản lý Cảnh báo Tự động — Flow & Implementation

**Module:** M11 Dashboard & Cảnh báo
**DocType chính:** SC Alert Rule (`SC-AR-{#####}`) + SC Alert
**Date:** 2026-05-11
**Source:** Phase 1 / UseCase_SupplyCore_v2.0.md UC-33

## Audit hiện trạng

| Spec | Trước UC-33 | Sau UC-33 |
|---|---|---|
| 1. Mở Alert Configuration | ✓ /app/sc-alert-rule | ✓ |
| 2. Chọn loại cảnh báo | ✓ alert_type select 7 options | ✓ |
| 3. Thiết lập ngưỡng | ✓ threshold_value/operator/unit | ✓ |
| 4. **Kênh: Email, In-app, SMS** | ⚠ ngầm hết — không có channel select | ✓ +channel_email +channel_inapp +channel_sms +sms_phones |
| 5. Người nhận theo role/email | ✓ recipient_roles + extra_emails | ✓ |
| 6. **Tần suất Realtime/Daily 8AM/Weekly Mon** | ⚠ chỉ Daily/Hourly/Realtime, không có time/day | ✓ +scheduled_time +day_of_week + Weekly option |
| 7. **Test gửi cảnh báo** | ✗ | ✓ `test_alert_rule()` thử từng channel + ghi error |
| 8. Lưu + active ngay | ✓ doctype save | ✓ |
| 5a. Email bounce retry 3x | ⚠ Frappe Email Queue retry built-in nhưng chưa dùng | ✓ dùng `frappe.sendmail(queue=True)` |
| 7a. Test fail show error cụ thể | ✗ | ✓ `last_test_status` + `last_test_error` |
| Ngoại lệ: Email server unavailable → queue | ⚠ chưa wire | ✓ Email Queue auto-retry scheduler |
| **scan_alerts** chỉ tạo SC Alert, không gửi notification | ⚠ gap nghiêm trọng | ✓ `dispatch_alert_notifications()` integrated |

## Actor

- SC-SYSADMIN (chính cấu hình), SC-MANAGER (xem + edit)

## Pre-condition

- User có quyền configure (System Manager hoặc SupplyCore Manager)
- Frappe Email Account đã setup (cho retry)

## Luồng chính

| Bước | Action | Implementation |
|---|---|---|
| 1 | Mở /app/sc-alert-rule → New | DocType List |
| 2 | Set title, alert_type, severity | Required fields |
| 3 | Set threshold_value + operator + unit | Threshold section |
| 4 | Tick channel_email/inapp/sms; nhập sms_phones nếu cần | New channels section |
| 5 | Set recipient_roles + extra_emails | Recipients section |
| 6 | Set frequency (Daily/Hourly/Realtime/Weekly) + scheduled_time + day_of_week | Schedule section |
| 7 | Click "Test Alert" → API `test_alert_rule()` gửi dummy notification | Returns success/error per channel |
| 8 | Save → enabled=1 → scan_alerts hourly scheduler dùng ngay | hooks.py daily/hourly |

## Luồng thay thế

### 5a — Email bounce retry

`frappe.sendmail(queue=True)` dùng Frappe Email Queue:
- Email Queue table lưu pending emails
- Frappe scheduler retry 3× với exponential backoff
- Failed → status="Error" + error message

### 7a — Test fail

`test_alert_rule()` capture exceptions per channel:
- Email: SMTP error → `last_test_error = "SMTP: <msg>"`
- SMS: gateway error → `last_test_error = "SMS: <msg>"`
- In-app: rare fail (Frappe internal)
- Set `last_test_status = "Failed"`, return error detail

## Xử lý ngoại lệ

### Email server không khả dụng

- Frappe Email Queue tự động retry khi server lên
- Email Queue có status: Not Sent, Sending, Sent, Error
- `dispatch_alert_notifications()` luôn dùng `queue=True` để vào queue

## Field changes

### SC Alert Rule (.json)

Add fields:
- `channel_email` Check default 1 — gửi qua email
- `channel_inapp` Check default 1 — tạo SC Alert in-app
- `channel_sms` Check default 0 — gửi SMS (cần config gateway)
- `sms_phones` Small Text — danh sách số điện thoại (phân cách dấu phẩy) khi `channel_sms=1`
- `scheduled_time` Time — giờ chạy daily (mặc định "08:00")
- `day_of_week` Select Mon..Sun — chỉ áp dụng cho Weekly
- `last_test_at` Datetime read_only
- `last_test_status` Select read_only ("Success / Failed / Partial")
- `last_test_error` Small Text read_only

Update `frequency` options: thêm `Weekly`.

### Error codes

- `SC-E-AR-NO-CHANNEL` — không có channel nào enabled
- `SC-E-AR-NO-RECIPIENT` — không có recipient (roles + emails đều rỗng)
- `SC-E-AR-INVALID-TIME` — scheduled_time format sai
- `SC-E-AR-SMS-NO-PHONES` — channel_sms=1 nhưng sms_phones rỗng

## Logic — `sc_alert_rule.py` (extensions)

```python
class SCAlertRule(Document):

    def validate(self):
        # Phải có ít nhất 1 channel
        if not (self.channel_email or self.channel_inapp or self.channel_sms):
            frappe.throw(_("SC-E-AR-NO-CHANNEL: Chọn ít nhất 1 kênh"))
        if self.channel_sms and not (self.sms_phones and self.sms_phones.strip()):
            frappe.throw(_("SC-E-AR-SMS-NO-PHONES: SMS bật nhưng chưa nhập số"))
        if not ((self.recipient_roles and self.recipient_roles.strip())
                 or (self.extra_emails and self.extra_emails.strip())
                 or (self.channel_sms and self.sms_phones)):
            frappe.throw(_("SC-E-AR-NO-RECIPIENT: Phải có recipient roles/emails/phones"))

    @frappe.whitelist()
    def test_alert_rule(self):
        """UC-33 step 7: gửi test notification mỗi channel đang enable."""
        results = {"email": None, "inapp": None, "sms": None}
        errors = []

        # Email channel
        if self.channel_email:
            try:
                recipients = self._resolve_email_recipients()
                if not recipients:
                    raise Exception("Không có recipient email")
                frappe.sendmail(
                    recipients=recipients,
                    subject=f"[TEST] {self.title}",
                    message=f"<p>Test alert rule {self.name}</p>",
                    queue=True, now=False,
                )
                results["email"] = {"status": "OK", "recipients": len(recipients)}
            except Exception as e:
                results["email"] = {"status": "Failed", "error": str(e)[:200]}
                errors.append(f"Email: {str(e)[:100]}")

        # In-app channel
        if self.channel_inapp:
            try:
                a = frappe.new_doc("SC Alert")
                a.alert_date = now()
                a.alert_rule = self.name
                a.alert_type = self.alert_type
                a.severity = self.severity or "Info"
                a.title = f"[TEST] {self.title}"
                a.message = "Test in-app notification"
                a.flags.ignore_permissions = True
                a.insert()
                results["inapp"] = {"status": "OK", "alert": a.name}
            except Exception as e:
                results["inapp"] = {"status": "Failed", "error": str(e)[:200]}
                errors.append(f"In-app: {str(e)[:100]}")

        # SMS channel
        if self.channel_sms:
            try:
                phones = [p.strip() for p in (self.sms_phones or "").split(",") if p.strip()]
                if not phones:
                    raise Exception("sms_phones rỗng")
                count = _send_sms_batch(phones, f"[TEST] {self.title}")
                results["sms"] = {"status": "OK", "count": count}
            except Exception as e:
                results["sms"] = {"status": "Failed", "error": str(e)[:200]}
                errors.append(f"SMS: {str(e)[:100]}")

        # Persist test outcome
        status = "Success" if not errors else ("Partial" if any(
            v and v["status"] == "OK" for v in results.values()) else "Failed")
        self.db_set({
            "last_test_at": now(),
            "last_test_status": status,
            "last_test_error": "; ".join(errors)[:200] if errors else None,
        })
        return {"status": status, "results": results}

    def dispatch_alert_notifications(self, alert_doc):
        """Gửi notification khi scan_alerts tạo SC Alert mới."""
        if self.channel_email:
            recipients = self._resolve_email_recipients()
            if recipients:
                try:
                    frappe.sendmail(
                        recipients=recipients,
                        subject=f"[{self.severity}] {alert_doc.title}",
                        message=f"<h3>{alert_doc.title}</h3><p>{alert_doc.message}</p>"
                                f"<p>Reference: {alert_doc.reference_doctype} "
                                f"{alert_doc.reference_name}</p>",
                        queue=True, now=False,
                    )
                except Exception as e:
                    frappe.log_error(message=str(e)[:1000], title=f"AR dispatch email {self.name}")
        if self.channel_sms:
            phones = [p.strip() for p in (self.sms_phones or "").split(",") if p.strip()]
            if phones:
                try:
                    _send_sms_batch(phones, f"[{self.severity}] {alert_doc.title[:120]}")
                except Exception as e:
                    frappe.log_error(message=str(e)[:1000], title=f"AR dispatch sms {self.name}")
        # In-app channel: SC Alert đã được tạo bởi scan_alerts; không cần thêm

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
    """SMS placeholder. Thực tế plug vào SupplyCore Settings.sms_gateway_endpoint
    (chưa configure → throw rõ ràng)."""
    endpoint = frappe.db.get_single_value("SupplyCore Settings", "sms_gateway_endpoint")
    if not endpoint:
        raise Exception("SMS gateway chưa cấu hình trong SupplyCore Settings")
    # Real impl: HTTP POST batch — tạm log + count
    for p in phones:
        frappe.logger().info(f"SMS to {p}: {message[:140]}")
    return len(phones)
```

## Migration

- Thêm field qua JSON — auto-migrate
- Cũ rules không có channel_email mặc định bật để giữ behavior cũ

## Test plan — `tests/uc33_test.py`

| Test | Scenario |
|---|---|
| `test_alert_rule_validates_no_channel` | Không tick channel nào → throw SC-E-AR-NO-CHANNEL |
| `test_alert_rule_validates_sms_phones` | channel_sms=1 + sms_phones rỗng → throw |
| `test_alert_rule_validates_no_recipient` | recipient_roles + extra_emails + sms_phones đều rỗng → throw |
| `test_test_alert_rule_email_success` | channel_email=1, recipient có user → results.email=OK |
| `test_test_alert_rule_inapp_creates_sc_alert` | channel_inapp=1 → tạo SC Alert "[TEST]" |
| `test_test_alert_rule_sms_no_gateway` | channel_sms=1 không gateway → results.sms.status=Failed |
| `test_test_alert_rule_persists_last_test` | sau test → last_test_at + status set |
| `test_dispatch_alert_notifications_email` | dispatch → frappe.sendmail called (queue=True) |
| `test_weekly_frequency_with_day_of_week` | frequency=Weekly + day_of_week=Mon → save OK |
| `test_scheduled_time_default_8am` | scheduled_time mặc định "08:00" khi tạo mới |
| `test_resolve_email_recipients_dedups` | role + extra_email overlap → emails dedup |

## Out-of-scope

- Real SMS gateway integration (placeholder)
- Custom alert types beyond 7 existing
- User-level subscription preference (defer to UC tương lai)

## File changes

1. `supplycore/m11_dashboard/UC-33_FLOW.md` — this file
2. `supplycore/m11_dashboard/doctype/sc_alert_rule/sc_alert_rule.json` — +9 fields
3. `supplycore/m11_dashboard/doctype/sc_alert_rule/sc_alert_rule.py` — full controller
4. `supplycore/m11_dashboard/tasks.py` — hook dispatch into scan_alerts
5. `supplycore/supplycore/doctype/supplycore_settings/supplycore_settings.json` — +sms_gateway_endpoint
6. `supplycore/tests/uc33_test.py` — 11 test scenarios
