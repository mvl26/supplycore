# UAT — SupplyCore tổng hợp

**Ngày test:** 2026-05-07
**Phương pháp:** REST API (HTTP) tới `http://localhost:8000` qua Frappe REST endpoints — giả lập user click trên UI, không gọi `frappe.get_doc()` trong code base.
**Harness:** `tests/uat/uat_runner.py` (Python + `requests`)

## Tổng quan

| Module | Steps | PASS | FAIL | Trạng thái |
|---|---|---|---|---|
| M1 — Hợp đồng khung | 7 | 6 | 1 | ⚠️ 1 BUG |
| M2 — Kế hoạch & Đặt hàng | 6 | 6 | 0 | ✅ |
| M3 — Tiếp nhận & QC | 4 | 4 | 0 | ✅ |
| M4 — WMS / Stock Entry | 5 | 5 | 0 | ✅ |
| M5 — FEFO + Lô | 4 | 4 | 0 | ✅ |
| M6 — Luân chuyển nội bộ | 3 | 3 | 0 | ✅ |
| M7 — Cấp phát & BHYT | 3 | 3 | 0 | ✅ |
| M8 — Kế toán & 3-way match | 2 | 2 | 0 | ✅ |
| M9 — Kiểm kê | 2 | 2 | 0 | ✅ |
| M10 — Truy xuất & Recall | 3 | 3 | 0 | ✅ |
| M11 — Dashboard & Alert | 5 | 5 | 0 | ✅ |
| **TỔNG** | **44** | **43** | **1** | **97.7% PASS** |

## Bug log

### BUG-M1-01 — Framework Contract không validate Link integrity của supplier

**Severity:** Medium
**Module:** M1 — Hợp đồng khung
**File:** `m1_contract/doctype/framework_contract/framework_contract.json`

**Reproduce:**
```bash
curl -X POST http://localhost:8000/api/resource/Framework%20Contract \
  -H "Authorization: token <key>:<secret>" \
  -H "Content-Type: application/json" \
  -d '{
    "supplier": "FAKE-NCC-KHONG-TON-TAI",
    "contract_number": "TEST-001",
    "contract_date": "2026-03-07",
    "valid_from": "2026-04-07",
    "valid_to": "2026-11-04",
    "total_value": 1000000,
    "items": [{"item_code": "VTTH-MASK-3PLY","contract_qty": 10,"uom": "Hộp","unit_price": 100000}]
  }'
# → HTTP 200 OK, FC được tạo dù supplier không tồn tại trong tabSC Supplier
```

**Expected:** Frappe phải reject với `LinkValidationError` (như `Release Order` đang làm).
**Actual:** FC được tạo + có thể submit. `tabFramework Contract.supplier` chứa giá trị "rác" không trỏ tới SC Supplier nào.

**Tác động:**
- Báo cáo theo NCC sẽ thiếu/sai khi join `Framework Contract` × `tabSC Supplier`
- `fetch_from` không hoạt động (supplier_name rỗng)
- Mất referential integrity

**Đề xuất fix:**
- Kiểm tra trong `framework_contract.py validate()`: thêm `frappe.db.exists("SC Supplier", self.supplier)` raise `frappe.LinkValidationError` nếu không tồn tại.
- Hoặc ép validation chuẩn của Frappe Link bằng cách bỏ override `validate()` chặn link validation (nếu có).
- So sánh với `Release Order` (validate đúng) để tìm root cause.

## Coverage chi tiết theo module

Mỗi module có file UAT chi tiết:
- [M1 UAT](supplycore/m1_contract/UAT.md)
- [M2 UAT](supplycore/m2_planning/UAT.md)
- [M3 UAT](supplycore/m3_receiving/UAT.md)
- [M4 UAT](supplycore/m4_wms/UAT.md)
- [M5 UAT](supplycore/m5_fefo/UAT.md)
- [M6 UAT](supplycore/m6_transfer/UAT.md)
- [M7 UAT](supplycore/m7_dispensing/UAT.md)
- [M8 UAT](supplycore/m8_accounting/UAT.md)
- [M9 UAT](supplycore/m9_stocktake/UAT.md)
- [M10 UAT](supplycore/m10_traceability/UAT.md)
- [M11 UAT](supplycore/m11_dashboard/UAT.md)

## Note tham khảo (không phải bug)

1. **Inconsistent quantity field naming across child doctypes** (đã ghi nhận trong từng module):
   - `FC Item.contract_qty` vs `SC PO Item.qty` vs `SC TR Item.requested_qty` vs `SC DR Item.requested_qty` vs `SC ICS Item.actual_qty/system_qty`
   - Khuyến nghị chuẩn hoá thành `qty` ở mọi nơi để đơn giản hoá REST API client (frontend, mobile, integration).

2. **`supplycore.api.fefo.get_suggested_batches` không validate warehouse exists** (M5):
   - Trả về list rỗng khi warehouse không tồn tại thay vì raise error rõ ràng.
   - `supplycore.api.kpi.get_warehouse_dashboard` đã validate đúng — pattern này nên áp dụng cho fefo.

3. **Patient gender options chỉ chấp nhận tiếng Việt "Nam/Nữ/Khác"** — phù hợp i18n VN; integration tích hợp HIS cần map từ "Male/Female".

## Cách chạy lại

```bash
# Server phải đang chạy (bench start hoặc gunicorn)
cd /home/hoangvietyeuem/frappe-bench/apps/supplycore
/home/hoangvietyeuem/frappe-bench/env/bin/python tests/uat/uat_runner.py
```

API key cứng trong `tests/uat/uat_runner.py` — lấy từ Administrator.api_key/api_secret. Đổi nếu site khác.
