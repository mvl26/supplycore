"""Backend OCR offline (tesseract) cho phiếu chuyển kho HIS — UC-18B.

Phương án KHÔNG cần API key: render PDF → ảnh (pdftoppm) → tesseract OCR
(lang vie+eng) → dựng lại cấu trúc {slip_no, slip_date, from/to_warehouse_name,
lines} bằng toạ độ bounding-box (cụm dòng theo y, cụm cột theo x).

⚠️ Độ chính xác OCR trên bảng số dày (số lô, HSD, thập phân) thấp hơn Vision
rõ rệt → backend này LUÔN tạo Draft cho người đối chiếu PDF rồi submit tay
(xem his_import._process_extracted force_draft).

Phụ thuộc:
  - hệ thống: tesseract-ocr + tesseract-ocr-vie  (sudo apt install ...)
  - python (bench env): pytesseract, Pillow  (đã cài)
  - poppler: pdftoppm  (render PDF)

`parse_words_to_slip()` là hàm THUẦN (nhận list word-box) → unit-test được mà
không cần tesseract.
"""

import re
import tempfile

import frappe
from frappe import _

# Bố cục cột bảng C31-HD (trái → phải) và từ khoá nhận diện trên dòng header.
# Dùng để tìm x-center mỗi cột rồi chia "băng cột" cho các dòng dữ liệu.
COLS = ["tt", "name", "his_code", "uom", "batch_no", "expiry", "qty", "unit_price", "amount"]
HEADER_KEYWORDS = {
    "tt": ["tt"],
    "his_code": ["mã"],          # "Mã số"
    "uom": ["vị", "tính"],        # "Đơn vị tính"
    "batch_no": ["lô"],           # "Số lô"
    "expiry": ["hạn"],            # "Hạn sử dụng"
    "qty": ["lượng"],             # "Số lượng"
    "unit_price": ["giá"],        # "Đơn giá"
    "amount": ["tiền"],           # "Thành tiền"
}
# Cột tên không có keyword riêng — nằm giữa TT và Mã số.

STOP_ROW = ("tổng tiền", "cộng khoản", "số tiền viết")


def vn_number(s) -> float:
    """Chuẩn số Việt Nam → float. '.' = phân tách nghìn, ',' = thập phân.

    '2.300'→2300 ; '2.099,99'→2099.99 ; '379,12'→379.12 ; '180.824,59'→180824.59.
    Bỏ mọi ký tự không phải số/.,. Rỗng/không có số → 0.0.
    """
    if s is None:
        return 0.0
    t = re.sub(r"[^0-9.,]", "", str(s))
    if not t:
        return 0.0
    t = t.replace(".", "").replace(",", ".")
    # phòng nhiều dấu chấm còn sót
    if t.count(".") > 1:
        head, _sep, tail = t.rpartition(".")
        t = head.replace(".", "") + "." + tail
    try:
        return float(t)
    except ValueError:
        return 0.0


def _norm(s):
    return " ".join((s or "").split())


def _clean_code(s):
    """Mã HIS chỉ gồm chữ-số → bỏ ký tự lạ lọt vào từ cột bên (vd '+2025GE185')."""
    return re.sub(r"[^A-Za-z0-9]", "", s or "")


def _clean_name(s):
    """Bỏ rác đầu tên VT: vạch bảng '|' và số TT / dấu chấm lọt vào (vd '3. | Cinnarizin')."""
    s = _norm(s)
    s = re.sub(r"^[\s|]*\d{0,3}[.\s|]*", "", s)
    return s.strip(" |")


# ---------------------------------------------------------------------------
# Parse header (regex trên full text)
# ---------------------------------------------------------------------------
def parse_header(full_text: str) -> dict:
    t = full_text or ""
    out = {"slip_no": "", "slip_date": "", "from_warehouse_name": "", "to_warehouse_name": ""}

    m = re.search(r"S[ốô]\s*[:.]?\s*([A-Z0-9][A-Z0-9\-]{4,})", t, re.IGNORECASE)
    if m:
        out["slip_no"] = m.group(1).strip()

    m = re.search(r"[Nn]g[àa]y\s*(\d{1,2})\s*th[áa]ng\s*(\d{1,2})\s*n[ăa]m\s*(\d{4})", t)
    if m:
        out["slip_date"] = f"{int(m.group(1)):02d}/{int(m.group(2)):02d}/{m.group(3)}"
    else:
        m = re.search(r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})", t)
        if m:
            out["slip_date"] = f"{int(m.group(1)):02d}/{int(m.group(2)):02d}/{m.group(3)}"

    m = re.search(r"Kho\s+đi[eề]u\s+chuy[eể]n\s*[:.]?\s*(.+)", t, re.IGNORECASE)
    if m:
        out["from_warehouse_name"] = _norm(m.group(1).splitlines()[0])
    m = re.search(r"Kho\s+nh[ậâ]n\s*[:.]?\s*(.+)", t, re.IGNORECASE)
    if m:
        out["to_warehouse_name"] = _norm(m.group(1).splitlines()[0])
    return out


