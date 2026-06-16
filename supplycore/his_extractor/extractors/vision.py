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
