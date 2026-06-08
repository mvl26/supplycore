"""PWA — phục vụ service worker và web manifest ở GỐC qua page_renderer (số ít).

Vì app chạy ở /supplycore/* còn asset ở /assets/..., service worker phải nằm ở
đường dẫn ANCESTOR của /supplycore để kiểm soát được route app (/assets/.../sw.js
chỉ có scope /assets/...). Giải pháp: phục vụ /sw.js ở gốc với header
Service-Worker-Allowed: /supplycore.

manifest.webmanifest cũng phải có ở GỐC /manifest.webmanifest: vite-plugin-pwa ghi
nó vào precache của SW bằng URL tương đối ("manifest.webmanifest") — với SW phục vụ
ở /sw.js, URL này phân giải thành /manifest.webmanifest, nên file phải tồn tại ở đó,
nếu không một precache 404 sẽ làm hỏng toàn bộ quá trình cài service worker.
"""

import frappe
from werkzeug.wrappers import Response

# path (không có dấu "/" đầu) -> (tên file build, content-type, có cần header SW-Allowed)
_PWA_FILES = {
    "sw.js": ("sw.js", "application/javascript", True),
    "manifest.webmanifest": ("manifest.webmanifest", "application/manifest+json", False),
}


class ServiceWorkerRenderer:
    def __init__(self, path, status_code=None):
        self.path = path
        self.status_code = status_code

    def can_render(self):
        return self.path in _PWA_FILES

    def render(self):
        filename, content_type, needs_sw_allowed = _PWA_FILES[self.path]
        build_file = frappe.get_app_path("supplycore", "public", "frontend", filename)
        try:
            with open(build_file, "r", encoding="utf-8") as f:
                content = f.read()
        except FileNotFoundError:
            content = "" if self.path == "manifest.webmanifest" else "// SupplyCore SW chưa build\n"
        resp = Response(content, mimetype=content_type)
        if needs_sw_allowed:
            resp.headers["Service-Worker-Allowed"] = "/supplycore"
        resp.headers["Cache-Control"] = "no-cache, max-age=0"
        return resp
