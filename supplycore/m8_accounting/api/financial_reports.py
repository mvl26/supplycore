"""UC-26 Financial Reports: 4 báo cáo + drill-down + finalization check."""

import frappe
from frappe.utils import flt, today, getdate

from supplycore.utils.permissions import block_portal


@frappe.whitelist()
def inventory_value_report(warehouse: str = None, item_group: str = None,
                            as_of_date: str = None, limit: int = 500) -> dict:
    """Tồn kho giá trị: aggregate SLE per (item, warehouse, batch).

    Returns: {rows: [...], total_qty, total_value, period_finalized}
    """
    block_portal()
    where = ["sle.is_cancelled = 0"]
    params = {"lim": int(limit)}
    if warehouse:
        where.append("sle.warehouse = %(wh)s"); params["wh"] = warehouse
    if item_group:
        where.append("i.item_group = %(ig)s"); params["ig"] = item_group
    if as_of_date:
        where.append("sle.posting_date <= %(asof)s"); params["asof"] = as_of_date

    sql = f"""
        SELECT sle.item, i.item_name, i.item_group, i.uom,
               sle.warehouse, sle.batch,
               SUM(sle.qty_change) AS qty,
               AVG(CASE WHEN sle.qty_change > 0 THEN sle.valuation_rate ELSE NULL END) AS avg_rate,
               SUM(sle.qty_change) * COALESCE(
                   AVG(CASE WHEN sle.qty_change > 0 THEN sle.valuation_rate ELSE NULL END), 0
               ) AS value
        FROM `tabSC Stock Ledger Entry` sle
        JOIN `tabSC Item` i ON i.name = sle.item
        WHERE {' AND '.join(where)}
        GROUP BY sle.item, sle.warehouse, sle.batch
        HAVING qty > 0
        ORDER BY i.item_name LIMIT %(lim)s
    """
    rows = frappe.db.sql(sql, params, as_dict=True)
    total_qty = sum(flt(r["qty"]) for r in rows)
    total_value = sum(flt(r["value"]) for r in rows)
    fin = check_period_finalized(today(), as_of_date or today())
    return {
        "rows": rows,
        "total_qty": total_qty,
        "total_value": total_value,
        "period_finalized": fin["finalized"],
        "pending_drafts": fin["pending"],
    }


@frappe.whitelist()
def ap_aging_report(supplier: str = None, as_of_date: str = None,
                     limit: int = 500) -> dict:
    """Công nợ NCC aging: bucket theo (today - due_date).

    Buckets: current (≤0), 0-30, 31-60, 61-90, >90

    Role-gate (GĐ4 Task 5): mirror `ar_aging_by_customer` -- chỉ System
    Manager/SupplyCore Manager/Executive/Accountant/Auditor mới được xem
    công nợ NCC. Trước fix: hàm này KHÔNG gate gì -- bất kỳ user đăng nhập
    nào (kể cả role Portal) gọi thẳng API đều đọc được toàn bộ payables.
    """
    _require_finance_report_role()
    asof = as_of_date or today()
    where = ["docstatus = 1", "outstanding_amount > 0", "status != 'Cancelled'"]
    params = {"asof": asof, "lim": int(limit)}
    if supplier:
        where.append("supplier = %(supp)s"); params["supp"] = supplier

    sql = f"""
        SELECT name, supplier, supplier_name, supplier_invoice_no,
               invoice_date, due_date, grand_total, paid_amount,
               outstanding_amount,
               DATEDIFF(%(asof)s, due_date) AS days_overdue
        FROM `tabSC Purchase Invoice`
        WHERE {' AND '.join(where)}
        ORDER BY supplier, due_date ASC LIMIT %(lim)s
    """
    rows = frappe.db.sql(sql, params, as_dict=True)

    buckets = {"current": 0, "0_30": 0, "31_60": 0, "61_90": 0, "over_90": 0}
    for r in rows:
        d = r.get("days_overdue") or 0
        amt = flt(r["outstanding_amount"])
        if d <= 0:
            r["bucket"] = "current"; buckets["current"] += amt
        elif d <= 30:
            r["bucket"] = "0_30"; buckets["0_30"] += amt
        elif d <= 60:
            r["bucket"] = "31_60"; buckets["31_60"] += amt
        elif d <= 90:
            r["bucket"] = "61_90"; buckets["61_90"] += amt
        else:
            r["bucket"] = "over_90"; buckets["over_90"] += amt

    return {
        "rows": rows,
        "buckets": buckets,
        "total_outstanding": sum(buckets.values()),
        "as_of_date": str(asof),
    }


