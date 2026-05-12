# UC Test — M9 — Kiểm kê & Đối soát

**Source:** Phase 1 / 03_Use-Case-Diagram-and-Descriptions / UseCase_SupplyCore_v2.0.md
**Cập nhật:** 2026-05-08
**Mục đích:** Test scenario từng UC tương ứng với module này — End-user (BS, dược sĩ, SK, kế toán) hoặc QA tester thực hiện thủ công, hệ thống xác nhận đúng.

> Tham khảo: [`docs/UC_COVERAGE.md`](../../docs/UC_COVERAGE.md) cho overview 37 UCs. [`docs/UAT_PROCEDURE.md`](../../docs/UAT_PROCEDURE.md) cho luồng E2E xuyên suốt.

## UC-27 — Lập & Thực hiện Kiểm kê

**Actor:** Storekeeper / Manager
**Status:** ✅ OK
**Pre-condition:** —

### Test scenario

1. `/app/sc-inventory-count-sheet/new`.
2. count_date + warehouse + count_type (Cycle Count / Annual / Spot Check).
3. Click "Auto-load Items" → snapshot system_qty từ SLE per item per batch.
4. Print phiếu đếm (anti-bias: hide system_qty nếu Settings.hide_system_qty=1).
5. SK đếm thực tế + nhập actual_qty per row.
6. Save ICS draft → submit.

### Expected result

- system_qty snapshot tại count_date.
- difference = actual_qty - system_qty.
- recount_threshold_pct vượt → flag recount.

### Checklist Pass/Fail

- [ ] ICS auto-load items đúng
- [ ] Submit ICS với actual_qty
- [ ] Recount flag khi diff > threshold

---

## UC-28 — Reconcile System vs Physical

**Actor:** Storekeeper / Accountant / Manager
**Status:** ✅ OK
**Pre-condition:** ICS submit có rows với diff ≠ 0.

### Test scenario

1. Trên ICS submit, button "Make Stock Reconciliation".
2. SR draft auto-fetch rows có diff > 0.
3. Review + Submit SR.
4. Submit → SLE adjustment ±diff_qty + GL post.

### Expected result

- GL: thừa kho Dr 152 / Cr 642 (giảm CP); thiếu kho Dr 642 / Cr 152 (tăng CP).

### Checklist Pass/Fail

- [ ] ICS → SR fetch đúng
- [ ] SR submit → SLE + GL cân
- [ ] Test thừa + test thiếu

---


## Tổng kết module m9_stocktake

**Total UCs:** 2

**Sign-off:**
- [ ] UC-27 Lập & Thực hiện Kiểm kê — Tester: __________ Date: __________
- [ ] UC-28 Reconcile System vs Physical — Tester: __________ Date: __________
