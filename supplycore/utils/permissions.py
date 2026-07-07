"""Custom permission logic — gọi từ hooks.py."""

import frappe
from urllib.parse import unquote


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


# ---------------------------------------------------------------------------
# Residual RSK-01 hardening (GĐ4 Task 2) — REST resource/document read
# `/api/resource/<child>/<name>` (v1) và `/api/v2/document/<child>/<name>` (v2)
# ---------------------------------------------------------------------------
# `frappe.client.get` (dùng bởi `/api/method/frappe.client.get`) đã được chặn
# qua `override_whitelisted_methods` (xem hooks.py + `api/portal.py::
# guarded_client_get`). Nhưng route REST single-doc KHÔNG đi qua
# `frappe.client.get` — Frappe có 2 router version song song
# (`frappe/api/__init__.py::API_URL_MAP`, submount cả `/api` và `/api/v1` vào
# `v1.py::url_rules`, và `/api/v2` vào `v2.py::url_rules`):
#   - v1: `GET /api/resource/<doctype>/<name>/` (cũng khớp `/api/v1/resource/...`)
#     -> `frappe/api/v1.py::read_doc` -> `frappe.get_doc(...).check_permission("read")`
#   - v2: `GET /api/v2/document/<doctype>/<name>/`
#     -> `frappe/api/v2.py::read_doc` -> CÙNG PATTERN `doc.check_permission("read")`
# Cả 2 đều dẫn tới `has_child_permission()`, và như đã trace ở
# `portal_child_permission`/`test_portal_child_read_scoped`, hàm này không lọc
# theo customer khi resolve 1 child doc độc lập (không có `parent_doc` gắn
# sẵn) — chỉ còn lại quyền doctype-level (luôn True với role Portal đã có
# read=1 trên doctype cha). Docname là hash ngẫu nhiên (không enumerable qua
# bất kỳ API portal nào) nên rủi ro thực tế thấp, nhưng đây vẫn là 1 lỗ hổng
# thật nếu caller biết đúng docname — đóng cả 2 đường bằng 1 `before_request`
# hook chặn Ở MỨC REQUEST-PATH, trước khi request được dispatch tới handler.

_PORTAL_BLOCKED_REST_CHILDREN = ("SO Item", "DN Item", "SI Item", "SFC Item")

# Thứ tự không quan trọng — kiểm từng prefix, dùng prefix khớp đầu tiên để
# tách tên doctype (segment ngay sau prefix).
_PORTAL_REST_CHILD_PREFIXES = (
    "/api/resource/",        # v1, submount "/api"
    "/api/v1/resource/",     # v1, submount "/api/v1" (cùng url_rules, xem api/__init__.py)
    "/api/v2/document/",     # v2, submount "/api/v2"
)


def block_portal(user: str = None) -> None:
    """GĐ4 Task 5 (RSK-01 completeness sweep) — chặn role Portal khỏi bất kỳ
    API nội bộ nào KHÔNG tự kiểm tra quyền per-doc (financial reports, KPI,
    audit trail, warehouse map, WMS/FEFO helper...).

    Khác với `_require_ar_aging_role`/`_require_user_admin` (allow-list nội
    bộ — chỉ N role cụ thể được gọi), đây là BLOCK-LIST: chỉ chặn role
    Portal, mọi role nội bộ khác (Manager/Storekeeper/User/...) đều đi qua
    bình thường. Vì vậy áp dụng hàm này ở đầu 1 whitelisted function KHÔNG
    có rủi ro hồi quy nội bộ — an toàn để áp rộng cho toàn bộ API nội bộ
    thiếu permission check, mà không cần liệt kê hết role nào được phép.

    KHÔNG dùng cho `api/portal.py` (Portal user PHẢI gọi được các hàm đó).

    LƯU Ý (phát hiện qua regression Task 5): `frappe.get_roles("Administrator")`
    KHÔNG đọc bảng "Has Role" như user thường — nó trả về TOÀN BỘ role đang
    tồn tại trong hệ thống (`frappe/permissions.py::get_roles`, đặc cách cho
    Administrator), tức là danh sách đó LUÔN chứa cả "SC Customer Portal".
    Nếu không loại trừ Administrator, mọi lời gọi nội bộ chạy dưới session
    Administrator (vd `bench execute` test, hoặc controller tự gọi các hàm
    này qua Python call bình thường) sẽ bị `block_portal()` chặn NHẦM — dù
    Administrator chưa từng và không thể là user Portal thật. Loại trừ ở đây
    an toàn tuyệt đối: `frappe.has_permission()` (đường enforcement chính của
    Frappe) cũng luôn trả True vô điều kiện cho Administrator, nên hành vi
    này chỉ đồng bộ theo đúng quy ước sẵn có của Frappe, không mở thêm lỗ hổng
    nào (Administrator thật ngoài đời không bao giờ là Portal user).
    """
    user = user or frappe.session.user
    if user == "Administrator":
        return
    if PORTAL_ROLE in frappe.get_roles(user):
        frappe.throw(frappe._("Không có quyền truy cập dữ liệu nội bộ này"),
                     frappe.PermissionError)


def portal_block_rest_child():
    """`before_request` hook (đăng ký ở hooks.py) — chặn role Portal truy cập
    REST resource/document endpoint (`/api/resource/`, `/api/v1/resource/`
    v1 và `/api/v2/document/` v2 — xem `_PORTAL_REST_CHILD_PREFIXES`) cho 4
    child doctype bán hàng (SO Item/DN Item/SI Item/SFC Item), bất kể có
    `<name>` hay không.

    Chạy trên MỌI request (Frappe gọi `before_request` cho tất cả request,
    kể cả static/non-API) — PHẢI rẻ và an toàn: return sớm nếu thiếu
    request/session, không bao giờ throw cho user không có role Portal hay
    path không khớp 1 trong 3 prefix REST của 4 child doctype này. Không đụng
    tới REST resource của doctype CHA (SC Sales Order/... — đã được gate qua
    `portal_doc_permission`/`has_permission` sẵn có, không thuộc phạm vi hook
    này) hay bất kỳ path nào khác.

    Thời điểm chạy: `frappe/app.py::init_request()` gọi các `before_request`
    hook SAU KHI `HTTPRequest()` đã resume session từ cookie (`set_session()`
    -> `LoginManager()`), nên `frappe.session.user` ở đây đã là user thật đã
    đăng nhập (không phải "Guest" mặc định của `frappe.init()`), TRƯỚC KHI
    request được dispatch tới route handler (`frappe.api.handle` / `read_doc`).
    """
    req = getattr(frappe.local, "request", None)
    if not req:
        return

    path = getattr(req, "path", None)
    if not path or "/api/" not in path:
        return

    decoded = unquote(path)
    matched_prefix = next((p for p in _PORTAL_REST_CHILD_PREFIXES if decoded.startswith(p)), None)
    if not matched_prefix:
        return

    doctype = decoded[len(matched_prefix):].split("/", 1)[0]
    if doctype not in _PORTAL_BLOCKED_REST_CHILDREN:
        return

    session = getattr(frappe.local, "session", None)
    user = getattr(session, "user", None) if session else None
    if not user or user == "Guest":
        return

    if PORTAL_ROLE in frappe.get_roles(user):
        frappe.throw(frappe._("Không có quyền truy cập dữ liệu này"), frappe.PermissionError)
