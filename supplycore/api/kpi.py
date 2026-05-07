"""KPI Dashboard API — supplycore.api.kpi.* (M11).

Endpoint canonical theo Phase 2 API §4.5:
  GET /api/method/supplycore.api.kpi.get_executive_dashboard
"""

import frappe
from frappe import _
from frappe.utils import flt, today, add_days, add_months, getdate


@frappe.whitelist()
def get_executive_dashboard(period: str = "this_month") -> dict:
    """6 KPIs theo SCR-01 Executive Dashboard:
       - stock_value: tổng giá trị tồn kho hiện tại
       - monthly_cost: chi phí mua hàng kỳ này
       - ap_outstanding: công nợ NCC còn phải trả
       - pending_pos: số PO chờ duyệt/chờ giao
       - expiring_soon: số lô sắp hết hạn (≤30 ngày)
       - low_stock_items: số mặt hàng dưới reorder threshold (placeholder)
    """
    from_date, to_date = _resolve_period(period)

    # 1. Stock value: SUM(qty × valuation_rate) hiện tại
    stock_value = flt(frappe.db.sql("""
        SELECT COALESCE(SUM(qty_change * valuation_rate), 0)
        FROM `tabSC Stock Ledger Entry`
        WHERE is_cancelled = 0
    """)[0][0])

    # 2. Monthly cost: SUM PI grand_total trong period
    monthly_cost = flt(frappe.db.sql("""
        SELECT COALESCE(SUM(grand_total), 0)
        FROM `tabSC Purchase Invoice`
        WHERE invoice_date BETWEEN %s AND %s AND docstatus = 1
    """, (from_date, to_date))[0][0])

    # 3. AP outstanding: tổng PI còn phải trả
    ap_outstanding = flt(frappe.db.sql("""
        SELECT COALESCE(SUM(outstanding_amount), 0)
        FROM `tabSC Purchase Invoice`
        WHERE docstatus = 1 AND status != 'Cancelled'
    """)[0][0])

    # 4. Pending POs: PO submit chưa Received
    pending_pos = frappe.db.count("SC Purchase Order",
        {"docstatus": 1, "status": ["in",
            ["Approved", "Sent to Supplier", "Partially Received"]]})

    # 5. Expiring soon: SC Batch <30 ngày
    expiring_soon = frappe.db.sql("""
        SELECT COUNT(DISTINCT b.name)
        FROM `tabSC Batch` b
        WHERE b.disabled = 0
          AND b.blocked = 0
          AND b.expiry_date IS NOT NULL
          AND b.expiry_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 30 DAY)
          AND EXISTS (
              SELECT 1 FROM `tabSC Stock Ledger Entry` sle
              WHERE sle.batch = b.name AND sle.is_cancelled = 0
              GROUP BY sle.batch
              HAVING SUM(sle.qty_change) > 0
          )
    """)[0][0]

    # 6. Low stock items: items có tổng tồn kho < safety_stock
    low_stock = flt(frappe.db.sql("""
        SELECT COUNT(*) FROM (
            SELECT i.name, COALESCE(SUM(sle.qty_change), 0) AS qty,
                   i.safety_stock
            FROM `tabSC Item` i
            LEFT JOIN `tabSC Stock Ledger Entry` sle
                ON sle.item = i.name AND sle.is_cancelled = 0
            WHERE i.disabled = 0 AND i.is_stock_item = 1
              AND i.safety_stock > 0
            GROUP BY i.name
            HAVING qty < i.safety_stock
        ) t
    """)[0][0])

    # Top 5 items by consumption value
    top_items = frappe.db.sql("""
        SELECT sle.item AS item_code, i.item_name,
               SUM(ABS(sle.qty_change)) AS qty_used,
               SUM(ABS(sle.qty_change) * sle.valuation_rate) AS cost
        FROM `tabSC Stock Ledger Entry` sle
        JOIN `tabSC Item` i ON i.name = sle.item
        WHERE sle.qty_change < 0 AND sle.is_cancelled = 0
          AND sle.posting_date BETWEEN %s AND %s
        GROUP BY sle.item
        ORDER BY cost DESC LIMIT 5
    """, (from_date, to_date), as_dict=True)

    # Outstanding alerts
    open_alerts = frappe.db.sql("""
        SELECT severity, COUNT(*) AS count
        FROM `tabSC Alert`
        WHERE resolved = 0
          AND (snooze_until IS NULL OR snooze_until < NOW())
        GROUP BY severity
    """, as_dict=True)
    alert_breakdown = {a.severity: int(a.count) for a in open_alerts}

    return {
        "period": {"from": from_date, "to": to_date, "label": period},
        "kpis": {
            "stock_value": flt(stock_value),
            "monthly_cost": flt(monthly_cost),
            "ap_outstanding": flt(ap_outstanding),
            "pending_pos": int(pending_pos),
            "expiring_soon": int(expiring_soon),
            "low_stock_items": int(low_stock),
        },
        "top_items": [{**r, "qty_used": flt(r["qty_used"]), "cost": flt(r["cost"])}
                       for r in top_items],
        "open_alerts": alert_breakdown,
        "open_alerts_total": sum(alert_breakdown.values()),
    }


@frappe.whitelist()
def get_warehouse_dashboard(warehouse: str) -> dict:
    """KPI cho SK theo warehouse cụ thể."""
    if not frappe.db.exists("SC Warehouse", warehouse):
        frappe.throw(_("Warehouse {0} không tồn tại").format(warehouse))

    qty_total = flt(frappe.db.sql("""
        SELECT COALESCE(SUM(qty_change), 0)
        FROM `tabSC Stock Ledger Entry`
        WHERE warehouse = %s AND is_cancelled = 0
    """, warehouse)[0][0])

    rows_exp = frappe.db.sql("""
        SELECT COUNT(DISTINCT b.name)
        FROM `tabSC Batch` b
        JOIN `tabSC Stock Ledger Entry` sle ON sle.batch = b.name
        WHERE sle.warehouse = %s AND sle.is_cancelled = 0
          AND b.disabled = 0 AND b.blocked = 0
          AND b.expiry_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 30 DAY)
        GROUP BY b.name
        HAVING SUM(sle.qty_change) > 0
    """, warehouse)
    expiring_at_wh = flt(rows_exp[0][0]) if rows_exp else 0

    pending_dr = frappe.db.count("SC Dispensing Request",
        {"from_warehouse": warehouse, "docstatus": 1,
         "status": ["in", ["Approved", "Issued"]]})

    pending_tr = frappe.db.count("SC Transfer Request",
        {"from_warehouse": warehouse, "docstatus": 1,
         "status": ["in", ["Approved", "In Transit"]]})

    return {
        "warehouse": warehouse,
        "stock_qty_total": qty_total,
        "expiring_batches": int(expiring_at_wh),
        "pending_dispensing_requests": pending_dr,
        "pending_transfer_requests": pending_tr,
    }


def _resolve_period(period: str):
    today_d = getdate(today())
    if period == "today":
        return today_d, today_d
    if period == "this_week":
        return add_days(today_d, -today_d.weekday()), today_d
    if period == "this_quarter":
        q_start_month = ((today_d.month - 1) // 3) * 3 + 1
        from datetime import date
        return date(today_d.year, q_start_month, 1), today_d
    if period == "this_year":
        from datetime import date
        return date(today_d.year, 1, 1), today_d
    # default this_month
    return today_d.replace(day=1), today_d
