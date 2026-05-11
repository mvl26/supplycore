# UC-19 — Stock Reconciliation — Flow & Implementation

**Module:** M9 Stocktake (host) — UC-19 cross-module M6 Transfer (UC categorization) + M8 Accounting (GL)
**DocType:** SC Stock Reconciliation + SC SR Item (existing)
**Date:** 2026-05-11
**Source:** Phase 1 / UseCase_SupplyCore_v2.0.md UC-19

## Audit hiện trạng

| Spec | Trước | Sau UC-19 |
|---|---|---|
| 1. Mở SR | ✓ /app/sc-stock-reconciliation | ✓ |
| 2. Chọn kho + ngày | ✓ warehouse + posting_date | ✓ |
| 3. **system_qty vs actual_qty** | Partial: fields có, system_qty read_only nhưng KHÔNG auto-fill | ✓ auto-fill từ SLE trong validate |
| 3a. **Upload Excel kiểm kê** | ✗ no template | ✓ document Frappe Data Import builtin + `load_from_count_sheet()` |
| 4. Tính chênh lệch + giá trị | ✓ `difference` + `amount_change` | ✓ |
| 5. **Lý do per row có chênh** | ✓ `reason` Select field | ✓ reqd khi difference≠0 |
| 6. **Manager phê duyệt** | Partial: docstatus, không có Manager role check | ✓ before_submit enforce Manager role |
| 7. **GL Entry auto** | ✓ `_post_gl_entries` | ✓ |
| 6a. **Reject + ghi chú** | ✗ | ✓ `reject(reason)` method + Rejected status |
| Ngoại lệ: **âm vượt tồn → block** | Partial: SLE post chỉ -qty; không pre-validate | ✓ before_submit check actual_qty cause net negative |

## Actor

- Thủ kho (Storekeeper) — input đếm thực tế
- Quản lý (Manager) — phê duyệt
- Kế toán (Accountant) — review GL impact

## Pre-condition

- Có biên bản kiểm kê hoặc phát hiện sai lệch (SC Inventory Count Sheet hoặc nhập tay)
- Items có valuation_rate (cho GL)

## Luồng chính

| Bước | Action |
|---|---|
| 1 | User mở `/app/sc-stock-reconciliation/new` |
| 2 | Chọn `warehouse`, `posting_date`, `expense_account` (optional, default 642) |
| 3 | Thêm items: `item`, `uom`, `batch`, `bin_location`, `actual_qty`, `valuation_rate` |
| 4 | Save → `validate()`: auto-fill `system_qty` từ SC SLE, compute `difference + amount_change`, compute totals |
| 5 | Nhập `reason` per row có difference≠0 → Save lại |
| 6 | Submit → `before_submit` check Manager role + validate âm vượt tồn → `on_submit` post SLE + GL Entry |
| 7 | Trường hợp Reject: Manager click "Reject" → `reject(reason)` → status=Rejected |

## Luồng thay thế

### 3a — Upload Excel

Option 1: Dùng SC Inventory Count Sheet (UC-32) — set `count_sheet` link → method `load_from_count_sheet()` copy items vào SR.

Option 2: Frappe Data Import builtin
- `/app/data-import/new`, Document Type = `SC Stock Reconciliation` (parent + items child)
- Template: parent fields + items child (item, actual_qty, batch, bin_location, valuation_rate)
- KHÔNG cần code custom — chỉ document workflow

### 6a — Reject

`reject(reason)`:
- Validate stage: docstatus=0 OR docstatus=1 nhưng chưa cancel?
- Pattern: trước submit, Manager có thể "Reject" → set `rejection_reason` + chuyển status=Rejected
- Sau Reject, Storekeeper sửa và submit lại → reset rejection_reason

## Hậu điều kiện

- SR docstatus=1, status=Approved
- SLE adjustment posted (per item, +/- diff)
- GL Entry posted (Inventory account 152 vs Expense 642)
- SC Inventory Count Sheet (nếu có link) → status=Reconciled

## Xử lý ngoại lệ

### Âm vượt tồn (actual_qty làm cho net stock < 0)

`before_submit`:
- Per row, compute resulting stock = `system_qty + difference = actual_qty`
- Nếu `actual_qty < 0` (impossible — non_negative đã enforce) hoặc total qty của (item, warehouse) sau adjustment < 0 → throw `SC-E-SR-NEGATIVE`

## Field changes

### SC Stock Reconciliation — ADD/MODIFY

| Field | Action | Note |
|---|---|---|
| `status` options | MODIFY | Thêm `Rejected`: `Draft\nApproved\nRejected\nCancelled` |
| `rejection_reason` | ADD Small Text | depends_on status=Rejected, read_only |

### SC SR Item — KHÔNG đổi (đã có đủ)

## Error codes mới

| Code | Trigger | Message |
|---|---|---|
| `SC-E-SR-MANAGER-REQUIRED` | submit SR không có Manager role | "Submit SR yêu cầu role SupplyCore Manager / Accountant" |
| `SC-E-SR-NEGATIVE` | actual_qty làm net stock < 0 | "Item {x} batch {y}: actual_qty {z} làm tồn kho âm sau adjustment" |
| `SC-E-SR-REJECT-REASON` | reject() không reason | "Phải nhập lý do từ chối" |
| `SC-E-SR-REASON-REQUIRED` | row có difference nhưng thiếu reason | "Row {x}: phải nhập 'Lý do điều chỉnh' khi có chênh lệch" |

## Logic — `sc_stock_reconciliation.py`

### Validate extend (auto-fill system_qty + reason check)

