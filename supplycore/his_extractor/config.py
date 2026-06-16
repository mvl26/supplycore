"""Cấu hình tool: ưu tiên biến môi trường ANTHROPIC_API_KEY, fallback config.toml."""
import os
import tomllib
from .errors import ExtractError

DEFAULT_CONFIG = os.path.expanduser("~/.his-extractor/config.toml")


def get_api_key(config_path: str = DEFAULT_CONFIG) -> str:
    key = (os.environ.get("ANTHROPIC_API_KEY") or "").strip()
    if key:
        return key
    if os.path.exists(config_path):
        with open(config_path, "rb") as f:
            key = (tomllib.load(f).get("anthropic_api_key") or "").strip()
        if key:
            return key
    raise ExtractError("Chưa cấu hình anthropic_api_key (env ANTHROPIC_API_KEY hoặc "
                       f"{config_path}). Backend vision cần key; dùng --backend ocr nếu không có.")
