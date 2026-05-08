# M5 — Lô, Hạn dùng & FEFO

Module quản lý vòng đời lô hàng (`SC Batch`) + thực thi nguyên tắc FEFO khi xuất kho + cảnh báo hết hạn.

> ⚠ **v0.2 — chỉ Frappe**: Batch giờ là `SC Batch`, query qua `SC Stock Ledger Entry`.

## DocTypes

| DocType | Loại | Mô tả |
|---|---|---|
| `SC Batch` | Master | Lô hàng — expiry, manufacturing, supplier, blocked flag |
| `FEFO Picker Rule` | Master | Cấu hình FEFO theo warehouse + item_group |
| `Batch Expiry Alert` | Log | Mỗi lần scheduler phát hiện batch sắp hết hạn |

**Master phụ thuộc:** `SC Item` · `SC Supplier` · `SC Warehouse` · `SC Stock Ledger Entry`

## Naming series

- `[ItemCode]-YYYYMM-XXXX` — SC Batch (auto khi PR submit)
- `SC-FEFO-#####` — FEFO Picker Rule
- `SC-EXP-YYYY-#####` — Batch Expiry Alert

## Logic FEFO (validate SC Stock Entry Issue/Transfer)

```
Cho mỗi row có batch + item + from_warehouse:

1. SC Batch lookup → expiry_date, blocked, block_reason

2. Block expired:
   if expiry < today → throw SC-E003 EXPIRY_TOO_CLOSE

3. Block recalled:
   if blocked = 1 → throw SC-E008 BATCH_RECALLED

4. FEFO violation check:
   Tìm SC Batch khác cùng (item, warehouse) có:
     - expiry < current row.batch.expiry  (gần hết hạn hơn)
     - SC SLE.qty_change SUM > 0  (còn hàng)
     - blocked = 0 và disabled = 0
     - chưa được dùng trong row khác của SE này

   Nếu có:
     ┌─ row.fefo_override = 0 + strict mode → throw SC-E001
     ├─ row.fefo_override = 0 + warn mode  → msgprint orange
     ├─ row.fefo_override = 1 + reason rỗng → throw "cần ghi lý do"
     └─ row.fefo_override = 1 + có reason  → log audit
```

`strict_mode` resolve theo: FEFO Picker Rule (warehouse+item_group match) → SupplyCore Settings.fefo_strict_mode (default true).

## Luồng hoạt động

```
[A] SC Batch tạo từ SC Purchase Receipt submit
    │ Batch.qc_status = Pending; chờ SC Quality Inspection
    │ Hook Batch.after_insert → register_batch:
    │   - Validate expiry; cảnh báo nếu < min_shelf_life
    ▼
[B] SC Quality Inspection submit
    │ Update SC Batch.qc_status (Accepted/Rejected/Conditional)
    │ Nếu Rejected → Batch.blocked = 1
    ▼
[C] SC Stock Entry Issue
    │ enforce_fefo (controller validate):
    │   - block expired/blocked
    │   - check FEFO order violation
    ▼
    Submit → SC SLE -qty_change
    │
[D] Daily scheduler scan_expiring_batches
    │ Query SC Batch với expiry trong window cấu hình
    │ Tạo Batch Expiry Alert (severity Critical / Warning)
    │ Email cảnh báo SK + MGR + PHARM
```

## API endpoints

| Endpoint | Mô tả |
|---|---|
| `POST /api/method/supplycore.api.fefo.get_suggested_batches` | Trả batches sorted FEFO + cumulative suggested_qty |
| `GET /api/method/supplycore.api.fefo.check_batch_status?batch_no=X` | Quick check expiry + blocked |

Body get_suggested_batches:
```json
{"item_code": "VT001", "warehouse": "Kho Tổng", "qty": 50, "uom": "Hộp"}
```

Response:
```json
{
  "batches": [
    {"batch_no", "expiry_date", "available_qty", "suggested_qty", "days_to_expiry", "severity"}
  ],
  "total_available": 350,
  "fully_satisfied": true,
  "shortfall": 0
}
```

Severity scale:
- `Critical` — < 30 ngày
- `Warning` — 30..90 ngày
- `OK` — > 90 ngày
- `Expired` / `NoExpiry`

## Scheduler

- **daily** `m5_fefo.api.fefo_picker.scan_expiring_batches`:
  - Query SC Batch chưa block, expiry trong [today, today + warning_days]
  - Tạo Batch Expiry Alert mới (skip nếu đã có alert OPEN cùng severity tuần qua)
  - Gửi email cho SK + MGR + Pharmacy

## Coverage Phase 1

| BR | Mô tả | Trạng thái |
|---|---|---|
| BR-M5-01 | FEFO tự động khi xuất kho | ✓ SC Stock Entry validate |
| BR-M5-02 | Cảnh báo 30/60/90 ngày + block expired | ✓ scheduler + Batch.blocked |
| BR-M5-03 | Recall theo lô | ✓ SC Batch.blocked + block_reason; M10 sẽ wrap |
| UC-15 | Batch Tracking | ✓ |
| UC-16 | FEFO Issue | ✓ |
| UC-17 | Expiry Alert | ✓ |

## Error codes

- `SC-E001 FEFO_OVERRIDE` — vi phạm FEFO mà không có override+reason
- `SC-E003 EXPIRY_TOO_CLOSE` — batch hết hạn
- `SC-E008 BATCH_RECALLED` — batch bị block

## Vận hành

- `/app/sc-batch` → list lô hàng, set blocked khi recall
- `/app/batch-expiry-alert?resolved=0` → list cảnh báo cần xử lý
- `/app/fefo-picker-rule` → cấu hình strict_mode per warehouse/group
- SupplyCore Settings → `fefo_strict_mode` global default

## Integration với module khác

**Incoming events (module này nhận trigger từ):**
- M3 PR auto-tạo SC Batch + ghi qc_status từ M3 QI
- M10 Recall Notice.on_submit → set Batch.blocked=1

**Outgoing events (module này trigger / cung cấp data cho):**
- FEFO sort → M6 TR + M7 DR + bất kỳ Stock Entry Issue
- API `get_suggested_batches` → return FEFO order với severity (Critical/Warning/OK)
- Daily scheduler `scan_expiring_batches` → M11 Alert (expiring_batch)
- SE validate: block expired/blocked batch (SC-E001 / SC-E008)

Xem [`FLOW.md`](../../FLOW.md) cho sơ đồ tổng thể.
