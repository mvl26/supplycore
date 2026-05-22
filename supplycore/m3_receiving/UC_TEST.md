# UC Test — M3 — Tiếp nhận & QC

**Source:** Phase 1 / 03_Use-Case-Diagram-and-Descriptions / UseCase_SupplyCore_v2.0.md
**Cập nhật:** 2026-05-08
**Mục đích:** Test scenario từng UC tương ứng với module này — End-user (BS, dược sĩ, SK, kế toán) hoặc QA tester thực hiện thủ công, hệ thống xác nhận đúng.

> Tham khảo: [`docs/UC_COVERAGE.md`](../../docs/UC_COVERAGE.md) cho overview 37 UCs. [`docs/UAT_PROCEDURE.md`](../../docs/UAT_PROCEDURE.md) cho luồng E2E xuyên suốt.

## UC-09 — Nhận hàng & Tạo PR

**Actor:** Storekeeper
**Status:** ✅ OK (slice mới: PO→PR auto-fetch)
**Pre-condition:** SC PO submit chưa Received.

### Test scenario

1. Trên SC PO submit, click button **"Tạo Purchase Receipt"**.
2. PR draft tự fetch: supplier, purchase_order, posting_date, to_warehouse, qc_required=1, items với qty=remaining.
3. Cho mỗi PR item: nhập batch (hoặc bỏ trống để auto-tạo), manufacturing_date, expiry_date, supplier_batch_no.
4. Submit PR.
5. Sau submit (tự động):
6.   - SC Batch auto-tạo nếu item.has_batch_no=1 (format `<item>-<YYYYMM>-<rand>`)
7.   - SC Stock Ledger Entry (+qty) post tại to_warehouse
8.   - SC Quality Inspection auto-tạo nếu qc_required=1
9.   - PO Item.received_qty cập nhật + PO.status=Received hoặc Partially Received

### Expected result

- Validate expiry_date ≥ today + min_shelf_life_days (Settings, default 30) → warn nếu nhỏ hơn.
- Negative: expiry < today → throw SC-E003.

### Checklist Pass/Fail

- [ ] PO→PR auto-fetch đúng
- [ ] PR submit → SLE + Batch + QI tự tạo
- [ ] PO.received_qty + status update
- [ ] Negative: expiry quá sát → warn

---

## UC-10 — Quality Inspection (QC)

**Actor:** Storekeeper / Manager (QC Officer)
**Status:** ✅ OK
**Pre-condition:** PR submit với qc_required=1.

### Test scenario

1. Mở QI auto-tạo: `/app/sc-quality-inspection?purchase_receipt=<PR>`.
2. Form fetch sẵn: purchase_receipt, item, batch, received_qty, checklist_template (theo item_group).
3. Readings child table: từng criteria từ template.
4. Cho mỗi reading: chọn status Accepted/Rejected/N/A + reading_value + remarks.
5. Set `manual_inspection=1` (tránh auto-flip).
6. Set `overall_status=Accepted` (sau khi tất cả readings = Accepted).
7. Submit QI.

### Expected result

- Rollup PR.qc_status: nếu tất cả QI submit có overall_status=Accepted → PR.qc_status=Pass.
- Rollup Batch.qc_status: =Accepted/Rejected/Conditional theo QI.
- **UAT-01 naming inconsistency:** PR.qc_status options Pass/Fail/Partial Pass khác QI/Batch options Accepted/Rejected/Conditional — đã document.

### Checklist Pass/Fail

- [ ] QI auto-tạo có readings đúng template
- [ ] Submit QI Accepted → PR.qc_status=Pass + Batch.qc_status=Accepted
- [ ] Submit QI Rejected → Batch.blocked=1 + auto-tạo PR Return draft (UC-11)

---

## UC-11 — Xử lý Trả hàng NCC

**Actor:** Storekeeper / Accountant
**Status:** ✅ OK (wire-up 2026-05-08)
**Pre-condition:** QI submit Rejected.

### Test scenario

1. Submit QI với overall_status=Rejected + failure_reason.
2. System tự động:
3.   - Batch.blocked=1 + block_reason ghi tên QI
4.   - Tạo SC Purchase Receipt Return draft với is_return=1, link supplier + PO + original PR (qua remarks)
5.   - msgprint với link PR Return mới
6. ACC mở PR Return → review qty + adjust → Submit.
7. Submit PR Return → SLE -qty (qty_sign=-1 trong _post_stock_ledger).

### Expected result

- Idempotent: QI Reject lần 2 cùng PR không tạo Return PR duplicate.
- Print Format "Debit Note" cho PR Return defer (cấu hình UI).

### Checklist Pass/Fail

- [ ] QI Reject → Batch.blocked=1
- [ ] QI Reject → PR Return draft auto-tạo
- [ ] PR Return submit → SLE giảm kho
- [ ] Idempotent guard hoạt động

---


## Tổng kết module m3_receiving

**Total UCs:** 3

**Sign-off:**
- [ ] UC-09 Nhận hàng & Tạo PR — Tester: __________ Date: __________
- [ ] UC-10 Quality Inspection (QC) — Tester: __________ Date: __________
- [ ] UC-11 Xử lý Trả hàng NCC — Tester: __________ Date: __________
