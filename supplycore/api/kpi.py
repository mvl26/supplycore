"""KPI Dashboard API — supplycore.api.kpi.* (M11).

Endpoint canonical theo Phase 2 API §4.5:
  GET /api/method/supplycore.api.kpi.get_executive_dashboard

UC-32 extensions:
  - filter by warehouse + department
  - 5-minute cache (TTL 300s)
  - drill-down URLs per KPI
  - monthly cost trend
  - role-aware dashboard
  - PDF snapshot data
  - contract-expiring + PO-overdue KPIs
"""

import frappe
from frappe import _
from frappe.utils import flt, today, add_days, add_months, getdate, now

from supplycore.utils.permissions import block_portal


CACHE_TTL = 300  # 5 minutes
VALID_PERIODS = {"today", "this_week", "this_month", "this_quarter", "this_year"}

ROLE_WIDGETS = {
    "SupplyCore Executive": [
        "stock_value", "monthly_cost", "ap_outstanding", "pending_pos",
        "expiring_soon", "low_stock_items", "contract_expiring_30d", "po_overdue_count",
    ],
    "SupplyCore Manager": [
        "stock_value", "monthly_cost", "pending_pos",
        "expiring_soon", "low_stock_items", "contract_expiring_30d", "po_overdue_count",
    ],
    "SupplyCore Accountant": [
        "monthly_cost", "ap_outstanding", "pending_pos",
    ],
    "SupplyCore Storekeeper": [
        "stock_value", "expiring_soon", "low_stock_items",
    ],
}


# -----------------------------------------------------------------------
# UC-32: helper — cache
# -----------------------------------------------------------------------
def _cache_key(scope, params):
    parts = [str(scope)] + [f"{k}={v}" for k, v in sorted(params.items()) if v]
    return "uc32:" + ":".join(parts)


def _cache_get(key):
    val = frappe.cache().get_value(key)
    if val is not None:
        val["cached"] = True
    return val


def _cache_set(key, value):
    value["cached"] = False
    try:
        frappe.cache().set_value(key, value, expires_in_sec=CACHE_TTL)
    except Exception:
        pass
    return value


def _warehouses_for_department(department: str) -> list:
    """UC-32 filter dept: trả về list warehouse trực thuộc department.
    SC Warehouse.department là Link → SC Department. Đệ quy con của warehouse cha
    để bao gồm cả sub-warehouse nếu phân cấp 3 tầng.
    """
    if not department:
        return []
    direct = frappe.db.get_all("SC Warehouse",
        filters={"department": department, "disabled": 0},
        pluck="name") or []
    # Bao gồm con của các kho khoa (kho con kế thừa dept của parent)
    if not direct:
        return []
    all_whs = set(direct)
    pending = list(direct)
    while pending:
        children = frappe.db.get_all("SC Warehouse",
            filters={"parent_warehouse": ["in", pending], "disabled": 0},
            pluck="name") or []
        new_children = [c for c in children if c not in all_whs]
        all_whs.update(new_children)
        pending = new_children
    return list(all_whs)


