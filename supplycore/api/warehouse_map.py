"""Bản đồ kho — 2 cấp: khuôn viên bệnh viện + sơ đồ bin trong kho.

Bệnh viện Y học cổ truyền Bộ Công an (Hà Đông, Hà Nội).

API:
  - get_site_map(target_warehouse) — bản đồ khuôn viên + chỉ đường tới 1 kho
  - get_warehouse_map(warehouse, target_bin) — sơ đồ bin + chỉ đường tới 1 bin
  - get_route(from_warehouse, to_warehouse) — chỉ đường chuyển kho A → B

Chỉ đường = đường Manhattan (đi dọc rồi đi ngang), trả list ô để FE highlight.
"""

import frappe
from frappe import _


SITE_NAME = "Bệnh viện Y học cổ truyền Bộ Công an"
SITE_ADDRESS = "Hà Đông, Hà Nội"
# Cổng chính khuôn viên (đồng bộ với seed_warehouse_map.SITE_ENTRANCE)
SITE_ENTRANCE = {"row": 5, "col": 3}


def _manhattan_path(start: dict, end: dict, vertical_first: bool = True) -> list:
    """Đường Manhattan từ start → end. Trả list [row, col] gồm cả 2 đầu mút."""
    if not start or not end:
        return []
    sr, sc = int(start["row"]), int(start["col"])
    er, ec = int(end["row"]), int(end["col"])
    path = [[sr, sc]]
    r, c = sr, sc

    def step_v():
        nonlocal r
        while r != er:
            r += 1 if er > r else -1
            path.append([r, c])

    def step_h():
        nonlocal c
        while c != ec:
            c += 1 if ec > c else -1
            path.append([r, c])

    if vertical_first:
        step_v(); step_h()
    else:
        step_h(); step_v()
    return path


@frappe.whitelist()
def get_site_map(target_warehouse: str = None) -> dict:
    """Bản đồ khuôn viên bệnh viện — vị trí các kho + chỉ đường tới target."""
    whs = frappe.get_all("SC Warehouse",
        filters={"disabled": 0},
        fields=["name", "warehouse_type", "site_row", "site_col",
                "site_block", "department", "is_group"],
        limit=0)

    cells = []
    max_row, max_col = SITE_ENTRANCE["row"], SITE_ENTRANCE["col"]
    target_cell = None
    for w in whs:
        if not w.site_row or not w.site_col:
            continue  # chưa gán toạ độ → bỏ qua
        cell = {
            "row": int(w.site_row),
            "col": int(w.site_col),
            "warehouse": w.name,
            "type": w.warehouse_type or "",
            "block": w.site_block or "",
            "department": w.department or "",
            "is_group": int(w.is_group or 0),
            "is_target": w.name == target_warehouse,
        }
        cells.append(cell)
        max_row = max(max_row, cell["row"])
        max_col = max(max_col, cell["col"])
        if cell["is_target"]:
            target_cell = {"row": cell["row"], "col": cell["col"]}

    path = []
    if target_cell:
        path = _manhattan_path(SITE_ENTRANCE, target_cell, vertical_first=True)

    return {
        "scope": "site",
        "site_name": SITE_NAME,
        "site_address": SITE_ADDRESS,
        "rows": max_row,
        "cols": max_col,
        "entrance": SITE_ENTRANCE,
        "entrance_label": "Cổng chính",
        "cells": cells,
        "target": target_cell,
        "target_warehouse": target_warehouse,
        "path": path,
    }


