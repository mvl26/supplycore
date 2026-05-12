"""Backend API cho SupplyCore SPA frontend.

Frappe v15 strict field whitelist trên /api/resource/<dt> chặn nhiều custom
fields. Frontend cần linh hoạt query bất kỳ field nào — wrap qua đây với
frappe.db.get_all (bypass field validation, nhưng vẫn check role permissions).
"""

import frappe
from frappe import _


@frappe.whitelist()
def list_docs(doctype, fields=None, filters=None, order_by=None, limit=20, start=0):
    """List docs với fields linh hoạt — bypass Frappe.client.get_list whitelist.

    Vẫn check role permission qua frappe.has_permission.
    """
    if not frappe.has_permission(doctype, "read"):
        frappe.throw(_("Không có quyền đọc {0}").format(doctype), frappe.PermissionError)

    import json
    if isinstance(fields, str):
        fields = json.loads(fields)
    if isinstance(filters, str):
        filters = json.loads(filters)

    fields = fields or ["name"]
    filters = filters or {}

    try:
        return frappe.db.get_all(
            doctype,
            fields=fields,
            filters=filters,
            order_by=order_by or "modified desc",
            limit=int(limit) if limit else None,
            start=int(start) if start else 0,
            ignore_permissions=False,
        )
    except Exception as e:
        frappe.log_error(message=f"list_docs({doctype}): {e}", title="frontend.list_docs")
        frappe.throw(_("Lỗi truy vấn {0}: {1}").format(doctype, str(e)[:200]))


@frappe.whitelist()
def get_doc(doctype, name):
    """Get full doc + child tables."""
    if not frappe.has_permission(doctype, "read", doc=name):
        frappe.throw(_("Không có quyền đọc {0} {1}").format(doctype, name), frappe.PermissionError)
    return frappe.get_doc(doctype, name).as_dict()


@frappe.whitelist()
def count_docs(doctype, filters=None):
    """Count docs."""
    if not frappe.has_permission(doctype, "read"):
        frappe.throw(_("Không có quyền").format(doctype), frappe.PermissionError)
    import json
    if isinstance(filters, str):
        filters = json.loads(filters)
    return frappe.db.count(doctype, filters=filters or {})


@frappe.whitelist()
def submit_doc(doctype, name):
    """Submit doc — tránh TimestampMismatchError do client-side fetch dance.

    frappe.client.submit() yêu cầu pass full doc dict + modified timestamp;
    nếu doc bị modify giữa fetch và submit → TimestampMismatchError.
    Wrapper này fetch fresh + submit trong cùng request.
    """
    if not frappe.has_permission(doctype, "submit", doc=name):
        frappe.throw(_("Không có quyền submit {0} {1}").format(doctype, name),
                      frappe.PermissionError)
    doc = frappe.get_doc(doctype, name)
    doc.submit()
    return doc.as_dict()


@frappe.whitelist()
def cancel_doc(doctype, name):
    """Cancel doc — tương tự submit_doc."""
    if not frappe.has_permission(doctype, "cancel", doc=name):
        frappe.throw(_("Không có quyền cancel {0} {1}").format(doctype, name),
                      frappe.PermissionError)
    doc = frappe.get_doc(doctype, name)
    doc.cancel()
    return doc.as_dict()


