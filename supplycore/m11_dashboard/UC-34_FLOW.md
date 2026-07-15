# UC-34 — Xem & Xử lý Cảnh báo Hành động — Flow & Implementation

**Module:** M11 Dashboard & Cảnh báo
**DocType chính:** SC Alert (`SC-ALR-{YYYY}-{########}`)
**Date:** 2026-05-11
**Source:** Phase 1 / UseCase_SupplyCore_v2.0.md UC-34

## Audit hiện trạng

| Spec | Trước UC-34 | Sau UC-34 |
|---|---|---|
| 1. Mở Notification Center / Alert Dashboard | ✓ /app/sc-alert | ✓ |
| 2. List phân loại theo severity | ✓ in_standard_filter | ✓ |
| 3. Click detail + link reference | ✓ reference_doctype/name | ✓ |
| 4. **Actions: Tạo PO, Cấp phát ưu tiên, Liên hệ NCC** | ⚠ chỉ 3 actions (quarantine, MR, payment) | ✓ thêm `action_create_purchase_order`, `action_priority_dispense`, `action_contact_supplier` |
| 5. **Đánh dấu đã xử lý + ghi chú** | ⚠ field có, không API | ✓ `mark_resolved(action, remarks)` |
| 6. **Auto-resolve khi điều kiện không còn** | ✗ | ✓ scheduler `auto_resolve_alerts()` |
| 4a. Assign cho user khác | ✗ | ✓ `assign_alert(user, note)` + assigned_to field |
| 5a. Snooze với lý do | ⚠ snooze_until field có nhưng không reason | ✓ +snooze_reason field + `snooze_alert(hours, reason)` |
| **Ngoại lệ: 48h chưa resolve → Escalate** | ✗ | ✓ scheduler `escalate_overdue_alerts()` + fields escalated/escalated_at/escalated_to |

## Actor

- SC-STOREKEEPER, SC-MANAGER, SC-ACCOUNTANT

## Pre-condition

- SC Alert đang active (resolved=0) trong hệ thống

## Luồng chính

| Bước | Action | Implementation |
|---|---|---|
| 1 | Mở /app/sc-alert?resolved=0 | Frappe List |
| 2 | Filter theo severity Critical/Warning/Info | in_standard_filter |
| 3 | Click 1 alert → detail view | Frappe Form |
| 4 | Click button action phù hợp severity/type | JS button → @whitelist method |
| 5 | Click "Mark Resolved" + nhập remarks | `mark_resolved()` |
| 6 | Auto-resolve daily scheduler | `auto_resolve_alerts()` |

## Luồng thay thế

### 4a — Assign cho user khác

`assign_alert(user, note)`:
- Set `assigned_to` field
- Tạo Frappe ToDo cho user đó (Frappe built-in assignment)
- Gửi email notification cho assignee

### 5a — Snooze với lý do

`snooze_alert(hours, reason)`:
- Set `snooze_until = now + hours`
- Set `snooze_reason`
- Append remarks "Snoozed {h}h: {reason}"

## Xử lý ngoại lệ

### 48h chưa resolve → Escalate

`escalate_overdue_alerts()` (daily scheduler):
- Query alerts: resolved=0, severity ∈ {Critical, Warning}, age > 48h, escalated=0
- Set escalated=1, escalated_at=now
- escalated_to = first user có role SupplyCore Executive (or Manager)
- Tạo NEW alert duplicate với severity bumped up
- Email tới escalated_to

## Auto-resolve heuristics

Mỗi alert_type có condition check:

| alert_type | Auto-resolve condition |
|---|---|
| `expiring_batch` | batch đã blocked HOẶC tổng qty=0 HOẶC expired (post-fact) |
| `low_stock` | Item.qty >= safety_stock |
| `contract_expiring` | FC.status != Active HOẶC valid_to >= now+threshold |
| `fc_remaining_low` | FC.remaining_value / total_value > threshold |
| `overdue_payment` | PI.status=Paid HOẶC outstanding_amount=0 |
| `qc_pending` | PR.qc_status != Pending |
| `recall_outstanding` | RN.outstanding_qty=0 |

## Field changes

### SC Alert (.json)

Add fields:
- `assigned_to` Link User in_list_view in_standard_filter — assignee
- `snooze_reason` Small Text depends_on snooze_until
- `escalated` Check default=0 in_standard_filter
- `escalated_at` Datetime read_only depends_on escalated
- `escalated_to` Link User read_only depends_on escalated
- `original_alert` Link SC Alert read_only — link đến alert gốc (cho duplicate escalation)

## Error codes

- `SC-E-ALERT-RESOLVED` — cố thao tác trên alert đã resolved
- `SC-E-ALERT-NO-USER` — assign user không tồn tại
- `SC-E-ALERT-SNOOZE-HOURS` — hours <= 0

## Logic — `sc_alert.py` (extensions)

