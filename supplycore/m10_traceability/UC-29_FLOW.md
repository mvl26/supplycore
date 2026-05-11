# UC-29 — Truy xuất nguồn gốc lô (Batch Trace) — Flow & Implementation

**Module:** M10 Traceability
**APIs:** `m10_traceability/api/trace.py`
**Date:** 2026-05-11
**Source:** Phase 1 / UseCase_SupplyCore_v2.0.md UC-29

## Audit hiện trạng

| Spec | Trước | Sau UC-29 |
|---|---|---|
| 1. Mở Batch Traceability | ✓ SC Batch List | ✓ |
| 2. Nhập Batch ID / supplier_batch_no | ✓ via UC-15 `lookup_batch_by_no` | ✓ |
| 3-7. **Show chuỗi cung ứng đầy đủ** | ✗ stub `get_batch_trace` | ✓ full implementation |
| 8. **Export PDF** | ✗ | ✓ qua Frappe Print Format (trả data) |
| 2a. Nhập tên VT → list batches | ✓ UC-15 | ✓ + thêm `list_batches_for_item()` |
| 7a. Batch hết hàng → vẫn show lịch sử | ✓ qua SLE history | ✓ |
| **Ngoại lệ: Thiếu thông tin truy xuất** | ✗ | ✓ `data_quality` check in response |

## Actor

- Quản lý / Thủ kho / Pharmacy Officer

## Pre-condition

- SC Batch + SC Stock Ledger Entry có dữ liệu

## Luồng chính

| Bước | Action |
|---|---|
| 1 | Mở `/app/sc-batch` |
| 2 | Search batch_id HOẶC supplier_batch_no qua `lookup_batch_by_no` (UC-15) |
| 3 | Click batch → click "Truy xuất" → call `get_batch_trace(batch_no)` |
| 4 | API trả tất cả: origin (PO/PR/QI), movements (SLE), dispensing (PD), current stock |
| 5 | UI render 5 sections (origin, movements, dispensing, current_stock, data_quality) |
| 6 | Click "Export PDF" → Frappe Print Format render `get_batch_trace` data |

## Luồng thay thế

### 2a — Search theo tên VT

`list_batches_for_item(item_code_or_name)`:
- Search SC Item by code/name LIKE
- Trả tất cả SC Batch của items match (active + disabled)

### 7a — Batch hết hàng

`get_batch_trace` luôn trả `movements` đầy đủ, không lọc theo current_qty. `current_stock.total_qty=0` nếu hết.

## Xử lý ngoại lệ

### Thiếu thông tin truy xuất

`data_quality` check trong response:
- `complete=True/False`
- `missing=[]` list field thiếu:
  - `supplier` không set → missing source
  - `supplier_batch_no` rỗng → missing supplier lot
  - `purchase_order` không tìm được qua SLE → missing origin
  - `qc_inspection` rỗng cho batch có qc_status=Pending → missing QC

UI hiển thị warning + list missing fields. Không block — chỉ inform.

## Field changes

KHÔNG — chỉ extend API.

## Error codes

KHÔNG — chỉ read-only.

## Logic — `m10_traceability/api/trace.py`

