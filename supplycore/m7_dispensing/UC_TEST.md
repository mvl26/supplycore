# UC Test — M7 — Cấp phát & BHYT

**Source:** Phase 1 / 03_Use-Case-Diagram-and-Descriptions / UseCase_SupplyCore_v2.0.md
**Cập nhật:** 2026-05-08
**Mục đích:** Test scenario từng UC tương ứng với module này — End-user (BS, dược sĩ, SK, kế toán) hoặc QA tester thực hiện thủ công, hệ thống xác nhận đúng.

> Tham khảo: [`docs/UC_COVERAGE.md`](../../docs/UC_COVERAGE.md) cho overview 37 UCs. [`docs/UAT_PROCEDURE.md`](../../docs/UAT_PROCEDURE.md) cho luồng E2E xuyên suốt.

## UC-20 — Tạo Dispensing Request (DR)

**Actor:** Ward Staff
**Status:** ✅ OK
**Pre-condition:** Department + From warehouse có sẵn.

### Test scenario

1. `/app/sc-dispensing-request/new`.
2. purpose: Routine / Urgent / Patient-Specific.
3. Department + from_warehouse + (optional) patient.
4. Items: requested_qty per item.
5. Submit → status=Approved.

### Expected result

- Patient field hiện chỉ khi purpose=Patient-Specific.

### Checklist Pass/Fail

- [ ] DR Routine submit OK
- [ ] DR Patient-Specific cần patient link

---

## UC-21 — Process & Dispense Stock

**Actor:** Storekeeper / Pharmacy Officer
**Status:** ✅ OK
**Pre-condition:** DR Approved.

### Test scenario

1. Trên DR Approved, button "Tạo SE" hoặc tạo SE Issue manual.
2. SE Material Issue + items từ DR + batch FEFO.
3. Submit SE → SLE -qty.
4. Tạo SC Patient Dispensing (link DR + SE).
5. Submit PD → BHYT auto-calc.
6. Print Format `dispensing_slip.html` để in phiếu cấp.

### Expected result

- FEFO bắt buộc cho SE Issue.
- Print format render đầy đủ thông tin BN + items + cost.

### Checklist Pass/Fail

- [ ] SE Issue từ DR + FEFO batch
- [ ] PD auto-fetch + submit
- [ ] Print dispensing slip

---

## UC-22 — Record Item Usage per Patient

**Actor:** Ward Staff
**Status:** ✅ OK
**Pre-condition:** Patient + DR Patient-Specific.

### Test scenario

1. Tạo PD với patient + items.
2. Mỗi PD Item ghi: qty, unit_cost, batch, bhyt_amount, patient_pays, ceiling_overage.
3. BHYT calc:
4.   - cfg = active SC BHYT Code Config (priority item-spec > group > fallback)
5.   - effective_rate = min(cfg.payment_rate, patient.bhyt_payment_rate)
6.   - cap = min(unit_cost, cfg.ceiling_price)
7.   - bhyt_amount = qty × cap × effective_rate / 100
8.   - patient_pays = total_cost - bhyt_amount
9. Submit PD.

### Expected result

- total_cost = bhyt_covered + patient_pays (cân tổng).
- ceiling_overage > 0 nếu unit_cost vượt ceiling.

### Checklist Pass/Fail

- [ ] PD calc BHYT đúng công thức
- [ ] Cân tổng total = bhyt + patient_pays
- [ ] Trace qua get_batch_trace tìm BN

---

## UC-23 — Quản lý mã BHYT N01-N09

**Actor:** Manager / Accountant
**Status:** ✅ OK
**Pre-condition:** —

### Test scenario

1. `/app/sc-bhyt-code-config/new`.
2. Code: N01..N09.
3. item_specific (Link SC Item) hoặc item_group (Link).
4. ceiling_price + payment_rate (%).
5. valid_from + valid_to.
6. Save → Active.

### Expected result

- Priority lookup: item-specific > item_group > fallback (no link).
- Multiple cfg cùng item → pick latest valid.

### Checklist Pass/Fail

- [ ] Tạo cfg N01 cho item cụ thể
- [ ] Tạo cfg N02 cho item_group
- [ ] PD pick đúng theo priority

---


## Tổng kết module m7_dispensing

**Total UCs:** 4

**Sign-off:**
- [ ] UC-20 Tạo Dispensing Request (DR) — Tester: __________ Date: __________
- [ ] UC-21 Process & Dispense Stock — Tester: __________ Date: __________
- [ ] UC-22 Record Item Usage per Patient — Tester: __________ Date: __________
- [ ] UC-23 Quản lý mã BHYT N01-N09 — Tester: __________ Date: __________
