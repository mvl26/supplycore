"""Seed toạ độ bản đồ — Bệnh viện Y học cổ truyền Bộ Công an (Hà Đông, Hà Nội).

Hai cấp bản đồ:
  1. Bản đồ khuôn viên BV — vị trí từng kho (site_row, site_col).
  2. Sơ đồ trong kho — vị trí từng bin (map_row, map_col) auto từ aisle/zone.

Chạy: bench --site supplycore execute supplycore.setup.seed_warehouse_map.run
"""

import frappe


# ---------------------------------------------------------------------------
# 1. Bản đồ khuôn viên — lưới 6 hàng × 7 cột.
#    Cổng chính ở (5,3). Kho Tổng trung tâm. Khoa phòng bố trí xung quanh.
#    (row, col, block)
# ---------------------------------------------------------------------------
SITE_LAYOUT = {
    "Kho Tổng Bệnh viện":      (2, 3, "Nhà A — Trung tâm"),
    "Kho Trung chuyển":        (2, 2, "Nhà A — Tầng 1"),
    "Kho Cách ly QC":          (2, 4, "Nhà A — Khu cách ly"),
    "Kho Dịch truyền":         (1, 2, "Nhà A — Tầng 2"),
    "Kho Hóa chất sinh phẩm":  (1, 4, "Nhà A — Tầng 2"),
    "Kho Vật tư tiêu hao":     (1, 3, "Nhà A — Tầng 2"),
    "Kho Vật tư cấy ghép":     (1, 5, "Nhà A — Tầng 3"),
    "Kho Khoa Dược":           (3, 3, "Nhà B — Tầng 1"),
    "Kho Khoa Nội tổng hợp":   (3, 1, "Nhà B — Tầng 2"),
    "Kho Khoa Ngoại tổng hợp": (3, 5, "Nhà B — Tầng 2"),
    "Kho Khoa Cấp cứu":        (4, 2, "Nhà C — Tầng 1"),
    "Kho Khoa ICU":            (4, 4, "Nhà C — Tầng 1"),
    "Kho Phòng Mổ":            (4, 3, "Nhà C — Tầng 2"),
    "Kho Khoa Nhi":            (3, 6, "Nhà D — Tầng 1"),
    "Kho Khoa Sản":            (4, 5, "Nhà D — Tầng 1"),
}
# Cổng chính khuôn viên — điểm bắt đầu chỉ đường
SITE_ENTRANCE = (5, 3)


def _zone_to_col(zone: str) -> int:
    """Zone chữ (A,B,C…) → cột số (1,2,3…). Zone số → giữ nguyên."""
    if not zone:
        return 1
    z = str(zone).strip().upper()
    if z.isdigit():
        return int(z)
    # Lấy ký tự đầu
    return ord(z[0]) - ord("A") + 1


def _aisle_to_row(aisle: str) -> int:
    """Aisle '01','02'… → hàng số."""
    if not aisle:
        return 1
    try:
        return int(str(aisle).strip())
    except ValueError:
        return 1


def run() -> dict:
    result = {"warehouses_mapped": 0, "bins_mapped": 0,
              "entrance_set": None, "warehouse_grid": {}, "errors": []}

    # === 1. Site map: gán toạ độ khuôn viên cho từng kho ===
    for wh_name, (srow, scol, block) in SITE_LAYOUT.items():
        if not frappe.db.exists("SC Warehouse", wh_name):
            result["errors"].append(f"Không tìm thấy kho: {wh_name}")
            continue
        frappe.db.set_value("SC Warehouse", wh_name, {
            "site_row": srow,
            "site_col": scol,
            "site_block": block,
            "is_site_entrance": 0,
        }, update_modified=False)
        result["warehouses_mapped"] += 1

    # Tạo / đánh dấu cổng chính: dùng kho Trung chuyển làm điểm vào kho,
    # nhưng cổng khuôn viên là 1 ô riêng — lưu qua SupplyCore Settings hoặc
    # đánh dấu kho gần cổng nhất. Ở đây set is_site_entrance cho Kho Tổng
    # (điểm tham chiếu chỉ đường) — đồng thời lưu toạ độ cổng.
    # Cổng = ô (5,3): không có kho — sẽ render riêng ở FE qua API.
    result["entrance_set"] = {"row": SITE_ENTRANCE[0], "col": SITE_ENTRANCE[1]}

    # === 2. Bin grid: gán map_row/map_col cho từng bin + map_rows/cols cho kho ===
    # Ranking per-warehouse: zone/aisle distinct → 1..N (lưới gọn, không lỗ hổng)
    bins = frappe.get_all("Bin Location",
                           fields=["name", "warehouse", "zone", "aisle"],
                           limit=0)
    # Gom theo warehouse để rank
    by_wh = {}
    for b in bins:
        by_wh.setdefault(b.warehouse, []).append(b)

    for wh, wh_bins in by_wh.items():
        # Distinct zone (cột) và aisle (hàng) — sort tự nhiên
        zones = sorted({(bn.zone or "?") for bn in wh_bins},
                       key=lambda z: (_zone_to_col(z), str(z)))
        aisles = sorted({(bn.aisle or "1") for bn in wh_bins},
                        key=lambda a: (_aisle_to_row(a), str(a)))
        zone_rank = {z: i + 1 for i, z in enumerate(zones)}
        aisle_rank = {a: i + 1 for i, a in enumerate(aisles)}
        for bn in wh_bins:
            row = aisle_rank.get(bn.aisle or "1", 1)
            col = zone_rank.get(bn.zone or "?", 1)
            frappe.db.set_value("Bin Location", bn.name, {
                "map_row": row, "map_col": col,
            }, update_modified=False)
            result["bins_mapped"] += 1
        if frappe.db.exists("SC Warehouse", wh):
            frappe.db.set_value("SC Warehouse", wh, {
                "map_rows": len(aisles), "map_cols": len(zones),
            }, update_modified=False)
            result["warehouse_grid"][wh] = {"rows": len(aisles), "cols": len(zones)}

    frappe.db.commit()
    return result
