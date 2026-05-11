"""SupplyCore SPA entrypoint — standalone, NO Frappe Desk UI.

Session is allowed (Guest OK) — SPA tự xử lý login flow qua /api/method/login.
"""

import json
import frappe
import time


def get_context(context):
    context.no_cache = 1
    context.no_breadcrumbs = True
    context.show_sidebar = False
    user = frappe.session.user if frappe.session else "Guest"
    context.session_user_json = json.dumps({
        "name": user,
        "full_name": frappe.db.get_value("User", user, "full_name") if user != "Guest" else "Guest",
        "is_guest": user == "Guest",
        "roles": frappe.get_roles(user) if user != "Guest" else [],
    })
    try:
        context.csrf_token = frappe.sessions.get_csrf_token()
    except Exception:
        context.csrf_token = ""
    context.build_v = int(time.time())
    return context


# Catch-all: any /supplycore/* trả về SPA shell
no_cache = True
