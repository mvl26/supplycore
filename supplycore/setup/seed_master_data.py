"""Seed master data đặc thù bệnh viện Việt Nam.

Idempotent: chạy lại không trùng. Gọi qua patch v0_2 hoặc bench execute thủ công:
  bench --site <site> execute supplycore.setup.seed_master_data.run

Bao gồm:
  - SC UOM         : 18 đơn vị tính y tế phổ biến
  - SC Item Group  : 6 nhóm gốc + ~20 nhóm con
  - SC Department  : 30+ khoa/phòng cấp BV quận-huyện
  - SC Warehouse   : Kho Tổng → 5 kho con + 8 kho khoa (3-tier)
  - SC Supplier    : 8 NCC tiêu biểu (đa quốc gia + nội địa)
  - SC Item        : 12 vật tư y tế mẫu mỗi nhóm chính
"""

import frappe
from frappe.utils import today


# ---------------------------------------------------------------------------
# 1. SC UOM
# ---------------------------------------------------------------------------
UOMS = [
    ("Cái",    "c",    1),  # must_be_whole_number
    ("Chiếc",  "chc",  1),
    ("Hộp",    "hộp",  1),
    ("Lọ",     "lọ",   1),
    ("Vỉ",     "vỉ",   1),
    ("Viên",   "vi",   1),
    ("Túi",    "túi",  1),
    ("Cuộn",   "cuộn", 1),
    ("Đôi",    "đôi",  1),
    ("Bộ",     "bộ",   1),
    ("Thùng",  "th",   1),
    ("Gói",    "gói",  1),
    ("Ống",    "ống",  1),
    ("Chai",   "chai", 1),
    ("Lít",    "L",    0),
    ("ml",     "ml",   0),
    ("g",      "g",    0),
    ("kg",     "kg",   0),
]


# ---------------------------------------------------------------------------
# 2. SC Item Group (nested)
# ---------------------------------------------------------------------------
ITEM_GROUPS = [
    # (name, parent, is_group, description)
    ("Tất cả vật tư",        None,                    1, "Root group"),
    # Vật tư tiêu hao
    ("Vật tư tiêu hao",      "Tất cả vật tư",          1, "Tiêu hao trong điều trị"),
    ("Băng gạc",             "Vật tư tiêu hao",        0, "Băng cuộn, gạc tiệt trùng"),
    ("Bông y tế",            "Vật tư tiêu hao",        0, "Bông gòn, bông tăm tiệt trùng"),
    ("Găng tay",             "Vật tư tiêu hao",        0, "Găng phẫu thuật, găng khám"),
    ("Khẩu trang",           "Vật tư tiêu hao",        0, "Khẩu trang y tế, N95"),
    ("Kim tiêm",             "Vật tư tiêu hao",        0, "Kim các size"),
    ("Bơm tiêm",             "Vật tư tiêu hao",        0, "Bơm tiêm 1/3/5/10/20ml"),
    ("Dây truyền",           "Vật tư tiêu hao",        0, "Dây truyền dịch, set"),
    # Vật tư thay thế / cấy ghép
    ("Vật tư thay thế",      "Tất cả vật tư",          1, "Cấy ghép, thay thế"),
    ("Stent mạch",           "Vật tư thay thế",        0, "Stent động mạch vành, ngoại biên"),
    ("Khớp nhân tạo",        "Vật tư thay thế",        0, "Khớp háng, gối"),
    ("Vít/Đinh xương",       "Vật tư thay thế",        0, "Đinh nội tủy, vít cố định"),
    # Hóa chất sinh phẩm
    ("Hóa chất sinh phẩm",   "Tất cả vật tư",          1, "Hóa chất xét nghiệm, test nhanh"),
    ("Test nhanh",           "Hóa chất sinh phẩm",     0, "Test nhanh các loại"),
    ("Hóa chất xét nghiệm",  "Hóa chất sinh phẩm",     0, "Sinh hóa, huyết học, vi sinh"),
    # Dịch truyền
    ("Dịch truyền",          "Tất cả vật tư",          1, "Dịch truyền IV"),
    ("Nước muối sinh lý",    "Dịch truyền",            0, "NaCl 0.9%"),
    ("Glucose",              "Dịch truyền",            0, "Glucose 5%, 10%, 30%"),
    ("Ringer Lactate",       "Dịch truyền",            0, "Ringer Lactate, Ringer's"),
    # Vật tư phụ trợ
    ("Vật tư phụ trợ",       "Tất cả vật tư",          1, "Sát khuẩn, cồn, povidine"),
    ("Cồn y tế",             "Vật tư phụ trợ",         0, "Cồn 70°, 90°"),
    ("Sát khuẩn",            "Vật tư phụ trợ",         0, "Povidine, Chlorhexidine"),
]


