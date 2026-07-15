# HIS Slip Extractor Tool — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Tách phần trích xuất phiếu chuyển kho HIS (PDF) thành một tool standalone (`his-slip-extractor`, repo Git riêng, không phụ thuộc Frappe) xuất ra file JSON + Excel; SupplyCore đổi sang import file đó thay vì đọc PDF trực tiếp.

**Architecture:** Tool đọc PDF theo "profile" (bệnh viện × loại phiếu) → JSON canonical + Excel. Bàn giao qua file: SupplyCore thêm endpoint `import_slip_file` nhận JSON *hoặc* Excel → quy về dict chuẩn → `_process_extracted` (matching/warehouse map GIỮ NGUYÊN). Hợp đồng giữa hai bên là JSON schema có version + layout cột Excel cố định.

**Tech Stack:** Tool — Python 3, argparse, `anthropic`, `pytesseract`+Pillow, `openpyxl`, `PyYAML`, `jsonschema`, subprocess `pdftoppm` (poppler), PyInstaller (đóng gói .exe). SupplyCore — Frappe (Python), Vue 3 (frontend).

**Tham chiếu spec:** `docs/superpowers/specs/2026-06-15-his-slip-extractor-tool-design.md`

---

## File Structure

### Repo mới: `~/his-slip-extractor/` (Git riêng, độc lập Frappe)

```
his-slip-extractor/
  pyproject.toml                 # metadata + deps
  README.md
  his_extractor/
    __init__.py
    errors.py                    # ExtractError
    config.py                    # đọc config.toml: anthropic_api_key, default backend, tesseract path
    schema.py                    # CANONICAL_SCHEMA + validate(dict)
    extractors/
      __init__.py
      render.py                  # render_pdf_to_pngs (pdftoppm) — de-frappe từ his_vision
      ocr_parse.py               # hàm THUẦN: vn_number, parse_header, parse_words_to_slip... (port his_ocr)
      ocr.py                     # extract_ocr(pdf, profile) — tesseract, de-frappe
      vision.py                  # extract_vision(pdf, profile, api_key) — Claude, de-frappe
    profiles/
      __init__.py                # registry: load_profile(name), list_profiles()
      default_c31hd.yaml         # profile đầu tiên = mẫu C31-HD hiện tại
    writers/
      __init__.py
      json_writer.py             # write_json(dict, path)
      xlsx_writer.py             # write_xlsx(dict, path) — layout cột là hợp đồng
    cli.py                       # entrypoint: argparse → extract → write json+xlsx
  packaging/
    his-extractor.spec           # PyInstaller spec (bundle poppler + tesseract + vie)
  tests/
    test_schema.py
    test_ocr_parse.py            # port T6 từ smoke_his_import
    test_writers.py
    test_profiles.py
    test_cli.py
    fixtures/
      sample_slip.json
```

### Repo hiện tại: `apps/supplycore/` (sửa phía nhận)

```
supplycore/
  api/
    his_import.py                # GIỮ _process_extracted & helpers; THÊM import_slip_file; BỎ import_transfer_slip
    his_file_read.py             # MỚI: read_json_file / read_xlsx_file → dict canonical
  utils/
    his_vision.py                # XÓA (chuyển sang tool)
    his_ocr.py                   # XÓA (chuyển sang tool)
  tests/
    smoke_his_import.py          # BỎ test trích xuất (T6); GIỮ T1-T5,T7; THÊM test file-import
    fixtures/
      sample_slip.json           # MỚI (khớp hợp đồng)
      sample_slip.xlsx           # MỚI (sinh từ tool/script)
frontend/src/pages/HISImport.vue # đổi upload PDF → upload JSON/Excel
pyproject.toml                   # BỎ dep anthropic khỏi SupplyCore
```

---

## Hợp đồng dữ liệu (dùng xuyên suốt — đọc trước khi code)

JSON canonical (tool xuất, SupplyCore nhận). `_process_extracted` chỉ đọc các key gạch dưới; 3 key đầu là metadata additive (bị bỏ qua an toàn):

```json
{
  "schema_version": 1,
  "slip_type": "transfer",
  "profile": "default/c31-hd",
  "slip_no": "PX050626-00021923",
  "slip_date": "05/06/2026",
  "from_warehouse_name": "Kho A",
  "to_warehouse_name": "Kho B",
  "lines": [
    {"tt": 1, "name": "...", "his_code": "...", "uom": "...",
     "batch_no": "...", "expiry": "05/06/2027", "qty": 2, "unit_price": 2300, "amount": 4600}
  ]
}
```

Excel: sheet `header` (cặp key/value: slip_no, slip_date, from_warehouse_name, to_warehouse_name, slip_type, profile, schema_version); sheet `lines` (hàng 1 = tiêu đề cột đúng thứ tự: `tt, name, his_code, uom, batch_no, expiry, qty, unit_price, amount`).

---

# PHASE A — Tool repo `his-slip-extractor`

### Task A1: Scaffold repo

**Files:**
- Create: `~/his-slip-extractor/pyproject.toml`
- Create: `~/his-slip-extractor/his_extractor/__init__.py`
- Create: `~/his-slip-extractor/tests/__init__.py`
- Create: `~/his-slip-extractor/README.md`

- [ ] **Step 1: Tạo cây thư mục + git init**

```bash
mkdir -p ~/his-slip-extractor/his_extractor/extractors \
         ~/his-slip-extractor/his_extractor/profiles \
         ~/his-slip-extractor/his_extractor/writers \
         ~/his-slip-extractor/packaging \
         ~/his-slip-extractor/tests/fixtures
cd ~/his-slip-extractor && git init -q
touch his_extractor/__init__.py his_extractor/extractors/__init__.py \
      his_extractor/writers/__init__.py tests/__init__.py
```

- [ ] **Step 2: Viết `pyproject.toml`**

```toml
[project]
name = "his-slip-extractor"
version = "0.1.0"
description = "Trích xuất phiếu chuyển kho HIS (PDF) -> JSON + Excel, độc lập SupplyCore"
requires-python = ">=3.10"
dependencies = [
  "anthropic>=0.40",
  "pytesseract>=0.3.10",
  "Pillow>=10",
  "openpyxl>=3.1",
  "PyYAML>=6",
  "jsonschema>=4",
]

[project.optional-dependencies]
dev = ["pytest>=8", "pyinstaller>=6"]

[project.scripts]
his-extract = "his_extractor.cli:main"

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"
```

- [ ] **Step 3: Tạo venv + cài dev deps**

Run:
```bash
cd ~/his-slip-extractor && python3 -m venv .venv && \
  .venv/bin/pip install -q -e ".[dev]"
```
Expected: cài xong không lỗi (anthropic/openpyxl/jsonschema/pytest có mặt).

- [ ] **Step 4: README tối thiểu**

```markdown
# his-slip-extractor
Tool standalone đọc phiếu chuyển kho HIS (PDF) -> file JSON + Excel để import vào SupplyCore.
Chạy: `his-extract --profile default/c31-hd slip.pdf` -> sinh slip.json + slip.xlsx.
Backend: vision (Claude, cần anthropic_api_key) | ocr (tesseract offline).
```

- [ ] **Step 5: Commit**

```bash
cd ~/his-slip-extractor && git add -A && \
  git commit -q -m "chore: scaffold his-slip-extractor (pyproject, package skeleton)"
```

---

### Task A2: Canonical schema + validator

**Files:**
- Create: `~/his-slip-extractor/his_extractor/errors.py`
- Create: `~/his-slip-extractor/his_extractor/schema.py`
- Test: `~/his-slip-extractor/tests/test_schema.py`

- [ ] **Step 1: Viết test thất bại**