@frappe.whitelist()
def related_docs(doctype, name):
    """Trả related/reverse-link docs cho 1 doc cụ thể.

    Mapping mỗi doctype → related queries:
    - Framework Contract → POs link FC + items
    - SC Purchase Order → PRs + PIs + MR liên quan
    - SC Purchase Receipt → QIs + Batches + PI
    - SC Quality Inspection → PR + Item
    - SC Item → Batches + recent SLE
    - SC Batch → SLE + Recall + Trace movements
    - SC Patient → recent PDs
    - SC Dispensing Request → PD generated
    """
    out = {}
    if not frappe.has_permission(doctype, "read", doc=name):
        frappe.throw(_("Không có quyền đọc {0}").format(doctype), frappe.PermissionError)

    if doctype == "Framework Contract":
        out["purchase_orders"] = frappe.db.get_all("SC Purchase Order",
            filters={"framework_contract": name},
            fields=["name", "transaction_date", "supplier", "grand_total", "status", "docstatus"],
            order_by="transaction_date desc", limit=20)

    elif doctype == "SC Purchase Order":
        out["material_requests"] = frappe.db.get_all("SC Material Request Item",
            filters={"po": name} if frappe.db.has_column("SC Material Request Item", "po") else {},
            fields=["parent"], limit=10) if frappe.db.has_column("SC Material Request Item", "po") else []
        out["purchase_receipts"] = frappe.db.get_all("SC Purchase Receipt",
            filters={"purchase_order": name},
            fields=["name", "posting_date", "supplier", "is_return", "qc_status", "docstatus"],
            order_by="posting_date desc", limit=20)

    elif doctype == "SC Purchase Receipt":
        out["quality_inspections"] = frappe.db.get_all("SC Quality Inspection",
            filters={"purchase_receipt": name},
            fields=["name", "inspection_date", "item", "batch", "overall_status", "docstatus"],
            order_by="inspection_date desc", limit=50)
        # Batches từ PR Item
        out["batches"] = frappe.db.sql("""
            SELECT DISTINCT pri.batch_no AS name, b.item, b.expiry_date, b.qc_status
            FROM `tabSC Purchase Receipt Item` pri
            LEFT JOIN `tabSC Batch` b ON b.name = pri.batch_no
            WHERE pri.parent = %s AND pri.batch_no IS NOT NULL
        """, name, as_dict=True)
        out["purchase_invoices"] = frappe.db.get_all("SC Purchase Invoice",
            filters={"purchase_receipt": name},
            fields=["name", "invoice_date", "supplier", "grand_total", "outstanding_amount", "status", "docstatus"],
            limit=10)

    elif doctype == "SC Quality Inspection":
        # Trả PR + Item info qua get_doc
        pass

    elif doctype == "SC Item":
        out["batches"] = frappe.db.get_all("SC Batch",
            filters={"item": name, "disabled": 0},
            fields=["name", "supplier", "supplier_batch_no", "manufacturing_date",
                     "expiry_date", "qc_status", "blocked"],
            order_by="expiry_date asc", limit=50)
        # Stock balance per warehouse
        out["stock_balance"] = frappe.db.sql("""
            SELECT warehouse, COALESCE(SUM(qty_change), 0) AS qty,
                   COALESCE(SUM(qty_change * valuation_rate), 0) AS value
            FROM `tabSC Stock Ledger Entry`
            WHERE item = %s AND is_cancelled = 0
            GROUP BY warehouse
            HAVING qty > 0
            ORDER BY qty DESC
        """, name, as_dict=True)
        out["recent_movements"] = frappe.db.get_all("SC Stock Ledger Entry",
            filters={"item": name, "is_cancelled": 0},
            fields=["name", "posting_date", "warehouse", "batch", "qty_change",
                     "balance_qty", "voucher_type", "voucher_no"],
            order_by="creation desc", limit=20)

    elif doctype == "SC Batch":
        out["movements"] = frappe.db.get_all("SC Stock Ledger Entry",
            filters={"batch": name, "is_cancelled": 0},
            fields=["name", "posting_date", "warehouse", "qty_change", "balance_qty",
                     "voucher_type", "voucher_no"],
            order_by="creation desc", limit=50)
        out["recalls"] = frappe.db.get_all("SC Recall Notice",
            filters={"batch_no": name},
            fields=["name", "recall_date", "severity", "status", "docstatus"],
            limit=5)
        out["stock_balance"] = frappe.db.sql("""
            SELECT warehouse, COALESCE(SUM(qty_change), 0) AS qty
            FROM `tabSC Stock Ledger Entry`
            WHERE batch = %s AND is_cancelled = 0
            GROUP BY warehouse
            HAVING qty > 0
        """, name, as_dict=True)

    elif doctype == "SC Patient":
        out["dispensings"] = frappe.db.get_all("SC Patient Dispensing",
            filters={"patient": name, "docstatus": 1},
            fields=["name", "dispensing_date", "ward", "total_cost", "patient_pays"],
            order_by="dispensing_date desc", limit=20)

    elif doctype == "SC Dispensing Request":
        out["patient_dispensings"] = frappe.db.get_all("SC Patient Dispensing",
            filters={"dispensing_request": name},
            fields=["name", "dispensing_date", "patient", "patient_name", "total_cost"],
            limit=10)

    elif doctype == "SC Supplier":
        out["framework_contracts"] = frappe.db.get_all("Framework Contract",
            filters={"supplier": name},
            fields=["name", "contract_number", "valid_from", "valid_to", "total_value",
                     "remaining_value", "status"],
            limit=20)
        out["purchase_orders"] = frappe.db.get_all("SC Purchase Order",
            filters={"supplier": name, "docstatus": 1},
            fields=["name", "transaction_date", "grand_total", "status"],
            order_by="transaction_date desc", limit=10)

    elif doctype == "SC Recall Notice":
        out["affected_items"] = frappe.db.get_all("SC Recall Affected Item",
            filters={"parent": name},
            fields=["name", "warehouse", "department", "patient", "qty_dispensed",
                     "recovered_qty", "destroyed_qty", "status"],
            limit=50)

    return out


@frappe.whitelist()
def stock_balance(item=None, warehouse=None, batch=None, item_group=None):
    """UC-16: tồn kho per item/warehouse/batch. Aggregate SLE."""
    conds = ["sle.is_cancelled = 0"]
    params = {}
    if item:
        conds.append("sle.item = %(item)s"); params["item"] = item
    if warehouse:
        conds.append("sle.warehouse = %(wh)s"); params["wh"] = warehouse
    if batch:
        conds.append("sle.batch = %(batch)s"); params["batch"] = batch
    if item_group:
        conds.append("i.item_group = %(g)s"); params["g"] = item_group

    rows = frappe.db.sql(f"""
        SELECT sle.item, i.item_name, sle.warehouse, sle.batch,
               COALESCE(SUM(sle.qty_change), 0) AS qty,
               COALESCE(SUM(sle.qty_change * sle.valuation_rate), 0) AS value,
               b.expiry_date, b.qc_status, b.blocked
        FROM `tabSC Stock Ledger Entry` sle
        LEFT JOIN `tabSC Item` i ON i.name = sle.item
        LEFT JOIN `tabSC Batch` b ON b.name = sle.batch
        WHERE {' AND '.join(conds)}
        GROUP BY sle.item, sle.warehouse, sle.batch
        HAVING qty > 0
        ORDER BY i.item_name, sle.warehouse, b.expiry_date ASC
        LIMIT 500
    """, params, as_dict=True)
    return rows


@frappe.whitelist()
def save_doc(doctype, name, fields):
    """Update doc fields + save (Draft only). Tránh TimestampMismatch."""
    import json
    if isinstance(fields, str):
        fields = json.loads(fields)
    if not frappe.has_permission(doctype, "write", doc=name):
        frappe.throw(_("Không có quyền sửa {0} {1}").format(doctype, name),
                      frappe.PermissionError)
    doc = frappe.get_doc(doctype, name)
    for k, v in (fields or {}).items():
        if k not in ("name", "doctype", "owner", "creation", "modified", "modified_by",
                     "docstatus", "idx", "parent", "parentfield", "parenttype"):
            doc.set(k, v)
    doc.save()
    return doc.as_dict()
