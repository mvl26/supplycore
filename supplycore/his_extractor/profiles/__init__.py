"""Registry profile (bệnh viện × loại phiếu). Onboard BV mới = thêm 1 file .yaml
(vision: config thuần) hoặc + code hook (ocr nếu cần parser riêng)."""
import os
import sys
import yaml
from ..errors import ExtractError

if getattr(sys, "frozen", False):
    _DIR = os.path.join(getattr(sys, "_MEIPASS", os.path.dirname(sys.executable)),
                        "his_extractor", "profiles")
else:
    _DIR = os.path.dirname(__file__)


def list_profiles() -> list[str]:
    out = []
    for f in os.listdir(_DIR):
        if not f.endswith(".yaml"):
            continue
        with open(os.path.join(_DIR, f), encoding="utf-8") as fh:
            prof = yaml.safe_load(fh) or {}
        name = prof.get("name")
        if name:
            out.append(name)
    return sorted(out)


def load_profile(name: str) -> dict:
    available = []
    for f in os.listdir(_DIR):
        if not f.endswith(".yaml"):
            continue
        with open(os.path.join(_DIR, f), encoding="utf-8") as fh:
            prof = yaml.safe_load(fh) or {}
        pname = prof.get("name")
        if pname == name:
            return prof
        if pname:
            available.append(pname)
    raise ExtractError(f"Không có profile '{name}'. Có: {', '.join(sorted(available))}")
