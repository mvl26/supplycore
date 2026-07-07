"""API Portal khách hàng -- M12 Customer Portal (GĐ3).

Task 1 (GĐ3): provisioning tài khoản Portal cho SC Customer. Các API còn
lại (portal_me, portal_contracts, portal_catalog, portal_order_place,
portal_order_track, portal_order_history, portal_document_download) sẽ
được bổ sung ở Task 3.
"""

import frappe
from frappe import _

PORTAL_ROLE = "SC Customer Portal"
PROVISION_ROLES = {"System Manager", "SupplyCore Manager", "SupplyCore Purchaser"}


@frappe.whitelist()
def portal_provision(customer, email):
    """Cấp tài khoản Portal cho SC Customer.

    Tạo (hoặc lấy) Website User theo `email`, gán role "SC Customer Portal",
    và link vào `SC Customer.portal_user`. Chỉ System Manager / SupplyCore
    Manager / SupplyCore Purchaser mới được gọi.
    """
    roles = set(frappe.get_roles(frappe.session.user))
    if not (roles & PROVISION_ROLES):
        frappe.throw(_("Không có quyền cấp tài khoản Portal"), frappe.PermissionError)

    customer_doc = frappe.get_doc("SC Customer", customer)
    if customer_doc.portal_user:
        return customer_doc.portal_user

    if frappe.db.exists("User", email):
        user_doc = frappe.get_doc("User", email)
    else:
        user_doc = frappe.get_doc({
            "doctype": "User",
            "email": email,
            "first_name": customer_doc.customer_name,
            "user_type": "Website User",
            "send_welcome_email": 0,
        }).insert(ignore_permissions=True)

    user_doc.add_roles(PORTAL_ROLE)

    frappe.db.set_value("SC Customer", customer, "portal_user", email)

    return email
