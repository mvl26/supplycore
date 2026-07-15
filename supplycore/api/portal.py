"""API Portal khách hàng -- M12 Customer Portal (GĐ3).

Task 1 (GĐ3): provisioning tài khoản Portal cho SC Customer.
Task 3 (GĐ3): 7 API portal tự lọc theo khách hàng đăng nhập -- portal_me,
portal_contracts, portal_catalog, portal_order_place, portal_order_track,
portal_order_history, portal_document_download.

Mọi API (trừ portal_provision) đều gọi `_require_portal_customer()` đầu
tiên rồi tự lọc/kiểm tra theo `customer` trả về -- không tin filters do
client gửi lên. Không trả `name` (docname) của dòng child-table ra ngoài
(chỉ item/qty/giá) để tránh rò rỉ định danh nội bộ không cần thiết.
"""

import re

import frappe
from frappe import _
from frappe.utils import cint, flt, today

PORTAL_ROLE = "SC Customer Portal"
# Role NHÃN khách hàng — gán KÈM PORTAL_ROLE (xem setup/ensure_customer_role.py).
# PORTAL_ROLE vẫn là role chức năng gating; CUSTOMER_ROLE chỉ để hiển thị/nhóm.
CUSTOMER_ROLE = "Khách hàng"
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PROVISION_ROLES = {"System Manager", "SupplyCore Manager", "SupplyCore Purchaser"}
DOWNLOADABLE_DOCTYPES = {"SC Sales Invoice", "SC Delivery Note", "SC Acceptance Record"}

# ---------------------------------------------------------------------------
# RSK-01 Critical — chặn rò rỉ chéo child-row qua `frappe.client.get`
# ---------------------------------------------------------------------------
# 4 child doctype bán hàng: khi đọc đơn lẻ (theo `name` hoặc `filters`) qua
# `frappe.client.get`, Frappe KHÔNG chạy `portal_doc_permission`/
# `portal_child_permission` (xem docstring `guarded_client_get` +
# `hooks.py::override_whitelisted_methods` để trace chi tiết bug gốc trong
# `has_child_permission()`) — chỉ còn lại kiểm tra doctype-level luôn True
# với role Portal. Portal user KHÔNG BAO GIỜ cần đọc trực tiếp các doctype
# này (7 API portal ở dưới đã tự lọc + trả field cần thiết), nên đơn giản
# và an toàn nhất là CHẶN HẲN mọi truy cập trực tiếp của Portal caller.
_PORTAL_BLOCKED_CHILD = {"SO Item", "DN Item", "SI Item", "SFC Item"}


