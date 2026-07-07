"""Custom permission logic — gọi từ hooks.py."""

import frappe


def stock_entry_query(user=None):
    """permission_query_conditions cho Stock Entry — giới hạn theo warehouse của user."""
    if not user:
        user = frappe.session.user
    if "System Manager" in frappe.get_roles(user):
        return ""
    # TODO: lookup warehouses gán cho user, return SQL where clause
    return ""


# ---------------------------------------------------------------------------
# M12 Customer Portal (GĐ3 Task 2) — cô lập dữ liệu khách (RSK-01)
# ---------------------------------------------------------------------------

PORTAL_ROLE = "SC Customer Portal"


def _portal_customer_scope(table_doctype: str, user: str) -> str:
    """SQL WHERE (string) giới hạn `tab{table_doctype}` theo customer của portal user.

    Nếu user không có role Portal → "" (nội bộ, không giới hạn). Nếu có role
    Portal → chỉ thấy các dòng có `customer` thuộc SC Customer mà
    `portal_user == user`. Portal user chưa link customer nào → subquery rỗng
    → không thấy gì (an toàn, không lộ dữ liệu).
    """
    roles = frappe.get_roles(user)
    if PORTAL_ROLE not in roles:
        return ""
    esc = frappe.db.escape(user)
    return (
        f"`tab{table_doctype}`.customer in "
        f"(select name from `tabSC Customer` where portal_user = {esc})"
    )


def sales_order_portal_query(user=None):
    return _portal_customer_scope("SC Sales Order", user or frappe.session.user)


def delivery_note_portal_query(user=None):
    return _portal_customer_scope("SC Delivery Note", user or frappe.session.user)


def sales_invoice_portal_query(user=None):
    return _portal_customer_scope("SC Sales Invoice", user or frappe.session.user)


def sales_receipt_portal_query(user=None):
    return _portal_customer_scope("SC Sales Receipt", user or frappe.session.user)


def sales_fc_portal_query(user=None):
    return _portal_customer_scope("SC Sales Framework Contract", user or frappe.session.user)


# ---------------------------------------------------------------------------
# Child-table isolation (RSK-01 caveat): `permission_query_conditions` được
# Frappe tra theo `self.doctype` CỦA TRUY VẤN, không phải theo doctype cha.
# Một truy vấn thẳng vào child doctype (vd. `frappe.get_list("SO Item",
# filters={"parent": <đơn của khách khác>}, parent_doctype="SC Sales Order")`)
# sẽ KHÔNG áp WHERE của `sales_order_portal_query` (hàm đó chỉ đăng ký cho
# doctype "SC Sales Order"). Nếu không đăng ký thêm ở đây, quyền đọc ở
# doctype-level (từ DocPerm của "SC Sales Order") vẫn cho phép Portal user
# liệt kê TOÀN BỘ dòng item của MỌI đơn — kể cả của khách khác — vì
# has_child_permission() chỉ kiểm tra quyền trên doctype cha, không lọc theo
# customer. Phải đăng ký permission_query_conditions RIÊNG cho 4 child
# doctype dưới đây (SC Sales Receipt không có child table item).
# ---------------------------------------------------------------------------

def _portal_child_scope(child_doctype: str, parent_doctype: str, user: str) -> str:
    """SQL WHERE giới hạn `tab{child_doctype}` theo customer của portal user,
    qua join `parent` -> `{parent_doctype}`.customer -> SC Customer.portal_user."""
    roles = frappe.get_roles(user)
    if PORTAL_ROLE not in roles:
        return ""
    esc = frappe.db.escape(user)
    return (
        f"`tab{child_doctype}`.parent in "
        f"(select name from `tab{parent_doctype}` where customer in "
        f"(select name from `tabSC Customer` where portal_user = {esc}))"
    )


def so_item_portal_query(user=None):
    return _portal_child_scope("SO Item", "SC Sales Order", user or frappe.session.user)


def dn_item_portal_query(user=None):
    return _portal_child_scope("DN Item", "SC Delivery Note", user or frappe.session.user)


def si_item_portal_query(user=None):
    return _portal_child_scope("SI Item", "SC Sales Invoice", user or frappe.session.user)


