import frappe

DEFAULT_ROLES = [
    # Roles cũ
    "SupplyCore Manager",
    "SupplyCore User",
    "SupplyCore Auditor",
    "Warehouse Officer",
    "QC Officer",
    # Roles URS-aligned (mapping với SC-* code trong tài liệu)
    "SupplyCore Storekeeper",   # SC-STOREKEEPER
    "SupplyCore Accountant",    # SC-ACCOUNTANT
    "SupplyCore Executive",     # SC-EXECUTIVE
    "SupplyCore Purchaser",     # SC-PURCHASER
    "SC Customer Portal",       # M12 Portal khach hang — desk_access=0
]

# Roles khong co desk access (Portal / Website User only)
NO_DESK_ACCESS_ROLES = {"SC Customer Portal"}


def after_install():
    create_default_roles()


def create_default_roles():
    for role_name in DEFAULT_ROLES:
        if not frappe.db.exists("Role", role_name):
            frappe.get_doc({
                "doctype": "Role",
                "role_name": role_name,
                "desk_access": 0 if role_name in NO_DESK_ACCESS_ROLES else 1,
            }).insert(ignore_permissions=True)
    frappe.db.commit()
