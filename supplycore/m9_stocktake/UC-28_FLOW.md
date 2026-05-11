# UC-28 — Đối soát kho + biên bản — Flow & Implementation

**Module:** M9 Stocktake
**DocType:** SC Stock Reconciliation (existing, extend) + SupplyCore Settings
**Date:** 2026-05-11
**Source:** Phase 1 / UseCase_SupplyCore_v2.0.md UC-28

## Audit hiện trạng

| Spec | Trước | Sau UC-28 |
|---|---|---|
| 1. Mở báo cáo đối soát | ✓ /app/sc-stock-reconciliation | ✓ |
| 2. List chênh lệch + giá trị | ✓ items + total_difference_value | ✓ |
| 3. Phân tích nguyên nhân | ✓ row.reason Select | ✓ |
| 4. Ghi chú per row | ✓ row.remarks | ✓ |
| 5. **Biên bản đối soát + chữ ký** | ✗ | ✓ `get_reconciliation_minutes_data()` |
| 6. Tạo SR điều chỉnh | ✓ UC-19 | ✓ |
| 7. Submit + Kế toán duyệt + GL | ✓ UC-19 GL post | ✓ |
| 3a. Hàng thừa | ✓ actual_qty > system_qty hoặc item mới | ✓ |
| 6a. Lỗi hệ thống | ✓ reason=System Error | ✓ |
| **Chênh lệch > 10tr → điều tra trước** | ✗ | ✓ `requires_investigation` flag + reqd `investigation_notes` |

## Actor

- Kế toán (Accountant) — lập SR, phê duyệt
- Quản lý (Manager) — điều tra khi chênh lệch lớn
- Thủ kho (Storekeeper) — cung cấp giải trình

## Pre-condition

- ICS đã Counted (UC-27) HOẶC SR manual với items chênh lệch

## Luồng chính

| Bước | Action |
|---|---|
| 1 | Mở `/app/sc-stock-reconciliation`, list SR Draft từ ICS submitted |
| 2 | Xem chênh lệch per item (system vs actual) + tổng giá trị |
| 3 | User phân tích → chọn `reason` (Theft / Damage / System Error / etc) |
| 4 | Ghi chú `remarks` per row |
| 5 | Print biên bản qua `get_reconciliation_minutes_data()` (chữ ký placeholder cho Thủ kho, Kế toán, Quản lý) |
| 6 | (Nếu |total_difference_value| > 10tr) `requires_investigation=1` auto-set. User nhập `investigation_notes` + chọn `investigated_by` |
| 7 | Submit → before_submit guard + Manager/Accountant role + GL Entry (Dr 152 / Cr 642 hoặc ngược) |

## Luồng thay thế

### 3a — Hàng thừa không trong danh sách

User append row mới vào SR với `actual_qty > 0` + `system_qty = 0` (auto-fill) → difference dương. Nhập reason="Receiving Error" hoặc "Other" + remarks.

### 6a — Lỗi hệ thống

Reason="System Error" + remarks ghi chi tiết bug. GL Entry vẫn post (cân bằng kế toán), audit log lưu Frappe `track_changes`.

## Xử lý ngoại lệ

### Chênh lệch > 10tr → điều tra

`validate`:
- Compute `abs(total_difference_value)`
- If > Settings.large_variance_threshold (default 10tr) → set `requires_investigation=1`
- Show msgprint warn

`before_submit`:
- If `requires_investigation=1` + `investigation_notes` rỗng → throw `SC-E-SR-INVESTIGATION-REQUIRED`
- Auto set `investigated_by=session.user`, `investigated_at=now()`

## Field changes

### SC Stock Reconciliation — ADD

| Field | Type | Note |
|---|---|---|
| `requires_investigation` | Check, read_only | auto-set khi \|total_diff_value\| > threshold |
| `investigation_notes` | Small Text | Required khi requires_investigation=1 |
| `investigated_by` | Link User, read_only | – |
| `investigated_at` | Datetime, read_only | – |

### SupplyCore Settings — ADD

| Field | Type | Note |
|---|---|---|
| `large_variance_threshold` | Currency (VND), default 10_000_000 | Ngưỡng chênh lệch SR lớn (UC-28 ngoại lệ) |

## Error codes mới

| Code | Trigger | Message |
|---|---|---|
| `SC-E-SR-INVESTIGATION-REQUIRED` | requires_investigation=1 + investigation_notes rỗng | "Chênh lệch giá trị > {threshold} — phải nhập 'Investigation notes' trước khi submit" |

## Logic — `sc_stock_reconciliation.py`

### Validate extend