@frappe.whitelist()
def portal_provision(customer, email, send_invite=False):
    """Cấp tài khoản Portal cho SC Customer.

    Tạo (hoặc lấy) Website User theo `email`, gán role "SC Customer Portal",
    và link vào `SC Customer.portal_user`. Chỉ System Manager / SupplyCore
    Manager / SupplyCore Purchaser mới được gọi.

    send_invite (truthy) → gửi email đặt/đổi mật khẩu để khách tự đăng nhập.
    Bọc lỗi: site chưa cấu hình SMTP vẫn provision thành công (chỉ bỏ qua email).
    """
    roles = set(frappe.get_roles(frappe.session.user))
    if not (roles & PROVISION_ROLES):
        frappe.throw(_("Không có quyền cấp tài khoản Portal"), frappe.PermissionError)

    send_invite = frappe.utils.cint(send_invite)

    customer_doc = frappe.get_doc("SC Customer", customer)
    if customer_doc.portal_user:
        return customer_doc.portal_user

    new_user = not frappe.db.exists("User", email)
    if new_user:
        user_doc = frappe.get_doc({
            "doctype": "User",
            "email": email,
            "first_name": customer_doc.customer_name,
            "user_type": "Website User",
            "send_welcome_email": 0,
        }).insert(ignore_permissions=True)
    else:
        user_doc = frappe.get_doc("User", email)

    user_doc.add_roles(PORTAL_ROLE)
    if frappe.db.exists("Role", CUSTOMER_ROLE):
        user_doc.add_roles(CUSTOMER_ROLE)  # nhãn 'Khách hàng' (kèm PORTAL_ROLE)

    # BRU-CUS-002: mỗi tài khoản Portal chỉ gắn ĐÚNG MỘT khách hàng. set_value
    # bên dưới ghi thẳng SQL (bỏ qua controller validate → _validate_portal_user_unique
    # không chạy), nên phải tự kiểm ở đây: nếu user (đã chuẩn hoá) đã là
    # portal_user của khách khác → chặn, tránh 1 user thấy dữ liệu chéo nhiều
    # khách (permission_query_conditions lọc theo portal_user).
    other = frappe.db.get_value(
        "SC Customer",
        {"portal_user": user_doc.name, "name": ["!=", customer]},
        "name",
    )
    if other:
        frappe.throw(_(
            "BRU-CUS-002: Tài khoản Portal {0} đã được gán cho khách hàng {1} — "
            "mỗi tài khoản chỉ gắn với đúng một khách hàng."
        ).format(user_doc.name, other))

    # Frappe chuẩn hoá User.name/email về chữ thường khi validate (xem
    # frappe/core/doctype/user/user.py: self.email = self.email.strip().lower()).
    # Phải dùng user_doc.name (đã chuẩn hoá) để lưu vào SC Customer.portal_user
    # và trả về -- nếu dùng lại biến `email` gốc (có thể khác hoa/thường),
    # sau này so sánh với frappe.session.user (luôn chữ thường sau khi đăng
    # nhập thật) sẽ lệch nhau và portal_doc_permission sẽ từ chối luôn cả
    # chủ sở hữu hợp lệ (GĐ3 Task 2 phát hiện qua isolation test).
    frappe.db.set_value("SC Customer", customer, "portal_user", user_doc.name)

    if send_invite:
        # Gửi link đặt mật khẩu để khách tự đăng nhập. Bọc lỗi: site chưa cấu
        # hình SMTP (vd dev) không được làm hỏng việc provision — tài khoản đã
        # tạo + link xong, admin có thể gửi lại sau.
        try:
            user_doc.reload()
            user_doc.reset_password(send_email=True)
        except Exception:
            frappe.log_error(frappe.get_traceback(),
                             f"portal_provision: gửi email đặt mật khẩu thất bại cho {user_doc.name}")

    return user_doc.name


@frappe.whitelist()
def guarded_client_get(doctype, name=None, filters=None, parent=None):
    """Override của `frappe.client.get` (đăng ký qua
    `hooks.py::override_whitelisted_methods`) — chặn RSK-01 Critical.

    Chữ ký PHẢI khớp CHÍNH XÁC `frappe.client.get(doctype, name=None,
    filters=None, parent=None)` (Frappe hiện tại không có kwargs nào khác)
    để `frappe.call`/dispatcher forward đúng tham số, không phá caller nội
    bộ hợp lệ nào.

    Với caller có role "SC Customer Portal": nếu `doctype` là 1 trong 4
    child doctype bán hàng (`SO Item`/`DN Item`/`SI Item`/`SFC Item`) →
    luôn từ chối (PermissionError), bất kể `name`/`filters` gì — vì
    `has_child_permission()` của Frappe (xem trace trong `hooks.py`) resolve
    `doc=None` khi đọc 1 dòng con độc lập (không nằm trong parent doc đầy
    đủ), bỏ qua hoàn toàn `portal_doc_permission`/`portal_child_permission`,
    và chỉ còn lại kiểm tra doctype-level (luôn True vì role Portal có
    read=1 trên 5 doctype cha). Portal user không cần đọc trực tiếp các
    doctype này — 7 API portal ở trên đã tự lọc theo customer + chỉ trả
    field cần thiết (không trả `name`/docname child ra ngoài).

    Mọi caller khác (không có role Portal) và mọi doctype khác → delegate
    nguyên vẹn cho `frappe.client.get` gốc — không thay đổi hành vi."""
    if doctype in _PORTAL_BLOCKED_CHILD and PORTAL_ROLE in frappe.get_roles(frappe.session.user):
        frappe.throw(_("Không có quyền truy cập dữ liệu này"), frappe.PermissionError)

    from frappe.client import get as _orig_client_get
    return _orig_client_get(doctype, name, filters, parent)


