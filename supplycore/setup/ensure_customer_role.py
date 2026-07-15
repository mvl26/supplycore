"""Role 'Khách hàng' — nhãn khách hàng cổng (GĐ MVL).

Theo quyết định vận hành: 'Khách hàng' là role NHÃN hiển thị trong Quyền & Người
dùng, gán KÈM 'SC Customer Portal'. Role chức năng thực sự (cách ly dữ liệu, cho
thao tác cổng) vẫn là 'SC Customer Portal' — mọi phân quyền gắn cứng vào role đó.
'Khách hàng' KHÔNG cấp DocPerm nào (thuần nhãn) nên không tạo lỗ hổng rò rỉ chéo.

Idempotent: tạo role nếu thiếu + gán 'Khách hàng' cho mọi user đang có
'SC Customer Portal'. Chạy: bench --site <site> execute
supplycore.setup.ensure_customer_role.run
"""

import frappe

CUSTOMER_ROLE = "Khách hàng"
PORTAL_ROLE = "SC Customer Portal"


def run() -> dict:
    # 1) Tạo role nhãn (desk_access=0: website user, không vào Desk).
    if not frappe.db.exists("Role", CUSTOMER_ROLE):
        role = frappe.new_doc("Role")
        role.role_name = CUSTOMER_ROLE
        role.desk_access = 0
        role.flags.ignore_permissions = True
        role.insert()

    # 2) Gán 'Khách hàng' cho mọi user đang có 'SC Customer Portal'.
    users = set(frappe.get_all("Has Role", filters={"role": PORTAL_ROLE}, pluck="parent"))
    assigned = 0
    for u in users:
        if not frappe.db.exists("Has Role", {"parent": u, "role": CUSTOMER_ROLE}):
            doc = frappe.get_doc("User", u)
            doc.add_roles(CUSTOMER_ROLE)
            assigned += 1

    frappe.db.commit()
    return {"role": CUSTOMER_ROLE, "portal_users": len(users), "newly_assigned": assigned}
