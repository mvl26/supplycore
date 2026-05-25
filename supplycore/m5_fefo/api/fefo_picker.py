"""M5 FEFO — internal helpers + scheduler tasks (UC-17)."""

import frappe
from frappe import _
from frappe.utils import flt, getdate, today, date_diff, now
from supplycore.api.fefo import get_suggested_batches


@frappe.whitelist()
def suggest_batches(item_code: str, warehouse: str, qty: float = 0):
    return get_suggested_batches(item_code, warehouse, qty)


def register_batch(doc, method=None):
    """after_insert Batch — validate expiry + log."""
    if not doc.expiry_date:
        return
    days_left = date_diff(doc.expiry_date, today())
    if days_left < 0:
        frappe.msgprint(_("Batch {0} hết hạn ngay khi tạo ({1})")
                        .format(doc.name, doc.expiry_date),
                        indicator="red", alert=True)
    elif days_left < _get_min_shelf_life():
        frappe.msgprint(_("Batch {0}: hạn dùng còn {1} ngày — dưới ngưỡng tối thiểu")
                        .format(doc.name, days_left),
                        indicator="orange", alert=True)


def scan_expiring_batches():
    """UC-17 Daily: scan batches expiry trong info_window, phân loại theo
    severity Critical(<30d)/Warning(30-90d)/Info(90-180d). Tạo Batch Expiry
    Alert per (batch, warehouse). Email summary."""
    settings = frappe.get_single("SupplyCore Settings")
    critical = int(settings.get("expiry_alert_days_critical") or 30)
    warning = int(settings.get("expiry_alert_days_warning") or 90)
    info_window = 180

    rows = frappe.db.sql("""
        SELECT b.name AS batch_no, b.item AS item_code, i.item_name,
               b.expiry_date,
               DATEDIFF(b.expiry_date, CURDATE()) AS days_left,
               sle.warehouse,
               COALESCE(SUM(sle.qty_change), 0) AS current_qty
        FROM `tabSC Batch` b
        JOIN `tabSC Item` i ON i.name = b.item
        LEFT JOIN `tabSC Stock Ledger Entry` sle
            ON sle.batch = b.name AND sle.is_cancelled = 0
        WHERE b.disabled = 0
          AND COALESCE(b.blocked, 0) = 0
          AND b.expiry_date IS NOT NULL
          AND b.expiry_date >= CURDATE()
          AND b.expiry_date <= DATE_ADD(CURDATE(), INTERVAL %s DAY)
        GROUP BY b.name, sle.warehouse
        HAVING current_qty > 0
        ORDER BY b.expiry_date ASC
        LIMIT 500
    """, info_window, as_dict=True)

    created_count = 0
    for r in rows:
        if r.days_left < critical:
            severity = "Critical"
        elif r.days_left < warning:
            severity = "Warning"
        else:
            severity = "Info"

        if frappe.db.exists("Batch Expiry Alert", {
            "batch_no": r.batch_no, "warehouse": r.warehouse,
            "severity": severity, "resolved": 0,
            "alert_date": [">=", frappe.utils.add_days(today(), -7)],
        }):
            continue
        try:
            a = frappe.new_doc("Batch Expiry Alert")
            a.alert_date = today()
            a.batch_no = r.batch_no
            a.item_code = r.item_code
            a.item_name = r.item_name
            a.expiry_date = r.expiry_date
            a.days_to_expiry = r.days_left
            a.severity = severity
            a.warehouse = r.warehouse
            a.current_qty = flt(r.current_qty)
            a.flags.ignore_permissions = True
            a.insert()
            created_count += 1
        except Exception as e:
            frappe.log_error(message=f"BatchExpiryAlert failed batch={r.batch_no}: {e}",
                              title="UC-17 scan_expiring_batches")

    if created_count:
        _send_expiry_email(rows, critical)
    return {"created": created_count, "scanned": len(rows)}


def _get_batch_total_qty(batch_no: str) -> float:
    """SC SLE-based tổng qty của batch (across warehouses)."""
    return flt(frappe.db.sql("""
        SELECT COALESCE(SUM(qty_change), 0)
        FROM `tabSC Stock Ledger Entry`
        WHERE batch = %s AND is_cancelled = 0
    """, batch_no)[0][0])


def _get_min_shelf_life() -> int:
    try:
        v = frappe.db.get_single_value("SupplyCore Settings", "fefo_min_shelf_life_days")
        return int(v) if v else 30
    except Exception:
        return 30


def _send_expiry_email(rows, critical_days):
    settings = frappe.get_single("SupplyCore Settings")
    raw = settings.get("email_alert_recipients") if settings else None
    recipients = [e.strip() for e in (raw or "").split(",") if e.strip()]
    if not recipients:
        recipients = frappe.db.sql_list("""
            SELECT DISTINCT u.email FROM `tabUser` u
            JOIN `tabHas Role` r ON r.parent = u.name
            WHERE r.role IN ('SupplyCore Storekeeper', 'SupplyCore Manager', 'Pharmacy Officer')
              AND u.enabled = 1 AND u.email IS NOT NULL AND u.email != ''
        """) or []
    if not recipients:
        return

    body = "".join(
        f"<tr><td>{r.batch_no}</td><td>{r.item_code}</td><td>{r.item_name or ''}</td>"
        f"<td>{r.warehouse or '—'}</td>"
        f"<td>{r.expiry_date}</td>"
        f"<td style='color:{'#DC3545' if r.days_left < critical_days else '#FFC107'};"
        f"font-weight:bold'>{r.days_left}</td>"
        f"<td>{flt(r.current_qty)}</td></tr>"
        for r in rows
    )
    msg = f"""
        <h3>SupplyCore — Cảnh báo lô hàng sắp hết hạn</h3>
        <p>Có <b>{len(rows)}</b> lô hàng sắp hết hạn cần xử lý ưu tiên.</p>
        <table border="1" cellpadding="6" cellspacing="0">
            <tr><th>Lô</th><th>Mã VT</th><th>Tên</th><th>Kho</th>
                <th>Hạn dùng</th><th>Ngày còn</th><th>SL</th></tr>
            {body}
        </table>
        <p><a href="/app/batch-expiry-alert?resolved=0">Xem danh sách Alert</a></p>
    """
    try:
        frappe.sendmail(
            recipients=recipients,
            subject=f"[SupplyCore] {len(rows)} lô sắp hết hạn",
            message=msg, delayed=True,
        )
    except Exception as e:
        frappe.log_error(message=f"Email scan_expiring failed: {e}",
                          title="UC-17 _send_expiry_email")