```python
# tests/test_schema.py
import pytest
from his_extractor.schema import validate, CANONICAL_SCHEMA
from his_extractor.errors import ExtractError

VALID = {
    "schema_version": 1, "slip_type": "transfer", "profile": "default/c31-hd",
    "slip_no": "PX-1", "slip_date": "05/06/2026",
    "from_warehouse_name": "A", "to_warehouse_name": "B",
    "lines": [{"tt": 1, "name": "x", "his_code": "C1", "uom": "Viên",
               "batch_no": "L1", "expiry": "", "qty": 2, "unit_price": 0, "amount": 0}],
}

def test_valid_passes():
    assert validate(VALID) == VALID

def test_missing_slip_no_raises():
    bad = {**VALID}; del bad["slip_no"]
    with pytest.raises(ExtractError):
        validate(bad)

def test_schema_version_constant():
    assert CANONICAL_SCHEMA["properties"]["schema_version"]["const"] == 1
```

- [ ] **Step 2: Chạy test — phải FAIL**

Run: `cd ~/his-slip-extractor && .venv/bin/pytest tests/test_schema.py -q`
Expected: FAIL (ImportError: no module `his_extractor.schema`).

- [ ] **Step 3: Viết `errors.py` + `schema.py`**

```python
# his_extractor/errors.py
class ExtractError(Exception):
    """Lỗi trích xuất/validate phiếu HIS (mã SC-E-HIS-EXTRACT phía SupplyCore)."""
```

```python
# his_extractor/schema.py
"""Hợp đồng JSON canonical giữa tool và hệ thống import. Có version."""
import jsonschema
from .errors import ExtractError

SCHEMA_VERSION = 1

_LINE = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "tt": {"type": "integer"},
        "name": {"type": "string"}, "his_code": {"type": "string"},
        "uom": {"type": "string"}, "batch_no": {"type": "string"},
        "expiry": {"type": "string"}, "qty": {"type": "number"},
        "unit_price": {"type": "number"}, "amount": {"type": "number"},
    },
    "required": ["tt", "name", "his_code", "uom", "batch_no", "expiry",
                 "qty", "unit_price", "amount"],
}

CANONICAL_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "schema_version": {"const": SCHEMA_VERSION},
        "slip_type": {"type": "string"},
        "profile": {"type": "string"},
        "slip_no": {"type": "string"}, "slip_date": {"type": "string"},
        "from_warehouse_name": {"type": "string"},
        "to_warehouse_name": {"type": "string"},
        "lines": {"type": "array", "items": _LINE},
    },
    "required": ["schema_version", "slip_type", "profile", "slip_no",
                 "slip_date", "from_warehouse_name", "to_warehouse_name", "lines"],
}


def validate(data: dict) -> dict:
    try:
        jsonschema.validate(data, CANONICAL_SCHEMA)
    except jsonschema.ValidationError as e:
        raise ExtractError(f"JSON canonical không hợp lệ: {e.message}") from e
    return data
```

- [ ] **Step 4: Chạy test — phải PASS**

Run: `cd ~/his-slip-extractor && .venv/bin/pytest tests/test_schema.py -q`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
cd ~/his-slip-extractor && git add -A && \
  git commit -q -m "feat: canonical JSON schema + validator (versioned contract)"
```

---

### Task A3: Hàm parse THUẦN (port từ his_ocr, không Frappe)

**Files:**
- Create: `~/his-slip-extractor/his_extractor/extractors/ocr_parse.py`
- Test: `~/his-slip-extractor/tests/test_ocr_parse.py`

- [ ] **Step 1: Viết test (port T6 từ `supplycore/tests/smoke_his_import.py`)**

```python
# tests/test_ocr_parse.py
from his_extractor.extractors.ocr_parse import vn_number, parse_header, parse_words_to_slip

def test_vn_number():
    assert vn_number("2.300") == 2300.0
    assert vn_number("2.099,99") == 2099.99
    assert vn_number("379,12") == 379.12
    assert vn_number("180.824,59") == 180824.59
    assert vn_number("") == 0.0 and vn_number("2") == 2.0

def test_parse_header():
    txt = ("PHIẾU XUẤT ĐIỀU CHUYỂN\nNgày 09 tháng 06 năm 2026   Số: PX050626-00021923\n"
           "Kho điều chuyển: Kho Khoa Điều trị Cao Cấp\nKho nhận: Kho lẻ nội trú\n")
    h = parse_header(txt)
    assert h["slip_no"] == "PX050626-00021923"
    assert h["slip_date"] == "09/06/2026"
    assert "Cao Cấp" in h["from_warehouse_name"]
    assert "nội trú" in h["to_warehouse_name"]

def test_parse_words_row_and_continuation():
    txt = "Số: PX1\nNgày 09 tháng 06 năm 2026\n"
    def w(t, left, top, line):
        return {"text": t, "left": left, "top": top, "width": 40, "height": 20, "line": line}
    words = [
        w("TT", 40, 100, "H"), w("Mã", 380, 100, "H"), w("vị", 500, 100, "H"),
        w("lô", 600, 100, "H"), w("Hạn", 700, 100, "H"), w("lượng", 800, 100, "H"),
        w("giá", 900, 100, "H"), w("tiền", 1020, 100, "H"),
        w("1", 40, 200, "R1"), w("Betahistin", 200, 200, "R1"), w("2025GE24", 380, 200, "R1"),
        w("Viên", 500, 200, "R1"), w("2602620", 600, 200, "R1"), w("01/03/2029", 700, 200, "R1"),
        w("2", 800, 200, "R1"), w("2.300", 900, 200, "R1"), w("4.600", 1020, 200, "R1"),
        w("24", 200, 240, "R2"), w("24mg", 245, 240, "R2"), w("0", 380, 240, "R2"),
        w("Tổng", 200, 300, "R3"), w("tiền", 250, 300, "R3"), w("180.824,59", 1020, 300, "R3"),
    ]
    d = parse_words_to_slip(words, txt, cols=None)
    assert len(d["lines"]) == 1
    ln = d["lines"][0]
    assert ln["his_code"] == "2025GE240"
    assert ln["name"] == "Betahistin 24 24mg"
    assert ln["batch_no"] == "2602620" and ln["qty"] == 2.0
    assert ln["unit_price"] == 2300.0 and ln["amount"] == 4600.0
```

- [ ] **Step 2: Chạy test — phải FAIL**

Run: `cd ~/his-slip-extractor && .venv/bin/pytest tests/test_ocr_parse.py -q`
Expected: FAIL (ImportError module `ocr_parse`).

- [ ] **Step 3: Tạo `ocr_parse.py`**

Sao chép NGUYÊN VĂN các hàm thuần từ `apps/supplycore/supplycore/utils/his_ocr.py` (dòng 20–242): `COLS`, `HEADER_KEYWORDS`, `STOP_ROW`, `vn_number`, `_norm`, `_clean_code`, `_clean_name`, `parse_header`, `_cx`, `_find_columns`, `_column_bands`, `_assign_col`, `parse_words_to_slip`. Hai chỉnh sửa:

1. Bỏ 2 dòng `import frappe` và `from frappe import _` ở đầu (các hàm này không dùng frappe).
2. Cho `parse_words_to_slip` nhận tham số `cols` để profile khác có thể nạp bố cục cột riêng (mặc định `None` = dùng `HEADER_KEYWORDS`/`COLS` C31-HD). Sửa chữ ký + `_find_columns`:

```python
def _find_columns(words, header_keywords=HEADER_KEYWORDS):
    from collections import defaultdict
    lines = defaultdict(list)
    for w in words:
        lines[w["line"]].append(w)

    def score(ws):
        toks = {(x["text"] or "").strip().lower() for x in ws}
        return sum(1 for kws in header_keywords.values() if any(k in toks for k in kws))

    header_line = max(lines.values(), key=score, default=[])
    if score(header_line) < 4:
        return {}, 0.0
    centers = {}
    low = [(w, (w["text"] or "").strip().lower()) for w in header_line]
    for col, kws in header_keywords.items():
        for w, txt in low:
            if txt in kws:
                centers[col] = _cx(w)
                break
    header_y = max(w["top"] + w["height"] for w in header_line)
    return centers, header_y


