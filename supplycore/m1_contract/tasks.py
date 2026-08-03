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
    from supplycore.utils.emailer import send_email, sc_list_url
    table = f"""
        <table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;font-size:13px">
            <tr style="background:#f3f6fb"><th align="left">Mã HĐ</th><th align="left">NCC</th>
                <th>Hết hạn</th><th>Số ngày còn lại</th><th align="right">Hạn mức còn lại</th></tr>
            {rows}
        </table>
    """
    send_email(
        recipients=recipients,
        subject=f"[SupplyCore] {len(expiring)} HĐ khung sắp hết hạn",
        title="Hợp đồng khung sắp hết hạn",
        intro=f"Có <b>{len(expiring)}</b> hợp đồng khung sắp hết hạn — cần theo dõi để gia hạn hoặc thanh lý:",
        body_html=table, note_kind="warn",
        cta_url=sc_list_url("Framework Contract"), cta_label="Mở danh sách HĐ khung",
    )
