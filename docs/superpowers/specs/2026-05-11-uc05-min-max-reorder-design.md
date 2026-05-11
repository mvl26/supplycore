# UC-05 — Thiết lập Mức Tồn Kho Min / Reorder / Max — Design

**Module:** M2 Planning
**Date:** 2026-05-11
**Status:** Approved for implementation
**Go-live target:** 2026-05-31
**Source:** Phase 1 / `03_Use-Case-Diagram-and-Descriptions/UseCase_SupplyCore_v2.0.md` UC-05

## 1. Context & Gap

**Hiện trạng (2026-05-11):**

- `SC Item` chỉ có `safety_stock` (Float) + `lead_time_days` (Int default 30) ở mức item.
- M11 `_scan_low_stock` trigger dựa trên `safety_stock` (item-level, không phân biệt kho).
- Không có `reorder_level`, `max_stock`, `standard_order_qty` (EOQ), không có per-warehouse override.
- UC-05 trong `m2_planning/UC_TEST.md` ghi status "✅ OK" nhưng chỉ ~30% spec Phase 1.

**Spec Phase 1 yêu cầu:**

- 4 ngưỡng: Safety Stock, Reorder Level, Max Stock, EOQ
- Lead time trung bình từ NCC
- Per-warehouse configuration
- Validate `min < reorder < max`
- Auto alert khi tồn ≤ Reorder Level
- Bulk import Excel
- Cảnh báo khi lead time = 0

**Lưu ý kiến trúc:** Spec Phase 1 ghi "lưu vào ERPNext Reorder Level" — đã shift kiến trúc bỏ ERPNext (2026-05-07). Storage thực tế là `SC Item` + child table `SC Item Reorder`.

## 2. Design decisions (đã chốt với user)

| # | Quyết định | Lý do |
|---|---|---|
| 1 | Hybrid: item-level default + per-warehouse override optional | Most items dùng default, chỉ critical items config per-warehouse |
| 2 | Lead time chỉ item-level (giữ `lead_time_days`) | Đơn giản, đủ cho Phase 1; per-supplier defer |
| 3 | Alert `low_stock` giữ trigger=`safety_stock`; `reorder_level` chỉ dùng cho UC-06 procurement plan + reference | Không break UC-07 alert→MR action hiện có |
| 4 | EOQ = manual input `standard_order_qty` (Float) | Bệnh viện không có đủ data demand/cost để auto-calc; defer Phase 2 |
| 5 | Excel import = Frappe Data Import builtin | 0 dòng code custom; pattern chuẩn Frappe |
| 6 | Data model: child table `SC Item Reorder` trên SC Item (Approach A) | Khớp pattern repo, gắn chặt form, lookup nhanh |

## 3. Data model

### 3.1 Field mới trên `SC Item`

| Field | Type | Default | Note |
|---|---|---|---|
| `reorder_level` | Float | 0 | Điểm tái đặt hàng |
| `max_stock` | Float | 0 | Mức tồn tối đa |
| `standard_order_qty` | Float | 0 | EOQ manual — qty đặt chuẩn |
| `reorder_levels` | Table → `SC Item Reorder` | – | Per-warehouse override |

Đặt trong section `section_planning` đã có, cùng `safety_stock` + `lead_time_days`.

### 3.2 Child DocType `SC Item Reorder` (istable=1)

Location: `supplycore/m2_planning/doctype/sc_item_reorder/`

| Field | Type | Reqd | Note |
|---|---|---|---|
| `warehouse` | Link `SC Warehouse` | ✓ | Unique per parent |
| `safety_stock` | Float | – | Override item-level, 0 = fallback |
| `reorder_level` | Float | – | Override item-level, 0 = fallback |
| `max_stock` | Float | – | Override item-level, 0 = fallback |
| `standard_order_qty` | Float | – | Override item-level, 0 = fallback |

### 3.3 Form layout (SC Item)

