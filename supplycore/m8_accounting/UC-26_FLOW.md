# UC-26 — Báo cáo Tài chính Vật tư — Flow & Implementation

**Module:** M8 Accounting
**APIs:** `m8_accounting/api/financial_reports.py` (NEW)
**Date:** 2026-05-11
**Source:** Phase 1 / UseCase_SupplyCore_v2.0.md UC-26

## Audit hiện trạng

| Spec | Trước | Sau UC-26 |
|---|---|---|
| 1. Mở Reports / Dashboard | ✓ M11 dashboard + KPI API existing | ✓ thêm 4 reports M8 |
| 2. **Chọn loại: Tồn kho / Công nợ / Chi phí / BHYT** | Partial: existing UC-14 stock balance; ✗ AP aging/Cost/BHYT settlement | ✓ 4 APIs |
| 3. Filter kỳ/kho/nhóm/NCC | Partial: từng API | ✓ unified filters |
| 4. Tổng hợp từ GL Entry + SLE | ✓ data source available | ✓ |
| 5. Hiển thị + biểu đồ | Backend API trả data; UI/chart defer JS | ✓ data API ready |
| 6. Export Excel/PDF/print | ✓ Frappe Report Builder builtin | Document |
| 2a. **Báo cáo BHYT theo N01-N09 + khoa** | ✗ | ✓ `bhyt_settlement_report()` |
| 5a. **Drill-down voucher details** | ✗ | ✓ `get_voucher_details()` |
| Ngoại lệ: **Chưa close kỳ → cảnh báo tạm thời** | ✗ | ✓ `check_period_finalized()` + flag in response |

## Actor

- Kế toán / Quản lý / Lãnh đạo

## Pre-condition

- Có giao dịch trong kỳ (SC PI/PE/SLE/PD)

## Luồng chính

| Bước | Action |
|---|---|
| 1 | Mở `/app/sc-purchase-invoice` Report Builder HOẶC gọi API trực tiếp |
| 2 | Chọn API: `inventory_value_report` / `ap_aging_report` / `period_cost_report` / `bhyt_settlement_report` |
| 3 | Truyền filters: `from_date`, `to_date`, `warehouse`, `item_group`, `supplier`, `bhyt_group`, `department` |
| 4 | API query GL Entry / SLE / PI / PE / SC Patient Dispensing |
| 5 | Response: rows + summary + `period_finalized` flag (true nếu kỳ đã close) |
| 6 | UI/Frappe Report Builder export Excel/CSV/PDF builtin |

## Luồng thay thế

### 2a — BHYT settlement report

`bhyt_settlement_report(from_date, to_date, department=None, bhyt_group=None)`:
- Aggregate SC PD Item theo (bhyt_group, department):
  - total_dispensed_qty, total_cost, total_bhyt_covered, total_patient_pays, total_ceiling_overage
- Filter: kỳ + optional department + optional bhyt_group
- Return: list rows + summary totals per N01-N09 + by department

### 5a — Drill-down

`get_voucher_details(voucher_type, voucher_no)`:
- Trả tóm tắt voucher (header) + line items + linked vouchers
- Support: SC Purchase Invoice, SC Payment Entry, SC GL Entry, SC Stock Ledger Entry

## Xử lý ngoại lệ

### Kỳ chưa close → cảnh báo tạm thời

`check_period_finalized(as_of_date)`:
- Check có Draft documents (PI, PE, PD) với date trong kỳ chưa submit → period NOT finalized
- Set flag `period_finalized=False` trong response + `pending_drafts` count
- Báo cáo vẫn hiển thị nhưng đánh dấu "tạm thời".

## Field changes

KHÔNG — chỉ thêm API module.

## Error codes mới

KHÔNG — chỉ read-only reports.

## API — `m8_accounting/api/financial_reports.py` (NEW)

```python
@frappe.whitelist()
def inventory_value_report(warehouse=None, item_group=None,
                            as_of_date=None, limit=500) -> dict:
    """Tồn kho giá trị: aggregate SLE qty × avg_rate per (item, warehouse, batch)."""
    ...

@frappe.whitelist()
def ap_aging_report(supplier=None, as_of_date=None, limit=500) -> dict:
    """Công nợ NCC aging: bucket 0-30/31-60/61-90/>90 ngày."""
    ...

@frappe.whitelist()
def period_cost_report(from_date, to_date, item_group=None,
                       warehouse=None) -> dict:
    """Chi phí vật tư kỳ: tổng PI grand_total + breakdown theo item_group."""
    ...

@frappe.whitelist()
def bhyt_settlement_report(from_date, to_date, department=None,
                            bhyt_group=None) -> dict:
    """Quyết toán BHYT theo N01-N09 + khoa phòng."""
    ...

@frappe.whitelist()
def get_voucher_details(voucher_type, voucher_no) -> dict:
    """Drill-down: chi tiết voucher gốc."""
    ...

@frappe.whitelist()
def check_period_finalized(from_date, to_date) -> dict:
    """Check có Draft documents trong kỳ → period chưa finalized."""
    ...
```

## Test plan — `tests/uc26_test.py`

| Test | Scenario |
|---|---|
| `test_inventory_value_basic` | SLE +100 × rate 1000 → inventory_value_report trả qty=100, value=100k |
| `test_inventory_value_filter_warehouse` | 2 warehouses → filter trả 1 |
| `test_ap_aging_buckets` | PI overdue 45d, 75d, 100d → bucket 31-60, 61-90, >90 |
| `test_period_cost_summary` | 2 PI trong kỳ → total cost = sum |
| `test_period_cost_filter_item_group` | filter item_group → chỉ trả items thuộc group |
| `test_bhyt_settlement_aggregates_by_group` | 2 PD với BHYT khác group → settlement có 2 rows |
| `test_bhyt_settlement_filter_department` | filter department → chỉ trả PD của department đó |
| `test_get_voucher_details_pi` | PI submitted → drill returns header + items |
| `test_check_period_finalized_draft_present` | Draft PI trong kỳ → finalized=False + count>0 |
| `test_check_period_finalized_all_submitted` | Không Draft → finalized=True |

## Out-of-scope

- Custom dashboards / charts (defer JS)
- Cross-period comparison reports (defer)
- PDF rendering custom template (Frappe Print Format builtin)
- Period close / finalize doctype (defer Phase 2)

## File changes

1. `supplycore/m8_accounting/UC-26_FLOW.md` — this file
2. `supplycore/m8_accounting/api/__init__.py` — package marker
3. `supplycore/m8_accounting/api/financial_reports.py` — 6 APIs
4. `supplycore/tests/uc26_test.py` — 10 test scenarios
