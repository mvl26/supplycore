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
