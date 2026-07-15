# UC-14 — Tra cứu tồn kho theo vị trí — Flow & Implementation

**Module:** M4 WMS & PDA
**DocType:** SC Stock Ledger Entry (existing) + Bin Location (existing)
**Date:** 2026-05-11
**Source:** Phase 1 / UseCase_SupplyCore_v2.0.md UC-14

## Audit hiện trạng

| Spec | Trước | Sau UC-14 |
|---|---|---|
| 1. Mở Stock Balance / Bin Wise Balance | Partial: UC-13 `query_stock_position` cơ bản | ✓ extend full filter |
| 2. Filter: Kho/VT/Nhóm/Lô/Hạn dùng | Partial: UC-13 chỉ filter item/warehouse/bin/batch | ✓ thêm `item_group`, `expiry_from`, `expiry_to` |
| 3. Show qty + value + bin + batch + expiry | Partial: thiếu value | ✓ thêm `value` (qty × valuation_rate) |
| 4. Chi tiết bin: lịch sử nhập xuất gần nhất | ✗ | ✓ `get_bin_history(bin, limit)` |
| 5. Export Excel/in | ✗ custom; ✓ qua Frappe Report Builder builtin | ✓ Document trong flow |
| 2a. Tồn kho point-in-time (quá khứ) | ✗ | ✓ param `as_of_date` filter SLE.posting_date ≤ |
| 5a. Tồn âm → highlight đỏ | ✗ | ✓ field `is_negative` flag trong response |
| Ngoại lệ: Reconciliation | ✗ | ✓ `reconcile_bin(bin_name)` + `reconcile_all_bins()` |

## Actor

- Thủ kho / Quản lý / Nhân viên khoa phòng (read-only access)

## Pre-condition

- Có SC Stock Ledger Entry submitted

## Luồng chính

| Bước | User | Hệ thống |
|---|---|---|
| 1 | Gọi `/api/method/supplycore.m4_wms.api.quick_stock.get_stock_balance` HOẶC mở SC SLE list / Report Builder | – |
| 2 | Truyền filters: `item`, `warehouse`, `item_group`, `bin_location`, `batch`, `expiry_from`, `expiry_to`, `as_of_date` | Filter SQL |
| 3 | Hệ thống trả list: qty, value (qty × rate), warehouse, bin_code, batch_id, expiry_date, qc_status, is_negative | Group theo (item, warehouse, bin, batch) |
| 4 | Click bin / gọi `get_bin_history(bin, limit=20)` | Trả 20 SLE gần nhất tại bin: posting_date, item, batch, qty_change, voucher |
| 5 | Frappe Report Builder cho phép Export → Excel/CSV/PDF builtin | – |

## Luồng thay thế

### 2a — Point-in-time (quá khứ)

`get_stock_balance(as_of_date="2026-04-01")` → filter `SLE.posting_date <= '2026-04-01'`. Aggregate qty tại thời điểm.

### 5a — Tồn kho âm

Trong response: `is_negative=1` nếu `qty < 0`. UI/Report Builder hiển thị màu đỏ (style theo client-side hoặc Frappe conditional formatting).

## Xử lý ngoại lệ

### Dữ liệu không đồng bộ

`reconcile_bin(bin_name)`:
- Recompute `current_qty` từ SC SLE
- Update Bin Location.current_qty + occupancy_pct + status
- Equivalent với UC-12 `recompute_occupancy()` nhưng callable từ menu

`reconcile_all_bins(warehouse=None)`:
- Loop tất cả Bin Location active (filter warehouse nếu truyền)
- Gọi recompute_occupancy() từng bin
- Trả tổng count bins reconciled

## Field changes

KHÔNG cần — chỉ thêm API methods.

## API — extend `m4_wms/api/quick_stock.py`

