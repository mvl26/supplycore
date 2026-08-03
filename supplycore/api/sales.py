"""API bán hàng M7 Sales — supplycore.api.sales.* (GĐ2 Task 9).

Endpoint canonical (gọi qua /api/method/supplycore.api.sales.<func>):
  customer_upsert, sales_framework_create, sales_order_approve,
  delivery_create, delivery_accept, sales_invoice_create, receipt_collect.

App KHÔNG có lớp alias `scm.*` riêng — mọi API hiện có (kpi.py, frontend.py,
users.py...) đều được frontend/gọi trực tiếp qua đường dẫn dotted path
`supplycore.api.<module>.<func>` (whitelisted method chuẩn của Frappe). Vì vậy
các hàm ở đây cũng expose trực tiếp `supplycore.api.sales.*`, KHÔNG cần alias
`scm.*` bổ sung — mirror đúng cách frontend.py/kpi.py đã làm.

Mỗi hàm: kiểm quyền (frappe.has_permission) → áp rule nghiệp vụ (ủy quyền cho
controller doctype qua insert()/submit()/method) → trả tên doc / kết quả chính.
Ngoại lệ nghiệp vụ (frappe.ValidationError, BRU-*) được để propagate nguyên
văn cho caller xử lý — không nuốt lỗi.
"""

import frappe
from frappe import _
from frappe.utils import flt, today


def _to_dict(data):
    """Chấp nhận data là dict HOẶC json string (mirror convention app hiện có)."""
    if isinstance(data, str):
        data = frappe.parse_json(data)
    return data or {}


# ---------------------------------------------------------------------------
# 1. Customer upsert
# ---------------------------------------------------------------------------
@frappe.whitelist()
def customer_upsert(data) -> str:
    """Tạo mới hoặc cập nhật SC Customer.

    data: dict/json {name?, customer_name, tax_code, credit_limit, billing_address,
                      shipping_address, payment_terms, status, portal_user}
    - Nếu data.name (hoặc name đã tồn tại) → load + cập nhật (cần quyền write).
    - Nếu không có name nhưng tax_code khớp customer đã tồn tại → cập nhật customer đó.
    - Ngược lại → tạo mới (cần quyền create).
    Trả về: tên (name) của SC Customer.
    """
    data = _to_dict(data)
    name = data.get("name")
    if not name and data.get("tax_code"):
        name = frappe.db.get_value("SC Customer", {"tax_code": data["tax_code"]}, "name")

    editable_fields = (
        "customer_name", "tax_code", "billing_address", "shipping_address",
        "credit_limit", "payment_terms", "status", "portal_user",
    )

    if name and frappe.db.exists("SC Customer", name):
        if not frappe.has_permission("SC Customer", "write", doc=name):
            frappe.throw(_("Không có quyền sửa SC Customer {0}").format(name),
                         frappe.PermissionError)
        doc = frappe.get_doc("SC Customer", name)
        for f in editable_fields:
            if f in data:
                doc.set(f, data[f])
        doc.save()
        return doc.name

    if not frappe.has_permission("SC Customer", "create"):
        frappe.throw(_("Không có quyền tạo SC Customer"), frappe.PermissionError)
    doc = frappe.new_doc("SC Customer")
    for f in editable_fields:
        if f in data:
            doc.set(f, data[f])
    doc.insert()
    return doc.name


# ---------------------------------------------------------------------------
# 2. Sales Framework Contract create
# ---------------------------------------------------------------------------
@frappe.whitelist()
def sales_framework_create(data) -> str:
    """Tạo SC Sales Framework Contract kèm items; submit nếu data.submit truthy.

    data: {customer, valid_from?, valid_to?, items:[{item, uom, contract_qty,
           unit_price}], submit?}
    Trả về: tên (name) của SC Sales Framework Contract.
    """
    data = _to_dict(data)
    if not frappe.has_permission("SC Sales Framework Contract", "create"):
        frappe.throw(_("Không có quyền tạo Hợp đồng khung bán hàng"), frappe.PermissionError)

    doc = frappe.new_doc("SC Sales Framework Contract")
    doc.customer = data.get("customer")
    doc.valid_from = data.get("valid_from") or today()
    doc.valid_to = data.get("valid_to")
    for row in (data.get("items") or []):
        doc.append("items", {
            "item": row.get("item"),
            "uom": row.get("uom"),
            "contract_qty": flt(row.get("contract_qty")),
            "unit_price": flt(row.get("unit_price")),
        })
    doc.insert()
    if data.get("submit"):
        doc.submit()
    return doc.name