# ---------------------------------------------------------------------------
# Task 3 (GĐ3) — 7 API portal khách hàng
# ---------------------------------------------------------------------------


def _require_portal_customer() -> str:
    """Chặn user không phải Portal hoặc chưa link SC Customer nào.

    Trả về `SC Customer.name` của `frappe.session.user`. Mọi API bên dưới
    PHẢI gọi hàm này đầu tiên và tự lọc/kiểm tra dữ liệu theo giá trị trả
    về -- không được tin bất kỳ tham số "customer" nào do client gửi lên.
    """
    user = frappe.session.user
    if PORTAL_ROLE not in frappe.get_roles(user):
        frappe.throw(_("Chỉ tài khoản Portal khách hàng mới được gọi API này"),
                      frappe.PermissionError)

    customer = frappe.db.get_value("SC Customer", {"portal_user": user}, "name")
    if not customer:
        frappe.throw(_("Tài khoản Portal chưa được liên kết với khách hàng nào"),
                      frappe.PermissionError)
    return customer


def _customer_outstanding(customer: str) -> float:
    """Dư nợ phải thu hiện tại của khách — delegate về HÀM CHUẨN DUY NHẤT
    `utils.receivables.get_customer_outstanding` (GĐ MVL: portal + rule + report
    dùng chung một nguồn, không còn resolve TK 131 rời rạc mỗi nơi)."""
    from supplycore.utils.receivables import get_customer_outstanding
    return get_customer_outstanding(customer)


@frappe.whitelist()
def portal_me():
    """Hồ sơ khách hàng đăng nhập: tên, hạn mức công nợ, dư nợ hiện tại."""
    customer = _require_portal_customer()
    doc = frappe.get_doc("SC Customer", customer)
    return {
        "customer": doc.name,
        "customer_name": doc.customer_name,
        "status": doc.status,
        "credit_limit": flt(doc.credit_limit),
        "outstanding": _customer_outstanding(customer),
    }


def _attach_item_names(rows):
    """Gắn `item_name` (tên vật tư, `SC Item.item_name`) vào từng dòng có
    field `item` (mã vật tư) -- UC-41 khách hàng tìm "theo tên hoặc mã",
    chỉ trả mã (item code) là không đủ. 1 query duy nhất theo danh sách mã
    distinct, tránh N+1."""
    item_codes = list({r["item"] for r in rows if r.get("item")})
    if not item_codes:
        return rows
    names_by_code = {
        r.name: r.item_name for r in frappe.get_all(
            "SC Item", filters={"name": ["in", item_codes]}, fields=["name", "item_name"])
    }
    for r in rows:
        r["item_name"] = names_by_code.get(r.get("item"))
    return rows


@frappe.whitelist()
def portal_contracts():
    """Danh sách Hợp đồng khung (SFC) đang Hiệu lực (và CHƯA hết hạn) của
    khách + items. `status="Hiệu lực"` không đủ: SFC không có scheduler tự
    chuyển "Hiệu lực" -> "Hết hạn" mỗi ngày (chỉ `_derive_status()` chạy khi
    doc được save lại) nên 1 hợp đồng đã qua `valid_to` vẫn có thể còn
    status "Hiệu lực" stale trong DB -- phải tự lọc thêm `valid_to >=
    today()` ở đây, không tin riêng field `status`."""
    customer = _require_portal_customer()
    contracts = frappe.get_all(
        "SC Sales Framework Contract",
        filters={"customer": customer, "status": "Hiệu lực", "valid_to": [">=", today()]},
        fields=["name", "contract_number", "valid_from", "valid_to", "total_value", "status"],
        order_by="valid_from desc",
    )
    for c in contracts:
        c["items"] = frappe.get_all(
            "SFC Item", filters={"parent": c["name"]},
            fields=["item", "uom", "contract_qty", "sold_qty", "remaining_qty", "unit_price"],
            order_by="idx",
        )
        _attach_item_names(c["items"])
        # c7 — tổng SL đã gọi (Σ sold_qty) + số lần gọi (số SC Sales Order đã
        # submit, không tính Từ chối) trên hợp đồng này. Dữ liệu sẵn có, chỉ tổng hợp.
        c["total_ordered_qty"] = sum(flt(it["sold_qty"]) for it in c["items"])
        c["order_count"] = frappe.db.count(
            "SC Sales Order",
            {"framework_contract": c["name"], "docstatus": 1, "status": ["!=", "Từ chối"]})
    return contracts


