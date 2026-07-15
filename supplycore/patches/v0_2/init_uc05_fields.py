"""Patch: reload SC Item + SC Item Reorder để UC-05 fields apply trên môi trường
đã migrate trước commit này. Idempotent (reload_doc tự kiểm tra)."""

import frappe


def execute():
    frappe.reload_doc("supplycore", "doctype", "sc_item")
    frappe.reload_doc("m2_planning", "doctype", "sc_item_reorder")
