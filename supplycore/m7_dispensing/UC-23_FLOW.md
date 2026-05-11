# UC-23 — Quản lý Mã BHYT cho Vật tư — Flow & Implementation

**Module:** M7 Dispensing (UC) + Supplycore (DocType host)
**DocType:** SC BHYT Code Config (existing)
**Date:** 2026-05-11
**Source:** Phase 1 / UseCase_SupplyCore_v2.0.md UC-23

## Audit hiện trạng

| Spec | Trước | Sau UC-23 |
|---|---|---|
| 1. Mở config BHYT | ✓ /app/sc-bhyt-code-config | ✓ |
| 2. Tìm vật tư theo tên/mã | ✓ in_standard_filter | ✓ |
| 3. **Xem 1-N mã của vật tư** | ✓ list view; ✗ summary "history" cho 1 item | ✓ `list_bhyt_configs_for_item()` |
| 4. Thêm/sửa Nhóm + Tỷ lệ + Hiệu lực | ✓ fields + validate rate [0,100] | ✓ + overlap check |
| 5. **Lịch sử audit** | ✓ `track_changes=1` + version history Frappe | ✓ |
| 6. Cập nhật config khi quy định thay đổi | ✓ effective_from/to chain | ✓ |
| 7. **Batch update Excel** | Partial: Frappe Data Import builtin | ✓ document workflow |
| 4a. Mã chưa có → tạo mới | ✓ DocType create | ✓ |
| 7a. **Import lỗi → báo dòng lỗi** | ✓ Frappe Data Import builtin tự handle | ✓ |
| Ngoại lệ: **rate > 100 → throw** | ✓ existing validate | ✓ |
| **Overlap configs cùng scope** | ✗ chưa check | ✓ add validate overlap |

## Actor

- Quản lý (Manager) / Kế toán (Accountant) / BHYT Officer

## Pre-condition

- Vật tư có trong SC Item
- Có văn bản quy định BHYT (để fill `legal_basis`)

## Luồng chính

| Bước | Action |
|---|---|
| 1 | Mở `/app/sc-bhyt-code-config` |
| 2 | Filter list theo `item` hoặc `bhyt_code` LIKE |
| 3 | Click item → list tất cả config của item đó qua `list_bhyt_configs_for_item()` |
| 4 | Tạo mới hoặc sửa: `bhyt_code`, `bhyt_name`, `bhyt_group` (N01-N09), `payment_rate`, `ceiling_price`, `effective_from`, `effective_to` |
| 5 | Save → validate: 0 ≤ rate ≤ 100, effective_to ≥ effective_from, scope không overlap |
| 6 | Sửa configs khi quy định thay đổi: tạo bản mới với effective_from sau effective_to của bản cũ |
| 7 | Batch update: `/app/data-import/new` → Document Type=SC BHYT Code Config → Update existing / Insert new → Frappe handle row errors |

## Luồng thay thế

### 4a — Mã BHYT chưa tồn tại

Tạo mới record với `bhyt_code` unique. SC BHYT Code Config không có ràng buộc danh mục riêng — `bhyt_code` là Data field, chấp nhận bất kỳ chuỗi nào theo Thông tư BYT.

### 7a — Import Excel lỗi

Frappe Data Import builtin: mỗi row lỗi được log riêng. Import tiếp tục các row hợp lệ. User xem Import Log → download Excel "Errors only" để sửa.

## Xử lý ngoại lệ

### Tỷ lệ > 100% hoặc < 0

`validate`: `payment_rate ∈ [0, 100]` → throw `SC-E-BHYT-RATE` "Tỷ lệ thanh toán phải trong [0..100]"

### Overlap configs cùng scope

Khi tạo/sửa SC BHYT Code Config:
- Check existing configs cùng (item, item_group, is_active=1)
- Nếu khoảng [effective_from, effective_to] overlap với khoảng của config khác → throw `SC-E-BHYT-OVERLAP`
- Buộc user phải close bản cũ (set `effective_to`) trước khi tạo bản mới

## Field changes

KHÔNG cần — current schema đủ.

## Error codes mới

| Code | Trigger | Message |
|---|---|---|
| `SC-E-BHYT-OVERLAP` | Tạo/sửa config có scope overlap với active config khác | "Config trùng phạm vi áp dụng + thời hạn với SC-BHYT-XXX. Close bản cũ trước." |

(Existing `SC-E-BHYT-RATE` không thay).

## Logic — `sc_bhyt_code_config.py`

### Validate extend