@frappe.whitelist()
def portal_catalog():
    """Danh mục vật tư gộp từ mọi SFC còn Hiệu lực VÀ chưa hết hạn (xem
    docstring `portal_contracts` -- cùng lý do cần lọc thêm `valid_to`) của
    khách."""
    customer = _require_portal_customer()
    sfc_names = frappe.get_all(
        "SC Sales Framework Contract",
        filters={
            "customer": customer, "status": "Hiệu lực",
            # BRU-SFC-001: chỉ HĐ CÒN hiệu lực theo NGÀY — vừa chưa hết hạn
            # (valid_to>=today) vừa đã tới ngày hiệu lực (valid_from<=today).
            # Thiếu lọc valid_from → HĐ tương lai (submit set status="Hiệu lực"
            # ngay) lọt vào catalog cho khách đặt sớm.
            "valid_to": [">=", today()], "valid_from": ["<=", today()],
        },
        pluck="name",
    )
    if not sfc_names:
        return []
    rows = frappe.get_all(
        "SFC Item", filters={"parent": ["in", sfc_names]},
        fields=["item", "uom", "unit_price", "remaining_qty", "parent as framework_contract"],
        order_by="item",
    )
    return _attach_item_names(rows)


@frappe.whitelist()
def portal_order_place(contract, items):
    """Tạo SC Sales Order cho khách đăng nhập trên Hợp đồng khung của chính
    khách. `items` chỉ cần `item` + `qty` -- đơn giá do controller SC Sales
    Order tự lấy từ SFC Item (BRU-SFC-002), không tin giá do client gửi.
    Insert bằng ignore_permissions (Portal không có quyền create ở DocPerm)
    nhưng controller vẫn enforce đầy đủ BRU-SFC-001/002 + BRU-SO-001 +
    BRU-AR-001 -- các throw của controller được cho lan (propagate) nguyên
    vẹn ra ngoài."""
    customer = _require_portal_customer()

    if isinstance(items, str):
        items = frappe.parse_json(items)

    fc_customer = frappe.db.get_value("SC Sales Framework Contract", contract, "customer")
    if not fc_customer or fc_customer != customer:
        frappe.throw(_("Không có quyền đặt hàng trên Hợp đồng khung này"),
                      frappe.PermissionError)

    # BUG 2: chan qty<=0 (hoac khong phai so) truoc khi tao SO -- portal user
    # khong duoc phep tao don rac tong tien = 0 (hoac am) qua Portal. Kiem
    # tra o day (som nhat) thay vi de controller SC Sales Order xu ly, vi
    # SO Item.qty chi co rang buoc non_negative (cho phep 0) chu khong bat
    # buoc > 0.
    for row in items:
        try:
            qty = flt(row.get("qty"))
        except (TypeError, ValueError):
            qty = 0
        if qty <= 0:
            frappe.throw(_("Số lượng phải > 0"))

    uom_by_item = {
        r.item: r.uom for r in frappe.get_all(
            "SFC Item", filters={"parent": contract}, fields=["item", "uom"])
    }

    so = frappe.new_doc("SC Sales Order")
    so.customer = customer
    so.framework_contract = contract
    so.order_date = today()
    for row in items:
        item_code = row.get("item")
        so.append("items", {
            "item": item_code,
            "uom": uom_by_item.get(item_code),
            "qty": flt(row.get("qty")),
        })
    so.flags.ignore_permissions = True
    so.insert()
    # BRU-INV-002 (Q1): chặn SỚM tồn không đủ ngay khi khách gọi hàng — sau insert
    # (đã qua BRU-SFC-001/002 + BRU-SO-001) và trước submit. Chốt cứng vẫn ở DN.
    so.check_stock_availability()
    so.submit()
    so.reload()

    return {"order": so.name, "total_amount": flt(so.total_amount)}