# ---------------------------------------------------------------------------
# 3. SC Department (cấp BV quận/huyện điển hình)
# ---------------------------------------------------------------------------
DEPARTMENTS = [
    # (name, code, type, head, phone)
    # Lâm sàng
    ("Khoa Nội tổng hợp",         "KNT", "Clinical", None, None),
    ("Khoa Ngoại tổng hợp",       "KNG", "Surgical", None, None),
    ("Khoa Sản",                  "KS",  "Clinical", None, None),
    ("Khoa Nhi",                  "KN",  "Clinical", None, None),
    ("Khoa Cấp cứu",              "KCC", "Clinical", None, None),
    ("Khoa Hồi sức tích cực",     "KHS", "Clinical", None, None),
    ("Khoa Tim mạch",             "KTM", "Clinical", None, None),
    ("Khoa Tiêu hóa",             "KTH", "Clinical", None, None),
    ("Khoa Thần kinh",            "KTK", "Clinical", None, None),
    ("Khoa Mắt",                  "KM",  "Clinical", None, None),
    ("Khoa Tai Mũi Họng",         "KTMH","Clinical", None, None),
    ("Khoa Răng Hàm Mặt",         "KRHM","Surgical", None, None),
    ("Khoa Da liễu",              "KDL", "Clinical", None, None),
    ("Khoa Truyền nhiễm",         "KTN", "Clinical", None, None),
    ("Khoa Y học cổ truyền",      "KYHCT","Clinical", None, None),
    ("Khoa Chấn thương chỉnh hình","KCTCH","Surgical", None, None),
    ("Khoa Ung bướu",             "KUB", "Clinical", None, None),
    ("Khoa Phục hồi chức năng",   "KPHCN","Clinical", None, None),
    # Cận lâm sàng
    ("Khoa Chẩn đoán hình ảnh",   "KCDHA","Lab",      None, None),
    ("Khoa Xét nghiệm",           "KXN", "Lab",       None, None),
    ("Khoa Vi sinh",              "KVS", "Lab",       None, None),
    ("Khoa Giải phẫu bệnh",       "KGPB","Lab",       None, None),
    ("Khoa Thăm dò chức năng",    "KTDCN","Lab",      None, None),
    # Phòng mổ + dược
    ("Khoa Gây mê hồi sức",       "KGMHS","Surgical", None, None),
    ("Phòng Mổ",                  "PM",   "Surgical", None, None),
    ("Khoa Dược",                 "KD",   "Pharmacy", None, None),
    ("Phòng Vật tư - TTBYT",      "PVT",  "Admin",    None, None),
    # Quản lý
    ("Phòng Khám tổng hợp",       "PKTH", "Clinical", None, None),
    ("Phòng Kế hoạch tổng hợp",   "PKHTH","Admin",    None, None),
    ("Phòng Tài chính kế toán",   "PTCKT","Admin",    None, None),
    ("Phòng Tổ chức cán bộ",      "PTCCB","Admin",    None, None),
    ("Phòng CNTT",                "PCNTT","Admin",    None, None),
    ("Ban Giám đốc",              "BGD",  "Admin",    None, None),
]


