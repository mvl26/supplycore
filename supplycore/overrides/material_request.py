"""Hook lifecycle vào ERPNext Material Request — tích hợp M2."""

import frappe
from frappe import _


def on_submit(doc, method=None):
    """on_submit: notify SC-ACCOUNTANT để xử lý sang Purchase Order."""
    if doc.material_request_type != "Purchase":
        return

    # Recipient: tất cả SC-ACCOUNTANT có email + có quyền Purchase Order
    recipients = frappe.db.sql_list("""
        SELECT DISTINCT u.email FROM `tabUser` u
        JOIN `tabHas Role` r ON r.parent = u.name
        WHERE r.role IN ('SupplyCore Accountant', 'SupplyCore Purchaser')
          AND u.enabled = 1 AND u.email IS NOT NULL AND u.email != ''
    """)
    if not recipients:
        return

    plan_link = ""
    if doc.get("sc_procurement_plan"):
        plan_link = f' (từ <a href="/app/procurement-plan/{doc.sc_procurement_plan}">{doc.sc_procurement_plan}</a>)'

    rows = "".join(
        f"<tr><td>{r.item_code}</td><td>{r.item_name or ''}</td>"
        f"<td>{r.qty}</td><td>{r.uom}</td><td>{r.warehouse or ''}</td></tr>"
        for r in doc.items
    )
    message = f"""
        <h3>SupplyCore — Material Request mới chờ xử lý</h3>
        <p>{doc.name}{plan_link} đã submit ngày {doc.transaction_date}.</p>
        <p>Cần ngày: {doc.schedule_date}. Tổng items: {len(doc.items)}.</p>
        <table border="1" cellpadding="6" cellspacing="0">
            <tr><th>Mã VT</th><th>Tên</th><th>SL</th><th>UOM</th><th>Kho</th></tr>
            {rows}
        </table>
        <p><a href="/app/material-request/{doc.name}">Mở Material Request</a></p>
    """
    frappe.sendmail(
        recipients=recipients,
        subject=f"[SupplyCore] Material Request {doc.name} chờ xử lý",
        message=message,
        delayed=True,
    )