def compute_milestones(order: str):
    """4 cột mốc theo dõi đơn hàng (GĐ3 Task 4 -- formalize từ bản provisional
    của Task 3): đặt hàng / giao & nghiệm thu / xuất hoá đơn / thanh toán.

    Mỗi mốc {key, label, status: done|current|pending, time}; mốc 2/3 (giao
    nghiệm thu / xuất hoá đơn) khi `done` có thêm {doctype, docname} trỏ tới
    SC Delivery Note/SC Sales Invoice tương ứng -- Portal UI (GĐ4 Task 3)
    dùng cặp này để gọi `portal_document_download(doctype, docname)` tải
    chứng từ; hàm đó tự kiểm tra lại quyền sở hữu nên không mở thêm rủi ro
    rò rỉ. Đi qua lần lượt
    4 mốc theo đúng thứ tự chuỗi nghiệp vụ (SO -> DN -> SI -> SR); mốc `pending`
    ĐẦU TIÊN gặp phải được đánh dấu `current`, các mốc sau đó (nếu có) vẫn giữ
    `pending`. Chỉ đọc (read-only), dùng `frappe.get_all`/`frappe.db.get_value`
    (không `get_doc`) và guard `None` ở mọi bước để chịu được chuỗi chưa đi
    hết (đơn mới đặt, chưa giao, chưa xuất HĐ, ...).

    Ngoại lệ: nếu SO ở trạng thái kết thúc KHÔNG tiến triển ("Từ chối") thì
    KHÔNG đánh dấu bất kỳ mốc nào là `current` -- các mốc sau mốc 1 vẫn giữ
    `pending` (không áp dụng/không còn ý nghĩa theo dõi), tránh Portal UI
    hiện nhầm hiệu ứng "đang xử lý" (pulsing current) trên 1 đơn đã bị từ
    chối."""
    so = frappe.db.get_value(
        "SC Sales Order", order, ["order_date", "creation", "status"], as_dict=True)

    milestones = [
        {"key": "placed", "label": "Đã đặt hàng", "status": "pending", "time": None},
        {"key": "delivered_accepted", "label": "Đã bàn giao & nghiệm thu", "status": "pending", "time": None},
        {"key": "invoiced", "label": "Đã cấp hóa đơn", "status": "pending", "time": None},
        {"key": "paid", "label": "Đã thu tiền", "status": "pending", "time": None},
    ]

    # Mốc 1 "placed": đơn đã tồn tại (luôn done -- portal_order_track đã xác
    # nhận đơn tồn tại + thuộc khách trước khi gọi hàm này).
    milestones[0]["status"] = "done"
    milestones[0]["time"] = (so.order_date or so.creation) if so else None

    # Mốc 2 "delivered_accepted": có SC Delivery Note của SO này đã nghiệm thu
    # (hoặc đã xuất HĐ, tức đã qua nghiệm thu từ trước).
    dn = frappe.db.get_value(
        "SC Delivery Note", {"sales_order": order, "docstatus": 1},
        ["name", "status", "modified"], order_by="creation", as_dict=True,
    )
    if dn and dn.status in ("Đã nghiệm thu", "Đã xuất HĐ"):
        milestones[1]["status"] = "done"
        milestones[1]["time"] = dn.modified
        # doctype/docname để Portal UI gọi `portal_document_download` tải
        # phiếu giao hàng -- không phải dữ liệu mới, chỉ trỏ tới đúng chứng
        # từ mà `portal_document_download` đã tự kiểm tra lại quyền sở hữu.
        milestones[1]["doctype"] = "SC Delivery Note"
        milestones[1]["docname"] = dn.name

    # Mốc 3 "invoiced": có SC Sales Invoice đã phát hành (docstatus=1 loại
    # trừ Nháp/Hủy) cho đúng Phiếu giao hàng ở mốc 2.
    si = None
    if dn:
        si = frappe.db.get_value(
            "SC Sales Invoice", {"delivery_note": dn.name, "docstatus": 1},
            ["name", "status", "invoice_date", "outstanding_amount"], order_by="creation", as_dict=True,
        )
    if si and si.status != "Nháp":
        milestones[2]["status"] = "done"
        milestones[2]["time"] = si.invoice_date
        milestones[2]["doctype"] = "SC Sales Invoice"
        milestones[2]["docname"] = si.name

        # Mốc 4 "paid": hóa đơn đã thu đủ (outstanding_amount <= 0); thời
        # điểm lấy từ phiếu thu gần nhất đã tất toán hóa đơn này.
        if flt(si.outstanding_amount) <= 0:
            last_receipt_date = frappe.db.get_value(
                "SC Sales Receipt", {"sales_invoice": si.name, "docstatus": 1},
                "receipt_date", order_by="creation desc",
            )
            milestones[3]["status"] = "done"
            milestones[3]["time"] = last_receipt_date

    # Đơn "Từ chối": KHÔNG có mốc nào là mốc "đang xử lý" tiếp theo -- chuỗi
    # nghiệp vụ đã dừng lại vĩnh viễn, các mốc chưa done giữ nguyên `pending`.
    is_rejected = bool(so and so.status == "Từ chối")

    if not is_rejected:
        found_current = False
        for m in milestones:
            if m["status"] == "pending" and not found_current:
                m["status"] = "current"
                found_current = True

    return milestones


