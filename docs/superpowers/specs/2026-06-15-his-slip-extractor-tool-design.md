# Thiết kế: Tách "HIS Slip Extractor" thành tool standalone

**Ngày:** 2026-06-15
**Trạng thái:** Draft chờ duyệt
**Liên quan:** UC-18B (`supplycore/m6_transfer/HIS_IMPORT_FLOW.md`), M6 Transfer
**Repo tool (mới):** `his-slip-extractor` (Git repo riêng, KHÔNG phụ thuộc Frappe)

---

## 1. Vấn đề & mục tiêu

Hiện việc "nhập phiếu chuyển kho từ HIS (PDF)" nằm trong SupplyCore và **gắn chặt với đúng một
mẫu phiếu** (C31-HD): prompt Claude (`his_vision.py`) và parser OCR (`his_ocr.py`) hard-code
tên cột, vị trí header, heuristic bảng. Mỗi bệnh viện in phiếu khác nhau → phải custom lớp trích
xuất → hiện phải chỉnh trong codebase chính của hệ thống.

**Mục tiêu:** Tách phần *trích xuất PDF* (phần biến thiên theo bệnh viện) ra thành một **tool
standalone**, để onboard bệnh viện mới **không phải đụng vào SupplyCore**. Tool đọc PDF và xuất
ra **file đúng định dạng** để import vào hệ thống.

### Phần biến thiên theo bệnh viện (đã xác nhận)
1. **Layout/định dạng PDF** — tên cột, vị trí header, có/không text layer, phông số.
2. **Tập trường có mặt** — nơi có cột "số lô/HSD", nơi không; tên trường khác nhau.
3. **Loại phiếu** — không chỉ phiếu chuyển kho; có thể thêm nhập/xuất/lĩnh.

### Phần KHÔNG biến thiên (giữ nguyên ở SupplyCore)
- Quy tắc **đối chiếu/map**: mã HIS → SC Item (`his_code`), tên kho → SC Warehouse
  (`SC HIS Warehouse Map`), check tồn, FEFO, idempotency theo `his_slip_no`.
- Toàn bộ `_process_extracted` trong `supplycore/api/his_import.py`.

---

## 2. Quyết định kiến trúc (đã chốt với người dùng — 2026-06-15)

| # | Quyết định | Chốt |
|---|---|---|
| 1 | Ranh giới tool | **Dịch vụ/CLI standalone**, độc lập Frappe, dùng được cho hệ thống khác |
| 2 | Biến thiên/BV | Layout PDF + tập field + loại phiếu (KHÔNG phải quy tắc map) |
| 3 | Chiều tích hợp | **Bàn giao qua file** — tool xuất file, hệ thống import file |
| 4 | Định dạng file | **Cả hai**: JSON (máy import) + Excel (người đối chiếu/sửa) |
| 5 | Excel sửa tay | **Là nguồn sự thật trên đường Excel** — phải import được, không chỉ để xem |
| 6 | Nơi chạy tool | **Máy Windows bệnh viện** — `.exe` đóng gói sẵn deps, có API key riêng |
| 7 | Vị trí mã nguồn | **Repo Git riêng** (`his-slip-extractor`) |

---

## 3. Kiến trúc tổng thể

```
┌─────────────────────────────┐         ┌──────────────────────────────┐
│  TOOL (máy Windows BV)       │  file   │  SupplyCore (VM/Docker)      │
│  .exe đóng gói sẵn:          │ ──────▶ │                              │
│   poppler+tesseract+python   │ JSON +  │  Importer mới: nhận JSON     │
│                              │ Excel   │   HOẶC Excel → dict chuẩn    │
│  PDF ─▶ profile ─▶ trích xuất│         │   → _process_extracted       │
│       ─▶ JSON + Excel        │         │   (matching GIỮ NGUYÊN)      │
│  config.toml: anthropic_key  │         │   → SC Transfer Request      │
└─────────────────────────────┘         └──────────────────────────────┘
   Soát lỗi TRÍCH XUẤT (Excel)             Soát lỗi ĐỐI CHIẾU (Draft)
```

**Hai điểm soát khác nhau, không trùng lặp:**
- **Tại tool (sửa Excel):** sửa lỗi *trích xuất* — sai số lượng/lô/mã/tên. Tool **không có DB**
  nên chỉ hiển thị dữ liệu thô đọc từ PDF.
