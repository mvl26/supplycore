"""UC-26 Financial Reports: 4 báo cáo + drill-down + finalization check."""

import frappe
from frappe.utils import flt, today, getdate


@frappe.whitelist()
def inventory_value_report(warehouse: str = None, item_group: str = None,
                            as_of_date: str = None, limit: int = 500) -> dict:
    """Tồn kho giá trị: aggregate SLE per (item, warehouse, batch).

    Returns: {rows: [...], total_qty, total_value, period_finalized}
    """
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
    """
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


@frappe.whitelist()
def period_cost_report(from_date: str, to_date: str,
                       item_group: str = None,
                       warehouse: str = None) -> dict:
    """Chi phí vật tư kỳ: PI grand_total + breakdown per item_group."""
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
