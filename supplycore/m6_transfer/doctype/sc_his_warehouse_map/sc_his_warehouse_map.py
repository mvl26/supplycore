"""SC HIS Warehouse Map — ánh xạ tên kho HIS → SC Warehouse (UC-18B).

Dùng khi nhập phiếu chuyển kho từ HIS: tên kho in trên phiếu (vd
"Kho Khoa Điều trị Cao Cấp") được map sang kho nội bộ SupplyCore.
"""

import frappe
from frappe.model.document import Document


def _norm(name: str) -> str:
    """Chuẩn hoá tên kho để đối chiếu: gộp khoảng trắng + lowercase."""
    return " ".join((name or "").split()).strip().lower()


class SCHISWarehouseMap(Document):
    pass


def resolve_warehouse(his_name: str):
    """Trả SC Warehouse name cho 1 tên kho HIS, hoặc None nếu chưa map.

    So khớp không phân biệt hoa/thường và bỏ qua khoảng trắng thừa.
    """
    if not his_name:
        return None
    target = _norm(his_name)
    rows = frappe.get_all(
        "SC HIS Warehouse Map",
        filters={"disabled": 0},
        fields=["his_warehouse_name", "warehouse"],
    )
    for r in rows:
        if _norm(r.his_warehouse_name) == target:
            return r.warehouse
    return None
