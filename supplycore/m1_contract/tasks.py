"""Scheduled tasks cho M1 Contract — chạy hàng ngày."""

import frappe
from frappe.utils import today, date_diff, getdate


def check_contract_expiry():
    """Daily: cảnh báo HĐK sắp hết hạn (30 / 15 / 7 ngày) — BR-M1-03."""
    settings = frappe.get_single("SupplyCore Settings")
    alert_days = settings.get("contract_expiry_alert_days") or 30

    contracts = frappe.get_all(
        "Framework Contract",
        filters={"docstatus": 1, "status": "Active"},
        fields=["name", "supplier", "supplier_name", "valid_to", "remaining_value"],
    )

    today_d = getdate(today())
    expiring = []
    for c in contracts:
        days_left = date_diff(c.valid_to, today_d)
        if days_left in (alert_days, 15, 7):
            expiring.append({**c, "days_left": days_left})
            frappe.db.set_value("Framework Contract", c.name, "expiring_soon", 1)
        elif days_left < 0:
            # Đã hết hạn — tự động đổi status
            frappe.db.set_value("Framework Contract", c.name, "status", "Expired")

    if not expiring:
        return

    # Gửi email cho recipient list trong Settings
    recipients_raw = settings.get("email_alert_recipients") or ""
    recipients = [e.strip() for e in recipients_raw.split(",") if e.strip()]
    if not recipients:
        # Fallback: tất cả user có role SupplyCore Manager / Accountant
        recipients = frappe.db.sql_list("""
            SELECT DISTINCT u.email FROM `tabUser` u
            JOIN `tabHas Role` r ON r.parent = u.name
            WHERE r.role IN ('SupplyCore Manager', 'SupplyCore Accountant')
              AND u.enabled = 1 AND u.email IS NOT NULL
        """)

    if not recipients:
        return

    rows = "".join(
        f"<tr><td>{c.name}</td><td>{c.supplier_name or c.supplier}</td>"
        f"<td>{c.valid_to}</td><td>{c.days_left}</td>"
        f"<td>{frappe.format(c.remaining_value, {'fieldtype': 'Currency'})}</td></tr>"
        for c in expiring
    )
    message = f"""
        <h3>SupplyCore — Hợp đồng khung sắp hết hạn</h3>
        <table border="1" cellpadding="6" cellspacing="0">
            <tr>
                <th>Mã HĐ</th><th>NCC</th><th>Hết hạn</th>
                <th>Số ngày còn lại</th><th>Hạn mức còn lại</th>
            </tr>
            {rows}
        </table>
        <p><a href="/app/framework-contract">Mở danh sách HĐK</a></p>
    """
    frappe.sendmail(
        recipients=recipients,
        subject=f"[SupplyCore] {len(expiring)} HĐK sắp hết hạn",
        message=message,
        delayed=True,
    )