```python
def validate(self):
    self._auto_fill_system_qty()
    self._compute_per_row()
    self._compute_totals()
    self._validate_reason_per_row()
    self._set_investigation_flag()  # NEW
    if self.docstatus == 0 and self.status not in ("Rejected",):
        self.status = "Draft"

def _set_investigation_flag(self):
    """UC-28 ngoại lệ: |total_difference_value| > threshold → flag."""
    threshold = flt(frappe.db.get_single_value(
        "SupplyCore Settings", "large_variance_threshold") or 10_000_000)
    if abs(flt(self.total_difference_value)) > threshold:
        self.requires_investigation = 1
        if self.is_new() or not self.investigated_by:
            frappe.msgprint(
                _("⚠ Chênh lệch giá trị {0} > {1} — yêu cầu điều tra trước khi submit").format(
                    frappe.format(abs(flt(self.total_difference_value)),
                                    {"fieldtype": "Currency"}),
                    frappe.format(threshold, {"fieldtype": "Currency"})),
                indicator="orange", alert=True,
            )
    else:
        self.requires_investigation = 0
```

### before_submit extend

```python
def before_submit(self):
    # UC-19 existing checks
    user_roles = set(frappe.get_roles(frappe.session.user))
    allowed = {"SupplyCore Manager", "SupplyCore Accountant", "System Manager"}
    if not (user_roles & allowed):
        frappe.throw(_(
            "SC-E-SR-MANAGER-REQUIRED: Submit SR yêu cầu role "
            "SupplyCore Manager / Accountant"
        ))
    for r in self.items:
        if flt(r.actual_qty) < 0:
            frappe.throw(_("SC-E-SR-NEGATIVE: Item {0}: actual_qty không thể âm")
                         .format(r.item))
    # UC-28 ngoại lệ: investigation reqd
    if self.requires_investigation:
        if not (self.investigation_notes and str(self.investigation_notes).strip()):
            threshold = flt(frappe.db.get_single_value(
                "SupplyCore Settings", "large_variance_threshold") or 10_000_000)
            frappe.throw(_(
                "SC-E-SR-INVESTIGATION-REQUIRED: Chênh lệch giá trị > {0} — "
                "phải nhập 'Investigation notes' trước khi submit"
            ).format(frappe.format(threshold, {"fieldtype": "Currency"})))
        if not self.investigated_by:
            self.investigated_by = frappe.session.user
            self.investigated_at = frappe.utils.now()
```

### `get_reconciliation_minutes_data` whitelisted

```python
@frappe.whitelist()
def get_reconciliation_minutes_data(self):
    """UC-28 step 5: data cho biên bản đối soát + chữ ký placeholders."""
    return {
        "name": self.name,
        "posting_date": str(self.posting_date) if self.posting_date else "",
        "warehouse": self.warehouse,
        "count_sheet": self.count_sheet,
        "items": [{
            "item": r.item, "uom": r.uom, "batch": r.batch,
            "bin_location": r.bin_location,
            "system_qty": flt(r.system_qty),
            "actual_qty": flt(r.actual_qty),
            "difference": flt(r.difference),
            "amount_change": flt(r.amount_change),
            "reason": r.reason,
            "remarks": r.remarks,
        } for r in self.items],
        "total_difference_qty": flt(self.total_difference_qty),
        "total_difference_value": flt(self.total_difference_value),
        "requires_investigation": int(self.requires_investigation or 0),
        "investigation_notes": self.investigation_notes,
        "investigated_by": self.investigated_by,
        "investigated_at": str(self.investigated_at) if self.investigated_at else "",
        "signatures": {
            "storekeeper": "_____________________",
            "accountant": "_____________________",
            "manager": "_____________________",
        },
        "url": f"/app/sc-stock-reconciliation/{self.name}",
    }
```

## Migration

- 4 fields SR mới + 1 Settings field Frappe tự migrate

## Test plan — `tests/uc28_test.py`

| Test | Scenario |
|---|---|
| `test_sr_small_variance_no_investigation` | Δ value < 10tr → requires_investigation=0 |
| `test_sr_large_variance_flag_investigation` | Δ value > 10tr → requires_investigation=1 |
| `test_sr_large_variance_submit_blocked_without_notes` | requires_investigation + no notes → SC-E-SR-INVESTIGATION-REQUIRED |
| `test_sr_large_variance_submit_with_notes_ok` | requires_investigation + notes → submit OK + investigated_by set |
| `test_sr_threshold_from_settings` | Settings threshold=5tr → Δ 7tr triggers flag |
| `test_get_reconciliation_minutes_data` | Method trả dict đủ field cho in biên bản |
| `test_sr_excess_item_supported` | Item mới với actual=10, system=0 → diff=10 (hàng thừa) |
| `test_sr_minutes_includes_signatures` | Minutes data có signatures dict |

## Out-of-scope

- Digital signature integration (chỉ placeholder text)
- Auto-create investigation task (defer Phase 2)
- Multi-level approval workflow cho chênh lệch lớn (chỉ 1 cấp Manager)

## File changes

1. `supplycore/m9_stocktake/UC-28_FLOW.md` — this file
2. `supplycore/m9_stocktake/doctype/sc_stock_reconciliation/sc_stock_reconciliation.json` — 4 fields mới
3. `supplycore/m9_stocktake/doctype/sc_stock_reconciliation/sc_stock_reconciliation.py` — investigation logic + minutes data
4. `supplycore/supplycore/doctype/supplycore_settings/supplycore_settings.json` — `large_variance_threshold`
5. `supplycore/tests/uc28_test.py` — 8 test scenarios
