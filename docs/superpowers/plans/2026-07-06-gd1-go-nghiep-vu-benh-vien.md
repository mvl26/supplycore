# GĐ1 — Gỡ nghiệp vụ bệnh viện — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Gỡ toàn bộ nghiệp vụ bệnh viện (cấp phát/BHYT/HIS/bệnh nhân) khỏi app `supplycore` in-place để lấy nền cho bản MVL, giữ app luôn boot & migrate sạch.

**Architecture:** Scrub tham chiếu trong file dùng chung TRƯỚC → xóa subsystem HIS/BHYT → xóa folder DocType bệnh viện → patch `v0_6` drop bảng khỏi DB → dọn test/seed → đổi metadata + verify. App phải boot được sau MỖI task.

**Tech Stack:** Frappe Framework v15 (thuần, không ERPNext), Python, MariaDB 10.6, `bench`.

## Global Constraints

- Nhánh làm việc: `feat/mvl-distributor`. Site: `supplycore-miyano.local`. Bench: `/home/hoangvietyeuem/frappe-bench-yhct`.
- App root: `/home/hoangvietyeuem/frappe-bench-yhct/apps/supplycore`; package dir: `.../apps/supplycore/supplycore`.
- Prefix DocType nghiệp vụ: `SC `. App thuần Frappe — KHÔNG thêm phụ thuộc ERPNext.
- Nguyên tắc bất biến: sau mỗi task, `bench --site supplycore-miyano.local migrate` phải chạy sạch và Desk phải boot.
- KHÔNG thêm SC Customer / Sales / Portal ở giai đoạn này (thuộc GĐ2).
- Đã backup DB mốc `20260703_153604`; đã xác nhận 0 bản ghi bệnh viện.
- Chạy `bench` từ thư mục bench. Sau lệnh bench, cwd shell có thể bị reset — luôn `cd` lại khi cần.
- Git identity local đã đặt: `vietbuihoang <buiviet9802@gmail.com>`. Mọi commit kèm trailer:
  `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`

**Lệnh verify dùng lại nhiều lần:**
- Grep ref bệnh viện (kỳ vọng giảm dần về 0):
  `grep -rniE "dispens|patient|bhyt|his_code|his_warehouse|SC Patient" /home/hoangvietyeuem/frappe-bench-yhct/apps/supplycore/supplycore --include=*.py --include=*.json --include=*.js --include=*.vue`
- Migrate: `cd /home/hoangvietyeuem/frappe-bench-yhct && bench --site supplycore-miyano.local migrate`
- Boot smoke: `cd /home/hoangvietyeuem/frappe-bench-yhct && bench --site supplycore-miyano.local execute frappe.ping` (kỳ vọng: `pong`).

---

### Task 1: Scrub file Python dùng chung — cắt nhánh cấp phát/BHYT

Cắt các nhánh nghiệp vụ bệnh viện trong file dùng chung. DocType vẫn còn tồn tại ở task này nên cắt nhánh là an toàn; mục tiêu là gỡ mọi truy vấn/hàm phụ thuộc cấp phát để bước xóa sau không gãy import.

**Files:**
- Modify: `supplycore/api/kpi.py` — bỏ KPI `pending_dispensing_requests` (query `SC Dispensing Request`, ~dòng 436, 448).
- Modify: `supplycore/api/trace.py` — bỏ nhánh `patient_dispensings` (query `SC Patient Dispensing`, ~dòng 22, 56–91); trace chỉ còn `batch → SC Stock Ledger Entry`.
- Modify: `supplycore/m10_traceability/api/trace.py` — như trên.
- Modify: `supplycore/m10_traceability/doctype/sc_recall_notice/sc_recall_notice.py` — bỏ nhánh recall qua `SC Patient Dispensing` (~dòng 88, 117–122); giữ nhánh recall theo tồn nội bộ/SLE.
- Modify: `supplycore/m11_dashboard/doctype/sc_alert/sc_alert.py` — bỏ method `action_priority_dispense` (~dòng 153).
- Modify: `supplycore/m8_accounting/api/financial_reports.py` — bỏ hàm `bhyt_settlement_report` (~dòng 145–164) và mọi export/whitelist của nó.
- Modify: `supplycore/overrides/stock_entry.py` — bỏ hàm `log_dispensing` (~dòng 17–…) và mọi nơi gọi nó; sửa docstring dòng 1 bỏ "+ M7 dispensing log".
- Modify: `supplycore/utils/permissions.py` — bỏ hàm `dispensing_perm` (~dòng 16).
- Modify (residual metadata dùng chung — làm ALL-CLEAN ở Task 8 đạt được):
  - `supplycore/m10_traceability/doctype/sc_recall_affected_item/sc_recall_affected_item.json` — đổi tên field `qty_dispensed` → `qty_issued` (label "SL đã xuất"), cập nhật cả `field_order`.
  - `supplycore/m10_traceability/doctype/sc_recall_notice/sc_recall_notice.py` — đổi mọi tham chiếu `qty_dispensed` → `qty_issued` (đồng bộ với đổi tên trên).
  - `supplycore/supplycore/doctype/sc_department/sc_department.json`, `sc_gl_entry/sc_gl_entry.json`, `sc_purchase_receipt/sc_purchase_receipt.json` — bỏ/đổi mọi nhãn/description/field chứa "cấp phát/patient/bhyt/HIS" sang thuật ngữ trung tính (không còn khớp grep).
  - `supplycore/supplycore/doctype/sc_stock_ledger_entry/sc_stock_ledger_entry.py` — bỏ/sửa comment nhắc dispensing/patient.

