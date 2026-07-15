# UC-18 — Chuyển kho nội bộ (Stock Transfer) — Flow & Implementation

**Module:** M6 Transfer
**DocType:** SC Transfer Request + SC Stock Entry (existing)
**Date:** 2026-05-11
**Source:** Phase 1 / UseCase_SupplyCore_v2.0.md UC-18

## Audit hiện trạng

| Spec | Trước | Sau UC-18 |
|---|---|---|
| 1. SE Material Transfer | ✓ SC Stock Entry | ✓ |
| 2. from/to warehouse | ✓ | ✓ |
| 3. Items + qty + batch | ✓ | ✓ |
| 4. Check tồn kho đủ | ✓ SC-E005 STOCK_INSUFFICIENT | ✓ + improve msg với max có thể chuyển |
| 5. **Cross-tier → cần Manager duyệt** | Partial: `requires_manager_approval` auto-set, nhưng submit không enforce role | ✓ TR.on_submit check Manager role khi cần |
| 6. Sau duyệt: SE submit → SLE | ✓ flow chuẩn | ✓ |
| 7. **In phiếu chuyển kho** | ✗ | ✓ `get_transfer_slip_data()` method |
| 4a. **Tồn không đủ → max có thể chuyển** | Partial: throw, không trả max | ✓ throw kèm detail "tối đa có thể chuyển: X" |
| 5a. **Same-tier → không cần approval** | Partial: auto-set khi to/from = Department | ✓ explicit Main↔Sub không Manager required |
| Ngoại lệ: rollback giữa chừng | ✓ Frappe transaction native | ✓ |

## Actor

- Thủ kho (Storekeeper, Warehouse Officer) — tạo + submit
- Quản lý (Manager) — phê duyệt khi cross-tier
- SupplyCore Storekeeper — request

## Pre-condition

- SC Item có tồn tại + tồn kho tại from_warehouse
- to_warehouse exists, không phải group, không disabled
- from_warehouse ≠ to_warehouse

## Luồng chính

| Bước | Action |
|---|---|
| 1 | User tạo SC Transfer Request `/app/sc-transfer-request/new` |
| 2 | Chọn `from_warehouse`, `to_warehouse`, `request_date`, `required_by` |
| 3 | Thêm items: `item`, `requested_qty`, `uom`, `batch` (optional) |
| 4 | Save → `validate()`: check warehouses, dates, fetch `available_at_source`, detect cross-tier (set `requires_manager_approval`) |
| 5 | Submit TR → `on_submit`: check Manager role nếu `requires_manager_approval=1`. Set status=Approved + record `approved_by/at` |
| 6 | Click "Tạo Stock Entry" → `make_stock_entry()` tạo SC SE Material Transfer Draft (link TR) |
| 7 | SE submit → SLE -qty tại from_warehouse + +qty tại to_warehouse + auto sync TR.status=Received |
| 8 | User print phiếu chuyển kho qua `get_transfer_slip_data()` + Frappe Print Format |

## Luồng thay thế

### 4a — Tồn không đủ

`_fill_available_qty()` trên TR submit:
- Compute `available_at_source = SUM(SLE.qty_change)` cho (item, from_warehouse)
- Nếu `approved_qty > available` → throw `SC-E-TRANSFER-INSUFFICIENT: Item {x}: SL duyệt {y} > tồn kho nguồn {z}. Tối đa có thể chuyển: {z}`

### 5a — Same-tier transfer không cần Manager

`_detect_cross_tier()`:
- Cross-tier: `from_type=Department OR to_type=Department` → `requires_manager_approval=1`
- Same-tier: Main↔Sub, Sub↔Sub, Main↔Main → `requires_manager_approval=0`

Khi `requires_manager_approval=0`, on_submit bỏ qua role check.

## Hậu điều kiện

- Cả TR và SE đều submitted
- SLE -qty từ `from_warehouse`, +qty tại `to_warehouse`
- TR.status=Received, TR.stock_entry link đến SE

## Field changes

KHÔNG cần thêm field — existing structure đủ.

## Error codes

| Code | Trigger | Message |
|---|---|---|
| `SC-E-TRANSFER-INSUFFICIENT` | approved_qty > available_at_source | "Item {x}: SL duyệt {y} > tồn kho nguồn {z}. Tối đa: {z}" |
| `SC-E-TRANSFER-MANAGER-REQUIRED` | submit TR với `requires_manager_approval=1` không có Manager role | "TR cross-tier yêu cầu role SupplyCore Manager để submit" |

