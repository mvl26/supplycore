"""Trích xuất phiếu xuất điều chuyển HIS (PDF ảnh-hoá) bằng Claude Vision — UC-18B.

Phiếu HIS (Mẫu C31-HD) được in qua "Microsoft: Print To PDF" nên KHÔNG có
text layer (pdftotext/pdfplumber vô dụng) và không nhúng ảnh raster — chữ vẽ
bằng glyph không map Unicode. Cách duy nhất đáng tin: render từng trang PDF
thành ảnh PNG (pdftoppm) rồi gửi cho Claude (`claude-opus-4-8`) đọc, trả JSON
có cấu trúc (output_config.format json_schema).

Toàn bộ điểm chạm Claude API nằm trong file này — phần orchestration
(api/his_import.py) chỉ tiêu thụ dict đã validate, nên test được không cần key.

Config bắt buộc (site_config.json): `anthropic_api_key`.
Dependency: bench env đã `pip install anthropic`; poppler (`pdftoppm`) có sẵn.
"""

import base64
import json
import os
import subprocess
import tempfile

import frappe
from frappe import _

MODEL = "claude-opus-4-8"
RENDER_DPI = 200  # đủ nét cho bảng số dày (số lô, HSD)

# JSON schema ép Claude trả đúng cấu trúc. Tránh type-union/null (structured
# outputs hạn chế) — field thiếu trả chuỗi rỗng / số 0, orchestration tự xử lý.
EXTRACT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "slip_no": {"type": "string", "description": "Số phiếu, vd PX050626-00021923"},
        "slip_date": {"type": "string", "description": "Ngày phiếu DD/MM/YYYY, rỗng nếu không có"},
        "from_warehouse_name": {"type": "string", "description": "Kho điều chuyển (nguồn)"},
        "to_warehouse_name": {"type": "string", "description": "Kho nhận (đích)"},
        "lines": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "tt": {"type": "integer", "description": "Số thứ tự dòng, 0 nếu không rõ"},
                    "name": {"type": "string", "description": "Tên/nhãn hiệu/quy cách vật tư"},
                    "his_code": {"type": "string", "description": "Cột 'Mã số' (mã HIS)"},
                    "uom": {"type": "string", "description": "Đơn vị tính"},
                    "batch_no": {"type": "string", "description": "Cột 'Số lô'"},
                    "expiry": {"type": "string", "description": "Hạn sử dụng DD/MM/YYYY, rỗng nếu không có"},
                    "qty": {"type": "number", "description": "Số lượng"},
                    "unit_price": {"type": "number", "description": "Đơn giá, 0 nếu không có"},
                    "amount": {"type": "number", "description": "Thành tiền, 0 nếu không có"},
                },
                "required": ["tt", "name", "his_code", "uom", "batch_no",
                             "expiry", "qty", "unit_price", "amount"],
            },
        },
    },
    "required": ["slip_no", "slip_date", "from_warehouse_name",
                 "to_warehouse_name", "lines"],
}

PROMPT = """Đây là ảnh các trang của 1 PHIẾU XUẤT ĐIỀU CHUYỂN kho (Mẫu số C31-HD) \
từ phần mềm HIS bệnh viện. Hãy đọc CHÍNH XÁC TUYỆT ĐỐI và trả về JSON theo schema.

Các trường ở đầu phiếu:
- "Số:" → slip_no (vd PX050626-00021923)
- "Ngày ... tháng ... năm ..." → slip_date dạng DD/MM/YYYY
- "Kho điều chuyển:" → from_warehouse_name (kho nguồn)
- "Kho nhận:" → to_warehouse_name (kho đích)

Bảng vật tư có các cột: TT | Tên/nhãn hiệu/quy cách | Mã số | Đơn vị tính | \
Số lô | Hạn sử dụng | Số lượng | Đơn giá | Thành tiền.
Map sang: tt | name | his_code | uom | batch_no | expiry | qty | unit_price | amount.

QUY TẮC BẮT BUỘC:
1. Định dạng số Việt Nam: dấu "." là phân tách hàng nghìn, dấu "," là thập phân. \
Trả về số thuần: "2.300" → 2300 ; "2.099,99" → 2099.99 ; "379,12" → 379.12 ; \
"180.824,59" → 180824.59. KHÔNG giữ dấu phân tách.
2. Một số ô bị xuống dòng (vd Mã số "2025GE24" và "0" ở 2 dòng) — hãy GHÉP LẠI \
thành 1 giá trị ("2025GE240"). Tên vật tư dài nhiều dòng cũng ghép thành 1 chuỗi.
3. Mỗi dòng TT là 1 phần tử trong "lines". Nếu cùng Mã số nhưng khác Số lô thì \
là 2 dòng riêng — giữ nguyên.
4. KHÔNG đọc dòng "Tổng tiền"/"Cộng khoản" thành 1 item.
5. Ô trống: chuỗi → "" , số → 0.
6. Giữ nguyên Số lô đúng như in (kể cả số 0 đứng đầu, vd "0126", "020126").

Trả về JSON đúng schema, không thêm chú thích."""