**Interfaces:**
- Produces: các module trên KHÔNG còn ký hiệu/hàm: `pending_dispensing_requests`, `patient_dispensings`, `action_priority_dispense`, `bhyt_settlement_report`, `log_dispensing`, `dispensing_perm`. Field recall đổi tên `qty_dispensed` → `qty_issued` (dùng nhất quán ở json + py). (Task 3 gỡ đăng ký `dispensing_perm`, `log_dispensing` trong hooks.)

- [ ] **Step 1: Tìm mọi nơi gọi các hàm sắp xóa** (để không bỏ sót caller)

Run:
```bash
cd /home/hoangvietyeuem/frappe-bench-yhct/apps/supplycore/supplycore && \
grep -rniE "log_dispensing|dispensing_perm|bhyt_settlement_report|action_priority_dispense|pending_dispensing_requests|patient_dispensings" . --include=*.py --include=*.json | grep -vE "/backups/"
```
Ghi lại danh sách caller (đặc biệt trong `hooks.py` — xử lý ở Task 3).

- [ ] **Step 2: Sửa từng file** — xóa đúng các hàm/nhánh liệt kê ở trên. Với nhánh trace/recall, thay bằng comment mốc:
```python
# TODO GĐ2: bổ sung trace/recall theo SC Delivery Note → SC Customer (chuỗi bán)
```
Giữ nguyên phần trace theo `SC Stock Ledger Entry`. KHÔNG để lại import tới DocType cấp phát.

- [ ] **Step 3: Kiểm tra cú pháp + không còn ref trong 8 file này**

Run:
```bash
cd /home/hoangvietyeuem/frappe-bench-yhct/apps/supplycore/supplycore && \
python3 -m py_compile api/kpi.py api/trace.py m10_traceability/api/trace.py \
  m10_traceability/doctype/sc_recall_notice/sc_recall_notice.py \
  m11_dashboard/doctype/sc_alert/sc_alert.py m8_accounting/api/financial_reports.py \
  overrides/stock_entry.py utils/permissions.py && echo OK-COMPILE && \
grep -niE "dispens|patient|bhyt" api/kpi.py api/trace.py m10_traceability/api/trace.py \
  m10_traceability/doctype/sc_recall_notice/sc_recall_notice.py \
  m11_dashboard/doctype/sc_alert/sc_alert.py m8_accounting/api/financial_reports.py \
  overrides/stock_entry.py utils/permissions.py || echo GREP-CLEAN
```
Expected: `OK-COMPILE` và `GREP-CLEAN`.

- [ ] **Step 4: Migrate + boot smoke** (DocType cấp phát vẫn còn — chỉ kiểm app không gãy)

Run: `cd /home/hoangvietyeuem/frappe-bench-yhct && bench --site supplycore-miyano.local migrate && bench --site supplycore-miyano.local execute frappe.ping`
Expected: migrate sạch, in `pong`.

