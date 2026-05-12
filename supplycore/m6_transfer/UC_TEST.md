# UC Test — M6 — Luân chuyển Nội bộ

**Source:** Phase 1 / 03_Use-Case-Diagram-and-Descriptions / UseCase_SupplyCore_v2.0.md
**Cập nhật:** 2026-05-08
**Mục đích:** Test scenario từng UC tương ứng với module này — End-user (BS, dược sĩ, SK, kế toán) hoặc QA tester thực hiện thủ công, hệ thống xác nhận đúng.

> Tham khảo: [`docs/UC_COVERAGE.md`](../../docs/UC_COVERAGE.md) cho overview 37 UCs. [`docs/UAT_PROCEDURE.md`](../../docs/UAT_PROCEDURE.md) cho luồng E2E xuyên suốt.

## UC-18 — Luân chuyển Nội bộ (Transfer Request)

**Actor:** Storekeeper / Manager
**Status:** ✅ OK
**Pre-condition:** Stock có ở from_warehouse.

### Test scenario

1. `/app/sc-transfer-request/new`.
2. from_warehouse + to_warehouse (must different + not group).
3. transfer_type: Routine / Urgent / Replenishment / Return to Main.
4. required_by date.
5. Items: requested_qty per item.
6. Submit → status=Approved.
7. Trên TR submit, button **"Tạo SE"** → SE Material Transfer draft.
8. SK chọn batch (FEFO suggest), submit SE → 2 SLE rows ±qty.
9. TR.status=Received tự động.

### Expected result

- Validate from_warehouse ≠ to_warehouse, both not group.
- Cross-tier transfer (vd Main → Department) flag `requires_manager_approval` (advisory; workflow defer).

### Checklist Pass/Fail

- [ ] TR submit OK
- [ ] SE từ TR tạo + submit
- [ ] 2 SLE rows đúng dấu
- [ ] TR.status=Received sau SE submit

---

## UC-19 — Adjust Stock (Reconciliation)

**Actor:** Storekeeper / Manager / Accountant
**Status:** ✅ OK (wire qua M9)
**Pre-condition:** ICS đã đếm + có chênh lệch.

### Test scenario

1. ICS submit → trên ICS form, button "Make Stock Reconciliation".
2. SR draft auto-fetch rows có difference > 0.
3. Review + Submit SR.
4. Submit → SLE adjustment ±diff_qty + GL Dr 152 / Cr 642 (or reverse).

### Expected result

- GL post đúng VAS: thừa Dr 152 / Cr 642, thiếu Dr 642 / Cr 152.
- Recount threshold (Settings.recount_threshold_pct, default 5%) → warn cần recount.

### Checklist Pass/Fail

- [ ] ICS → SR auto-fetch
- [ ] SR submit → SLE + GL
- [ ] GL Σ Dr = Σ Cr

---


## Tổng kết module m6_transfer

**Total UCs:** 2

**Sign-off:**
- [ ] UC-18 Luân chuyển Nội bộ (Transfer Request) — Tester: __________ Date: __________
- [ ] UC-19 Adjust Stock (Reconciliation) — Tester: __________ Date: __________