# ---------------------------------------------------------------------------
# 4. SC Warehouse (3-tier)
# ---------------------------------------------------------------------------
WAREHOUSES = [
    # (name, code, type, parent, is_group, department)
    # Tầng 1: Kho Tổng (group)
    ("Kho Tổng Bệnh viện",        "KHO-TONG",      "Main",      None,                   1, None),
    # Tầng 2: Kho con
    ("Kho Vật tư tiêu hao",        "KHO-VTTH",      "Sub",       "Kho Tổng Bệnh viện",   0, None),
    ("Kho Hóa chất sinh phẩm",     "KHO-HCSP",      "Sub",       "Kho Tổng Bệnh viện",   0, None),
    ("Kho Vật tư cấy ghép",        "KHO-CG",        "Sub",       "Kho Tổng Bệnh viện",   0, None),
    ("Kho Dịch truyền",            "KHO-DT",        "Sub",       "Kho Tổng Bệnh viện",   0, None),
    ("Kho Cách ly QC",             "KHO-QC",        "Quarantine","Kho Tổng Bệnh viện",   0, None),
    ("Kho Trung chuyển",           "KHO-TC",        "Transit",   "Kho Tổng Bệnh viện",   0, None),
    # Tầng 3: Kho khoa phòng
    ("Kho Khoa Cấp cứu",           "KHO-KCC",       "Department","Kho Tổng Bệnh viện",   0, "Khoa Cấp cứu"),
    ("Kho Khoa ICU",               "KHO-KHS",       "Department","Kho Tổng Bệnh viện",   0, "Khoa Hồi sức tích cực"),
    ("Kho Khoa Nội tổng hợp",      "KHO-KNT",       "Department","Kho Tổng Bệnh viện",   0, "Khoa Nội tổng hợp"),
    ("Kho Khoa Ngoại tổng hợp",    "KHO-KNG",       "Department","Kho Tổng Bệnh viện",   0, "Khoa Ngoại tổng hợp"),
    ("Kho Khoa Sản",               "KHO-KS",        "Department","Kho Tổng Bệnh viện",   0, "Khoa Sản"),
    ("Kho Khoa Nhi",               "KHO-KN",        "Department","Kho Tổng Bệnh viện",   0, "Khoa Nhi"),
    ("Kho Phòng Mổ",               "KHO-PM",        "Department","Kho Tổng Bệnh viện",   0, "Phòng Mổ"),
    ("Kho Khoa Dược",              "KHO-KD",        "Department","Kho Tổng Bệnh viện",   0, "Khoa Dược"),
]


# ---------------------------------------------------------------------------
# 5. SC Supplier (NCC điển hình ngành VTYT Việt Nam)
# ---------------------------------------------------------------------------
SUPPLIERS = [
    # (name, code, tax_id, type, email, phone, address)
    ("Công ty CP Dược Hậu Giang",        "DHG",         "1800156801", "Nhà sản xuất",
     "info@dhgpharma.com.vn", "0292-3891433", "288 Bis Nguyễn Văn Cừ, Q. Ninh Kiều, TP. Cần Thơ"),
    ("Công ty CP Traphaco",              "TRAPHACO",    "0100109953", "Nhà sản xuất",
     "info@traphaco.com.vn", "024-37345686", "75 Yên Ninh, Ba Đình, Hà Nội"),
    ("Công ty CP Pymepharco",            "PYMEPHARCO",  "4400111383", "Nhà sản xuất",
     "info@pymepharco.com",  "0257-3823250", "166-170 Nguyễn Huệ, Phú Yên"),
    ("Công ty CP Imexpharm",             "IMEXPHARM",   "1400384433", "Nhà sản xuất",
     "info@imexpharm.com",   "0277-3851941", "04 Đường 30/4, TP. Cao Lãnh, Đồng Tháp"),
    ("Boston Scientific Vietnam",        "BSC-VN",      "0316578901", "Nhà phân phối",
     "vn-info@bsci.com",     "028-39999000", "Vincom Center, Q1, TP.HCM"),
    ("Medtronic Vietnam",                "MDT-VN",      "0316578902", "Nhà phân phối",
     "vn-info@medtronic.com","028-39106000", "Bitexco Tower, Q1, TP.HCM"),
    ("B. Braun Vietnam",                 "BBRAUN-VN",   "0316578903", "Nhà sản xuất",
     "info-vn@bbraun.com",   "024-32268888", "170 La Thành, Đống Đa, Hà Nội"),
    ("3M Vietnam Co. Ltd",               "3M-VN",       "0316578904", "Nhà phân phối",
     "vn-info@3m.com",       "028-39101888", "Diamond Plaza, Q1, TP.HCM"),
]


