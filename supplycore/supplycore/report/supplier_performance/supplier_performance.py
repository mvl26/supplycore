"""Supplier Performance — báo cáo đánh giá NCC (UC-01).

Frappe Script Report: hỗ trợ filter + export Excel/CSV/PDF builtin.

Filters: supplier (optional), supplier_type, province, default_item_group,
         from_date / to_date (default: 12 tháng gần nhất)
"""

import frappe
from frappe import _
from frappe.utils import flt, today, add_months


def execute(filters=None):
    filters = frappe._dict(filters or {})
    columns = _get_columns()
    data = _get_data(filters)
    return columns, data


def _get_columns():
    return [
        {"fieldname": "supplier",        "label": _("Mã NCC"),
         "fieldtype": "Link", "options": "SC Supplier", "width": 130},
        {"fieldname": "supplier_name",   "label": _("Tên NCC"),
         "fieldtype": "Data", "width": 220},
        {"fieldname": "supplier_type",   "label": _("Loại"),
         "fieldtype": "Data", "width": 110},
        {"fieldname": "province",        "label": _("Tỉnh/TP"),
         "fieldtype": "Data", "width": 110},
        {"fieldname": "rating",          "label": _("Rating ★"),
         "fieldtype": "Float", "precision": 2, "width": 90},
        {"fieldname": "active_contracts","label": _("HĐ Active"),
         "fieldtype": "Int", "width": 90},
        {"fieldname": "fc_remaining",    "label": _("HĐ còn lại"),
         "fieldtype": "Currency", "options": "VND", "width": 130},
        {"fieldname": "total_pos",       "label": _("PO 12t"),
         "fieldtype": "Int", "width": 80},
        {"fieldname": "total_value",     "label": _("Giá trị PO"),
         "fieldtype": "Currency", "options": "VND", "width": 140},
        {"fieldname": "on_time_pct",     "label": _("On-time %"),
         "fieldtype": "Float", "precision": 2, "width": 100},
        {"fieldname": "qc_pass_pct",     "label": _("QC Pass %"),
         "fieldtype": "Float", "precision": 2, "width": 100},
        {"fieldname": "ap_outstanding",  "label": _("Công nợ"),
         "fieldtype": "Currency", "options": "VND", "width": 130},
        {"fieldname": "blacklist_flag",  "label": _("Blacklist"),
         "fieldtype": "Check", "width": 80},
        {"fieldname": "gpp_expiry",      "label": _("Hết hạn GPP"),
         "fieldtype": "Date", "width": 110},
    ]


def _get_data(filters):
    sup_filters = {"disabled": 0}
    if filters.get("supplier"):
        sup_filters["name"] = filters["supplier"]
    if filters.get("supplier_type"):
        sup_filters["supplier_type"] = filters["supplier_type"]
    if filters.get("province"):
        sup_filters["province"] = filters["province"]
    if filters.get("default_item_group"):
        sup_filters["default_item_group"] = filters["default_item_group"]

    suppliers = frappe.get_all("SC Supplier",
        filters=sup_filters,
        fields=["name", "supplier_name", "supplier_type", "province",
                 "rating", "blacklist_flag", "gpp_expiry"])

    cutoff = filters.get("from_date") or add_months(today(), -12)
    to_date = filters.get("to_date") or today()

    rows = []
    for s in suppliers:
        rows.append(_build_row(s, cutoff, to_date))
    # Sort: rating desc, then on_time_pct desc
    rows.sort(key=lambda r: (-(r["rating"] or 0), -(r.get("on_time_pct") or 0)))
    return rows


def _build_row(s: dict, cutoff: str, to_date: str) -> dict:
    sup = s["name"]

    fc = frappe.db.sql("""
        SELECT COUNT(*) AS c, COALESCE(SUM(remaining_value), 0) AS rv
        FROM `tabFramework Contract`
        WHERE supplier = %s AND docstatus = 1 AND status = 'Active'
    """, sup, as_dict=True)[0]

    po = frappe.db.sql("""
        SELECT COUNT(*) AS c, COALESCE(SUM(grand_total), 0) AS gt
        FROM `tabSC Purchase Order`
        WHERE supplier = %s AND docstatus = 1 AND transaction_date BETWEEN %s AND %s
    """, (sup, cutoff, to_date), as_dict=True)[0]

    on_time = frappe.db.sql("""
        SELECT
          SUM(CASE WHEN pr.posting_date <= po.schedule_date THEN 1 ELSE 0 END) AS on_time,
          COUNT(*) AS total
        FROM `tabSC Purchase Receipt` pr
        JOIN `tabSC Purchase Order` po ON po.name = pr.purchase_order
        WHERE pr.supplier = %s AND pr.docstatus = 1 AND pr.is_return = 0
          AND po.docstatus = 1 AND pr.posting_date BETWEEN %s AND %s
    """, (sup, cutoff, to_date), as_dict=True)[0]
    on_time_pct = (round(flt(on_time.on_time) / flt(on_time.total) * 100, 2)
                    if on_time.total else None)

    qc = frappe.db.sql("""
        SELECT
          SUM(CASE WHEN qi.overall_status = 'Accepted' THEN 1 ELSE 0 END) AS pass_,
          COUNT(*) AS total
        FROM `tabSC Quality Inspection` qi
        JOIN `tabSC Purchase Receipt` pr ON pr.name = qi.purchase_receipt
        WHERE pr.supplier = %s AND qi.docstatus = 1
          AND qi.inspection_date BETWEEN %s AND %s
    """, (sup, cutoff, to_date), as_dict=True)[0]
    qc_pass_pct = (round(flt(qc.pass_) / flt(qc.total) * 100, 2)
                    if qc.total else None)

    ap = flt(frappe.db.sql("""
        SELECT COALESCE(SUM(outstanding_amount), 0)
        FROM `tabSC Purchase Invoice`
        WHERE supplier = %s AND docstatus = 1 AND status NOT IN ('Paid', 'Cancelled')
    """, sup)[0][0])

    return {
        "supplier": sup,
        "supplier_name": s["supplier_name"],
        "supplier_type": s.get("supplier_type"),
        "province": s.get("province"),
        "rating": flt(s.get("rating") or 0),
        "active_contracts": int(fc.c or 0),
        "fc_remaining": flt(fc.rv or 0),
        "total_pos": int(po.c or 0),
        "total_value": flt(po.gt or 0),
        "on_time_pct": on_time_pct,
        "qc_pass_pct": qc_pass_pct,
        "ap_outstanding": ap,
        "blacklist_flag": int(s.get("blacklist_flag") or 0),
        "gpp_expiry": s.get("gpp_expiry"),
    }