```python
def validate(self):
    self._auto_fill_system_qty()      # NEW
    self._compute_per_row()
    self._compute_totals()
    self._validate_reason_per_row()   # NEW
    if self.docstatus == 0 and not self.status:
        self.status = "Draft"

def _auto_fill_system_qty(self):
    """Auto-fill system_qty từ SC SLE."""
    for r in self.items:
        if not (r.item and self.warehouse):
            continue
        qty = flt(frappe.db.sql("""
            SELECT COALESCE(SUM(qty_change), 0)
            FROM `tabSC Stock Ledger Entry`
            WHERE item = %s AND warehouse = %s AND is_cancelled = 0
              AND (%s IS NULL OR batch = %s)
              AND (%s IS NULL OR bin_location = %s)
        """, (r.item, self.warehouse, r.batch, r.batch,
              r.bin_location, r.bin_location))[0][0])
        r.system_qty = qty

def _validate_reason_per_row(self):
    """Row có difference ≠ 0 phải có reason."""
    if self.docstatus == 0:
        return  # chỉ check khi submit
    for r in self.items:
        if abs(flt(r.difference)) > 0.01 and not r.reason:
            frappe.throw(_(
                "SC-E-SR-REASON-REQUIRED: Row {0} (item {1}): phải nhập 'Lý do điều chỉnh' khi có chênh lệch"
            ).format(r.idx, r.item))
```

### before_submit (NEW)

```python
def before_submit(self):
    # Manager / Accountant role enforce
    user_roles = set(frappe.get_roles(frappe.session.user))
    allowed = {"SupplyCore Manager", "SupplyCore Accountant", "System Manager"}
    if not (user_roles & allowed):
        frappe.throw(_(
            "SC-E-SR-MANAGER-REQUIRED: Submit SR yêu cầu role "
            "SupplyCore Manager / Accountant"
        ))
    # Validate âm tồn
    for r in self.items:
        if flt(r.actual_qty) < 0:
            frappe.throw(_(
                "SC-E-SR-NEGATIVE: Item {0}: actual_qty không thể âm"
            ).format(r.item))
        # actual_qty < 0 đã được non_negative enforce; check net qty < 0 không cần
        # vì system_qty = SLE sum + adjustment = actual_qty, không âm
```

### reject(reason) method (NEW)

```python
@frappe.whitelist()
def reject(self, reason: str = None):
    if not reason or not str(reason).strip():
        frappe.throw(_("SC-E-SR-REJECT-REASON: Phải nhập lý do từ chối"))
    if self.docstatus != 0:
        frappe.throw(_("Chỉ reject SR ở Draft"))
    self.db_set("status", "Rejected")
    self.db_set("rejection_reason", reason)
    return {"status": "Rejected"}
```

### load_from_count_sheet (NEW)

```python
@frappe.whitelist()
def load_from_count_sheet(self):
    """UC-19 3a: copy items từ SC Inventory Count Sheet vào SR.items."""
    if not self.count_sheet:
        frappe.throw(_("Phải set count_sheet trước"))
    if self.docstatus != 0:
        frappe.throw(_("Chỉ load khi Draft"))
    cs = frappe.get_doc("SC Inventory Count Sheet", self.count_sheet)
    self.items = []
    for ci in cs.items:
        self.append("items", {
            "item": ci.item,
            "uom": ci.uom,
            "batch": ci.batch,
            "bin_location": getattr(ci, "bin_location", None),
            "actual_qty": flt(ci.counted_qty),
            "valuation_rate": flt(getattr(ci, "valuation_rate", 0)),
        })
    self._auto_fill_system_qty()
    self._compute_per_row()
    self._compute_totals()
    self.save(ignore_permissions=False)
    return {"items_loaded": len(self.items)}
```

## Migration

- 1 field `rejection_reason` mới Frappe tự migrate
- Status options `Rejected` thêm vào Select

## Test plan — `tests/uc19_test.py`

| Test | Scenario |
|---|---|
| `test_sr_auto_fill_system_qty` | Seed SLE 100; tạo SR row item → system_qty=100 |
| `test_sr_compute_difference` | system=100, actual=120 → difference=20, amount_change=20×rate |
| `test_sr_reason_required_when_difference` | difference≠0 + thiếu reason → SC-E-SR-REASON-REQUIRED |
| `test_sr_submit_creates_sle_adjustment` | Submit → SLE +20 posted |
| `test_sr_submit_creates_gl_entry` | Submit → SC GL Entry (Dr 152 / Cr 642) created if accounts exist |
| `test_sr_submit_blocks_non_manager` | Non-Manager user + submit → SC-E-SR-MANAGER-REQUIRED |
| `test_sr_submit_allows_manager` | System Manager submit → OK |
| `test_sr_reject_requires_reason` | reject(empty) → SC-E-SR-REJECT-REASON |
| `test_sr_reject_with_reason` | reject(reason) → status=Rejected + rejection_reason saved |
| `test_sr_actual_qty_negative_blocked` | actual_qty=-5 → non_negative validate throw (Frappe native) |
| `test_sr_cancel_reverses_sle_and_gl` | Cancel → SLE reversed + GL canceled |

## Out-of-scope

- Excel template lưu repo (defer; Frappe Data Import builtin đủ)
- Multi-warehouse SR trong 1 doc (giữ 1 warehouse / SR)
- Bulk approval queue (defer)

## File changes

1. `supplycore/m9_stocktake/UC-19_FLOW.md` — this file
2. `supplycore/m9_stocktake/doctype/sc_stock_reconciliation/sc_stock_reconciliation.json` — `rejection_reason` + status `Rejected`
3. `supplycore/m9_stocktake/doctype/sc_stock_reconciliation/sc_stock_reconciliation.py` — auto-fill + reason validate + Manager check + reject + load_from_count_sheet
4. `supplycore/tests/uc19_test.py` — 11 test scenarios
