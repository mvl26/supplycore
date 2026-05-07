"""M5 FEFO — internal helpers + scheduler tasks.

Public API endpoints ở `supplycore/api/fefo.py` (theo Phase 2 API §4.1).
Module này chứa:
- `register_batch` (hook Batch.after_insert)
- `scan_expiring_batches` (scheduler daily)
- `suggest_batches` (alias cho compatibility với hooks cũ)
"""

import frappe
from frappe import _
from frappe.utils import flt, getdate, today, date_diff, now
from supplycore.api.fefo import get_suggested_batches


# ---------------------------------------------------------------------------
# Public alias — referenced trong cấu trúc cũ của hooks
# ---------------------------------------------------------------------------
@frappe.whitelist()
def suggest_batches(item_code: str, warehouse: str, qty: float = 0):
    return get_suggested_batches(item_code, warehouse, qty)


# ---------------------------------------------------------------------------
# Hook: Batch.after_insert
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Scheduler: daily expiry scan (BR-M5-02)
# ---------------------------------------------------------------------------
def scan_expiring_batches():
    """Daily: find batches expiring trong window cấu hình → tạo Batch Expiry Alert + email."""
    settings = frappe.get_single("SupplyCore Settings")
    critical = int(settings.get("expiry_alert_days_critical") or 30)
    warning = int(settings.get("expiry_alert_days_warning") or 90)

    rows = frappe.db.sql("""
        SELECT b.name AS batch_no, b.item AS item_code, i.item_name,
               b.expiry_date,
               DATEDIFF(b.expiry_date, CURDATE()) AS days_left
        FROM `tabSC Batch` b
        JOIN `tabSC Item` i ON i.name = b.item
        WHERE b.disabled = 0
          AND COALESCE(b.blocked, 0) = 0
          AND b.expiry_date IS NOT NULL
          AND b.expiry_date >= CURDATE()
          AND b.expiry_date <= DATE_ADD(CURDATE(), INTERVAL %s DAY)
        ORDER BY b.expiry_date ASC
        LIMIT 500
    """, warning, as_dict=True)

    if not rows:
        return

    created_count = 0
    for r in rows:
        severity = "Critical" if r.days_left < critical else "Warning"
        # Skip nếu đã có alert OPEN trong tuần qua cho cùng batch + severity
        existing = frappe.db.exists("Batch Expiry Alert", {
            "batch_no": r.batch_no,
            "severity": severity,
            "resolved": 0,
            "alert_date": [">=", frappe.utils.add_days(today(), -7)],
        })
        if existing:
            continue
        try:
            cur_qty = _get_batch_total_qty(r.batch_no)
            alert = frappe.new_doc("Batch Expiry Alert")
            alert.alert_date = today()
            alert.batch_no = r.batch_no
            alert.item_code = r.item_code
            alert.item_name = r.item_name
            alert.expiry_date = r.expiry_date
            alert.days_to_expiry = r.days_left
            alert.severity = severity
            alert.current_qty = cur_qty
            alert.flags.ignore_permissions = True
            alert.insert()
            created_count += 1
        except Exception as e:
            frappe.log_error(message=f"BatchExpiryAlert insert failed batch={r.batch_no}: {e}",
                             title="M5 scan_expiring_batches")

    if created_count:
        _send_expiry_email(rows, critical)


def _get_batch_total_qty(batch_no: str) -> float:
    return flt(frappe.db.sql("""
        SELECT COALESCE(SUM(actual_qty), 0)
        FROM `tabStock Ledger Entry`
        WHERE batch_no = %s AND is_cancelled = 0
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
        f"<td>{r.expiry_date}</td><td style='color:{'#DC3545' if r.days_left < critical_days else '#FFC107'};font-weight:bold'>{r.days_left}</td></tr>"
        for r in rows
    )
    msg = f"""
        <h3>SupplyCore — Cảnh báo lô hàng sắp hết hạn</h3>
        <p>Có <b>{len(rows)}</b> lô hàng sắp hết hạn cần xử lý ưu tiên (FEFO/trả NCC/hủy).</p>
        <table border="1" cellpadding="6" cellspacing="0">
            <tr><th>Lô</th><th>Mã VT</th><th>Tên</th><th>Hạn dùng</th><th>Số ngày còn</th></tr>
            {body}
        </table>
        <p><a href="/app/batch-expiry-alert?resolved=0">Xem danh sách Batch Expiry Alert</a></p>
    """
    try:
        frappe.sendmail(
            recipients=recipients,
            subject=f"[SupplyCore] {len(rows)} lô sắp hết hạn",
            message=msg, delayed=False,
        )
    except Exception as e:
        frappe.log_error(message=f"Email scan_expiring failed: {e}", title="M5 scan_expiring_batches")