@frappe.whitelist()
def get_warehouse_map(warehouse: str, target_bin: str = None) -> dict:
    """Sơ đồ bin trong 1 kho — lưới ô + chỉ đường tới target_bin.

    Entrance kho = ô ảo phía trên lưới (row 0, cột giữa).
    """
    if not frappe.db.exists("SC Warehouse", warehouse):
        frappe.throw(_("Kho {0} không tồn tại").format(warehouse))

    wh = frappe.db.get_value("SC Warehouse", warehouse,
        ["map_rows", "map_cols", "warehouse_type", "site_block"], as_dict=True)

    bins = frappe.get_all("Bin Location",
        filters={"warehouse": warehouse},
        fields=["name", "bin_code", "zone", "aisle", "rack", "shelf",
                "map_row", "map_col", "status", "occupancy_pct",
                "current_qty", "capacity_qty", "is_quarantine",
                "temperature_controlled", "enabled"],
        order_by="map_row asc, map_col asc", limit=0)

    cells = []
    max_row = int(wh.map_rows or 0)
    max_col = int(wh.map_cols or 0)
    target_cell = None
    for b in bins:
        r = int(b.map_row or 0)
        c = int(b.map_col or 0)
        if r <= 0 or c <= 0:
            continue
        cell = {
            "row": r, "col": c,
            "bin": b.name,
            "bin_code": b.bin_code,
            "zone": b.zone or "", "aisle": b.aisle or "",
            "rack": b.rack or "", "shelf": b.shelf or "",
            "status": b.status or "Empty",
            "occupancy_pct": float(b.occupancy_pct or 0),
            "current_qty": float(b.current_qty or 0),
            "capacity_qty": float(b.capacity_qty or 0),
            "is_quarantine": int(b.is_quarantine or 0),
            "temperature_controlled": int(b.temperature_controlled or 0),
            "enabled": int(b.enabled or 0),
            "is_target": b.name == target_bin,
        }
        cells.append(cell)
        max_row = max(max_row, r)
        max_col = max(max_col, c)
        if cell["is_target"]:
            target_cell = {"row": r, "col": c}

    # Entrance kho: ô ảo phía trên lưới, cột giữa
    entrance = {"row": 0, "col": max(1, (max_col + 1) // 2)}

    path = []
    if target_cell:
        # đi ngang tới cột đích trước rồi đi dọc xuống — giống lối đi kho thật
        path = _manhattan_path(entrance, target_cell, vertical_first=False)

    return {
        "scope": "warehouse",
        "warehouse": warehouse,
        "warehouse_type": wh.warehouse_type or "",
        "block": wh.site_block or "",
        "rows": max_row,
        "cols": max_col,
        "entrance": entrance,
        "entrance_label": "Lối vào kho",
        "cells": cells,
        "target": target_cell,
        "target_bin": target_bin,
        "path": path,
    }


@frappe.whitelist()
def get_route(from_warehouse: str, to_warehouse: str) -> dict:
    """Chỉ đường chuyển kho A → B trên bản đồ khuôn viên.

    Dùng cho M6 Chuyển kho: hiển thị tuyến từ kho nguồn tới kho đích.
    """
    base = get_site_map(target_warehouse=to_warehouse)
    src = next((c for c in base["cells"] if c["warehouse"] == from_warehouse), None)
    dst = next((c for c in base["cells"] if c["warehouse"] == to_warehouse), None)
    if not src or not dst:
        base["route"] = []
        base["route_error"] = _("Một trong hai kho chưa có toạ độ trên bản đồ")
        return base
    src_pt = {"row": src["row"], "col": src["col"]}
    dst_pt = {"row": dst["row"], "col": dst["col"]}
    base["route"] = _manhattan_path(src_pt, dst_pt, vertical_first=True)
    base["route_from"] = from_warehouse
    base["route_to"] = to_warehouse
    base["from_cell"] = src_pt
    # path từ cổng không cần khi xem route chuyển kho → ghi đè
    base["path"] = base["route"]
    return base


@frappe.whitelist()
def list_mapped_warehouses() -> list:
    """List kho đã có sơ đồ bin (map_rows>0) — cho UI chọn xem."""
    return frappe.get_all("SC Warehouse",
        filters={"disabled": 0, "is_group": 0},
        fields=["name", "warehouse_type", "map_rows", "map_cols",
                "site_block", "site_row", "site_col"],
        order_by="warehouse_type asc, name asc", limit=0)
