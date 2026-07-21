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

import re

import frappe
from frappe import _


# ---------------------------------------------------------------------------
# Chính sách mật khẩu dùng chung (nhân viên qua api/users + khách tự đăng ký
# qua api/portal). Quy định: ≥ 8 ký tự, có chữ HOA + chữ thường + số + ký tự
# đặc biệt. Enforce phía backend — FE chỉ là lớp tiện dụng.
# ---------------------------------------------------------------------------
def validate_password_strength(password: str) -> None:
    errs = []
    if len(password or "") < 8:
        errs.append(_("ít nhất 8 ký tự"))
    if not re.search(r"[A-Z]", password or ""):
        errs.append(_("1 chữ in HOA"))
    if not re.search(r"[a-z]", password or ""):
        errs.append(_("1 chữ thường"))
    if not re.search(r"[0-9]", password or ""):
        errs.append(_("1 chữ số"))
    if not re.search(r"[^A-Za-z0-9]", password or ""):
        errs.append(_("1 ký tự đặc biệt (vd @ # ! $ %)"))
    if errs:
        frappe.throw(
            _("Mật khẩu chưa đủ mạnh — cần có: {0}.").format(", ".join(errs)),
            title=_("Mật khẩu không hợp lệ"),
        )


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


def block_non_draft_delete(doc, method=None):
    """Guard xóa: chỉ cho xóa phiếu submittable khi còn Nháp (docstatus == 0).

    Đăng ký qua hooks.doc_events["<dt>"]["before_delete"] cho mọi doctype
    submittable. Là lớp phòng thủ nghiệp vụ song song với JSON delete-perm
    ("ai được xóa") — hàm này quyết định "xóa cái gì".

    - docstatus 1 (đã Submit): Frappe đã tự chặn ở tầng delete_doc; guard này
      chỉ là backup + thông điệp tiếng Việt.
    - docstatus 2 (đã Hủy): Frappe MẶC ĐỊNH cho xóa — guard chặn để giữ dấu vết.
    - Lệnh xóa lập trình/test (ignore_permissions=True) được bỏ qua, tránh phá
      cleanup trong tests/, setup/, patches/ (xem before_delete chạy cả khi force).
    """
    if getattr(doc.flags, "ignore_permissions", False):
        return
    if (doc.docstatus or 0) != 0:
        frappe.throw(
            _("Chỉ xóa được phiếu ở trạng thái Nháp. "
              "Phiếu đã gửi hoặc đã hủy phải được giữ lại (có thể Hủy thay vì xóa)."),
            title=_("Không thể xóa"),
        )
