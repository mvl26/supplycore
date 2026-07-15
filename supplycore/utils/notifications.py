"""Helper gửi notification — wrap Frappe Email + SMS."""

import frappe


def notify(users, subject, message, doctype=None, name=None):
    for u in users:
        frappe.publish_realtime(
            event="supplycore_alert",
            message={"subject": subject, "message": message},
            user=u,
        )
