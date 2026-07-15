"""Shared validators — bù cho lỗ hổng Frappe link validation khi field có sibling fetch_from.

Lý do: Frappe v15 trong `BaseDocument.get_invalid_links()` có nhánh:
    if not fields_to_fetch:
        values = _dict(name=frappe.db.get_value(doctype, docname, "name", cache=True))
    else:
        values = frappe.db.get_value(doctype, docname, [...], as_dict=True)

Khi Link không tồn tại VÀ có field sibling `fetch_from: <link>.foo`, nhánh `else` chạy
trả về `values=None` → `if values:` False → không append invalid_links → silent pass.

Workaround: gọi explicit validators dưới đây trong `validate()` của các controller.
"""

import frappe
from frappe import _


def validate_link(doctype: str, name: str, label: str = None,
                   error_title: str = None, allow_blank: bool = False):
    """Bắt buộc giá trị Link tồn tại trong doctype tham chiếu.

    Args:
        doctype: target DocType
        name: docname để check
        label: tên hiển thị (mặc định = doctype)
        error_title: title cho frappe.throw
        allow_blank: nếu True, name rỗng → bỏ qua
    """
    if not name:
        if allow_blank:
            return
        frappe.throw(_("Bắt buộc chọn {0}").format(label or doctype),
                      title=error_title or "SC-E-LINK")
    if not frappe.db.exists(doctype, name):
        frappe.throw(_("{0} {1} không tồn tại").format(label or doctype, name),
                      frappe.LinkValidationError,
                      title=error_title or "SC-E-LINK")


def validate_supplier(name: str, *, allow_blank: bool = False):
    """SC Supplier link + active check."""
    validate_link("SC Supplier", name, label=_("NCC"),
                   error_title="SC-E-SUPPLIER", allow_blank=allow_blank)
    if not name:
        return
    sup = frappe.db.get_value("SC Supplier", name,
                                ["disabled", "blacklist_flag"], as_dict=True)
    if sup.disabled:
        frappe.throw(_("NCC {0} đang bị vô hiệu hóa").format(name),
                      title="SC-E-SUPPLIER")
    return sup


def validate_warehouse(name: str, *, allow_blank: bool = False, label: str = None):
    """SC Warehouse link + not disabled."""
    validate_link("SC Warehouse", name, label=label or _("Kho"),
                   error_title="SC-E-WAREHOUSE", allow_blank=allow_blank)
    if name and frappe.db.get_value("SC Warehouse", name, "disabled"):
        frappe.throw(_("Kho {0} đang bị vô hiệu hóa").format(name),
                      title="SC-E-WAREHOUSE")


def validate_item(name: str, *, allow_blank: bool = False):
    """SC Item link + not disabled."""
    validate_link("SC Item", name, label=_("Vật tư"),
                   error_title="SC-E-ITEM", allow_blank=allow_blank)
    if name and frappe.db.get_value("SC Item", name, "disabled"):
        frappe.throw(_("Vật tư {0} đang bị vô hiệu hóa").format(name),
                      title="SC-E-ITEM")
