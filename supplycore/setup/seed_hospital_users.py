"""Tạo 6 tài khoản chức danh bệnh viện thực tế (BV pilot).

Mỗi tài khoản 1 Frappe role chính → resolvePersona() tự nhận đúng persona UI.

Lưu ý: "Trưởng phòng Vật tư" và "NV Mua sắm" cùng dùng Frappe role
`SupplyCore Manager` → cả hai login sẽ thấy persona Lan (Trưởng phòng).
Hệ thống đã bỏ persona switcher (2026-05-25) nên không tách view được.

Chạy: bench --site supplycore execute supplycore.setup.seed_hospital_users.run
"""

import frappe


HOSPITAL_USERS = [
    # (email, full_name, first_name, role, password)
    ("truongphong.vattu@bv.local",  "Trưởng phòng Vật tư",   "Trưởng phòng VT",
     "SupplyCore Manager",     "BvVattu@2026"),
    ("nv.muasam@bv.local",          "NV Mua sắm",             "NV Mua sắm",
     "SupplyCore Manager",     "BvMuasam@2026"),
    ("thukho.trungtam@bv.local",    "Thủ kho Trung tâm",      "Thủ kho TT",
     "SupplyCore Storekeeper", "BvKho@2026"),
    ("dieuduong.truong@bv.local",   "Điều dưỡng trưởng",      "Điều dưỡng",
     "SupplyCore Ward Staff",  "BvDieuduong@2026"),
    ("ketoan.thanhtoan@bv.local",   "Kế toán Thanh toán",     "Kế toán TT",
     "SupplyCore Accountant",  "BvKetoan@2026"),
    ("duocsi.qc@bv.local",          "Dược sĩ / KCS",           "Dược sĩ QC",
     "Pharmacy Officer",       "BvDuocsi@2026"),
]


def run() -> dict:
    created = []
    updated = []
    for email, full_name, first_name, role, password in HOSPITAL_USERS:
        if frappe.db.exists("User", email):
            u = frappe.get_doc("User", email)
            u.set("roles", [])
            u.append("roles", {"role": role})
            u.first_name = first_name
            u.full_name = full_name
            u.enabled = 1
            u.flags.ignore_permissions = True
            u.save()
            updated.append(email)
        else:
            u = frappe.new_doc("User")
            u.email = email
            u.first_name = first_name
            u.full_name = full_name
            u.enabled = 1
            u.send_welcome_email = 0
            u.new_password = password
            u.user_type = "System User"
            u.append("roles", {"role": role})
            u.flags.ignore_permissions = True
            u.insert()
            created.append(email)

    # Force-set password (đảm bảo khớp dù user đã tồn tại)
    from frappe.utils.password import update_password
    for email, _, _, _, password in HOSPITAL_USERS:
        try:
            update_password(email, password)
        except Exception as e:
            frappe.log_error(f"update_password failed for {email}: {e}",
                             "seed_hospital_users")

    frappe.db.commit()
    return {
        "created": created,
        "updated": updated,
        "total": len(HOSPITAL_USERS),
        "credentials": [
            {"email": e, "name": fn, "role": r, "password": p}
            for e, fn, _, r, p in HOSPITAL_USERS
        ],
    }
