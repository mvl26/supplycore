# UC-12 — Quản lý Bin Location & Putaway Rules — Flow & Implementation

**Module:** M4 WMS & PDA
**DocType:** Bin Location + Putaway Rule + SC Warehouse (existing tree)
**Date:** 2026-05-11
**Source:** Phase 1 / UseCase_SupplyCore_v2.0.md UC-12

## Audit hiện trạng (trước UC-12)

| Spec | Trước | Sau UC-12 |
|---|---|---|
| 1. Mở Bin Management | ✓ /app/bin-location | ✓ |
| 2. Sơ đồ 3 cấp Kho tổng → con → khoa phòng | ✓ SC Warehouse `is_tree=1`, `parent_warehouse` | ✓ |
| 3. Thêm/sửa bin: mã, vị trí, sức chứa | ✓ Bin Location đủ fields | ✓ |
| 4. Gán bin mặc định | Partial: `SC Item.default_bin_location` có, không có suggest logic | ✓ `suggest_bin(item, warehouse, qty)` API |
| 5. Bin status Đang dùng/Trống/Đầy | ✗ | ✓ field `current_qty`, `occupancy_pct`, `status` (computed read_only) |
| 6. In nhãn barcode | ✗ | ✓ `get_barcode_label_data()` whitelisted method trả data + format |
| 7. Putaway rules: Item Group → Bin | ✗ Putaway Rule doctype empty | ✓ Create doctype + matching logic |
| 3a. Bin đầy → suggest gần nhất | ✗ | ✓ `get_alternative_bin(bin_name, qty)` API |
| 4a. Item không default → suggest qua Item Group | ✗ | ✓ logic trong suggest_bin |
| Ngoại lệ: Xóa bin có hàng | Partial: check Stock Entry Detail (sai DocType) | ✓ check SLE bin_location current qty |

## Actor

- Thủ kho (SupplyCore Storekeeper, Warehouse Officer)

## Pre-condition

- SC Warehouse có cấu trúc 3 cấp (kho tổng `is_group=1` → kho con `is_group=1` → kho khoa phòng `is_group=0`)

## Luồng chính

| Bước | User | Hệ thống |
|---|---|---|
| 1 | Mở `/app/bin-location` | Form/List view |
| 2 | Xem `/app/sc-warehouse` (Tree view) | Tree view 3 cấp |
| 3 | Tạo Bin Location: nhập `warehouse`, `bin_code`, `zone/aisle/rack/shelf/level`, `capacity_qty`, `capacity_uom` | `validate()` check temperature range nếu controlled |
| 4 | Trên SC Item: set `default_bin_location` HOẶC tạo Putaway Rule | Putaway Rule matching khi PR submitted (UC-09) suggest bin |
| 5 | List view filter `status` Empty/In Use/Full | Daily scheduler hoặc on-demand recompute `current_qty` + `status` |
| 6 | Click "In nhãn barcode" | `get_barcode_label_data()` return barcode + bin_code + warehouse → in qua Frappe Print Format |
| 7 | Cấu hình Putaway Rule: nhập `item_group` HOẶC `item` + `warehouse` + `target_bin` + `priority` + `enabled` | Lưu thành record Putaway Rule |

## Luồng thay thế

### 3a — Bin đầy → suggest bin thay thế

`get_alternative_bin(bin_name, qty)`:
1. Lấy bin hiện tại + warehouse + zone
2. Tìm bin khác cùng warehouse, cùng zone (gần nhất), `enabled=1`, `current_qty + qty ≤ capacity_qty`
3. Sort theo: cùng zone → cùng aisle → bin_code asc
4. Trả về list top 5 alternatives

### 4a — Item không có default → suggest qua Item Group

Trong `suggest_bin(item, warehouse, qty)`:
1. Check Putaway Rule match (item, warehouse) → return target_bin
2. Else SC Item.default_bin_location nếu cùng warehouse → return
3. Else Putaway Rule match (item_group, warehouse) → return target_bin
4. Else Putaway Rule match (item_group, warehouse=None) → return target_bin
5. Else return None + warn "Không có suggested bin"

## Xử lý ngoại lệ

### Xóa bin đang có hàng

`on_trash()` check `SUM(qty_change) FROM SC Stock Ledger Entry WHERE bin_location = self.name AND is_cancelled = 0`. Nếu > 0 → throw `SC-E-BIN-NOT-EMPTY`. User phải tạo Stock Transfer di chuyển hàng sang bin khác trước khi xóa.

## Field changes

### Bin Location — ADD

| Field | Type | Note |
|---|---|---|
| `current_qty` | Float, read_only | tổng SLE.qty_change tại bin (recompute on-demand) |
| `occupancy_pct` | Percent, read_only | current_qty / capacity_qty × 100 |
| `status` | Select `Empty\nIn Use\nFull`, read_only | tính theo occupancy_pct: 0% Empty, <95% In Use, ≥95% Full |
| `last_recomputed_at` | Datetime, read_only | timestamp recompute cuối |

### Putaway Rule — NEW DocType