# GĐ4 Task 5 (security sweep) -- gate chung cho báo cáo tài chính nội bộ
# (AP/AR aging): chỉ Kế toán/Quản lý/Kiểm toán/Executive được xem. Data tổng
# hợp toàn hệ thống (công nợ NCC, công nợ khách + credit_limit — BRU-AR-001)
# KHÔNG được lộ qua Portal hay bất kỳ role vận hành khác (Storekeeper,
# Purchaser...). Dùng allow-list (không phải block_portal) vì đây là báo cáo
# tài chính nhạy cảm -- chỉ role tài chính/quản lý cụ thể mới được gọi, kể cả
# nội bộ.
FINANCE_REPORT_ROLES = (
    "System Manager", "SupplyCore Manager", "SupplyCore Executive",
    "SupplyCore Accountant", "SupplyCore Auditor",
)


def _require_finance_report_role():
    user_roles = set(frappe.get_roles(frappe.session.user))
    if not user_roles.intersection(FINANCE_REPORT_ROLES):
        frappe.throw(frappe._("Không có quyền xem báo cáo tài chính này"),
                      frappe.PermissionError)


@frappe.whitelist()
def ar_aging_by_customer(customer: str = None, as_of_date: str = None,
                          limit: int = 500) -> dict:
    """Cong no phai thu theo khach hang: bucket theo (today - invoice_date),
    canh bao vuot credit_limit (BRU-AR-001).

    Buckets: 0-30, 31-60, 61-90, >90 (tinh tu invoice_date, SC Sales Invoice
    khong co due_date rieng nhu SC Purchase Invoice).

    Role-gate: chi System Manager/SupplyCore Manager/Executive/Accountant/
    Auditor -- role Portal (SC Customer Portal) hay cac role noi bo khac
    (Storekeeper/Purchaser...) KHONG duoc goi.
    """
    _require_finance_report_role()

    asof = as_of_date or today()
    where = ["si.docstatus = 1", "si.outstanding_amount > 0", "si.status != 'Hủy'"]
    params = {"asof": asof, "lim": int(limit)}
    if customer:
        where.append("si.customer = %(cust)s"); params["cust"] = customer

    sql = f"""
        SELECT si.customer, c.customer_name, c.credit_limit,
               si.name, si.invoice_date, si.outstanding_amount,
               DATEDIFF(%(asof)s, si.invoice_date) AS age_days
        FROM `tabSC Sales Invoice` si
        JOIN `tabSC Customer` c ON c.name = si.customer
        WHERE {' AND '.join(where)}
        ORDER BY si.customer, si.invoice_date ASC LIMIT %(lim)s
    """
    invoice_rows = frappe.db.sql(sql, params, as_dict=True)

    by_customer: dict[str, dict] = {}
    for r in invoice_rows:
        entry = by_customer.setdefault(r["customer"], {
            "customer": r["customer"],
            "customer_name": r["customer_name"],
            "credit_limit": flt(r["credit_limit"]),
            "total_outstanding": 0.0,
            "buckets": {"0_30": 0.0, "31_60": 0.0, "61_90": 0.0, "over_90": 0.0},
        })
        age = r.get("age_days") or 0
        amt = flt(r["outstanding_amount"])
        if age <= 30:
            bucket = "0_30"
        elif age <= 60:
            bucket = "31_60"
        elif age <= 90:
            bucket = "61_90"
        else:
            bucket = "over_90"
        entry["buckets"][bucket] += amt
        entry["total_outstanding"] += amt

    rows = list(by_customer.values())
    for entry in rows:
        entry["over_limit"] = bool(entry["credit_limit"] and
                                    entry["total_outstanding"] > entry["credit_limit"])
    rows.sort(key=lambda r: r["total_outstanding"], reverse=True)

    return {
        "rows": rows,
        "as_of_date": str(asof),
        "total_outstanding": sum(r["total_outstanding"] for r in rows),
    }


