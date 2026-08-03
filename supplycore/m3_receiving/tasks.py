"""Scheduled tasks cho M3 Receiving."""

import frappe


def check_return_responses():
    """Daily (UC-11 ngoại lệ): escalate Return PR Pending > 7 ngày không phản hồi NCC.

    - Find Return PR docstatus=1, return_status=Pending Supplier Response,
      posting_date < today-7, escalated_at IS NULL.
    - Email Manager.
    - Set escalated_at = now (dedup — chỉ escalate 1 lần / Return PR).
    """
    rows = frappe.db.sql("""
        SELECT name, supplier, supplier_name, posting_date, total_value
        FROM `tabSC Purchase Receipt`
        WHERE docstatus = 1 AND is_return = 1
          AND return_status = 'Pending Supplier Response'
          AND escalated_at IS NULL
          AND DATEDIFF(CURDATE(), posting_date) >= 7
        LIMIT 50
    """, as_dict=True)

    if not rows:
        return {"escalated": 0, "candidates": 0}

    managers = frappe.db.sql_list("""
        SELECT DISTINCT u.email FROM `tabUser` u
        JOIN `tabHas Role` r ON r.parent = u.name
        WHERE r.role = 'SupplyCore Manager' AND u.enabled = 1
          AND u.email IS NOT NULL AND u.email != ''
    """) or []

    escalated = 0
    for r in rows:
        if managers:
            try:
                frappe.sendmail(
                    recipients=managers,
                    subject=f"[SupplyCore][ESCALATE] Return PR {r.name} chưa xử lý sau 7 ngày",
                    message=(f"<p>Return PR <a href='{frappe.utils.get_url('/supplycore/doc/SC%20Purchase%20Receipt/' + r.name)}'>{r.name}</a> "
                             f"gửi NCC <b>{r.supplier_name or r.supplier}</b> ngày {r.posting_date} "
                             f"chưa nhận được phản hồi xác nhận đổi hàng / hoàn tiền.</p>"
                             f"<p>Giá trị: {frappe.format(r.total_value, {'fieldtype':'Currency'})}</p>"
                             f"<p>Vui lòng liên hệ NCC để xử lý.</p>"),
                    delayed=True,
                )
            except Exception as e:
                frappe.log_error(message=f"PR={r.name}: {str(e)[:500]}",
                                  title="UC-11 check_return_responses")
        frappe.db.set_value("SC Purchase Receipt", r.name,
                             "escalated_at", frappe.utils.now())
        escalated += 1
    frappe.db.commit()
    return {"escalated": escalated, "candidates": len(rows)}
