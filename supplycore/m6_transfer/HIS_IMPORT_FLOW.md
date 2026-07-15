# UC-18B — Tạo chuyển kho tự động từ phiếu HIS (PDF) — Flow & Implementation

**Module:** M6 Transfer
**DocType liên quan:** SC Transfer Request + SC Stock Entry (tái dùng), SC Item, SC Warehouse, SC Batch, SC HIS Warehouse Map (mới)
**Date:** 2026-06-11
**Nguồn:** Yêu cầu — đọc phiếu "PHIẾU XUẤT ĐIỀU CHUYỂN" (Mẫu C31-HD) của HIS, tạo chuyển kho tự động trong SupplyCore.
**Nguồn mẫu:** `docs/Phiếu ĐC KHo.pdf`

---

## 0. Phát hiện kỹ thuật quan trọng (đã kiểm chứng)

| Kiểm tra | Kết quả | Hệ quả |
|---|---|---|
| Producer PDF | `Microsoft: Print To PDF` | PDF **ảnh hoá**, không có text layer |
| `pdftotext -layout` | ra ~2 ký tự (rỗng) | `pdfplumber`/`pdftotext` **vô dụng** |
| `pdfimages -list` | không có ảnh raster nhúng | chữ vẽ bằng glyph không map Unicode |
| `pdftoppm -r 150 -png` | render sạch, đọc tốt | OCR/Vision khả thi |
| `tesseract` | **chưa cài** | OCR cục bộ không sẵn |

→ **Hai backend trích xuất (cùng trả 1 cấu trúc dict, orchestration dùng chung):**
- **`vision`** (mặc định) — Claude API `claude-opus-4-8` đọc ảnh render. Chính xác cao trên bảng + tiếng Việt + số VN. Khớp 100% → **auto-submit**. Cần `anthropic_api_key`.
- **`ocr`** — tesseract offline (lang `vie+eng`), dựng bảng bằng bounding-box. **KHÔNG cần API key**. Độ chính xác bảng số dày thấp hơn → **LUÔN tạo Draft** điền sẵn để người dùng đối chiếu PDF rồi submit tay (không auto-submit). Cần system `tesseract-ocr` + `tesseract-ocr-vie`.

Chọn backend: tham số `backend` của endpoint > site_config `his_extract_backend` > `vision`.

---

## 1. Quyết định thiết kế (đã chốt với người dùng — 2026-06-11)

| # | Quyết định | Chốt |
|---|---|---|
| 1 | Đối chiếu vật tư HIS → SC Item | Thêm field `his_code` trên SC Item, map theo mã |
| 2 | Vai trò SupplyCore với phiếu HIS | Ghi nhận lại + **auto-submit** (HIS là nguồn sự thật) |
| 3 | Dòng không đối chiếu được | Tạo phiếu **Draft**, đánh dấu dòng lỗi để sửa tay |
| 4 | Đối chiếu kho HIS → SC Warehouse | **DocType bảng ánh xạ** (tên kho HIS → SC Warehouse) |
| 5 | Cách trích xuất dữ liệu | **Vision AI (Claude API)** đọc ảnh render |
| 6 | Tồn kho nguồn | Có sẵn trong SupplyCore → check đủ tồn + auto-submit chạy được |

### 1.1 Dung hòa "auto-submit" (QĐ#2) vs "Draft khi lỗi" (QĐ#3)
- **Phiếu khớp 100%** (mọi dòng OK + cả 2 kho map được + đủ tồn) → tạo TR → auto-approve → make_stock_entry() → **submit SE** → SLE → status `Received`.
- **Phiếu có ≥1 lỗi** (item/lô/kho không tìm thấy, hoặc tồn không đủ) → tạo TR **Draft**, tô dòng lỗi, **KHÔNG submit**. Thủ kho sửa tay rồi submit theo luồng UC-18 chuẩn.

