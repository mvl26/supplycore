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

    _ocr = profile.get("ocr") or {}
    cols = {"header_keywords": _ocr["header_keywords"]} if _ocr.get("header_keywords") else None
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