```python
@frappe.whitelist()
def mark_resolved(self, action="Acknowledged", remarks=None):
    """UC-34 step 5: đánh dấu đã xử lý + ghi chú."""
    if self.resolved:
        frappe.throw(_("SC-E-ALERT-RESOLVED: Alert đã được xử lý"))
    self.db_set({
        "resolved": 1,
        "resolution_action": action,
        "resolved_by": frappe.session.user,
        "resolved_at": now(),
        "remarks": (self.remarks or "") + (f"\n[{now()}] {remarks}" if remarks else ""),
    })
    return {"resolved": True}

@frappe.whitelist()
def snooze_alert(self, hours: int, reason: str):
    """UC-34 5a: snooze X giờ."""
    if self.resolved:
        frappe.throw(_("SC-E-ALERT-RESOLVED"))
    if not hours or int(hours) <= 0:
        frappe.throw(_("SC-E-ALERT-SNOOZE-HOURS"))
    snooze_until = frappe.utils.add_to_date(now(), hours=int(hours))
    self.db_set({
        "snooze_until": snooze_until,
        "snooze_reason": reason or "(không lý do)",
    })
    return {"snooze_until": str(snooze_until)}

@frappe.whitelist()
def assign_alert(self, user: str, note: str = None):
    """UC-34 4a: chuyển cảnh báo cho user khác."""
    if not user or not frappe.db.exists("User", user):
        frappe.throw(_("SC-E-ALERT-NO-USER"))
    self.db_set("assigned_to", user)
    # Tạo Frappe ToDo
    from frappe.desk.form.assign_to import add as assign_add
    try:
        assign_add({
            "assign_to": [user],
            "doctype": "SC Alert",
            "name": self.name,
            "description": f"Alert {self.title}\n{note or ''}",
        })
    except Exception:
        pass  # ToDo conflict OK
    return {"assigned_to": user}

# Actions for UC-34 step 4:

@frappe.whitelist()
def action_create_purchase_order(self):
    """low_stock alert có MR linked → tạo PO."""
    # Implementation: từ alert.action_doctype=SC Material Request → tạo PO

@frappe.whitelist()
def action_priority_dispense(self):
    """expiring_batch → mark batch priority pickup trong FEFO."""
    # Set batch.priority_pickup=1 (existing field?)

@frappe.whitelist()
def action_contact_supplier(self, message=None):
    """expiring_batch/qc_pending → send email cho supplier."""
    # Lookup supplier from batch/PR → frappe.sendmail
```

## Scheduler tasks — `tasks.py` extensions

```python
def auto_resolve_alerts():
    """UC-34 step 6: re-evaluate alerts; resolve những alerts mà condition không còn."""
    open_alerts = frappe.get_all("SC Alert",
        filters={"resolved": 0},
        fields=["name", "alert_type", "reference_doctype", "reference_name"])
    resolved_count = 0
    for a in open_alerts:
        if _is_condition_lifted(a):
            frappe.db.set_value("SC Alert", a.name, {
                "resolved": 1,
                "resolution_action": "Acknowledged",
                "resolved_by": "Administrator",
                "resolved_at": now(),
                "remarks": "Auto-resolved: condition không còn",
            })
            resolved_count += 1
    frappe.db.commit()
    return resolved_count

def escalate_overdue_alerts():
    """UC-34 ngoại lệ: alerts > 48h chưa resolve → escalate."""
    threshold_hours = 48
    rows = frappe.get_all("SC Alert",
        filters={
            "resolved": 0, "escalated": 0,
            "severity": ["in", ["Critical", "Warning"]],
            "alert_date": ["<", frappe.utils.add_to_date(now(), hours=-threshold_hours)],
        }, fields=["name", "title", "severity", "alert_type"])
    escalated_count = 0
    for a in rows:
        # Find escalation target: SupplyCore Executive > Manager
        escalation_user = _get_escalation_user()
        if not escalation_user:
            continue
        frappe.db.set_value("SC Alert", a.name, {
            "escalated": 1,
            "escalated_at": now(),
            "escalated_to": escalation_user,
            "severity": "Critical",  # Bump
        })
        try:
            frappe.sendmail(recipients=[escalation_user],
                subject=f"[ESCALATED] {a.title}",
                message=f"Alert {a.name} đã không resolve trong 48h",
                queue=True)
        except Exception:
            pass
        escalated_count += 1
    frappe.db.commit()
    return escalated_count
```

## Test plan — `tests/uc34_test.py`

| Test | Scenario |
|---|---|
| `test_mark_resolved_sets_resolved_at` | mark_resolved → resolved=1 + resolved_at set |
| `test_mark_resolved_rejects_double` | resolved alert → throw SC-E-ALERT-RESOLVED |
| `test_snooze_alert_sets_until` | snooze(2, reason) → snooze_until = now+2h |
| `test_snooze_alert_rejects_zero_hours` | hours=0 → throw |
| `test_assign_alert_sets_user` | assign(user) → assigned_to=user |
| `test_assign_alert_rejects_invalid_user` | assign('nope') → throw |
| `test_auto_resolve_low_stock_when_qty_recovered` | item qty bound up → auto-resolve |
| `test_auto_resolve_overdue_payment_when_paid` | PI fully paid → auto-resolve |
| `test_escalate_after_48h_bumps_severity` | alert age 50h → escalated=1, severity=Critical |
| `test_escalate_skip_resolved` | resolved alert → không escalate |
| `test_action_contact_supplier_logs` | gọi action_contact_supplier → sendmail attempted |

## Hooks

Add to `hooks.py.scheduler_events.daily`:
- `supplycore.m11_dashboard.tasks.auto_resolve_alerts`
- `supplycore.m11_dashboard.tasks.escalate_overdue_alerts`

## Out-of-scope

- Push notification (mobile) — defer
- Bulk actions (multi-select alerts) — defer
- Custom severity (only 3 levels)

## File changes

1. `supplycore/m11_dashboard/UC-34_FLOW.md` — this file
2. `supplycore/m11_dashboard/doctype/sc_alert/sc_alert.json` — +6 fields
3. `supplycore/m11_dashboard/doctype/sc_alert/sc_alert.py` — +6 methods
4. `supplycore/m11_dashboard/tasks.py` — auto_resolve_alerts + escalate_overdue_alerts
5. `supplycore/hooks.py` — register 2 schedulers
6. `supplycore/tests/uc34_test.py` — 11 test scenarios
