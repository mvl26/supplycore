"""Verify PI tạo từ PR auto-fetch đủ kho + batch + refs."""
import frappe
from frappe.utils import today


def run():
    from supplycore.m8_accounting.doctype.sc_purchase_invoice.sc_purchase_invoice import make_invoice_from_pr

    # Lấy PR đã submit, qc_status != Rejected, chưa có PI
    pr_name = frappe.db.sql("""
        SELECT pr.name FROM `tabSC Purchase Receipt` pr
        LEFT JOIN `tabSC Purchase Invoice` pi ON pi.purchase_receipt = pr.name AND pi.docstatus != 2
        WHERE pr.docstatus = 1
          AND COALESCE(pr.qc_status, '') != 'Rejected'
          AND pr.is_return = 0
          AND pi.name IS NULL
        ORDER BY pr.creation DESC LIMIT 1
    """)
    if not pr_name:
        return {"error": "No suitable PR found"}
    pr_name = pr_name[0][0]
    pr = frappe.get_doc("SC Purchase Receipt", pr_name)

    pi_name = make_invoice_from_pr(pr_name)
    pi = frappe.get_doc("SC Purchase Invoice", pi_name)

    # Check parent-level
    checks = {}
    checks["supplier"] = pi.supplier == pr.supplier
    checks["supplier_name"] = bool(pi.supplier_name)
    checks["purchase_order"] = pi.purchase_order == pr.purchase_order
    checks["purchase_receipt"] = pi.purchase_receipt == pr_name
    checks["remarks_has_warehouse"] = pr.to_warehouse in (pi.remarks or "")

    # Check item-level
    item_checks = []
    for i, (pr_row, pi_row) in enumerate(zip(pr.items, pi.items)):
        item_checks.append({
            "idx": i + 1,
            "item_match": pi_row.item == pr_row.item,
            "item_name_present": bool(pi_row.item_name),
            "warehouse_match": pi_row.warehouse == (pr_row.warehouse or pr.to_warehouse),
            "batch_match": pi_row.batch_no == pr_row.batch_no,
            "pr_item_ref_set": pi_row.pr_item_ref == pr_row.name,
            "po_item_ref_set": pi_row.po_item_ref == (pr_row.po_item_ref or None),
            "values": {
                "item": pi_row.item, "warehouse": pi_row.warehouse,
                "batch_no": pi_row.batch_no, "pr_item_ref": pi_row.pr_item_ref,
                "po_item_ref": pi_row.po_item_ref,
            },
        })

    # Cleanup
    pi.flags.ignore_permissions = True
    pi.delete()
    frappe.db.commit()

    all_parent_ok = all(checks.values())
    items_ok = all(
        ic["item_match"] and ic["item_name_present"] and ic["warehouse_match"]
        and ic["batch_match"] and ic["pr_item_ref_set"]
        for ic in item_checks
    )

    return {
        "pr_used": pr_name,
        "pi_created": pi_name,
        "parent_checks": checks,
        "parent_pass": all_parent_ok,
        "item_count": len(item_checks),
        "items": item_checks,
        "items_pass": items_ok,
        "OVERALL": all_parent_ok and items_ok,
    }