# ---------------------------------------------------------------------------
# 3. Sales Order approve
# ---------------------------------------------------------------------------
@frappe.whitelist()
def sales_order_approve(name) -> dict:
    """Duyệt SC Sales Order đã submit — ủy quyền cho SCSalesOrder.approve()."""
    if not frappe.has_permission("SC Sales Order", "submit", doc=name):
        frappe.throw(_("Không có quyền duyệt Đơn hàng bán {0}").format(name),
                     frappe.PermissionError)
    doc = frappe.get_doc("SC Sales Order", name)
    return doc.approve()


# ---------------------------------------------------------------------------
# 4. Delivery Note create + submit
# ---------------------------------------------------------------------------
@frappe.whitelist()
def make_delivery(sales_order, from_warehouse=None, delivery_date=None, submit=1) -> dict:
    """Nút 'Tạo phiếu giao' trên SC Sales Order.

    Wrapper kwargs-phẳng cho ActionPanel (delivery_create nhận dict `data` không
    hợp injection phẳng). Copy đầy đủ dòng hàng/SL từ SO; batch do controller DN
    tự FEFO auto-pick. from_warehouse rỗng → lấy Settings.default_warehouse.

    submit=1 (mặc định): tạo + submit ngay (giữ hành vi cũ cho test/seed/luồng
    tự động). submit=0: tạo NHÁP cần soạn hàng (picking_required=1) — nhân viên
    kho quét xác nhận từng dòng rồi mới submit.
    Trả {name} để ActionPanel navigate sang DN vừa tạo.
    """
    if not from_warehouse:
        # Fallback: kho SC Warehouse không-group đầu tiên (Settings.default_warehouse
        # là Link 'Warehouse' ERPNext — không dùng ở app no-ERPNext). Nhân viên nên
        # nhập kho xuất rõ ràng; fallback chỉ để nút không lỗi khi bỏ trống.
        from_warehouse = frappe.db.get_value(
            "SC Warehouse", {"is_group": 0, "disabled": 0}, "name", order_by="name")
    dn_name = delivery_create({
        "sales_order": sales_order,
        "from_warehouse": from_warehouse,
        "delivery_date": delivery_date,
    }, submit=submit)
    return {"name": dn_name}


@frappe.whitelist()
def delivery_create(data, submit=1) -> str:
    """Tạo SC Delivery Note từ SC Sales Order.

    data: {sales_order, from_warehouse, delivery_date?, items?}
    Nếu items không truyền → suy ra từ SO Item (item, uom, qty đầy đủ theo SO);
    batch được controller tự FEFO auto-pick (gợi ý, sửa được ở luồng soạn hàng).

    submit=1 (mặc định): insert + submit ngay (trừ tồn kho luôn) — giữ hành vi cũ.
    submit=0: chỉ insert NHÁP với picking_required=1 (chờ quét xác nhận từng
    dòng qua confirm_pick_line, đủ mới submit → trừ tồn ở bước submit đó).
    Trả về: tên (name) của SC Delivery Note.
    """
    from frappe.utils import cint
    data = _to_dict(data)
    if not frappe.has_permission("SC Delivery Note", "create"):
        frappe.throw(_("Không có quyền tạo Phiếu giao hàng"), frappe.PermissionError)

    sales_order = data.get("sales_order")
    doc = frappe.new_doc("SC Delivery Note")
    doc.sales_order = sales_order
    doc.from_warehouse = data.get("from_warehouse")
    doc.delivery_date = data.get("delivery_date") or today()
    doc.picking_required = 0 if cint(submit) else 1

    items = data.get("items")
    if not items:
        so_items = frappe.get_all("SO Item", filters={"parent": sales_order},
                                   fields=["item", "uom", "qty"])
        items = [{"item": r.item, "uom": r.uom, "qty": r.qty} for r in so_items]

    for row in items:
        doc.append("items", {
            "item": row.get("item"),
            "uom": row.get("uom"),
            "qty": flt(row.get("qty")),
            "batch": row.get("batch"),
            "warehouse": row.get("warehouse"),
        })
    doc.insert()
    if cint(submit):
        doc.submit()
    elif sales_order:
        # Đánh dấu SO "Đang xử lý" → nút "Tạo phiếu giao" (when: status=="Đã duyệt")
        # ẩn đi, tránh tạo TRÙNG phiếu giao nháp → trừ tồn 2 lần. Khôi phục
        # "Đã duyệt" khi hủy (on_cancel) hoặc xóa phiếu nháp (on_trash).
        frappe.db.set_value("SC Sales Order", sales_order, "status", "Đang xử lý")
    return doc.name