```
section_planning
├── safety_stock          (col 1)
├── reorder_level         (col 1) [NEW]
├── max_stock             (col 1) [NEW]
├── column_break
├── standard_order_qty    (col 2) [NEW, label "Số lượng đặt hàng chuẩn (EOQ)"]
├── lead_time_days        (col 2)
├── section_break "Override theo kho" (collapsible, depends_on=eval:!doc.__islocal)
└── reorder_levels         (table SC Item Reorder)
```

Section "Override theo kho" collapsible — mặc định ẩn.

## 4. Validation (chạy trong `SC Item.validate`)

### 4.1 Item-level fields

- Tất cả 4 ngưỡng + `lead_time_days` ≥ 0 → else `SC-E-NEGATIVE` "Giá trị không được âm"
- Nếu `max_stock > 0`: phải `safety_stock ≤ reorder_level ≤ max_stock` → else `SC-E-MIN-MAX` "Phải thỏa Safety ≤ Reorder ≤ Max"
- Nếu `lead_time_days == 0`: msgprint warning màu vàng "Lead time = 0 — nên cập nhật giá trị > 0" (warn only, không throw — UX không cản nhập liệu)

### 4.2 Child table `reorder_levels`

- `warehouse` unique trong table → else `SC-E-DUPLICATE-WAREHOUSE` "Kho {wh} đã có override — không trùng"
- Mỗi row, các field set (> 0): cùng quy tắc safety ≤ reorder ≤ max (`SC-E-MIN-MAX`)
- Field bỏ trống (= 0) → fallback item-level khi lookup, không validate

### 4.3 Error codes mới

| Code | Trigger | Message VN |
|---|---|---|
| `SC-E-NEGATIVE` | Bất kỳ ngưỡng / lead_time < 0 | "Giá trị không được âm" |
| `SC-E-MIN-MAX` | `max_stock>0` AND không thỏa safety ≤ reorder ≤ max | "Phải thỏa Safety ≤ Reorder ≤ Max" |
| `SC-E-DUPLICATE-WAREHOUSE` | Child table 2 row cùng warehouse | "Kho {wh} đã có override — không trùng" |

## 5. Lookup helper

**Location:** `supplycore/m2_planning/reorder.py` (new file)

```python
def get_reorder_thresholds(item: str, warehouse: str | None = None) -> dict:
    """
    Returns dict with keys:
      safety_stock, reorder_level, max_stock, standard_order_qty, lead_time_days

    Precedence (per field): child row khớp warehouse (nếu warehouse truyền vào và
    field >0) > item-level (nếu >0) > 0.

    Single source of truth for UC-06, UC-07, M11 alert scanner.
    """
```

Behavior:

- Nếu `warehouse=None` → trả về item-level only
- Per-field fallback: row override field=0 → fallback item-level (không phải all-or-nothing)
- Cache theo `(item, warehouse)` trong request (frappe.local cache pattern)

## 6. Consumer wiring

### 6.1 M11 alert `_scan_low_stock` (m11_dashboard/tasks.py)

Giữ trigger = `safety_stock` (decision 3). Hỗ trợ per-warehouse override.

**Logic mới:** 2 queries merged:

1. **Query 1** — Items có override row với `safety_stock > 0`: scan per (item, warehouse) với JOIN SLE filter theo warehouse.
2. **Query 2** — Items KHÔNG có override row: fallback item-level (logic cũ).

Pseudocode:

```python
def _scan_low_stock(rule) -> int:
    rows_wh = _scan_low_stock_per_warehouse()  # NEW
    rows_item = _scan_low_stock_item_level()   # existing logic + WHERE NOT EXISTS override
    return _create_alerts_dedup(rule, rows_wh + rows_item, ...)
```

Alert message: `{item_name}: tồn {qty} < safety {safety}` (+ ` @ {warehouse}` nếu per-warehouse).
Alert reference giữ `("SC Item", item)` để slice 2 alert→action MR vẫn fire đúng.

### 6.2 UC-06 Procurement Plan `auto_load_reorder_items`