```python
def validate(self):
    if not self.item and not self.item_group:
        frappe.throw(_("Cần chọn `Item` hoặc `Item Group` (ít nhất 1)"))
    if self.payment_rate is not None and (flt(self.payment_rate) < 0 or flt(self.payment_rate) > 100):
        frappe.throw(_("SC-E-BHYT-RATE: Tỷ lệ thanh toán phải trong [0..100]"))
    if self.effective_to and getdate(self.effective_to) < getdate(self.effective_from):
        frappe.throw(_("Hết hiệu lực phải sau Hiệu lực từ"))
    # UC-23: overlap check
    self._validate_no_overlap()

def _validate_no_overlap(self):
    """UC-23: prevent overlapping active configs cùng scope."""
    if not self.is_active:
        return
    # Build scope match clause: same item HOẶC same item_group nếu item rỗng
    if self.item:
        scope_filter = "item = %(item)s"
        params = {"item": self.item}
    else:
        scope_filter = "(item IS NULL OR item = '') AND item_group = %(ig)s"
        params = {"ig": self.item_group}

    # Find configs overlap [effective_from, effective_to OR ∞]
    eff_to = self.effective_to or "9999-12-31"
    params.update({
        "self_name": self.name or "",
        "ef": self.effective_from,
        "et": eff_to,
    })
    overlap = frappe.db.sql(f"""
        SELECT name, effective_from, effective_to
        FROM `tabSC BHYT Code Config`
        WHERE {scope_filter}
          AND is_active = 1
          AND name != %(self_name)s
          AND effective_from <= %(et)s
          AND COALESCE(effective_to, '9999-12-31') >= %(ef)s
        LIMIT 1
    """, params, as_dict=True)
    if overlap:
        o = overlap[0]
        frappe.throw(_(
            "SC-E-BHYT-OVERLAP: Config trùng scope với {0} ({1}–{2}). "
            "Close bản cũ trước (set effective_to)."
        ).format(o["name"], o["effective_from"], o["effective_to"] or "∞"))
```

## API — `supplycore/api/bhyt.py` extend

```python
@frappe.whitelist()
def list_bhyt_configs_for_item(item_code: str) -> dict:
    """UC-23 step 3: list tất cả configs (active + expired) của item.

    Bao gồm:
      - Configs cụ thể (item=X)
      - Configs theo item_group (group-level apply)
    """
    item_group = frappe.db.get_value("SC Item", item_code, "item_group")
    rows = frappe.db.sql("""
        SELECT name, bhyt_code, bhyt_name, bhyt_group,
               payment_rate, ceiling_price,
               item, item_group, is_active,
               effective_from, effective_to,
               legal_basis, modified
        FROM `tabSC BHYT Code Config`
        WHERE item = %(item)s
           OR (
               (item IS NULL OR item = '')
               AND item_group = %(ig)s
           )
        ORDER BY effective_from DESC, modified DESC
    """, {"item": item_code, "ig": item_group}, as_dict=True)
    return {
        "item": item_code,
        "item_group": item_group,
        "count": len(rows),
        "configs": rows,
    }


@frappe.whitelist()
def get_bhyt_history(item_code: str) -> dict:
    """Alias đơn giản cho list_bhyt_configs_for_item (UC step 5 audit view)."""
    return list_bhyt_configs_for_item(item_code)
```

## Frappe Data Import — UC step 7

Document trong README:
1. `/app/data-import/new` (System Manager only)
2. Document Type = `SC BHYT Code Config`
3. Import Type = `Insert New Records` HOẶC `Update Existing Records`
4. Download template Excel → fill: bhyt_code, bhyt_name, bhyt_group, payment_rate, ceiling_price, item OR item_group, effective_from, effective_to, legal_basis
5. Upload → Frappe gọi `validate()` per row → lỗi vào Import Log (UC 7a)

## Migration

- KHÔNG cần — chỉ thêm API + validate.

## Test plan — `tests/uc23_test.py`

| Test | Scenario |
|---|---|
| `test_bhyt_create_basic` | Tạo config với item + rate 80% → save OK |
| `test_bhyt_rate_over_100_blocked` | rate=120 → throw SC-E-BHYT-RATE |
| `test_bhyt_rate_negative_blocked` | rate=-10 → throw SC-E-BHYT-RATE |
| `test_bhyt_requires_item_or_group` | Không item + không group → throw |
| `test_bhyt_effective_to_before_from` | effective_to < effective_from → throw |
| `test_bhyt_overlap_same_item_blocked` | 2 configs cùng item + date overlap → SC-E-BHYT-OVERLAP |
| `test_bhyt_overlap_close_old_allows_new` | Set effective_to bản cũ + tạo bản mới sau → OK |
| `test_bhyt_inactive_no_overlap_check` | is_active=0 → không check overlap |
| `test_list_bhyt_configs_for_item` | Tạo 2 configs khác kỳ → list trả 2 records |
| `test_get_active_config_picks_latest` | 2 configs date khác → get_active_config trả bản hiện hành |

## Out-of-scope

- BHYT category master list (defer; bhyt_code là free text)
- Notification khi config sắp hết hiệu lực (defer Phase 2)
- API real-time validate với hệ thống BYT (defer)

## File changes

1. `supplycore/m7_dispensing/UC-23_FLOW.md` — this file
2. `supplycore/supplycore/doctype/sc_bhyt_code_config/sc_bhyt_code_config.py` — validate overlap
3. `supplycore/api/bhyt.py` — thêm `list_bhyt_configs_for_item` + `get_bhyt_history`
4. `supplycore/tests/uc23_test.py` — 10 test scenarios
