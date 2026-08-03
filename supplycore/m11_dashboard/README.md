# M11 — Dashboard & Alert Center

Module quản lý **Executive Dashboard** (KPI realtime) + **SC Alert Rule** (rule-based alerts) + **SC Alert** (alert log + workflow xử lý).

## DocTypes

| DocType | Loại | Mô tả |
|---|---|---|
| `SC Alert Rule` | Master | Cấu hình rule: type, threshold, recipients |
| `SC Alert` | Log | Instance alert đã trigger, có workflow resolve/snooze |

## Naming series

- `SC-AR-#####` — Alert Rule
- `SC-ALR-YYYY-########` — Alert instance

## 6 Executive KPIs (theo SCR-01)

```
GET /api/method/supplycore.api.kpi.get_executive_dashboard?period=this_month

Returns {
  "kpis": {
    "stock_value":      Tổng giá trị tồn kho (SUM SLE qty × valuation)
    "monthly_cost":     Chi phí mua hàng kỳ (SUM PI grand_total)
    "ap_outstanding":   Công nợ NCC còn phải trả (SUM PI outstanding)
    "pending_pos":      Số PO chờ duyệt/giao
    "expiring_soon":    Số lô sắp hết hạn ≤30 ngày (có stock)
    "low_stock_items":  Số items dưới safety_stock
  },
  "top_items":     [Top 5 items by consumption value],
  "open_alerts":   {Critical/Warning/Info breakdown},
  "open_alerts_total": int
}
```

Period: `today` / `this_week` / `this_month` (default) / `this_quarter` / `this_year`.

## Warehouse Dashboard (cho SK)

```
GET /api/method/supplycore.api.kpi.get_warehouse_dashboard?warehouse=X

Returns {
  warehouse, stock_qty_total, expiring_batches,
  pending_transfer_requests
}
```

## Alert Rule types

| Type | Threshold meaning | Quét |
|---|---|---|
| `expiring_batch` | days threshold (default 30) | SC Batch.expiry_date trong [today, today+threshold] có stock |
| `contract_expiring` | days threshold (default 30) | Framework Contract.valid_to gần hết hạn |
| `fc_remaining_low` | % threshold (default 20) | FC.remaining_value / total_value ≤ threshold |
| `low_stock` | (no threshold) | SC Item.qty < safety_stock |
| `overdue_payment` | (no threshold) | SC PI.due_date < today + outstanding > 0 |
| `qc_pending` | days threshold (default 1) | SC PR.qc_status=Pending quá X ngày |
| `recall_outstanding` | (no threshold) | SC Recall Notice.status=Issued/In Progress, outstanding > 0 |

## Luồng hoạt động

```
[1] Setup SC Alert Rule (1 lần)
    /app/sc-alert-rule/new
    - title, alert_type, severity, threshold_value, frequency
    - recipient_roles (vd "SupplyCore Manager,SupplyCore Storekeeper")

[2] Daily scheduler m11_dashboard.tasks.scan_alerts
    Cho mỗi rule enabled:
      Query DB theo logic rule.alert_type
      Tạo SC Alert mới (deduped: same rule + reference + open + 7 ngày)
    Update rule.last_triggered_at + last_alert_count

[3] User mở /app/sc-alert?resolved=0 — Alert Center
    - Filter theo severity (Critical/Warning/Info)
    - Click reference_doctype/name → link đến doc gốc
    - Mark resolved + resolution_action
    - Snooze (set snooze_until)

[4] Daily scheduler m11_dashboard.tasks.send_daily_kpi
    Snapshot 6 KPIs + open_alerts breakdown
    Email đến SupplyCore Executive + Manager
```

## Coverage Phase 1

| BR / UC | Status |
|---|---|
| UC-32 Executive Dashboard tổng thể | ✓ get_executive_dashboard 6 KPIs + top items + open alerts |
| UC-33 Cấu hình cảnh báo tự động | ✓ SC Alert Rule với 7 alert types |
| UC-34 Xem + xử lý cảnh báo | ✓ SC Alert workflow resolved/snooze + reference link |
| Daily KPI email cho EXEC | ✓ scheduler send_daily_kpi |

## API endpoints

```
GET  /api/method/supplycore.api.kpi.get_executive_dashboard?period=this_month
GET  /api/method/supplycore.api.kpi.get_warehouse_dashboard?warehouse=X
```

## Phase 3 mockup compliance

Theo SCR-01 Executive Dashboard (Phase 3 design):
- 6 KPI cards với màu RAG (Critical=red / Warning=orange / OK=green)
- Top 5 items table
- Open alerts badge per severity
- Period filter (today/this_month/this_quarter)

Frontend (Frappe Workspace + Number Cards) — defer; v1 chỉ cung cấp API JSON.

## Alert → Action (slice 2 — 2026-05-08)

Mỗi alert có thể trigger 1 action cụ thể tuỳ `alert_type`:

| Alert type | Button trên Alert form | Action method | Tạo doc |
|---|---|---|---|
| `expiring_batch` | "Chuyển vào Kho Cách ly" | `action_quarantine_batch` | SC Stock Entry (Material Transfer) |
| `low_stock` | "Tạo Material Request bổ sung" | `action_create_material_request` | SC Material Request (qty=safety×2) |
| `overdue_payment` | "Tạo Payment Entry" | `action_create_payment` | SC Payment Entry |
| Khác | "Đánh dấu đã xử lý" / "Bỏ qua" | (resolve thủ công) | — |

Sau action:
- `Alert.action_taken=1`, `action_doctype/action_name` link đến doc đã tạo
- `Alert.resolved=1`, `resolution_action='Acted Upon'`
- `Alert.resolved_by/resolved_at` auto set
- Idempotent: gọi action 2 lần → throw "Đã có action"

Test: `tests/smoke_alert_action.py` — verify expiring_batch + low_stock đầy đủ.

## Vận hành

```
1. Setup rules (1 lần):
   /app/sc-alert-rule/new
   - "Lô hết hạn 30 ngày": alert_type=expiring_batch, threshold=30, severity=Warning
   - "HĐK hết hạn 30 ngày": alert_type=contract_expiring, threshold=30, severity=Warning
   - "Tồn dưới safety": alert_type=low_stock, severity=Critical
   - "PI quá hạn TT": alert_type=overdue_payment, severity=Critical

2. Daily 02:00 (scheduler) tự scan + tạo Alert + email KPI

3. User truy cập:
   - /app/sc-alert?resolved=0 — alert center
   - api/method/supplycore.api.kpi.get_executive_dashboard — JSON cho dashboard UI custom
```

## Integration với module khác

**Incoming events (module này nhận trigger từ):**
- Mọi module SC* (qua SQL query trên các table)
- M3 PR.qc_status, M1 FC.valid_to, M5 Batch.expiry_date, M8 PI.due_date, …

**Outgoing events (module này trigger / cung cấp data cho):**
- API `get_executive_dashboard` → 6 KPI cho UI dashboard
- API `get_warehouse_dashboard` → KPI per warehouse cho SK
- Daily scheduler `scan_alerts` → SC Alert (7 alert types, dedup)
- Daily scheduler `send_daily_kpi` → email EXEC + MGR
- Phase 1.1+: alert action button (low_stock → tạo TR, expiring → tạo write-off SE)

Xem [`FLOW.md`](../../FLOW.md) cho sơ đồ tổng thể.
