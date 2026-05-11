# UC-13 — Nhập/Xuất kho thủ công với Batch + Bin tracking — Flow & Implementation

**Module:** M4 WMS & PDA
**DocType:** SC Stock Entry (existing) + SC Stock Ledger Entry (existing)
**Date:** 2026-05-11
**Source:** Phase 1 / UseCase_SupplyCore_v2.0.md UC-13

## Bối cảnh & Điều chỉnh phạm vi (user-confirmed 2026-05-11)

Spec UC-13 gốc giả định có **PDA/máy quét barcode**. Bệnh viện hiện tại **KHÔNG có PDA và không có hệ thống quét mã**. UC-13 được điều chỉnh:

- Thay "quét barcode bin/item/batch" bằng **nhập tay / autocomplete search** trên form
- Mục tiêu giữ nguyên: **biết hàng nào, lô nào, số lượng bao nhiêu, ở bin nào**
- Quick form chuyên cho putaway (xếp lên kệ) + picking (lấy xuống) — đỡ tốn click hơn SC Stock Entry full form
- Defer offline sync + PDA battery cases — không applicable

## Audit hiện trạng

| Spec line | Có sẵn | UC-13 cần |
|---|---|---|
| 1. Mở app PDA | ❌ no PDA → web form | ✓ quick form web (sẵn có SC Stock Entry full + thêm API quick) |
| 2. Chọn In/Out/Count | ✓ SC Stock Entry `entry_type` Material Receipt/Issue/Transfer | ✓ |
| 3. Quét bin destination | → User type/select bin_code, autocomplete Link | ✓ Link Bin Location filtered |
| 4. Quét item barcode | → User type item_code or item_name, autocomplete | ✓ `lookup_item(code_or_name)` helper |
| 5. Nhập/xác nhận qty | ✓ row.qty | ✓ |
| 6. Quét batch | → User select batch (filtered by item) | ✓ `lookup_batch(item, search)` helper |
| 7. Xác nhận → SLE real-time | ✓ SE.on_submit posts SLE | ✓ |
| 4a. Barcode không nhận | → Đã là nhập tay default | ✓ N/A |
| 7a. Mất kết nối → offline | Không applicable (web online) | ✗ defer |
| Ngoại lệ pin PDA hết | Không applicable | ✗ defer |
| **Yêu cầu user**: biết item/lô/qty/bin | Partial: SLE có `bin_location` field; thiếu API query tổng hợp | ✓ `query_stock_position()` API |

## Actor

- Thủ kho (SupplyCore Storekeeper, Warehouse Officer)

## Pre-condition

- SC Item, SC Batch (nếu has_batch), Bin Location đã tồn tại
- User login, có quyền SC Stock Entry create+submit

## Luồng chính (web form, KHÔNG PDA)

### Putaway (xếp hàng lên kệ — đã nhận hàng từ PR, xếp vào bin)

| Bước | User | Hệ thống |
|---|---|---|
| 1 | Mở "Quick Putaway" — `/api/method/supplycore.m4_wms.api.quick_stock.quick_putaway` (UI thực tế qua Frappe API call hoặc Bench Script) | – |
| 2 | Chọn `entry_type=Putaway` (Material Receipt) | – |
| 3 | Type bin_code → autocomplete trả Bin Location, chọn `bin_location` | Link field filter `enabled=1` |
| 4 | Type item_code or item_name → chọn `item` | Autocomplete SC Item, fetch uom auto |
| 5 | Nhập `qty` | – |
| 6 | (Nếu item has_batch=1) chọn `batch` từ list lọc theo item (sort by expiry FEFO) | Link SC Batch filtered |
| 7 | Click "Xác nhận" → API `quick_putaway()` → tạo SC Stock Entry + Submit | SE → SLE +qty tại `bin_location` |

### Picking (lấy hàng xuống — xuất ra khoa phòng / chuyển kho)

Tương tự nhưng `entry_type=Material Issue` + `source_bin` thay `target_bin`. Sau submit SLE -qty tại bin.

## Luồng thay thế

### 4a — Item code nhập sai

Lookup helpers tra cứu nhanh:
- `lookup_item(text)` — search item_code OR item_name LIKE
- `lookup_batch(item, text)` — search batch_id OR supplier_batch_no LIKE
- `lookup_bin(text)` — search bin_code OR barcode LIKE