```python
@frappe.whitelist()
def get_stock_balance(item=None, item_group=None, warehouse=None,
                      bin_location=None, batch=None,
                      expiry_from=None, expiry_to=None,
                      as_of_date=None, limit=500) -> list:
    """UC-14: stock balance with rich filters + value + negative flag."""
    where = ["sle.is_cancelled = 0"]
    params = {"lim": int(limit)}
    if item:
        where.append("sle.item = %(item)s"); params["item"] = item
    if item_group:
        where.append("i.item_group = %(ig)s"); params["ig"] = item_group
    if warehouse:
        where.append("sle.warehouse = %(wh)s"); params["wh"] = warehouse
    if bin_location:
        where.append("sle.bin_location = %(bin)s"); params["bin"] = bin_location
    if batch:
        where.append("sle.batch = %(batch)s"); params["batch"] = batch
    if expiry_from:
        where.append("b.expiry_date >= %(efrom)s"); params["efrom"] = expiry_from
    if expiry_to:
        where.append("b.expiry_date <= %(eto)s"); params["eto"] = expiry_to
    if as_of_date:
        where.append("sle.posting_date <= %(asof)s"); params["asof"] = as_of_date

    sql = f"""
        SELECT sle.item, i.item_name, i.item_group, i.uom,
               sle.warehouse, sle.bin_location,
               COALESCE(bl.bin_code, '') AS bin_code,
               sle.batch,
               COALESCE(b.batch_id, '') AS batch_id,
               b.expiry_date, COALESCE(b.qc_status, '') AS qc_status,
               SUM(sle.qty_change) AS qty,
               AVG(CASE WHEN sle.qty_change > 0 THEN sle.valuation_rate ELSE NULL END) AS avg_rate,
               SUM(sle.qty_change) * COALESCE(
                   AVG(CASE WHEN sle.qty_change > 0 THEN sle.valuation_rate ELSE NULL END),
                   0
               ) AS value,
               CASE WHEN SUM(sle.qty_change) < 0 THEN 1 ELSE 0 END AS is_negative
        FROM `tabSC Stock Ledger Entry` sle
        JOIN `tabSC Item` i ON i.name = sle.item
        LEFT JOIN `tabBin Location` bl ON bl.name = sle.bin_location
        LEFT JOIN `tabSC Batch` b ON b.name = sle.batch
        WHERE {' AND '.join(where)}
        GROUP BY sle.item, sle.warehouse, sle.bin_location, sle.batch
        HAVING qty != 0
        ORDER BY i.item_name, sle.warehouse, bin_code, expiry_date
        LIMIT %(lim)s
    """
    return frappe.db.sql(sql, params, as_dict=True)


@frappe.whitelist()
def get_bin_history(bin_location: str, limit: int = 20) -> list:
    """UC-14 bước 4: lịch sử nhập xuất gần nhất tại bin."""
    return frappe.db.sql("""
        SELECT sle.posting_date, sle.posting_time,
               sle.item, i.item_name,
               sle.batch, COALESCE(b.batch_id, '') AS batch_id,
               sle.qty_change, sle.valuation_rate,
               sle.voucher_type, sle.voucher_no,
               sle.voucher_detail_no
        FROM `tabSC Stock Ledger Entry` sle
        JOIN `tabSC Item` i ON i.name = sle.item
        LEFT JOIN `tabSC Batch` b ON b.name = sle.batch
        WHERE sle.bin_location = %s AND sle.is_cancelled = 0
        ORDER BY sle.posting_date DESC, sle.posting_time DESC, sle.creation DESC
        LIMIT %s
    """, (bin_location, int(limit)), as_dict=True)


@frappe.whitelist()
def reconcile_bin(bin_name: str) -> dict:
    """UC-14 ngoại lệ: recompute current_qty + status từ SLE thực tế."""
    bin_doc = frappe.get_doc("Bin Location", bin_name)
    return bin_doc.recompute_occupancy()


@frappe.whitelist()
def reconcile_all_bins(warehouse: str = None) -> dict:
    """Recompute tất cả Bin Location (filter warehouse nếu truyền)."""
    filters = {"enabled": 1}
    if warehouse:
        filters["warehouse"] = warehouse
    names = frappe.get_all("Bin Location", filters=filters, pluck="name")
    count = 0
    for n in names:
        try:
            frappe.get_doc("Bin Location", n).recompute_occupancy()
            count += 1
        except Exception as e:
            frappe.log_error(message=f"bin={n}: {str(e)[:300]}",
                              title="UC-14 reconcile_all_bins")
    frappe.db.commit()
    return {"reconciled": count, "total": len(names)}
```

## Frappe Report Builder usage (UC step 5)

User export Excel/CSV/PDF qua builtin:
1. Mở `/app/sc-stock-ledger-entry` (List view)
2. Click **Menu → Report Builder**
3. Add filters: item, warehouse, batch, posting_date range
4. Add columns: item, batch, bin_location, qty_change, voucher_no
5. Save as report → Export Excel/PDF từ Menu

Không cần code custom report — Frappe builtin đủ.

## Error codes mới

KHÔNG cần — chỉ là read-only queries.

## Migration

KHÔNG — chỉ thêm API methods, không thay schema.

## Test plan — `tests/uc14_test.py`

| Test | Scenario |
|---|---|
| `test_get_stock_balance_basic` | Sau putaway → balance returns row đủ qty + value + flags |
| `test_get_stock_balance_filter_item_group` | Filter item_group → chỉ trả items thuộc group |
| `test_get_stock_balance_filter_expiry_range` | Filter expiry_from/to → chỉ batches trong range |
| `test_get_stock_balance_as_of_date` | as_of_date trong quá khứ → exclude SLE sau date đó |
| `test_get_stock_balance_negative_flag` | SLE -qty > +qty → row có is_negative=1 |
| `test_get_bin_history_recent` | Putaway + Picking → get_bin_history trả 2 entries, newest first |
| `test_reconcile_bin_updates_current_qty` | SLE +50 + reconcile_bin → bin.current_qty=50 |
| `test_reconcile_all_bins_processes_multiple` | 3 bins + reconcile_all → return count=3 |

## Out-of-scope

- Custom Frappe Script Report (defer; Report Builder builtin đủ)
- Real-time dashboard widget (defer Phase 2)
- Reorder integration trong stock balance (UC-05 đã có lookup riêng)

## File changes

1. `supplycore/m4_wms/UC-14_FLOW.md` — this file
2. `supplycore/m4_wms/api/quick_stock.py` — extend với 4 methods UC-14
3. `supplycore/tests/uc14_test.py` — 8 test scenarios
