# UC-27 — Lập kế hoạch & thực hiện kiểm kê — Flow & Implementation

**Module:** M9 Stocktake
**DocType:** SC Inventory Count Sheet + SC ICS Item (existing)
**Date:** 2026-05-11
**Source:** Phase 1 / UseCase_SupplyCore_v2.0.md UC-27

## Audit hiện trạng

| Spec | Trước | Sau UC-27 |
|---|---|---|
| 1. Tạo lịch: kho + ngày + scope | ✓ count_date + warehouse + count_scope All/Group/Zone | ✓ |
| 2. **In phiếu kiểm kê + ẩn system_qty** | Partial: `hide_system_qty` flag, ✗ print API | ✓ `get_count_sheet_print_data(hide_system=...)` |
| 3-4. Đếm + nhập actual_qty | ✓ row.actual_qty | ✓ |
| 4a. **PDA scan** | ✗ no PDA | N/A (như UC-13 — bệnh viện không có PDA) |
| 5. Tính chênh lệch | ✓ `_compute_variances` | ✓ |
| 6. Đếm lại > ngưỡng (5%) | ✓ `needs_recount` + `recount_actual_qty` | ✓ |
| 6a. **Chênh lệch lớn → đếm lần 3 + Manager** | ✗ chỉ 2 lần đếm | ✓ thêm `third_count_qty` + `manager_witness` reqd |
| 7. Submit → tạo SR | ✓ `make_stock_reconciliation` | ✓ |
| **Gián đoạn → partial save** | ✓ Draft + In Progress status | ✓ thêm `start_counting()` method để set In Progress |

## Actor

- Quản lý (Manager) — tạo lịch + chứng kiến đếm lần 3
- Thủ kho (Storekeeper) — đếm

## Pre-condition

- Có quyền create SC Inventory Count Sheet

## Luồng chính

| Bước | Action |
|---|---|
| 1 | Manager mở `/app/sc-inventory-count-sheet/new`, chọn warehouse + count_date + scope |
| 2 | Auto-load items qua `auto_load_items()`. In phiếu qua `get_count_sheet_print_data()` (hide_system_qty=1 mặc định) |
| 3 | Thủ kho đếm thực tế trên phiếu giấy |
| 4 | Nhập `actual_qty` per row vào UI → click "Start counting" để chuyển status=In Progress |
| 5 | Save → `_compute_variances` tính difference + variance_pct + flag needs_recount |
| 6 | Đếm lại các row needs_recount=1 → nhập `recount_actual_qty` |
| 6a | Nếu vẫn chênh > threshold sau recount → nhập `third_count_qty` + `manager_witness` (User Manager chứng kiến) |
| 7 | Submit (status=Counted) → click "Tạo Stock Reconciliation" → UC-19 flow |

## Luồng thay thế

### 4a — PDA scan

Không applicable (bệnh viện chưa có PDA — như UC-13). Thay bằng nhập tay qua UI.

### 6a — Chênh lệch lớn → đếm lần 3

Sau recount, nếu `recount_actual_qty` vẫn khác system_qty > threshold:
- Thủ kho nhập `third_count_qty` (lần đếm thứ 3)
- Reqd `manager_witness` (Link User có role Manager) chứng kiến
- `_compute_variances` ưu tiên third_count_qty > recount_actual_qty > actual_qty

## Xử lý ngoại lệ

### Gián đoạn → partial save

ICS Draft state cho phép save từng phần. `start_counting()` set status=In Progress để indicate đang đếm dở. User có thể quay lại sau, complete remaining rows, submit.

## Field changes

### SC ICS Item — ADD

| Field | Type | Note |
|---|---|---|
| `third_count_qty` | Float, non_negative | Lần đếm thứ 3 khi recount vẫn chênh |

### SC Inventory Count Sheet — ADD

| Field | Type | Note |
|---|---|---|
| `manager_witness` | Link User | Manager chứng kiến đếm lần 3 |

## Error codes mới

| Code | Trigger | Message |
|---|---|---|
| `SC-E-ICS-WITNESS-REQUIRED` | Có row với third_count_qty nhưng không có manager_witness | "Đếm lần 3 yêu cầu Manager chứng kiến — chọn 'Manager witness'" |

## Logic — `sc_inventory_count_sheet.py`

### `_compute_variances` extend với third_count