def sfc_item_portal_query(user=None):
    return _portal_child_scope("SFC Item", "SC Sales Framework Contract", user or frappe.session.user)


def portal_child_permission(doc, user=None, ptype=None, **kwargs):
    """has_permission hook cho 4 child doctype (SO/DN/SI/SFC Item) — phòng
    thủ chiều sâu (defense-in-depth), theo phát hiện review Task 2 (Minor 1).

    LƯU Ý QUAN TRỌNG (đã trace source `frappe/permissions.py`): đây KHÔNG
    PHẢI đường đi enforcement chính. `frappe.has_permission()` kiểm tra
    `frappe.is_table(doctype)` TRƯỚC TIÊN — nếu đúng, nó gọi thẳng
    `has_child_permission()` (permissions.py:763), hàm này resolve
    `child_doc.parent` (docname CHA THẬT của dòng con) rồi gọi lại
    `has_permission(parent_doctype, doc=<cha thật>, ...)` — tức là luôn
    chạy `portal_doc_permission` (ở trên) trên ĐÚNG chứng từ cha, không
    bao giờ chạm tới hook đăng ký riêng cho doctype con (hook con chỉ được
    tra qua `has_controller_permissions()`, mà hàm đó chỉ được gọi từ
    `get_doc_permissions()` — nhánh mà `is_table()` đã bỏ qua trước khi tới
    đó). Vì vậy hook này thực chất KHÔNG BAO GIỜ được Frappe core gọi qua
    luồng chuẩn (`doc.check_permission()`, `frappe.client.get`, single-doc
    `frappe.has_permission(...)`) — cơ chế cô lập con THẬT SỰ vẫn là:
      - `permission_query_conditions` trên 4 child doctype (Task 2) — lọc
        list-query thẳng vào child doctype.
      - `portal_doc_permission` trên 5 doctype cha (Task 2) — chặn
        single-doc read của cha (kể cả khi resolve từ child qua
        has_child_permission như trên).
    Đăng ký hook này chỉ để phòng ngừa Frappe thay đổi hành vi tương lai
    hoặc một đường gọi phi chuẩn nào đó gọi thẳng `has_controller_permissions`
    cho doctype con — KHÔNG được coi/báo cáo đây là cơ chế đang chặn thật.
    """
    user = user or frappe.session.user
    if PORTAL_ROLE not in frappe.get_roles(user):
        return True

    if ptype not in (None, "read", "print", "report"):
        return False

    parent_customer = frappe.db.get_value(doc.parenttype, doc.parent, "customer")
    if not parent_customer:
        return False
    return frappe.db.get_value("SC Customer", parent_customer, "portal_user") == user


def portal_doc_permission(doc, user=None, ptype=None, **kwargs):
    """has_permission hook cho 5 doctype bán — chặn Portal user khỏi doc của khách khác.

    LƯU Ý: Frappe gọi hook này qua `frappe.call(method, doc=doc, ptype=ptype,
    user=user, debug=debug)` (frappe/permissions.py::has_controller_permissions).
    `frappe.call` chỉ forward các kwargs khớp TÊN tham số của hàm đích — tham
    số ở đây PHẢI tên là `ptype` (không phải `permission_type`), nếu không
    Frappe sẽ luôn truyền None và mọi permission_type (kể cả write/submit)
    sẽ bị coi như read, làm mất tác dụng chặn ghi.

    Hook này CHỈ CÓ THỂ TỪ CHỐI (deny), không thể cấp thêm quyền — quyền đọc
    nền tảng vẫn đến từ DocPerm role permission (JSON) của role
    "SC Customer Portal" trên 5 doctype này (read/print/email/report).

    Nội bộ (không có role Portal) → True (permission thường xử lý). Portal
    user → chỉ True khi ptype là loại đọc VÀ doc.customer thuộc chính khách
    hàng của user; ngược lại False (chặn write/create/submit/cancel/delete
    và doc của khách khác).
    """
    user = user or frappe.session.user
    if PORTAL_ROLE not in frappe.get_roles(user):
        return True

    if ptype not in (None, "read", "print", "email", "report"):
        return False

    customer = getattr(doc, "customer", None)
    if not customer:
        return False

    owner_user = frappe.db.get_value("SC Customer", customer, "portal_user")
    return owner_user == user
