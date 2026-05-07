# M3 — Tiếp nhận & Kiểm tra QC

Module xử lý **SC Purchase Receipt** (phiếu nhập kho) + **SC Quality Inspection** (kiểm tra chất lượng) + **QC Checklist Template** (mẫu QC theo nhóm vật tư).

> ⚠ **v0.2 — chỉ Frappe**: PR/QI là SC*, không dùng ERPNext.

## DocTypes

| DocType | Loại | Mô tả |
|---|---|---|
| `SC Purchase Receipt` | Submittable | Phiếu nhập kho — link SC PO |
| `SC Purchase Receipt Item` | Child | Dòng item nhận, kèm batch_no + expiry để auto tạo SC Batch |
| `SC Quality Inspection` | Submittable | QC từng item theo checklist, status Accepted/Rejected |
| `SC QI Reading` | Child | Tiêu chí check-list từng dòng |
| `QC Checklist Template` | Master | Mẫu checklist gắn nhóm SC Item Group |
| `QC Checklist Item` | Child | Tiêu chí trong template |

## Naming series

- `SC-PR-YYYY-#####` — SC Purchase Receipt
- `SC-QI-YYYY-#####` — SC Quality Inspection
- `SC-QCT-#####` — QC Checklist Template

## Luồng hoạt động

```
[1] SC-STOREKEEPER tạo SC Purchase Receipt
        │ chọn supplier + purchase_order (link SC PO)
        │ thêm rows: item, qty, expiry_date, supplier_batch_no, target_bin
        ▼
    Submit
        │
        ├─ create_batches_if_needed():
        │    Cho row có expiry_date + chưa có batch_no
        │    → tạo SC Batch tự động (id = ItemCode-YYYYMM-XXXX)
        │
        ├─ post_stock_ledger():
        │    Mỗi row → SC Stock Ledger Entry +qty_change
        │    voucher_type=SC Purchase Receipt
        │
        ├─ auto_create_qi() (nếu qc_required=1):
        │    Cho mỗi row → 1 SC Quality Inspection draft
        │    template = SC Item Group default OR global fallback
        │    readings populate từ template criteria
        │
        └─ update_po_received_qty():
             Update SC PO Item.received_qty cumulative từ tất cả PR
             PO.status: Received | Partially Received
        ▼
[2] SC-STOREKEEPER mở SC QI mỗi item
        │ tick từng reading: Accepted / Rejected
        │ overall_status auto-derive
        ▼
    Submit QI
        │
        ├─ Update SC Batch.qc_status (Accepted/Rejected/Conditional)
        │
        ├─ Rollup PR.qc_status:
        │    - Tất cả QI Accepted → PR.qc_status = Pass
        │    - Tất cả QI Rejected → PR.qc_status = Fail
        │    - Mixed → PR.qc_status = Partial Pass
        │    - Còn item chưa QI → Pending
        │
        └─ Nếu Rejected:
             - SC Batch.blocked = 1, block_reason = QC Rejected by QI
             - (TODO: tạo PR draft is_return=1)
             - Email NCC + nội bộ team
        ▼
[3] Khi PR.qc_status = Pass → batch sẵn sàng xuất kho (M5/M7)
```

## Validate quan trọng

- PR.posting_date validate row.expiry_date < SC Settings.fefo_min_shelf_life_days → cảnh báo (SC-E003)
- Tolerance qty PR vs PO: ±2% cảnh báo, +5% throw SC-E009 (TODO khi link PO)
- SC Batch tự sinh nếu item.has_batch_no=1 và row có expiry_date

## Coverage Phase 1

| BR | Mô tả | Trạng thái |
|---|---|---|
| BR-M3-01 | Mọi PR phải QC bắt buộc | ✓ on_submit auto-create QI nếu qc_required=1 |
| BR-M3-02 | Partial receipt + backorder | ✓ field `backorder_for`, update `received_qty` cumulative |
| BR-M3-03 | Lưu lý do reject + email NCC | ✓ `failure_reason` + auto-block batch + email |
| UC-09 | PR | ✓ |
| UC-10 | QC checklist | ✓ Template by Item Group |
| UC-11 | Trả NCC | ⚠ schema có (`is_return`); auto-tạo defer |

## Hooks

Logic chính nằm trong CONTROLLER `sc_purchase_receipt.py` và `sc_quality_inspection.py` — không qua ERPNext doc_events.

## Error codes

- `SC-E003 EXPIRY_TOO_CLOSE`
- `SC-E009 PR_OVERAGE` (>+5% so PO)
- `SC-E004 QC_FAILED` (rejected)

## Vận hành

- `/app/qc-checklist-template/new` → tạo mẫu checklist cho mỗi SC Item Group
- `/app/sc-purchase-receipt/new` → nhận hàng từ NCC
- `/app/sc-quality-inspection?docstatus=0` → list QI chờ check
