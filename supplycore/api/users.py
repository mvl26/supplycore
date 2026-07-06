"""SupplyCore — Quản lý người dùng & phân quyền.

API path: supplycore.api.users.*

- list_roles()        — danh sách role có hướng dẫn (chức năng + giới hạn) tiếng Việt
- list_users()        — bảng user hệ thống + role + trạng thái
- get_user(name)      — chi tiết 1 user (cho form sửa)
- create_user(...)    — tạo user mới + gán role
- update_user_roles() — set lại danh sách role của 1 user
- set_user_enabled()  — bật/tắt user
- reset_password()    — gửi link đặt lại mật khẩu

Quyền gọi: chỉ "System Manager" hoặc "SupplyCore Manager".
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cint
from frappe.utils.password import update_password


# ---------------------------------------------------------------------------
# Role guide — chức năng + giới hạn cho người phân quyền
# ---------------------------------------------------------------------------

# vn_name = tên hiển thị tiếng Việt
# scope = phạm vi hoạt động chính
# duties = chức năng được làm (bullets)
# limits = giới hạn / điều cấm (bullets)
# modules = các module dùng nhiều
# danger_level = "high" hiện badge đỏ (System Manager etc.), "medium" vàng, "low" xanh
ROLE_GUIDE: dict[str, dict] = {
    "System Manager": {
        "vn_name": "Quản trị Frappe (siêu quyền)",
        "scope": "Toàn bộ Frappe + ERPNext + SupplyCore",
        "duties": [
            "Tạo / sửa / xoá MỌI DocType, user, role",
            "Cấu hình hệ thống, fixtures, hooks",
            "Truy cập tất cả dữ liệu, không bị filter",
        ],
        "limits": [
            "⚠ Cấp tối cao — chỉ admin IT mới được gán",
            "Hành động bị log đầy đủ trong Audit Log",
            "Không có giới hạn nào về dữ liệu — gán cho sai người = mất kiểm soát",
        ],
        "modules": ["ALL"],
        "danger_level": "high",
    },
    "SupplyCore Manager": {
        "vn_name": "Quản lý hệ thống SupplyCore",
        "scope": "Toàn bộ 11 module SupplyCore",
        "duties": [
            "Duyệt hợp đồng khung (Framework Contract), PO giá trị lớn",
            "Cấu hình rule alert, FEFO, putaway",
            "Truy cập Dashboard + tất cả báo cáo KPI",
            "Quản lý người dùng + phân quyền cấp module",
        ],
        "limits": [
            "Không thay thế role System Manager (admin Frappe)",
            "Không trực tiếp sửa SLE/GL Entry — chỉ qua voucher",
            "Mọi hành động duyệt được ghi audit",
        ],
        "modules": ["M1", "M2", "M3", "M4", "M5", "M6", "M7", "M8", "M9", "M10", "M11"],
        "danger_level": "medium",
    },
    "SupplyCore User": {
        "vn_name": "Người dùng SupplyCore (cơ bản)",
        "scope": "Đọc dữ liệu chung + thao tác nghiệp vụ cơ bản",
        "duties": [
            "Đọc danh sách Item, Supplier, Warehouse",
            "Tạo / sửa các phiếu nghiệp vụ cấp Draft",
            "Xem báo cáo cá nhân",
        ],
        "limits": [
            "Không duyệt/submit hợp đồng, PO, PI",
            "Không cấu hình rule/alert",
            "Không quản lý user khác",
        ],
        "modules": ["M0", "M3", "M4", "M6"],
        "danger_level": "low",
    },
    "SupplyCore Auditor": {
        "vn_name": "Kiểm toán SupplyCore",
        "scope": "Chỉ đọc — toàn bộ dữ liệu lịch sử",
        "duties": [
            "Xem mọi DocType + Audit Log",
            "Xuất báo cáo, dữ liệu lịch sử",
            "Đánh giá compliance, lập biên bản kiểm tra",
        ],
        "limits": [
            "🛡 KHÔNG được tạo / sửa / xoá bất kỳ bản ghi nào",
            "Không submit / cancel / amend",
            "Phù hợp cho kiểm toán nội bộ hoặc thanh tra",
        ],
        "modules": ["M1", "M2", "M3", "M8", "M9", "M10", "M11"],
        "danger_level": "low",
    },
    "SupplyCore Storekeeper": {
        "vn_name": "Thủ kho",
        "scope": "M3 Nhập, M4 Kho, M5 FEFO, M6 Chuyển kho",
        "duties": [
            "Tạo Phiếu nhập (PR) từ PO",
            "Xếp hàng lên kệ (Putaway), phân bin",
            "Tạo / submit Phiếu chuyển kho (SE)",
            "Truy cập tồn kho tất cả warehouse được gán",
        ],
        "limits": [
            "Không tạo / sửa Item, Supplier",
            "Không duyệt PO, hợp đồng",
            "Không đụng vào kế toán (M8) / cấp phát BN (M7)",
            "Bị filter theo warehouse được gán (permission_query_conditions)",
        ],
        "modules": ["M3", "M4", "M5", "M6", "M9"],
        "danger_level": "low",
    },
    "SupplyCore Accountant": {
        "vn_name": "Kế toán",
        "scope": "M8 Kế toán, M1 hợp đồng, đọc M2 PO",
        "duties": [
            "Tạo / submit Hoá đơn mua (PI), Payment Entry",
            "Đối soát 3-way match (PO ↔ PR ↔ PI)",
            "Truy cập GL Entry, sổ kế toán",
            "Đọc Framework Contract để khớp giá",
        ],
        "limits": [
            "Không trực tiếp sửa SLE — chỉ qua voucher",
            "Không thay đổi master Item / Supplier",
            "Payment > 50tr cần duyệt thêm bởi Manager",
            "Không cấp phát BN, không kiểm kê",
        ],
        "modules": ["M8", "M1"],
        "danger_level": "medium",
    },
    "SupplyCore Executive": {
        "vn_name": "Lãnh đạo / Phê duyệt cấp cao",
        "scope": "Dashboard + duyệt phiếu giá trị lớn",
        "duties": [
            "Duyệt cấp 2 cho hợp đồng / PO giá trị lớn",
            "Xem Dashboard KPI tổng hợp toàn bệnh viện",
            "Đọc báo cáo điều hành (M11)",
        ],
        "limits": [
            "Không tạo phiếu nghiệp vụ trực tiếp",
            "Chỉ duyệt khi có recommendation từ Manager",
            "Không truy cập chi tiết cấp phát BN",
        ],
        "modules": ["M1", "M2", "M11"],
        "danger_level": "medium",
    },
    "SupplyCore Purchaser": {
        "vn_name": "Cán bộ mua hàng",
        "scope": "M2 Lập kế hoạch & mua, đọc M1 hợp đồng",
        "duties": [
            "Tạo Material Request, Purchase Order",
            "Gửi PO cho NCC (Send to Supplier)",
            "Đọc Framework Contract để khớp giá + remaining_value",
            "Theo dõi tình trạng PO",
        ],
        "limits": [
            "Không submit PO > ngưỡng giá trị (cần Manager)",
            "Không sửa Framework Contract đã duyệt",
            "Không cấp phát / kiểm kê / kế toán",
        ],
        "modules": ["M2", "M1"],
        "danger_level": "low",
    },
    "Warehouse Officer": {
        "vn_name": "Phụ trách kho (vận hành)",
        "scope": "M4 WMS, M6 Chuyển kho, hỗ trợ M3",
        "duties": [
            "Quản lý bin location, putaway rule",
            "Phối hợp với Storekeeper khi nhập / chuyển kho",
            "Đọc tồn kho realtime",
        ],
        "limits": [
            "Không tạo Item / Supplier mới",
            "Không duyệt PO / PI",
            "Bị filter theo warehouse được gán",
        ],
        "modules": ["M3", "M4", "M5", "M6"],
        "danger_level": "low",
    },
    "QC Officer": {
        "vn_name": "Cán bộ kiểm tra chất lượng (QC)",
        "scope": "M3 Quality Inspection, M4 batch quarantine",
        "duties": [
            "Lấy mẫu + ghi nhận kết quả QI cho batch nhập kho",
            "Quyết định Accept / Reject / Conditional",
            "Khoá batch hỏng (blocked)",
        ],
        "limits": [
            "Không sửa kết quả QI đã submit (chỉ amend qua Manager)",
            "Không cấp phát / chuyển kho",
            "Không truy cập kế toán",
        ],
        "modules": ["M3", "M4", "M5"],
        "danger_level": "low",
    },
}


# ---------------------------------------------------------------------------
# Permission gate
# ---------------------------------------------------------------------------

def _require_user_admin():
    """Chỉ System Manager hoặc SupplyCore Manager mới được dùng API user-mgmt."""
    user_roles = set(frappe.get_roles())
    if "System Manager" in user_roles or "SupplyCore Manager" in user_roles:
        return
    frappe.throw(_("Chỉ System Manager hoặc SupplyCore Manager mới được quản lý user"),
                 frappe.PermissionError)


# ---------------------------------------------------------------------------
# Role guide
# ---------------------------------------------------------------------------

@frappe.whitelist()
def list_roles() -> list[dict]:
    """Trả role guide. UI render checkboxes + giải thích."""
    _require_user_admin()
    out = []
    for role_name, g in ROLE_GUIDE.items():
        exists = bool(frappe.db.exists("Role", role_name))
        out.append({
            "role": role_name,
            "vn_name": g["vn_name"],
            "scope": g["scope"],
            "duties": g["duties"],
            "limits": g["limits"],
            "modules": g["modules"],
            "danger_level": g["danger_level"],
            "available": int(exists),
        })
    return out


# ---------------------------------------------------------------------------
# List + get user
# ---------------------------------------------------------------------------

def _user_to_row(u: dict) -> dict:
    roles = frappe.db.sql("""
        SELECT role FROM `tabHas Role`
        WHERE parent = %s AND parenttype = 'User'
        ORDER BY role
    """, u["name"], as_dict=True)
    return {
        "name": u["name"],
        "email": u.get("email") or u["name"],
        "full_name": u.get("full_name") or "",
        "enabled": int(u.get("enabled") or 0),
        "user_type": u.get("user_type") or "",
        "last_login": u.get("last_login"),
        "creation": u.get("creation"),
        "roles": [r["role"] for r in roles],
        "sc_roles": [r["role"] for r in roles if r["role"] in ROLE_GUIDE],
    }


@frappe.whitelist()
def list_users(search: str = "", limit: int = 100, only_supplycore: int = 1) -> list[dict]:
    _require_user_admin()
    conds = ["u.user_type != 'Website User'"]
    params: dict = {}
    if search:
        conds.append("(u.name LIKE %(q)s OR u.full_name LIKE %(q)s OR u.email LIKE %(q)s)")
        params["q"] = f"%{search}%"
    if cint(only_supplycore):
        # Chỉ user có ít nhất 1 role thuộc ROLE_GUIDE (hoặc Administrator)
        sc_roles_in = ", ".join(["%s"] * len(ROLE_GUIDE))
        conds.append(f"""(u.name = 'Administrator' OR EXISTS (
            SELECT 1 FROM `tabHas Role` hr
            WHERE hr.parent = u.name AND hr.parenttype = 'User'
              AND hr.role IN ({sc_roles_in})))""")

    sql = f"""
        SELECT u.name, u.email, u.full_name, u.enabled, u.user_type,
               u.last_login, u.creation
        FROM `tabUser` u
        WHERE {' AND '.join(conds)}
        ORDER BY u.enabled DESC, u.creation DESC
        LIMIT {cint(limit) or 100}
    """
    if cint(only_supplycore):
        rows = frappe.db.sql(sql, tuple(ROLE_GUIDE.keys()) + tuple(params.values()) if params else tuple(ROLE_GUIDE.keys()), as_dict=True)
    else:
        rows = frappe.db.sql(sql, params, as_dict=True)
    return [_user_to_row(r) for r in rows]


@frappe.whitelist()
def get_user(name: str) -> dict:
    _require_user_admin()
    if not frappe.db.exists("User", name):
        frappe.throw(_("User không tồn tại"))
    u = frappe.db.get_value("User", name,
        ["name", "email", "full_name", "enabled", "user_type", "last_login", "creation"],
        as_dict=True)
    return _user_to_row(u)


# ---------------------------------------------------------------------------
# Create / update
# ---------------------------------------------------------------------------

@frappe.whitelist()
def create_user(email: str, full_name: str, roles=None,
                 password: str = "", send_welcome: int | str = 0,
                 user_type: str = "System User") -> dict:
    """Tạo user mới + gán role."""
    _require_user_admin()
    if not email or "@" not in email:
        frappe.throw(_("Email không hợp lệ"))
    if frappe.db.exists("User", email):
        frappe.throw(_("Email {0} đã tồn tại").format(email))

    if isinstance(roles, str):
        import json
        roles = json.loads(roles)
    roles = roles or []
    # Lọc role không hợp lệ
    valid = [r for r in roles if frappe.db.exists("Role", r)]
    invalid = [r for r in roles if r not in valid]
    if invalid:
        frappe.msgprint(_("Bỏ qua role không tồn tại: {0}").format(", ".join(invalid)))

    # BUG-008: tách full_name → first_name + last_name (+ middle_name nếu có)
    # vì Frappe User auto-compute full_name = first + middle + last; chỉ set
    # first_name = bị mất phần còn lại (vd "Nguyễn Thị Thu Hương" → "Nguyễn").
    parts = (full_name or email.split("@")[0]).strip().split()
    if len(parts) >= 3:
        first, middle, last = parts[0], " ".join(parts[1:-1]), parts[-1]
    elif len(parts) == 2:
        first, middle, last = parts[0], "", parts[1]
    else:
        first, middle, last = parts[0] if parts else email.split("@")[0], "", ""

    doc = frappe.get_doc({
        "doctype": "User",
        "email": email,
        "first_name": first,
        "middle_name": middle,
        "last_name": last,
        "send_welcome_email": cint(send_welcome),
        "user_type": user_type,
        "enabled": 1,
        "roles": [{"role": r} for r in valid],
    })
    doc.insert(ignore_permissions=False)
    if password:
        update_password(email, password)
    frappe.db.commit()
    return _user_to_row({
        "name": doc.name, "email": doc.email, "full_name": doc.full_name,
        "enabled": 1, "user_type": doc.user_type,
        "last_login": None, "creation": doc.creation,
    })


@frappe.whitelist()
def update_user_roles(name: str, roles=None) -> dict:
    """Set lại toàn bộ SupplyCore roles của user (giữ nguyên các role khác)."""
    _require_user_admin()
    if not frappe.db.exists("User", name):
        frappe.throw(_("User không tồn tại"))
    if name == "Administrator":
        frappe.throw(_("Không được sửa role của Administrator qua giao diện này"))

    if isinstance(roles, str):
        import json
        roles = json.loads(roles)
    target_sc = set(r for r in (roles or []) if r in ROLE_GUIDE)

    doc = frappe.get_doc("User", name)
    # Lấy role hiện tại không nằm trong ROLE_GUIDE → giữ nguyên
    non_sc = [r.role for r in doc.roles if r.role not in ROLE_GUIDE]
    new_role_list = sorted(set(non_sc) | target_sc)
    # Xoá toàn bộ + add lại theo new_role_list
    doc.set("roles", [])
    for r in new_role_list:
        if frappe.db.exists("Role", r):
            doc.append("roles", {"role": r})
    doc.save(ignore_permissions=False)
    frappe.db.commit()
    return _user_to_row({
        "name": doc.name, "email": doc.email, "full_name": doc.full_name,
        "enabled": doc.enabled, "user_type": doc.user_type,
        "last_login": doc.last_login, "creation": doc.creation,
    })


@frappe.whitelist()
def set_user_enabled(name: str, enabled: int | str) -> dict:
    _require_user_admin()
    if not frappe.db.exists("User", name):
        frappe.throw(_("User không tồn tại"))
    if name == "Administrator":
        frappe.throw(_("Không được vô hiệu hoá Administrator"))
    doc = frappe.get_doc("User", name)
    doc.enabled = cint(enabled)
    doc.save(ignore_permissions=False)
    frappe.db.commit()
    return {"name": name, "enabled": doc.enabled}


@frappe.whitelist()
def reset_password(name: str) -> dict:
    """Gửi email reset password cho user."""
    _require_user_admin()
    if not frappe.db.exists("User", name):
        frappe.throw(_("User không tồn tại"))
    if name == "Administrator":
        frappe.throw(_("Không reset Administrator qua đây"))
    user = frappe.get_doc("User", name)
    try:
        link = user.reset_password(send_email=True)
        return {"ok": 1, "link": link}
    except Exception as e:
        frappe.throw(_("Không gửi được email: {0}").format(e))