def parse_words_to_slip(words, full_text, cols=None):
    header_keywords = (cols or {}).get("header_keywords", HEADER_KEYWORDS) if cols else HEADER_KEYWORDS
    data = parse_header(full_text)
    data["lines"] = []
    centers, header_y = _find_columns(words, header_keywords)
    # ... phần thân còn lại GIỮ NGUYÊN như his_ocr.py dòng 177–242 ...
```

(Phần thân từ `if "his_code" not in centers ...` đến hết giữ y nguyên.)

- [ ] **Step 4: Chạy test — phải PASS**

Run: `cd ~/his-slip-extractor && .venv/bin/pytest tests/test_ocr_parse.py -q`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
cd ~/his-slip-extractor && git add -A && \
  git commit -q -m "feat: port pure OCR table parser (vn_number, parse_header, parse_words_to_slip)"
```

---

### Task A4: JSON writer

**Files:**
- Create: `~/his-slip-extractor/his_extractor/writers/json_writer.py`
- Test: `~/his-slip-extractor/tests/test_writers.py`

- [ ] **Step 1: Viết test thất bại**

```python
# tests/test_writers.py
import json
from his_extractor.writers.json_writer import write_json

SLIP = {
    "schema_version": 1, "slip_type": "transfer", "profile": "default/c31-hd",
    "slip_no": "PX-1", "slip_date": "05/06/2026",
    "from_warehouse_name": "A", "to_warehouse_name": "B",
    "lines": [{"tt": 1, "name": "Paracetamol", "his_code": "C1", "uom": "Viên",
               "batch_no": "L1", "expiry": "", "qty": 2, "unit_price": 0, "amount": 0}],
}

def test_write_json_roundtrip(tmp_path):
    p = tmp_path / "slip.json"
    write_json(SLIP, str(p))
    back = json.loads(p.read_text(encoding="utf-8"))
    assert back == SLIP
    assert "Paracetamol" in p.read_text(encoding="utf-8")  # không escape unicode
```

- [ ] **Step 2: Chạy test — phải FAIL**

Run: `cd ~/his-slip-extractor && .venv/bin/pytest tests/test_writers.py -q`
Expected: FAIL (no module `json_writer`).

- [ ] **Step 3: Viết `json_writer.py`**

```python
# his_extractor/writers/json_writer.py
import json

def write_json(data: dict, path: str) -> str:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path
```

- [ ] **Step 4: Chạy test — phải PASS**

Run: `cd ~/his-slip-extractor && .venv/bin/pytest tests/test_writers.py -q`
Expected: 1 passed.

- [ ] **Step 5: Commit**

```bash
cd ~/his-slip-extractor && git add -A && \
  git commit -q -m "feat: JSON writer (utf-8, indented)"
```

---

### Task A5: Excel writer (layout cột = hợp đồng)

**Files:**
- Create: `~/his-slip-extractor/his_extractor/writers/xlsx_writer.py`
- Test: `~/his-slip-extractor/tests/test_writers.py` (thêm)

- [ ] **Step 1: Thêm test thất bại vào `tests/test_writers.py`**

```python
from his_extractor.writers.xlsx_writer import write_xlsx, LINE_COLUMNS
from openpyxl import load_workbook

def test_write_xlsx_layout(tmp_path):
    p = tmp_path / "slip.xlsx"
    write_xlsx(SLIP, str(p))
    wb = load_workbook(str(p))
    assert set(wb.sheetnames) == {"header", "lines"}
    ls = wb["lines"]
    header = [c.value for c in ls[1]]
    assert header == LINE_COLUMNS  # đúng thứ tự cột — phần hợp đồng
    assert ls[2][1].value == "Paracetamol"  # cột 'name'
    hdr = {r[0].value: r[1].value for r in wb["header"].iter_rows()}
    assert hdr["slip_no"] == "PX-1" and hdr["profile"] == "default/c31-hd"
```

- [ ] **Step 2: Chạy test — phải FAIL**

Run: `cd ~/his-slip-extractor && .venv/bin/pytest tests/test_writers.py -q`
Expected: FAIL (no module `xlsx_writer`).

- [ ] **Step 3: Viết `xlsx_writer.py`**

```python
# his_extractor/writers/xlsx_writer.py
"""Xuất Excel cho người đối chiếu/sửa. Layout cột LÀ HỢP ĐỒNG — SupplyCore đọc theo
đúng tên cột này (his_file_read.read_xlsx_file)."""
from openpyxl import Workbook

LINE_COLUMNS = ["tt", "name", "his_code", "uom", "batch_no", "expiry",
                "qty", "unit_price", "amount"]
HEADER_KEYS = ["slip_no", "slip_date", "from_warehouse_name", "to_warehouse_name",
               "slip_type", "profile", "schema_version"]


def write_xlsx(data: dict, path: str) -> str:
    wb = Workbook()
    hs = wb.active
    hs.title = "header"
    for k in HEADER_KEYS:
        hs.append([k, data.get(k, "")])
    ls = wb.create_sheet("lines")
    ls.append(LINE_COLUMNS)
    for ln in data.get("lines", []):
        ls.append([ln.get(c, "") for c in LINE_COLUMNS])
    wb.save(path)
    return path
```

- [ ] **Step 4: Chạy test — phải PASS**

Run: `cd ~/his-slip-extractor && .venv/bin/pytest tests/test_writers.py -q`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
cd ~/his-slip-extractor && git add -A && \
  git commit -q -m "feat: Excel writer (header+lines sheets, fixed column contract)"
```

---

### Task A6: Profile model + registry

**Files:**
- Create: `~/his-slip-extractor/his_extractor/profiles/__init__.py`
- Create: `~/his-slip-extractor/his_extractor/profiles/default_c31hd.yaml`
- Test: `~/his-slip-extractor/tests/test_profiles.py`

- [ ] **Step 1: Viết test thất bại**

```python
# tests/test_profiles.py
import pytest
from his_extractor.profiles import load_profile, list_profiles
from his_extractor.errors import ExtractError

def test_list_includes_default():
    assert "default/c31-hd" in list_profiles()

def test_load_default_fields():
    p = load_profile("default/c31-hd")
    assert p["slip_type"] == "transfer"
    assert p["backend"] in ("vision", "ocr")
    assert "prompt" in p and "schema" in p   # cho vision
    assert isinstance(p["schema"], dict)

def test_unknown_profile_raises():
    with pytest.raises(ExtractError):
        load_profile("khong/co")
```

- [ ] **Step 2: Chạy test — phải FAIL**

Run: `cd ~/his-slip-extractor && .venv/bin/pytest tests/test_profiles.py -q`
Expected: FAIL (no module `profiles`).

- [ ] **Step 3: Viết profile YAML đầu tiên**

Trích `PROMPT` và `EXTRACT_SCHEMA` từ `apps/supplycore/supplycore/utils/his_vision.py` (dòng 30–88) vào YAML:

```yaml
# his_extractor/profiles/default_c31hd.yaml
name: default/c31-hd
slip_type: transfer
backend: vision        # vision | ocr
render_dpi: 200
# Vision: prompt + schema (tập field của loại phiếu này)
prompt: |
  Đây là ảnh các trang của 1 PHIẾU XUẤT ĐIỀU CHUYỂN kho (Mẫu số C31-HD) từ phần mềm HIS bệnh viện.
  Hãy đọc CHÍNH XÁC TUYỆT ĐỐI và trả về JSON theo schema.
  (… dán nguyên văn PROMPT từ his_vision.py, giữ mọi quy tắc số VN/ghép ô …)
