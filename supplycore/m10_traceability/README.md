# M10 — Truy xuất & Recall

Module quản lý **SC Recall Notice** (thu hồi lô) + **API trace** (batch lifecycle + audit trail) — đóng vòng audit pháp lý y tế.

## DocTypes

| DocType | Loại | Mô tả |
|---|---|---|
| `SC Recall Notice` + Affected Item | Submittable | Thông báo thu hồi lô + tracking thu hồi per location |

## Naming series

- `SC-RCL-YYYY-#####`

## Luồng hoạt động

```
[1] MGR/EXEC tạo SC Recall Notice
        │ chọn item + batch_no
        │ recall_type (Voluntary/Mandatory/Precautionary)
        │ severity (Class I/II/III)
        │ recall_reason + regulatory_reference
        │
[2] Click "Populate Affected Items"
        │ Auto-load từ batch trace:
        │   - Tồn kho hiện tại theo warehouse → location_type=Warehouse
        │   - SC Patient Dispensing đã dùng cho BN → location_type=Patient
        │   - SC Stock Entry Material Transfer đã chuyển khoa → location_type=Department
        │
[3] Submit Recall Notice
        │ on_submit:
        │   - SC Batch.blocked = 1
        │   - SC Batch.block_reason = "Recall {name}: {reason}"
        │   - blocked_by + blocked_at set
        │ → MỌI giao dịch xuất kho dùng batch này sẽ throw SC-E008 BATCH_RECALLED (M5 logic)
        │ status = Issued
        │
[4] Theo dõi tiến độ
        │ Per affected_items row: nhập recovered_qty/destroyed_qty
        │ Auto compute outstanding_qty + recall_resolution_pct
        │ Email notify các khoa liên quan (defer)
        │
[5] Khi outstanding = 0 → status auto = Completed
        │ resolution: Return to Supplier / Destroy / Quarantine
        │
[6] Cancel (nếu sai) → batch.blocked = 0 (unblock)
```

## API endpoints

```
GET /api/method/supplycore.api.trace.get_batch_trace?batch_no=X
  Returns full lifecycle:
    - source: PR đã tạo batch (supplier, qc_status)
    - movements: chronological SC SLE (SE/PR/SR/Issue movements)
    - patient_dispensings: BN đã dùng + bhyt_amount
    - current_qty_per_warehouse: tồn còn ở từng kho
    - remaining_qty: tổng còn lại

GET /api/method/supplycore.api.trace.get_audit_trail?item=X&warehouse=Y&from_date&to_date
  Returns điều tra thất thoát (UC-31):
    - rows: full SLE history với user/voucher/qty
    - total_in/out/net + cancelled_count
```

## Coverage Phase 1

| BR / UC | Status |
|---|---|
| UC-29 Truy xuất nguồn gốc batch | ✓ get_batch_trace API đầy đủ chain |
| UC-30 Recall management | ✓ Submit → batch.blocked, populate affected, tracking outstanding |
| UC-31 Điều tra thất thoát | ✓ get_audit_trail API |
| BR-M5-03 Recall theo lô | ✓ |
| Block xuất kho khi recall | ✓ M5 SC-E008 BATCH_RECALLED throw |

## Connections panel hiển thị

- Form **SC Batch** → Connections sang SC Recall Notice (filter batch_no)
- Form **SC Recall Notice** → affected_items child show items đã/chưa thu

## Vận hành

```
1. Phát hiện vấn đề chất lượng → MGR mở /app/sc-recall-notice/new
2. Chọn item + batch → Populate Affected Items (auto load từ trace)
3. Submit → batch tự khóa khắp hệ thống (M5 enforce)
4. Theo dõi: nhập recovered_qty per row khi khoa trả về
5. status = Completed khi outstanding = 0
```