# ---------------------------------------------------------------------------
# 6. SC Item (vật tư mẫu — 12 items đại diện)
# ---------------------------------------------------------------------------
ITEMS = [
    # (code, name, group, uom, has_batch, is_medical, lead_time, min_shelf_life, has_bhyt, bhyt_group, bhyt_rate)
    ("VTTH-GLOVE-S",   "Găng tay phẫu thuật vô trùng cỡ 7.5", "Găng tay",     "Đôi",  1, 1, 14, 180, 1, "N05", 80),
    ("VTTH-MASK-3PLY", "Khẩu trang y tế 3 lớp",                "Khẩu trang",   "Cái",  1, 1, 7,  90,  0, None, None),
    ("VTTH-GAUZE-5",   "Băng gạc y tế cuộn 5cm",               "Băng gạc",     "Cuộn", 1, 1, 14, 180, 1, "N05", 80),
    ("VTTH-COTTON",    "Bông y tế tiệt trùng 100g",            "Bông y tế",    "Gói",  1, 1, 14, 180, 1, "N05", 80),
    ("VTTH-NEEDLE-23", "Kim tiêm 23G x 1 inch",                "Kim tiêm",     "Cái",  1, 1, 14, 180, 1, "N05", 100),
    ("VTTH-SYR-5ML",   "Bơm tiêm 5ml + kim",                   "Bơm tiêm",     "Cái",  1, 1, 14, 180, 1, "N05", 100),
    ("VTTH-IV-SET",    "Dây truyền dịch tiệt trùng",           "Dây truyền",   "Bộ",   1, 1, 14, 180, 1, "N05", 100),
    ("DTRC-NACL09",    "Dịch truyền NaCl 0.9% 500ml",          "Nước muối sinh lý", "Chai", 1, 1, 21, 180, 1, "N05", 100),
    ("DTRC-GLU5",      "Dịch truyền Glucose 5% 500ml",         "Glucose",      "Chai", 1, 1, 21, 180, 1, "N05", 100),
    ("DTRC-RL",        "Dịch truyền Ringer Lactate 500ml",     "Ringer Lactate","Chai",1, 1, 21, 180, 1, "N05", 100),
    ("VTPT-COND-70",   "Cồn 70 độ y tế 500ml",                 "Cồn y tế",     "Chai", 1, 1, 14, 365, 0, None, None),
    ("VTPT-IODINE",    "Povidine iod 10% 500ml",               "Sát khuẩn",    "Chai", 1, 1, 14, 365, 1, "N05", 100),
]


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------
def run():
    """Seed toàn bộ master data idempotent."""
    summary = {}
    summary["uom"]        = _seed_uom()
    summary["item_group"] = _seed_item_groups()
    summary["department"] = _seed_departments()
    summary["warehouse"]  = _seed_warehouses()
    summary["supplier"]   = _seed_suppliers()
    summary["item"]       = _seed_items()
    summary["bin"]        = _seed_bins()
    summary["item_default_bin"] = _assign_default_bins()
    summary["gl_account"] = _seed_gl_accounts()
    frappe.db.commit()
    return summary


def _seed_uom() -> int:
    created = 0
    for name, abbr, whole in UOMS:
        if frappe.db.exists("SC UOM", name):
            continue
        d = frappe.new_doc("SC UOM")
        d.uom_name = name
        d.abbreviation = abbr
        d.must_be_whole_number = whole
        d.flags.ignore_permissions = True
        d.insert()
        created += 1
    return created


def _seed_item_groups() -> int:
    created = 0
    # Insert theo thứ tự: parent trước con
    for name, parent, is_group, desc in ITEM_GROUPS:
        if frappe.db.exists("SC Item Group", name):
            continue
        d = frappe.new_doc("SC Item Group")
        d.group_name = name
        d.parent_group = parent
        d.is_group = is_group
        d.description = desc
        d.flags.ignore_permissions = True
        try:
            d.insert()
            created += 1
        except Exception as e:
            frappe.log_error(message=f"Item Group {name} insert failed: {e}",
                              title="Seed master data")
    return created


def _seed_departments() -> int:
    created = 0
    for name, code, dtype, head, phone in DEPARTMENTS:
        if frappe.db.exists("SC Department", name):
            continue
        d = frappe.new_doc("SC Department")
        d.department_name = name
        d.department_code = code
        d.department_type = dtype
        d.head_user = head
        d.phone = phone
        d.flags.ignore_permissions = True
        d.insert()
        created += 1
    return created


