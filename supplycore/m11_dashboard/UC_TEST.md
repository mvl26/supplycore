# UC Test — M11 — Dashboard & Alerts

**Source:** Phase 1 / 03_Use-Case-Diagram-and-Descriptions / UseCase_SupplyCore_v2.0.md
**Cập nhật:** 2026-05-08
**Mục đích:** Test scenario từng UC tương ứng với module này — End-user (BS, dược sĩ, SK, kế toán) hoặc QA tester thực hiện thủ công, hệ thống xác nhận đúng.

> Tham khảo: [`docs/UC_COVERAGE.md`](../../docs/UC_COVERAGE.md) cho overview 37 UCs. [`docs/UAT_PROCEDURE.md`](../../docs/UAT_PROCEDURE.md) cho luồng E2E xuyên suốt.

## UC-32 — Executive Dashboard

**Actor:** Executive / Manager
**Status:** ⚠ Partial (frontend Workspace defer)
**Pre-condition:** Data có ở các module.

### Test scenario

1. API `GET /api/method/supplycore.api.kpi.get_executive_dashboard?period=this_month`.
2. Returns 6 KPI: stock_value, monthly_cost, ap_outstanding, pending_pos, expiring_soon, low_stock_items + top_items + open_alerts breakdown.
3. (Defer) Frappe Workspace + Number Cards (no code, ~2-3h config qua /app/build).

### Expected result

- period: today / this_week / this_month / this_quarter / this_year.
- top_items 5 mặt hàng tiêu thụ nhiều nhất.

### Checklist Pass/Fail

- [ ] API trả đủ 6 KPI
- [ ] Period filter hoạt động
- [ ] (Defer) Workspace UI

---

## UC-33 — Configure Auto-Alerts

**Actor:** SysAdmin / Manager
**Status:** ✅ OK
**Pre-condition:** —

### Test scenario

1. `/app/sc-alert-rule/new`.
2. alert_type: 7 loại — expiring_batch, contract_expiring, fc_remaining_low, low_stock, overdue_payment, qc_pending, recall_outstanding.
3. severity (Critical/Warning/Info), threshold_value, frequency.
4. recipient_roles (CSV vd "SupplyCore Manager,Pharmacy Officer").
5. enabled=1.
6. Daily 02:00 → scan_alerts() chạy → tạo SC Alert (dedup 7-day window theo rule × reference).

### Expected result

- scan_alerts trả total_created mỗi run.
- Dedup: cùng rule + reference + open + alert_date ≥ today-7 → skip.

### Checklist Pass/Fail

- [ ] Rule expiring_batch tạo alert đúng
- [ ] Dedup không tạo duplicate
- [ ] All 7 alert types hoạt động

---

## UC-34 — View & Action Alerts

**Actor:** Storekeeper / Manager / Accountant
**Status:** ✅ OK (slice 2 actions)
**Pre-condition:** SC Alert có open.

### Test scenario

1. `/app/sc-alert?resolved=0` — Alert Center.
2. Filter theo severity + alert_type.
3. Click reference link → navigate doc gốc.
4. Slice 2 actions:
5.   - expiring_batch → button "Chuyển vào Kho Cách ly" → SE Material Transfer to Quarantine
6.   - low_stock → button "Tạo Material Request bổ sung" → MR draft (qty=safety×2)
7.   - overdue_payment → button "Tạo Payment Entry" → PE draft
8. Sau action: action_taken=1, action_doctype/name link, resolved=1, resolution_action=Acted Upon.
9. Hoặc: button "Đánh dấu đã xử lý" / "Bỏ qua" cho alert types khác.

### Expected result

- Idempotent: gọi action 2 lần → throw "Đã có action".
- Alert resolved → ẩn khỏi Alert Center default filter.

### Checklist Pass/Fail

- [ ] 3 action types hoạt động
- [ ] Idempotent guard
- [ ] Generic Acknowledge/Dismiss

---


## Tổng kết module m11_dashboard

**Total UCs:** 3

**Sign-off:**
- [ ] UC-32 Executive Dashboard — Tester: __________ Date: __________
- [ ] UC-33 Configure Auto-Alerts — Tester: __________ Date: __________
- [ ] UC-34 View & Action Alerts — Tester: __________ Date: __________