Whitelisted method trên `procurement_plan.py`:

```python
@frappe.whitelist()
def auto_load_reorder_items(plan_name: str, warehouse: str) -> dict:
    """
    Quét tất cả SC Item:
      - get_reorder_thresholds(item, warehouse) → thresholds
      - current_qty = SLE sum tại warehouse
      - if reorder_level > 0 AND current_qty ≤ reorder_level:
          suggested_qty = standard_order_qty (nếu >0) else max(0, max_stock - current_qty)
          append vào plan.items
    Returns: {items_added: int, items_skipped: int}
    """
```

JS button trên Procurement Plan form: "Auto-load Items" → gọi method này.

### 6.3 UC-07 MR auto-suggest qty (out-of-scope, defer)

Không trong scope UC-05 — chỉ note: helper `get_reorder_thresholds()` có thể consume sau khi cần.

## 7. Excel import (Frappe Data Import builtin — zero code)

**Quy trình end-user:**

1. `/app/data-import/new`
2. Document Type = `SC Item`, Import Type = `Update Existing Records`
3. Download template Excel
4. Cols: `id, safety_stock, reorder_level, max_stock, standard_order_qty, lead_time_days`
5. Upload → Frappe gọi `validate()` parent → 4 validate rule fire tự động → lỗi từng row vào import log

**Per-warehouse override import:**

- Document Type = `SC Item Reorder` (child)
- Cols: `parent, parenttype="SC Item", parentfield="reorder_levels", warehouse, safety_stock, reorder_level, max_stock, standard_order_qty`

**Permissions:**

- Frappe Data Import default = `System Manager` only.
- Giữ default → IT/admin handle bulk import giúp storekeeper khi cần. Adjust sau nếu UAT phàn nàn.

**Template Excel mẫu:** defer — không lưu trong repo. Add `docs/import_templates/` sau khi UAT yêu cầu.

## 8. Permissions matrix

| Role | Read SC Item | Write threshold fields | Bulk Data Import |
|---|---|---|---|
| SC Storekeeper | ✓ | ✓ | – (default System Manager only) |
| SC Manager | ✓ | ✓ | – |
| SC Accountant | ✓ | – | – |
| SC Doctor | ✓ | – | – |

## 9. Migration & backward compat

- Field mới có default = 0 → SC Item cũ không gãy.
- Patch `supplycore/patches/v0_2/init_uc05_fields.py`:
  - `frappe.reload_doc("supplycore", "doctype", "sc_item")`
  - `frappe.reload_doc("m2_planning", "doctype", "sc_item_reorder")`
  - **Không backfill dữ liệu** — user nhập / import qua Frappe Data Import.
- Register patch trong `supplycore/patches.txt`.

## 10. Test plan

### 10.1 Unit tests — `supplycore/tests/uc05_test.py` (file đã có untracked, sẽ filled)

| Test | Assertion |
|---|---|
| `test_negative_threshold_rejected` | set `safety_stock=-1` → throw `SC-E-NEGATIVE` |
| `test_min_max_inversion_rejected` | safety=10, reorder=5, max=20 → throw `SC-E-MIN-MAX` |
| `test_valid_thresholds_pass` | safety=5, reorder=10, max=20 → save OK |
| `test_lead_time_zero_warns_not_throws` | lead_time=0 → msgprint warning, save OK |
| `test_child_warehouse_duplicate_rejected` | 2 row cùng WH-CENTRAL → throw `SC-E-DUPLICATE-WAREHOUSE` |
| `test_get_reorder_thresholds_fallback` | item có item-level safety=10, no override → helper trả 10 |
| `test_get_reorder_thresholds_override` | item có override safety=20 cho WH-X → helper trả 20 |
| `test_get_reorder_thresholds_partial_override` | row override chỉ set safety, các field khác trống → fallback item-level cho field trống |

### 10.2 Integration tests — extend `supplycore/tests/smoke_m2.py`