schema:
  type: object
  additionalProperties: false
  properties:
    slip_no: {type: string}
    slip_date: {type: string}
    from_warehouse_name: {type: string}
    to_warehouse_name: {type: string}
    lines:
      type: array
      items:
        type: object
        additionalProperties: false
        properties:
          tt: {type: integer}
          name: {type: string}
          his_code: {type: string}
          uom: {type: string}
          batch_no: {type: string}
          expiry: {type: string}
          qty: {type: number}
          unit_price: {type: number}
          amount: {type: number}
        required: [tt, name, his_code, uom, batch_no, expiry, qty, unit_price, amount]
  required: [slip_no, slip_date, from_warehouse_name, to_warehouse_name, lines]
# OCR: bố cục cột (mặc định = C31-HD trong ocr_parse). Có thể trỏ ocr_hook nếu cần parser riêng.
ocr:
  header_keywords:
    tt: ["tt"]
    his_code: ["mã"]
    uom: ["vị", "tính"]
    batch_no: ["lô"]
    expiry: ["hạn"]
    qty: ["lượng"]
    unit_price: ["giá"]
    amount: ["tiền"]
```

- [ ] **Step 4: Viết registry `profiles/__init__.py`**

```python
# his_extractor/profiles/__init__.py
"""Registry profile (bệnh viện × loại phiếu). Onboard BV mới = thêm 1 file .yaml
(vision: config thuần) hoặc + code hook (ocr nếu cần parser riêng)."""
import os
import yaml
from ..errors import ExtractError

_DIR = os.path.dirname(__file__)


def list_profiles() -> list:
    out = []
    for f in os.listdir(_DIR):
        if f.endswith(".yaml"):
            with open(os.path.join(_DIR, f), encoding="utf-8") as fh:
                out.append(yaml.safe_load(fh)["name"])
    return sorted(out)


def load_profile(name: str) -> dict:
    for f in os.listdir(_DIR):
        if not f.endswith(".yaml"):
            continue
        with open(os.path.join(_DIR, f), encoding="utf-8") as fh:
            prof = yaml.safe_load(fh)
        if prof.get("name") == name:
            return prof
    raise ExtractError(f"Không có profile '{name}'. Có: {', '.join(list_profiles())}")
```

- [ ] **Step 5: Chạy test — phải PASS**

Run: `cd ~/his-slip-extractor && .venv/bin/pytest tests/test_profiles.py -q`
Expected: 3 passed.

- [ ] **Step 6: Commit**

```bash
cd ~/his-slip-extractor && git add -A && \
  git commit -q -m "feat: profile registry + default/c31-hd (vision prompt/schema + ocr layout as config)"
```

---

### Task A7: Render PDF (de-frappe)

**Files:**
- Create: `~/his-slip-extractor/his_extractor/extractors/render.py`

- [ ] **Step 1: Viết `render.py`** (port `render_pdf_to_pngs` từ his_vision.py dòng 101–122, thay `frappe.throw` → `raise ExtractError`)

```python
# his_extractor/extractors/render.py
import os
import subprocess
from ..errors import ExtractError


def render_pdf_to_pngs(pdf_path: str, out_dir: str, dpi: int = 200) -> list:
    if not os.path.exists(pdf_path):
        raise ExtractError(f"Không tìm thấy file PDF: {pdf_path}")
    prefix = os.path.join(out_dir, "his_page")
    try:
        subprocess.run(["pdftoppm", "-r", str(dpi), "-png", pdf_path, prefix],
                       check=True, capture_output=True, timeout=120)
    except FileNotFoundError:
        raise ExtractError("Thiếu 'pdftoppm' (poppler) — bản .exe phải bundle poppler")
    except subprocess.CalledProcessError as e:
        raise ExtractError("Render PDF lỗi: " + (e.stderr or b"").decode("utf-8", "ignore")[:300])
    pages = sorted(os.path.join(out_dir, f) for f in os.listdir(out_dir)
                   if f.startswith("his_page") and f.endswith(".png"))
    if not pages:
        raise ExtractError("PDF không render được trang nào")
    return pages
```

- [ ] **Step 2: Smoke import**

Run: `cd ~/his-slip-extractor && .venv/bin/python -c "from his_extractor.extractors.render import render_pdf_to_pngs; print('ok')"`
Expected: `ok`.

- [ ] **Step 3: Commit**

```bash
cd ~/his-slip-extractor && git add -A && \
  git commit -q -m "feat: de-frappe PDF renderer (pdftoppm)"
```

---

### Task A8: OCR extractor (de-frappe, profile-driven)

**Files:**
- Create: `~/his-slip-extractor/his_extractor/extractors/ocr.py`
- Test: `~/his-slip-extractor/tests/test_ocr_parse.py` (thêm 1 test stamp metadata)

- [ ] **Step 1: Viết test cho `_stamp` (thuần, không cần tesseract)**

```python
# thêm vào tests/test_ocr_parse.py
from his_extractor.extractors.ocr import stamp_meta

def test_stamp_meta_adds_contract_fields():
    raw = {"slip_no": "X", "slip_date": "", "from_warehouse_name": "",
           "to_warehouse_name": "", "lines": []}
    out = stamp_meta(raw, profile_name="default/c31-hd", slip_type="transfer")
    assert out["schema_version"] == 1
    assert out["profile"] == "default/c31-hd" and out["slip_type"] == "transfer"
```

- [ ] **Step 2: Chạy — phải FAIL**

Run: `cd ~/his-slip-extractor && .venv/bin/pytest tests/test_ocr_parse.py::test_stamp_meta_adds_contract_fields -q`
Expected: FAIL (no module `ocr`).

- [ ] **Step 3: Viết `ocr.py`** (port `extract_slip_ocr` từ his_ocr.py dòng 248–307; de-frappe; nhận profile)

```python
# his_extractor/extractors/ocr.py
import tempfile
from ..errors import ExtractError
from ..schema import SCHEMA_VERSION
from .render import render_pdf_to_pngs
from .ocr_parse import parse_words_to_slip


def stamp_meta(raw: dict, profile_name: str, slip_type: str) -> dict:
    return {"schema_version": SCHEMA_VERSION, "slip_type": slip_type,
            "profile": profile_name, **raw}


def extract_ocr(pdf_path: str, profile: dict) -> dict:
    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        raise ExtractError("Thiếu pytesseract/Pillow")
    try:
        langs = pytesseract.get_languages(config="")
    except (pytesseract.TesseractNotFoundError, EnvironmentError):
        raise ExtractError("Chưa có tesseract — bản .exe phải bundle tesseract + vie")
    lang = "vie+eng" if "vie" in langs else "eng"

    cols = {"header_keywords": (profile.get("ocr") or {}).get("header_keywords")} \
        if (profile.get("ocr") or {}).get("header_keywords") else None
    dpi = profile.get("render_dpi", 200)

    all_words, full_text_parts = [], []
    with tempfile.TemporaryDirectory(prefix="his_ocr_") as tmp:
        pages = render_pdf_to_pngs(pdf_path, tmp, dpi=dpi)
        for pg_idx, p in enumerate(pages):
            img = Image.open(p)
            full_text_parts.append(pytesseract.image_to_string(img, lang=lang, config="--psm 4"))
            tsv = pytesseract.image_to_data(img, lang=lang, config="--psm 4",
                                            output_type=pytesseract.Output.DICT)
            y_shift = pg_idx * 100000
            for i in range(len(tsv["text"])):
                txt = (tsv["text"][i] or "").strip()
                if not txt:
                    continue
                try:
                    conf = float(tsv["conf"][i])
                except (ValueError, TypeError):
                    conf = -1
                if conf < 30:
                    continue
                all_words.append({
                    "text": txt, "left": tsv["left"][i], "top": tsv["top"][i] + y_shift,
                    "width": tsv["width"][i], "height": tsv["height"][i],
                    "line": (pg_idx, tsv["block_num"][i], tsv["par_num"][i], tsv["line_num"][i]),
                })
    raw = parse_words_to_slip(all_words, "\n".join(full_text_parts), cols=cols)
    if not raw.get("slip_no") and not raw.get("lines"):
        raise ExtractError("OCR không đọc được nội dung phiếu (kiểm tra PDF / gói vie)")
    return stamp_meta(raw, profile["name"], profile["slip_type"])
