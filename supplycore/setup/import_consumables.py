"""Import danh mục vật tư y tế tiêu hao (docs/list_consumable_item.xlsx) → SC Item.

Chuẩn hoá + nạp toàn bộ ~2999 vật tư làm item nền của SupplyCore.

Chạy:
  bench --site <site> execute supplycore.setup.import_consumables.dry_run   # chỉ kiểm tra + xuất CSV chuẩn hoá
  bench --site <site> execute supplycore.setup.import_consumables.run       # tạo group/uom + import item

Idempotent: item đã tồn tại → bỏ qua; commit theo lô 200 → chết giữa chừng chạy lại tiếp.

Quyết định (chốt 2026-06-11):
  - has_batch_no = 0 cho tất cả (vật tư tiêu hao; bật lô theo nhóm sau nếu cần).
  - UOM giữ nguyên text gốc (chỉ trim khoảng trắng) — không remap rác.
  - item_group lấy từ cột "Tên nhóm" (4 nhóm: VTTH/HC/DCYT/TBYT) dưới 1 root.
  - item_name cắt 140 ký tự (full vào description).
"""

import csv
import os
import re

import frappe

XLSX_REL = ("..", "docs", "list_consumable_item.xlsx")
CSV_OUT_REL = ("..", "docs", "list_consumable_item_normalized.csv")
ROOT_GROUP = "Tất cả nhóm vật tư"
FALLBACK_UOM = "Chưa xác định"
HEADER_ROW = 4  # 0-based: dòng 5 trong file là dữ liệu đầu tiên

# Map cột (0-based) theo header dòng 4
C_CODE, C_NAME, C_UOM, C_GROUP = 1, 6, 7, 16
C_PACK, C_REG, C_MAKER, C_COUNTRY = 8, 11, 13, 14


def _paths():
    base = frappe.get_app_path("supplycore")
    xlsx = os.path.abspath(os.path.join(base, *XLSX_REL))
    csv_out = os.path.abspath(os.path.join(base, *CSV_OUT_REL))
    return xlsx, csv_out


def _clean(v):
    if v is None:
        return ""
    return re.sub(r"\s+", " ", str(v).strip())


def _clean_name(v):
    s = _clean(v).strip('"').strip()
    return re.sub(r"\s+", " ", s)


def _load_rows():
    import openpyxl
    xlsx, _ = _paths()
    if not os.path.exists(xlsx):
        frappe.throw("Không tìm thấy file: {0}".format(xlsx))
    wb = openpyxl.load_workbook(xlsx, read_only=True, data_only=True)
    ws = wb["Sheet1"]
    rows = list(ws.iter_rows(values_only=True))
    return rows[HEADER_ROW + 1:]


def _norm_rows(raw):
    """Chuẩn hoá → list dict {code,item_name,full_name,uom,group,description}."""
    out = []
    for r in raw:
        code = _clean(r[C_CODE])
        if not code:
            continue
        full = _clean_name(r[C_NAME])
        uom = _clean(r[C_UOM]) or FALLBACK_UOM
        group = _clean(r[C_GROUP]) or ROOT_GROUP
        desc = []
        if len(full) > 140:
            desc.append("Tên đầy đủ: " + full)
        for label, idx in (("Quy cách", C_PACK), ("Hãng SX", C_MAKER),
                           ("Nước SX", C_COUNTRY), ("Số ĐK", C_REG)):
            v = _clean(r[idx])
            if v and v not in (".", "-"):
                desc.append("{0}: {1}".format(label, v))
        out.append({
            "code": code,
            "item_name": full[:140],
            "full_name": full,
            "uom": uom,
            "group": group,
            "description": "\n".join(desc),
        })
    return out


# ---------------------------------------------------------------------------
# Prerequisites
# ---------------------------------------------------------------------------
def _ensure_root():
    if not frappe.db.exists("SC Item Group", ROOT_GROUP):
        g = frappe.new_doc("SC Item Group")
        g.group_name = ROOT_GROUP
        g.is_group = 1
        g.parent_group = ""
        g.flags.ignore_permissions = True
        g.insert()


def _ensure_group(name):
    if name == ROOT_GROUP or frappe.db.exists("SC Item Group", name):
        return
    g = frappe.new_doc("SC Item Group")
    g.group_name = name
    g.is_group = 0
    g.parent_group = ROOT_GROUP
    g.flags.ignore_permissions = True
    g.insert()


def _ensure_uom(name):
    if not frappe.db.exists("SC UOM", name):
        u = frappe.new_doc("SC UOM")
        u.uom_name = name
        u.flags.ignore_permissions = True
        u.insert()


def _make_item(row):
    it = frappe.new_doc("SC Item")
    it.item_code = row["code"]
    it.item_name = row["item_name"]
    it.uom = row["uom"]
    it.item_group = row["group"]
    if row["description"]:
        it.description = row["description"]
    it.is_stock_item = 1
    it.is_purchase_item = 1
    it.is_medical_supply = 1
    it.has_batch_no = 0
    it.inspection_required_before_purchase = 0
    it.flags.ignore_permissions = True
    it.insert()


def _write_csv(rows):
    _, csv_out = _paths()
    with open(csv_out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["item_code", "item_name", "uom", "item_group", "description"])
        for r in rows:
            w.writerow([r["code"], r["item_name"], r["uom"], r["group"],
                        r["description"].replace("\n", " | ")])
    return csv_out


# ---------------------------------------------------------------------------
# Entry points
# ---------------------------------------------------------------------------
def dry_run():
    rows = _norm_rows(_load_rows())
    groups = sorted({r["group"] for r in rows})
    uoms = sorted({r["uom"] for r in rows})
    csv_out = _write_csv(rows)
    print("=== DRY RUN ===")
    print("Tổng item:", len(rows))
    print("Nhóm ({0}): {1}".format(len(groups), groups))
    print("UOM distinct:", len(uoms))
    print("Tên >140 (cắt):", sum(1 for r in rows if len(r["full_name"]) > 140))
    print("CSV chuẩn hoá:", csv_out)
    # vài mẫu
    for r in rows[:5]:
        print("  ", r["code"], "|", r["item_name"][:40], "|", r["uom"], "|", r["group"])


def run(limit=None):
    rows = _norm_rows(_load_rows())

    # 1) Prerequisites (commit trước khi tạo item)
    _ensure_root()
    for g in sorted({r["group"] for r in rows}):
        _ensure_group(g)
    for u in sorted({r["uom"] for r in rows}):
        _ensure_uom(u)
    frappe.db.commit()

    # 2) Items (idempotent + commit theo lô)
    created = skipped = errors = 0
    errlist = []
    for r in rows:
        if limit and created >= int(limit):
            break
        if frappe.db.exists("SC Item", r["code"]):
            skipped += 1
            continue
        try:
            _make_item(r)
            created += 1
            if created % 200 == 0:
                frappe.db.commit()
                print("...{0} created".format(created))
        except Exception as e:
            errors += 1
            errlist.append((r["code"], str(e)[:120]))
    frappe.db.commit()

    print("=== DONE ===")
    print("groups + root, uoms tạo xong | items_created={0} skipped={1} errors={2}".format(
        created, skipped, errors))
    for c, e in errlist[:25]:
        print("  ERR", c, e)