```python
def _compute_variances(self):
    threshold = flt(self.recount_threshold_pct or 5)
    for row in self.items:
        # Priority: third_count > recount > actual
        if row.third_count_qty:
            actual = flt(row.third_count_qty)
        elif row.recount_actual_qty:
            actual = flt(row.recount_actual_qty)
        else:
            actual = flt(row.actual_qty if row.actual_qty is not None else 0)
        row.difference = actual - flt(row.system_qty or 0)
        if flt(row.system_qty or 0) > 0:
            row.variance_pct = abs(row.difference) / flt(row.system_qty) * 100
        else:
            row.variance_pct = 100 if row.difference else 0
        row.needs_recount = 1 if flt(row.variance_pct) > threshold else 0
        row.variance_value = flt(row.difference) * flt(row.valuation_rate or 0)
```

### before_submit guard witness

```python
def before_submit(self):
    has_third_count = any(flt(r.third_count_qty) > 0 for r in self.items)
    if has_third_count and not self.manager_witness:
        frappe.throw(_(
            "SC-E-ICS-WITNESS-REQUIRED: Đếm lần 3 yêu cầu Manager chứng kiến — "
            "chọn 'Manager witness'"
        ))
```

### `start_counting` whitelisted

```python
@frappe.whitelist()
def start_counting(self):
    """UC-27 step 4: chuyển ICS sang In Progress để track partial counting."""
    if self.docstatus != 0:
        frappe.throw(_("Chỉ start khi Draft"))
    self.db_set("status", "In Progress")
    return {"status": "In Progress"}
```

### `get_count_sheet_print_data` whitelisted

```python
@frappe.whitelist()
def get_count_sheet_print_data(self, hide_system_qty: int = None):
    """UC-27 step 2: data in phiếu kiểm kê. Default hide_system_qty
    theo settings (1 = ẩn để tránh bias)."""
    hide = self.hide_system_qty if hide_system_qty is None else int(hide_system_qty)
    items = []
    for r in self.items:
        row_data = {
            "item": r.item, "item_name": r.item_name, "uom": r.uom,
            "batch": r.batch, "bin_location": r.bin_location,
        }
        if not hide:
            row_data["system_qty"] = flt(r.system_qty)
        items.append(row_data)
    return {
        "name": self.name,
        "count_date": str(self.count_date) if self.count_date else "",
        "warehouse": self.warehouse,
        "planned_by": self.planned_by,
        "counted_by": self.counted_by,
        "count_scope": self.count_scope,
        "hide_system_qty": hide,
        "items": items,
        "url": f"/app/sc-inventory-count-sheet/{self.name}",
    }
```

## Migration

- 2 fields mới Frappe tự migrate

## Test plan — `tests/uc27_test.py`

| Test | Scenario |
|---|---|
| `test_ics_create_basic` | Tạo ICS với warehouse + scope All Items → save Draft |
| `test_ics_auto_load_items` | Seed SLE 2 items → auto_load_items → 2 rows |
| `test_ics_snapshot_system_qty` | Tạo ICS với item, save → system_qty auto fill từ SLE |
| `test_ics_compute_variance` | actual_qty=120, system=100 → diff=20, variance_pct=20% |
| `test_ics_needs_recount_flag` | variance_pct=20 > threshold 5 → needs_recount=1 |
| `test_ics_recount_priority` | recount_actual_qty=110 vs actual=120 → diff dùng 110 |
| `test_ics_third_count_priority` | third_count=105 → diff dùng 105 (over recount + actual) |
| `test_ics_third_count_requires_witness` | submit với third_count + no witness → SC-E-ICS-WITNESS-REQUIRED |
| `test_ics_third_count_with_witness_ok` | third_count + witness → submit OK |
| `test_ics_start_counting_sets_status` | start_counting → status=In Progress |
| `test_ics_make_sr` | ICS Counted + diff > 0 → make_stock_reconciliation tạo SR Draft |
| `test_get_count_sheet_print_data_hides_system` | hide=1 → row không có system_qty key |
| `test_get_count_sheet_print_data_shows_system` | hide=0 → row có system_qty |

## Out-of-scope

- PDA barcode scan (no PDA)
- Multi-day counting workflow (chỉ 1 ICS / kỳ)
- Cycle counting automation (defer Phase 2)

## File changes

1. `supplycore/m9_stocktake/UC-27_FLOW.md` — this file
2. `supplycore/m9_stocktake/doctype/sc_ics_item/sc_ics_item.json` — `third_count_qty` field
3. `supplycore/m9_stocktake/doctype/sc_inventory_count_sheet/sc_inventory_count_sheet.json` — `manager_witness` field
4. `supplycore/m9_stocktake/doctype/sc_inventory_count_sheet/sc_inventory_count_sheet.py` — extend _compute_variances + before_submit + 2 methods
5. `supplycore/tests/uc27_test.py` — 13 test scenarios
