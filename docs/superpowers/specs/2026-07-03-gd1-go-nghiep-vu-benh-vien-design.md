# Spec GĐ1 — Gỡ nghiệp vụ bệnh viện khỏi SupplyCore (chuyển sang MVL)

- **Ngày:** 2026-07-03
- **Nhánh:** `feat/mvl-distributor`
- **Bối cảnh:** SupplyCore chuyển từ bản bệnh viện → bản MVL (công ty phân phối), **thay thế in-place**. Xem `docs/ba-miyano/PHAN_TICH_HUONG_THIET_KE_MVL.md`.
- **Phạm vi giai đoạn này (GĐ1):** CHỈ **gỡ** nghiệp vụ bệnh viện. KHÔNG thêm Sales/Portal (GĐ2–3).
- **Quyết định đã chốt:** (1) Xóa hẳn subsystem HIS/BHYT; (2) M10 recall gỡ nhánh bệnh nhân, tạm trace theo tồn nội bộ, rewire theo Sales ở GĐ2; (3) gỡ luôn `his_code` trên SC Item; (4) test/seed bệnh viện thì xóa/cắt, không sửa cho pass.

## 1. Mục tiêu (end-state có thể kiểm chứng)

1. `bench --site supplycore-miyano.local migrate` chạy **sạch** (không lỗi).
2. `bench build` sạch; app **boot** được; Desk mở được.
3. `grep -rniE "dispens|patient|bhyt|his_code|his_warehouse|SC Patient"` trên `supplycore/` (trừ `/backups/`, tài liệu `docs/`) trả về **0 dòng code sống**.
4. Các phân hệ M1–M6, M8–M11 **còn nguyên chức năng** (đã cắt nhánh bệnh viện, không mất chức năng chung).
5. Test suite còn lại (sau khi xóa test bệnh viện) **pass**.
6. Không còn DocType/module/role/API thuộc nghiệp vụ bệnh viện trong DB sau migrate.

**Ngoài phạm vi:** thêm SC Customer / Sales / Portal (GĐ2), rewire M10 recall theo Delivery Note/Customer (GĐ2), viết lại seed/test cho MVL (GĐ2–4), cập nhật README/FLOW chi tiết (GĐ4 — chỉ đổi `app_description` ở GĐ1).

## 2. Các nhóm thay đổi

### 2.1. Drop DocType (patch `v0_6.remove_hospital_domain`)

Force-delete các DocType sau (đã xác nhận **0 bản ghi** trong DB → drop bảng an toàn):

| Module | DocType |
|---|---|
| m7_dispensing | SC Dispensing Request, SC DR Item, SC Patient Dispensing, SC PD Item |
| m7_dispensing (legacy stub) | BHYT Claim, Dispensing Request, Dispensing Request Item, Patient Dispensing |
| supplycore | SC Patient, SC BHYT Code Config |
| supplycore (legacy stub) | BHYT Config |
| m6_transfer | SC HIS Warehouse Map |

- Patch dùng `frappe.delete_doc("DocType", name, force=True, ignore_missing=True)` cho từng cái; bọc try/except log để idempotent.
- Sau đó **xóa folder** tương ứng trong source; gỡ module **"M7 Dispensing"** khỏi `supplycore/modules.txt` và xóa folder `m7_dispensing/`.
- Đăng ký patch trong `patches.txt`: `supplycore.patches.v0_6.remove_hospital_domain`.

### 2.2. Xóa subsystem HIS/BHYT (xóa file)

- `supplycore/his_extractor/` — toàn bộ thư mục.
- `supplycore/api/his_import.py`, `his_file_read.py`, `fetch_upstream.py`, `bhyt.py`, `integration.py`.
- `supplycore/setup/seed_his_demo.py`.
- Dọn tham chiếu (import/endpoint/branch) trong: `api/access.py`, `api/users.py`, `api/webhook.py`, `api/wipe.py`, `api/data_io.py`, `api/voucher_io.py`, `api/frontend.py`. Nếu file nào chỉ tồn tại để phục vụ HIS thì xóa; nếu dùng chung thì chỉ cắt nhánh HIS/BHYT.

### 2.3. Scrub file dùng chung (cắt nhánh bệnh viện, giữ phần chung)

| File | Việc |
|---|---|
| `api/kpi.py` | Bỏ KPI `pending_dispensing_requests` (count SC Dispensing Request) |
| `api/trace.py` | Bỏ nhánh `patient_dispensings`; trace chỉ theo `batch → SC Stock Ledger Entry`. Gắn `# TODO GĐ2: trace batch → SC Delivery Note → SC Customer` |
| `m10_traceability/api/trace.py` | Như trên |
| `m10_traceability/doctype/sc_recall_notice/sc_recall_notice.py` | Bỏ nhánh recall qua SC Patient Dispensing; giữ recall theo tồn nội bộ/SLE. Gắn TODO GĐ2 |
| `m11_dashboard/doctype/sc_alert/sc_alert.py` | Bỏ action `action_priority_dispense` |
| `m8_accounting/api/financial_reports.py` | Bỏ hàm `bhyt_settlement_report` |
| `overrides/stock_entry.py` | Bỏ hook `log_dispensing` + comment "M7 dispensing" |
| `utils/permissions.py` | Bỏ hàm `dispensing_perm` |
| `supplycore/doctype/sc_item/sc_item.json` | Bỏ field `his_code`; bỏ cả section BHYT: `section_bhyt`, `has_bhyt`, `bhyt_code`, `bhyt_group`, `column_break_bhyt`, `bhyt_payment_rate`; sửa label `use_uom` bỏ "/BHYT" |
| `supplycore/doctype/sc_item/sc_item.py` | Bỏ validate `has_bhyt`/`bhyt_code` |
| `public/js/item.js` | Bỏ logic liên quan his_code/bhyt |
| `supplycore/doctype/sc_purchase_receipt/sc_purchase_receipt.json` | Rà & bỏ field/ref bhyt/patient nếu có |
| `supplycore/doctype/sc_department/sc_department.json`, `sc_gl_entry.json`, `sc_stock_ledger_entry.py`, `m10 sc_recall_affected_item.json` | Rà & cắt ref bệnh viện (vd `qty_dispensed`) — nếu là field lịch sử vô hại thì để lại + TODO, nếu là ref cứng tới doctype đã xóa thì gỡ |

