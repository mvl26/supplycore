# UC-32 — Dashboard Điều hành Tổng thể — Flow & Implementation

**Module:** M11 Dashboard & Cảnh báo
**API chính:** `supplycore.api.kpi`
**Date:** 2026-05-11
**Source:** Phase 1 / UseCase_SupplyCore_v2.0.md UC-32

## Audit hiện trạng

| Spec | Trước UC-32 | Sau UC-32 |
|---|---|---|
| 1. Login → Dashboard theo role | ⚠ Frappe Workspace role-based, không có code custom | ✓ `get_dashboard_for_role(role)` |
| 2. **KPI widgets** (stock_value, monthly_cost, ap_outstanding, pending_pos) | ✓ `get_executive_dashboard()` | ✓ + drill_down URLs + last_updated_at |
| 3a. **Top 10 vật tư tiêu thụ** | ⚠ chỉ LIMIT 5 | ✓ LIMIT 10 + filter period |
| 3b. **Chi phí theo tháng (xu hướng)** | ✗ | ✓ `get_monthly_cost_trend(months=12)` |
| 4. **Bảng cảnh báo: Hết hàng + Sắp hết hạn + HĐ sắp hết + PO chưa nhận** | ⚠ thiếu HĐ + PO | ✓ thêm `contract_expiring_30d` + `po_overdue_count` |
| 5. **Drill-down từ widget** | ✗ | ✓ `drill_down` URL map per widget |
| 6. **Filter Period + Warehouse + Department** | ⚠ chỉ period | ✓ warehouse + department params |
| 6a. **Export PDF snapshot** | ✗ | ✓ `get_dashboard_snapshot_pdf_data()` |
| 1a. Role khác → widget khác | ✗ | ✓ `get_dashboard_for_role()` per-role widget list |
| **Cache 5 phút** | ✗ | ✓ `frappe.cache().get_value/set_value` 300s TTL |
| **Ngoại lệ: timestamp cập nhật cuối** | ✗ | ✓ `last_updated_at` + `cached` flag trong response |

## Actor

- SC-EXECUTIVE (chính), SC-MANAGER

## Pre-condition

- Có dữ liệu hoạt động (SLE, PI, PO, FC, Batch, Alert)

## Luồng chính

| Bước | Action | Implementation |
|---|---|---|
| 1 | Login → Frappe redirect → /app/dashboard hoặc role workspace | Frappe Workspace |
| 2 | Trang dashboard load → call `get_dashboard_for_role(role)` | Server-side |
| 3 | Server check cache `dashboard:{role}:{period}:{wh}:{dept}` | Redis cache 300s |
| 4 | Nếu cache hit → return; miss → query + cache | Lazy populate |
| 5 | Response: kpis + top_items + alerts + trends + drill_down + last_updated_at | JSON payload |
| 6 | User click widget → navigate đến `drill_down[widget].url` | URL map |
| 7 | User thay filter → re-call API → cache mới key | Stateless |

## Luồng thay thế

### 1a — Role khác

`get_dashboard_for_role(role)`:
- **SupplyCore Executive**: tất cả KPI + trends + alerts
- **SupplyCore Manager**: KPI + alerts (skip ap_outstanding nếu không có Accountant role)
- **SupplyCore Accountant**: ap_outstanding + monthly_cost + invoices breakdown
- **SupplyCore Storekeeper**: per-warehouse view (`get_warehouse_dashboard()`)
- **Pharmacy Officer**: dispensing-focused widgets
- Default (role không match): basic KPIs

### 6a — Export PDF Snapshot

`get_dashboard_snapshot_pdf_data()` trả structure đầy đủ + signature placeholder cho Print Format. UI render qua Frappe Print/HTML template.

## Xử lý ngoại lệ

### Dữ liệu chưa tổng hợp

- Response luôn có `last_updated_at` (timestamp tính lúc cache miss)
- Khi cache hit → `last_updated_at` = thời điểm cache; `cached=True`
- UI hiển thị "Cập nhật lúc {last_updated_at}" + nút Refresh để force re-query

## Field changes

KHÔNG có doctype thay đổi — chỉ extend API.

## Error codes