# -----------------------------------------------------------------------
# UC-32 main: executive dashboard (extended)
# -----------------------------------------------------------------------
@frappe.whitelist()
def get_executive_dashboard(period: str = "this_month",
                             warehouse=None, department=None,
                             force_refresh: int = 0) -> dict:
    """6+2 KPIs theo SCR-01 + UC-32:
       Existing: stock_value, monthly_cost, ap_outstanding, pending_pos,
                  expiring_soon, low_stock_items
       Added: contract_expiring_30d, po_overdue_count
       Plus: drill_down URLs, last_updated_at, cached flag.
    """
    block_portal()
    if period not in VALID_PERIODS:
        frappe.throw(_(
            "SC-E-DSH-INVALID-PERIOD: period phải thuộc {0}"
        ).format(sorted(VALID_PERIODS)))
    if warehouse and not frappe.db.exists("SC Warehouse", warehouse):
        frappe.throw(_(
            "SC-E-DSH-INVALID-WAREHOUSE: Warehouse {0} không tồn tại"
        ).format(warehouse))

    key = _cache_key("exec", {"p": period, "wh": warehouse, "d": department})
    if not int(force_refresh or 0):
        cached = _cache_get(key)
        if cached:
            return cached

    from_date, to_date = _resolve_period(period)

    # UC-32: derive warehouse list từ department filter (nếu có)
    dept_whs = _warehouses_for_department(department) if department else []
    if department and not dept_whs:
        # Department tồn tại nhưng không có kho → KPIs stock-related = 0
        pass
    effective_whs = None
    if warehouse and dept_whs:
        # Cả 2: warehouse phải nằm trong dept_whs
        effective_whs = [warehouse] if warehouse in dept_whs else []
    elif warehouse:
        effective_whs = [warehouse]
    elif dept_whs:
        effective_whs = dept_whs

    # ---- 1. Stock value: SUM(qty × valuation_rate) hiện tại ----
    if effective_whs is not None:
        if not effective_whs:
            stock_value = 0.0
        else:
            stock_value = flt(frappe.db.sql("""
                SELECT COALESCE(SUM(qty_change * valuation_rate), 0)
                FROM `tabSC Stock Ledger Entry`
                WHERE is_cancelled = 0 AND warehouse IN %(whs)s
            """, {"whs": tuple(effective_whs)})[0][0])
    else:
        stock_value = flt(frappe.db.sql("""
            SELECT COALESCE(SUM(qty_change * valuation_rate), 0)
            FROM `tabSC Stock Ledger Entry`
            WHERE is_cancelled = 0
        """)[0][0])

    # ---- 2. Monthly cost: SUM PI grand_total trong period ----
    monthly_cost = flt(frappe.db.sql("""
        SELECT COALESCE(SUM(grand_total), 0)
        FROM `tabSC Purchase Invoice`
        WHERE invoice_date BETWEEN %s AND %s AND docstatus = 1
    """, (from_date, to_date))[0][0])

    # ---- 3. AP outstanding: tổng PI còn phải trả ----
    ap_outstanding = flt(frappe.db.sql("""
        SELECT COALESCE(SUM(outstanding_amount), 0)
        FROM `tabSC Purchase Invoice`
        WHERE docstatus = 1 AND status != 'Cancelled'
    """)[0][0])

    # ---- 4. Pending POs ----
    pending_pos = frappe.db.count("SC Purchase Order",
        {"docstatus": 1, "status": ["in",
            ["Approved", "Sent to Supplier", "Partially Received"]]})

    # ---- 5. Expiring soon ≤30 days ----
    if effective_whs is not None:
        if not effective_whs:
            expiring_soon = 0
        else:
            expiring_soon = flt(frappe.db.sql("""
                SELECT COUNT(DISTINCT b.name)
                FROM `tabSC Batch` b
                WHERE b.disabled = 0 AND b.blocked = 0
                  AND b.expiry_date IS NOT NULL
                  AND b.expiry_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 30 DAY)
                  AND EXISTS (
                      SELECT 1 FROM `tabSC Stock Ledger Entry` sle
                      WHERE sle.batch = b.name AND sle.is_cancelled = 0
                        AND sle.warehouse IN %(whs)s
                      GROUP BY sle.batch
                      HAVING SUM(sle.qty_change) > 0
                  )
            """, {"whs": tuple(effective_whs)})[0][0])
    else:
        expiring_soon = flt(frappe.db.sql("""
            SELECT COUNT(DISTINCT b.name)
            FROM `tabSC Batch` b
            WHERE b.disabled = 0 AND b.blocked = 0
              AND b.expiry_date IS NOT NULL
              AND b.expiry_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 30 DAY)
              AND EXISTS (
                  SELECT 1 FROM `tabSC Stock Ledger Entry` sle
                  WHERE sle.batch = b.name AND sle.is_cancelled = 0
                  GROUP BY sle.batch
                  HAVING SUM(sle.qty_change) > 0
              )
        """)[0][0])

    # ---- 6. Low stock items ----
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

    # ---- 7. UC-32: Contract expiring trong 30d ----
    contract_expiring_30d = flt(frappe.db.sql("""
        SELECT COUNT(*) FROM `tabFramework Contract`
        WHERE status = 'Active'
          AND valid_to IS NOT NULL
          AND valid_to BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 30 DAY)
    """)[0][0])

    # ---- 8. UC-32: PO overdue (schedule_date < today, not fully received) ----
    po_overdue_count = flt(frappe.db.sql("""
        SELECT COUNT(*) FROM `tabSC Purchase Order`
        WHERE docstatus = 1
          AND status IN ('Approved', 'Sent to Supplier', 'Partially Received')
          AND schedule_date IS NOT NULL
          AND schedule_date < CURDATE()
    """)[0][0])

    # ---- Top 10 items by consumption value ----
    if effective_whs is not None:
        if not effective_whs:
            top_items = []
        else:
            top_items = frappe.db.sql("""
                SELECT sle.item AS item_code, i.item_name,
                       SUM(ABS(sle.qty_change)) AS qty_used,
                       SUM(ABS(sle.qty_change) * sle.valuation_rate) AS cost
                FROM `tabSC Stock Ledger Entry` sle
                JOIN `tabSC Item` i ON i.name = sle.item
                WHERE sle.qty_change < 0 AND sle.is_cancelled = 0
                  AND sle.posting_date BETWEEN %(start)s AND %(end)s
                  AND sle.warehouse IN %(whs)s
                GROUP BY sle.item
                ORDER BY cost DESC LIMIT 10
            """, {"start": from_date, "end": to_date,
                  "whs": tuple(effective_whs)}, as_dict=True)
    else:
        top_items = frappe.db.sql("""
            SELECT sle.item AS item_code, i.item_name,
                   SUM(ABS(sle.qty_change)) AS qty_used,
                   SUM(ABS(sle.qty_change) * sle.valuation_rate) AS cost
            FROM `tabSC Stock Ledger Entry` sle
            JOIN `tabSC Item` i ON i.name = sle.item
            WHERE sle.qty_change < 0 AND sle.is_cancelled = 0
              AND sle.posting_date BETWEEN %(start)s AND %(end)s
            GROUP BY sle.item
            ORDER BY cost DESC LIMIT 10
        """, {"start": from_date, "end": to_date}, as_dict=True)

    # ---- Outstanding alerts ----
    open_alerts = frappe.db.sql("""
        SELECT severity, COUNT(*) AS count
        FROM `tabSC Alert`
        WHERE resolved = 0
          AND (snooze_until IS NULL OR snooze_until < NOW())
        GROUP BY severity
    """, as_dict=True)
    alert_breakdown = {a.severity: int(a.count) for a in open_alerts}

    payload = {
        "period": {"from": str(from_date), "to": str(to_date), "label": period},
        "filters": {"warehouse": warehouse, "department": department},
        "kpis": {
            "stock_value": flt(stock_value),
            "monthly_cost": flt(monthly_cost),
            "ap_outstanding": flt(ap_outstanding),
            "pending_pos": int(pending_pos),
            "expiring_soon": int(expiring_soon),
            "low_stock_items": int(low_stock),
            "contract_expiring_30d": int(contract_expiring_30d),
            "po_overdue_count": int(po_overdue_count),
        },
        "top_items": [{**r, "qty_used": flt(r["qty_used"]), "cost": flt(r["cost"])}
                       for r in top_items],
        "open_alerts": alert_breakdown,
        "open_alerts_total": sum(alert_breakdown.values()),
        "drill_down": _drill_down_urls(),
        "last_updated_at": now(),
    }
    return _cache_set(key, payload)


