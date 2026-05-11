# UC-16 — Xuất kho theo FEFO — Flow & Implementation

**Module:** M5 FEFO & Hạn dùng
**DocType:** SC Stock Entry + SC Stock Entry Item + SC Batch (all existing)
**Date:** 2026-05-11
**Source:** Phase 1 / UseCase_SupplyCore_v2.0.md UC-16

## Audit hiện trạng

| Spec | Trước | Sau UC-16 |
|---|---|---|
| 1. Tạo yêu cầu xuất kho | ✓ SC SE Material Issue/Transfer | ✓ |
| 2. Auto-suggest FEFO | ✓ `get_suggested_batches` API | ✓ |
| 3. Hiển thị batch + EXP + qty | ✓ + severity (OK/Warning/Critical/Expired) | ✓ |
| 4. Xác nhận / đổi batch + lý do nếu không FEFO | ✓ `fefo_override` + `fefo_override_reason` per row | ✓ + Manager role check |
| 5. SLE update per batch | ✓ on_submit posts | ✓ |
| 4a. Override → **audit + Manager xác nhận** | Partial: ghi reason; ✗ Manager role check + audit log | ✓ enforce role + record approver + Comment audit |
| 2a. Chỉ 1 batch → auto chọn | Partial: API trả; ✗ helper auto-fill | ✓ `auto_pick_fefo()` returns single batch |
| Ngoại lệ: Batch hết giữa chừng → auto next | Partial: API cumulative; ✗ split helper | ✓ `auto_pick_fefo` split qty across batches |

## Actor

- Thủ kho (Storekeeper) — request issue
- Quản lý (Manager) — confirm khi override FEFO
- Hệ thống — gợi ý FEFO + audit log

## Pre-condition

- Item có multiple batches (hoặc 1) tại warehouse
- Tất cả batches có `expiry_date`

## Luồng chính

| Bước | User / System | Action |
|---|---|---|
| 1 | User | Tạo SC Stock Entry Material Issue/Transfer, chọn from_warehouse |
| 2 | User → `get_suggested_batches(item, warehouse, qty)` | API trả list batch sort theo expiry ASC + cumulative suggested_qty |
| 3 | UI hiển thị | batch_no, expiry, available_qty, suggested_qty, severity |
| 4 | User | Chấp nhận FEFO HOẶC tick `fefo_override=1` + nhập `fefo_override_reason`. Nếu override, user phải có role Manager |
| 5 | SE submit | `_enforce_fefo_rules` validate. Submit → SLE -qty per batch + record `fefo_override_approved_by/at` nếu override + log Frappe Comment |

## Luồng thay thế

### 2a — Chỉ có 1 batch

`auto_pick_fefo(item, warehouse, qty)`:
- Nếu chỉ 1 batch khả dụng → trả `{batches: [{batch_no, qty}], single_batch: True}`
- Không yêu cầu user confirm thêm (UI có thể auto-fill row)

### 4a — Override FEFO

Khi user submit SE với `fefo_override=1`:
- Validate user role có "SupplyCore Manager" OR "System Manager" → else throw `SC-E-FEFO-MANAGER-REQUIRED`
- Set `fefo_override_approved_by=session.user`, `fefo_override_approved_at=now()`
- Insert Frappe Comment vào SE với content "FEFO Override: row X, batch Y, reason: Z" (audit trail)

### Batch hết giữa chừng (Ngoại lệ)

`auto_pick_fefo(item, warehouse, qty=100)`:
- Batch A (EXP 2027-01) avail=30, Batch B (EXP 2027-06) avail=80
- Trả: [{batch=A, qty=30}, {batch=B, qty=70}]
- UI tự split thành 2 rows SE.items

## Hậu điều kiện

- SLE -qty per batch khớp FEFO
- Frappe Comment audit log nếu override
- SE.items[i].fefo_override_approved_by populated nếu override

## Field changes

### SC Stock Entry Item — ADD

| Field | Type | Note |
|---|---|---|
| `fefo_override_approved_by` | Link User, read_only | Manager xác nhận override |
| `fefo_override_approved_at` | Datetime, read_only | timestamp |

## Error codes mới

| Code | Trigger | Message |
|---|---|---|
| `SC-E-FEFO-MANAGER-REQUIRED` | fefo_override=1 nhưng user không có role Manager | "FEFO Override yêu cầu xác nhận Quản lý — bạn cần role SupplyCore Manager để submit" |

