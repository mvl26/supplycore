# UC Test — M4 — WMS & PDA

**Source:** Phase 1 / 03_Use-Case-Diagram-and-Descriptions / UseCase_SupplyCore_v2.0.md
**Cập nhật:** 2026-05-08
**Mục đích:** Test scenario từng UC tương ứng với module này — End-user (BS, dược sĩ, SK, kế toán) hoặc QA tester thực hiện thủ công, hệ thống xác nhận đúng.

> Tham khảo: [`docs/UC_COVERAGE.md`](../../docs/UC_COVERAGE.md) cho overview 37 UCs. [`docs/UAT_PROCEDURE.md`](../../docs/UAT_PROCEDURE.md) cho luồng E2E xuyên suốt.

## UC-12 — Quản lý Bin Location

**Actor:** Storekeeper
**Status:** ✅ OK
**Pre-condition:** SC Warehouse có sẵn.

### Test scenario

1. `/app/bin-location/new`.
2. Bin code: format `Aisle-Rack-Shelf-Level` (vd `A-01-01-01`).
3. Chọn warehouse, zone, capacity_qty.
4. Save.
5. Set Item.default_bin_location = bin này (cho putaway suggest).

### Expected result

- Bin code unique trong cùng warehouse.
- Validate: bin thuộc đúng warehouse khi Stock Entry tham chiếu.

### Checklist Pass/Fail

- [ ] Tạo Bin Location
- [ ] Set default_bin_location cho Item
- [ ] Putaway test (UC-13) suggest đúng bin

---

## UC-13 — PDA Stock In/Out

**Actor:** Storekeeper
**Status:** ⚠ Partial (PDA offline defer)
**Pre-condition:** Bin Location + Item có barcode.

### Test scenario

1. Mở `/pda` (mobile UI 480px touch).
2. Chọn context: Receive / Issue.
3. Quét barcode item → API `scan_barcode(barcode, context)` trả item info + suggested_bin.
4. Nhập qty + chọn bin.
5. Submit → API `confirm_putaway(item, qty, batch, bin_location, warehouse)` tạo SE Material Receipt + SLE.

### Expected result

- **UAT-03:** signature `scan_barcode(barcode, context=None)` — không nhận `warehouse` kwarg như README mô tả.
- PDA offline IndexedDB sync chưa implement (defer Phase 1.1+).

### Checklist Pass/Fail

- [ ] scan_barcode trả item info
- [ ] confirm_putaway tạo SE + SLE đúng
- [ ] (Defer) Offline mode + sync queue

---

## UC-14 — Truy vấn tồn kho theo Location

**Actor:** Storekeeper / Manager
**Status:** ✅ OK
**Pre-condition:** SLE có data.

### Test scenario

1. `/app/sc-stock-ledger-entry` — list view filter theo item, warehouse, batch, bin_location.
2. API `supplycore.api.kpi.get_warehouse_dashboard(warehouse)` trả: stock_qty_total, expiring_batches, pending DR/TR.
3. Frappe Report Builder: `/app/report-builder/new` tạo custom report theo nhu cầu.

### Expected result

- SLE balance_qty chính xác cumulative.
- API warehouse dashboard < 1s.

### Checklist Pass/Fail

- [ ] Filter SLE theo item + warehouse
- [ ] API warehouse_dashboard trả 4 metric
- [ ] Custom Report Builder tạo + export Excel

---


## Tổng kết module m4_wms

**Total UCs:** 3

**Sign-off:**
- [ ] UC-12 Quản lý Bin Location — Tester: __________ Date: __________
- [ ] UC-13 PDA Stock In/Out — Tester: __________ Date: __________
- [ ] UC-14 Truy vấn tồn kho theo Location — Tester: __________ Date: __________