| Field | Type | Note |
|---|---|---|
| `title` | Data, autoname | format "PWR-{#####}" |
| `item_group` | Link `SC Item Group`, optional | rule theo group |
| `item` | Link `SC Item`, optional | rule cụ thể (priority cao hơn group) |
| `warehouse` | Link `SC Warehouse`, optional | rule scope warehouse (null = áp dụng mọi warehouse) |
| `target_bin` | Link `Bin Location`, reqd | bin để putaway |
| `priority` | Int, default 1 | higher first |
| `enabled` | Check, default 1 | – |
| `remarks` | Small Text | – |

Validation: ít nhất 1 trong (item, item_group) phải set.

## Error codes mới

| Code | Trigger | Message |
|---|---|---|
| `SC-E-BIN-NOT-EMPTY` | xóa bin có current_qty > 0 | "Bin {name} đang có {qty} đơn vị — chuyển hàng trước khi xóa" |
| `SC-E-BIN-CAPACITY` | suggest bin không còn capacity | "Bin {name} vượt capacity {qty}/{max}" |
| `SC-E-PUTAWAY-RULE` | Putaway Rule không có item/item_group | "Phải nhập 'item' HOẶC 'item_group'" |

## Logic

### Bin Location — recompute + on_trash

```python
def on_trash(self):
    qty = flt(frappe.db.sql("""
        SELECT COALESCE(SUM(qty_change), 0)
        FROM `tabSC Stock Ledger Entry`
        WHERE bin_location = %s AND is_cancelled = 0
    """, self.name)[0][0])
    if qty > 0:
        frappe.throw(_(
            "SC-E-BIN-NOT-EMPTY: Bin {0} đang có {1} đơn vị — chuyển hàng trước khi xóa"
        ).format(self.bin_code, qty))

@frappe.whitelist()
def recompute_occupancy(self):
    qty = flt(frappe.db.sql("""
        SELECT COALESCE(SUM(qty_change), 0)
        FROM `tabSC Stock Ledger Entry`
        WHERE bin_location = %s AND is_cancelled = 0
    """, self.name)[0][0])
    cap = flt(self.capacity_qty)
    pct = (qty / cap * 100) if cap > 0 else 0
    if qty <= 0.001:
        st = "Empty"
    elif pct >= 95:
        st = "Full"
    else:
        st = "In Use"
    self.db_set("current_qty", qty)
    self.db_set("occupancy_pct", pct)
    self.db_set("status", st)
    self.db_set("last_recomputed_at", frappe.utils.now())
    return {"current_qty": qty, "occupancy_pct": pct, "status": st}

@frappe.whitelist()
def get_barcode_label_data(self):
    return {
        "barcode": self.barcode or self.name,
        "bin_code": self.bin_code,
        "warehouse": self.warehouse,
        "zone": self.zone,
        "rack": self.rack, "shelf": self.shelf, "level": self.level,
        "capacity_qty": self.capacity_qty,
        "capacity_uom": self.capacity_uom,
    }
```

### Putaway Rule — controller

```python
class PutawayRule(Document):
    def validate(self):
        if not self.item and not self.item_group:
            frappe.throw(_("SC-E-PUTAWAY-RULE: Phải nhập 'item' HOẶC 'item_group'"))
```

### m4_wms/api/bin_helpers.py — NEW

