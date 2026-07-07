"""Patch: đổi tên kho/phòng ban bệnh viện còn sót trong DB sang MVL phân phối
(GĐ4 Task 1 — rebrand Miyano).

Bối cảnh: seed_master_data.py (patch v0_2, đã chạy 1 lần) tạo warehouse/
department bệnh viện ("Kho Tổng Bệnh viện", "Khoa Cấp cứu"...). Sửa source
seed không tự re-run trên site đã migrate — patch này rename các bản ghi
ĐANG CÓ trong DB, dùng frappe.rename_doc để cascade toàn bộ Link field
(SC Warehouse.department, SC Warehouse.parent_warehouse, SC Transfer Request,
SC Material Request, SC Recall Affected Item...).

Idempotent — bỏ qua nếu tên cũ không còn hoặc tên mới đã tồn tại.
"""

import frappe
from frappe.model.rename_doc import rename_doc as _rename_doc_impl

# (old, new) — khớp seed_master_data.py sau rebrand
WAREHOUSE_RENAMES = [
    ("Kho Tổng Bệnh viện", "Kho Tổng MVL"),
    ("Kho Khoa Cấp cứu", "Kho Phòng Kinh doanh"),
    ("Kho Khoa ICU", "Kho Phòng Mua hàng"),
    ("Kho Khoa Nội tổng hợp", "Kho Phòng Kế toán"),
    ("Kho Khoa Ngoại tổng hợp", "Kho Phòng Marketing"),
    ("Kho Khoa Sản", "Kho Phòng Nhân sự"),
    ("Kho Khoa Nhi", "Kho Phòng CSKH"),
    ("Kho Phòng Mổ", "Kho Phòng QC"),
    ("Kho Khoa Dược", "Kho Giao hàng"),
]

DEPARTMENT_RENAMES = [
    ("Khoa Cấp cứu", "Phòng Kinh doanh"),
    ("Khoa Hồi sức tích cực", "Phòng Mua hàng"),
    ("Khoa Nội tổng hợp", "Phòng Kế toán"),
    ("Khoa Ngoại tổng hợp", "Phòng Marketing"),
    ("Khoa Sản", "Phòng Nhân sự"),
    ("Khoa Nhi", "Phòng Chăm sóc khách hàng"),
    ("Phòng Mổ", "Phòng QC - Chất lượng"),
    ("Khoa Dược", "Phòng Giao nhận"),
]

# Khoa lâm sàng/cận lâm sàng còn sót — không còn dùng trong seed MVL (không
# tied tới warehouse nào). Xoá nếu mồ côi (không bị Link ràng buộc); bỏ qua
# nếu đang được transaction nào tham chiếu (LinkExistsError).
ORPHAN_HOSPITAL_DEPARTMENTS = [
    "Khoa Tim mạch", "Khoa Tiêu hóa", "Khoa Thần kinh", "Khoa Mắt",
    "Khoa Tai Mũi Họng", "Khoa Răng Hàm Mặt", "Khoa Da liễu", "Khoa Truyền nhiễm",
    "Khoa Y học cổ truyền", "Khoa Chấn thương chỉnh hình", "Khoa Ung bướu",
    "Khoa Phục hồi chức năng", "Khoa Chẩn đoán hình ảnh", "Khoa Xét nghiệm",
    "Khoa Vi sinh", "Khoa Giải phẫu bệnh", "Khoa Thăm dò chức năng",
    "Khoa Gây mê hồi sức", "Phòng Vật tư - TTBYT", "Phòng Khám tổng hợp",
    "Phòng Kế hoạch tổng hợp", "Phòng Tài chính kế toán", "Phòng Tổ chức cán bộ",
]

OLD_SITE_NAME = "Bệnh viện Y học cổ truyền Bộ Công an"
NEW_SITE_NAME = "Công ty Miyano Việt Nam"
OLD_SITE_ADDRESS_HINT = "Hà Đông"
NEW_SITE_ADDRESS = "Hà Nội, Việt Nam"


def _rename(doctype: str, old: str, new: str) -> str | None:
    if not frappe.db.exists(doctype, old):
        return None
    if frappe.db.exists(doctype, new):
        return None  # đích đã tồn tại — coi như đã rename trước đó
    try:
        _rename_doc_impl(doctype=doctype, old=old, new=new, force=True,
                          ignore_permissions=True, show_alert=False)
        frappe.db.commit()
        return new
    except Exception as e:
        frappe.log_error(message=f"rebrand_miyano: rename {doctype} '{old}'→'{new}' fail: {e}",
                          title="MVL GĐ4 Task 1")
        return None


def execute():
    result = {"warehouse_renamed": [], "department_renamed": [],
              "department_deleted": [], "settings_updated": False}

    # Đổi department trước (warehouse.department field sẽ theo bằng cascade
    # link update của rename_doc; đổi trước để _rename warehouse khỏi phụ
    # thuộc thứ tự).
    for old, new in DEPARTMENT_RENAMES:
        r = _rename("SC Department", old, new)
        if r:
            result["department_renamed"].append(r)

    for old, new in WAREHOUSE_RENAMES:
        r = _rename("SC Warehouse", old, new)
        if r:
            result["warehouse_renamed"].append(r)

    for name in ORPHAN_HOSPITAL_DEPARTMENTS:
        if not frappe.db.exists("SC Department", name):
            continue
        try:
            frappe.delete_doc("SC Department", name, force=True,
                               ignore_missing=True)
            frappe.db.commit()
            result["department_deleted"].append(name)
        except Exception as e:
            frappe.log_error(message=f"rebrand_miyano: không xoá được dept mồ côi {name}: {e}",
                              title="MVL GĐ4 Task 1")

    # Settings — chỉ ghi đè nếu vẫn còn giá trị mặc định bệnh viện (không
    # đụng nếu user đã tùy chỉnh tên/địa chỉ khác trên site).
    if frappe.db.exists("DocType", "SupplyCore Settings"):
        s = frappe.get_single("SupplyCore Settings")
        changed = False
        if (s.get("site_name") or "") == OLD_SITE_NAME:
            s.site_name = NEW_SITE_NAME
            changed = True
        if OLD_SITE_ADDRESS_HINT in (s.get("site_address") or ""):
            s.site_address = NEW_SITE_ADDRESS
            changed = True
        if changed:
            s.flags.ignore_permissions = True
            s.save()
            frappe.db.commit()
            result["settings_updated"] = True

    return result