- [ ] **Step 5: Commit**
```bash
cd /home/hoangvietyeuem/frappe-bench-yhct/apps/supplycore && git add -A && \
git commit -m "refactor(mvl): cắt nhánh cấp phát/BHYT trong file dùng chung (M8/M10/M11/kpi/trace)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: Gỡ field HIS/BHYT khỏi SC Item

**Files:**
- Modify: `supplycore/supplycore/doctype/sc_item/sc_item.json` — bỏ khỏi `field_order` và khỏi `fields[]`: `his_code`, `section_bhyt`, `has_bhyt`, `bhyt_code`, `bhyt_group`, `column_break_bhyt`, `bhyt_payment_rate`; sửa label `use_uom` từ "Đơn vị sử dụng/BHYT" → "Đơn vị sử dụng".
- Modify: `supplycore/supplycore/doctype/sc_item/sc_item.py` — bỏ validate `has_bhyt`/`bhyt_code` (~dòng 13–14).
- Modify: `supplycore/public/js/item.js` — bỏ logic liên quan `his_code`/`bhyt`.

**Interfaces:**
- Produces: SC Item không còn field `his_code`, `has_bhyt`, `bhyt_code`, `bhyt_group`, `bhyt_payment_rate`.

- [ ] **Step 1: Grep ngược các field sắp xóa** — bảo đảm không DocType/report/JS nào Link/tham chiếu

Run:
```bash
cd /home/hoangvietyeuem/frappe-bench-yhct/apps/supplycore/supplycore && \
grep -rniE "his_code|has_bhyt|bhyt_code|bhyt_group|bhyt_payment_rate" . --include=*.json --include=*.py --include=*.js | grep -vE "/backups/|doctype/sc_item/"
```
Nếu có tham chiếu ngoài SC Item → xử lý (xóa cột report / bỏ field phụ thuộc) trong task này.

- [ ] **Step 2: Sửa 3 file** như mô tả Files.

- [ ] **Step 3: Migrate để reload SC Item + boot smoke**

Run: `cd /home/hoangvietyeuem/frappe-bench-yhct && bench --site supplycore-miyano.local migrate && bench --site supplycore-miyano.local execute frappe.ping`
Expected: migrate sạch (SC Item reload, drop cột đã bỏ), `pong`.

- [ ] **Step 4: Xác nhận field đã biến mất**

Run:
```bash
cd /home/hoangvietyeuem/frappe-bench-yhct && bench --site supplycore-miyano.local execute frappe.client.get_list \
  --kwargs '{"doctype":"DocField","filters":{"parent":"SC Item","fieldname":["in",["his_code","has_bhyt","bhyt_code"]]},"fields":["fieldname"]}'
```
Expected: danh sách rỗng `[]`.

- [ ] **Step 5: Commit**
```bash
cd /home/hoangvietyeuem/frappe-bench-yhct/apps/supplycore && git add -A && \
git commit -m "refactor(mvl): gỡ field HIS/BHYT khỏi SC Item

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: Dọn `hooks.py` và `install.py`

**Files:**
- Modify: `supplycore/hooks.py`:
  - Bỏ entry `has_permission` `"Patient Dispensing": "supplycore.utils.permissions.dispensing_perm"` (dòng ~87).
  - Bỏ khỏi danh sách role fixtures filter (dòng ~98): `Pharmacy Officer`, `BHYT Officer`, `Department Requester`; và `SupplyCore Ward Staff` nếu xuất hiện trong filter.
  - Bỏ `"M7 Dispensing"` khỏi danh sách module (dòng ~105).
  - Bỏ comment `# Outbound webhooks (HIS / Cổng BHYT) …` (dòng ~114) hoặc sửa bỏ phần HIS/BHYT.
  - Bỏ mọi entry trong `doc_events`/`scheduler_events` trỏ tới hàm đã xóa ở Task 1 hoặc file sẽ xóa ở Task 4 (dùng danh sách caller thu ở Task 1 Step 1).
- Modify: `supplycore/install.py` — trong `create_default_roles`, bỏ `"Pharmacy Officer"`, `"BHYT Officer"`, `"SupplyCore Ward Staff"` (dòng ~10, 11, 15).

**Interfaces:**
- Consumes: danh sách caller từ Task 1 Step 1.
- Produces: hooks không còn đăng ký `dispensing_perm`/`log_dispensing`; module list không còn "M7 Dispensing".

- [ ] **Step 1: Sửa `hooks.py` và `install.py`** theo mô tả.

- [ ] **Step 2: Kiểm cú pháp + không còn ref bệnh viện trong 2 file**

Run:
```bash
cd /home/hoangvietyeuem/frappe-bench-yhct/apps/supplycore/supplycore && \
python3 -m py_compile hooks.py install.py && echo OK && \
grep -niE "dispens|patient|bhyt|his|Pharmacy|Ward|Department Requester" hooks.py install.py || echo GREP-CLEAN
```
Expected: `OK` và `GREP-CLEAN`.