- **Tại SupplyCore (luồng Draft hiện có):** sửa lỗi *đối chiếu* — không thấy vật tư/kho, thiếu tồn.

---

## 4. Hợp đồng dữ liệu (contract) — phần quan trọng nhất

Một **schema chuẩn, có version**, với trường `slip_type` để phân loại (hiện chỉ `transfer`).

### 4.1 JSON canonical

```jsonc
{
  "schema_version": 1,
  "slip_type": "transfer",
  "profile": "<hospital>/<form>",        // vd "benhvienX/c31-hd"
  "slip_no": "PX050626-00021923",
  "slip_date": "05/06/2026",              // DD/MM/YYYY
  "from_warehouse_name": "Kho A",
  "to_warehouse_name": "Kho B",
  "lines": [
    { "tt": 1, "name": "...", "his_code": "...", "uom": "...",
      "batch_no": "...", "expiry": "DD/MM/YYYY", "qty": 0,
      "unit_price": 0, "amount": 0 }
  ]
}
```

- Giữ tương thích với `EXTRACT_SCHEMA` hiện tại (`his_vision.py`) để `_process_extracted` dùng lại
  gần như nguyên trạng; **thêm** `schema_version`, `slip_type`, `profile`.
- Field thiếu (tùy bệnh viện): chuỗi → `""`, số → `0` (giữ quy ước hiện tại, tránh null-union).

### 4.2 Excel (cùng nội dung, layout là một phần hợp đồng)

- **Sheet `header`**: slip_no, slip_date, from/to_warehouse_name, profile, slip_type.
- **Sheet `lines`**: đúng các cột `tt | name | his_code | uom | batch_no | expiry | qty |
  unit_price | amount` (header cột cố định, có hàng tiêu đề tiếng Việt để người đọc).
- **Excel đã sửa tay phải import lại được** → bộ import SupplyCore đọc đúng tên cột này.
- Khi cả JSON lẫn Excel cùng có, **đường import xác định nguồn sự thật theo file người chọn nạp**:
  nạp Excel → Excel thắng; nạp JSON → JSON thắng. (Tool xuất cả hai khớp nhau lúc đầu; sau khi
  người sửa Excel thì hai file lệch — đó là lý do phải cho import Excel.)

### 4.3 Versioning
- `schema_version` tăng khi đổi cấu trúc. Bộ import SupplyCore kiểm tra version; version lạ → báo
  lỗi thân thiện, không cố đoán.

---

## 5. Nội bộ tool (`his-slip-extractor`)

### 5.1 Cấu trúc package

```
his-slip-extractor/
  his_extractor/
    cli.py            # entrypoint: kéo-thả file / đối số dòng lệnh
    config.py         # đọc config.toml (anthropic_api_key, backend mặc định, tesseract path)
    schema.py         # định nghĩa + validate JSON canonical (jsonschema)
    profiles/         # mỗi profile = (bệnh viện × loại phiếu)
      __init__.py     # registry: nạp & chọn profile theo tên
      <hospital>_<form>.yaml   # config khai báo (vision)
      <hospital>_<form>.py     # (tùy chọn) code hook khi cần parser OCR riêng
    extractors/
      vision.py       # port từ his_vision.py — render PDF + Claude, prompt/schema TỪ profile
      ocr.py          # port từ his_ocr.py — tesseract bảng, tham số hóa cột TỪ profile
    writers/
      json_writer.py
      xlsx_writer.py
  pyproject.toml
  packaging/          # PyInstaller spec + bundle poppler/tesseract
  tests/              # test trích xuất (port từ smoke_his_import phần OCR/vision)
  README.md
```

### 5.2 Mô hình profile "lai" (hybrid)

Onboard bệnh viện mới = **thêm 1 profile**, không sửa core.

- **Vision (mặc định) = config khai báo thuần.** Profile YAML chứa:
  prompt template, JSON schema (tập field của loại phiếu này), ánh xạ cột Excel.
  → Thêm BV chỉ cần **sửa file config, không viết code**.
- **OCR (offline) = config + code hook khi cần.** Parser bảng (C31-HD) vốn nhiều heuristic
  (psm tuning, dò header, ghép ô xuống dòng). Per-hospital OCR **nhiều khả năng cần một hàm
  parser riêng** → profile cho phép trỏ tới một code hook Python. **Lưu ý trung thực:** "thêm BV
  = sửa config" **đúng hoàn toàn cho Vision, đúng một phần cho OCR**.

