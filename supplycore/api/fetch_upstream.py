"""SupplyCore — Fetch dữ liệu từ doc upstream để tạo doc downstream.

Khi tạo MR, PO, PR, PI, QI, SE, PD, SR... user có thể "Lấy từ" doc upstream để
auto-prefill header + items. Tránh nhập tay 2 lần — giống ERPNext "Get Items From".

Mapping được khai báo trong `MAPPINGS` dưới đây. Mỗi cặp (source_dt, target_dt)
xác định:
  - header_map: source field → target field
  - constants: target field → constant value
  - items: source child table + cách transform mỗi row
  - source_to_target_link: target field lưu reference ngược về source (vd material_request)

API: supplycore.api.fetch_upstream.fetch(source_doctype, source_name, target_doctype)
     supplycore.api.fetch_upstream.sources_for(target_doctype) → list các source khả dụng
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt


# Mỗi mapping: dict với các key:
#   header_map: {source_field: target_field}
#   constants:  {target_field: constant_value}
#   items: {
#     source_child_field: tên field child table trong source
#     row_map:    {source_col: target_col}
#     row_constants: {target_col: const}
#     row_filter: callable(row) -> bool (skip dòng đã hoàn thành)
#     qty_logic:  callable(row) -> qty for target (vd qty - received_qty)
#     target_field: tên field child table trong target (default 'items')
#   }
#   source_link_field: tên field trên target lưu source name (vd material_request)
#   description: hiển thị cho user

MAPPINGS: dict[tuple[str, str], dict] = {

    # ===== M1 Framework Contract → M2 Material Request =====
    ("Framework Contract", "SC Material Request"): {
        "description": "Lấy danh mục vật tư trong HĐ khung — tạo MR mua hàng theo SL còn lại",
        "constants": {"request_type": "Purchase"},
        "items": {
            "source_child_field": "items",  # FC.items (FC Item)
            "row_filter": lambda r: flt(r.get("remaining_qty") or r.get("contract_qty")) > 0,
            "row_map": {
                "item_code": "item",
                "uom": "uom",
                "unit_price": "estimated_unit_cost",
            },
            "qty_logic": lambda r: flt(r.get("remaining_qty") or r.get("contract_qty")),
            "qty_target": "qty",
            "row_constants_per_source": lambda src: {"framework_contract": src.name},
        },
    },

    # ===== M1 Framework Contract → M2 Purchase Order =====
    ("Framework Contract", "SC Purchase Order"): {
        "description": "Lấy NCC + vật tư + giá từ HĐ khung",
        "header_map": {
            "supplier": "supplier",
            "payment_terms": "payment_terms",
            "delivery_terms": "delivery_terms",
        },
        "source_link_field": "framework_contract",
        "items": {
            "source_child_field": "items",
            "row_filter": lambda r: flt(r.get("remaining_qty") or r.get("contract_qty")) > 0,
            "row_map": {
                "item_code": "item",
                "uom": "uom",
                "unit_price": "rate",
            },
            "qty_logic": lambda r: flt(r.get("remaining_qty") or r.get("contract_qty")),
            "qty_target": "qty",
            "row_constants": {"fc_unit_price_field": "unit_price"},  # marker — populate fc_unit_price
        },
    },

    # ===== M2 MR → M2 PO =====
    ("SC Material Request", "SC Purchase Order"): {
        "description": "Lấy items từ Yêu cầu mua đã duyệt",
        "source_link_field": "material_request",
        "header_map": {
            "schedule_date": "schedule_date",
        },
        "items": {
            "source_child_field": "items",
            "row_map": {
                "item": "item",
                "uom": "uom",
                "warehouse": "warehouse",
                "schedule_date": "schedule_date",
                "estimated_unit_cost": "rate",
                "framework_contract": "framework_contract_ref",  # informational
            },
            "qty_logic": lambda r: flt(r.get("qty")),
            "qty_target": "qty",
            # F01: kho đích dòng PO kế thừa 'Kho nhận' (header) của MR khi dòng MR
            # không có kho riêng — vẫn editable ở form PO.
            "row_enrich": lambda row, src: {
                "warehouse": row.get("warehouse") or src.get("warehouse"),
                "schedule_date": row.get("schedule_date") or src.get("schedule_date"),
            },
        },
    },

    # ===== M2 PO → M3 Purchase Receipt =====
    ("SC Purchase Order", "SC Purchase Receipt"): {
        "description": "Tạo phiếu nhập từ PO — SL còn lại = qty - received_qty",
        "source_link_field": "purchase_order",
        "header_map": {
            "supplier": "supplier",
            "to_warehouse": "to_warehouse",
        },
        "items": {
            "source_child_field": "items",
            "row_filter": lambda r: flt(r.get("qty")) - flt(r.get("received_qty") or 0) > 0,
            "row_map": {
                "item": "item",
                "uom": "uom",
                "rate": "rate",
                "warehouse": "warehouse",
            },
            "qty_logic": lambda r: flt(r.get("qty")) - flt(r.get("received_qty") or 0),
            "qty_target": "qty",
        },
    },

    # ===== M3 PR → M8 Purchase Invoice =====
    ("SC Purchase Receipt", "SC Purchase Invoice"): {
        "description": "Tạo hoá đơn từ phiếu nhập (3-way match)",
        "source_link_field": "purchase_receipt",
        "header_map": {
            "supplier": "supplier",
            "purchase_order": "purchase_order",
        },
        "items": {
            "source_child_field": "items",
            "row_filter": lambda r: flt(r.get("qty")) > 0,
            "row_map": {
                "item": "item",
                "uom": "uom",
                "rate": "rate",
            },
            "qty_logic": lambda r: flt(r.get("qty")),
            "qty_target": "qty",
        },
    },

    # ===== M3 PR → M3 QI (1 doc QI/lô) =====
    ("SC Purchase Receipt", "SC Quality Inspection"): {
        "description": "Tạo phiếu QC cho phiếu nhập",
        "source_link_field": "purchase_receipt",
        "header_map": {
            "supplier": "supplier",
        },
    },

    # ===== M6 TR → M6 Stock Entry =====
    ("SC Transfer Request", "SC Stock Entry"): {
        "description": "Chuyển kho theo Yêu cầu — entry_type = Material Transfer",
        "source_link_field": "transfer_request",
        "header_map": {
            "from_warehouse": "from_warehouse",
            "to_warehouse": "to_warehouse",
        },
        "constants": {"entry_type": "Material Transfer"},
        "items": {
            "source_child_field": "items",
            "row_filter": lambda r: flt(r.get("approved_qty") or r.get("requested_qty")) > 0,
            "row_map": {
                "item": "item",
                "uom": "uom",
                "batch": "batch",
            },
            "qty_logic": lambda r: flt(r.get("approved_qty") or r.get("requested_qty")),
            "qty_target": "qty",
            # Đơn giá lấy theo tồn kho nguồn của lô — gắn sẵn, không nhập tay
            "row_enrich": lambda row, src: {
                "valuation_rate": _stock_valuation(
                    row.get("item"), src.get("from_warehouse"), row.get("batch")),
            },
        },
    },

    # ===== M7 DR → M7 PD =====
    ("SC Dispensing Request", "SC Patient Dispensing"): {
        "description": "Cấp phát cho BN từ Yêu cầu cấp phát — pull items đã duyệt",
        "source_link_field": "dispensing_request",
        "header_map": {
            "patient": "patient",
            "department": "ward",
        },
        "items": {
            "source_child_field": "items",
            "row_filter": lambda r: flt(r.get("approved_qty") or r.get("requested_qty")) > 0,
            "row_map": {
                "item": "item",
                "uom": "uom",
                "batch": "batch",
                "warehouse": "warehouse",
            },
            "qty_logic": lambda r: flt(r.get("approved_qty") or r.get("requested_qty")),
            "qty_target": "qty",
        },
    },

    # ===== M9 ICS → M9 Stock Reconciliation =====
    ("SC Inventory Count Sheet", "SC Stock Reconciliation"): {
        "description": "Tạo phiếu điều chỉnh từ kiểm kê — lấy dòng có chênh lệch",
        "source_link_field": "count_sheet",
        "header_map": {
            "warehouse": "warehouse",
        },
        "items": {
            "source_child_field": "items",
            "row_filter": lambda r: abs(flt(r.get("counted_qty") or 0) - flt(r.get("system_qty") or 0)) > 0.001,
            "row_map": {
                "item": "item",
                "batch": "batch",
                "system_qty": "system_qty",
                "counted_qty": "counted_qty",
            },
            "qty_logic": lambda r: flt(r.get("counted_qty") or 0) - flt(r.get("system_qty") or 0),
            "qty_target": "variance_qty",
        },
    },
}


def _doctype_label(dt: str) -> str:
    try:
        return frappe.db.get_value("DocType", dt, "name") or dt
    except Exception:
        return dt


def _stock_valuation(item, warehouse, batch=None):
    """Đơn giá tồn kho của 1 item/lô tại 1 kho — valuation_rate SLE gần nhất.
    Dùng để gắn sẵn đơn giá lô khi tạo Phiếu chuyển kho (không nhập tay)."""
    if not item or not warehouse:
        return 0.0
    conds = ["item = %(i)s", "warehouse = %(w)s", "is_cancelled = 0", "valuation_rate > 0"]
    params = {"i": item, "w": warehouse}
    if batch:
        conds.append("batch = %(b)s")
        params["b"] = batch
    v = frappe.db.sql(f"""
        SELECT valuation_rate FROM `tabSC Stock Ledger Entry`
        WHERE {' AND '.join(conds)}
        ORDER BY posting_date DESC, creation DESC LIMIT 1
    """, params)
    return flt(v[0][0]) if v else 0.0


@frappe.whitelist()
def sources_for(target_doctype: str) -> list[dict]:
    """List các source doctype có thể fetch tới target này."""
    out = []
    for (src, tgt), spec in MAPPINGS.items():
        if tgt != target_doctype:
            continue
        if not frappe.db.exists("DocType", src):
            continue
        if not frappe.has_permission(src, "read"):
            continue
        out.append({
            "source_doctype": src,
            "label": _doctype_label(src),
            "description": spec.get("description", ""),
            "has_items": "items" in spec,
            "source_link_field": spec.get("source_link_field", ""),
        })
    return out


@frappe.whitelist()
def fetch(source_doctype: str, source_name: str, target_doctype: str) -> dict:
    """Fetch từ source doc → trả về dict {header, items} để FE merge vào form."""
    spec = MAPPINGS.get((source_doctype, target_doctype))
    if not spec:
        frappe.throw(_("Không hỗ trợ fetch {0} → {1}").format(source_doctype, target_doctype))

    if not frappe.has_permission(source_doctype, "read", doc=source_name):
        frappe.throw(_("Không có quyền đọc {0} {1}").format(source_doctype, source_name),
                     frappe.PermissionError)
    if not frappe.has_permission(target_doctype, "create"):
        frappe.throw(_("Không có quyền tạo {0}").format(target_doctype),
                     frappe.PermissionError)

    source = frappe.get_doc(source_doctype, source_name)

    # === Header ===
    header: dict = {}
    for src_f, tgt_f in (spec.get("header_map") or {}).items():
        v = source.get(src_f)
        if v is not None and v != "":
            header[tgt_f] = v
    for k, v in (spec.get("constants") or {}).items():
        header[k] = v
    if spec.get("source_link_field"):
        header[spec["source_link_field"]] = source.name

    # === Items ===
    items: list[dict] = []
    items_spec = spec.get("items")
    if items_spec:
        src_rows = source.get(items_spec["source_child_field"]) or []
        row_filter = items_spec.get("row_filter") or (lambda r: True)
        row_map = items_spec.get("row_map") or {}
        qty_logic = items_spec.get("qty_logic")
        qty_target = items_spec.get("qty_target", "qty")
        per_src_const = items_spec.get("row_constants_per_source")
        per_src_const_dict = per_src_const(source) if callable(per_src_const) else {}

        for r in src_rows:
            r_d = r.as_dict() if hasattr(r, "as_dict") else dict(r)
            try:
                if not row_filter(r_d):
                    continue
            except Exception:
                pass
            row: dict = {}
            for src_c, tgt_c in row_map.items():
                v = r_d.get(src_c)
                if v is not None and v != "":
                    row[tgt_c] = v
            if qty_logic:
                try:
                    q = qty_logic(r_d)
                    if q > 0:
                        row[qty_target] = q
                except Exception:
                    pass
            row.update(per_src_const_dict)
            # row_enrich: bổ sung field tính toán theo từng dòng (vd: đơn giá lô)
            enrich = items_spec.get("row_enrich")
            if callable(enrich) and row:
                try:
                    for ek, ev in (enrich(row, source) or {}).items():
                        if ev is not None and ev != "":
                            row[ek] = ev
                except Exception:
                    pass
            if row:
                items.append(row)

    return {
        "header": header,
        "items": items,
        "source": {
            "doctype": source_doctype,
            "name": source.name,
            "label": _doctype_label(source_doctype),
        },
    }


@frappe.whitelist()
def list_candidates(source_doctype: str, target_doctype: str,
                     search: str = "", limit: int = 20) -> list[dict]:
    """List các source doc có thể chọn để fetch.
    Mặc định: docstatus=1 (submitted) hoặc 0 (draft) tuỳ doctype.
    """
    if (source_doctype, target_doctype) not in MAPPINGS:
        frappe.throw(_("Mapping không hợp lệ"))
    if not frappe.has_permission(source_doctype, "read"):
        frappe.throw(_("Không có quyền"), frappe.PermissionError)

    filters: dict = {}
    # Theo mặc định: chỉ pick submitted (docstatus=1) hoặc đã duyệt.
    # Riêng Framework Contract: status=Active.
    meta = frappe.get_meta(source_doctype)
    if meta.is_submittable:
        filters["docstatus"] = 1
    if source_doctype == "Framework Contract":
        filters["status"] = "Active"
    elif source_doctype == "SC Material Request":
        # Chỉ MR mua hàng ĐÃ DUYỆT và CHƯA đặt đủ (F05: ẩn MR đã 'Ordered').
        filters["request_type"] = "Purchase"
        filters["status"] = "Approved"
    elif source_doctype == "SC Purchase Order":
        # PO đã gửi NCC nhưng chưa nhận hết
        filters["status"] = ["in", ["Sent to Supplier", "Partially Received", "Approved"]]

    or_filters = []
    if search:
        or_filters = [["name", "like", f"%{search}%"]]
        # Một số doctype có trường tên/số phụ
        if source_doctype == "Framework Contract":
            or_filters.append(["contract_number", "like", f"%{search}%"])
        if source_doctype == "SC Purchase Order":
            or_filters.append(["supplier", "like", f"%{search}%"])

    # Fields cho display
    base_fields = ["name", "modified"]
    extra = {
        # F02: kèm supplier_name để panel nguồn hiện Tên NCC (mã phụ)
        "Framework Contract": ["contract_number", "supplier", "supplier_name", "valid_to", "remaining_value"],
        "SC Material Request": ["transaction_date", "schedule_date", "warehouse"],
        "SC Purchase Order": ["transaction_date", "supplier", "supplier_name", "grand_total", "status"],
        "SC Purchase Receipt": ["posting_date", "supplier", "supplier_name", "to_warehouse"],
        "SC Transfer Request": ["request_date", "from_warehouse", "to_warehouse"],
        "SC Dispensing Request": ["request_date", "department", "from_warehouse"],
        "SC Inventory Count Sheet": ["posting_date", "warehouse", "count_type"],
    }.get(source_doctype, [])

    fields = list({*base_fields, *extra})
    try:
        rows = frappe.get_all(source_doctype,
                               filters=filters,
                               or_filters=or_filters or None,
                               fields=fields,
                               order_by="modified desc",
                               limit=int(limit) or 20)
    except Exception:
        rows = frappe.get_all(source_doctype, filters=filters,
                               fields=["name"], limit=int(limit) or 20)
    return rows