- [ ] **Step 3: Migrate + boot smoke**

Run: `cd /home/hoangvietyeuem/frappe-bench-yhct && bench --site supplycore-miyano.local migrate && bench --site supplycore-miyano.local execute frappe.ping`
Expected: sạch, `pong`.

- [ ] **Step 4: Commit**
```bash
cd /home/hoangvietyeuem/frappe-bench-yhct/apps/supplycore && git add -A && \
git commit -m "refactor(mvl): dọn hooks/install — bỏ perm, role, module cấp phát/BHYT

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: Xóa subsystem HIS/BHYT (file)

**Files:**
- Delete: `supplycore/his_extractor/` (toàn bộ).
- Delete: `supplycore/api/his_import.py`, `supplycore/api/his_file_read.py`, `supplycore/api/fetch_upstream.py`, `supplycore/api/bhyt.py`, `supplycore/api/integration.py`.
- Delete: `supplycore/setup/seed_his_demo.py`.
- Modify (dọn ref còn lại): `supplycore/api/access.py`, `api/users.py`, `api/webhook.py`, `api/wipe.py`, `api/data_io.py`, `api/voucher_io.py`, `api/frontend.py` — bỏ import/nhánh HIS/BHYT.

- [ ] **Step 1: Tìm importer của các module sắp xóa**

Run:
```bash
cd /home/hoangvietyeuem/frappe-bench-yhct/apps/supplycore/supplycore && \
grep -rniE "his_import|his_file_read|fetch_upstream|api\.bhyt|api\.integration|his_extractor|seed_his_demo" . --include=*.py | grep -vE "/backups/"
```
Ghi lại mọi importer (ngoài chính các file sắp xóa).

- [ ] **Step 2: Xóa file/thư mục**
```bash
cd /home/hoangvietyeuem/frappe-bench-yhct/apps/supplycore/supplycore && \
git rm -r his_extractor api/his_import.py api/his_file_read.py api/fetch_upstream.py api/bhyt.py api/integration.py setup/seed_his_demo.py
```

- [ ] **Step 3: Dọn importer** trong các file `api/*.py` liệt kê ở Files (bỏ dòng import + nhánh dùng chúng).

- [ ] **Step 4: Không còn ref + compile toàn bộ api/**

Run:
```bash
cd /home/hoangvietyeuem/frappe-bench-yhct/apps/supplycore/supplycore && \
grep -rniE "his_import|his_file_read|fetch_upstream|api\.bhyt|api\.integration|his_extractor|seed_his_demo" . --include=*.py | grep -vE "/backups/" || echo GREP-CLEAN && \
python3 -m compileall -q api && echo OK-COMPILE
```
Expected: `GREP-CLEAN` và `OK-COMPILE`.

- [ ] **Step 5: Migrate + boot smoke**

Run: `cd /home/hoangvietyeuem/frappe-bench-yhct && bench --site supplycore-miyano.local migrate && bench --site supplycore-miyano.local execute frappe.ping`
Expected: sạch, `pong`.

- [ ] **Step 6: Commit**
```bash
cd /home/hoangvietyeuem/frappe-bench-yhct/apps/supplycore && git add -A && \
git commit -m "refactor(mvl): xóa subsystem HIS/BHYT (his_extractor + api/his_*, bhyt, integration)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: Xóa folder DocType bệnh viện + cập nhật `modules.txt`

**Files:**
- Delete: `supplycore/m7_dispensing/` (toàn bộ module: sc_dispensing_request, sc_dr_item, sc_patient_dispensing, sc_pd_item + stub legacy bhyt_claim, dispensing_request(+item), patient_dispensing).
- Delete: `supplycore/supplycore/doctype/sc_patient/`, `supplycore/supplycore/doctype/sc_bhyt_code_config/`, `supplycore/supplycore/doctype/bhyt_config/`.
- Delete: `supplycore/m6_transfer/doctype/sc_his_warehouse_map/`.
- Modify: `supplycore/modules.txt` — bỏ dòng `M7 Dispensing`.

Lưu ý: task này chỉ xóa source. DB vẫn còn DocType record + bảng → drop ở Task 6.

- [ ] **Step 1: Xóa folder + sửa modules.txt**
```bash
cd /home/hoangvietyeuem/frappe-bench-yhct/apps/supplycore/supplycore && \
git rm -r m7_dispensing supplycore/doctype/sc_patient supplycore/doctype/sc_bhyt_code_config \
  supplycore/doctype/bhyt_config m6_transfer/doctype/sc_his_warehouse_map 2>/dev/null; \
grep -v "M7 Dispensing" modules.txt > modules.txt.tmp && mv modules.txt.tmp modules.txt && cat modules.txt
```
(Nếu folder nào không tồn tại, bỏ qua — chỉ xóa cái có thật.)

- [ ] **Step 2: Boot smoke** (DB còn orphan doctype nhưng Frappe vẫn boot)

Run: `cd /home/hoangvietyeuem/frappe-bench-yhct && bench --site supplycore-miyano.local execute frappe.ping`
Expected: `pong`.

- [ ] **Step 3: Commit**
```bash
cd /home/hoangvietyeuem/frappe-bench-yhct/apps/supplycore && git add -A && \
git commit -m "refactor(mvl): xóa folder DocType bệnh viện (M7 Dispensing, Patient, BHYT, HIS map)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 6: Patch `v0_6` drop DocType khỏi DB

**Files:**
- Create: `supplycore/patches/v0_6/__init__.py` (rỗng, nếu chưa có).
- Create: `supplycore/patches/v0_6/remove_hospital_domain.py`.
- Modify: `supplycore/patches.txt` — thêm dòng cuối `supplycore.patches.v0_6.remove_hospital_domain`.

- [ ] **Step 1: Tạo patch**

`supplycore/patches/v0_6/remove_hospital_domain.py`:
```python
import frappe

# Các DocType nghiệp vụ bệnh viện bị loại khỏi bản MVL (0 bản ghi — an toàn drop).
HOSPITAL_DOCTYPES = [
    "SC Dispensing Request", "SC DR Item",
    "SC Patient Dispensing", "SC PD Item",
    "SC Patient", "SC BHYT Code Config", "SC HIS Warehouse Map",
    # stub legacy (có thể không tồn tại như DocType — bỏ qua nếu thiếu)
    "BHYT Claim", "Dispensing Request", "Dispensing Request Item",
    "Patient Dispensing", "BHYT Config",
]


def execute():
    for dt in HOSPITAL_DOCTYPES:
        if frappe.db.exists("DocType", dt):
            try:
                frappe.delete_doc("DocType", dt, force=True, ignore_missing=True)
                frappe.db.commit()
            except Exception:
                frappe.log_error(f"remove_hospital_domain: không xóa được {dt}",
                                 "MVL GĐ1")
        # dọn bảng mồ côi nếu còn
        table = f"tab{dt}"
        if frappe.db.table_exists(table):
            frappe.db.sql_ddl(f"DROP TABLE IF EXISTS `{table}`")
```

- [ ] **Step 2: Đăng ký patch**
```bash
cd /home/hoangvietyeuem/frappe-bench-yhct/apps/supplycore/supplycore && \
[ -f patches/v0_6/__init__.py ] || touch patches/v0_6/__init__.py; \
printf '\nsupplycore.patches.v0_6.remove_hospital_domain\n' >> patches.txt && tail -3 patches.txt
```

- [ ] **Step 3: Chạy migrate (thực thi patch)**

Run: `cd /home/hoangvietyeuem/frappe-bench-yhct && bench --site supplycore-miyano.local migrate`
Expected: log chạy patch `remove_hospital_domain`, migrate sạch.

- [ ] **Step 4: Xác nhận DocType + bảng đã biến mất**

Run:
```bash
cd /home/hoangvietyeuem/frappe-bench-yhct && bench --site supplycore-miyano.local execute frappe.client.get_list \
  --kwargs '{"doctype":"DocType","filters":{"name":["in",["SC Patient","SC Dispensing Request","SC Patient Dispensing","SC BHYT Code Config","SC HIS Warehouse Map"]]},"fields":["name"]}'
```
Expected: `[]`.

- [ ] **Step 5: Commit**
```bash
cd /home/hoangvietyeuem/frappe-bench-yhct/apps/supplycore && git add -A && \
git commit -m "feat(mvl): patch v0_6 drop DocType bệnh viện khỏi DB

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 7: Dọn test & seed

**Files:**
- Delete: `supplycore/tests/smoke_m7.py`, `supplycore/tests/uc22_test.py`, `uc23_test.py`, `uc26_test.py`, `uc30_test.py`; `supplycore/tests/smoke_his_import.py` nếu tồn tại.
- Modify (prune nhánh bệnh viện): `supplycore/tests/smoke_m10.py`, `smoke_m11.py`, `uc34_test.py`, `uat_e2e_runner.py`, `uc_coverage.py`.
- Modify (bỏ seed patient/dispensing/bhyt + role BV): `supplycore/setup/seed_master_data.py`, `seed_10_full_flow.py`, `seed_uc_scenario.py`, `import_consumables.py`, `seed_test_users.py`.

- [ ] **Step 1: Xóa test thuần bệnh viện**
```bash
cd /home/hoangvietyeuem/frappe-bench-yhct/apps/supplycore/supplycore && \
git rm tests/smoke_m7.py tests/uc22_test.py tests/uc23_test.py tests/uc26_test.py tests/uc30_test.py 2>/dev/null; \
[ -f tests/smoke_his_import.py ] && git rm tests/smoke_his_import.py; echo done
```

- [ ] **Step 2: Prune nhánh bệnh viện** trong các test/seed còn lại (bỏ block tạo/kiểm patient/dispensing/bhyt, bỏ role Pharmacy/BHYT/Ward). Sau khi sửa, đảm bảo không import DocType đã xóa.

- [ ] **Step 3: Không còn ref trong tests/ và setup/**

Run:
```bash
cd /home/hoangvietyeuem/frappe-bench-yhct/apps/supplycore/supplycore && \
grep -rniE "dispens|patient|bhyt|his_code|SC Patient" tests setup --include=*.py | grep -vE "/backups/" || echo GREP-CLEAN
```
Expected: `GREP-CLEAN`.

- [ ] **Step 4: Chạy test suite còn lại**

Run: `cd /home/hoangvietyeuem/frappe-bench-yhct && bench --site supplycore-miyano.local run-tests --app supplycore 2>&1 | tail -25`
Expected: không có test fail vì thiếu DocType cấp phát. (Ghi nhận nếu có seed chạy — seed đã prune.)

- [ ] **Step 5: Commit**
```bash
cd /home/hoangvietyeuem/frappe-bench-yhct/apps/supplycore && git add -A && \
git commit -m "test(mvl): xóa/prune test & seed nghiệp vụ bệnh viện

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 8: Đổi metadata + verify tổng thể + backup mốc

**Files:**
- Modify: `supplycore/hooks.py` — `app_description` bỏ "Hospital": vd `"Medical supply distribution management — Frappe-only custom app (no ERPNext dependency)"`.

- [ ] **Step 1: Sửa `app_description`.**

- [ ] **Step 2: Verify tổng thể — grep toàn app = 0**

Run:
```bash
grep -rniE "dispens|patient|bhyt|his_code|his_warehouse|SC Patient" \
  /home/hoangvietyeuem/frappe-bench-yhct/apps/supplycore/supplycore \
  --include=*.py --include=*.json --include=*.js --include=*.vue | grep -vE "/backups/" || echo ALL-CLEAN
```
Expected: `ALL-CLEAN`.

- [ ] **Step 3: Migrate + build + boot sạch**

Run:
```bash
cd /home/hoangvietyeuem/frappe-bench-yhct && \
bench --site supplycore-miyano.local migrate && \
bench build --app supplycore && \
bench --site supplycore-miyano.local execute frappe.ping
```
Expected: tất cả sạch, `pong`.

- [ ] **Step 4: Backup mốc "MVL GĐ1 done"**

Run: `cd /home/hoangvietyeuem/frappe-bench-yhct && bench --site supplycore-miyano.local backup --with-files`
Expected: backup thành công (ghi lại timestamp).

- [ ] **Step 5: Commit cuối**
```bash
cd /home/hoangvietyeuem/frappe-bench-yhct/apps/supplycore && git add -A && \
git commit -m "chore(mvl): đổi app_description sang phân phối + hoàn tất GĐ1 gỡ nghiệp vụ bệnh viện

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Định nghĩa Done (toàn kế hoạch)
- [ ] `grep` ref bệnh viện toàn app = 0 (`ALL-CLEAN`).
- [ ] `bench migrate` + `bench build` + `frappe.ping` sạch.
- [ ] DocType/module/role/API/field bệnh viện không còn trong source lẫn DB.
- [ ] Test suite còn lại pass; test/seed bệnh viện đã xóa/prune.
- [ ] Đã backup mốc hoàn tất; các commit trên nhánh `feat/mvl-distributor`.
- [ ] Sẵn sàng GĐ2 (thêm M7 Sales) — nhánh trace/recall đã gắn TODO.
