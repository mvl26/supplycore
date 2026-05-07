"""Integration endpoints xuyên module — HIS, LIS, SMS, Email."""

import frappe


@frappe.whitelist()
def his_notify_dispensing(patient_dispensing: str):
    """Gửi event sang HIS khi Patient Dispensing submit."""
    return {"sent": False}
