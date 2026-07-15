# UC-06 — Lập Kế hoạch Mua hàng Định kỳ — Flow & Implementation

**Module:** M2 Planning
**DocType:** Procurement Plan
**Date:** 2026-05-11
**Source:** Phase 1 / UseCase_SupplyCore_v2.0.md UC-06

## Actor

- Storekeeper / Manager (tạo + submit)
- Manager / Executive (phê duyệt qua docstatus submit)

## Pre-condition

- Có ≥ 3 tháng dữ liệu SC Stock Ledger Entry (consumption history)
- SC Item có `safety_stock` thiết lập (item-level hoặc per-warehouse override — UC-05)

## Luồng chính

| Bước | Hành động user | Hành vi hệ thống |
|---|---|---|
| 1 | Mở `/app/procurement-plan/new`, chọn `period_type` (Monthly/Quarterly/Yearly/Adhoc), `from_date`, `to_date`, `warehouse`, `consumption_lookback_months` (default 3), `safety_stock_factor` (default 20%) | Form load Draft |
| 2 | Click **"Tự nạp danh mục từ lịch sử tiêu thụ"** | `auto_load_items()` tự tính từng item:<br>• `avg_monthly` = SUM(ABS(qty_change)) / N months từ SLE (qty_change < 0)<br>• `current_stock` = SUM(qty_change) tại warehouse<br>• `pending_po_qty` = SUM(qty - received_qty) trên SC PO submitted chưa nhận hết<br>• `target_stock` = avg_monthly × (lead_time/30) × (1 + safety_factor%) + safety_stock<br>• `suggested_qty` = max(0, target_stock - current_stock - pending_po_qty) |
| 3 | Hệ thống fill rows với `planned_qty = suggested_qty` | Bảng items hiển thị |
| 4 | User chỉnh `planned_qty` cho event đặc biệt (lễ, dịch) | `_compute_amounts()` recompute total |
| 5 | User nhập `budget` (ngân sách dự kiến cho kỳ) | Field Currency optional |
| 6 | Save → Submit | `validate()`: nếu `total_estimated_cost > budget` AND `budget > 0` AND `budget_acknowledged=0` → throw `SC-E-BUDGET-EXCEEDED`. `on_submit()`: status=Approved |
| 7 | Sau Submit | Nếu tick `auto_create_mr=1` → `make_material_request()` chạy tự động; nếu không → user click button "Tạo Material Request" thủ công |

## Luồng thay thế

### 2a — Chưa đủ dữ liệu lịch sử

Khi `auto_load_items()` query SLE trả về 0 items (không có item nào có consumption < 0 trong window):
- `msgprint` orange: "Không có dữ liệu tiêu thụ trong N tháng — vui lòng nhập items thủ công"
- User tự append rows vào child table `items` qua UI Frappe

### 5a — Vượt ngân sách

Khi save/submit với `total_estimated_cost > budget`:
- Throw `SC-E-BUDGET-EXCEEDED: Tổng chi phí ({total}) vượt ngân sách ({budget}). Tick "Xác nhận vượt ngân sách" để tiếp tục.`
- User tick field `budget_acknowledged` (Check) → save lại → qua

## Hậu điều kiện

- Procurement Plan `docstatus=1`, `status=Approved`
- Nếu `auto_create_mr=1`: `material_request` link đến SC Material Request mới tạo, `status=Generated`
- Frappe `track_changes=1` audit toàn bộ field changes

## Field additions (so với state hiện tại)

### Procurement Plan parent

| Field | Type | Default | Position |
|---|---|---|---|
| `budget` | Currency (VND) | 0 | section_total, trước `total_estimated_cost` |
| `budget_acknowledged` | Check | 0 | section_total, depends_on `eval:doc.budget>0 && doc.total_estimated_cost>doc.budget` |
| `auto_create_mr` | Check | 0 | section_other, label "Tự tạo Material Request sau Submit" |

### Procurement Plan Item child

| Field | Type | Position |
|---|---|---|
| `pending_po_qty` | Float, read_only | sau `current_stock`, in_list_view |

## Error codes

| Code | Trigger | Message |
|---|---|---|
| `SC-E-BUDGET-EXCEEDED` | `total_estimated_cost > budget > 0` AND `budget_acknowledged=0` | "Tổng chi phí (X) vượt ngân sách (Y). Tick xác nhận để tiếp tục." |

## Logic changes — `procurement_plan.py`

### `auto_load_items()` (modify)