### 1.2 "Allow negative" KHÔNG phải lựa chọn
Tồn không đủ tại kho nguồn được xử lý như **lỗi dòng → Draft** (không cho âm kho). Composes QĐ#2+#3, không tạo đường nguy hiểm mới.

---

## 2. Schema changes

### 2.1 SC Item — thêm field
| fieldname | type | label | ghi chú |
|---|---|---|---|
| `his_code` | Data | Mã HIS | index, dùng đối chiếu; cho phép trống (vật tư chưa map) |

### 2.2 SC HIS Warehouse Map (DocType mới, trong m6_transfer)
| fieldname | type | label | ghi chú |
|---|---|---|---|
| `his_warehouse_name` | Data | Tên kho HIS | **unique**, autoname theo field này |
| `warehouse` | Link (SC Warehouse) | Kho SupplyCore | bắt buộc |
| `disabled` | Check | Ngừng dùng | |

- Naming: `field:his_warehouse_name` (tên kho HIS là khoá).
- Đối chiếu: chuẩn hoá khoảng trắng + so khớp không phân biệt hoa/thường.

### 2.3 SC Transfer Request — thêm field (section "Nguồn HIS")
| fieldname | type | label | ghi chú |
|---|---|---|---|
| `import_source` | Select (`Manual`\|`HIS Import`) | Nguồn phiếu | default Manual |
| `his_slip_no` | Data | Số phiếu HIS | **unique** (idempotency), read-only |
| `his_slip_date` | Date | Ngày phiếu HIS | read-only |
| `his_pdf` | Attach | File phiếu HIS gốc | lưu để đối chiếu/audit |
| `his_import_log` | Small Text | Nhật ký import | tóm tắt kết quả, dòng lỗi |

- `his_slip_no` unique → re-import cùng PDF bị chặn (không double tồn kho).

### 2.4 SC Transfer Request Item — thêm field
| fieldname | type | label | ghi chú |
|---|---|---|---|
| `his_match_status` | Select (`OK`\|`Item Not Found`\|`Batch Not Found`\|`Insufficient Stock`) | Trạng thái đối chiếu | |
| `his_raw_name` | Data | Tên VT (HIS gốc) | hiển thị để sửa tay |
| `his_raw_code` | Data | Mã HIS gốc | |
| `his_note` | Data | Ghi chú lỗi | thông điệp lỗi cụ thể |

---

## 3. Luồng chính (happy path — khớp 100%)

| Bước | Action |
|---|---|
| 1 | User mở màn M6, bấm "Nhập từ phiếu HIS", chọn file PDF |
| 2 | Frontend upload PDF → gọi `supplycore.api.his_import.import_transfer_slip(file_url)` |
| 3 | Backend render PDF → ảnh PNG (pdftoppm 150dpi), base64 từng trang |
| 4 | Gọi Claude API (`claude-opus-4-8`, vision + `output_config.format` json_schema) → JSON: `{slip_no, slip_date, from_warehouse_name, to_warehouse_name, lines:[{tt,name,his_code,uom,batch_no,expiry,qty,unit_price,amount}]}` |
| 5 | **Idempotency**: nếu `his_slip_no` đã tồn tại → throw `SC-E-HIS-DUPLICATE` |
| 6 | Map kho: `from/to_warehouse_name` → SC Warehouse qua SC HIS Warehouse Map |
| 7 | Mỗi dòng: match SC Item theo `his_code`; match SC Batch theo (item, batch_no); check tồn đủ tại from_warehouse |
| 8 | Mọi dòng OK + 2 kho map được → tạo TR (`import_source=HIS Import`, gắn slip_no/date/pdf), set batch **tường minh** (FEFO KHÔNG re-pick) |
| 9 | Auto-approve (bỏ qua Manager check vì là ghi nhận HIS) → `make_stock_entry()` → **submit SE** → SLE −/+ → TR.status=`Received` |
| 10 | Trả report: `{status: "submitted", transfer_request, lines_ok, ...}` |

## 4. Luồng thay thế