> Nguyên tắc scrub: sau khi cắt, **không được** còn import/tham chiếu tới DocType đã drop (nếu không `bench migrate`/boot sẽ lỗi).

### 2.4. `hooks.py`

- Bỏ dòng `has_permission` cho `"Patient Dispensing": "...dispensing_perm"`.
- Bỏ roles bệnh viện khỏi fixtures filter: `Pharmacy Officer`, `BHYT Officer`, `Department Requester`, và `SupplyCore Ward Staff` (nếu có trong filter).
- Bỏ `"M7 Dispensing"` khỏi danh sách module (boot/menu).
- Bỏ comment `# Outbound webhooks (HIS / Cổng BHYT)`.
- Rà `doc_events` và `scheduler_events`: gỡ mọi handler trỏ tới file/hàm đã xóa (vd forecast/dispensing nếu có).

### 2.5. `install.py`

- Bỏ tạo các role bệnh viện trong `create_default_roles`: `Pharmacy Officer`, `BHYT Officer`, `SupplyCore Ward Staff`.
- Giữ nguyên các role dùng chung (Manager, Storekeeper, Accountant, Executive, Purchaser, Auditor, User, Warehouse Officer, QC Officer). (Role `SC Customer Portal` thêm ở GĐ2.)

### 2.6. Seed & tests

**Xóa (test/seed thuần bệnh viện):**
- `tests/smoke_m7.py`, `tests/smoke_his_import.py` (nếu có), `tests/uc22_test.py`, `uc23_test.py`, `uc26_test.py`, `uc30_test.py` (các UC cấp phát/BHYT theo đánh số bản bệnh viện).
- `setup/seed_his_demo.py` (đã liệt ở 2.2).

**Prune nhánh bệnh viện (giữ file, cắt phần BV):**
- `tests/smoke_m10.py`, `tests/smoke_m11.py`, `tests/uc34_test.py`, `tests/uat_e2e_runner.py`, `tests/uc_coverage.py`.
- `setup/seed_master_data.py`, `setup/seed_10_full_flow.py`, `setup/seed_uc_scenario.py`, `setup/import_consumables.py`, `setup/seed_test_users.py` (bỏ seed patient/dispensing/bhyt và role BV).

> Test bệnh viện **không sửa cho pass** — xóa hoặc cắt. Bộ test MVL viết lại ở GĐ2–4.

### 2.7. Metadata

- `hooks.py`: `app_description` đổi từ *"Hospital medical supply chain management…"* → *"Medical supply distribution management — Frappe-only custom app (no ERPNext dependency)"* (hoặc mô tả tương đương chiều phân phối).
- README/FLOW: cập nhật đầy đủ ở GĐ4; GĐ1 chỉ chỉnh mô tả nếu tiện.

## 3. Migration & Verify (thứ tự chạy)

1. Áp dụng thay đổi source (2.1–2.7).
2. `bench --site supplycore-miyano.local migrate` → chạy patch `v0_6` (drop DocType) → **sạch**.
3. `bench build` → sạch.
4. `grep -rniE "dispens|patient|bhyt|his_code|his_warehouse|SC Patient" supplycore/ --include=*.py --include=*.json --include=*.js --include=*.vue` (loại `/backups/`) → **0**.
5. Boot: mở Desk / gọi 1 API KPI → không lỗi.
6. Chạy test suite còn lại → pass.
7. Backup lại sau khi xong (mốc "MVL GĐ1 done").

## 4. Rủi ro & giảm thiểu

| Rủi ro | Giảm thiểu |
|---|---|
| Xóa file/DocType làm import cứng gãy → boot lỗi | Scrub ref TRƯỚC khi drop; chạy `bench migrate` + boot ngay sau mỗi cụm lớn |
| Field bị các DocType khác Link tới (vd `qty_dispensed`) | Grep ngược mọi field bị xóa trước khi xóa; nếu bị Link → xử lý hoặc giữ + TODO |
| `patches.txt` sai thứ tự / patch không idempotent | Patch bọc try/except + `ignore_missing`; đặt cuối danh sách v0_6 |
| Mất dữ liệu | Đã backup (mục backup 20260703_153604); 0 bản ghi BV nên không mất dữ liệu thật |
| Fixtures export lại kéo theo role đã xóa | Kiểm `fixtures/role.json` (đang rỗng) không chứa role BV |

## 5. Định nghĩa "Done"

Tất cả 6 tiêu chí mục 1 đạt, commit trên nhánh `feat/mvl-distributor`, backup mốc hoàn tất. Sẵn sàng chuyển GĐ2 (thêm M7 Sales).