| Test | Assertion |
|---|---|
| `test_low_stock_alert_item_level` | tồn item < safety (no override) → `_scan_low_stock` tạo 1 SC Alert |
| `test_low_stock_alert_per_warehouse` | item có override WH-X safety=50, qty WH-X=30 → alert chỉ tạo cho (item, WH-X) |
| `test_low_stock_alert_no_override_no_change` | regression: items không có override hành xử y như trước |
| `test_procurement_plan_auto_load_reorder` | UC-06 button: item dưới reorder_level → load vào plan với suggested qty |

### 10.3 Test runner

```bash
cd /home/hoangvietyeuem/frappe-bench
bench --site <site> run-tests --app supplycore --module supplycore.tests.uc05_test
bench --site <site> run-tests --app supplycore --module supplycore.tests.smoke_m2
```

## 11. Rollout order (file changes)

1. `supplycore/m2_planning/doctype/sc_item_reorder/` — NEW child doctype (`__init__.py`, json, py)
2. `supplycore/supplycore/doctype/sc_item/sc_item.json` — 3 fields + table field + section "Override theo kho"
3. `supplycore/supplycore/doctype/sc_item/sc_item.py` — validate logic + 3 error codes
4. `supplycore/m2_planning/reorder.py` — NEW helper `get_reorder_thresholds()`
5. `supplycore/m11_dashboard/tasks.py` — update `_scan_low_stock` (2-query merge)
6. `supplycore/m2_planning/doctype/procurement_plan/procurement_plan.py` — `auto_load_reorder_items()` whitelisted
7. `supplycore/m2_planning/doctype/procurement_plan/procurement_plan.js` — button "Auto-load Items"
8. `supplycore/patches/v0_2/init_uc05_fields.py` + register `supplycore/patches.txt`
9. `supplycore/tests/uc05_test.py` — unit tests
10. `supplycore/tests/smoke_m2.py` — integration tests (extend)
11. `supplycore/m2_planning/UC_TEST.md` — rewrite UC-05 section (detailed format like m1_contract)
12. `docs/UC_COVERAGE.md` — flip UC-05 status row

## 12. UC_TEST.md rewrite plan

Section UC-05 trong `m2_planning/UC_TEST.md` rewrite theo format chi tiết m1_contract:

- Test scenario (6 bước): mở SC Item → set 4 thresholds + lead_time → optional override per kho → save → Excel import → verify procurement plan auto-load
- Luồng thay thế: Excel import qua Frappe Data Import (3a)
- Negative tests: SC-E-NEGATIVE, SC-E-MIN-MAX, SC-E-DUPLICATE-WAREHOUSE
- Xử lý ngoại lệ: lead_time = 0 warning
- Checklist 10 item Pass/Fail
- Status: ✅ OK (enhanced 2026-05-11 — full per-warehouse override + 4 thresholds + EOQ)

## 13. Verification gate (definition of done)

- [ ] `bench migrate` chạy sạch (patch apply)
- [ ] `bench run-tests --module supplycore.tests.uc05_test` PASS
- [ ] `bench run-tests --module supplycore.tests.smoke_m2` PASS (no regression)
- [ ] Manual: tạo 1 SC Item, set 4 thresholds, save → form load OK
- [ ] Manual: Frappe Data Import 1 file Excel update 5 items → import log success
- [ ] Manual: alert rule `low_stock`, qty item < safety → `bench execute supplycore.m11_dashboard.tasks.run_alert_scan` → alert tạo đúng
- [ ] Manual: per-warehouse override → alert chỉ fire cho warehouse có safety > current_qty

## 14. Out-of-scope (defer Phase 1.1+)

- Dedicated "Reorder Level Manager" screen (dùng SC Item list + Report Builder)
- Auto-EOQ formula calculation
- Lead time per-supplier override
- Custom bulk import UI (dùng Frappe Data Import)
- Excel template mẫu lưu repo
- Cấp quyền SC Storekeeper truy cập Data Import (giữ System Manager only)
