"""Cổng khách hàng SupplyCore MVL (GĐ4 Task 3) — trang web độc lập cho
khách hàng (role "SC Customer Portal"), TÁCH khỏi SPA nội bộ /supplycore.

Guard (`get_context`), theo đúng thứ tự:
  1. Guest -> redirect `/login?redirect-to=/portal` (đăng nhập Frappe chuẩn).
  2. Đăng nhập nhưng KHÔNG có role "SC Customer Portal" -> render thông báo
     từ chối truy cập tối giản (không lộ menu/dữ liệu nội bộ nào).
  3. Có role -> context chỉ gồm csrf_token (không fetch dữ liệu khách ở
     server) — toàn bộ dữ liệu (portal_me/portal_catalog/...) do trang tải
     qua `fetch()` client-side tới các hàm whitelist trong
     `supplycore.api.portal` (đã cô lập theo khách hàng, xem GĐ3).
"""

import frappe

PORTAL_ROLE = "SC Customer Portal"

no_cache = 1


def get_context(context):
    context.no_cache = 1
    context.show_sidebar = False
    context.no_breadcrumbs = True

    user = frappe.session.user if frappe.session else "Guest"

    # Khách vãng lai (Guest): KHÔNG redirect nữa — hiển thị màn Đăng ký / Đăng
    # nhập ngay trên /portal (thương mại điện tử: tự đăng ký rồi tự đăng nhập
    # qua supplycore.api.portal.portal_register — allow_guest).
    context.is_guest = (user == "Guest")

    # Chỉ user đăng nhập mà KHÔNG có role Portal mới là "access_denied".
    context.access_denied = (not context.is_guest) and (
        PORTAL_ROLE not in frappe.get_roles(user))

    # csrf_token cấp cho cả guest (phiên guest có token) để POST đăng ký hợp lệ.
    try:
        context.csrf_token = frappe.sessions.get_csrf_token()
    except Exception:
        context.csrf_token = ""

    return context