def _seed_warehouses() -> int:
    created = 0
    for name, code, wtype, parent, is_group, dept in WAREHOUSES:
        if frappe.db.exists("SC Warehouse", name):
            continue
        d = frappe.new_doc("SC Warehouse")
        d.warehouse_name = name
        d.warehouse_code = code
        d.warehouse_type = wtype
        d.parent_warehouse = parent if parent and frappe.db.exists("SC Warehouse", parent) else None
        d.is_group = is_group
        if dept and frappe.db.exists("SC Department", dept):
            d.department = dept
        d.flags.ignore_permissions = True
        d.flags.allow_group_with_stock = True
        try:
            d.insert()
            created += 1
        except Exception as e:
            frappe.log_error(message=f"Warehouse {name} insert failed: {e}",
                              title="Seed master data")
    return created


def _seed_suppliers() -> int:
    created = 0
    for name, code, tax, stype, email, phone, addr in SUPPLIERS:
        if frappe.db.exists("SC Supplier", {"supplier_name": name}):
            continue
        d = frappe.new_doc("SC Supplier")
        d.supplier_name = name
        d.supplier_code = code
        d.tax_id = tax
        d.supplier_type = stype
        d.email_id = email
        d.mobile_no = phone
        d.address = addr
        d.payment_terms = "Net 30"
        d.flags.ignore_permissions = True
        d.insert()
        created += 1
    return created


def _seed_items() -> int:
    created = 0
    for code, name, group, uom, has_batch, is_med, lead, min_shelf, has_bhyt, bhyt_grp, bhyt_rate in ITEMS:
        if frappe.db.exists("SC Item", code):
            continue
        if not frappe.db.exists("SC UOM", uom):
            continue
        if group and not frappe.db.exists("SC Item Group", group):
            continue
        d = frappe.new_doc("SC Item")
        d.item_code = code
        d.item_name = name
        d.item_group = group
        d.uom = uom
        d.buy_uom = uom
        d.use_uom = uom
        d.uom_conversion_factor = 1
        d.has_batch_no = has_batch
        d.is_stock_item = 1
        d.is_purchase_item = 1
        d.is_medical_supply = is_med
        d.inspection_required_before_purchase = 1
        d.lead_time_days = lead
        d.min_shelf_life_days = min_shelf
        d.safety_stock = 50
        d.has_bhyt = has_bhyt
        d.bhyt_code = code if has_bhyt else None
        d.bhyt_group = bhyt_grp
        d.bhyt_payment_rate = bhyt_rate or 0
        d.flags.ignore_permissions = True
        d.insert()
        created += 1
    return created