# ---------------------------------------------------------------------------
# 5. Acceptance Record create + submit
# ---------------------------------------------------------------------------
@frappe.whitelist()
def delivery_accept(delivery_note, accepted_by=None, note=None) -> str:
    """Tạo + submit SC Acceptance Record cho 1 Phiếu giao hàng. Trả tên biên bản."""
    if not frappe.has_permission("SC Acceptance Record", "create"):
        frappe.throw(_("Không có quyền lập biên bản nghiệm thu"), frappe.PermissionError)

    doc = frappe.new_doc("SC Acceptance Record")
    doc.delivery_note = delivery_note
    doc.acceptance_date = today()
    doc.accepted_by = accepted_by
    doc.note = note
    doc.insert()
    doc.submit()
    return doc.name


# ---------------------------------------------------------------------------
# 6. Sales Invoice create + submit
# ---------------------------------------------------------------------------
@frappe.whitelist()
def sales_invoice_create(delivery_note, tax_rate: float = 0) -> dict:
    """Tạo + submit SC Sales Invoice từ 1 DN đã nghiệm thu — items + đơn giá suy
    ra từ DN Item (số lượng) khớp với SO Item (đơn giá theo SFC).

    Trả về: {name, grand_total}.
    """
    if not frappe.has_permission("SC Sales Invoice", "create"):
        frappe.throw(_("Không có quyền lập hóa đơn bán hàng"), frappe.PermissionError)

    dn = frappe.get_doc("SC Delivery Note", delivery_note)

    dn_qty_by_item = {}
    for r in dn.items:
        dn_qty_by_item[r.item] = flt(dn_qty_by_item.get(r.item, 0)) + flt(r.qty)

    price_by_item = {}
    if dn.sales_order:
        for r in frappe.get_all("SO Item", filters={"parent": dn.sales_order},
                                  fields=["item", "unit_price"]):
            price_by_item[r.item] = flt(r.unit_price)

    doc = frappe.new_doc("SC Sales Invoice")
    doc.customer = dn.customer or frappe.db.get_value(
        "SC Sales Order", dn.sales_order, "customer")
    doc.delivery_note = dn.name
    doc.invoice_date = today()
    doc.tax_rate = flt(tax_rate)
    for item, qty in dn_qty_by_item.items():
        doc.append("items", {
            "item": item, "qty": qty,
            "unit_price": price_by_item.get(item, 0),
        })
    doc.insert()
    doc.submit()
    doc.reload()
    return {"name": doc.name, "grand_total": flt(doc.grand_total)}


# ---------------------------------------------------------------------------
# 7. Sales Receipt create + submit
# ---------------------------------------------------------------------------
@frappe.whitelist()
def receipt_collect(sales_invoice, amount, mode: str = "Chuyển khoản") -> dict:
    """Tạo + submit SC Sales Receipt thu tiền cho 1 hóa đơn bán hàng.

    Trả về: {name, outstanding} (outstanding_amount của SI sau khi thu).
    """
    if not frappe.has_permission("SC Sales Receipt", "create"):
        frappe.throw(_("Không có quyền lập phiếu thu"), frappe.PermissionError)

    customer = frappe.db.get_value("SC Sales Invoice", sales_invoice, "customer")

    doc = frappe.new_doc("SC Sales Receipt")
    doc.customer = customer
    doc.sales_invoice = sales_invoice
    doc.receipt_date = today()
    doc.amount = flt(amount)
    doc.mode = mode
    doc.insert()
    doc.submit()

    outstanding = frappe.db.get_value("SC Sales Invoice", sales_invoice, "outstanding_amount")
    return {"name": doc.name, "outstanding": flt(outstanding)}


@frappe.whitelist()
def sales_framework_items(framework_contract: str) -> list:
    """Danh mục vật tư của 1 HĐ khung bán — dùng cho màn Đơn bán:
    (1) tự nạp chi tiết vào đơn khi chọn HĐ khung,
    (2) lọc ô chọn Vật tư ở dòng chi tiết chỉ trong HĐ khung (yêu cầu #5).

    Trả về mỗi dòng: item, item_name, uom, unit_price, remaining_qty, contract_qty.
    unit_price lấy đúng theo HĐ khung (BRU-SFC-002 — server ghi đè lại khi lưu)."""
    from supplycore.utils.permissions import block_portal
    block_portal()
    if not frappe.has_permission("SC Sales Framework Contract", "read"):
        frappe.throw(_("Không có quyền đọc HĐ khung bán"), frappe.PermissionError)
    if not framework_contract:
        return []
    rows = frappe.get_all(
        "SFC Item",
        filters={"parent": framework_contract, "parenttype": "SC Sales Framework Contract"},
        fields=["item", "uom", "unit_price", "contract_qty", "remaining_qty"],
        order_by="idx asc",
    )
    for r in rows:
        r["item_name"] = frappe.db.get_value("SC Item", r["item"], "item_name") or r["item"]
        r["unit_price"] = flt(r.get("unit_price"))
        r["remaining_qty"] = flt(r.get("remaining_qty"))
        r["contract_qty"] = flt(r.get("contract_qty"))
    return rows
