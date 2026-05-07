import frappe

DEFAULT_ROLES = [
    # Roles cũ
    "SupplyCore Manager",
    "SupplyCore User",
    "SupplyCore Auditor",
    "Warehouse Officer",
    "QC Officer",
    "Pharmacy Officer",
    "BHYT Officer",
    "Department Requester",
    # Roles URS-aligned (mapping với SC-* code trong tài liệu)
    "SupplyCore Storekeeper",   # SC-STOREKEEPER
    "SupplyCore Ward Staff",    # SC-WARD-STAFF
    "SupplyCore Accountant",    # SC-ACCOUNTANT
    "SupplyCore Executive",     # SC-EXECUTIVE
    "SupplyCore Purchaser",     # SC-PURCHASER
]


def after_install():
    create_default_roles()


def create_default_roles():
    for role_name in DEFAULT_ROLES:
        if not frappe.db.exists("Role", role_name):
            frappe.get_doc({
                "doctype": "Role",
                "role_name": role_name,
                "desk_access": 1,
            }).insert(ignore_permissions=True)
    frappe.db.commit()
