"""PWA — phục vụ service worker ở gốc /sw.js với header Service-Worker-Allowed.

Vì app chạy ở /supplycore/* còn asset ở /assets/..., service worker phải nằm ở
đường dẫn ANCESTOR của /supplycore để kiểm soát được route app. /assets/.../sw.js
KHÔNG kiểm soát được /supplycore. Giải pháp: phục vụ sw.js ở gốc /sw.js, cho phép
scope /supplycore/ qua header Service-Worker-Allowed.
"""

import frappe
from werkzeug.wrappers import Response


class ServiceWorkerRenderer:
    def __init__(self, path, status_code=None):
        self.path = path
        self.status_code = status_code

    def can_render(self):
        return self.path == "sw.js"

    def render(self):
        sw_file = frappe.get_app_path("supplycore", "public", "frontend", "sw.js")
        try:
            with open(sw_file, "r", encoding="utf-8") as f:
                content = f.read()
        except FileNotFoundError:
            content = "// SupplyCore SW chưa build\n"
        resp = Response(content, mimetype="application/javascript")
        resp.headers["Service-Worker-Allowed"] = "/supplycore/"
        resp.headers["Cache-Control"] = "no-cache, max-age=0"
        return resp