```

- [ ] **Step 4: Chạy test — phải PASS**

Run: `cd ~/his-slip-extractor && .venv/bin/pytest tests/test_ocr_parse.py -q`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
cd ~/his-slip-extractor && git add -A && \
  git commit -q -m "feat: OCR extractor (de-frappe, profile-driven, stamps contract meta)"
```

---

### Task A9: Vision extractor (de-frappe, profile-driven)

**Files:**
- Create: `~/his-slip-extractor/his_extractor/config.py`
- Create: `~/his-slip-extractor/his_extractor/extractors/vision.py`
- Test: `~/his-slip-extractor/tests/test_profiles.py` (thêm test config)

- [ ] **Step 1: Viết test config (đọc env, không gọi API)**

```python
# thêm vào tests/test_profiles.py
from his_extractor.config import get_api_key
from his_extractor.errors import ExtractError

def test_api_key_from_env(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    assert get_api_key() == "sk-test"

def test_api_key_missing_raises(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(ExtractError):
        get_api_key(config_path="/khong/ton/tai.toml")
```

- [ ] **Step 2: Chạy — phải FAIL**

Run: `cd ~/his-slip-extractor && .venv/bin/pytest tests/test_profiles.py -q`
Expected: FAIL (no module `config`).

- [ ] **Step 3: Viết `config.py`** (tool tự giữ key — KHÔNG đọc site_config Frappe)

```python
# his_extractor/config.py
"""Cấu hình tool: ưu tiên biến môi trường ANTHROPIC_API_KEY, fallback config.toml."""
import os
import tomllib
from .errors import ExtractError

DEFAULT_CONFIG = os.path.expanduser("~/.his-extractor/config.toml")


def get_api_key(config_path: str = DEFAULT_CONFIG) -> str:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        return key
    if os.path.exists(config_path):
        with open(config_path, "rb") as f:
            key = (tomllib.load(f).get("anthropic_api_key") or "").strip()
        if key:
            return key
    raise ExtractError("Chưa cấu hình anthropic_api_key (env ANTHROPIC_API_KEY hoặc "
                       f"{config_path}). Backend vision cần key; dùng --backend ocr nếu không có.")
```

- [ ] **Step 4: Viết `vision.py`** (port `extract_slip` từ his_vision.py dòng 125–186; prompt/schema từ profile; key từ config)

```python
# his_extractor/extractors/vision.py
import base64
import json
import tempfile
from ..errors import ExtractError
from .render import render_pdf_to_pngs
from .ocr import stamp_meta

MODEL = "claude-opus-4-8"


def extract_vision(pdf_path: str, profile: dict, api_key: str) -> dict:
    try:
        import anthropic
    except ImportError:
        raise ExtractError("Chưa cài SDK 'anthropic'")
    dpi = profile.get("render_dpi", 200)
    with tempfile.TemporaryDirectory(prefix="his_render_") as tmp:
        pages = render_pdf_to_pngs(pdf_path, tmp, dpi=dpi)
        content = []
        for p in pages:
            with open(p, "rb") as f:
                b64 = base64.standard_b64encode(f.read()).decode("utf-8")
            content.append({"type": "image",
                            "source": {"type": "base64", "media_type": "image/png", "data": b64}})
        content.append({"type": "text", "text": profile["prompt"]})
        client = anthropic.Anthropic(api_key=api_key)
        try:
            resp = client.messages.create(
                model=MODEL, max_tokens=16000, thinking={"type": "adaptive"},
                output_config={"format": {"type": "json_schema", "schema": profile["schema"]}},
                messages=[{"role": "user", "content": content}])
        except anthropic.APIError as e:
            raise ExtractError(f"Lỗi gọi Claude API: {str(e)[:300]}")
        if resp.stop_reason == "refusal":
            raise ExtractError("Claude từ chối xử lý ảnh phiếu (refusal)")
        if resp.stop_reason == "max_tokens":
            raise ExtractError("Phiếu quá dài, JSON bị cắt (max_tokens) — tách phiếu")
        text = next((b.text for b in resp.content if getattr(b, "type", None) == "text"), "")
    try:
        raw = json.loads(text)
    except (ValueError, TypeError):
        raise ExtractError(f"Không parse được JSON từ Claude:\n{(text or '')[:500]}")
    if not isinstance(raw, dict) or "lines" not in raw:
        raise ExtractError("Kết quả Claude không đúng cấu trúc mong đợi")
    return stamp_meta(raw, profile["name"], profile["slip_type"])
```

- [ ] **Step 5: Chạy test — phải PASS**

Run: `cd ~/his-slip-extractor && .venv/bin/pytest tests/test_profiles.py -q`
Expected: 5 passed.

- [ ] **Step 6: Commit**

```bash
cd ~/his-slip-extractor && git add -A && \
  git commit -q -m "feat: vision extractor (de-frappe, prompt/schema from profile, own api key config)"
```

---

### Task A10: CLI

**Files:**
- Create: `~/his-slip-extractor/his_extractor/cli.py`
- Test: `~/his-slip-extractor/tests/test_cli.py`

- [ ] **Step 1: Viết test (dùng backend ocr giả qua monkeypatch — không cần tesseract)**

```python
# tests/test_cli.py
import json
from openpyxl import load_workbook
from his_extractor import cli

FAKE = {
    "schema_version": 1, "slip_type": "transfer", "profile": "default/c31-hd",
    "slip_no": "PX-CLI", "slip_date": "05/06/2026",
    "from_warehouse_name": "A", "to_warehouse_name": "B",
    "lines": [{"tt": 1, "name": "VT", "his_code": "C1", "uom": "Viên",
               "batch_no": "L1", "expiry": "", "qty": 1, "unit_price": 0, "amount": 0}],
}

def test_cli_writes_json_and_xlsx(tmp_path, monkeypatch):
    monkeypatch.setattr(cli, "extract_ocr", lambda pdf, prof: FAKE)
    pdf = tmp_path / "in.pdf"; pdf.write_bytes(b"%PDF-1.4")
    rc = cli.main(["--profile", "default/c31-hd", "--backend", "ocr",
                   "--out-dir", str(tmp_path), str(pdf)])
    assert rc == 0
    j = json.loads((tmp_path / "in.json").read_text(encoding="utf-8"))
    assert j["slip_no"] == "PX-CLI"
    wb = load_workbook(str(tmp_path / "in.xlsx"))
    assert wb["lines"][2][1].value == "VT"
```

- [ ] **Step 2: Chạy — phải FAIL**

Run: `cd ~/his-slip-extractor && .venv/bin/pytest tests/test_cli.py -q`
Expected: FAIL (no `main` / import).

- [ ] **Step 3: Viết `cli.py`**