- Trong `for it in items:` loop, sau khi tính `avg_monthly`:
  - Thêm `pending = self._get_pending_po_qty(it.item_code, self.warehouse)`
  - `suggested = max(0, target_stock - current_stock - pending)`
- Append `pending_po_qty=pending` vào row dict
- Sau loop: nếu `added == 0` → `frappe.msgprint(_("Không có dữ liệu tiêu thụ trong {0} tháng..."), indicator="orange")`

### `validate()` (extend)

```python
def _validate_budget(self):
    if self.budget and self.budget > 0:
        total = flt(self.total_estimated_cost)
        if total > flt(self.budget) and not self.budget_acknowledged:
            frappe.throw(_(
                "SC-E-BUDGET-EXCEEDED: Tổng chi phí ({0}) vượt ngân sách ({1}). "
                "Tick 'Xác nhận vượt ngân sách' để tiếp tục."
            ).format(frappe.format(total, {"fieldtype": "Currency"}),
                     frappe.format(flt(self.budget), {"fieldtype": "Currency"})))
```

Gọi trong `validate()` sau `_compute_amounts()`.

### `on_submit()` (extend)

```python
def on_submit(self):
    self.db_set("status", "Approved")
    if self.auto_create_mr:
        self.make_material_request()
```

### `_get_pending_po_qty()` (new static helper)

```python
@staticmethod
def _get_pending_po_qty(item_code, warehouse) -> float:
    """Sum qty - received_qty trên SC PO docstatus=1 status pending."""
    result = frappe.db.sql("""
        SELECT COALESCE(SUM(GREATEST(poi.qty - COALESCE(poi.received_qty, 0), 0)), 0)
        FROM `tabSC Purchase Order Item` poi
        JOIN `tabSC Purchase Order` po ON po.name = poi.parent
        WHERE poi.item = %s
          AND poi.warehouse = %s
          AND po.docstatus = 1
          AND po.status IN ('Approved', 'Sent to Supplier', 'Partially Received')
    """, (item_code, warehouse))
    return flt(result[0][0]) if result else 0.0
```

**Fallback:** Nếu `SC Purchase Order Item.received_qty` không tồn tại trong schema → dùng `poi.qty` trực tiếp. Check schema trước khi viết.
**Fallback:** Nếu `SC Purchase Order Item.warehouse` không tồn tại → filter qua parent PO `target_warehouse` hoặc bỏ filter warehouse.

## Migration

- 4 field mới Frappe tự migrate khi `bench migrate`
- KHÔNG cần patch riêng — fields default về 0/False, không backfill

## Test plan — `supplycore/tests/uc06_test.py`

| Test | Scenario |
|---|---|
| `test_budget_exceeded_blocks_submit` | budget=1tr, items totaling 2tr, budget_acknowledged=0 → throw SC-E-BUDGET-EXCEEDED |
| `test_budget_acknowledged_allows_submit` | budget=1tr, total=2tr, budget_acknowledged=1 → save+submit OK |
| `test_auto_load_subtracts_pending_po` | Seed: item có avg 100/tháng, current=10, pending PO 50 → suggested ≈ target - 10 - 50 |
| `test_auto_load_empty_warns` | Warehouse không có SLE consumption → auto_load trả 0 items + msgprint orange (không throw) |
| `test_auto_create_mr_on_submit` | auto_create_mr=1, plan submit → material_request link populate, MR tồn tại |

Test runner pattern: `def test_X(): ... return {"pass": bool, "msg": str}` + `run()` aggregator như uc05_test.py.

## Out-of-scope (KHÔNG làm trong UC-06)

- ML/trend-based forecast (defer Phase 2)
- Multi-warehouse plan trong 1 record (giữ 1 plan/warehouse)
- Approval workflow tier (Manager/Executive) — dùng docstatus submit native
- Email notification sau submit/auto-MR (defer)

## File changes

1. `supplycore/m2_planning/UC-06_FLOW.md` — this file
2. `supplycore/m2_planning/doctype/procurement_plan/procurement_plan.json` — 3 fields mới
3. `supplycore/m2_planning/doctype/procurement_plan_item/procurement_plan_item.json` — `pending_po_qty` field
4. `supplycore/m2_planning/doctype/procurement_plan/procurement_plan.py` — `_validate_budget`, `on_submit` auto-MR, `_get_pending_po_qty`, `auto_load_items` extend
5. `supplycore/tests/uc06_test.py` — 5 test scenarios