- `SC-E-DSH-INVALID-PERIOD` — period không thuộc {today, this_week, this_month, this_quarter, this_year}
- `SC-E-DSH-INVALID-WAREHOUSE` — warehouse không tồn tại
- `SC-E-DSH-INVALID-ROLE` — role không phải supplycore role

## Logic — `supplycore/api/kpi.py` (extensions)

```python
CACHE_TTL = 300  # 5 phút

def _cache_key(scope, params):
    parts = [str(scope)] + [f"{k}={v}" for k, v in sorted(params.items()) if v]
    return "uc32:" + ":".join(parts)

def _cache_get(key):
    val = frappe.cache().get_value(key)
    if val is not None:
        val["cached"] = True
    return val

def _cache_set(key, value):
    value["cached"] = False
    frappe.cache().set_value(key, value, expires_in_sec=CACHE_TTL)
    return value

# Extension: thêm warehouse + department filter + cache + drill-down
@frappe.whitelist()
def get_executive_dashboard(period: str = "this_month",
                             warehouse=None, department=None,
                             force_refresh: int = 0) -> dict:
    """Mở rộng theo UC-32: filter, drill-down, cache, role-aware FC alerts."""
    key = _cache_key("exec", {"p": period, "wh": warehouse, "d": department})
    if not int(force_refresh or 0):
        cached = _cache_get(key)
        if cached:
            return cached
    # ... (existing query + new filters)
    payload = {...}
    return _cache_set(key, payload)

@frappe.whitelist()
def get_monthly_cost_trend(months: int = 12) -> list:
    """Trả [{month: '2026-05', cost: 12345}] 12 tháng gần nhất."""
    ...

@frappe.whitelist()
def get_dashboard_for_role(role: str = None) -> dict:
    """Role-aware widget list. Default: lấy role chính của session user."""
    if not role:
        user_roles = set(frappe.get_roles(frappe.session.user))
        for r in ("SupplyCore Executive", "SupplyCore Manager",
                   "SupplyCore Accountant", "SupplyCore Storekeeper",
                   "Pharmacy Officer"):
            if r in user_roles:
                role = r; break
    ...

@frappe.whitelist()
def get_dashboard_snapshot_pdf_data(period="this_month", warehouse=None) -> dict:
    """UC-32 6a: data cho Frappe Print Format snapshot."""
    ...
```

## Migration

KHÔNG — chỉ API.

## Test plan — `tests/uc32_test.py`

| Test | Scenario |
|---|---|
| `test_get_executive_dashboard_returns_required_keys` | KPIs keys + drill_down + last_updated_at + cached |
| `test_dashboard_cache_hit_returns_cached_true` | Gọi 2 lần — lần 2 `cached=True` |
| `test_dashboard_force_refresh_bypasses_cache` | force_refresh=1 → cached=False |
| `test_dashboard_filter_by_warehouse` | warehouse filter → KPI chỉ tính warehouse đó |
| `test_get_monthly_cost_trend_12_months` | Trả 12 rows với `month` + `cost` |
| `test_top_items_limit_10` | top_items ≤ 10 |
| `test_contract_expiring_30d_in_kpis` | FC valid_to trong 30d → KPI `contract_expiring_30d` > 0 |
| `test_get_dashboard_for_role_executive` | Role Executive → tất cả widgets |
| `test_get_dashboard_for_role_accountant` | Accountant → có ap_outstanding |
| `test_get_dashboard_for_role_storekeeper` | Storekeeper → warehouse view nếu có default_warehouse |
| `test_invalid_period_throws` | period='invalid' → throw SC-E-DSH-INVALID-PERIOD |
| `test_invalid_warehouse_throws` | warehouse='NONEXIST' → throw |
| `test_pdf_snapshot_structure` | Trả kpis + signatures + timestamp keys |
| `test_drill_down_urls_provided` | drill_down có URL cho mỗi KPI key |

## Out-of-scope

- Real-time WebSocket push (defer)
- Cross-org dashboard
- Custom widget per user (user-level personalization)
- ML forecasting

## File changes

1. `supplycore/m11_dashboard/UC-32_FLOW.md` — this file
2. `supplycore/api/kpi.py` — extend với 4 functions + filter/cache + drill-down
3. `supplycore/tests/uc32_test.py` — 14 test scenarios