@frappe.whitelist()
def portal_order_track(order):
    """Theo dõi 1 đơn hàng của khách đăng nhập. Đơn của khách khác -> PermissionError."""
    customer = _require_portal_customer()

    so_customer, so_status = frappe.db.get_value(
        "SC Sales Order", order, ["customer", "status"]) or (None, None)
    if not so_customer or so_customer != customer:
        frappe.throw(_("Không có quyền theo dõi đơn hàng này"), frappe.PermissionError)

    return {
        "order": order,
        "status": so_status,
        "milestones": compute_milestones(order),
    }


@frappe.whitelist()
def portal_order_history(limit=20, start=0):
    """Lịch sử đơn hàng của khách đăng nhập (phân trang)."""
    customer = _require_portal_customer()
    return frappe.get_all(
        "SC Sales Order", filters={"customer": customer},
        fields=["name", "order_date", "status", "total_amount"],
        order_by="creation desc",
        limit_page_length=cint(limit), limit_start=cint(start),
    )


@frappe.whitelist()
def portal_document_download(doctype, name):
    """Xuất bản in HTML (SC Sales Invoice / SC Delivery Note) của khách
    đăng nhập. Doctype ngoài danh sách cho phép -> throw (ValidationError,
    KHÔNG phải PermissionError -- lỗi tham số, không phải lỗi phân quyền).
    Chứng từ của khách khác -> PermissionError."""
    customer = _require_portal_customer()

    if doctype not in DOWNLOADABLE_DOCTYPES:
        frappe.throw(_("Loại tài liệu {0} không được phép tải xuống qua Portal").format(doctype))

    doc_customer = frappe.db.get_value(doctype, name, "customer")
    if not doc_customer or doc_customer != customer:
        frappe.throw(_("Không có quyền tải tài liệu này"), frappe.PermissionError)

    return {"html": frappe.get_print(doctype, name)}


# ===========================================================================
# GĐ MVL — Portal: giao nhận, nghiệm thu, hoá đơn, công nợ (bước 3 & 4)
# ===========================================================================