```python
# his_extractor/cli.py
"""CLI: PDF -> JSON + Excel. Kéo-thả file lên .exe hoặc gọi dòng lệnh.
  his-extract --profile default/c31-hd [--backend vision|ocr] [--out-dir DIR] slip.pdf
"""
import argparse
import os
import sys
from .errors import ExtractError
from .profiles import load_profile, list_profiles
from .schema import validate
from .config import get_api_key
from .extractors.ocr import extract_ocr
from .extractors.vision import extract_vision
from .writers.json_writer import write_json
from .writers.xlsx_writer import write_xlsx


def main(argv=None):
    ap = argparse.ArgumentParser(prog="his-extract")
    ap.add_argument("pdf")
    ap.add_argument("--profile", required=True, help="vd default/c31-hd; liệt kê: --list")
    ap.add_argument("--backend", choices=["vision", "ocr"], default=None)
    ap.add_argument("--out-dir", default=None)
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args(argv)

    if args.list:
        print("\n".join(list_profiles())); return 0
    try:
        profile = load_profile(args.profile)
        backend = args.backend or profile.get("backend", "vision")
        if backend == "vision":
            data = extract_vision(args.pdf, profile, get_api_key())
        else:
            data = extract_ocr(args.pdf, profile)
        validate(data)
    except ExtractError as e:
        print(f"SC-E-HIS-EXTRACT: {e}", file=sys.stderr); return 2

    out_dir = args.out_dir or os.path.dirname(os.path.abspath(args.pdf))
    base = os.path.splitext(os.path.basename(args.pdf))[0]
    jp = write_json(data, os.path.join(out_dir, base + ".json"))
    xp = write_xlsx(data, os.path.join(out_dir, base + ".xlsx"))
    print(f"OK [{backend}] {data['slip_no']} -> {jp} | {xp}  ({len(data['lines'])} dòng)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Chạy test — phải PASS**

Run: `cd ~/his-slip-extractor && .venv/bin/pytest tests/test_cli.py -q`
Expected: 1 passed.

- [ ] **Step 5: Sinh fixture cho SupplyCore (cần ở Phase B)**

Run:
```bash
cd ~/his-slip-extractor && .venv/bin/python - <<'PY'
import json
from his_extractor.writers.json_writer import write_json
from his_extractor.writers.xlsx_writer import write_xlsx
slip = json.load(open("tests/fixtures/sample_slip.json")) if __import__("os").path.exists("tests/fixtures/sample_slip.json") else {
  "schema_version":1,"slip_type":"transfer","profile":"default/c31-hd",
  "slip_no":"PX-FIX","slip_date":"05/06/2026","from_warehouse_name":"HIS Kho Nguồn Smoke",
  "to_warehouse_name":"HIS Kho Đích Smoke",
  "lines":[{"tt":1,"name":"Smoke VT HIS","his_code":"SMOKEHIS1","uom":"Viên",
            "batch_no":"SMOKELOT1","expiry":"01/01/2030","qty":10,"unit_price":0,"amount":0}]}
write_json(slip, "tests/fixtures/sample_slip.json")
write_xlsx(slip, "tests/fixtures/sample_slip.xlsx")
print("fixtures written")
PY
```
Expected: `fixtures written`.

- [ ] **Step 6: Commit**

```bash
cd ~/his-slip-extractor && git add -A && \
  git commit -q -m "feat: CLI (PDF -> JSON+Excel, profile/backend select) + fixtures"
