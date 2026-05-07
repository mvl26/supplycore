"""Accounting API — supplycore.api.accounting.* (M8)."""

import frappe
from frappe import _
from frappe.utils import flt


@frappe.whitelist()
def three_way_match(purchase_invoice: str = None,
                     purchase_order: str = None,
                     pi_subtotal: float = None) -> dict:
    """Check 3-way match cho 1 PI hoặc tự build từ PO.

    Returns:
        {po_total, pr_total, pi_total, po_var_pct, pr_var_pct,
         status: Match/Mismatch/Not Applicable, variance_amount}
    """
    if purchase_invoice:
        pi = frappe.db.get_value("SC Purchase Invoice", purchase_invoice,
                                   ["purchase_order", "subtotal"], as_dict=True)
        if not pi:
            frappe.throw(_("PI {0} không tồn tại").format(purchase_invoice))
        po_name = pi.purchase_order
        pi_total = flt(pi.subtotal)
    else:
        po_name = purchase_order
        pi_total = flt(pi_subtotal or 0)

    if not po_name:
        return {"status": "Not Applicable", "po_total": 0, "pr_total": 0,
                "pi_total": pi_total, "po_var_pct": 0, "pr_var_pct": 0,
                "variance_amount": 0}

    po_total = flt(frappe.db.get_value("SC Purchase Order", po_name, "grand_total"))
    pr_total = flt(frappe.db.sql("""
        SELECT COALESCE(SUM(total_value), 0)
        FROM `tabSC Purchase Receipt`
        WHERE purchase_order = %s AND docstatus = 1 AND is_return = 0
    """, po_name)[0][0])

    po_var = abs(pi_total - po_total) / po_total * 100 if po_total else 0
    pr_var = abs(pi_total - pr_total) / pr_total * 100 if pr_total else 0
    tolerance = 1.0
    matched = po_var <= tolerance and (pr_total == 0 or pr_var <= tolerance)

    return {
        "status": "Match" if matched else "Mismatch",
        "po_total": po_total,
        "pr_total": pr_total,
        "pi_total": pi_total,
        "po_var_pct": round(po_var, 2),
        "pr_var_pct": round(pr_var, 2),
        "variance_amount": round(max(abs(pi_total - po_total), abs(pi_total - pr_total)), 2),
        "tolerance_pct": tolerance,
    }


@frappe.whitelist()
def supplier_balance(supplier: str) -> dict:
    """Số dư phải trả NCC + công nợ quá hạn."""
    from frappe.utils import today, getdate
    payable = flt(frappe.db.sql("""
        SELECT COALESCE(SUM(grand_total - paid_amount), 0)
        FROM `tabSC Purchase Invoice`
        WHERE supplier = %s AND docstatus = 1 AND status != 'Cancelled'
    """, supplier)[0][0])

    overdue = flt(frappe.db.sql("""
        SELECT COALESCE(SUM(grand_total - paid_amount), 0)
        FROM `tabSC Purchase Invoice`
        WHERE supplier = %s AND docstatus = 1 AND due_date < %s
          AND status NOT IN ('Paid', 'Cancelled')
    """, (supplier, today()))[0][0])

    credit_limit = flt(frappe.db.get_value("SC Supplier", supplier, "credit_limit") or 0)

    return {
        "supplier": supplier,
        "outstanding": payable,
        "overdue": overdue,
        "credit_limit": credit_limit,
        "limit_used_pct": round(payable / credit_limit * 100, 2) if credit_limit else None,
        "exceeds_limit": credit_limit > 0 and payable > credit_limit,
    }