API trả top 10 matches, user pick.

### Query "biết hàng/lô/qty/ở đâu"

`query_stock_position(item=None, warehouse=None, bin_location=None, batch=None)`:
- Group SLE theo (item, warehouse, bin_location, batch)
- HAVING sum(qty_change) > 0
- Trả: `[{item, item_name, warehouse, bin_location, bin_code, batch, batch_id, expiry_date, qty, uom}, ...]`

UI build sau (defer JS) — backend API sẵn.

## Hậu điều kiện

- 1 SC Stock Entry submitted với entry_type + items
- 1+ SC Stock Ledger Entry per item row (post bằng SE.on_submit logic hiện có)
- `current_qty` của bin update khi gọi `recompute_occupancy()` hoặc tự nhiên khi query SLE

## Field changes

KHÔNG cần field mới — toàn bộ tracking đã có:
- SC Stock Entry: `entry_type`, `from/to_warehouse`, `posting_date`
- SC Stock Entry Item: `item`, `qty`, `uom`, `batch`, `source_bin`, `target_bin`
- SC Stock Ledger Entry: `item`, `warehouse`, `bin_location`, `batch`, `qty_change`

## API — `m4_wms/api/quick_stock.py` (NEW)

```python
@frappe.whitelist()
def quick_putaway(item, qty, uom, warehouse, bin_location, batch=None,
                   valuation_rate=0, remarks=None) -> dict:
    """Quick xếp hàng vào bin — tạo SC Stock Entry Material Receipt + submit."""
    se = frappe.new_doc("SC Stock Entry")
    se.entry_type = "Material Receipt"
    se.posting_date = today()
    se.to_warehouse = warehouse
    se.purpose = "Quick Putaway (UC-13)"
    se.remarks = remarks or f"Putaway via quick form"
    se.append("items", {
        "item": item,
        "qty": flt(qty),
        "uom": uom,
        "valuation_rate": flt(valuation_rate),
        "batch": batch,
        "target_bin": bin_location,
    })
    se.flags.ignore_permissions = True
    se.insert()
    se.submit()
    return {"stock_entry": se.name, "status": "OK"}


@frappe.whitelist()
def quick_picking(item, qty, uom, warehouse, bin_location, batch=None,
                   remarks=None) -> dict:
    """Quick lấy hàng từ bin — tạo SC Stock Entry Material Issue + submit."""
    se = frappe.new_doc("SC Stock Entry")
    se.entry_type = "Material Issue"
    se.posting_date = today()
    se.from_warehouse = warehouse
    se.purpose = "Quick Picking (UC-13)"
    se.remarks = remarks or f"Picking via quick form"
    se.append("items", {
        "item": item,
        "qty": flt(qty),
        "uom": uom,
        "batch": batch,
        "source_bin": bin_location,
    })
    se.flags.ignore_permissions = True
    se.insert()
    se.submit()
    return {"stock_entry": se.name, "status": "OK"}


@frappe.whitelist()
def lookup_item(text: str, limit: int = 10) -> list:
    return frappe.db.sql("""
        SELECT name AS item_code, item_name, uom, has_batch_no
        FROM `tabSC Item`
        WHERE disabled = 0 AND is_stock_item = 1
          AND (name LIKE %(t)s OR item_name LIKE %(t)s)
        ORDER BY item_name LIMIT %(lim)s
    """, {"t": f"%{text}%", "lim": int(limit)}, as_dict=True)


@frappe.whitelist()
def lookup_batch(item: str, text: str = "", limit: int = 10) -> list:
    return frappe.db.sql("""
        SELECT name AS batch_no, batch_id, expiry_date,
               manufacturing_date, supplier_batch_no, qc_status
        FROM `tabSC Batch`
        WHERE item = %(item)s AND disabled = 0 AND COALESCE(blocked,0) = 0
          AND (batch_id LIKE %(t)s OR COALESCE(supplier_batch_no,'') LIKE %(t)s)
        ORDER BY expiry_date ASC LIMIT %(lim)s
    """, {"item": item, "t": f"%{text}%", "lim": int(limit)}, as_dict=True)


@frappe.whitelist()
def lookup_bin(text: str, warehouse: str = None, limit: int = 10) -> list:
    cond = "AND warehouse = %(warehouse)s" if warehouse else ""
    return frappe.db.sql(f"""
        SELECT name, bin_code, warehouse, barcode, zone,
               COALESCE(current_qty,0) AS current_qty, capacity_qty, status
        FROM `tabBin Location`
        WHERE enabled = 1 {cond}
          AND (bin_code LIKE %(t)s OR COALESCE(barcode,'') LIKE %(t)s)
        ORDER BY bin_code LIMIT %(lim)s
    """, {"t": f"%{text}%", "lim": int(limit), "warehouse": warehouse}, as_dict=True)


@frappe.whitelist()
def query_stock_position(item=None, warehouse=None, bin_location=None,
                          batch=None, limit=200) -> list:
    """UC-13 yêu cầu: biết hàng nào, lô nào, số lượng, ở đâu.

    Group SLE theo (item, warehouse, bin_location, batch).
    Filter optional — không truyền nghĩa là all.
    """
    where = ["sle.is_cancelled = 0"]
    params = {}
    if item:
        where.append("sle.item = %(item)s"); params["item"] = item
    if warehouse:
        where.append("sle.warehouse = %(warehouse)s"); params["warehouse"] = warehouse
    if bin_location:
        where.append("sle.bin_location = %(bin)s"); params["bin"] = bin_location
    if batch:
        where.append("sle.batch = %(batch)s"); params["batch"] = batch
    params["lim"] = int(limit)

    sql = f"""
        SELECT sle.item, i.item_name, i.uom,
               sle.warehouse, sle.bin_location,
               COALESCE(bl.bin_code, '') AS bin_code,
               sle.batch,
               COALESCE(b.batch_id, '') AS batch_id,
               COALESCE(b.expiry_date, NULL) AS expiry_date,
               COALESCE(b.qc_status, '') AS qc_status,
               SUM(sle.qty_change) AS qty
        FROM `tabSC Stock Ledger Entry` sle
        JOIN `tabSC Item` i ON i.name = sle.item
        LEFT JOIN `tabBin Location` bl ON bl.name = sle.bin_location
        LEFT JOIN `tabSC Batch` b ON b.name = sle.batch
        WHERE {' AND '.join(where)}
        GROUP BY sle.item, sle.warehouse, sle.bin_location, sle.batch
        HAVING qty > 0
        ORDER BY i.item_name, sle.warehouse, bin_code, expiry_date
        LIMIT %(lim)s
    """
    return frappe.db.sql(sql, params, as_dict=True)
```