@frappe.whitelist()
def portal_deliveries(limit=20, start=0):
    """Danh sách Phiếu giao hàng của khách đăng nhập. Kèm biên bản nghiệm thu
    tương ứng (acceptance_ref) nếu đã có."""
    customer = _require_portal_customer()
    rows = frappe.get_all(
        "SC Delivery Note", filters={"customer": customer, "docstatus": 1},
        fields=["name", "delivery_date", "status", "sales_order", "acceptance_ref"],
        order_by="creation desc",
        limit_page_length=cint(limit), limit_start=cint(start),
    )
    return rows


@frappe.whitelist()
def portal_acceptance_records(limit=20, start=0):
    """Danh sách Biên bản nghiệm thu của khách đăng nhập."""
    customer = _require_portal_customer()
    return frappe.get_all(
        "SC Acceptance Record", filters={"customer": customer, "docstatus": 1},
        fields=["name", "delivery_note", "acceptance_date", "status", "accepted_by"],
        order_by="creation desc",
        limit_page_length=cint(limit), limit_start=cint(start),
    )


@frappe.whitelist()
def portal_invoices(limit=20, start=0):
    """Danh sách Hoá đơn bán của khách đăng nhập + công nợ từng hoá đơn."""
    customer = _require_portal_customer()
    return frappe.get_all(
        "SC Sales Invoice", filters={"customer": customer, "docstatus": 1},
        fields=["name", "invoice_date", "status", "grand_total", "outstanding_amount",
                "delivery_note"],
        order_by="creation desc",
        limit_page_length=cint(limit), limit_start=cint(start),
    )


@frappe.whitelist()
def portal_confirm_delivery(delivery_note, note=None):
    """KH TỰ xác nhận đã nhận hàng trên Portal (bước 3) → tạo + submit SC
    Acceptance Record. Chỉ cho phiếu giao của CHÍNH khách và đang ở "Đã giao".

    Portal role không có DocPerm create trên SC Acceptance Record (chỉ read) —
    tạo bằng ignore_permissions sau khi TỰ kiểm ownership + trạng thái; controller
    SC Acceptance Record vẫn enforce BRU (DN phải 'Đã giao', 1 biên bản/DN)."""
    customer = _require_portal_customer()

    dn = frappe.db.get_value("SC Delivery Note", delivery_note,
                             ["customer", "status"], as_dict=True)
    if not dn or dn.customer != customer:
        frappe.throw(_("Không có quyền xác nhận phiếu giao này"), frappe.PermissionError)
    if dn.status != "Đã giao":
        frappe.throw(_(
            "Phiếu giao {0} không ở trạng thái 'Đã giao' (hiện: {1}) — không thể xác nhận."
        ).format(delivery_note, dn.status))

    doc = frappe.new_doc("SC Acceptance Record")
    doc.delivery_note = delivery_note
    doc.acceptance_date = today()
    doc.accepted_by = frappe.db.get_value("SC Customer", customer, "customer_name")
    doc.note = note
    doc.flags.ignore_permissions = True
    doc.insert(ignore_permissions=True)
    doc.submit()
    return {"acceptance_record": doc.name, "delivery_note": delivery_note}


# ===========================================================================
# Thương mại điện tử: khách TỰ đăng ký + danh mục chung + đặt hàng lẻ
# ===========================================================================

