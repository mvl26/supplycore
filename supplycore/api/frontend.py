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