## Logic — `sc_stock_entry.py`

### `_enforce_fefo_rules` extend

```python
def _enforce_fefo_rules(self):
    if self.docstatus != 0:
        return
    if self.entry_type not in ISSUE_TYPES:
        return
    # existing FEFO check loop ...

    # UC-16 4a: Manager role check + audit log
    has_override = any(r.fefo_override and r.batch for r in self.items)
    if has_override:
        user_roles = frappe.get_roles(frappe.session.user)
        if not any(r in user_roles for r in ("SupplyCore Manager", "System Manager")):
            frappe.throw(_(
                "SC-E-FEFO-MANAGER-REQUIRED: FEFO Override yêu cầu xác nhận Quản lý — "
                "user phải có role SupplyCore Manager để submit"
            ))
```

### on_submit extend — record approver + log

```python
def on_submit(self):
    ...existing SLE posting...
    self._log_fefo_override_audit()

def _log_fefo_override_audit(self):
    for row in self.items:
        if row.fefo_override and row.batch:
            row.db_set("fefo_override_approved_by", frappe.session.user)
            row.db_set("fefo_override_approved_at", frappe.utils.now())
            try:
                self.add_comment(
                    "Comment",
                    text=(f"<b>FEFO Override</b> — row {row.idx} batch {row.batch}: "
                          f"{frappe.utils.escape_html(row.fefo_override_reason or '')}"),
                )
            except Exception as e:
                frappe.log_error(message=str(e)[:500], title="UC-16 fefo_override audit")
```

## API — `supplycore/api/fefo.py` extend

```python
@frappe.whitelist()
def auto_pick_fefo(item_code: str, warehouse: str, qty: float) -> dict:
    """UC-16 2a + ngoại lệ: tự pick batch theo FEFO + split nếu cần."""
    suggested = get_suggested_batches(item_code, warehouse, qty)
    batches = suggested["batches"]
    picked = [b for b in batches if flt(b["suggested_qty"]) > 0]
    return {
        "picked":           picked,
        "single_batch":     len(picked) == 1 and not suggested["shortfall"],
        "fully_satisfied":  suggested["fully_satisfied"],
        "shortfall":        suggested["shortfall"],
        "total_picked":     sum(flt(b["suggested_qty"]) for b in picked),
    }
```

## Migration

- 2 fields SE Item Frappe tự migrate
- Không cần patch

## Test plan — `tests/uc16_test.py`

| Test | Scenario |
|---|---|
| `test_get_suggested_batches_fefo_order` | 2 batches expiry 30d / 90d → API trả batch 30d trước |
| `test_get_suggested_batches_excludes_expired` | Batch expired → skip |
| `test_get_suggested_batches_excludes_blocked` | Batch blocked=1 → skip |
| `test_auto_pick_fefo_single_batch` | 1 batch khả dụng → single_batch=True, picked qty đúng |
| `test_auto_pick_fefo_split_multiple` | 2 batches qty 30 + 70, request 100 → split correctly |
| `test_auto_pick_fefo_shortfall` | Request 200, avail 100 → shortfall=100 |
| `test_fefo_override_requires_manager` | User không Manager + fefo_override → throw SC-E-FEFO-MANAGER-REQUIRED |
| `test_fefo_override_with_manager_succeeds` | User Manager + override + reason → submit OK |
| `test_fefo_override_records_approver` | Submit với override → fefo_override_approved_by + at populated |
| `test_fefo_override_logs_comment` | Submit với override → Frappe Comment được tạo trên SE |

## Out-of-scope

- JS auto-fill UI row từ auto_pick_fefo (defer; whitelisted API đủ)
- Multi-warehouse FEFO consolidation (chỉ trong 1 warehouse)
- Hash-based audit chain (Frappe Comment + track_changes đủ)

## File changes

1. `supplycore/m5_fefo/UC-16_FLOW.md` — this file
2. `supplycore/supplycore/doctype/sc_stock_entry_item/sc_stock_entry_item.json` — 2 fields mới
3. `supplycore/supplycore/doctype/sc_stock_entry/sc_stock_entry.py` — extend `_enforce_fefo_rules` + on_submit
4. `supplycore/api/fefo.py` — thêm `auto_pick_fefo()`
5. `supplycore/tests/uc16_test.py` — 10 test scenarios
