"""M11 Dashboard scheduler tasks."""

import frappe
from frappe import _
from frappe.utils import flt, today, now, add_days, getdate


def send_daily_kpi():
    """Daily: snapshot KPI + email tóm tắt cho EXEC + MGR."""
    from supplycore.api.kpi import get_executive_dashboard
    snapshot = get_executive_dashboard("this_month")

    recipients = _get_recipients(["SupplyCore Executive", "SupplyCore Manager"])
    if not recipients:
        return

    kpis = snapshot["kpis"]
    body = f"""
        <h3>SupplyCore — Daily KPI Snapshot</h3>
        <table border="1" cellpadding="6" cellspacing="0">
            <tr><th>KPI</th><th>Giá trị</th></tr>
            <tr><td>Tổng giá trị tồn kho</td><td>{frappe.format(kpis['stock_value'], {'fieldtype': 'Currency'})}</td></tr>
            <tr><td>Chi phí tháng này</td><td>{frappe.format(kpis['monthly_cost'], {'fieldtype': 'Currency'})}</td></tr>
            <tr><td>Công nợ NCC</td><td>{frappe.format(kpis['ap_outstanding'], {'fieldtype': 'Currency'})}</td></tr>
            <tr><td>PO chờ duyệt/giao</td><td>{kpis['pending_pos']}</td></tr>
            <tr><td>Lô sắp hết hạn (≤30 ngày)</td><td>{kpis['expiring_soon']}</td></tr>
            <tr><td>Items tồn dưới safety stock</td><td>{kpis['low_stock_items']}</td></tr>
        </table>
        <p>Cảnh báo open: <b>{snapshot['open_alerts_total']}</b>
           ({', '.join(f'{k}={v}' for k, v in snapshot['open_alerts'].items())})</p>
        <p><a href="/app/sc-alert?resolved=0">Mở Alert Center</a></p>
    """
    try:
        frappe.sendmail(recipients=recipients,
                         subject=f"[SupplyCore] Daily KPI {today()}",
                         message=body, delayed=False)
    except Exception as e:
        frappe.log_error(message=str(e)[:1000], title="M11 send_daily_kpi")


def scan_alerts():
    """Daily: scan toàn bộ active rules + tạo SC Alert mới (deduped)."""
    rules = frappe.get_all("SC Alert Rule",
        filters={"enabled": 1}, fields=["name", "title", "alert_type",
                  "severity", "threshold_value", "recipient_roles"])
    total_created = 0
    for rule in rules:
        try:
            created = _scan_one_rule(rule)
            total_created += created
            frappe.db.set_value("SC Alert Rule", rule.name, {
                "last_triggered_at": now(),
                "last_alert_count": created,
            })
        except Exception as e:
            frappe.log_error(message=f"Rule {rule.name}: {str(e)[:500]}",
                              title="M11 scan_alerts")
    frappe.db.commit()
    return total_created


def _scan_one_rule(rule) -> int:
    """Scan 1 rule, tạo SC Alert nếu match."""
    handler = {
        "expiring_batch": _scan_expiring_batch,
        "contract_expiring": _scan_contract_expiring,
        "fc_remaining_low": _scan_fc_remaining_low,
        "low_stock": _scan_low_stock,
        "overdue_payment": _scan_overdue_payment,
        "qc_pending": _scan_qc_pending,
        "recall_outstanding": _scan_recall_outstanding,
    }.get(rule.alert_type)
    if not handler:
        return 0
    return handler(rule)


def _scan_expiring_batch(rule) -> int:
    threshold = int(flt(rule.threshold_value) or 30)
    rows = frappe.db.sql("""
        SELECT b.name AS batch, b.item, b.expiry_date,
               DATEDIFF(b.expiry_date, CURDATE()) AS days_left
        FROM `tabSC Batch` b
        WHERE b.disabled = 0 AND b.blocked = 0
          AND b.expiry_date IS NOT NULL
          AND b.expiry_date >= CURDATE()
          AND b.expiry_date <= DATE_ADD(CURDATE(), INTERVAL %s DAY)
          AND EXISTS (
            SELECT 1 FROM `tabSC Stock Ledger Entry` sle
            WHERE sle.batch = b.name AND sle.is_cancelled = 0
            GROUP BY sle.batch HAVING SUM(sle.qty_change) > 0
          )
        LIMIT 100
    """, threshold, as_dict=True)
    return _create_alerts_dedup(rule, rows, lambda r:
        f"Batch {r.batch} sắp hết hạn",
        lambda r: f"Item {r.item} batch {r.batch} còn {r.days_left} ngày (hết hạn {r.expiry_date})",
        lambda r: ("SC Batch", r.batch))


