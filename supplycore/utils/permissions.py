"""Custom permission logic — gọi từ hooks.py."""

import frappe


def stock_entry_query(user=None):
    """permission_query_conditions cho Stock Entry — giới hạn theo warehouse của user."""
    if not user:
        user = frappe.session.user
    if "System Manager" in frappe.get_roles(user):
        return ""
    # TODO: lookup warehouses gán cho user, return SQL where clause
    return ""