# ---------------------------------------------------------------------------
# Parse bảng từ word-box (THUẦN — test được)
# ---------------------------------------------------------------------------
def _cx(w):
    return w["left"] + w["width"] / 2.0


def _find_columns(words):
    """Tìm x-center mỗi cột + đáy header.

    Trước hết xác định ĐÚNG dòng header (dòng chứa nhiều keyword cột nhất) rồi
    chỉ dò keyword trong dòng đó — tránh khớp nhầm 'TT' trong câu quy định
    '(Ban hành theo TT số 107/2017...)' ở đầu trang.
    Trả (centers: {col: x}, header_bottom_y: float).
    """
    from collections import defaultdict
    lines = defaultdict(list)
    for w in words:
        lines[w["line"]].append(w)

    def score(ws):
        toks = {(x["text"] or "").strip().lower() for x in ws}
        return sum(1 for kws in HEADER_KEYWORDS.values() if any(k in toks for k in kws))

    header_line = max(lines.values(), key=score, default=[])
    if score(header_line) < 4:
        return {}, 0.0

    centers = {}
    low = [(w, (w["text"] or "").strip().lower()) for w in header_line]
    for col, kws in HEADER_KEYWORDS.items():
        for w, txt in low:
            if txt in kws:
                centers[col] = _cx(w)
                break
    header_y = max(w["top"] + w["height"] for w in header_line)
    return centers, header_y


def _column_bands(centers):
    """Từ x-center các cột → biên (band) mỗi cột (midpoint giữa 2 cột kề)."""
    present = [(c, centers[c]) for c in COLS if c in centers]
    present.sort(key=lambda x: x[1])
    bands = {}
    for i, (col, x) in enumerate(present):
        left = 0 if i == 0 else (present[i - 1][1] + x) / 2.0
        right = float("inf") if i == len(present) - 1 else (present[i + 1][1] + x) / 2.0
        bands[col] = (left, right)
    return bands, present


def _assign_col(x, bands):
    for col, (lo, hi) in bands.items():
        if lo <= x < hi:
            return col
    return None


def parse_words_to_slip(words, full_text):
    """Dựng dict phiếu từ list word-box + full_text.

    words: [{text,left,top,width,height,line}] (line = khoá dòng duy nhất).
    """
    data = parse_header(full_text)
    data["lines"] = []

    centers, header_y = _find_columns(words)
    if "his_code" not in centers or "amount" not in centers:
        # không tìm được header → trả phần header, lines rỗng (sẽ thành Draft trống)
        return data
    # Suy ra cột 'name' = giữa tt (hoặc mép trái) và his_code
    left_anchor = centers.get("tt", 0)
    centers["name"] = (left_anchor + centers["his_code"]) / 2.0
    bands, present = _column_bands(centers)

    # Gom word theo dòng (line key), chỉ lấy dòng nằm DƯỚI header
    rows = {}
    for w in words:
        if w["top"] <= header_y:
            continue
        rows.setdefault(w["line"], []).append(w)

    ordered = sorted(rows.values(), key=lambda ws: min(x["top"] for x in ws))

    current = None
    tt_counter = 0
    for ws in ordered:
        line_text = _norm(" ".join((x["text"] or "") for x in ws)).lower()
        if any(s in line_text for s in STOP_ROW):
            break
        cells = {c: [] for c in COLS}
        for w in sorted(ws, key=lambda x: x["left"]):
            col = _assign_col(_cx(w), bands)
            txt = (w["text"] or "").strip()
            # Cột Tên rộng & canh trái, sát cột TT (1 con số). Từ rơi vào băng TT
            # nhưng KHÔNG phải số TT (1-3 chữ số) thật ra là phần đầu của Tên →
            # chuyển sang cột name (nếu không sẽ mất chữ đầu tên VT).
            if col == "tt" and not re.fullmatch(r"\d{1,3}", txt):
                col = "name"
            if col:
                cells[col].append(txt)
        # Dòng MỚI = có số ở cột Thành tiền hoặc Số lượng (OCR đọc TT không đáng
        # tin). Dòng nối tiếp (ô tên/mã/lô xuống dòng) không có 2 cột này.
        amount_str = " ".join(cells["amount"]).strip()
        qty_str = " ".join(cells["qty"]).strip()
        is_new_row = bool(re.search(r"\d", amount_str)) or bool(re.search(r"\d", qty_str))

        if is_new_row:
            tt_counter += 1
            tt_raw = " ".join(cells["tt"]).strip()
            current = {
                "tt": int(tt_raw) if re.fullmatch(r"\d{1,3}", tt_raw) else tt_counter,
                "name": _clean_name(" ".join(cells["name"])),
                "his_code": _clean_code("".join(cells["his_code"])),
                "uom": " ".join(cells["uom"]).strip(),
                "batch_no": "".join(cells["batch_no"]).strip(),
                "expiry": "".join(cells["expiry"]).strip(),
                "qty": vn_number(" ".join(cells["qty"])),
                "unit_price": vn_number(" ".join(cells["unit_price"])),
                "amount": vn_number(" ".join(cells["amount"])),
            }
            data["lines"].append(current)
        elif current is not None:
            # dòng nối tiếp (ô bị xuống dòng) → ghép vào row hiện tại
            if cells["name"]:
                current["name"] = _norm(current["name"] + " " + " ".join(cells["name"]))
            if cells["his_code"]:
                current["his_code"] = _clean_code(current["his_code"] + "".join(cells["his_code"]))
            if cells["batch_no"]:
                current["batch_no"] += "".join(cells["batch_no"]).strip()
            if cells["expiry"] and not current["expiry"]:
                current["expiry"] = "".join(cells["expiry"]).strip()
    return data


