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