## Error codes mới

KHÔNG cần — SC Stock Entry validate sẵn các trường hợp (item invalid, warehouse invalid, qty ≤ 0, FEFO violation, etc).

## Migration

KHÔNG — chỉ thêm API module, không thay schema.

## Test plan — `tests/uc13_test.py`

| Test | Scenario |
|---|---|
| `test_quick_putaway_creates_se_and_sle` | quick_putaway() → SE submitted + SLE +qty tại bin |
| `test_quick_picking_creates_se_and_sle` | quick_picking() (sau khi putaway) → SE submitted + SLE -qty |
| `test_lookup_item_by_code` | lookup_item("VTTH") → trả items có name LIKE |
| `test_lookup_item_by_name` | lookup_item("găng tay") → trả items có item_name LIKE |
| `test_lookup_batch_by_id` | lookup_batch(item, "BAT") → trả batches |
| `test_lookup_bin_by_code` | lookup_bin("UC13") → trả bins |
| `test_query_stock_position_all` | sau putaway → query_stock_position() trả row có item, batch, bin, qty đúng |
| `test_query_stock_position_filter_by_item` | filter item → chỉ trả rows item đó |
| `test_query_stock_position_filter_by_bin` | filter bin → chỉ trả rows bin đó |
| `test_query_stock_position_excludes_picked` | putaway +50, picking -30 → query trả qty=20 |

## Out-of-scope (deferred / N/A)

- PDA / barcode scanning hardware (no PDA available)
- Offline sync queue (web-only, online)
- PDA battery handling
- JS quick form UI (defer; whitelisted API đủ cho test + future UI build)
- "Stocktake / Kiểm kho" — đó là UC-32 phạm vi riêng

## File changes

1. `supplycore/m4_wms/UC-13_FLOW.md` — this file
2. `supplycore/m4_wms/api/quick_stock.py` — NEW API module
3. `supplycore/tests/uc13_test.py` — 10 test scenarios