# ---------------------------------------------------------------------------
# 7. Bin Location seed cho từng kho con + kho khoa
# ---------------------------------------------------------------------------
# (warehouse_name, bin_code, zone, aisle, rack, shelf, level, capacity, description)
BINS = [
    # Kho VTTH — 4 zones × 3 bins = 12 bins
    ("Kho Vật tư tiêu hao", "VTTH-A-01-01", "A", "01", "01", "01", "L1", 200, "Băng gạc cuộn"),
    ("Kho Vật tư tiêu hao", "VTTH-A-01-02", "A", "01", "01", "02", "L1", 200, "Bông y tế"),
    ("Kho Vật tư tiêu hao", "VTTH-A-02-01", "A", "02", "01", "01", "L1", 200, "Băng dán y tế"),
    ("Kho Vật tư tiêu hao", "VTTH-B-01-01", "B", "01", "01", "01", "L1", 500, "Găng tay phẫu thuật"),
    ("Kho Vật tư tiêu hao", "VTTH-B-01-02", "B", "01", "01", "02", "L1", 500, "Găng tay khám"),
    ("Kho Vật tư tiêu hao", "VTTH-C-01-01", "C", "01", "01", "01", "L1", 1000, "Bơm tiêm 1-5ml"),
    ("Kho Vật tư tiêu hao", "VTTH-C-01-02", "C", "01", "01", "02", "L1", 1000, "Bơm tiêm 10-20ml"),
    ("Kho Vật tư tiêu hao", "VTTH-C-02-01", "C", "02", "01", "01", "L1", 1000, "Kim tiêm các size"),
    ("Kho Vật tư tiêu hao", "VTTH-D-01-01", "D", "01", "01", "01", "L1", 500, "Khẩu trang 3 lớp"),
    ("Kho Vật tư tiêu hao", "VTTH-D-01-02", "D", "01", "01", "02", "L1", 500, "Khẩu trang N95"),
    ("Kho Vật tư tiêu hao", "VTTH-E-01-01", "E", "01", "01", "01", "L1", 300, "Dây truyền dịch"),
    ("Kho Vật tư tiêu hao", "VTTH-E-01-02", "E", "01", "01", "02", "L1", 300, "Set tiêm truyền"),

    # Kho Hóa chất sinh phẩm
    ("Kho Hóa chất sinh phẩm", "HCSP-A-01-01", "A", "01", "01", "01", "L1", 100, "Test nhanh COVID"),
    ("Kho Hóa chất sinh phẩm", "HCSP-A-01-02", "A", "01", "01", "02", "L1", 100, "Test nhanh sốt rét"),
    ("Kho Hóa chất sinh phẩm", "HCSP-B-01-01", "B", "01", "01", "01", "L1", 50,  "Hóa chất sinh hóa"),
    ("Kho Hóa chất sinh phẩm", "HCSP-B-01-02", "B", "01", "01", "02", "L1", 50,  "Hóa chất huyết học"),
    ("Kho Hóa chất sinh phẩm", "HCSP-B-02-01", "B", "02", "01", "01", "L1", 50,  "Hóa chất vi sinh"),

    # Kho Vật tư cấy ghép (capacity nhỏ, giá trị cao)
    ("Kho Vật tư cấy ghép", "CG-A-01-01", "A", "01", "01", "01", "L1", 50, "Stent động mạch vành"),
    ("Kho Vật tư cấy ghép", "CG-A-01-02", "A", "01", "01", "02", "L1", 50, "Stent ngoại biên"),
    ("Kho Vật tư cấy ghép", "CG-B-01-01", "B", "01", "01", "01", "L1", 30, "Khớp háng nhân tạo"),
    ("Kho Vật tư cấy ghép", "CG-B-01-02", "B", "01", "01", "02", "L1", 30, "Khớp gối nhân tạo"),
    ("Kho Vật tư cấy ghép", "CG-C-01-01", "C", "01", "01", "01", "L1", 100, "Vít/Đinh xương"),

    # Kho Dịch truyền (capacity lớn)
    ("Kho Dịch truyền", "DT-A-01-01", "A", "01", "01", "01", "L1", 500, "NaCl 0.9% 500ml"),
    ("Kho Dịch truyền", "DT-A-01-02", "A", "01", "01", "02", "L1", 500, "NaCl 0.9% 1000ml"),
    ("Kho Dịch truyền", "DT-B-01-01", "B", "01", "01", "01", "L1", 500, "Glucose 5%"),
    ("Kho Dịch truyền", "DT-B-01-02", "B", "01", "01", "02", "L1", 500, "Glucose 10%"),
    ("Kho Dịch truyền", "DT-C-01-01", "C", "01", "01", "01", "L1", 500, "Ringer Lactate"),

    # Kho Cách ly QC (small zones)
    ("Kho Cách ly QC", "QC-HOLD-01", "Q", "01", "01", "01", "L1", 200, "Lô chờ QC pass"),
    ("Kho Cách ly QC", "QC-FAIL-01", "Q", "02", "01", "01", "L1", 200, "Lô QC fail chờ trả NCC"),
    ("Kho Cách ly QC", "QC-RECALL-01", "Q", "03", "01", "01", "L1", 100, "Lô bị recall"),
]


def _seed_bins() -> int:
    created = 0
    for warehouse, code, zone, aisle, rack, shelf, level, capacity, desc in BINS:
        if not frappe.db.exists("SC Warehouse", warehouse):
            continue
        if frappe.db.exists("Bin Location", {"bin_code": code}):
            continue
        d = frappe.new_doc("Bin Location")
        d.warehouse = warehouse
        d.bin_code = code
        d.description = desc
        d.zone = zone
        d.aisle = aisle
        d.rack = rack
        d.shelf = shelf
        d.level = level
        d.capacity_qty = capacity
        d.is_quarantine = 1 if "Cách ly" in warehouse else 0
        d.flags.ignore_permissions = True
        try:
            d.insert()
            created += 1
        except Exception as e:
            frappe.log_error(message=f"Bin {code} insert failed: {e}",
                              title="Seed bin locations")
    return created