def _scan_contract_expiring(rule) -> int:
    threshold = int(flt(rule.threshold_value) or 30)
    rows = frappe.db.sql("""
        SELECT name AS fc, supplier, valid_to,
               DATEDIFF(valid_to, CURDATE()) AS days_left
        FROM `tabFramework Contract`
        WHERE docstatus = 1 AND status = 'Active'
          AND valid_to <= DATE_ADD(CURDATE(), INTERVAL %s DAY)
          AND valid_to >= CURDATE()
        LIMIT 50
    """, threshold, as_dict=True)
    return _create_alerts_dedup(rule, rows, lambda r:
        f"Framework Contract {r.fc} sắp hết hạn",
        lambda r: f"NCC {r.supplier}, hết hạn {r.valid_to} (còn {r.days_left} ngày)",
        lambda r: ("Framework Contract", r.fc))


def _scan_fc_remaining_low(rule) -> int:
    threshold_pct = flt(rule.threshold_value) or 20
    rows = frappe.db.sql("""
        SELECT name AS fc, supplier, total_value, remaining_value,
               (remaining_value / total_value * 100) AS remaining_pct
        FROM `tabFramework Contract`
        WHERE docstatus = 1 AND status = 'Active'
          AND total_value > 0
          AND (remaining_value / total_value * 100) <= %s
        LIMIT 50
    """, threshold_pct, as_dict=True)
    return _create_alerts_dedup(rule, rows, lambda r:
        f"HĐK {r.fc} sắp hết hạn mức",
        lambda r: f"NCC {r.supplier}, còn {round(r.remaining_pct, 1)}% (= {frappe.format(r.remaining_value, {'fieldtype': 'Currency'})})",
        lambda r: ("Framework Contract", r.fc))


def _scan_low_stock(rule) -> int:
    """Scan items below safety_stock.

    UC-05: support per-warehouse override via SC Item Reorder child rows.
    - Items với override rows (safety_stock>0) → scan per (item, warehouse)
    - Items KHÔNG có override rows → fallback item-level (logic cũ)
    """
    rows_wh = frappe.db.sql("""
        SELECT r.parent AS item, i.item_name, r.warehouse,
               COALESCE(SUM(sle.qty_change), 0) AS qty,
               r.safety_stock
        FROM `tabSC Item Reorder` r
        JOIN `tabSC Item` i ON i.name = r.parent
        LEFT JOIN `tabSC Stock Ledger Entry` sle
            ON sle.item = r.parent AND sle.warehouse = r.warehouse
           AND sle.is_cancelled = 0
        WHERE i.disabled = 0 AND i.is_stock_item = 1
          AND r.parenttype = 'SC Item'
          AND COALESCE(r.safety_stock, 0) > 0
        GROUP BY r.parent, r.warehouse, r.safety_stock, i.item_name
        HAVING qty < r.safety_stock
        LIMIT 50
    """, as_dict=True)

    rows_item = frappe.db.sql("""
        SELECT i.name AS item, i.item_name, NULL AS warehouse,
               COALESCE(SUM(sle.qty_change), 0) AS qty,
               i.safety_stock
        FROM `tabSC Item` i
        LEFT JOIN `tabSC Stock Ledger Entry` sle
            ON sle.item = i.name AND sle.is_cancelled = 0
        WHERE i.disabled = 0 AND i.is_stock_item = 1
          AND i.safety_stock > 0
          AND NOT EXISTS (
              SELECT 1 FROM `tabSC Item Reorder` r
              WHERE r.parent = i.name AND r.parenttype = 'SC Item'
                AND COALESCE(r.safety_stock, 0) > 0
          )
        GROUP BY i.name, i.item_name, i.safety_stock
        HAVING qty < i.safety_stock
        LIMIT 50
    """, as_dict=True)

    def _title(r):
        if r.warehouse:
            return f"Item {r.item} dưới safety stock @ {r.warehouse}"
        return f"Item {r.item} dưới safety stock"

    def _msg(r):
        if r.warehouse:
            return f"{r.item_name} @ {r.warehouse}: tồn {r.qty} < safety {r.safety_stock}"
        return f"{r.item_name}: tồn {r.qty} < safety {r.safety_stock}"

    return _create_alerts_dedup(rule, rows_wh + rows_item, _title, _msg,
                                  lambda r: ("SC Item", r.item))


