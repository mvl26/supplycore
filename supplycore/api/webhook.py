"""Webhook outbound — HIS/EMR, Cổng BHYT (Phase 2)."""

import frappe


@frappe.whitelist()
def bhyt_submit_claim(claim_name: str):
    """POST quyết toán BHYT lên Bộ Y tế (REST)."""
    return {"submitted": False, "reason": "stub"}


def flush_outbound_queue():
    """Scheduler hourly — đẩy webhook đang queue."""
    pass
