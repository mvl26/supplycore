# UC Test — M2 — Kế hoạch & Đặt hàng

**Module:** M2 Planning
**UCs covered:** UC-05, UC-06, UC-07, UC-08

---

## UC-05 — Cấu hình Min/Max & Reorder Level

**Actor:** Storekeeper / Manager
**Status:** ✅ OK (enhanced 2026-05-11 — full per-warehouse override + 4 thresholds + EOQ)
**Pre-condition:** SC Item đã có; SC Warehouse seed sẵn.

### Test scenario (6 bước theo Phase 1)

1. **Mở SC Item**: `/app/sc-item/<code>` (item hiện có) hoặc `/app/sc-item/new`.
2. **Section "Kế hoạch & FEFO"** — set 5 field item-level:
   - `safety_stock` (Tồn kho an toàn — trigger M11 alert `low_stock`)
   - `reorder_level` (Mức tái đặt hàng — trigger UC-06 auto-load)
   - `max_stock` (Tồn kho tối đa)
   - `standard_order_qty` (Số lượng đặt hàng chuẩn — EOQ)
   - `lead_time_days` (mặc định 30; = 0 → warning màu cam)
3. **Section "Ngưỡng tái đặt theo kho"** (collapsible) — optional:
   - Add row: chọn warehouse + override 4 ngưỡng (field bỏ trống = fallback item-level)
   - Mỗi kho chỉ 1 row (validate dedup)
4. **Save (Ctrl+S)** — validate:
   - Tất cả ngưỡng ≥ 0 (`SC-E-NEGATIVE`)
   - Nếu `max_stock > 0`: phải `safety ≤ reorder ≤ max` (`SC-E-MIN-MAX`)
   - Child rows: cùng quy tắc + warehouse unique (`SC-E-DUPLICATE-WAREHOUSE`)
5. **Verify M11 alert**: thiết lập SC Alert Rule `low_stock` enabled → `bench execute supplycore.m11_dashboard.tasks.scan_alerts` (hoặc đợi daily scheduler) → SC Alert tạo cho item có `qty < safety_stock` (per-warehouse nếu có override row).
6. **Verify UC-06 auto-load**: mở Procurement Plan draft → chọn warehouse → click **"Tự nạp theo Reorder Level (UC-05)"** → items có `current_qty ≤ reorder_level` tự fill vào plan với `planned_qty = standard_order_qty` (nếu set).

### Luồng thay thế

- **3a — Excel import hàng loạt:**
  - `/app/data-import/new` → Document Type = `SC Item`, Import Type = `Update Existing Records`
  - Cols: `id, safety_stock, reorder_level, max_stock, standard_order_qty, lead_time_days`
  - Upload → Frappe gọi `validate()` per row → lỗi vào import log
  - Per-warehouse: Document Type = `SC Item Reorder` với cols `parent, parenttype, parentfield, warehouse, safety_stock, reorder_level, max_stock, standard_order_qty`
  - Permissions: Frappe Data Import default = `System Manager` only

### Negative tests

- `safety_stock=-1` → throw `SC-E-NEGATIVE`
- `safety=10, reorder=5, max=20` → throw `SC-E-MIN-MAX`
- Child rows 2 row cùng warehouse → throw `SC-E-DUPLICATE-WAREHOUSE`
- Child row `safety=10, reorder=5, max=20` → throw `SC-E-MIN-MAX`

### Xử lý ngoại lệ

- `lead_time_days = 0` → msgprint warning màu cam "Lead time = 0 — nên cập nhật giá trị > 0" (KHÔNG throw, save OK)

### Hậu điều kiện

- Ngưỡng lưu trên `SC Item` + child `SC Item Reorder`.
- M11 `_scan_low_stock` quét daily — tạo SC Alert per (item, warehouse) nếu có override, hoặc item-level fallback.
- Procurement Plan có thể auto-load items theo reorder_level qua button mới.

### Checklist Pass/Fail

- [ ] Set 5 thresholds item-level cho 1 SC Item → save OK
- [ ] Set per-warehouse override row → save OK
- [ ] Negative: `safety_stock=-1` → SC-E-NEGATIVE
- [ ] Negative: safety>reorder hoặc reorder>max → SC-E-MIN-MAX
- [ ] Negative: 2 row override cùng warehouse → SC-E-DUPLICATE-WAREHOUSE
- [ ] `lead_time_days=0` → warning màu cam, không cản save
- [ ] Excel import SC Item với 5 thresholds → import log success
- [ ] M11 `_scan_low_stock`: item có override WH-A safety=50, qty=30 → alert chỉ tạo cho (item, WH-A)
- [ ] M11 `_scan_low_stock`: item không có override + safety=10 + qty=5 → alert item-level (regression)
- [ ] Procurement Plan button "Tự nạp theo Reorder Level" → items dưới reorder_level fill với qty=standard_order_qty

---

## UC-06 — Procurement Plan định kỳ

**Actor:** Manager
**Status:** ⚠️ Partial (scheduler placeholder; auto-MR defer Phase 1.1+)
**Pre-condition:** SC Item có reorder_level; SC Warehouse seed sẵn.

### Test scenario (stub)

- Mở Procurement Plan → chọn warehouse → click "Tự nạp theo Reorder Level (UC-05)" → verify items fill.
- `generate_procurement_forecast` scheduler: chỉ log — defer cho đến khi có SLE history 3 tháng.

---

## UC-07 — Tạo Purchase Request (MR)

**Actor:** Requester / Storekeeper
**Status:** ✅ OK
**Pre-condition:** SC Item, SC Warehouse seed sẵn.

### Test scenario (stub)

- Tạo SC Material Request → submit → status=Approved.

---

## UC-08 — Tạo & Phê duyệt PO

**Actor:** Manager / Purchaser
**Status:** ✅ OK
**Pre-condition:** SC MR đã Approved.

### Test scenario (stub)

- `create_purchase_orders` từ MR → SC PO draft → submit.
- Nếu grand_total ≥ po_approval_threshold → cần approval.

---

## Sign-off

| UC | Tên | Status |
|---|---|---|
| UC-05 | Cấu hình Min/Max & Reorder Level | ✅ OK (enhanced 2026-05-11 — full per-WH + 4 thresholds + EOQ) |
| UC-06 | Procurement Plan định kỳ | ⚠️ Partial |
| UC-07 | Tạo Purchase Request (MR) | ✅ OK |
| UC-08 | Tạo & Phê duyệt PO | ✅ OK |
