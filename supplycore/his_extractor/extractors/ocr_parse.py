"""Hàm parse THUẦN cho phiếu chuyển kho HIS — dựng bảng từ word-box (tesseract).

Port từ SupplyCore utils/his_ocr.py, gỡ phụ thuộc Frappe. parse_words_to_slip nhận
tham số `cols` để profile khác nạp bố cục cột riêng (mặc định = C31-HD)."""

import re

COLS = ["tt", "name", "his_code", "uom", "batch_no", "expiry", "qty", "unit_price", "amount"]
HEADER_KEYWORDS = {
    "tt": ["tt"],
    "his_code": ["mã"],
    "uom": ["vị", "tính"],
    "batch_no": ["lô"],
    "expiry": ["hạn"],
    "qty": ["lượng"],
    "unit_price": ["giá"],
    "amount": ["tiền"],
}

STOP_ROW = ("tổng tiền", "cộng khoản", "số tiền viết")


def vn_number(s) -> float:
    """Chuẩn số Việt Nam → float. '.'=nghìn, ','=thập phân. Rỗng→0.0."""
    if s is None:
        return 0.0
    t = re.sub(r"[^0-9.,]", "", str(s))
    if not t:
        return 0.0
    t = t.replace(".", "").replace(",", ".")
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
    return re.sub(r"[^A-Za-z0-9]", "", s or "")


def _clean_name(s):
    s = _norm(s)
    s = re.sub(r"^[\s|]*\d{0,3}[.\s|]*", "", s)
    return s.strip(" |")


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


def _cx(w):
    return w["left"] + w["width"] / 2.0


def _find_columns(words, header_keywords=HEADER_KEYWORDS):
    """Tìm x-center mỗi cột + đáy header. Dò keyword trong đúng dòng header (dòng
    có nhiều keyword cột nhất) để tránh khớp nhầm 'TT' ở câu quy định đầu trang."""
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


def _column_bands(centers):
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


def parse_words_to_slip(words, full_text, cols=None):
    """Dựng dict phiếu từ list word-box + full_text.
    words: [{text,left,top,width,height,line}] (line = khoá dòng duy nhất).
    cols: dict tuỳ chọn {'header_keywords': {...}} cho layout khác C31-HD."""
    header_keywords = (cols or {}).get("header_keywords") or HEADER_KEYWORDS
    data = parse_header(full_text)
    data["lines"] = []
    centers, header_y = _find_columns(words, header_keywords)
    if "his_code" not in centers or "amount" not in centers:
        return data
    left_anchor = centers.get("tt", 0)
    centers["name"] = (left_anchor + centers["his_code"]) / 2.0
    bands, present = _column_bands(centers)
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
            if col == "tt" and not re.fullmatch(r"\d{1,3}", txt):
                col = "name"
            if col:
                cells[col].append(txt)
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
            if cells["name"]:
                current["name"] = _norm(current["name"] + " " + " ".join(cells["name"]))
            if cells["his_code"]:
                current["his_code"] = _clean_code(current["his_code"] + "".join(cells["his_code"]))
            if cells["batch_no"]:
                current["batch_no"] += "".join(cells["batch_no"]).strip()
            if cells["expiry"] and not current["expiry"]:
                current["expiry"] = "".join(cells["expiry"]).strip()
    return data
