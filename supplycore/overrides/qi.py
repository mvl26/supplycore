"""Hook QI on_submit — rollup PR QC status + tự tạo Supplier Return nếu reject (M3)."""

import frappe
from frappe import _
from frappe.utils import flt, today


def release_to_stock(doc, method=None):
    """on_submit Quality Inspection:
    1) Rollup status lên Purchase Receipt (sc_qc_status)
    2) Nếu Rejected → notify NCC + tạo Purchase Return draft (BR-M3-03)
    """
    if doc.reference_type != "Purchase Receipt":
        return
    if not frappe.db.exists("Purchase Receipt", doc.reference_name):
        return

    pr = frappe.get_doc("Purchase Receipt", doc.reference_name)

    # 1. Rollup
    new_status = _compute_pr_qc_status(pr)
    if new_status != pr.get("sc_qc_status"):
        frappe.db.set_value("Purchase Receipt", pr.name, "sc_qc_status", new_status)

    # 2. Nếu QI Rejected → tự tạo draft Purchase Return + thông báo
    if doc.status == "Rejected":
        _handle_rejected(doc, pr)


def _compute_pr_qc_status(pr) -> str:
    """Rollup từ tất cả QI submitted trên PR này."""
    qis = frappe.get_all(
        "Quality Inspection",
        filters={"reference_type": "Purchase Receipt", "reference_name": pr.name},
        fields=["status", "docstatus"],
    )
    if not qis:
        return "Pending"
    submitted = [q for q in qis if q.docstatus == 1]
    if len(submitted) < len(pr.items):
        return "Pending"
    if all(q.status == "Accepted" for q in submitted):
        return "Pass"
    if all(q.status == "Rejected" for q in submitted):
        return "Fail"
    return "Partial Pass"


def _handle_rejected(qi, pr):
    """Tạo Purchase Return draft + email NCC."""
    if qi.get("sc_action_taken") != "Return to Supplier":
        # Mặc định cho Rejected
        frappe.db.set_value("Quality Inspection", qi.name, "sc_action_taken", "Return to Supplier")

    # Tránh duplicate: check đã có Return draft chưa
    existing = frappe.db.exists("Purchase Receipt", {
        "is_return": 1,
        "return_against": pr.name,
        "docstatus": ["<", 2],
    })

    return_doc_name = existing
    if not existing:
        return_doc_name = _create_purchase_return_draft(pr, qi)

    _notify_supplier_qc_rejected(pr, qi, return_doc_name)


def _create_purchase_return_draft(pr, qi):
    """Tạo Purchase Receipt với is_return=1, return_against=pr.name."""
    try:
        ret = frappe.new_doc("Purchase Receipt")
        ret.is_return = 1
        ret.return_against = pr.name
        ret.supplier = pr.supplier
        ret.posting_date = today()
        ret.set_warehouse = pr.set_warehouse

        # Chỉ trả lại item đã bị QI fail
        for row in pr.items:
            if row.item_code != qi.item_code:
                continue
            ret.append("items", {
                "item_code": row.item_code,
                "qty": -1 * flt(row.qty),  # negative cho return
                "uom": row.uom,
                "rate": row.rate,
                "warehouse": row.warehouse,
                "purchase_order": row.purchase_order,
                "purchase_receipt": pr.name,
                "purchase_receipt_item": row.name,
            })

        if not ret.items:
            return None
        ret.flags.ignore_permissions = True
        ret.insert()
        return ret.name
    except Exception as e:
        frappe.log_error(f"Create Purchase Return draft failed: {e}", "M3 _create_purchase_return_draft")
        return None


def _notify_supplier_qc_rejected(pr, qi, return_doc_name):
    """Email cho NCC + nội bộ team SK/ACCT."""
    supplier_email = frappe.db.get_value("Supplier", pr.supplier, "email_id")
    internal = frappe.db.sql_list("""
        SELECT DISTINCT u.email FROM `tabUser` u
        JOIN `tabHas Role` r ON r.parent = u.name
        WHERE r.role IN ('SupplyCore Storekeeper', 'SupplyCore Accountant', 'SupplyCore Manager')
          AND u.enabled = 1 AND u.email IS NOT NULL AND u.email != ''
    """) or []
    recipients = [e for e in (internal + ([supplier_email] if supplier_email else [])) if e]
    if not recipients:
        return

    return_link = ""
    if return_doc_name:
        return_link = f' <a href="/app/purchase-receipt/{return_doc_name}">{return_doc_name}</a>'

    msg = f"""
        <h3>SupplyCore — QC Reject thông báo NCC</h3>
        <p>Lô hàng theo Purchase Receipt <a href="/app/purchase-receipt/{pr.name}">{pr.name}</a>
           không đạt kiểm tra chất lượng.</p>
        <ul>
          <li>Item: <b>{qi.item_code}</b></li>
          <li>QC: <a href="/app/quality-inspection/{qi.name}">{qi.name}</a></li>
          <li>Lý do: {qi.get('sc_failure_reason') or qi.get('remarks') or 'Xem chi tiết QC'}</li>
          <li>Phiếu trả hàng draft:{return_link or ' (chưa tạo)'}</li>
        </ul>
        <p>Vui lòng phối hợp xác nhận đổi/hoàn hàng theo điều khoản hợp đồng.</p>
    """
    try:
        frappe.sendmail(
            recipients=recipients,
            subject=f"[SupplyCore] QC Rejected - {pr.name} / {qi.item_code}",
            message=msg,
            delayed=False,
        )
    except Exception as e:
        frappe.log_error(f"Email QC reject failed: {e}", "M3 _notify_supplier_qc_rejected")