```python
@frappe.whitelist()
def suggest_bin(item: str, warehouse: str, qty: float = 0) -> dict:
    """UC-12: trả bin gợi ý theo putaway rules + default + capacity."""
    qty = flt(qty)
    # 1. Rule match (item, warehouse) priority cao nhất
    rule = frappe.db.sql("""
        SELECT target_bin FROM `tabPutaway Rule`
        WHERE enabled = 1 AND item = %s AND warehouse = %s
        ORDER BY priority DESC LIMIT 1
    """, (item, warehouse))
    if rule:
        bin_name = rule[0][0]
        if _bin_has_capacity(bin_name, qty):
            return {"bin": bin_name, "source": "rule_item_wh"}

    # 2. SC Item.default_bin_location
    default_bin = frappe.db.get_value("SC Item", item, "default_bin_location")
    if default_bin:
        b_wh = frappe.db.get_value("Bin Location", default_bin, "warehouse")
        if b_wh == warehouse and _bin_has_capacity(default_bin, qty):
            return {"bin": default_bin, "source": "item_default"}

    # 3. Rule match (item_group, warehouse)
    item_group = frappe.db.get_value("SC Item", item, "item_group")
    if item_group:
        rule = frappe.db.sql("""
            SELECT target_bin FROM `tabPutaway Rule`
            WHERE enabled = 1 AND item_group = %s AND warehouse = %s
            ORDER BY priority DESC LIMIT 1
        """, (item_group, warehouse))
        if rule:
            bin_name = rule[0][0]
            if _bin_has_capacity(bin_name, qty):
                return {"bin": bin_name, "source": "rule_group_wh"}

        # 4. Rule match (item_group, warehouse=None) — global
        rule = frappe.db.sql("""
            SELECT target_bin FROM `tabPutaway Rule`
            WHERE enabled = 1 AND item_group = %s AND (warehouse IS NULL OR warehouse = '')
            ORDER BY priority DESC LIMIT 1
        """, item_group)
        if rule:
            bin_name = rule[0][0]
            b_wh = frappe.db.get_value("Bin Location", bin_name, "warehouse")
            if b_wh == warehouse and _bin_has_capacity(bin_name, qty):
                return {"bin": bin_name, "source": "rule_group_global"}

    return {"bin": None, "source": "no_match"}


def _bin_has_capacity(bin_name: str, qty: float) -> bool:
    b = frappe.db.get_value("Bin Location", bin_name,
                              ["capacity_qty", "current_qty", "enabled"], as_dict=True)
    if not b or not b.enabled:
        return False
    if not b.capacity_qty:  # 0 = không giới hạn
        return True
    return (flt(b.current_qty) + flt(qty)) <= flt(b.capacity_qty)


@frappe.whitelist()
def get_alternative_bin(bin_name: str, qty: float = 0) -> dict:
    """UC-12 3a: bin đầy → tìm bin thay thế gần nhất (cùng warehouse, cùng zone)."""
    qty = flt(qty)
    b = frappe.db.get_value("Bin Location", bin_name,
                              ["warehouse", "zone", "aisle"], as_dict=True)
    if not b:
        frappe.throw(_("Bin {0} không tồn tại").format(bin_name))

    candidates = frappe.db.sql("""
        SELECT name, bin_code, zone, aisle, capacity_qty, current_qty
        FROM `tabBin Location`
        WHERE name != %(self_name)s
          AND warehouse = %(warehouse)s
          AND enabled = 1
          AND (capacity_qty = 0 OR (COALESCE(current_qty, 0) + %(qty)s) <= capacity_qty)
        ORDER BY
          CASE WHEN zone = %(zone)s THEN 0 ELSE 1 END,
          CASE WHEN aisle = %(aisle)s THEN 0 ELSE 1 END,
          bin_code
        LIMIT 5
    """, {"self_name": bin_name, "warehouse": b.warehouse,
           "zone": b.zone, "aisle": b.aisle, "qty": qty}, as_dict=True)
    return {"alternatives": candidates}
```

## Migration

- 4 field Bin Location + Putaway Rule doctype (NEW) Frappe tự migrate
- Không cần patch

## Test plan — `tests/uc12_test.py`

| Test | Scenario |
|---|---|
| `test_bin_create_basic` | Tạo bin với warehouse + bin_code + capacity → save OK |
| `test_bin_temperature_range_validate` | min ≥ max → throw |
| `test_bin_delete_blocked_when_has_stock` | Bin có SLE qty > 0 + delete → SC-E-BIN-NOT-EMPTY |
| `test_bin_delete_allowed_when_empty` | Bin không có qty → delete OK |
| `test_bin_recompute_occupancy_empty` | Bin chưa có SLE → recompute → status=Empty, pct=0 |
| `test_bin_recompute_occupancy_in_use` | SLE +50 vào bin (cap=100) → recompute → status=In Use, pct=50 |
| `test_bin_recompute_occupancy_full` | SLE +95 vào bin (cap=100) → recompute → status=Full, pct=95 |
| `test_putaway_rule_requires_item_or_group` | Tạo Putaway Rule không item/group → SC-E-PUTAWAY-RULE |
| `test_suggest_bin_uses_item_rule` | Rule item + warehouse → suggest_bin trả bin đó |
| `test_suggest_bin_falls_back_to_default` | Không rule, có item.default_bin_location → suggest trả default |
| `test_suggest_bin_falls_back_to_item_group` | Không rule item, có rule item_group → suggest trả rule group bin |
| `test_suggest_bin_skips_full_bin` | Rule trỏ bin đầy → suggest_bin trả no_match (hoặc fallback) |
| `test_get_alternative_bin_same_zone_first` | Bin đầy → alternative ưu tiên cùng zone |
| `test_get_barcode_label_data` | Method trả dict đủ field cho in barcode |

## Out-of-scope

- JS tree view custom render (defer)
- PDF Print Format render barcode (chỉ trả data; user dùng Frappe Print Format builtin)
- Auto-recompute occupancy trên hook SLE.after_insert (heavy — defer; gọi on-demand)
- Bulk import bin từ Excel (defer; Frappe Data Import builtin đủ)

## File changes

1. `supplycore/m4_wms/UC-12_FLOW.md` — this file
2. `supplycore/m4_wms/doctype/bin_location/bin_location.json` — 4 fields mới
3. `supplycore/m4_wms/doctype/bin_location/bin_location.py` — fix on_trash + recompute_occupancy + get_barcode_label_data
4. `supplycore/m4_wms/doctype/putaway_rule/putaway_rule.json` — NEW
5. `supplycore/m4_wms/doctype/putaway_rule/putaway_rule.py` — NEW
6. `supplycore/m4_wms/api/__init__.py` — package marker (if not exists)
7. `supplycore/m4_wms/api/bin_helpers.py` — NEW suggest_bin + get_alternative_bin
8. `supplycore/tests/uc12_test.py` — 14 test scenarios