def _scan_overdue_payment(rule) -> int:
    rows = frappe.db.sql("""
        SELECT name AS pi, supplier, due_date, outstanding_amount,
               DATEDIFF(CURDATE(), due_date) AS days_overdue
        FROM `tabSC Purchase Invoice`
        WHERE docstatus = 1 AND status NOT IN ('Paid', 'Cancelled')
          AND due_date < CURDATE()
          AND outstanding_amount > 0
        LIMIT 50
    """, as_dict=True)
    return _create_alerts_dedup(rule, rows, lambda r:
        f"PI {r.pi} quá hạn {r.days_overdue} ngày",
        lambda r: f"NCC {r.supplier}, còn nợ {frappe.format(r.outstanding_amount, {'fieldtype': 'Currency'})}",
        lambda r: ("SC Purchase Invoice", r.pi))


def _scan_qc_pending(rule) -> int:
    rows = frappe.db.sql("""
        SELECT name AS pr, supplier, posting_date,
               DATEDIFF(CURDATE(), posting_date) AS days_pending
        FROM `tabSC Purchase Receipt`
        WHERE docstatus = 1 AND qc_status = 'Pending' AND qc_required = 1
          AND DATEDIFF(CURDATE(), posting_date) >= %s
        LIMIT 50
    """, int(flt(rule.threshold_value) or 1), as_dict=True)
    return _create_alerts_dedup(rule, rows, lambda r:
        f"PR {r.pr} chờ QC quá {r.days_pending} ngày",
        lambda r: f"NCC {r.supplier}, posting {r.posting_date}",
        lambda r: ("SC Purchase Receipt", r.pr))


def _scan_recall_outstanding(rule) -> int:
    rows = frappe.db.sql("""
        SELECT name AS rcl, batch_no, item, outstanding_qty
        FROM `tabSC Recall Notice`
        WHERE docstatus = 1 AND status IN ('Issued', 'In Progress')
          AND outstanding_qty > 0
        LIMIT 30
    """, as_dict=True)
    return _create_alerts_dedup(rule, rows, lambda r:
        f"Recall {r.rcl} chưa xử lý xong",
        lambda r: f"Batch {r.batch_no}, item {r.item}, còn {r.outstanding_qty} chưa thu hồi",
        lambda r: ("SC Recall Notice", r.rcl))


