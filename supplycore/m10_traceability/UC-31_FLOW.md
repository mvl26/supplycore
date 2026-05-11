# UC-31 — Điều tra Sự cố Thất thoát Vật tư (Investigation) — Flow & Implementation

**Module:** M10 Traceability
**DocType chính:** SC Investigation Report (`SC-INV-{YYYY}-{#####}`)
**Date:** 2026-05-11
**Source:** Phase 1 / UseCase_SupplyCore_v2.0.md UC-31

## Audit hiện trạng

| Spec | Trước | Sau UC-31 |
|---|---|---|
| 1. Mở Audit Trail / Stock Ledger chi tiết | ⚠ chỉ SLE List view | ✓ `get_audit_trail(item, start, end, warehouse, user)` |
| 2. Lọc theo Item/Period/Warehouse/User | ⚠ List filter chỉ qua UI | ✓ API filter |
| 3. Show Người tạo, Thời gian, IP, Thay đổi | ⚠ SLE có owner+creation; IP missing | ✓ join Activity Log để best-effort IP |
| 4. So sánh tồn lý thuyết vs thực tế | ⚠ SLE.balance_qty có nhưng không compare | ✓ `compare_theoretical_vs_actual()` |
| 5. **Xác định giao dịch bất thường** | ✗ | ✓ `detect_anomalies()` + Finding records |
| 6. **Xuất báo cáo điều tra + chữ ký** | ✗ | ✓ Print Format + `get_investigation_minutes_data()` |
| 5a. Phát hiện gian lận → khóa user | ✗ | ✓ `lock_user(user, reason)` set enabled=0 + log |
| 4a. Lỗi hệ thống → tạo phiếu điều chỉnh | ✗ | ✓ `create_system_error_adjustment()` → SC Stock Reconciliation reason='System Error' |
| **Ngoại lệ: Audit log bị xóa** | ⚠ Frappe Version + Activity Log mặc định không hard-delete | ✓ thêm method `verify_audit_integrity()` so sánh Version count vs expected |

## Actor

- SC-MANAGER (chính điều tra), SC-SYSADMIN (technical lock user)

## Pre-condition

- Phát hiện sai lệch tồn (Stocktake variance > threshold) hoặc nghi ngờ thất thoát
- SC Stock Ledger Entry và Frappe Version có dữ liệu

## Luồng chính

| Bước | Action | Implementation |
|---|---|---|
| 1 | Mở SC Investigation Report (new draft), nhập filter scope | DocType — Draft |
| 2 | Set item, warehouse, period_start, period_end, user (optional) | Field setters |
| 3 | Click "Run Audit Trail" → API trả tất cả SLE + metadata | `get_audit_trail()` |
| 4 | Click "Compare Theoretical vs Actual" → diff hiện ra parent fields | `compare_theoretical_vs_actual()` |
| 5 | Click "Detect Anomalies" → populate findings child table | `detect_anomalies()` |
| 6 | Click "Generate Minutes" → Print Format + chữ ký placeholder | `get_investigation_minutes_data()` |
| 7 | Submit → status=Resolved, approved_by set | `on_submit()` |

## Luồng thay thế

### 5a — Phát hiện gian lận

Trong findings table, row có severity=Critical và user_suspected:
- Click "Lock User" → API `lock_user(user, reason)`
- Set `User.enabled = 0`
- Append entry vào `suspended_users_log` text field của report
- Send escalation email cho SupplyCore Manager + System Manager

### 4a — Lỗi hệ thống

- Click "Create Adjustment SR" với delta_qty (variance)
- API `create_system_error_adjustment()` tạo SC Stock Reconciliation:
  - reason = "System Error — Investigation {self.name}"
  - investigation_notes = self.description
  - Link sang `system_error_adjustment` field

## Heuristics — `detect_anomalies()`

Phát hiện theo các pattern:

| Anomaly Type | Heuristic | Severity |
|---|---|---|
| `Large Qty Change` | abs(qty_change) > threshold (default 1000) | Medium |
| `Off-Hours Transaction` | creation outside 06:00-22:00 | Low |
| `Cancelled Without Reason` | is_cancelled=1 AND no remarks | High |
| `Modified After Submit` | Version có rows sau docstatus=1 | High |
| `Repeated User Pattern` | cùng user > 10 SLE âm trong period | Medium |
| `Balance Mismatch` | SLE.balance_qty không khớp với cumulative sum | Critical |
| `Backdated Entry` | posting_date < creation - 7 days | High |

## Field changes

### New DocType — SC Investigation Report

| Field | Type | Notes |
|---|---|---|
| investigation_date | Date reqd | Mặc định Today |
| investigation_type | Select | "Stock Loss / Discrepancy / Fraud / System Error / Other" |
| item | Link SC Item | Optional |
| warehouse | Link SC Warehouse | Optional |
| batch | Link SC Batch | Optional |
| period_start | Date reqd | |
| period_end | Date reqd | |
| filter_user | Link User | Optional — filter SLE owner |
| description | Small Text | |
| theoretical_qty | Float read_only | Cumulative SLE qty |
| actual_qty | Float | Manually entered (from physical count) |
| variance_qty | Float read_only | actual - theoretical |
| variance_value | Currency read_only | variance_qty * valuation_rate |
| anomalies_detected | Int read_only | count findings |
| findings | Table SC Investigation Finding | |
| recommendation | Long Text | Biện pháp khắc phục |
| conclusion | Long Text | |
| suspended_users_log | Long Text read_only | Lịch sử lock user |
| system_error_adjustment | Link SC Stock Reconciliation read_only | |
| status | Select | "Draft/Investigating/Resolved/Closed" |
| approved_by, approved_at | Link User + Datetime read_only | |
| amended_from, remarks | Standard | |