### 4a — Có dòng lỗi (item/lô không tìm thấy, hoặc tồn không đủ)
- Tạo TR **Draft**, gắn slip_no/date/pdf, ghi tất cả dòng (kể cả lỗi).
- Dòng lỗi: `his_match_status` ≠ OK, `his_note` mô tả, item/batch để trống nếu không match.
- KHÔNG submit. `his_import_log` liệt kê dòng lỗi.
- Report: `{status: "draft_with_errors", transfer_request, lines_error:[...]}`.

### 4b — Kho HIS chưa có trong bảng ánh xạ
- Không xác định được from/to → tạo TR Draft, để trống kho lỗi, ghi `his_note` + log.
- Report liệt kê `unmapped_warehouses:[...]` để user thêm vào SC HIS Warehouse Map.

### 4c — Phiếu trùng (đã import)
- Throw `SC-E-HIS-DUPLICATE: Phiếu {slip_no} đã được import (TR {name})`. Không tạo mới.

### 4d — Vision/Claude lỗi (thiếu API key, refusal, network)
- Throw `SC-E-HIS-EXTRACT` kèm chi tiết. Không tạo TR. (Không tạo dữ liệu rác.)

### 4e — Vật tư/kho chưa map (báo cáo precondition)
- Report luôn liệt kê **tên** item/kho chưa map để user biết chính xác cần điền gì (`his_code` trên SC Item / dòng SC HIS Warehouse Map).

---

## 5. Quy tắc đối chiếu chi tiet

- **Item**: `SC Item` WHERE `his_code` = line.his_code (đã trim). Không thấy → `Item Not Found`.
- **Batch**: `SC Batch` WHERE item=matched_item AND batch_no=line.batch_no. Không thấy → `Batch Not Found`. (KHÔNG auto-tạo batch: batch không có nghĩa là không có tồn → sẽ insufficient.)
- **Tồn**: `SUM(SLE.qty_change)` cho (item, batch, from_warehouse) ≥ line.qty. Thiếu → `Insufficient Stock` kèm "tối đa: X".
- **FEFO**: batch gán **tường minh** từ phiếu (Số lô). FEFO của UC-18 chỉ chọn khi batch trống → ở đây luôn có batch nên FEFO không can thiệp. (Tuân thủ memory: FEFO bắt buộc, nhưng phiếu HIS chỉ định lô chính xác → ghi đúng lô đó.)
- **Số VN**: prompt yêu cầu model trả số sạch (kiểu `2.099,99`→2099.99, `379,12`→379.12); model xử lý định dạng + ô xuống dòng + mã bị tách (vd `2025GE24`+`0`→`2025GE240`).

---

## 6. Vision extraction (chi tiết kỹ thuật)

- **Render**: `pdftoppm -r 150 -png <pdf> <prefix>` (subprocess; poppler đã có). 150dpi đủ nét, mỗi trang 1 PNG.
- **API**: `anthropic` SDK, `client.messages.create(model="claude-opus-4-8", thinking={"type":"adaptive"}, output_config={"format":{"type":"json_schema","schema":SCHEMA}}, messages=[{role:user, content:[{image base64 png}*N, {text: prompt}]}])`.
- **API key**: `frappe.conf.get("anthropic_api_key")` (đặt trong `site_config.json`). Thiếu → SC-E-HIS-EXTRACT.
- **Prompt**: mô tả mẫu C31-HD, các cột, định dạng số VN, yêu cầu trả JSON đúng schema; nếu ô trống trả null.
- **max_tokens**: ~8000 đủ cho 12–30 dòng.

---

## 7. Phân rã file / công việc

