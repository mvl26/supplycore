# UC Test — M8 — Kế toán & Thanh toán NCC

**Source:** Phase 1 / 03_Use-Case-Diagram-and-Descriptions / UseCase_SupplyCore_v2.0.md
**Cập nhật:** 2026-05-08
**Mục đích:** Test scenario từng UC tương ứng với module này — End-user (BS, dược sĩ, SK, kế toán) hoặc QA tester thực hiện thủ công, hệ thống xác nhận đúng.

> Tham khảo: [`docs/UC_COVERAGE.md`](../../docs/UC_COVERAGE.md) cho overview 37 UCs. [`docs/UAT_PROCEDURE.md`](../../docs/UAT_PROCEDURE.md) cho luồng E2E xuyên suốt.

## UC-24 — Tạo & 3-way Match PI

**Actor:** Accountant
**Status:** ✅ OK (slice 1 + slice mới make_invoice_from_pr)
**Pre-condition:** PR submit + qc_status≠Rejected.

### Test scenario

1. Trên PR submit, button **"Tạo Purchase Invoice"**.
2. PI draft auto-fetch: supplier, PO link, items + supplier_invoice_no = `AUTO-<PR>` (placeholder).
3. User sửa supplier_invoice_no thật (số HĐ NCC) + vat_rate (default 10%).
4. Submit PI:
5.   - 3-way match check: |PI - PO| / PO ≤ 1% → "Match"; > 1% → "Mismatch"; > 5% hard cap → SC-E009
6.   - GL post Dr 152 (subtotal) + Dr 1331 (vat) / Cr 331 (grand_total)
7.   - PI.outstanding_amount = grand_total

### Expected result

- Σ Dr = Σ Cr (cân kế toán).
- PI duplicate cùng PR throw SC-E007.

### Checklist Pass/Fail

- [ ] PR→PI auto-fetch OK
- [ ] 3-way match status đúng
- [ ] GL cân + đúng VAS account
- [ ] Negative: PI duplicate

---

## UC-25 — Payment Entry & Track AP

**Actor:** Accountant / Manager
**Status:** ✅ OK
**Pre-condition:** PI submit có outstanding > 0.

### Test scenario

1. `/app/sc-payment-entry/new`.
2. supplier + payment_date + payment_method (Bank Transfer/Cash/Check/...)
3. amount + bank_account.
4. References child table: append PI link + allocated_amount.
5. Submit → GL Dr 331 / Cr 1121 + update PI.outstanding.

### Expected result

- PI.status auto: Paid (outstanding=0) / Partly Paid / Overdue.
- Slice 2 alert→action: button "Tạo Payment Entry" trên overdue_payment alert.

### Checklist Pass/Fail

- [ ] PE submit → PI.outstanding giảm
- [ ] PE auto từ alert (slice 2)
- [ ] GL Dr 331 / Cr 1121 đúng

---

## UC-26 — Báo cáo Tài chính (Supply Items)

**Actor:** Accountant / Manager / Executive
**Status:** ⚠ Partial (Trial Balance / AP Aging chưa build)
**Pre-condition:** SC GL Entry + SC PI có data.

### Test scenario

1. API `get_executive_dashboard(period)` trả 6 KPI: stock_value, monthly_cost, ap_outstanding, pending_pos, expiring_soon, low_stock_items.
2. API `supplier_balance(supplier)` trả outstanding + overdue + credit_limit_used%.
3. (Defer) Trial Balance / AP Aging / Stock Cost report build qua Frappe Report Builder UI (no code, ~2-4h config).

### Expected result

- Dashboard < 2s.
- Top 5 items by consumption value.

### Checklist Pass/Fail

- [ ] Dashboard 6 KPI
- [ ] supplier_balance API
- [ ] (Defer) Trial Balance via Report Builder

---


## Tổng kết module m8_accounting

**Total UCs:** 3

**Sign-off:**
- [ ] UC-24 Tạo & 3-way Match PI — Tester: __________ Date: __________
- [ ] UC-25 Payment Entry & Track AP — Tester: __________ Date: __________
- [ ] UC-26 Báo cáo Tài chính (Supply Items) — Tester: __________ Date: __________