# ---------------------------------------------------------------------------
# OCR thật (cần tesseract)
# ---------------------------------------------------------------------------
def extract_slip_ocr(pdf_path: str) -> dict:
    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        frappe.throw(_("SC-E-HIS-EXTRACT: Thiếu pytesseract/Pillow trong môi trường"),
                     title="SC-E-HIS-EXTRACT")

    # Kiểm tra tesseract binary + gói tiếng Việt
    try:
        langs = pytesseract.get_languages(config="")
    except (pytesseract.TesseractNotFoundError, EnvironmentError):
        frappe.throw(_(
            "SC-E-HIS-EXTRACT: Chưa cài tesseract. Chạy: "
            "sudo apt install tesseract-ocr tesseract-ocr-vie"
        ), title="SC-E-HIS-EXTRACT")
    lang = "vie+eng" if "vie" in langs else "eng"

    from supplycore.utils.his_vision import render_pdf_to_pngs

    all_words = []
    full_text_parts = []
    line_offset = 0
    with tempfile.TemporaryDirectory(prefix="his_ocr_") as tmp:
        pages = render_pdf_to_pngs(pdf_path, tmp)
        for pg_idx, p in enumerate(pages):
            img = Image.open(p)
            full_text_parts.append(pytesseract.image_to_string(img, lang=lang, config="--psm 4"))
            tsv = pytesseract.image_to_data(img, lang=lang, config="--psm 4",
                                            output_type=pytesseract.Output.DICT)
            n = len(tsv["text"])
            y_shift = pg_idx * 100000  # tách trang theo y để không trộn dòng
            for i in range(n):
                txt = (tsv["text"][i] or "").strip()
                if not txt:
                    continue
                try:
                    conf = float(tsv["conf"][i])
                except (ValueError, TypeError):
                    conf = -1
                if conf < 30:
                    continue
                line_key = (pg_idx, tsv["block_num"][i], tsv["par_num"][i], tsv["line_num"][i])
                all_words.append({
                    "text": txt,
                    "left": tsv["left"][i],
                    "top": tsv["top"][i] + y_shift,
                    "width": tsv["width"][i],
                    "height": tsv["height"][i],
                    "line": line_key,
                })

    full_text = "\n".join(full_text_parts)
    data = parse_words_to_slip(all_words, full_text)
    if not data.get("slip_no") and not data.get("lines"):
        frappe.throw(_(
            "SC-E-HIS-EXTRACT: OCR không đọc được nội dung phiếu. Kiểm tra chất "
            "lượng PDF hoặc cài gói tiếng Việt (tesseract-ocr-vie)."
        ), title="SC-E-HIS-EXTRACT")
    return data