```python
@frappe.whitelist()
def get_batch_trace(batch_no: str) -> dict:
    """Trả full vòng đời batch: header + origin + movements + dispensing
    + current_stock + data_quality."""
    if not frappe.db.exists("SC Batch", batch_no):
        return {"exists": False, "batch_no": batch_no}

    batch = frappe.get_doc("SC Batch", batch_no)

    # 1. Header
    header = {
        "name": batch.name, "batch_id": batch.batch_id,
        "item": batch.item, "item_name": batch.item_name,
        "manufacturer": batch.manufacturer,
        "supplier": batch.supplier,
        "supplier_batch_no": batch.supplier_batch_no,
        "country_of_origin": batch.country_of_origin,
        "manufacturing_date": str(batch.manufacturing_date) if batch.manufacturing_date else None,
        "expiry_date": str(batch.expiry_date) if batch.expiry_date else None,
        "qc_status": batch.qc_status,
        "blocked": bool(batch.blocked),
        "block_reason": batch.block_reason,
    }

    # 2. Origin: tìm PR (Purchase Receipt) → PO → QI
    pr_data = frappe.db.sql("""
        SELECT pri.parent AS pr, pr.posting_date, pr.supplier, pr.purchase_order, pr.qc_status
        FROM `tabSC Purchase Receipt Item` pri
        JOIN `tabSC Purchase Receipt` pr ON pr.name = pri.parent
        WHERE pri.batch_no = %s AND pr.docstatus = 1 AND pr.is_return = 0
        ORDER BY pr.posting_date ASC LIMIT 1
    """, batch_no, as_dict=True)
    origin = None
    if pr_data:
        p = pr_data[0]
        qi = frappe.db.get_value("SC Quality Inspection",
            {"purchase_receipt": p["pr"], "batch": batch_no},
            ["name", "overall_status", "inspection_date"], as_dict=True)
        origin = {
            "purchase_receipt": p["pr"],
            "received_date": str(p["posting_date"]),
            "supplier": p["supplier"],
            "purchase_order": p["purchase_order"],
            "pr_qc_status": p["qc_status"],
            "qc_inspection": qi.get("name") if qi else None,
            "qc_result": qi.get("overall_status") if qi else None,
            "qc_date": str(qi.get("inspection_date")) if qi and qi.get("inspection_date") else None,
        }

    # 3. Movements: all SLE
    movements = frappe.db.sql("""
        SELECT sle.posting_date, sle.posting_time,
               sle.warehouse, sle.bin_location, sle.qty_change,
               sle.valuation_rate, sle.voucher_type, sle.voucher_no,
               sle.remarks, sle.is_cancelled
        FROM `tabSC Stock Ledger Entry` sle
        WHERE sle.batch = %s
        ORDER BY sle.posting_date ASC, sle.posting_time ASC, sle.creation ASC
    """, batch_no, as_dict=True)

    # 4. Dispensing: SC PD Item
    dispensing = frappe.db.sql("""
        SELECT pdi.parent AS pd, pd.dispensing_date, pd.patient,
               p.patient_name, pd.ward, pdi.qty, pdi.unit_cost,
               pdi.bhyt_amount, pdi.patient_pays
        FROM `tabSC PD Item` pdi
        JOIN `tabSC Patient Dispensing` pd ON pd.name = pdi.parent
        LEFT JOIN `tabSC Patient` p ON p.name = pd.patient
        WHERE pdi.batch = %s AND pd.docstatus = 1
        ORDER BY pd.dispensing_date ASC
    """, batch_no, as_dict=True)

    # 5. Current stock per warehouse
    by_wh = frappe.db.sql("""
        SELECT warehouse, COALESCE(SUM(qty_change), 0) AS qty
        FROM `tabSC Stock Ledger Entry`
        WHERE batch = %s AND is_cancelled = 0
        GROUP BY warehouse
        HAVING qty > 0
    """, batch_no, as_dict=True)
    total_current = sum(flt(r["qty"]) for r in by_wh)
    current_stock = {
        "total_qty": total_current,
        "by_warehouse": by_wh,
    }

    # 6. Data quality check
    missing = []
    if not batch.supplier:
        missing.append("supplier")
    if not batch.supplier_batch_no:
        missing.append("supplier_batch_no")
    if not batch.manufacturer:
        missing.append("manufacturer")
    if not batch.manufacturing_date:
        missing.append("manufacturing_date")
    if not origin:
        missing.append("purchase_receipt_origin")
    if batch.qc_status == "Pending":
        missing.append("qc_inspection_pending")
    data_quality = {
        "complete": len(missing) == 0,
        "missing": missing,
    }

    return {
        "exists": True,
        "header": header,
        "origin": origin,
        "movements": [{**m, "posting_date": str(m["posting_date"]),
                        "posting_time": str(m["posting_time"]) if m["posting_time"] else None}
                       for m in movements],
        "dispensing": [{**d, "dispensing_date": str(d["dispensing_date"])}
                        for d in dispensing],
        "current_stock": current_stock,
        "data_quality": data_quality,
    }


@frappe.whitelist()
def list_batches_for_item(item_code_or_name: str, limit: int = 20) -> list:
    """UC-29 2a: search batches by item code/name LIKE."""
    items = frappe.db.sql_list("""
        SELECT name FROM `tabSC Item`
        WHERE name LIKE %(t)s OR item_name LIKE %(t)s
        LIMIT 10
    """, {"t": f"%{item_code_or_name}%"})
    if not items:
        return []
    return frappe.db.sql("""
        SELECT b.name, b.batch_id, b.item, i.item_name,
               b.supplier, b.supplier_batch_no, b.manufacturer,
               b.expiry_date, b.qc_status, b.blocked, b.disabled
        FROM `tabSC Batch` b
        JOIN `tabSC Item` i ON i.name = b.item
        WHERE b.item IN ({items})
        ORDER BY b.expiry_date DESC LIMIT {lim}
    """.format(
        items=", ".join(["%s"] * len(items)),
        lim=int(limit),
    ), tuple(items), as_dict=True)
```

## Migration

KHÔNG.

## Test plan — `tests/uc29_test.py`

| Test | Scenario |
|---|---|
| `test_trace_nonexistent_batch` | batch_no không tồn tại → exists=False |
| `test_trace_basic_batch_no_movements` | Batch tạo manual không có SLE → exists=True, movements=[] |
| `test_trace_batch_with_movements` | Batch có 3 SLE → movements trả 3 entries sorted by date |
| `test_trace_origin_from_pr` | Batch có SC PR submitted → origin có purchase_receipt + supplier |
| `test_trace_current_stock_per_warehouse` | SLE 2 warehouses → current_stock.by_warehouse có 2 rows |
| `test_trace_current_stock_zero_when_depleted` | SLE +50 / -50 → total_qty=0 |
| `test_trace_dispensing_from_pd` | Batch có SC PD Item submitted → dispensing có entries |
| `test_trace_data_quality_complete` | Batch đủ supplier+lot+mfg+pr → complete=True |
| `test_trace_data_quality_missing_supplier` | Batch không supplier → missing có 'supplier' |
| `test_list_batches_for_item_by_code` | Search item_code → trả batches của item đó |
| `test_list_batches_for_item_by_name` | Search item_name → trả batches |

## Out-of-scope

- Multi-batch comparison (defer)
- Graphical trace visualization (defer UI)
- Cross-batch recall linkage (UC-30/31 territory)

## File changes

1. `supplycore/m10_traceability/UC-29_FLOW.md` — this file
2. `supplycore/m10_traceability/api/trace.py` — full implementation
3. `supplycore/tests/uc29_test.py` — 11 test scenarios