def _drill_down_urls():
    """UC-32 step 5: URL drill-down cho mỗi KPI key."""
    return {
        "stock_value": "/app/sc-stock-ledger-entry?is_cancelled=0",
        "monthly_cost": "/app/sc-purchase-invoice?docstatus=1",
        "ap_outstanding": "/app/sc-purchase-invoice?docstatus=1&outstanding_amount=>0",
        "pending_pos": "/app/sc-purchase-order?docstatus=1&status=[%22in%22,%5B%22Approved%22,%22Sent%20to%20Supplier%22,%22Partially%20Received%22%5D]",
        "expiring_soon": "/app/sc-batch?expiry_date=<=30d",
        "low_stock_items": "/app/sc-item?safety_stock=>0",
        "contract_expiring_30d": "/app/framework-contract?status=Active&valid_to=<=30d",
        "po_overdue_count": "/app/sc-purchase-order?docstatus=1&schedule_date=<today",
        "open_alerts": "/app/sc-alert?resolved=0",
    }


# -----------------------------------------------------------------------
# UC-32 step 3b: monthly cost trend
# -----------------------------------------------------------------------
@frappe.whitelist()
def get_monthly_cost_trend(months: int = 12) -> list:
    """Trả 12 tháng gần nhất với chi phí PI submitted."""
    block_portal()
    months = max(1, min(int(months), 36))
    rows = frappe.db.sql("""
        SELECT DATE_FORMAT(invoice_date, '%%Y-%%m') AS month,
               COALESCE(SUM(grand_total), 0) AS cost,
               COUNT(*) AS invoice_count
        FROM `tabSC Purchase Invoice`
        WHERE docstatus = 1
          AND invoice_date >= DATE_SUB(CURDATE(), INTERVAL %s MONTH)
        GROUP BY DATE_FORMAT(invoice_date, '%%Y-%%m')
        ORDER BY month ASC
    """, months, as_dict=True)
    return [{"month": r["month"], "cost": flt(r["cost"]),
              "invoice_count": int(r["invoice_count"])} for r in rows]