def _create_alerts_dedup(rule, rows, title_fn, msg_fn, ref_fn) -> int:
    """Tạo Alert deduplicated: 1 ref → 1 open alert active.

    UC-33: sau khi tạo SC Alert, gọi rule.dispatch_alert_notifications()
    để gửi qua các channel enabled (email/sms). In-app đã được tạo qua doc.

    BUG-012: Dedup theo (alert_type, reference_doctype, reference_name,
    DATE(alert_date)) chứ KHÔNG chỉ theo alert_rule — vì 2 rule khác nhau
    có thể cùng tạo alert cho 1 reference (vd 'fc_expiring 30d' + 'fc_expiring
    7d' cùng fire cho FC hết hạn trong 7 ngày).
    """
    created = 0
    rule_doc = None
    for row in rows:
        ref_dt, ref_nm = ref_fn(row)
        # BUG-012: Check existing open alert cùng (alert_type, reference) trong 7 ngày
        # bất kể alert_rule nào tạo ra.
        existing = frappe.db.exists("SC Alert", {
            "alert_type": rule.alert_type,
            "reference_doctype": ref_dt,
            "reference_name": ref_nm,
            "resolved": 0,
            "alert_date": [">=", add_days(today(), -7)],
        })
        if existing:
            continue
        a = frappe.new_doc("SC Alert")
        a.alert_date = now()
        a.alert_rule = rule.name
        a.alert_type = rule.alert_type
        a.severity = rule.severity
        a.title = title_fn(row)
        a.message = msg_fn(row)
        a.reference_doctype = ref_dt
        a.reference_name = ref_nm
        a.flags.ignore_permissions = True
        a.insert()
        created += 1
        # UC-33: dispatch email/sms qua rule
        if rule_doc is None:
            try:
                rule_doc = frappe.get_doc("SC Alert Rule", rule.name)
            except Exception:
                rule_doc = False
        if rule_doc:
            try:
                rule_doc.dispatch_alert_notifications(a)
            except Exception as e:
                frappe.log_error(message=str(e)[:1000],
                                  title=f"UC-33 dispatch {rule.name}")
    return created


def _get_recipients(roles: list) -> list:
    return frappe.db.sql_list("""
        SELECT DISTINCT u.email FROM `tabUser` u
        JOIN `tabHas Role` r ON r.parent = u.name
        WHERE r.role IN ({roles_in})
          AND u.enabled = 1 AND u.email IS NOT NULL AND u.email != ''
    """.format(roles_in=", ".join(["%s"] * len(roles))), tuple(roles)) or []


# =====================================================================
# UC-34: lifecycle scheduler tasks
# =====================================================================
def auto_resolve_alerts():
    """UC-34 step 6: re-evaluate điều kiện; resolve nếu không còn áp dụng."""
    open_alerts = frappe.db.sql("""
        SELECT name, alert_type, reference_doctype, reference_name, alert_rule
        FROM `tabSC Alert`
        WHERE resolved = 0
          AND (snooze_until IS NULL OR snooze_until < NOW())
        LIMIT 500
    """, as_dict=True)
    resolved_count = 0
    for a in open_alerts:
        try:
            if _is_condition_lifted(a):
                frappe.db.set_value("SC Alert", a.name, {
                    "resolved": 1,
                    "resolution_action": "Acknowledged",
                    "resolved_by": "Administrator",
                    "resolved_at": now(),
                    "remarks": "Auto-resolved: condition không còn áp dụng",
                })
                resolved_count += 1
        except Exception as e:
            frappe.log_error(message=f"{a.name}: {str(e)[:300]}",
                              title="UC-34 auto_resolve_alerts")
    if resolved_count:
        frappe.db.commit()
    return resolved_count


