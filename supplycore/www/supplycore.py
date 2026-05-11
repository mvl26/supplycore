"""SupplyCore frontend SPA entrypoint."""

import frappe


def get_context(context):
    """Inject CSRF token + login check."""
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login?redirect-to=/supplycore"
        raise frappe.Redirect
    context.no_cache = 1
    context.show_sidebar = False
    context.no_breadcrumbs = True
    context.csrf_token = frappe.sessions.get_csrf_token()
    return context