# -----------------------------------------------------------------------
# UC-32 step 1a: role-aware
# -----------------------------------------------------------------------
@frappe.whitelist()
def get_dashboard_for_role(role: str = None, period: str = "this_month",
                            warehouse=None) -> dict:
    """Trả dashboard tailored cho role.
    Nếu role không truyền → dùng role chính của session user."""
    block_portal()
    if not role:
        user_roles = set(frappe.get_roles(frappe.session.user))
        for r in ("SupplyCore Executive", "SupplyCore Manager",
                   "SupplyCore Accountant", "SupplyCore Storekeeper"):
            if r in user_roles:
                role = r
                break
    if not role or role not in ROLE_WIDGETS:
        # Default minimal view
        role = "SupplyCore Manager"

    full = get_executive_dashboard(period=period, warehouse=warehouse)
    widgets = ROLE_WIDGETS[role]
    filtered_kpis = {k: v for k, v in full["kpis"].items() if k in widgets}

    return {
        "role": role,
        "widgets_enabled": widgets,
        "period": full["period"],
        "filters": full["filters"],
        "kpis": filtered_kpis,
        "top_items": full["top_items"] if role in (
            "SupplyCore Executive", "SupplyCore Manager") else [],
        "open_alerts": full["open_alerts"],
        "open_alerts_total": full["open_alerts_total"],
        "drill_down": {k: v for k, v in full["drill_down"].items() if k in widgets},
        "last_updated_at": full["last_updated_at"],
        "cached": full.get("cached", False),
    }


# -----------------------------------------------------------------------
# UC-32 step 6a: PDF snapshot data
# -----------------------------------------------------------------------
@frappe.whitelist()
def get_dashboard_snapshot_pdf_data(period: str = "this_month",
                                      warehouse=None) -> dict:
    """Data cho Frappe Print Format dashboard snapshot."""
    block_portal()
    full = get_executive_dashboard(period=period, warehouse=warehouse,
                                     force_refresh=1)
    trend = get_monthly_cost_trend(months=12)
    return {
        "title": "SupplyCore — Dashboard Snapshot",
        "generated_at": now(),
        "generated_by": frappe.session.user,
        "period": full["period"],
        "filters": full["filters"],
        "kpis": full["kpis"],
        "top_items": full["top_items"],
        "monthly_trend": trend,
        "open_alerts": full["open_alerts"],
        "open_alerts_total": full["open_alerts_total"],
        "signatures": {
            "executive": "_____________________",
            "manager": "_____________________",
            "accountant": "_____________________",
        },
    }


# -----------------------------------------------------------------------
# Existing: warehouse dashboard (unchanged)
# -----------------------------------------------------------------------
@frappe.whitelist()
def get_warehouse_dashboard(warehouse: str) -> dict:
    """KPI cho SK theo warehouse cụ thể."""
    block_portal()
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

    pending_tr = frappe.db.count("SC Transfer Request",
        {"from_warehouse": warehouse, "docstatus": 1,
         "status": ["in", ["Approved", "In Transit"]]})

    return {
        "warehouse": warehouse,
        "stock_qty_total": qty_total,
        "expiring_batches": int(expiring_at_wh),
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
