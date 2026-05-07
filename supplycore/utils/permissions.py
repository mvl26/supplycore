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


def dispensing_perm(doc, user=None, permission_type=None):
    """has_permission cho Patient Dispensing — chỉ Pharmacy Officer + bác sĩ liên quan."""
    if not user:
        user = frappe.session.user
    roles = frappe.get_roles(user)
    if "System Manager" in roles or "Pharmacy Officer" in roles:
        return True
    return False
