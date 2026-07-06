"""SupplyCore — Access matrix cho FE.

Trả về 1 call duy nhất tại boot: module nào hiện, doctype nào đọc/ghi/tạo/submit
được, feature nào (data_io/users/putaway) bật. FE dùng để ẩn menu, gate route,
ẩn nút action — "không có phận sự thì không thấy".

API: supplycore.api.access.menu()
"""

from __future__ import annotations

import frappe


# ---------------------------------------------------------------------------
# Static role matrix — đồng bộ với ROLE_GUIDE trong users.py
# ---------------------------------------------------------------------------

# Mỗi module → role tối thiểu để xem (intersection: user có ≥ 1 role là OK).
# 'admin' là alias cho System Manager / SupplyCore Manager (luôn xem tất cả).
MODULE_ROLES: dict[str, list[str]] = {
    "m0":  ["System Manager", "SupplyCore Manager", "SupplyCore User",
            "SupplyCore Storekeeper", "SupplyCore Accountant",
            "Warehouse Officer", "SupplyCore Auditor"],
    "m1":  ["System Manager", "SupplyCore Manager", "SupplyCore Accountant",
            "SupplyCore Executive", "SupplyCore Purchaser", "SupplyCore Auditor"],
    "m2":  ["System Manager", "SupplyCore Manager", "SupplyCore Purchaser",
            "SupplyCore Auditor"],
    "m3":  ["System Manager", "SupplyCore Manager", "SupplyCore Storekeeper",
            "Warehouse Officer", "QC Officer", "SupplyCore Auditor"],
    "m4":  ["System Manager", "SupplyCore Manager", "SupplyCore Storekeeper",
            "Warehouse Officer", "SupplyCore Auditor"],
    "m5":  ["System Manager", "SupplyCore Manager",
            "QC Officer", "SupplyCore Storekeeper", "SupplyCore Auditor"],
    "m6":  ["System Manager", "SupplyCore Manager", "SupplyCore Storekeeper",
            "Warehouse Officer", "SupplyCore Auditor"],
    "m8":  ["System Manager", "SupplyCore Manager", "SupplyCore Accountant",
            "SupplyCore Auditor"],
    "m9":  ["System Manager", "SupplyCore Manager", "SupplyCore Storekeeper",
            "Warehouse Officer", "SupplyCore Auditor"],
    "m10": ["System Manager", "SupplyCore Manager", "SupplyCore Auditor",
            "QC Officer"],
    "m11": ["System Manager", "SupplyCore Manager", "SupplyCore Executive",
            "SupplyCore Auditor", "SupplyCore Accountant"],
}

# Feature flags — top-level page khác module
FEATURE_ROLES: dict[str, list[str]] = {
    # /dashboard, /alerts, /stock-balance — mọi role SC đều thấy
    "dashboard":     ["System Manager"] + list({r for v in MODULE_ROLES.values() for r in v}),
    "alerts":        ["System Manager", "SupplyCore Manager", "SupplyCore Auditor",
                       "Warehouse Officer", "QC Officer",
                       "SupplyCore Storekeeper"],
    "stock_balance": ["System Manager", "SupplyCore Manager", "SupplyCore Storekeeper",
                       "Warehouse Officer", "SupplyCore Auditor",
                       "SupplyCore Accountant"],
    "warehouses":    ["System Manager", "SupplyCore Manager", "SupplyCore Storekeeper",
                       "Warehouse Officer", "SupplyCore Auditor"],
    "putaway":       ["System Manager", "SupplyCore Manager", "SupplyCore Storekeeper",
                       "Warehouse Officer"],
    "data_io":       ["System Manager", "SupplyCore Manager", "SupplyCore Storekeeper",
                       "SupplyCore Accountant", "SupplyCore Auditor",
                       "Warehouse Officer",
                       "SupplyCore Purchaser"],
    "users":         ["System Manager", "SupplyCore Manager"],
    "financial_reports": ["System Manager", "SupplyCore Manager", "SupplyCore Executive",
                          "SupplyCore Accountant", "SupplyCore Auditor"],
    "batch_trace":   ["System Manager", "SupplyCore Manager", "SupplyCore Executive",
                       "SupplyCore Storekeeper", "Warehouse Officer", "QC Officer",
                       "SupplyCore Auditor"],
    "warehouse_map": ["System Manager", "SupplyCore Manager", "SupplyCore Storekeeper",
                       "Warehouse Officer",
                       "SupplyCore Auditor"],
    "map_editor":    ["System Manager", "SupplyCore Manager"],
}

# Doctype được FE quan tâm — dùng để batch-load permission
# Tránh fetch perm cho tất cả 200+ doctype Frappe — chỉ những doctype SC dùng.
TRACKED_DOCTYPES: list[str] = [
    # M0
    "SC Item", "SC Item Group", "SC UOM", "SC Supplier", "SC Warehouse",
    "Bin Location", "SC Department",
    "SC GL Account",
    # M1
    "Framework Contract",
    # M2
    "SC Material Request", "SC Purchase Order",
    # M3
    "SC Purchase Receipt", "SC Quality Inspection",
    # M4
    "SC Batch", "SC Stock Ledger Entry",
    # M6
    "SC Transfer Request", "SC Stock Entry",
    # M8
    "SC Purchase Invoice", "SC Payment Entry", "SC GL Entry",
    # M9
    "SC Inventory Count Sheet", "SC Stock Reconciliation",
    # M10
    "SC Recall Notice", "SC Investigation Report",
    # M11
    "SC Alert", "SC Alert Rule",
]


def _has_any(user_roles: set[str], required: list[str]) -> bool:
    return bool(user_roles.intersection(required))


@frappe.whitelist()
def menu() -> dict:
    """Ma trận quyền cho user hiện tại. Gọi 1 lần tại boot, cache ở FE."""
    user = frappe.session.user
    user_roles = set(frappe.get_roles(user))

    is_admin = "System Manager" in user_roles or "SupplyCore Manager" in user_roles

    modules = {m: _has_any(user_roles, roles) for m, roles in MODULE_ROLES.items()}
    features = {k: _has_any(user_roles, roles) for k, roles in FEATURE_ROLES.items()}

    # Doctype perms — batch
    doctypes: dict[str, dict] = {}
    for dt in TRACKED_DOCTYPES:
        try:
            if not frappe.db.exists("DocType", dt):
                continue
            meta = frappe.get_meta(dt)
            doctypes[dt] = {
                "read":   1 if frappe.has_permission(dt, "read", user=user) else 0,
                "write":  1 if frappe.has_permission(dt, "write", user=user) else 0,
                "create": 1 if frappe.has_permission(dt, "create", user=user) else 0,
                "submit": 1 if (meta.is_submittable and
                                  frappe.has_permission(dt, "submit", user=user)) else 0,
                "cancel": 1 if (meta.is_submittable and
                                  frappe.has_permission(dt, "cancel", user=user)) else 0,
                "delete": 1 if frappe.has_permission(dt, "delete", user=user) else 0,
                "is_submittable": int(meta.is_submittable or 0),
            }
        except Exception:
            # Nếu lỗi (doctype mới chưa migrate, v.v.) → coi như no access
            doctypes[dt] = {"read": 0, "write": 0, "create": 0, "submit": 0,
                             "cancel": 0, "delete": 0, "is_submittable": 0}

    return {
        "user": user,
        "roles": sorted(user_roles),
        "is_admin": int(is_admin),
        "modules": modules,
        "features": features,
        "doctypes": doctypes,
    }
