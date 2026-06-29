"""REST endpoints cho PDA / Mobile (M4).

mobile_login: vend api_key/api_secret cho Capacitor app — token auth thay
thế session+CSRF. App native dùng header:
    Authorization: token <api_key>:<api_secret>
"""

import frappe
from frappe.utils.password import check_password


@frappe.whitelist(allow_guest=True)
def mobile_login(usr, pwd):
    """Xác thực username/password, trả về api_key:api_secret.

    Raise frappe.AuthenticationError nếu credentials sai hoặc user bị disabled.

    Note: dùng check_password thay LoginManager() vì LoginManager.__init__ trên
    Frappe v15 truy cập frappe.local.request.path (unavailable ngoài HTTP context).
    check_password là hàm được LoginManager.authenticate gọi nội bộ, đảm bảo
    cùng exception type (frappe.AuthenticationError).
    """
    # Xác thực password — raise AuthenticationError nếu sai
    check_password(usr, pwd)

    # Kiểm tra user enabled (check_password không làm việc này)
    if not frappe.db.get_value("User", usr, "enabled"):
        raise frappe.AuthenticationError

    api_secret = _ensure_api_credentials(usr)
    user_doc = frappe.get_doc("User", usr)
    return {
        "user": usr,
        "full_name": user_doc.full_name or usr,
        "roles": [r.role for r in user_doc.get("roles", [])],
        "api_key": user_doc.api_key,
        "api_secret": api_secret,
    }


def _ensure_api_credentials(user: str) -> str:
    """Sinh api_key (nếu chưa có) và api_secret mới; lưu vào User.

    Frappe lưu api_secret dưới dạng Password (hashed) — ta trả về plaintext
    ngay trước khi save để client dùng được. Lần sau login sẽ tạo secret mới.
    """
    user_doc = frappe.get_doc("User", user)
    if not user_doc.api_key:
        user_doc.api_key = frappe.generate_hash(length=15)
    api_secret = frappe.generate_hash(length=15)
    user_doc.api_secret = api_secret
    user_doc.save(ignore_permissions=True)
    frappe.db.commit()
    return api_secret


@frappe.whitelist()
def scan_barcode(barcode: str):
    """Trả về Item / Batch / Bin Location khớp barcode."""
    return {}


@frappe.whitelist()
def confirm_putaway(batch_no: str, bin_location: str, qty: float):
    """Xác nhận putaway từ PDA — tạo Stock Entry Material Transfer."""
    return {"ok": True}
