"""Trang đăng nhập riêng cho Cổng khách hàng (/portal/login).

Tách khỏi trang /login mặc định của Frappe — giao diện thương hiệu Miyano, đăng
nhập qua /api/method/login rồi chuyển vào /portal. Nếu đã đăng nhập sẵn với role
khách hàng thì chuyển thẳng vào cổng.
"""

import frappe

# Các role được coi là "khách hàng cổng" — đăng nhập xong vào thẳng /portal.
PORTAL_ROLES = {"SC Customer Portal", "Khách hàng"}

no_cache = 1


def get_context(context):
    context.no_cache = 1
    context.show_sidebar = False
    context.no_breadcrumbs = True

    user = frappe.session.user
    if user and user != "Guest":
        # Đã đăng nhập + có role khách hàng -> vào cổng luôn.
        if PORTAL_ROLES & set(frappe.get_roles(user)):
            frappe.local.flags.redirect_location = "/portal"
            raise frappe.Redirect

    context.csrf_token = frappe.sessions.get_csrf_token()
    return context
