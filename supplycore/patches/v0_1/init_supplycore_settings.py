"""Patch: ensure SupplyCore Settings có default values sau khi migrate field mới."""

import frappe


def execute():
    settings = frappe.get_single("SupplyCore Settings")
    defaults = {
        "fefo_strict_mode": 1,
        "fefo_min_shelf_life_days": 30,
        "expiry_alert_days_critical": 30,
        "expiry_alert_days_warning": 90,
        "po_approval_threshold": 50_000_000,
        "default_safety_stock_pct": 20,
        "contract_expiry_alert_days": 30,
        "audit_log_retention_days": 2555,
    }
    changed = False
    for field, value in defaults.items():
        if not settings.get(field):
            settings.set(field, value)
            changed = True
    if changed:
        settings.flags.ignore_permissions = True
        settings.save()
        frappe.db.commit()