1. `supplycore/supplycore/doctype/sc_item/sc_item.json` — thêm `his_code`.
2. `supplycore/m6_transfer/doctype/sc_his_warehouse_map/` — DocType mới (+ .json/.py/__init__).
3. `supplycore/m6_transfer/doctype/sc_transfer_request/sc_transfer_request.json` — thêm field nguồn HIS.
4. `.../sc_transfer_request_item.json` — thêm field đối chiếu.
5. `supplycore/m6_transfer/doctype/sc_transfer_request/sc_transfer_request.py` — hàm `make_stock_entry` đã có; thêm helper auto-approve cho import nếu cần.
6. `supplycore/utils/his_vision.py` — render PDF + gọi Claude + trả dict đã validate.
7. `supplycore/api/his_import.py` — endpoint `import_transfer_slip(file_url)`: orchestrate parse → match → tạo TR → submit/draft → report.
8. Frontend (M6): nút "Nhập từ phiếu HIS" + dialog upload + hiển thị report.
9. `requirements.txt` / cài `anthropic` trong bench env.
10. Fixtures/quyền: RBAC cho endpoint (Storekeeper/Warehouse Officer/Manager).

## 8. Error codes (theo convention SC-Exxx)
- `SC-E-HIS-DUPLICATE` — phiếu đã import.
- `SC-E-HIS-EXTRACT` — lỗi trích xuất (key/refusal/network/parse).
- `SC-E-HIS-WAREHOUSE` — kho HIS chưa map (đưa vào log dòng, không nhất thiết throw).
- Tái dùng `SC-E005 STOCK_INSUFFICIENT` cho tồn không đủ (mức dòng → Draft).