def _is_condition_lifted(alert) -> bool:
    """Trả True nếu điều kiện trigger không còn áp dụng."""
    t = alert.alert_type
    ref_dt = alert.reference_doctype
    ref_nm = alert.reference_name
    if not (ref_dt and ref_nm and frappe.db.exists(ref_dt, ref_nm)):
        return True  # Reference đã bị xóa → resolve

    if t == "low_stock" and ref_dt == "SC Item":
        # Compare current qty vs safety_stock
        safety = flt(frappe.db.get_value("SC Item", ref_nm, "safety_stock") or 0)
        if safety <= 0:
            return True
        qty = flt(frappe.db.sql("""
            SELECT COALESCE(SUM(qty_change), 0)
            FROM `tabSC Stock Ledger Entry`
            WHERE item = %s AND is_cancelled = 0
        """, ref_nm)[0][0])
        return qty >= safety

    if t == "expiring_batch" and ref_dt == "SC Batch":
        blocked = int(frappe.db.get_value("SC Batch", ref_nm, "blocked") or 0)
        if blocked:
            return True
        # Hết stock của batch
        qty = flt(frappe.db.sql("""
            SELECT COALESCE(SUM(qty_change), 0)
            FROM `tabSC Stock Ledger Entry`
            WHERE batch = %s AND is_cancelled = 0
        """, ref_nm)[0][0])
        return qty <= 0

    if t == "contract_expiring" and ref_dt == "Framework Contract":
        status = frappe.db.get_value("Framework Contract", ref_nm, "status")
        return status != "Active"

    if t == "fc_remaining_low" and ref_dt == "Framework Contract":
        fc = frappe.db.get_value("Framework Contract", ref_nm,
            ["status", "total_value", "remaining_value"], as_dict=True)
        if not fc or fc.status != "Active":
            return True
        if not fc.total_value:
            return True
        threshold = 20  # default
        if alert.alert_rule:
            tv = frappe.db.get_value("SC Alert Rule", alert.alert_rule, "threshold_value")
            threshold = flt(tv) or 20
        pct = (flt(fc.remaining_value) / flt(fc.total_value)) * 100
        return pct > threshold

    if t == "overdue_payment" and ref_dt == "SC Purchase Invoice":
        pi = frappe.db.get_value("SC Purchase Invoice", ref_nm,
            ["status", "outstanding_amount"], as_dict=True)
        if not pi:
            return True
        return (pi.status == "Paid") or (flt(pi.outstanding_amount) <= 0.01)

    if t == "qc_pending" and ref_dt == "SC Purchase Receipt":
        qc = frappe.db.get_value("SC Purchase Receipt", ref_nm, "qc_status")
        return qc != "Pending"

    if t == "recall_outstanding" and ref_dt == "SC Recall Notice":
        outstanding = flt(frappe.db.get_value("SC Recall Notice", ref_nm, "outstanding_qty") or 0)
        return outstanding <= 0.01

    return False  # Default: keep open


def escalate_overdue_alerts(threshold_hours: int = 48):
    """UC-34 ngoại lệ: alerts > X giờ chưa resolve → escalate.

    - Set escalated=1, escalated_at, escalated_to
    - Bump severity về Critical
    - Email tới escalated_to
    """
    from frappe.utils import add_to_date
    cutoff = add_to_date(now(), hours=-int(threshold_hours))
    rows = frappe.db.sql("""
        SELECT name, title, severity, alert_type, alert_date, assigned_to
        FROM `tabSC Alert`
        WHERE resolved = 0
          AND escalated = 0
          AND severity IN ('Critical', 'Warning')
          AND alert_date < %s
        LIMIT 200
    """, cutoff, as_dict=True)

    escalation_user = _get_escalation_user()
    if not escalation_user:
        return 0

    escalated_count = 0
    for a in rows:
        try:
            frappe.db.set_value("SC Alert", a.name, {
                "escalated": 1,
                "escalated_at": now(),
                "escalated_to": escalation_user,
                "severity": "Critical",  # Bump
            })
            try:
                frappe.sendmail(
                    recipients=[escalation_user],
                    subject=f"[ESCALATED] {a.title}",
                    message=(
                        f"<p>Alert <b>{a.name}</b> đã không được resolve trong "
                        f"{threshold_hours} giờ.</p>"
                        f"<p>Title: {a.title}</p>"
                        f"<p>Type: {a.alert_type} / Severity: {a.severity}</p>"
                        f"<p>Vui lòng xem: /app/sc-alert/{a.name}</p>"
                    ),
                    queue=True, now=False,
                )
            except Exception:
                pass
            escalated_count += 1
        except Exception as e:
            frappe.log_error(message=f"{a.name}: {str(e)[:300]}",
                              title="UC-34 escalate_overdue_alerts")
    if escalated_count:
        frappe.db.commit()
    return escalated_count


def _get_escalation_user() -> str:
    """Tìm user có role SupplyCore Executive (ưu tiên) → Manager → System Manager."""
    for role in ("SupplyCore Executive", "SupplyCore Manager", "System Manager"):
        u = frappe.db.sql("""
            SELECT u.name FROM `tabUser` u
            JOIN `tabHas Role` r ON r.parent = u.name
            WHERE r.role = %s AND u.enabled = 1
              AND u.name NOT IN ('Administrator', 'Guest')
            LIMIT 1
        """, role)
        if u:
            return u[0][0]
    return None