@frappe.whitelist()
def period_cost_report(from_date: str, to_date: str,
                       item_group: str = None,
                       warehouse: str = None) -> dict:
    """Chi phí vật tư kỳ: PI grand_total + breakdown per item_group."""
    block_portal()
    if not (from_date and to_date):
        frappe.throw("from_date và to_date bắt buộc")

    # Total cost
    total = flt(frappe.db.sql("""
        SELECT COALESCE(SUM(grand_total), 0)
        FROM `tabSC Purchase Invoice`
        WHERE invoice_date BETWEEN %s AND %s
          AND docstatus = 1 AND status != 'Cancelled'
    """, (from_date, to_date))[0][0])

    # Breakdown by item_group via PI Item
    where = ["pi.invoice_date BETWEEN %(fd)s AND %(td)s",
             "pi.docstatus = 1", "pi.status != 'Cancelled'"]
    params = {"fd": from_date, "td": to_date}
    if item_group:
        where.append("i.item_group = %(ig)s"); params["ig"] = item_group

    breakdown = frappe.db.sql(f"""
        SELECT i.item_group, COUNT(DISTINCT pi.name) AS pi_count,
               SUM(pii.qty) AS total_qty,
               SUM(pii.amount) AS subtotal
        FROM `tabSC PI Item` pii
        JOIN `tabSC Purchase Invoice` pi ON pi.name = pii.parent
        JOIN `tabSC Item` i ON i.name = pii.item
        WHERE {' AND '.join(where)}
        GROUP BY i.item_group
        ORDER BY subtotal DESC
    """, params, as_dict=True)

    fin = check_period_finalized(from_date, to_date)
    return {
        "from_date": from_date,
        "to_date": to_date,
        "total_cost": total,
        "by_item_group": breakdown,
        "period_finalized": fin["finalized"],
        "pending_drafts": fin["pending"],
    }


@frappe.whitelist()
def get_voucher_details(voucher_type: str, voucher_no: str) -> dict:
    """UC-26 5a drill-down: header + items + linked vouchers."""
    block_portal()
    if not frappe.db.exists(voucher_type, voucher_no):
        return {"exists": False}
    doc = frappe.get_doc(voucher_type, voucher_no)
    header = {}
    for fld in doc.meta.fields:
        if fld.fieldtype in ("Table", "Section Break", "Column Break", "Tab Break"):
            continue
        header[fld.fieldname] = doc.get(fld.fieldname)
    data = {
        "doctype": voucher_type,
        "name": voucher_no,
        "exists": True,
        "header": header,
    }
    # Items child tables
    items = []
    for fld in doc.meta.get_table_fields():
        items_list = doc.get(fld.fieldname) or []
        items.append({
            "table": fld.fieldname,
            "options": fld.options,
            "rows": [{k: r.get(k) for k in r.as_dict().keys()
                      if not k.startswith("__")} for r in items_list],
        })
    data["items"] = items
    return data


@frappe.whitelist()
def check_period_finalized(from_date: str, to_date: str) -> dict:
    """UC-26 ngoại lệ: check có Draft document trong kỳ → chưa finalized."""
    block_portal()
    pending_pi = frappe.db.count("SC Purchase Invoice", {
        "docstatus": 0,
        "invoice_date": ["between", [from_date, to_date]],
    })
    pending_pe = frappe.db.count("SC Payment Entry", {
        "docstatus": 0,
        "payment_date": ["between", [from_date, to_date]],
    })
    total = pending_pi + pending_pe
    return {
        "finalized": total == 0,
        "pending": {
            "purchase_invoice": pending_pi,
            "payment_entry": pending_pe,
            "total": total,
        },
    }
