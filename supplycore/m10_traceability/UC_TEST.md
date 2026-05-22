# UC Test — M10 — Truy xuất & Recall

**Source:** Phase 1 / 03_Use-Case-Diagram-and-Descriptions / UseCase_SupplyCore_v2.0.md
**Cập nhật:** 2026-05-08
**Mục đích:** Test scenario từng UC tương ứng với module này — End-user (BS, dược sĩ, SK, kế toán) hoặc QA tester thực hiện thủ công, hệ thống xác nhận đúng.

> Tham khảo: [`docs/UC_COVERAGE.md`](../../docs/UC_COVERAGE.md) cho overview 37 UCs. [`docs/UAT_PROCEDURE.md`](../../docs/UAT_PROCEDURE.md) cho luồng E2E xuyên suốt.

## UC-29 — Trace Item Origin

**Actor:** Manager / Storekeeper
**Status:** ✅ OK
**Pre-condition:** Batch có data SLE + PD.

### Test scenario

1. API `GET /api/method/supplycore.api.trace.get_batch_trace?batch_no=<X>`.
2. Returns: batch metadata + source PR + movements (SLE) + patient_dispensings + current qty per warehouse.

### Expected result

- total_movements = số SLE rows.
- total_patient_uses = số PD Item.
- remaining_qty = sum balance per warehouse.

### Checklist Pass/Fail

- [ ] API get_batch_trace trả đầy đủ
- [ ] patient_dispensings list đúng
- [ ] current_qty_per_warehouse cân với SLE

---

## UC-30 — Recall Management

**Actor:** Manager / Storekeeper / QC Officer
**Status:** ✅ OK (slice 3 spec đã có cho email + UI mark)
**Pre-condition:** Batch xác định bị recall.

### Test scenario

1. `/app/sc-recall-notice/new`.
2. recall_date + recall_type (Voluntary/Mandatory/Precautionary).
3. severity (Class I Critical / II High / III Low).
4. item + batch_no (auto fetch supplier).
5. recall_reason + regulatory_reference.
6. Click "Populate Affected Items" → quét SLE + PD Item, build child rows phân loại location_type (Warehouse/Department/Patient).
7. Submit Recall:
8.   - Batch.blocked=1 → chặn mọi SE Issue/Transfer (SC-E008)
9.   - status=Issued
10. (Slice 3 chưa implement code — spec ở `docs/superpowers/specs/2026-05-08-recall-notify-design.md`):
11.   - Email Khoa head_user + Pharmacy + Manager (Class I+II)
12.   - Button "Đánh dấu đã liên hệ" bulk update affected_items.status

### Expected result

- Issue batch recalled → SC-E008.
- outstanding_qty = sum(qty_dispensed - recovered_qty - destroyed_qty).
- status auto Completed khi outstanding=0.

### Checklist Pass/Fail

- [ ] Populate affected_items đầy đủ
- [ ] Submit → batch.blocked + chặn issue
- [ ] Update recovered_qty → outstanding giảm
- [ ] (TODO slice 3) email notify + UI mark contacted

---

## UC-31 — Investigate Stock Loss/Variance

**Actor:** Manager / SysAdmin / Auditor
**Status:** ✅ OK
**Pre-condition:** Phát hiện thất thoát hoặc nghi ngờ.

### Test scenario

1. API `get_audit_trail(item, warehouse, from_date, to_date)`.
2. Returns: full SLE history + cancelled count + total_in/out/net + entries với owner + voucher.

### Expected result

- cancelled_count > 0 = có SLE đã cancel (nghi vấn).
- net_movement ≠ stock_check → cần thanh tra.

### Checklist Pass/Fail

- [ ] API get_audit_trail trả full history
- [ ] Filter theo period đúng
- [ ] Owner + modified_by hiển thị

---


## Tổng kết module m10_traceability

**Total UCs:** 3

**Sign-off:**
- [ ] UC-29 Trace Item Origin — Tester: __________ Date: __________
- [ ] UC-30 Recall Management — Tester: __________ Date: __________
- [ ] UC-31 Investigate Stock Loss/Variance — Tester: __________ Date: __________