def _require_api_key() -> str:
    key = frappe.conf.get("anthropic_api_key")
    if not key:
        frappe.throw(_(
            "SC-E-HIS-EXTRACT: Chưa cấu hình 'anthropic_api_key' trong site_config.json. "
            "Chạy: bench --site <site> set-config anthropic_api_key <key>"
        ), title="SC-E-HIS-EXTRACT")
    return key


def render_pdf_to_pngs(pdf_path: str, out_dir: str) -> list:
    """Render mỗi trang PDF thành 1 PNG bằng pdftoppm (poppler). Trả list path."""
    if not os.path.exists(pdf_path):
        frappe.throw(_("SC-E-HIS-EXTRACT: Không tìm thấy file PDF: {0}").format(pdf_path))
    prefix = os.path.join(out_dir, "his_page")
    try:
        subprocess.run(
            ["pdftoppm", "-r", str(RENDER_DPI), "-png", pdf_path, prefix],
            check=True, capture_output=True, timeout=120,
        )
    except FileNotFoundError:
        frappe.throw(_("SC-E-HIS-EXTRACT: Thiếu 'pdftoppm' (poppler-utils) trên server"))
    except subprocess.CalledProcessError as e:
        frappe.throw(_("SC-E-HIS-EXTRACT: Render PDF lỗi: {0}").format(
            (e.stderr or b"").decode("utf-8", "ignore")[:300]))
    pages = sorted(
        os.path.join(out_dir, f) for f in os.listdir(out_dir)
        if f.startswith("his_page") and f.endswith(".png")
    )
    if not pages:
        frappe.throw(_("SC-E-HIS-EXTRACT: PDF không render được trang nào"))
    return pages


def extract_slip(pdf_path: str) -> dict:
    """Trích xuất phiếu HIS từ PDF → dict {slip_no, slip_date, from/to_warehouse_name, lines}.

    Raise (frappe.throw) với mã SC-E-HIS-EXTRACT nếu thiếu key / SDK / refusal /
    network / parse lỗi. KHÔNG trả dữ liệu một phần.
    """
    api_key = _require_api_key()
    try:
        import anthropic
    except ImportError:
        frappe.throw(_(
            "SC-E-HIS-EXTRACT: Chưa cài SDK 'anthropic'. Chạy: "
            "./env/bin/pip install anthropic"
        ), title="SC-E-HIS-EXTRACT")

    with tempfile.TemporaryDirectory(prefix="his_render_") as tmp:
        pages = render_pdf_to_pngs(pdf_path, tmp)
        content = []
        for p in pages:
            with open(p, "rb") as f:
                b64 = base64.standard_b64encode(f.read()).decode("utf-8")
            content.append({
                "type": "image",
                "source": {"type": "base64", "media_type": "image/png", "data": b64},
            })
        content.append({"type": "text", "text": PROMPT})

        client = anthropic.Anthropic(api_key=api_key)
        try:
            resp = client.messages.create(
                model=MODEL,
                # 16000 đủ cho adaptive thinking + JSON bảng ~30 dòng, vẫn dưới
                # ngưỡng timeout non-streaming của SDK.
                max_tokens=16000,
                thinking={"type": "adaptive"},
                output_config={"format": {"type": "json_schema", "schema": EXTRACT_SCHEMA}},
                messages=[{"role": "user", "content": content}],
            )
        except anthropic.APIError as e:
            frappe.throw(_("SC-E-HIS-EXTRACT: Lỗi gọi Claude API: {0}").format(str(e)[:300]),
                         title="SC-E-HIS-EXTRACT")

        if resp.stop_reason == "refusal":
            frappe.throw(_("SC-E-HIS-EXTRACT: Claude từ chối xử lý ảnh phiếu (refusal)."),
                         title="SC-E-HIS-EXTRACT")
        if resp.stop_reason == "max_tokens":
            frappe.throw(_(
                "SC-E-HIS-EXTRACT: Phiếu quá dài, JSON bị cắt (max_tokens). "
                "Phiếu nhiều dòng — hãy tách phiếu hoặc liên hệ kỹ thuật tăng giới hạn."
            ), title="SC-E-HIS-EXTRACT")

        text = next((b.text for b in resp.content if getattr(b, "type", None) == "text"), "")
        try:
            data = json.loads(text)
        except (ValueError, TypeError):
            frappe.throw(_("SC-E-HIS-EXTRACT: Không parse được JSON từ Claude:\n{0}").format(
                (text or "")[:500]), title="SC-E-HIS-EXTRACT")

    if not isinstance(data, dict) or "lines" not in data:
        frappe.throw(_("SC-E-HIS-EXTRACT: Kết quả không đúng cấu trúc mong đợi"),
                     title="SC-E-HIS-EXTRACT")
    return data