# ---------------------------------------------------------------------------
# 8. Assign default_bin_location cho 12 sample items
# ---------------------------------------------------------------------------
ITEM_BIN_MAP = {
    "VTTH-GLOVE-S":   "VTTH-B-01-01",
    "VTTH-MASK-3PLY": "VTTH-D-01-01",
    "VTTH-GAUZE-5":   "VTTH-A-01-01",
    "VTTH-COTTON":    "VTTH-A-01-02",
    "VTTH-NEEDLE-23": "VTTH-C-02-01",
    "VTTH-SYR-5ML":   "VTTH-C-01-01",
    "VTTH-IV-SET":    "VTTH-E-01-01",
    "DTRC-NACL09":    "DT-A-01-01",
    "DTRC-GLU5":      "DT-B-01-01",
    "DTRC-RL":        "DT-C-01-01",
    "VTPT-COND-70":   None,  # chưa có bin VTPT — để None
    "VTPT-IODINE":    None,
}


def _assign_default_bins() -> int:
    updated = 0
    for item_code, bin_code in ITEM_BIN_MAP.items():
        if not bin_code:
            continue
        if not frappe.db.exists("SC Item", item_code):
            continue
        bin_name = frappe.db.get_value("Bin Location", {"bin_code": bin_code}, "name")
        if not bin_name:
            continue
        current = frappe.db.get_value("SC Item", item_code, "default_bin_location")
        if current == bin_name:
            continue
        frappe.db.set_value("SC Item", item_code, "default_bin_location", bin_name)
        updated += 1
    return updated


# ---------------------------------------------------------------------------
# 9. SC GL Account — chart of accounts theo TT 200/2014/TT-BTC (đơn giản hóa)
# ---------------------------------------------------------------------------
GL_ACCOUNTS = [
    # (code, name, account_type, parent, is_group, root_type, vas_ref)
    ("100", "TÀI SẢN",                 None,         None,  1, "Asset",     None),
    ("110", "Tiền & TĐ tiền",          None,         "100", 1, "Asset",     None),
    ("1111", "Tiền mặt VND",           "Cash",       "110", 0, "Asset",     "TT200"),
    ("1121", "Tiền gửi NH VND",        "Bank",       "110", 0, "Asset",     "TT200"),
    ("130", "Phải thu khách hàng",     None,         "100", 1, "Asset",     None),
    ("131", "Phải thu KH",             "Receivable", "130", 0, "Asset",     "TT200"),
    ("133", "Thuế GTGT khấu trừ",      None,         "100", 1, "Asset",     None),
    ("1331", "Thuế GTGT khấu trừ",     "Tax",        "133", 0, "Asset",     "TT200"),
    ("150", "Hàng tồn kho",            None,         "100", 1, "Asset",     None),
    ("152", "Nguyên liệu vật liệu",    "Stock",      "150", 0, "Asset",     "TT200 — vật tư y tế tiêu hao"),
    ("153", "Công cụ dụng cụ",         "Stock",      "150", 0, "Asset",     "TT200"),
    ("156", "Hàng hóa",                "Stock",      "150", 0, "Asset",     "TT200"),

    ("300", "NỢ PHẢI TRẢ",             None,         None,  1, "Liability", None),
    ("330", "Phải trả NCC",            None,         "300", 1, "Liability", None),
    ("331", "Phải trả NCC",            "Payable",    "330", 0, "Liability", "TT200"),
    ("333", "Thuế phải nộp NN",        None,         "300", 1, "Liability", None),
    ("3331", "Thuế GTGT phải nộp",     "Tax",        "333", 0, "Liability", "TT200"),

    ("600", "CHI PHÍ",                 None,         None,  1, "Expense",   None),
    ("632", "Giá vốn hàng bán",        "Expense",    "600", 0, "Expense",   "TT200"),
    ("641", "Chi phí bán hàng",        "Expense",    "600", 0, "Expense",   "TT200"),
    ("642", "Chi phí QLDN",            "Expense",    "600", 0, "Expense",   "TT200"),
]


def _seed_gl_accounts() -> int:
    created = 0
    # Insert theo thứ tự (parent trước con)
    for code, name, atype, parent, is_group, root, vas in GL_ACCOUNTS:
        if frappe.db.exists("SC GL Account", code):
            continue
        d = frappe.new_doc("SC GL Account")
        d.account_code = code
        d.account_name = name
        d.account_type = atype
        d.parent_account = parent if parent and frappe.db.exists("SC GL Account", parent) else None
        d.is_group = is_group
        d.root_type = root
        d.vas_reference = vas
        d.flags.ignore_permissions = True
        try:
            d.insert()
            created += 1
        except Exception as e:
            frappe.log_error(message=f"GL Account {code} failed: {e}",
                              title="Seed GL accounts")
    return created
