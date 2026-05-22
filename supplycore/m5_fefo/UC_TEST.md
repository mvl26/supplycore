# UC Test — M5 — Lô, Hạn dùng & FEFO

**Source:** Phase 1 / 03_Use-Case-Diagram-and-Descriptions / UseCase_SupplyCore_v2.0.md
**Cập nhật:** 2026-05-08
**Mục đích:** Test scenario từng UC tương ứng với module này — End-user (BS, dược sĩ, SK, kế toán) hoặc QA tester thực hiện thủ công, hệ thống xác nhận đúng.

> Tham khảo: [`docs/UC_COVERAGE.md`](../../docs/UC_COVERAGE.md) cho overview 37 UCs. [`docs/UAT_PROCEDURE.md`](../../docs/UAT_PROCEDURE.md) cho luồng E2E xuyên suốt.

## UC-15 — Quản lý thông tin Lô

**Actor:** Storekeeper
**Status:** ✅ OK
**Pre-condition:** PR submit auto-tạo SC Batch.

### Test scenario

1. `/app/sc-batch?item=<X>` list batch của item.
2. Mỗi batch có: batch_id, mfg/exp date, supplier, qc_status, blocked, blocked_reason.
3. qc_status auto-rollup từ QI submit.

### Expected result

- Batch.blocked=1 chặn mọi SE Issue/Transfer (SC-E008 BATCH_RECALLED hoặc SC-E007 QC_REJECTED).
- Batch.expiry_date < today → expired → SE issue throw SC-E001.

### Checklist Pass/Fail

- [ ] Batch auto-tạo từ PR có format đúng
- [ ] qc_status rollup từ QI
- [ ] Batch.blocked chặn SE

---

## UC-16 — Issue Stock theo FEFO

**Actor:** Storekeeper / System
**Status:** ✅ OK
**Pre-condition:** Có nhiều batch cùng item với expiry khác nhau.

### Test scenario

1. API `POST /api/method/supplycore.api.fefo.get_suggested_batches`
2.   payload: `{item_code, warehouse, qty}`
3.   Returns: batches sorted ASC theo expiry_date với suggested_qty cumulative.
4. Tạo SC Stock Entry Issue: nhập batch theo gợi ý FEFO.
5. Submit SE → validate fefo_strict_mode (Settings).

### Expected result

- Vi phạm FEFO (chọn batch sau khi có batch trước hết hạn) → throw SC-E001 trừ khi override + reason.
- Expired/blocked batch → block luôn.

### Checklist Pass/Fail

- [ ] FEFO API trả ASC theo expiry
- [ ] SE Issue dùng batch FEFO → OK
- [ ] Negative: chọn batch sai → SC-E001

---

## UC-17 — Cảnh báo Hạn dùng

**Actor:** System / Manager / Storekeeper
**Status:** ✅ OK
**Pre-condition:** Daily scheduler enabled.

### Test scenario

1. Daily 02:00 — `scan_expiring_batches` chạy.
2. M11 Alert Rule `expiring_batch` (threshold default 30 ngày) trigger.
3. Tạo SC Alert per batch sắp hết hạn (dedup 7 ngày).
4. Slice 2: button **"Chuyển vào Kho Cách ly"** trên alert → SE Material Transfer to Quarantine warehouse.

### Expected result

- Severity scale: Critical (<30d), Warning (30-90d), OK (>90d).
- Email daily summary qua send_daily_kpi.

### Checklist Pass/Fail

- [ ] Scheduler tạo alert đúng
- [ ] Dedup không tạo duplicate trong 7 ngày
- [ ] Slice 2 action quarantine OK

---


## Tổng kết module m5_fefo

**Total UCs:** 3

**Sign-off:**
- [ ] UC-15 Quản lý thông tin Lô — Tester: __________ Date: __________
- [ ] UC-16 Issue Stock theo FEFO — Tester: __________ Date: __________
- [ ] UC-17 Cảnh báo Hạn dùng — Tester: __________ Date: __________
