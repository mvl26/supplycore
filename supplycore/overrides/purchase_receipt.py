"""Hook lifecycle vào ERPNext Purchase Receipt — M3 Tiếp nhận & QC."""

import frappe
from frappe import _
from frappe.utils import flt, getdate, today, date_diff


# ---------------------------------------------------------------------------
# auto_create_qc — after_insert
# ---------------------------------------------------------------------------
def auto_create_qc(doc, method=None):
    """Sau khi tạo PR draft, tự sinh Quality Inspection draft cho từng item.

    BR-M3-01: mọi lô nhập kho PHẢI đi qua QC bắt buộc.
    Nếu sc_qc_required = 0, bỏ qua (cho non-medical items).
    """
    if doc.get("is_return"):
        return  # Phiếu trả NCC không cần QC
    if not doc.get("sc_qc_required", 1):
        return

    for row in doc.items:
        # Đã có QI cho item này? Skip
        existing = frappe.db.exists("Quality Inspection", {
            "reference_type": "Purchase Receipt",
            "reference_name": doc.name,
            "item_code": row.item_code,
        })
        if existing:
            continue

        # SupplyCore enforce QC cho mọi item nhập (BR-M3-01).
        # Auto-enable inspection_required_before_purchase nếu chưa bật.
        if not frappe.db.get_value("Item", row.item_code, "inspection_required_before_purchase"):
            frappe.db.set_value("Item", row.item_code, "inspection_required_before_purchase", 1)

        template_name = _find_checklist_template(row.item_code)

        qi = frappe.new_doc("Quality Inspection")
        qi.inspection_type = "Incoming"
        qi.reference_type = "Purchase Receipt"
        qi.reference_name = doc.name
        qi.item_code = row.item_code
        qi.sample_size = 1
        qi.received_qty = row.qty
        qi.batch_no = row.get("batch_no")
        qi.sc_checklist_template = template_name
        qi.manual_inspection = 1  # Bỏ qua auto-status logic của ERPNext, dùng UI checklist
        # ERPNext QI requires inspected_by (Link User) — fallback Administrator nếu session=Guest
        qi.inspected_by = frappe.session.user if frappe.session.user not in (None, "", "Guest") else "Administrator"

        # Populate readings từ template criteria
        if template_name:
            template = frappe.get_doc("QC Checklist Template", template_name)
            for crit in sorted(template.criteria, key=lambda c: c.sequence or 0):
                qi.append("readings", {
                    "specification": crit.criterion_name,
                    "manual_inspection": 1,  # User tự set status, ERPNext không auto-flip
                    "numeric": 0,
                    "status": "",
                })

        try:
            qi.insert(ignore_permissions=True)
        except Exception as e:
            # log_error: title max 140 chars
            frappe.log_error(message=f"Auto-create QI failed for PR={doc.name} item={row.item_code}: {e}",
                             title="M3 auto_create_qc")

    # Set initial QC status
    frappe.db.set_value("Purchase Receipt", doc.name, "sc_qc_status", "Pending")


# ---------------------------------------------------------------------------
# validate — kiểm tra qty tolerance + expiry
# ---------------------------------------------------------------------------
def validate_against_contract(doc, method=None):
    """validate: tolerance qty PR vs PO + expiry batch ≥ today + min_shelf_life."""
    if doc.get("is_return"):
        return

    min_shelf_life = _get_min_shelf_life_days()

    for row in doc.items:
        # 1. Tolerance qty so với PO (±2% cảnh báo, +5% block — TechSpec §M3)
        if row.purchase_order:
            po_qty = frappe.db.get_value(
                "Purchase Order Item",
                {"parent": row.purchase_order, "item_code": row.item_code, "name": row.purchase_order_item}
                if row.get("purchase_order_item")
                else {"parent": row.purchase_order, "item_code": row.item_code},
                "qty",
            )
            if po_qty:
                received_pct = flt(row.qty) / flt(po_qty)
                if received_pct > 1.05:
                    frappe.throw(
                        _("Item {0}: SL nhận {1} > PO {2} quá 5%").format(
                            row.item_code, row.qty, po_qty),
                        title="SC-E009 PR_OVERAGE")

        # 2. Expiry check
        expiry = row.get("manufacture_date")  # placeholder
        if row.get("batch_no") and frappe.db.exists("Batch", row.batch_no):
            expiry = frappe.db.get_value("Batch", row.batch_no, "expiry_date")
            if expiry:
                days_to_expiry = date_diff(expiry, today())
                if days_to_expiry < 0:
                    frappe.throw(_("Batch {0} đã hết hạn ({1})").format(row.batch_no, expiry),
                                 title="SC-E003 EXPIRY_TOO_CLOSE")
                if days_to_expiry < min_shelf_life:
                    frappe.msgprint(
                        _("Item {0} batch {1}: hạn dùng còn {2} ngày (< ngưỡng {3}). Cần xác nhận.").format(
                            row.item_code, row.batch_no, days_to_expiry, min_shelf_life),
                        indicator="orange", alert=True)


# ---------------------------------------------------------------------------
# update_putaway — on_submit (M4)
# ---------------------------------------------------------------------------
def update_putaway(doc, method=None):
    """on_submit: TODO M4 — apply Putaway Rule, gán bin location."""
    pass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _find_checklist_template(item_code: str):
    """Tìm template phù hợp: theo item_group → fallback global."""
    item_group = frappe.db.get_value("Item", item_code, "item_group")
    if item_group:
        tpl = frappe.db.get_value("QC Checklist Template", {
            "item_group": item_group,
            "is_default_for_group": 1,
            "enabled": 1,
        }, "name")
        if tpl:
            return tpl
    # Fallback: global template (item_group rỗng)
    return frappe.db.get_value("QC Checklist Template", {
        "item_group": ["in", [None, ""]],
        "enabled": 1,
    }, "name")


def _get_min_shelf_life_days() -> int:
    try:
        v = frappe.db.get_single_value("SupplyCore Settings", "fefo_min_shelf_life_days")
        return int(v) if v else 30
    except Exception:
        return 30