## 9. Preconditions (tài liệu hoá)
- `his_code` đã điền trên các SC Item tương ứng.
- SC HIS Warehouse Map đã có dòng cho mọi kho HIS dùng trong phiếu.
- `anthropic_api_key` đã đặt trong site_config; bench env đã `pip install anthropic`.
- Kho nguồn có tồn trong SupplyCore (QĐ#6).

## 10. Idempotency & an toàn
- `his_slip_no` unique → chặn double-import (kể cả race đồng thời qua DB constraint;
  rỗng lưu NULL nên TR thủ công không bị ảnh hưởng — đã kiểm chứng).
- Pre-check `get_value(his_slip_no)` trong `_process_extracted` → báo lỗi thân thiện SC-E-HIS-DUPLICATE trước.
- Submit chạy trong transaction Frappe (rollback nếu lỗi giữa chừng).
- PDF gốc lưu ở `his_pdf` để audit/đối chiếu.
- Không gửi PDF ra ngoài ngoài Claude API (dữ liệu là phiếu chuyển kho dược, không phải PHI bệnh nhân).

## 11. As-built (đã implement & kiểm chứng — 2026-06-11)

Điều chỉnh so với thiết kế ban đầu (sau review):
- Check tồn dùng đúng `SCStockLedgerEntry.get_available_qty()` (loại QC Pending/Rejected/blocked)
  — để dòng "OK" thật sự submit được, không văng lỗi giữa chừng.
- Clean path bọc try/except: auto-submit thất bại bất kỳ lý do → rollback + hạ Draft (không lỗi thô).
- `max_tokens=16000` + bắt `stop_reason=="max_tokens"` (chống JSON bị cắt khi phiếu dài).
- Draft-có-lỗi dùng `flags.his_import_staging` + `ignore_mandatory` để lưu được phiếu nháp
  với dòng item/kho trống; khi user sửa & save lại → validation đầy đủ áp dụng.

Đã kiểm chứng (smoke_his_import.run, không cần API key):
- T1 luồng lỗi → Draft staging, dòng đánh dấu, kho/item chưa map liệt kê.
- T2 chống import trùng.
- T3 luồng sạch → submit + make_stock_entry + SE submit + SLE chuyển đúng tồn.
- T4 luồng hỗn hợp (1 OK + 1 lỗi) → Draft, dòng OK populate, dòng lỗi trống.
- T5 luồng UC-18 thủ công nguyên vẹn (same-warehouse vẫn chặn SC-E024, manual submit chuẩn).
- Shape Claude API verified: output_config/thinking là kwarg hợp lệ, call key-giả trả 401 (endpoint+params đúng).

- T6 OCR parse thuần (vn_number, parse_header, parse_words_to_slip dựng bảng word-box, ghép mã tách).
- T7 backend OCR force_draft → status `draft_review`, KHÔNG tạo SE, tồn không đổi.

CHƯA verify: độ chính xác Vision thực tế (cần `anthropic_api_key`); độ chính xác OCR thực tế
(cần `sudo apt install tesseract-ocr tesseract-ocr-vie` rồi quét PDF thật).

Backend OCR (không cần API key):
- utils/his_ocr.py — render → tesseract image_to_data (vie+eng, **psm 4**) → dựng bảng bằng
  bounding-box: tìm đúng dòng header (nhiều keyword cột nhất), nhận diện dòng mới bằng cột
  "Thành tiền" có số, ghép ô xuống dòng (tên/mã/lô), lọc mã chỉ chữ-số, vn_number.
- import_transfer_slip(file_url, backend='ocr') → force_draft (luôn Draft 'draft_review').
- Trạng thái report: submitted | draft_review (OCR/khớp, chờ đối chiếu) | draft_with_errors.

**Nghiệm thu OCR thật (2026-06-11, tesseract 5.3.4 + vie, trên `docs/Phiếu ĐC KHo.pdf`):**
- Trích đủ **12/12 dòng** (2 trang), độ chính xác 100% trên mọi trường quan trọng:
  mã HIS, số lô, HSD, số lượng, đơn giá, thành tiền (kể cả mã bị xuống dòng "2025GE222",
  thập phân "2.099,99"→2099.99). Header (số phiếu/ngày/2 kho) chính xác.
- End-to-end OCR→đối chiếu→Draft chạy đúng (chưa seed → 12 dòng Item Not Found + 2 kho chưa map,
  report liệt kê đủ mã/kho cần điền).
- Lỗi đã sửa khi test thật: psm 6→4 (psm 6 đọc hỏng trang 2 layout bảng+chữ ký);
  dò đúng dòng header (tránh khớp 'TT' trong câu quy định); nhận diện dòng theo cột tiền;
  lọc ký tự lạ ở mã ('+2025GE185'→'2025GE185').
- Lớp trích xuất (his_vision/his_ocr) đã chuyển sang standalone tool (B3); không còn trong app.

File đã tạo/sửa:
- SC Item: +`his_code`
- SC HIS Warehouse Map (DocType mới)
- SC Transfer Request: +section nguồn HIS; .py guard validate/on_submit
- SC Transfer Request Item: +field đối chiếu HIS
- utils/his_vision.py, api/his_import.py
- frontend: pages/HISImport.vue, route /his-import, nút ModuleHub (m6), api.uploadFile
- pyproject.toml: +anthropic; tests/smoke_his_import.py

## 12. Tách lớp trích xuất ra tool standalone (2026-06-16)

Lớp trích xuất PDF (vision + ocr) đã được **tách khỏi SupplyCore** thành tool độc lập
`his-slip-extractor` (repo Git riêng, không phụ thuộc Frappe). Lý do: mỗi bệnh viện có
mẫu phiếu/định dạng PDF khác nhau → onboard bệnh viện mới = thêm 1 "profile" trong tool,
KHÔNG sửa SupplyCore.

**Mô hình bàn giao qua file:**
- Tool đọc PDF → xuất **JSON** (máy import) + **Excel** (người đối chiếu/sửa tay).
- SupplyCore nhận file qua endpoint `supplycore.api.his_import.import_slip_file(file_url)`:
  - `.json` → nguồn máy, khớp 100% có thể auto-submit.
  - `.xlsx` → có thể đã sửa tay (nguồn sự thật) → luôn tạo Draft để đối chiếu rồi submit.
- Đọc file: `supplycore/api/his_file_read.py` (`read_json_file` / `read_xlsx_file`) → dict
  canonical → `_process_extracted` (đối chiếu/map/idempotency **GIỮ NGUYÊN**).

**Hợp đồng** = JSON schema có version (`schema_version=1`, `slip_type`, `profile`, `slip_no`,
`slip_date`, `from/to_warehouse_name`, `lines[...]`) + layout cột Excel cố định
(`tt,name,his_code,uom,batch_no,expiry,qty,unit_price,amount`).

**Hai điểm soát khác nhau:** sửa lỗi *trích xuất* ở tool (Excel); sửa lỗi *đối chiếu*
ở SupplyCore (luồng Draft hiện có).

**Đã gỡ khỏi SupplyCore:** `utils/his_vision.py`, `utils/his_ocr.py`, endpoint
`import_transfer_slip`, dep `anthropic`/`pytesseract`. Frontend `HISImport.vue` đổi sang
upload file JSON/Excel.

**Onboard bệnh viện mới:** thêm profile trong tool — Vision = config thuần (prompt + schema),
OCR = config + (khi cần) code hook parser riêng.

**Tham chiếu:** `docs/superpowers/specs/2026-06-15-his-slip-extractor-tool-design.md`,
`docs/superpowers/plans/2026-06-15-his-slip-extractor-tool.md`. Repo tool: `his-slip-extractor`.

## 13. ĐẢO LẠI — đưa trích xuất PDF về in-app (2026-06-16, chốt với người dùng)

Quyết định mục 12 (tách tool) bị **đảo lại**: người dùng muốn chức năng đọc PDF **gắn
trong hệ thống**, không tool riêng. Lý do nghiệp vụ: per-hospital customization vốn đã là
**dữ liệu** (his_code + SC HIS Warehouse Map) chứ không phải code, nên không cần repo riêng;
gắn in-app cho vận hành đơn giản (upload PDF thẳng trên UI).

**Cách làm — vendor package vào app (KHÔNG khôi phục code cũ his_vision/his_ocr):**
- Copy package trích xuất đã trưởng thành của tool vào `supplycore/his_extractor/`
  (`errors/schema/config`, `profiles/` YAML theo bệnh viện, `extractors/` render+ocr+ocr_parse+vision).
  Bỏ phần `cli.py`/`writers/` (chỉ dành cho tool). Giữ được **profile theo bệnh viện**
  (onboard BV mới = thêm 1 file `.yaml`, không sửa code).
- Endpoint **khôi phục**: `supplycore.api.his_import.import_transfer_slip(file_url, backend, profile)`:
  - `backend`: site_config `his_extract_backend` > **mặc định `ocr`** (offline, hợp appliance).
  - `profile`: site_config `his_extract_profile` > mặc định `default/c31-hd`.
  - **LUÔN `force_draft=True`** → mọi phiếu PDF ra TR **Draft** cho người dùng sửa rồi submit
    tay (không auto-submit, kể cả backend vision) — đúng yêu cầu "phiếu nháp sửa được".
- API key vision lấy từ `frappe.conf.get("anthropic_api_key")` (không dùng `~/.his-extractor`).
- Frontend `HISImport.vue`: **khôi phục upload PDF** + chọn backend (OCR mặc định) → gọi
  `import_transfer_slip`.
- `pyproject.toml`: thêm lại `pytesseract/Pillow/PyYAML/jsonschema/anthropic`
  (system vẫn cần poppler `pdftoppm` + `tesseract-ocr-vie`).

**Đường file (`import_slip_file` cho JSON/Excel) GIỮ NGUYÊN** như đường phụ — không bắt buộc.

**Repo `his-slip-extractor` giữ nguyên, không xóa** nhưng **deprecated** (in-app là chuẩn).

**Đã kiểm chứng (2026-06-16):**
- `smoke_his_import.run` ALL PASSED, thêm **T10**: endpoint PDF→OCR in-app → Draft (12 dòng,
  kho resolve qua map đã seed). T1 đổi tên kho MOCK sang giả (`*KHONGMAP`) để độc lập dữ liệu thật.
- End-to-end qua bench console: `import_transfer_slip` trên `docs/Phiếu ĐC KHo.pdf` (backend ocr)
  → TR Draft (docstatus 0, status `draft_with_errors`), idempotent (xóa theo his_slip_no trước/sau).