is_submittable=1, track_changes=1, autoname=SC-INV-{YYYY}-{#####}

### New child — SC Investigation Finding

| Field | Type | Notes |
|---|---|---|
| finding_type | Select | "Large Qty Change/Off-Hours/Cancelled/Modified After Submit/Repeated User/Balance Mismatch/Backdated" |
| voucher_type | Data | |
| voucher_no | Data | |
| voucher_date | Date | |
| user_suspected | Link User | SLE owner |
| qty_change | Float | |
| balance_after | Float | |
| severity | Select | "Low/Medium/High/Critical" |
| evidence | Small Text | |
| ip_address | Data | Best-effort từ Activity Log |
| acknowledged | Check | |
| action_taken | Data | "Locked / Adjusted / Noted / Dismissed" |

## Error codes

- `SC-E-INV-NOT-DRAFT` — cố sửa khi đã submit
- `SC-E-INV-NO-SCOPE` — không có item/warehouse/period
- `SC-E-INV-USER-NOT-FOUND` — lock user không tồn tại
- `SC-E-INV-USER-IS-ADMIN` — không cho lock System Manager / Administrator

## Logic — `m10_traceability/api/investigation.py`

```python
@frappe.whitelist()
def get_audit_trail(item=None, warehouse=None, start_date=None, end_date=None,
                     user=None, limit=500) -> list:
    """UC-31 step 1-3: trả audit trail SLE filtered."""
    conds = ["sle.is_cancelled IN (0, 1)"]
    params = {}
    if item:
        conds.append("sle.item = %(item)s"); params["item"] = item
    if warehouse:
        conds.append("sle.warehouse = %(wh)s"); params["wh"] = warehouse
    if start_date:
        conds.append("sle.posting_date >= %(start)s"); params["start"] = start_date
    if end_date:
        conds.append("sle.posting_date <= %(end)s"); params["end"] = end_date
    if user:
        conds.append("sle.owner = %(user)s"); params["user"] = user
    where = " AND ".join(conds)
    rows = frappe.db.sql(f"""
        SELECT sle.name, sle.posting_date, sle.posting_time,
               sle.item, sle.warehouse, sle.batch,
               sle.voucher_type, sle.voucher_no,
               sle.qty_change, sle.balance_qty, sle.valuation_rate,
               sle.is_cancelled, sle.owner AS creator,
               sle.creation, sle.modified, sle.modified_by, sle.remarks
        FROM `tabSC Stock Ledger Entry` sle
        WHERE {where}
        ORDER BY sle.posting_date DESC, sle.creation DESC
        LIMIT %(lim)s
    """, {**params, "lim": int(limit)}, as_dict=True)
    return rows

@frappe.whitelist()
def compare_theoretical_vs_actual(item, warehouse=None, batch=None) -> dict:
    """UC-31 step 4: so sánh sum(SLE.qty_change) với current physical count
    (caller phải nhập actual)."""
    conds = ["item = %(item)s", "is_cancelled = 0"]
    params = {"item": item}
    if warehouse:
        conds.append("warehouse = %(wh)s"); params["wh"] = warehouse
    if batch:
        conds.append("batch = %(batch)s"); params["batch"] = batch
    theoretical = flt(frappe.db.sql(f"""
        SELECT COALESCE(SUM(qty_change), 0)
        FROM `tabSC Stock Ledger Entry`
        WHERE {' AND '.join(conds)}
    """, params)[0][0])
    return {"theoretical_qty": theoretical,
            "item": item, "warehouse": warehouse, "batch": batch}
```

## Migration

- New doctypes — `bench migrate` tạo tables tự động
- Không cần data migration

## Test plan — `tests/uc31_test.py`

| Test | Scenario |
|---|---|
| `test_create_investigation_report_draft` | Tạo Draft → status=Draft |
| `test_get_audit_trail_filters_by_item` | get_audit_trail(item=X) → chỉ SLE của item X |
| `test_get_audit_trail_filters_by_period` | period_start/end → chỉ SLE trong khoảng |
| `test_get_audit_trail_filters_by_user` | user=Y → chỉ SLE creator=Y |
| `test_compare_theoretical_vs_actual` | Item có SLE +100/-30 → theoretical=70 |
| `test_detect_anomalies_large_qty_change` | SLE qty=10000 → finding type=Large Qty Change |
| `test_detect_anomalies_cancelled_no_remarks` | is_cancelled=1, remarks rỗng → High severity finding |
| `test_detect_anomalies_balance_mismatch` | SLE có balance_qty sai vs cumulative → Critical |
| `test_lock_user_disables_account` | lock_user(user) → User.enabled=0 |
| `test_lock_user_rejects_admin` | lock_user("Administrator") → throw |
| `test_create_system_error_adjustment` | create_system_error_adjustment(qty=5) → SR draft với reason 'System Error' |
| `test_submit_investigation_sets_approved` | submit → status=Resolved + approved_by set |
| `test_verify_audit_integrity_count` | Đếm Version rows cho 1 doc → trả đúng count |

## Out-of-scope

- Real-time fraud detection / ML-based anomaly
- Hardware HSM digital signature (chỉ placeholder)
- Cross-tenant audit (SupplyCore single-tenant)
- IP geolocation lookup

## File changes

1. `supplycore/m10_traceability/UC-31_FLOW.md` — this file
2. `supplycore/m10_traceability/doctype/sc_investigation_report/sc_investigation_report.json + .py + __init__.py`
3. `supplycore/m10_traceability/doctype/sc_investigation_finding/sc_investigation_finding.json + __init__.py`
4. `supplycore/m10_traceability/api/investigation.py`
5. `supplycore/tests/uc31_test.py`
