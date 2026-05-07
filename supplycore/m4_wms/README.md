# M4 — WMS & PDA

Module quản lý vị trí lưu kho (Bin Location) + giao diện PDA/Mobile cho kho thực địa.

> ⚠ **v0.2 — chỉ Frappe**: Stock Entry/Bin/Item đều SC*. Không còn ERPNext.

## DocTypes

| DocType | Loại | Mô tả |
|---|---|---|
| `Bin Location` | Master | Vị trí chi tiết trong SC Warehouse (zone/aisle/rack/shelf/level) |
| `SC Stock Entry` | Submittable | Material Receipt / Issue / Transfer — tạo SC SLE |
| `SC Stock Entry Item` | Child | Dòng item với source_bin/target_bin |

**Master phụ thuộc:** `SC Item` · `SC Warehouse` · `SC Batch` · `SC Stock Ledger Entry`

## Naming series

- `SC-BIN-#####` — Bin Location
- `SC-SE-YYYY-#####` — SC Stock Entry

## Cấu trúc kho 3 tầng (BR)

```
SC Warehouse (warehouse_type)
├── Main           ← Kho tổng (group)
│   ├── Sub        ← Kho con
│   │   ├── Department ← Kho khoa phòng
│   │   └── Quarantine ← Cách ly QC
│   └── Transit    ← Trung chuyển
└── Bin Location (gắn warehouse) — vị trí chi tiết
        zone, aisle, rack, shelf, level
```

## Luồng hoạt động

```
[1] Setup masters:
    - SC Department (khoa phòng)
    - SC Warehouse (parent_warehouse, warehouse_type)
    - Bin Location (gắn warehouse, có barcode)
    - SC Item.default_bin_location, default_warehouse
    - SC Item.barcodes (table SC Item Barcode)

[2] PDA scan via /pda web page
    │ Quick Scan input → API supplycore.api.wms.scan_barcode
    │   Resolve theo thứ tự:
    │     1. SC Item Barcode (table)
    │     2. SC Item.name trực tiếp
    │     3. SC Batch.name
    │     4. Bin Location.barcode hoặc .name
    │
    ├─ Type=item  → trả item info + suggested_bin (default_bin_location)
    ├─ Type=batch → trả batch + expiry + item liên kết
    └─ Type=bin   → trả bin info + warehouse + is_quarantine

[3] PDA confirm putaway
    │ POST supplycore.api.wms.confirm_putaway
    │   {item_code, warehouse, qty, batch_no, bin_location, pda_session}
    ▼
    Tạo SC Stock Entry (entry_type=Material Receipt) draft
        │ append item với target_bin
        │ SE controller (validate):
        │   - bin↔warehouse consistency
        │   - bin enabled, không quarantine cho source
        │
        │ submit → ghi SC Stock Ledger Entry +qty
        ▼
    SC Item.default_bin_location → auto-suggest target_bin nếu user không nhập

[4] Bin inventory query
    │ Bin Location.get_current_inventory()
    │ SQL: SUM(qty_change) target_bin − SUM source_bin từ SC SLE submit
```

## API endpoints công bố

| Endpoint | Mô tả |
|---|---|
| `POST /api/method/supplycore.api.wms.scan_barcode` | Resolve barcode → item/batch/bin |
| `GET /api/method/supplycore.api.wms.lookup_bin_for_item?item_code=X&warehouse=Y` | Suggest bin |
| `GET /api/method/supplycore.api.wms.get_bin_inventory?bin_location=Z` | Items hiện ở bin |
| `POST /api/method/supplycore.api.wms.confirm_putaway` | PDA tạo SC Stock Entry |
| `GET /api/method/supplycore.api.wms.quick_search?keyword=K&entity_type=item|bin` | Autocomplete |

## PDA Web App `/pda`

- Single-column 480px max-width, mobile-first (Inter font, touch ≥44px)
- 4 menu: Nhập kho / Xuất kho / Chuyển kho / Kiểm kê (V1: Receipt only)
- Quick Scan section ở menu chính
- Online/offline detection — banner khi mất mạng (IndexedDB sync defer)

## Coverage Phase 1+3

| Yêu cầu | Trạng thái |
|---|---|
| UC-12 Bin Management | ✓ Bin Location DocType với layout fields |
| UC-13 PDA scan barcode | ✓ /pda + 5 API endpoints |
| UC-14 Tra cứu tồn kho theo vị trí | ✓ get_bin_inventory + SC SLE query |
| Bin capacity check | ⚠ field có (`capacity_qty`); validate runtime defer |
| Block delete bin có hàng | ✓ on_trash check SC Stock Entry Item refs |
| Hierarchical 3-tier warehouse | ✓ SC Warehouse NestedSet |
| Mobile-friendly (SCR-14, WF-08) | ✓ /pda layout |

## Vận hành

- `/app/sc-warehouse` → tạo cấu trúc 3 tầng
- `/app/bin-location/new` → tạo bin cho từng warehouse
- `/app/sc-item` → set `default_bin_location` để auto-suggest
- `/pda` (mở trên mobile) → scan + putaway