## Logic — `sc_transfer_request.py`

### Validate improve

```python
def _fill_available_qty(self):
    for row in self.items:
        if not row.item or not self.from_warehouse:
            continue
        available = flt(frappe.db.sql("""
            SELECT COALESCE(SUM(qty_change), 0)
            FROM `tabSC Stock Ledger Entry`
            WHERE item = %s AND warehouse = %s AND is_cancelled = 0
        """, (row.item, self.from_warehouse))[0][0])
        row.available_at_source = available
        if not row.approved_qty:
            row.approved_qty = row.requested_qty
        if self.docstatus == 1 and flt(row.approved_qty) > available:
            frappe.throw(_(
                "SC-E-TRANSFER-INSUFFICIENT: Item {0}: SL duyệt {1} > "
                "tồn kho nguồn {2}. Tối đa có thể chuyển: {2}"
            ).format(row.item, row.approved_qty, available))
```

### on_submit enforce Manager role

```python
def on_submit(self):
    if self.requires_manager_approval:
        user_roles = set(frappe.get_roles(frappe.session.user))
        if not (user_roles & {"SupplyCore Manager", "System Manager"}):
            frappe.throw(_(
                "SC-E-TRANSFER-MANAGER-REQUIRED: TR cross-tier yêu cầu role "
                "SupplyCore Manager để submit"
            ))
    self.db_set("status", "Approved")
    self.db_set("approved_by",
                 frappe.session.user
                 if frappe.session.user not in (None, "", "Guest") else "Administrator")
    self.db_set("approved_at", now())
```

### Print slip data

```python
@frappe.whitelist()
def get_transfer_slip_data(self):
    items = [{
        "item": r.item, "uom": r.uom, "batch": r.batch,
        "requested_qty": flt(r.requested_qty),
        "approved_qty": flt(r.approved_qty),
        "transferred_qty": flt(r.transferred_qty or 0),
    } for r in self.items]
    return {
        "name": self.name,
        "request_date": str(self.request_date),
        "transfer_type": self.transfer_type,
        "required_by": str(self.required_by),
        "from_warehouse": self.from_warehouse,
        "to_warehouse": self.to_warehouse,
        "requested_by": self.requested_by,
        "approved_by": self.approved_by,
        "items": items,
        "total_qty": flt(self.total_qty),
        "url": f"/app/sc-transfer-request/{self.name}",
    }
```

## Migration

- KHÔNG cần — chỉ thêm logic enforcement + method.

## Test plan — `tests/uc18_test.py`

| Test | Scenario |
|---|---|
| `test_tr_create_basic` | Tạo TR Main→Sub với items + save OK |
| `test_tr_same_warehouse_rejected` | from=to → throw |
| `test_tr_insufficient_stock_throws` | approved_qty > available → SC-E-TRANSFER-INSUFFICIENT |
| `test_tr_detect_cross_tier_to_department` | to=Department → requires_manager_approval=1 |
| `test_tr_same_tier_no_approval_required` | Main↔Sub → requires_manager_approval=0 |
| `test_tr_cross_tier_blocks_non_manager` | requires_manager_approval=1 + non-Manager user submit → SC-E-TRANSFER-MANAGER-REQUIRED |
| `test_tr_cross_tier_allows_manager` | Admin (Manager+) submit cross-tier → OK |
| `test_tr_make_stock_entry` | TR Approved → make_stock_entry → SE Draft tạo OK |
| `test_se_submit_syncs_tr_received` | SE submit → TR.status=Received + transferred_qty set |
| `test_get_transfer_slip_data` | API trả dict đủ field cho in |

## Out-of-scope

- Bin-to-bin transfer trong cùng warehouse (UC-13 quick stock entry đã hỗ trợ)
- Multi-stop transfer (defer; chỉ 1 from + 1 to)
- Auto-generate transfer phiếu PDF (chỉ trả data; user dùng Frappe Print Format builtin)

## File changes

1. `supplycore/m6_transfer/UC-18_FLOW.md` — this file
2. `supplycore/m6_transfer/doctype/sc_transfer_request/sc_transfer_request.py` — enforce Manager + improve error msg + slip data method
3. `supplycore/tests/uc18_test.py` — 10 test scenarios