@frappe.whitelist(allow_guest=True)
def portal_register(customer_name, email, password, phone=None, tax_code=None):
    """Khách vãng lai TỰ đăng ký: tạo tài khoản đăng nhập (Website User) +
    tự tạo SC Customer (Hoạt động, đã gắn Portal → thỏa BRU-CUS-001) + gán
    role Portal (khóa 1-1 BRU-CUS-002), rồi TỰ ĐĂNG NHẬP.

    Chạy dưới Guest nên tạo doc bằng ignore_permissions. Chỉ gán đúng
    PORTAL_ROLE (không cho leo thang role khác)."""
    customer_name = (customer_name or "").strip()
    email = (email or "").strip().lower()
    password = password or ""
    tax_code = (tax_code or "").strip() or None

    if not customer_name or not email or not password:
        frappe.throw(_("Vui lòng nhập đầy đủ Tên khách hàng, Email và Mật khẩu"))
    if not _EMAIL_RE.match(email):
        frappe.throw(_("Email không hợp lệ"))
    if len(password) < 6:
        frappe.throw(_("Mật khẩu tối thiểu 6 ký tự"))
    if frappe.db.exists("User", email):
        frappe.throw(_("Email {0} đã được đăng ký — vui lòng đăng nhập").format(email))
    if tax_code and frappe.db.exists("SC Customer", {"tax_code": tax_code}):
        frappe.throw(_("Mã số thuế {0} đã tồn tại trong hệ thống").format(tax_code))

    user = frappe.get_doc({
        "doctype": "User", "email": email, "first_name": customer_name,
        "user_type": "Website User", "send_welcome_email": 0, "new_password": password,
    })
    user.flags.ignore_permissions = True
    user.insert(ignore_permissions=True)
    user.add_roles(PORTAL_ROLE)
    if frappe.db.exists("Role", CUSTOMER_ROLE):
        user.add_roles(CUSTOMER_ROLE)  # nhãn 'Khách hàng' (kèm PORTAL_ROLE)

    cust = frappe.get_doc({
        "doctype": "SC Customer", "customer_name": customer_name,
        "tax_code": tax_code, "phone": (phone or "").strip() or None,
        "status": "Hoạt động", "portal_user": user.name, "credit_limit": 0,
    })
    cust.flags.ignore_permissions = True
    cust.insert(ignore_permissions=True)
    frappe.db.commit()

    # Tự đăng nhập: thiết lập session cho chính user vừa tạo.
    frappe.local.login_manager.login_as(user.name)
    return {"customer": cust.name, "user": user.name, "redirect": "/portal"}


@frappe.whitelist()
def portal_catalog_general():
    """Danh mục CHUNG (bán online) — mọi khách đã đăng nhập Portal đều xem
    được (không phụ thuộc hợp đồng). Chỉ hàng available_online=1 & giá > 0."""
    _require_portal_customer()  # chặn guest / non-portal
    return frappe.get_all(
        "SC Item",
        filters={"available_online": 1, "selling_price": [">", 0], "disabled": 0},
        fields=["name as item", "item_name", "uom", "selling_price"],
        order_by="item_name asc", limit_page_length=500,
    )


@frappe.whitelist()
def portal_order_place_general(items):
    """Đặt hàng lẻ từ danh mục chung: tạo SC Sales Order KHÔNG hợp đồng, giá
    lấy SERVER-SIDE từ SC Item.selling_price (không tin client), qty > 0, tự
    gắn đúng khách đang đăng nhập."""
    customer = _require_portal_customer()
    if isinstance(items, str):
        items = frappe.parse_json(items)
    if not items:
        frappe.throw(_("Chưa chọn mặt hàng nào"))

    lines = []
    for row in items:
        code = row.get("item")
        try:
            qty = flt(row.get("qty"))
        except (TypeError, ValueError):
            qty = 0
        if qty <= 0:
            frappe.throw(_("Số lượng phải > 0"))
        it = frappe.db.get_value(
            "SC Item", code,
            ["item_name", "uom", "selling_price", "available_online", "disabled"],
            as_dict=True)
        if not it or it.disabled or not it.available_online or flt(it.selling_price) <= 0:
            frappe.throw(_("Mặt hàng {0} không bán online").format(code))
        price = flt(it.selling_price)
        lines.append({"item": code, "uom": it.uom, "qty": qty,
                      "unit_price": price, "amount": qty * price})

    so = frappe.new_doc("SC Sales Order")
    so.customer = customer
    so.order_date = today()
    # KHÔNG gắn framework_contract → controller bỏ qua pricing HĐ, giữ giá đã set.
    for ln in lines:
        so.append("items", ln)
    so.flags.ignore_permissions = True
    so.insert()
    so.submit()
    so.reload()
    return {"order": so.name, "total_amount": flt(so.total_amount)}