### 5.3 Backend trích xuất
- `vision` (Claude `claude-opus-4-8`) — chính xác cao, cần `anthropic_api_key` trong config tool.
- `ocr` (tesseract `vie+eng`) — offline, không cần key.
- Chọn backend: đối số CLI > config.toml > mặc định của profile.
- **Tool tự giữ API key trong `config.toml`/biến môi trường — KHÔNG đọc `site_config` của Frappe.**

### 5.4 Đóng gói Windows
- `.exe` build bằng **PyInstaller**, **bundle sẵn poppler (`pdftoppm`) + tesseract (+`vie`)** để
  nhân viên không phải cài thủ công.
- Build `.exe` chỉ qua CI/máy build (giống ràng buộc Windows installer hiện có).
- UX: kéo-thả PDF lên `.exe` (hoặc chọn file) → chọn profile → xuất `slip.json` + `slip.xlsx`
  cạnh file PDF.

---

## 6. Thay đổi phía SupplyCore (tối thiểu)

### 6.1 Thêm
- Endpoint mới `import_slip_file(file_url)` trong `supplycore/api/his_import.py`:
  - Nhận file **JSON hoặc Excel** (theo đuôi/định dạng).
  - JSON → validate `schema_version`/`slip_type` → dict.
  - Excel → đọc sheet `header`+`lines` theo layout hợp đồng → dict.
  - Gọi `_process_extracted(dict, ...)` **giữ nguyên** (matching, warehouse map, idempotency,
    clean/draft flow, OCR force_draft-tương-đương cho nguồn ngoài).
- Frontend `HISImport.vue`: đổi từ "upload PDF" → "upload file JSON/Excel từ tool"; phần báo cáo
  kết quả (lines_ok/error, unmapped) **giữ nguyên**.

### 6.2 Chuyển ra tool (xóa khỏi SupplyCore)
- `supplycore/utils/his_vision.py` → `his_extractor/extractors/vision.py`.
- `supplycore/utils/his_ocr.py` → `his_extractor/extractors/ocr.py`.

### 6.3 Bỏ/deprecate
- Đường `import_transfer_slip(file_url=PDF, backend=...)` cũ (đọc PDF trong SupplyCore).
  **Quyết định:** xóa hẳn (không giữ deps `anthropic`/poppler/tesseract trong bench env nữa) —
  trừ khi cần giữ tạm cho tương thích ngược một thời gian (chốt khi viết plan).

### 6.4 Giữ nguyên (không đụng)
- `SC Item.his_code`, `SC HIS Warehouse Map`, các field nguồn HIS trên `SC Transfer Request`/
  `...Item`, `_process_extracted`, `_match_line`, warehouse map, idempotency.

---

## 7. Test & migration

| Loại test | Vị trí sau tách |
|---|---|
| Trích xuất (vision shape, OCR parse bảng, vn_number, ghép ô) | **Chuyển sang repo tool** (`tests/`) |
| Đối chiếu `_process_extracted` (T1–T5: duplicate, clean→submit, mixed, draft) | **Ở lại SupplyCore** |
| Import file (JSON/Excel → dict): test mới | **SupplyCore** |

- `smoke_his_import.py`: tách phần OCR/vision đem sang tool; phần `_process_extracted` giữ lại và
  thêm test cho `import_slip_file` (JSON path + Excel path + Excel sửa tay).

---

## 8. Phạm vi (YAGNI) & đường nối tương lai

**Làm trọn vẹn đường phiếu chuyển kho (`slip_type=transfer`) end-to-end ngay bây giờ.**

Để sẵn *đường nối*, **không** xây thêm:
- `slip_type` discriminator + `schema_version` trong contract.
- Profile registry trong tool (thêm BV/loại phiếu = thêm profile).
- **Không** xây importer cho loại phiếu khác (nhập/xuất/lĩnh) cho tới khi thực sự cần — vì mỗi loại
  phiếu map sang DocType khác (Stock Entry/PR...) là việc lớn riêng, sẽ có spec riêng.

---

## 9. Mở/cần chốt khi viết plan
- Xóa hẳn hay deprecate-tạm đường PDF cũ trong SupplyCore (§6.3).
- Tên/tổ chức repo tool, license, CI build `.exe`.
- Cơ chế người dùng nạp file vào SupplyCore web (1 file JSON; hay cho phép chọn JSON/Excel).
- Có cần ký/hash file để chống sửa nhầm giữa JSON và Excel không (nice-to-have, có thể bỏ).