```

---

### Task A11: PyInstaller packaging (build infra — không TDD)

**Files:**
- Create: `~/his-slip-extractor/packaging/his-extractor.spec`
- Create: `~/his-slip-extractor/packaging/README.md`

- [ ] **Step 1: Viết spec PyInstaller** (bundle profiles + binary poppler/tesseract)

```python
# packaging/his-extractor.spec  — chạy trên máy/CI Windows
# Yêu cầu: đặt poppler/ và tesseract/ (kèm tessdata/vie.traineddata) cạnh spec trước khi build.
import os
block_cipher = None
a = Analysis(
    ['../his_extractor/cli.py'],
    pathex=['..'],
    datas=[
        ('../his_extractor/profiles', 'his_extractor/profiles'),  # YAML profiles
        ('poppler', 'poppler'),            # pdftoppm.exe + dll
        ('tesseract', 'tesseract'),        # tesseract.exe + tessdata/vie.traineddata
    ],
    hiddenimports=['anthropic', 'pytesseract', 'PIL', 'openpyxl', 'yaml', 'jsonschema'],
    hookspath=[], runtime_hooks=[], excludes=[],
    cipher=block_cipher,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(pyz, a.scripts, a.binaries, a.zipfiles, a.datas, [],
          name='his-extract', console=True)
```

- [ ] **Step 2: README build** (ghi rõ runtime hook để CLI tìm poppler/tesseract bundle)

```markdown
# Build .exe (CI Windows)
1. Tải poppler-windows + tesseract (kèm tessdata/vie.traineddata) vào packaging/poppler, packaging/tesseract.
2. `pip install -e ".[dev]"` rồi `pyinstaller packaging/his-extractor.spec`.
3. Khi đóng gói, đặt PATH tới poppler/tesseract bundle ở đầu cli.main (runtime):
   trỏ pytesseract.pytesseract.tesseract_cmd tới ./tesseract/tesseract.exe và
   thêm ./poppler/bin vào os.environ['PATH'] khi chạy dưới PyInstaller (sys.frozen).
```

- [ ] **Step 3: Thêm runtime path-fix vào `cli.py`** (đầu `main`, chỉ khi đóng gói)

```python
# thêm vào his_extractor/cli.py, đầu hàm main(), trước khi parse:
def _bundle_paths():
    import sys, os
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
        os.environ["PATH"] = os.path.join(base, "poppler", "bin") + os.pathsep + os.environ.get("PATH", "")
        tcmd = os.path.join(base, "tesseract", "tesseract.exe")
        if os.path.exists(tcmd):
            try:
                import pytesseract
                pytesseract.pytesseract.tesseract_cmd = tcmd
                os.environ["TESSDATA_PREFIX"] = os.path.join(base, "tesseract", "tessdata")
            except ImportError:
                pass
```
Gọi `_bundle_paths()` ở dòng đầu `main()`.

- [ ] **Step 4: Chạy lại test CLI (đảm bảo không vỡ)**

Run: `cd ~/his-slip-extractor && .venv/bin/pytest -q`
Expected: tất cả pass (test không chạy ở chế độ frozen nên `_bundle_paths` no-op).

- [ ] **Step 5: Commit**

```bash
cd ~/his-slip-extractor && git add -A && \
  git commit -q -m "build: PyInstaller spec + runtime poppler/tesseract bundling"
```

---

# PHASE B — SupplyCore: import từ file (repo `apps/supplycore`)

> Các task dưới chạy trong bench. Test: `bench --site <site> execute <dotted.path>`.

### Task B1: Đọc file JSON/Excel → dict canonical

**Files:**
- Create: `supplycore/api/his_file_read.py`
- Create: `supplycore/tests/fixtures/sample_slip.json` (copy từ tool Task A10 Step 5)
- Create: `supplycore/tests/fixtures/sample_slip.xlsx` (copy từ tool Task A10 Step 5)
- Test: `supplycore/tests/smoke_his_import.py` (thêm `_file_read_test`)

- [ ] **Step 1: Copy fixtures từ repo tool**

```bash
cp ~/his-slip-extractor/tests/fixtures/sample_slip.json \
   ~/frappe-bench/apps/supplycore/supplycore/tests/fixtures/sample_slip.json
cp ~/his-slip-extractor/tests/fixtures/sample_slip.xlsx \
   ~/frappe-bench/apps/supplycore/supplycore/tests/fixtures/sample_slip.xlsx
```

- [ ] **Step 2: Thêm test thất bại vào `smoke_his_import.py`** (hàm mới, gọi trong `run()` sau T7)

```python
def _file_read_test():
    import os
    from supplycore.api.his_file_read import read_json_file, read_xlsx_file
    base = os.path.join(os.path.dirname(__file__), "fixtures")
    dj = read_json_file(os.path.join(base, "sample_slip.json"))
    dx = read_xlsx_file(os.path.join(base, "sample_slip.xlsx"))
    for d in (dj, dx):
        assert d["slip_no"] == "PX-FIX", d.get("slip_no")
        assert d["from_warehouse_name"] == "HIS Kho Nguồn Smoke"
        assert len(d["lines"]) == 1
        ln = d["lines"][0]
        assert ln["his_code"] == "SMOKEHIS1" and ln["qty"] == 10.0
    return f"T8 json_lines={len(dj['lines'])} xlsx_lines={len(dx['lines'])} ok"
```

Thêm vào `run()` (sau dòng T7): `out.append(_file_read_test())`.

- [ ] **Step 3: Chạy — phải FAIL**

Run: `bench --site <site> execute supplycore.tests.smoke_his_import.run`
Expected: FAIL ở T8 (no module `his_file_read`).

- [ ] **Step 4: Viết `his_file_read.py`**

```python
# supplycore/api/his_file_read.py
"""Đọc file bàn giao từ tool his-slip-extractor → dict canonical cho _process_extracted.
Hỗ trợ JSON (máy) và Excel (người sửa tay — Excel là nguồn sự thật trên đường đó)."""
import json
import frappe
from frappe import _
from frappe.utils import flt, cint

SUPPORTED_VERSION = 1
LINE_COLUMNS = ["tt", "name", "his_code", "uom", "batch_no", "expiry",
                "qty", "unit_price", "amount"]
NUM_COLS = {"tt", "qty", "unit_price", "amount"}


def _check_version(v):
    if cint(v) != SUPPORTED_VERSION:
        frappe.throw(_("SC-E-HIS-EXTRACT: schema_version {0} không hỗ trợ (cần {1}). "
                       "Cập nhật tool/SupplyCore.").format(v, SUPPORTED_VERSION),
                     title="SC-E-HIS-EXTRACT")


def read_json_file(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    _check_version(data.get("schema_version"))
    return data


def read_xlsx_file(path: str) -> dict:
    from openpyxl import load_workbook
    wb = load_workbook(path, data_only=True)
    if "header" not in wb.sheetnames or "lines" not in wb.sheetnames:
        frappe.throw(_("SC-E-HIS-EXTRACT: Excel thiếu sheet 'header'/'lines'"),
                     title="SC-E-HIS-EXTRACT")
    hdr = {r[0].value: r[1].value for r in wb["header"].iter_rows() if r[0].value}
    _check_version(hdr.get("schema_version"))
    ls = wb["lines"]
    cols = [c.value for c in ls[1]]
    if cols[:len(LINE_COLUMNS)] != LINE_COLUMNS:
        frappe.throw(_("SC-E-HIS-EXTRACT: cột sheet 'lines' sai layout hợp đồng"),
                     title="SC-E-HIS-EXTRACT")
    lines = []
    for row in ls.iter_rows(min_row=2):
        vals = {cols[i]: (c.value if c.value is not None else "") for i, c in enumerate(row)}
        if all((v == "" or v is None) for v in vals.values()):
            continue
        line = {}
        for k in LINE_COLUMNS:
            v = vals.get(k, "")
            line[k] = flt(v) if k in NUM_COLS else str(v).strip()
        line["tt"] = cint(line["tt"])
        lines.append(line)
    return {
        "schema_version": SUPPORTED_VERSION,
        "slip_type": hdr.get("slip_type", "transfer"),
        "profile": hdr.get("profile", ""),
        "slip_no": str(hdr.get("slip_no", "")).strip(),
        "slip_date": str(hdr.get("slip_date", "")).strip(),
        "from_warehouse_name": str(hdr.get("from_warehouse_name", "")).strip(),
        "to_warehouse_name": str(hdr.get("to_warehouse_name", "")).strip(),
        "lines": lines,
    }
```

- [ ] **Step 5: Chạy — phải PASS (T8 và toàn bộ T1-T7 còn xanh)**

Run: `bench --site <site> execute supplycore.tests.smoke_his_import.run`
Expected: in `T8 ... ok` và `ALL TESTS PASSED`.

- [ ] **Step 6: Commit**

```bash
cd ~/frappe-bench/apps/supplycore && git add supplycore/api/his_file_read.py \
  supplycore/tests/fixtures/ supplycore/tests/smoke_his_import.py && \
  git commit -m "feat(his): read JSON/Excel handoff file -> canonical dict (his_file_read)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task B2: Endpoint `import_slip_file`

**Files:**
- Modify: `supplycore/api/his_import.py` (thêm endpoint; bỏ `import_transfer_slip` cũ)
- Test: `supplycore/tests/smoke_his_import.py` (thêm `_import_file_test`)

- [ ] **Step 1: Thêm test thất bại** (import file JSON đầu-cuối → draft_with_errors khi chưa seed)

```python
def _import_file_test():
    """import_slip_file(JSON) khi chưa seed map/item → draft_with_errors (đi qua _process_extracted)."""
    import os
    from supplycore.api.his_import import _read_and_process
    base = os.path.join(os.path.dirname(__file__), "fixtures")
    r = _read_and_process(os.path.join(base, "sample_slip.json"))
    assert r["status"] in ("draft_with_errors", "draft_review", "submitted"), r["status"]
    assert r["his_slip_no"] == "PX-FIX"
    return f"T9 import_file status={r['status']} slip={r['his_slip_no']}"
```

Thêm `out.append(_import_file_test())` vào `run()` sau T8.

- [ ] **Step 2: Chạy — phải FAIL**

Run: `bench --site <site> execute supplycore.tests.smoke_his_import.run`
Expected: FAIL ở T9 (no `_read_and_process`).

- [ ] **Step 3: Sửa `his_import.py`** — thêm reader-dispatch + endpoint; xóa `import_transfer_slip` + `_check_permission` cũ thay bằng dùng chung

Thay block cuối (`@frappe.whitelist() def import_transfer_slip...` đến hết file, dòng 285–326) bằng:

```python
# ---------------------------------------------------------------------------
# Đọc + xử lý file bàn giao từ tool his-slip-extractor
# ---------------------------------------------------------------------------
def _read_and_process(path: str, pdf_file_url=None) -> dict:
    from supplycore.api.his_file_read import read_json_file, read_xlsx_file
    lower = path.lower()
    if lower.endswith(".json"):
        data = read_json_file(path)
    elif lower.endswith((".xlsx", ".xls")):
        data = read_xlsx_file(path)
    else:
        frappe.throw(_("SC-E-HIS-EXTRACT: Chỉ nhận file .json hoặc .xlsx"),
                     title="SC-E-HIS-EXTRACT")
    # Excel có thể được sửa tay (nguồn sự thật) → KHÔNG auto-submit, luôn Draft đối chiếu.
    force_draft = lower.endswith((".xlsx", ".xls"))
    return _process_extracted(data, pdf_file_url=pdf_file_url, force_draft=force_draft)


@frappe.whitelist()
def import_slip_file(file_url: str) -> dict:
    """Nhập 1 phiếu chuyển kho từ FILE do tool his-slip-extractor sinh ra.

    file_url: URL file .json (máy) hoặc .xlsx (người đã đối chiếu/sửa). Trả report
    dict (xem _process_extracted). PDF gốc lưu để audit qua his_pdf nếu cần (đính kèm
    riêng — không bắt buộc).
    """
    _check_permission()
    if not file_url:
        frappe.throw(_("Thiếu file_url"))
    try:
        file_doc = frappe.get_doc("File", {"file_url": file_url})
    except frappe.DoesNotExistError:
        frappe.throw(_("Không tìm thấy file: {0}").format(file_url))
    return _read_and_process(file_doc.get_full_path(), pdf_file_url=file_url)


def _check_permission():
    allowed = {"System Manager", "SupplyCore Manager", "SupplyCore Storekeeper",
               "Warehouse Officer"}
    if not (set(frappe.get_roles(frappe.session.user)) & allowed):
        frappe.throw(_("Bạn không có quyền nhập phiếu chuyển kho HIS"),
                     frappe.PermissionError)
```

- [ ] **Step 4: Chạy — phải PASS (T1-T9 xanh)**

Run: `bench --site <site> execute supplycore.tests.smoke_his_import.run`
Expected: `T9 import_file status=...` và `ALL TESTS PASSED`.

- [ ] **Step 5: Commit**

```bash
cd ~/frappe-bench/apps/supplycore && git add supplycore/api/his_import.py \
  supplycore/tests/smoke_his_import.py && \
  git commit -m "feat(his): import_slip_file endpoint (JSON auto / Excel force-draft); drop PDF import path

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task B3: Xóa lớp trích xuất khỏi SupplyCore + dọn test

**Files:**
- Delete: `supplycore/utils/his_vision.py`
- Delete: `supplycore/utils/his_ocr.py`
- Modify: `supplycore/tests/smoke_his_import.py` (bỏ `_ocr_parse_test` T6, `ocr_real`, `ocr_debug` — đã chuyển sang tool)
- Modify: `pyproject.toml` (bỏ dep `anthropic`)

- [ ] **Step 1: Bỏ T6 + helper OCR khỏi smoke test**

Trong `smoke_his_import.py`: xóa dòng gọi T6 trong `run()` (`out.append(_ocr_parse_test())` và comment T6), xóa hàm `_ocr_parse_test`, `ocr_real`, `ocr_debug` (trích xuất giờ test ở repo tool). GIỮ T1–T5, T7, T8, T9.

- [ ] **Step 2: Xóa 2 file lớp trích xuất**

```bash
cd ~/frappe-bench/apps/supplycore && \
  git rm supplycore/utils/his_vision.py supplycore/utils/his_ocr.py
```

- [ ] **Step 3: Bỏ dep `anthropic` khỏi `pyproject.toml`**

Mở `pyproject.toml`, xóa dòng `anthropic` trong `dependencies` (SupplyCore không gọi Claude nữa).

- [ ] **Step 4: Kiểm tra backend không còn tham chiếu**

Run: `cd ~/frappe-bench/apps/supplycore && grep -rn "his_vision\|his_ocr" supplycore/ || echo "CLEAN"`
Expected: `CLEAN`. (Lưu ý: `frontend/` vẫn còn gọi `import_transfer_slip` tới khi Task B4 sửa — grep toàn cục để ở Verification cuối, sau B4.)

- [ ] **Step 5: Chạy smoke test còn lại**

Run: `bench --site <site> execute supplycore.tests.smoke_his_import.run`
Expected: `ALL TESTS PASSED` (T1-T5,T7,T8,T9).

- [ ] **Step 6: Commit**

```bash
cd ~/frappe-bench/apps/supplycore && git add -A && \
  git commit -m "refactor(his): remove in-app extraction (his_vision/his_ocr) — moved to standalone tool

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task B4: Frontend — upload file JSON/Excel thay vì PDF

**Files:**
- Modify: `frontend/src/pages/HISImport.vue`

- [ ] **Step 1: Đổi `<script setup>` — bỏ chọn backend, đổi endpoint + accept file**

Thay khối chọn `method` và `runImport` (HISImport.vue dòng 17, 27–50) bằng:

```javascript
const file = ref(null)
const fileName = ref('')
const busy = ref(false)
const result = ref(null)
const errorMsg = ref('')

function onPick(e) {
  const f = e.target.files && e.target.files[0]
  file.value = f || null
  fileName.value = f ? f.name : ''
  result.value = null
  errorMsg.value = ''
}

async function runImport() {
  if (!file.value) { toast.error('Chọn file .json hoặc .xlsx từ tool trích xuất'); return }
  busy.value = true; result.value = null; errorMsg.value = ''
  try {
    const up = await uploadFile(file.value, { isPrivate: true })
    const r = await call('supplycore.api.his_import.import_slip_file', { file_url: up.file_url })
    result.value = r
    if (r.status === 'submitted') {
      toast.success(`Đã ghi nhận & submit phiếu ${r.his_slip_no} (${r.lines_ok} dòng)`)
    } else if (r.status === 'draft_review') {
      toast.success(`Đã nạp & tạo phiếu nháp ${r.his_slip_no} — đối chiếu rồi submit`)
    } else {
      toast.warning(`Tạo phiếu nháp — ${r.lines_error} dòng cần sửa`)
    }
  } catch (e) {
    errorMsg.value = e.message || String(e); toast.error(errorMsg.value)
  } finally { busy.value = false }
}
```

- [ ] **Step 2: Đổi `<template>` — bỏ radio backend, đổi mô tả + accept**

- Xóa khối "Phương thức đọc" (dòng 72–84).
- Đổi đoạn mô tả (dòng 65–70) thành: "Chọn file **.json** hoặc **.xlsx** do tool *his-slip-extractor* sinh ra. JSON khớp 100% → ghi nhận tự động; Excel (đã đối chiếu/sửa) → tạo phiếu nháp để submit tay."
- Đổi `<input type="file" accept="...">` (dòng 91) thành `accept=".json,.xlsx,application/json"` và nhãn nút "Chọn file" thay vì "Chọn PDF".
- Đổi `code="M6 · UC-18B"` subtitle thành "Nhập phiếu chuyển kho HIS từ file (tool tách riêng)".

- [ ] **Step 3: Build frontend**

Run: `cd ~/frappe-bench/apps/supplycore/frontend && npm run build`
Expected: build thành công, không lỗi tham chiếu `method`.

- [ ] **Step 4: Kiểm tra thủ công (mô tả)**

Mở màn M6 → "Nhập phiếu chuyển kho HIS" → chọn `sample_slip.json` → "Nhập" → thấy report (status + dòng). Chọn `sample_slip.xlsx` → thấy status `draft_review`/`draft_with_errors`.

- [ ] **Step 5: Commit**

```bash
cd ~/frappe-bench/apps/supplycore && git add frontend/ && \
  git commit -m "feat(his-ui): upload JSON/Excel from extractor tool instead of PDF

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task B5: Cập nhật tài liệu UC-18B (as-built sau tách)

**Files:**
- Modify: `supplycore/m6_transfer/HIS_IMPORT_FLOW.md`

- [ ] **Step 1: Thêm mục "12. Tách lớp trích xuất ra tool standalone (2026-06-15)"**

Ghi: lớp trích xuất (vision/ocr) chuyển sang repo `his-slip-extractor` (file handoff JSON+Excel); SupplyCore chỉ còn `import_slip_file` + `_process_extracted`; hợp đồng = JSON schema v1 + layout Excel; onboard BV mới = thêm profile trong tool (vision = config thuần, ocr = config + hook); trỏ tới spec/plan trong `docs/superpowers/`.

- [ ] **Step 2: Commit**

```bash
cd ~/frappe-bench/apps/supplycore && git add supplycore/m6_transfer/HIS_IMPORT_FLOW.md && \
  git commit -m "docs(his): as-built — extraction tách ra tool standalone, SupplyCore nhận file

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Verification cuối (sau khi xong cả 2 phase)

- [ ] Tool: `cd ~/his-slip-extractor && .venv/bin/pytest -q` → toàn bộ pass.
- [ ] Tool thật (cần tesseract+vie): `.venv/bin/his-extract --backend ocr --profile default/c31-hd ~/frappe-bench/apps/supplycore/docs/"Phiếu ĐC KHo.pdf"` → sinh `.json`+`.xlsx`, kiểm 12 dòng.
- [ ] SupplyCore: `bench --site <site> execute supplycore.tests.smoke_his_import.run` → `ALL TESTS PASSED`.
- [ ] End-to-end: chạy tool trên PDF mẫu → upload `.json` qua màn M6 → phiếu tạo đúng; upload `.xlsx` đã sửa → Draft đối chiếu.
- [ ] `grep` xác nhận SupplyCore không còn `anthropic`/`his_vision`/`his_ocr`/`import_transfer_slip`.

## Ghi chú quyết định còn mở (từ spec §9, đã chốt trong plan)
- **Đường PDF cũ:** XÓA hẳn (Task B3) — không deprecate-tạm (giảm deps SupplyCore).
- **Nạp file vào web:** cho phép cả `.json` và `.xlsx`; `.xlsx` luôn force-draft (Task B2 Step 3).
- **Ký/hash file:** BỎ (YAGNI) — không thêm trong phạm vi này.
