"""Backend API cho SupplyCore SPA frontend.

Frappe v15 strict field whitelist trên /api/resource/<dt> chặn nhiều custom
fields. Frontend cần linh hoạt query bất kỳ field nào — wrap qua đây với
frappe.db.get_all (bypass field validation, nhưng vẫn check role permissions).
"""

import frappe
from frappe import _
from frappe.utils import flt

from supplycore.utils.permissions import block_portal


@frappe.whitelist()
def list_docs(doctype, fields=None, filters=None, order_by=None, limit=20, start=0, or_filters=None):
    """List docs với fields linh hoạt — bypass Frappe.client.get_list whitelist.

    Vẫn check role permission qua frappe.has_permission.
    or_filters: list điều kiện OR (vd tìm theo mã HOẶC tên) — L11/T05.

    RSK-01 (phát hiện task-5 completeness sweep, sibling gap của data_io.py):
    dù truyền `ignore_permissions=False`, `frappe.db.get_all` → `frappe.get_all`
    LUÔN ghi đè `kwargs["ignore_permissions"] = True` (frappe/__init__.py) trước
    khi gọi `get_list` — nghĩa là `permission_query_conditions` (cơ chế cô lập
    khách hàng cho 5 doctype bán hàng, xem utils/permissions.py) KHÔNG BAO GIỜ
    được áp dụng ở đây, bất kể tham số truyền vào. Chỉ còn lại
    `frappe.has_permission(doctype, "read")` doctype-level — mà role
    "SC Customer Portal" có read=1 trên cả 5 doctype đó. Phải `block_portal()`
    giống hệt `count_docs` bên dưới (cùng lý do, cùng doctype phạm vi).
    """
    block_portal()
    if not frappe.has_permission(doctype, "read"):
        frappe.throw(_("Không có quyền đọc {0}").format(doctype), frappe.PermissionError)

    import json
    if isinstance(fields, str):
        fields = json.loads(fields)
    if isinstance(filters, str):
        filters = json.loads(filters)
    if isinstance(or_filters, str):
        or_filters = json.loads(or_filters)

    fields = fields or ["name"]
    filters = filters or {}

    try:
        kwargs = dict(
            fields=fields,
            filters=filters,
            order_by=order_by or "modified desc",
            limit=int(limit) if limit else None,
            start=int(start) if start else 0,
            ignore_permissions=False,
        )
        if or_filters:
            kwargs["or_filters"] = or_filters
        rows = frappe.db.get_all(doctype, **kwargs)
        _attach_list_customer_names(doctype, rows)
        return rows
    except Exception as e:
        frappe.log_error(message=f"list_docs({doctype}): {e}", title="frontend.list_docs")
        frappe.throw(_("Lỗi truy vấn {0}: {1}").format(doctype, str(e)[:200]))


# Doctype bán hàng hiện cột "Khách hàng" — cần TÊN thay vì mã (không lưu
# customer_name, chỉ có link customer). displayKey='customer_name' ở modules.js.
_LIST_CUSTOMER_NAME_DTS = {
    "SC Sales Order", "SC Delivery Note", "SC Sales Invoice", "SC Sales Receipt",
    "SC Acceptance Record", "SC Sales Framework Contract",
}


def _attach_list_customer_names(doctype, rows):
    """Đính kèm customer_name cho mỗi dòng list bán hàng (1 truy vấn batch)."""
    if doctype not in _LIST_CUSTOMER_NAME_DTS or not rows:
        return
    codes = {r.get("customer") for r in rows if r.get("customer")}
    if not codes:
        return
    names = dict(frappe.db.get_all(
        "SC Customer", filters={"name": ["in", list(codes)]},
        fields=["name", "customer_name"], as_list=True))
    for r in rows:
        c = r.get("customer")
        if c:
            r["customer_name"] = names.get(c) or c


@frappe.whitelist()
def search_framework_contract(q=None, limit=20):
    """L11: tìm HĐ khung theo mã HĐ, số HĐ, mã NCC, tên NCC, và MÃ/TÊN VẬT TƯ
    trong danh mục (child) — điều mà or_filters đơn giản không làm được."""
    if not frappe.has_permission("Framework Contract", "read"):
        frappe.throw(_("Không có quyền đọc HĐ khung"), frappe.PermissionError)
    q = (q or "").strip()
    params = {"lim": int(limit or 20)}
    cond = ""
    if q:
        params["like"] = f"%{q}%"
        cond = """WHERE fc.name LIKE %(like)s
                  OR fc.supplier LIKE %(like)s
                  OR fc.supplier_name LIKE %(like)s
                  OR fc.contract_number LIKE %(like)s
                  OR EXISTS (
                     SELECT 1 FROM `tabFC Item` fci
                     WHERE fci.parent = fc.name
                       AND (fci.item_code LIKE %(like)s OR fci.item_name LIKE %(like)s)
                  )"""
    return frappe.db.sql(f"""
        SELECT fc.name, fc.contract_number, fc.supplier_name
        FROM `tabFramework Contract` fc
        {cond}
        ORDER BY fc.modified DESC
        LIMIT %(lim)s
    """, params, as_dict=True)


@frappe.whitelist()
def search_sales_framework_contract(q=None, limit=20, customer=None):
    """M7 UX: tìm HĐ khung BÁN theo TÊN khách hàng (chính), mã HĐ, mã khách,
    và mã/tên vật tư trong danh mục (child) — trả kèm customer_name để hiển thị
    tường minh (SFC không có field tên riêng, chỉ định danh bằng khách + kỳ).
    Mirror search_framework_contract (chiều mua).

    customer: nếu truyền → chỉ trả HĐ khung của khách đó (dùng khi màn Đơn bán
    đã chọn khách trước — lọc HĐ khung theo khách, yêu cầu #5)."""
    # SQL thô bỏ qua permission_query_conditions → chặn Portal (nếu không, portal
    # user thấy HĐ + tên KH của MỌI khách — rò chéo BRU-SEC-001). Nội bộ SPA dùng.
    block_portal()
    if not frappe.has_permission("SC Sales Framework Contract", "read"):
        frappe.throw(_("Không có quyền đọc HĐ khung bán"), frappe.PermissionError)
    q = (q or "").strip()
    params = {"lim": int(limit or 20)}
    conds = []
    if customer:
        params["customer"] = customer
        conds.append("sfc.customer = %(customer)s")
    if q:
        params["like"] = f"%{q}%"
        conds.append("""(sfc.name LIKE %(like)s
                  OR sfc.customer LIKE %(like)s
                  OR cust.customer_name LIKE %(like)s
                  OR EXISTS (
                     SELECT 1 FROM `tabSFC Item` sfci
                     WHERE sfci.parent = sfc.name
                       AND sfci.item LIKE %(like)s
                  ))""")
    cond = ("WHERE " + " AND ".join(conds)) if conds else ""
    return frappe.db.sql(f"""
        SELECT sfc.name, sfc.customer, cust.customer_name,
               sfc.valid_from, sfc.valid_to, sfc.status
        FROM `tabSC Sales Framework Contract` sfc
        LEFT JOIN `tabSC Customer` cust ON cust.name = sfc.customer
        {cond}
        ORDER BY sfc.modified DESC
        LIMIT %(lim)s
    """, params, as_dict=True)


# M7 UX: các chứng từ bán hàng tham chiếu (SO/DN/SI) — hiện TÊN khách + ngày
# thay vì chỉ mã doc. field (date, amount) lấy từ whitelist này (an toàn khỏi
# SQL injection vì doctype + field đều từ config server-side, không từ client).
_SALES_DOC_SEARCH = {
    "SC Sales Order":   ("order_date",   "total_amount"),
    "SC Delivery Note": ("delivery_date", None),
    "SC Sales Invoice": ("invoice_date", "grand_total"),
}


@frappe.whitelist()
def search_sales_doc(doctype, q=None, limit=20):
    """Tìm chứng từ bán hàng (SO/DN/SI) theo mã, mã khách, hoặc TÊN khách —
    trả kèm customer_name + ngày + số tiền để hiển thị tường minh trong droplist."""
    cfg = _SALES_DOC_SEARCH.get(doctype)
    if not cfg:
        frappe.throw(_("Doctype {0} không hỗ trợ tìm kiếm bán hàng").format(doctype))
    # SQL thô bỏ qua permission_query → chặn Portal (rò chéo khách, BRU-SEC-001).
    block_portal()
    if not frappe.has_permission(doctype, "read"):
        frappe.throw(_("Không có quyền đọc {0}").format(doctype), frappe.PermissionError)
    date_field, amount_field = cfg
    q = (q or "").strip()
    params = {"lim": int(limit or 20)}
    cond = ""
    if q:
        params["like"] = f"%{q}%"
        cond = ("WHERE d.name LIKE %(like)s OR d.customer LIKE %(like)s "
                "OR cust.customer_name LIKE %(like)s")
    amount_sel = f"d.`{amount_field}` AS amount" if amount_field else "NULL AS amount"
    return frappe.db.sql(f"""
        SELECT d.name, d.customer, cust.customer_name,
               d.`{date_field}` AS ref_date, {amount_sel}, d.status
        FROM `tab{doctype}` d
        LEFT JOIN `tabSC Customer` cust ON cust.name = d.customer
        {cond}
        ORDER BY d.modified DESC
        LIMIT %(lim)s
    """, params, as_dict=True)


@frappe.whitelist()
def get_doc(doctype, name):
    """Get full doc + child tables."""
    if not frappe.has_permission(doctype, "read", doc=name):
        frappe.throw(_("Không có quyền đọc {0} {1}").format(doctype, name), frappe.PermissionError)
    d = frappe.get_doc(doctype, name).as_dict()
    _attach_display_names(doctype, d)
    return d


def _attach_display_names(doctype, d):
    """M7 UX: đính kèm TÊN hiển thị cho các link chính (khách hàng, HĐ khung bán)
    để MÀN CHI TIẾT hiện tên thay vì mã doc. SO/DN/SI/SR không lưu customer_name
    (chỉ có link customer) nên phải resolve tại đây. Chỉ 1-2 truy vấn nhẹ khi mở
    chi tiết; không đụng doctype mua (framework_contract của bên mua trỏ
    'Framework Contract' khác — exists() bên dưới trả False nên bỏ qua)."""
    if doctype != "SC Customer" and d.get("customer") and not d.get("customer_name"):
        d["customer_name"] = frappe.db.get_value("SC Customer", d["customer"], "customer_name")
    fc = d.get("framework_contract")
    if fc and frappe.db.exists("SC Sales Framework Contract", fc):
        row = frappe.db.get_value(
            "SC Sales Framework Contract", fc, ["customer", "valid_to"], as_dict=True)
        if row:
            cn = frappe.db.get_value("SC Customer", row.customer, "customer_name") or row.customer
            # Hiện TÊN khách + SỐ HĐ (fc = SC-SFC-YYYY-#####) + kỳ hiệu lực.
            d["framework_contract_display"] = (
                f"{cn} — {fc} (đến {row.valid_to})" if row.valid_to else f"{cn} — {fc}")


@frappe.whitelist()
def count_docs(doctype, filters=None, or_filters=None):
    """Count docs.

    GĐ4 Task 5 (security sweep): `frappe.db.count()` KHÔNG áp
    `permission_query_conditions` (khác `frappe.db.get_all`/`list_docs` ở
    trên) — chỉ check quyền doctype-level. Với 5 doctype bán hàng, role
    Portal CÓ read=1 doctype-level (bị lọc theo khách hàng chỉ ở list-query),
    nên nếu không chặn riêng, portal user gọi thẳng count_docs sẽ đếm được
    TỔNG số đơn/hoá đơn... của TOÀN BỘ khách hàng (rò rỉ quy mô kinh doanh
    liên khách hàng). Hàm này chỉ dùng nội bộ (SPA `frontend/src/api.js`),
    Portal khách không cần và không được gọi.
    """
    block_portal()
    if not frappe.has_permission(doctype, "read"):
        frappe.throw(_("Không có quyền").format(doctype), frappe.PermissionError)
    import json
    if isinstance(filters, str):
        filters = json.loads(filters)
    if isinstance(or_filters, str):
        or_filters = json.loads(or_filters)
    if or_filters:
        # frappe.db.count không nhận or_filters → dùng get_all (áp cả
        # permission_query_conditions) rồi đếm. App quy mô nhỏ nên OK.
        return len(frappe.get_all(doctype, filters=filters or {}, or_filters=or_filters,
                                  pluck="name", limit=0))
    return frappe.db.count(doctype, filters=filters or {})


@frappe.whitelist()
def submit_doc(doctype, name):
    """Submit doc — tránh TimestampMismatchError do client-side fetch dance.

    frappe.client.submit() yêu cầu pass full doc dict + modified timestamp;
    nếu doc bị modify giữa fetch và submit → TimestampMismatchError.
    Wrapper này fetch fresh + submit trong cùng request.
    """
    if not frappe.has_permission(doctype, "submit", doc=name):
        frappe.throw(_("Không có quyền submit {0} {1}").format(doctype, name),
                      frappe.PermissionError)
    doc = frappe.get_doc(doctype, name)
    doc.submit()
    return doc.as_dict()


@frappe.whitelist()
def cancel_doc(doctype, name):
    """Cancel doc — tương tự submit_doc."""
    if not frappe.has_permission(doctype, "cancel", doc=name):
        frappe.throw(_("Không có quyền cancel {0} {1}").format(doctype, name),
                      frappe.PermissionError)
    doc = frappe.get_doc(doctype, name)
    doc.cancel()
    return doc.as_dict()


@frappe.whitelist()
def related_docs(doctype, name):
    """Trả related/reverse-link docs cho 1 doc cụ thể.

    Mapping mỗi doctype → related queries:
    - Framework Contract → POs link FC + items
    - SC Purchase Order → PRs + PIs + MR liên quan
    - SC Purchase Receipt → QIs + Batches + PI
    - SC Quality Inspection → PR + Item
    - SC Item → Batches + recent SLE
    - SC Batch → SLE + Recall + Trace movements
    """
    block_portal()
    out = {}
    if not frappe.has_permission(doctype, "read", doc=name):
        frappe.throw(_("Không có quyền đọc {0}").format(doctype), frappe.PermissionError)

    if doctype == "Framework Contract":
        out["purchase_orders"] = frappe.db.get_all("SC Purchase Order",
            filters={"framework_contract": name},
            fields=["name", "transaction_date", "supplier", "grand_total", "status", "docstatus"],
            order_by="transaction_date desc", limit=20)

    elif doctype == "SC Purchase Order":
        out["material_requests"] = frappe.db.get_all("SC Material Request Item",
            filters={"po": name} if frappe.db.has_column("SC Material Request Item", "po") else {},
            fields=["parent"], limit=10) if frappe.db.has_column("SC Material Request Item", "po") else []
        out["purchase_receipts"] = frappe.db.get_all("SC Purchase Receipt",
            filters={"purchase_order": name},
            fields=["name", "posting_date", "supplier", "is_return", "qc_status", "docstatus"],
            order_by="posting_date desc", limit=20)

    elif doctype == "SC Purchase Receipt":
        out["quality_inspections"] = frappe.db.get_all("SC Quality Inspection",
            filters={"purchase_receipt": name},
            fields=["name", "inspection_date", "item", "supplier", "batch", "overall_status", "docstatus"],
            order_by="inspection_date desc", limit=50)
        # Batches từ PR Item
        out["batches"] = frappe.db.sql("""
            SELECT DISTINCT pri.batch_no AS name, b.item, b.supplier_batch_no,
                   b.expiry_date, b.qc_status
            FROM `tabSC Purchase Receipt Item` pri
            LEFT JOIN `tabSC Batch` b ON b.name = pri.batch_no
            WHERE pri.parent = %s AND pri.batch_no IS NOT NULL
        """, name, as_dict=True)
        out["purchase_invoices"] = frappe.db.get_all("SC Purchase Invoice",
            filters={"purchase_receipt": name},
            fields=["name", "invoice_date", "supplier", "grand_total", "outstanding_amount", "status", "docstatus"],
            limit=10)

    elif doctype == "SC Quality Inspection":
        # Trả PR + Item info qua get_doc
        pass

    elif doctype == "SC Item":
        out["batches"] = frappe.db.get_all("SC Batch",
            filters={"item": name, "disabled": 0},
            fields=["name", "supplier", "supplier_batch_no", "manufacturing_date",
                     "expiry_date", "qc_status", "blocked"],
            order_by="expiry_date asc", limit=50)
        # Stock balance per warehouse
        out["stock_balance"] = frappe.db.sql("""
            SELECT warehouse, COALESCE(SUM(qty_change), 0) AS qty,
                   COALESCE(SUM(qty_change * valuation_rate), 0) AS value
            FROM `tabSC Stock Ledger Entry`
            WHERE item = %s AND is_cancelled = 0
            GROUP BY warehouse
            HAVING qty > 0
            ORDER BY qty DESC
        """, name, as_dict=True)
        out["recent_movements"] = frappe.db.get_all("SC Stock Ledger Entry",
            filters={"item": name, "is_cancelled": 0},
            fields=["name", "posting_date", "warehouse", "batch", "qty_change",
                     "balance_qty", "voucher_type", "voucher_no"],
            order_by="creation desc", limit=20)

    elif doctype == "SC Batch":
        out["movements"] = frappe.db.get_all("SC Stock Ledger Entry",
            filters={"batch": name, "is_cancelled": 0},
            fields=["name", "posting_date", "warehouse", "qty_change", "balance_qty",
                     "voucher_type", "voucher_no"],
            order_by="creation desc", limit=50)
        out["recalls"] = frappe.db.get_all("SC Recall Notice",
            filters={"batch_no": name},
            fields=["name", "recall_date", "severity", "status", "docstatus"],
            limit=5)
        out["stock_balance"] = frappe.db.sql("""
            SELECT warehouse, COALESCE(SUM(qty_change), 0) AS qty
            FROM `tabSC Stock Ledger Entry`
            WHERE batch = %s AND is_cancelled = 0
            GROUP BY warehouse
            HAVING qty > 0
        """, name, as_dict=True)

    elif doctype == "SC Supplier":
        out["framework_contracts"] = frappe.db.get_all("Framework Contract",
            filters={"supplier": name},
            fields=["name", "contract_number", "valid_from", "valid_to", "total_value",
                     "remaining_value", "status"],
            limit=20)
        out["purchase_orders"] = frappe.db.get_all("SC Purchase Order",
            filters={"supplier": name, "docstatus": 1},
            fields=["name", "transaction_date", "grand_total", "status"],
            order_by="transaction_date desc", limit=10)

    elif doctype == "SC Warehouse":
        # Tồn kho tại warehouse này — top 30 items
        out["stock_balance"] = frappe.db.sql("""
            SELECT sle.item, i.item_name, sle.batch,
                   COALESCE(SUM(sle.qty_change), 0) AS qty,
                   COALESCE(SUM(sle.qty_change * sle.valuation_rate), 0) AS value,
                   b.expiry_date, b.qc_status
            FROM `tabSC Stock Ledger Entry` sle
            LEFT JOIN `tabSC Item` i ON i.name = sle.item
            LEFT JOIN `tabSC Batch` b ON b.name = sle.batch
            WHERE sle.warehouse = %s AND sle.is_cancelled = 0
            GROUP BY sle.item, sle.batch
            HAVING qty > 0
            ORDER BY value DESC LIMIT 30
        """, name, as_dict=True)
        out["recent_movements"] = frappe.db.get_all("SC Stock Ledger Entry",
            filters={"warehouse": name, "is_cancelled": 0},
            fields=["name", "posting_date", "item", "batch", "qty_change",
                     "voucher_type", "voucher_no"],
            order_by="creation desc", limit=15)

    elif doctype == "SC Recall Notice":
        out["affected_items"] = frappe.db.get_all("SC Recall Affected Item",
            filters={"parent": name},
            fields=["name", "warehouse", "department", "qty_issued",
                     "recovered_qty", "destroyed_qty", "status"],
            limit=50)

    # === Chuỗi BÁN HÀNG (O2C) — đối xứng với chuỗi mua hàng ở trên ===
    # Khách hàng → HĐ khung bán → Đơn hàng → Phiếu giao → Nghiệm thu → Hóa đơn → Thu tiền.
    elif doctype == "SC Customer":
        out["sales_framework_contracts"] = frappe.db.get_all("SC Sales Framework Contract",
            filters={"customer": name},
            fields=["name", "valid_from", "valid_to", "total_value", "remaining_value",
                     "status", "docstatus"],
            order_by="valid_from desc", limit=20)
        out["sales_orders"] = frappe.db.get_all("SC Sales Order",
            filters={"customer": name},
            fields=["name", "order_date", "total_amount", "status", "docstatus"],
            order_by="order_date desc", limit=20)
        out["sales_invoices"] = frappe.db.get_all("SC Sales Invoice",
            filters={"customer": name},
            fields=["name", "invoice_date", "grand_total", "outstanding_amount",
                     "status", "docstatus"],
            order_by="invoice_date desc", limit=20)

    elif doctype == "SC Sales Framework Contract":
        out["sales_orders"] = frappe.db.get_all("SC Sales Order",
            filters={"framework_contract": name},
            fields=["name", "order_date", "customer", "total_amount", "status", "docstatus"],
            order_by="order_date desc", limit=50)

    elif doctype == "SC Sales Order":
        out["delivery_notes"] = frappe.db.get_all("SC Delivery Note",
            filters={"sales_order": name},
            fields=["name", "delivery_date", "customer", "status", "docstatus"],
            order_by="delivery_date desc", limit=20)
        # Hóa đơn bán phát sinh qua các phiếu giao của đơn này.
        out["sales_invoices"] = frappe.db.sql("""
            SELECT si.name, si.invoice_date, si.grand_total, si.outstanding_amount,
                   si.status, si.docstatus
            FROM `tabSC Sales Invoice` si
            JOIN `tabSC Delivery Note` dn ON dn.name = si.delivery_note
            WHERE dn.sales_order = %s
            ORDER BY si.invoice_date DESC LIMIT 20
        """, name, as_dict=True)

    elif doctype == "SC Delivery Note":
        out["acceptance_records"] = frappe.db.get_all("SC Acceptance Record",
            filters={"delivery_note": name},
            fields=["name", "acceptance_date", "accepted_by", "status", "docstatus"],
            limit=10)
        out["sales_invoices"] = frappe.db.get_all("SC Sales Invoice",
            filters={"delivery_note": name},
            fields=["name", "invoice_date", "grand_total", "outstanding_amount",
                     "status", "docstatus"],
            limit=10)
        out["sold_batches"] = frappe.db.sql("""
            SELECT DISTINCT dni.batch AS name, b.item, b.supplier_batch_no,
                   b.expiry_date, b.qc_status
            FROM `tabDN Item` dni
            LEFT JOIN `tabSC Batch` b ON b.name = dni.batch
            WHERE dni.parent = %s AND dni.batch IS NOT NULL AND dni.batch != ''
        """, name, as_dict=True)

    elif doctype == "SC Sales Invoice":
        out["sales_receipts"] = frappe.db.get_all("SC Sales Receipt",
            filters={"sales_invoice": name},
            fields=["name", "receipt_date", "amount", "docstatus"],
            order_by="receipt_date desc", limit=20)

    elif doctype == "SC Sales Receipt":
        _si = frappe.db.get_value("SC Sales Receipt", name, "sales_invoice")
        if _si:
            out["sales_invoices"] = frappe.db.get_all("SC Sales Invoice",
                filters={"name": _si},
                fields=["name", "invoice_date", "grand_total", "outstanding_amount",
                         "status", "docstatus"],
                limit=1)

    return out


@frappe.whitelist()
def stock_balance(item=None, warehouse=None, batch=None, item_group=None):
    """UC-16: tồn kho per item/warehouse/batch. Aggregate SLE."""
    block_portal()
    conds = ["sle.is_cancelled = 0"]
    params = {}
    if item:
        conds.append("sle.item = %(item)s"); params["item"] = item
    if warehouse:
        conds.append("sle.warehouse = %(wh)s"); params["wh"] = warehouse
    if batch:
        conds.append("sle.batch = %(batch)s"); params["batch"] = batch
    if item_group:
        conds.append("i.item_group = %(g)s"); params["g"] = item_group

    rows = frappe.db.sql(f"""
        SELECT sle.item, i.item_name, sle.warehouse, sle.batch, b.supplier_batch_no,
               COALESCE(SUM(sle.qty_change), 0) AS qty,
               COALESCE(SUM(sle.qty_change * sle.valuation_rate), 0) AS value,
               b.expiry_date, b.qc_status, b.blocked
        FROM `tabSC Stock Ledger Entry` sle
        LEFT JOIN `tabSC Item` i ON i.name = sle.item
        LEFT JOIN `tabSC Batch` b ON b.name = sle.batch
        WHERE {' AND '.join(conds)}
        GROUP BY sle.item, sle.warehouse, sle.batch
        HAVING qty > 0
        ORDER BY i.item_name, sle.warehouse, b.expiry_date ASC
        LIMIT 500
    """, params, as_dict=True)
    # L21/T09: đánh dấu tồn KHẢ DỤNG = đã QC Đạt và KHÔNG bị khoá. Lô chưa QC
    # (Pending/NULL), Không đạt (Rejected), Có điều kiện (Conditional) hoặc bị
    # khoá KHÔNG tính vào tồn khả dụng — frontend cộng riêng để không thổi phồng
    # tồn. Vẫn trả về mọi dòng để hiển thị nhóm riêng kèm badge trạng thái.
    for r in rows:
        r["available"] = 1 if (r.get("qc_status") == "Accepted" and not r.get("blocked")) else 0
    return rows


@frappe.whitelist()
def items_in_warehouse(warehouse=None):
    """Danh sách MÃ vật tư CÓ TỒN (>0) trong 1 kho — để giới hạn dropdown vật tư
    ở phiếu chuyển kho / cấp phát chỉ hiện VT thực sự đang có trong kho nguồn.
    Trả list[str] mã item; rỗng nếu kho không truyền hoặc không có tồn."""
    block_portal()
    if not warehouse:
        return []
    rows = frappe.db.sql("""
        SELECT sle.item
        FROM `tabSC Stock Ledger Entry` sle
        WHERE sle.warehouse = %(wh)s AND sle.is_cancelled = 0
        GROUP BY sle.item
        HAVING COALESCE(SUM(sle.qty_change), 0) > 0
    """, {"wh": warehouse})
    return [r[0] for r in rows]


@frappe.whitelist()
def warehouse_stock_for_item(warehouse, item=None):
    """List batches của item (hoặc tất cả) trong warehouse với bin + qty.
    UC-18: hỗ trợ TR form khi user chọn item → hiện tồn + bin.
    """
    block_portal()
    if not warehouse:
        return []
    conds = ["sle.warehouse = %(wh)s", "sle.is_cancelled = 0"]
    params = {"wh": warehouse}
    if item:
        conds.append("sle.item = %(item)s")
        params["item"] = item
    return frappe.db.sql(f"""
        SELECT sle.item, i.item_name, i.uom, sle.batch, b.supplier_batch_no, sle.bin_location,
               COALESCE(SUM(sle.qty_change), 0) AS qty,
               MIN(sle.posting_date) AS received_date,
               b.expiry_date, b.qc_status, b.blocked,
               i.safety_stock
        FROM `tabSC Stock Ledger Entry` sle
        LEFT JOIN `tabSC Item` i ON i.name = sle.item
        LEFT JOIN `tabSC Batch` b ON b.name = sle.batch
        WHERE {' AND '.join(conds)}
        GROUP BY sle.item, sle.batch, sle.bin_location
        HAVING qty > 0
        ORDER BY b.expiry_date ASC, sle.batch
    """, params, as_dict=True)


@frappe.whitelist()
def check_safety_after_transfer(warehouse, item, qty):
    """Kiểm tra nếu chuyển qty từ warehouse → tồn còn lại có dưới safety_stock không.
    Trả {current, after, safety_stock, below_safety, warning_msg}.
    """
    block_portal()
    current = flt(frappe.db.sql("""
        SELECT COALESCE(SUM(qty_change), 0)
        FROM `tabSC Stock Ledger Entry`
        WHERE warehouse = %s AND item = %s AND is_cancelled = 0
    """, (warehouse, item))[0][0])
    safety = flt(frappe.db.get_value("SC Item", item, "safety_stock") or 0)
    after = current - flt(qty)
    below = safety > 0 and after < safety
    return {
        "current": current,
        "transfer_qty": flt(qty),
        "after_transfer": after,
        "safety_stock": safety,
        "below_safety": below,
        "warning_msg": f"⚠ Sau chuyển còn {after:.0f} < safety stock {safety:.0f}" if below else None,
    }


@frappe.whitelist()
def fefo_pick_guide(item, warehouse, qty_needed):
    """UC-17/UC-21: FEFO picking guide.
    Trả picking plan: lô nào lấy trước, bin nào, qty bao nhiêu.

    Sort batches by expiry_date ASC (first-expired-first-out).
    Skip blocked batches. Skip batches HD đã hết.
    """
    block_portal()
    qty_needed = flt(qty_needed)
    if qty_needed <= 0:
        return {"error": "qty_needed phải > 0", "picks": [], "total_picked": 0}

    rows = frappe.db.sql("""
        SELECT sle.batch, sle.bin_location,
               COALESCE(SUM(sle.qty_change), 0) AS qty,
               b.expiry_date, b.qc_status, b.blocked,
               DATEDIFF(b.expiry_date, CURDATE()) AS days_left
        FROM `tabSC Stock Ledger Entry` sle
        JOIN `tabSC Batch` b ON b.name = sle.batch
        WHERE sle.warehouse = %s AND sle.item = %s AND sle.is_cancelled = 0
          AND b.disabled = 0
          AND COALESCE(b.blocked, 0) = 0
          AND b.qc_status = 'Accepted'
          AND (b.expiry_date IS NULL OR b.expiry_date >= CURDATE())
        GROUP BY sle.batch, sle.bin_location, b.expiry_date, b.qc_status, b.blocked
        HAVING qty > 0
        ORDER BY b.expiry_date ASC, sle.batch
    """, (warehouse, item), as_dict=True)

    picks = []
    remaining = qty_needed
    for r in rows:
        if remaining <= 0:
            break
        pick_qty = min(flt(r["qty"]), remaining)
        picks.append({
            "batch": r["batch"],
            "bin_location": r["bin_location"] or "(chưa xếp bin)",
            "expiry_date": str(r["expiry_date"]) if r["expiry_date"] else None,
            "days_left": int(r["days_left"]) if r["days_left"] is not None else None,
            "available": flt(r["qty"]),
            "pick_qty": pick_qty,
            "qc_status": r["qc_status"],
            "instruction": (f"Lấy {pick_qty:.0f} từ lô {r['batch']} "
                            f"tại {r['bin_location'] or '(chưa có bin)'} "
                            f"(HD {r['expiry_date']}, còn {r['days_left']} ngày)"),
        })
        remaining -= pick_qty

    total_picked = qty_needed - remaining
    return {
        "item": item, "warehouse": warehouse,
        "qty_needed": qty_needed,
        "total_picked": total_picked,
        "shortage": max(0, remaining),
        "is_sufficient": remaining <= 0.01,
        "picks": picks,
        "summary": (f"Đủ {total_picked:.0f} / {qty_needed:.0f} qua {len(picks)} lô"
                     if remaining <= 0.01
                     else f"⚠ THIẾU {remaining:.0f}: chỉ có {total_picked:.0f} / {qty_needed:.0f}"),
    }


@frappe.whitelist()
def pending_putaway(warehouse=None, limit=50):
    """List SLE recent (PR/SE Material Receipt) chưa có bin_location.
    UC: phiếu xếp hàng lên kệ.
    """
    block_portal()
    conds = ["sle.qty_change > 0", "sle.is_cancelled = 0",
              "(sle.bin_location IS NULL OR sle.bin_location = '')",
              "sle.voucher_type IN ('SC Purchase Receipt', 'SC Stock Entry')"]
    params = {}
    if warehouse:
        conds.append("sle.warehouse = %(wh)s")
        params["wh"] = warehouse
    return frappe.db.sql(f"""
        SELECT sle.name AS sle_name, sle.posting_date,
               sle.item, i.item_name, sle.warehouse, sle.batch,
               sle.qty_change AS qty,
               sle.voucher_type, sle.voucher_no,
               b.expiry_date, b.qc_status
        FROM `tabSC Stock Ledger Entry` sle
        LEFT JOIN `tabSC Item` i ON i.name = sle.item
        LEFT JOIN `tabSC Batch` b ON b.name = sle.batch
        WHERE {' AND '.join(conds)}
        ORDER BY sle.creation DESC
        LIMIT %(lim)s
    """, {**params, "lim": int(limit)}, as_dict=True)


@frappe.whitelist()
def assign_bin(assignments):
    """Bulk assign bin_location cho list SLE rows.
    Args: assignments = [{sle_name, bin_location}]
    """
    block_portal()
    import json
    if isinstance(assignments, str):
        assignments = json.loads(assignments)
    updated = 0
    for a in assignments or []:
        if not (a.get("sle_name") and a.get("bin_location")):
            continue
        # Verify bin thuộc warehouse của SLE
        sle = frappe.db.get_value("SC Stock Ledger Entry", a["sle_name"],
            ["warehouse"], as_dict=True)
        if not sle:
            continue
        bin_wh = frappe.db.get_value("Bin Location", a["bin_location"], "warehouse")
        if bin_wh != sle.warehouse:
            frappe.throw(_("Bin {0} không thuộc kho {1}").format(
                a["bin_location"], sle.warehouse))
        frappe.db.sql("""
            UPDATE `tabSC Stock Ledger Entry`
            SET bin_location = %s
            WHERE name = %s
        """, (a["bin_location"], a["sle_name"]))
        updated += 1
    frappe.db.commit()
    return {"updated": updated}


@frappe.whitelist()
def batch_labels(names):
    """Dữ liệu in nhãn cho NHIỀU Lô (in hàng loạt từ danh sách Lô).
    names: JSON list (hoặc chuỗi phẩy) các mã lô. Trả field cần cho nhãn."""
    import json as _json
    block_portal()
    if not frappe.has_permission("SC Batch", "read"):
        frappe.throw(_("Không có quyền đọc Lô"), frappe.PermissionError)
    if isinstance(names, str):
        try:
            names = _json.loads(names)
        except Exception:
            names = [n.strip() for n in names.split(",") if n.strip()]
    if not names:
        return []
    return frappe.get_all(
        "SC Batch",
        filters={"name": ["in", list(names)]},
        fields=["name", "barcode", "batch_id", "item", "item_name",
                "supplier_batch_no", "manufacturing_date", "expiry_date",
                "model", "country_of_origin"],
    )


@frappe.whitelist()
def item_eligible_uoms(item=None):
    """Trả về danh sách UOM hợp lệ cho 1 vật tư.

    SC Item có 3 trường UOM: uom (tồn kho), buy_uom (mua), use_uom (sử dụng).
    Frontend dùng để filter dropdown UOM trong child table — chỉ hiển thị các UOM
    của item đang chọn, không phải toàn bộ SC UOM.
    """
    block_portal()
    if not item:
        return []
    row = frappe.db.get_value("SC Item", item,
                                ["uom", "buy_uom", "use_uom"], as_dict=True)
    if not row:
        return []
    return [u for u in dict.fromkeys([row.uom, row.buy_uom, row.use_uom]).keys() if u]


@frappe.whitelist()
def framework_contracts_for_item(item=None):
    """Trả về danh sách Framework Contract (Active, đã duyệt) có chứa vật tư `item`.

    Frontend dùng để filter dropdown 'HĐ khung' trong bảng chi tiết Yêu cầu mua —
    chỉ gợi ý HĐ khung nào thực sự có vật tư đang chọn ở dòng đó (scope theo mã VT).
    """
    block_portal()
    if not item:
        return []
    rows = frappe.db.sql("""
        SELECT DISTINCT fc.name
        FROM `tabFC Item` fci
        JOIN `tabFramework Contract` fc ON fc.name = fci.parent
        WHERE fci.item_code = %s AND fc.docstatus = 1 AND fc.status = 'Active'
        ORDER BY fc.name DESC
    """, item)
    return [r[0] for r in rows]


@frappe.whitelist()
def pd_item_autofetch(item=None, warehouse=None):
    """Auto-fetch UOM + đơn giá + lô FEFO khi cấp phát/xuất kho 1 vật tư
    tại 1 kho. Lô được chọn = lô có qty > 0 trong kho, QC Accepted (hoặc
    chưa gắn QC), không blocked, sort expiry_date ASC (FEFO).
    """
    block_portal()
    if not item or not warehouse:
        return {}

    uom = frappe.db.get_value("SC Item", item, "uom")

    # Đơn giá: ưu tiên valuation_rate gần nhất trong kho; fallback unit_price
    # từ FC Item Active rẻ nhất.
    val_row = frappe.db.sql("""
        SELECT valuation_rate FROM `tabSC Stock Ledger Entry`
        WHERE item=%s AND warehouse=%s AND is_cancelled=0
              AND valuation_rate > 0
        ORDER BY posting_date DESC, creation DESC LIMIT 1
    """, (item, warehouse))
    unit_cost = flt(val_row[0][0]) if val_row else 0

    if not unit_cost:
        fc_row = frappe.db.sql("""
            SELECT fci.unit_price FROM `tabFC Item` fci
            JOIN `tabFramework Contract` fc ON fc.name = fci.parent
            WHERE fci.item_code=%s AND fc.docstatus=1 AND fc.status='Active'
            ORDER BY fci.unit_price ASC LIMIT 1
        """, item)
        unit_cost = flt(fc_row[0][0]) if fc_row else 0

    # FEFO batch trong kho
    batch_row = frappe.db.sql("""
        SELECT sle.batch, SUM(sle.qty_change) AS qty,
               b.expiry_date, b.qc_status, b.blocked
        FROM `tabSC Stock Ledger Entry` sle
        LEFT JOIN `tabSC Batch` b ON b.name = sle.batch
        WHERE sle.item=%s AND sle.warehouse=%s AND sle.is_cancelled=0
          AND sle.batch IS NOT NULL AND sle.batch != ''
          AND (b.blocked = 0 OR b.blocked IS NULL)
          AND (b.qc_status = 'Accepted' OR b.qc_status IS NULL)
        GROUP BY sle.batch
        HAVING qty > 0
        ORDER BY b.expiry_date ASC, sle.batch ASC
        LIMIT 1
    """, (item, warehouse), as_dict=True)
    batch = batch_row[0].batch if batch_row else None

    return {
        "uom": uom,
        "unit_cost": unit_cost,
        "batch": batch,
        "available_qty": flt(batch_row[0].qty) if batch_row else 0,
        "expiry_date": str(batch_row[0].expiry_date) if batch_row and batch_row[0].expiry_date else None,
    }


@frappe.whitelist()
def bins_for_warehouse(warehouse=None):
    """List bins. Nếu warehouse=None → trả tất cả bins kèm warehouse
    để frontend có thể group + lọc theo từng row Putaway."""
    block_portal()
    filters = {"warehouse": warehouse} if warehouse else {}
    return frappe.db.get_all("Bin Location",
        filters=filters,
        fields=["name", "bin_code", "warehouse"],
        order_by="warehouse asc, bin_code asc", limit=500)


@frappe.whitelist()
def warehouse_summary():
    """Liệt kê tất cả warehouse + tổng SL + tổng giá trị + số items."""
    block_portal()
    return frappe.db.sql("""
        SELECT
            w.name AS name,
            w.warehouse_name,
            w.warehouse_type,
            w.is_group,
            w.disabled,
            COALESCE(SUM(sle.qty_change), 0) AS total_qty,
            COALESCE(SUM(sle.qty_change * sle.valuation_rate), 0) AS total_value,
            COUNT(DISTINCT sle.item) AS distinct_items
        FROM `tabSC Warehouse` w
        LEFT JOIN `tabSC Stock Ledger Entry` sle
            ON sle.warehouse = w.name AND sle.is_cancelled = 0
        WHERE w.is_group = 0 AND w.disabled = 0
        GROUP BY w.name
        ORDER BY total_value DESC
    """, as_dict=True)


@frappe.whitelist()
def save_doc(doctype, name, fields):
    """Update doc fields + save (Draft only). Tránh TimestampMismatch."""
    import json
    if isinstance(fields, str):
        fields = json.loads(fields)
    if not frappe.has_permission(doctype, "write", doc=name):
        frappe.throw(_("Không có quyền sửa {0} {1}").format(doctype, name),
                      frappe.PermissionError)
    doc = frappe.get_doc(doctype, name)
    for k, v in (fields or {}).items():
        if k not in ("name", "doctype", "owner", "creation", "modified", "modified_by",
                     "docstatus", "idx", "parent", "parentfield", "parenttype"):
            doc.set(k, v)
    doc.save()
    return doc.as_dict()


@frappe.whitelist()
def get_audit_trail(
    doctype: str = "",
    user: str = "",
    from_date: str = "",
    to_date: str = "",
    limit: int = 200,
):
    """FEAT-003: Audit Trail global — filter theo doctype / user / khoảng thời gian.

    Trả về danh sách thay đổi (tabVersion) cộng dồn từ mọi DocType SC.
    Chỉ user có role SupplyCore Manager / Auditor / System Manager mới xem được.
    """
    roles = set(frappe.get_roles(frappe.session.user))
    if not (roles & {"System Manager", "SupplyCore Manager", "SupplyCore Auditor"}):
        frappe.throw(
            _("Chỉ Quản lý hoặc Kiểm toán mới xem được Audit Trail"),
            frappe.PermissionError,
        )

    filters = {}
    if doctype:
        filters["ref_doctype"] = doctype
    else:
        # Chỉ trả về các DocType bắt đầu SC * hoặc Framework Contract (in-scope)
        filters["ref_doctype"] = (
            "in",
            tuple(
                r.name for r in frappe.db.get_all(
                    "DocType",
                    filters={"module": ("in", ("Supplycore",
                                               "M1 Contract", "M2 Planning",
                                               "M3 Receiving", "M4 Wms",
                                               "M5 Fefo", "M6 Transfer",
                                               "M8 Accounting",
                                               "M9 Stocktake", "M10 Traceability",
                                               "M11 Dashboard"))},
                    pluck="name",
                )
            ) or ("__none__",),
        )
    if user:
        filters["owner"] = user
    if from_date:
        filters["creation"] = (">=", from_date)
    if to_date:
        existing = filters.get("creation")
        filters["creation"] = (
            ("between", [from_date or "1970-01-01", to_date])
            if existing else ("<=", to_date)
        )

    rows = frappe.db.get_all(
        "Version",
        filters=filters,
        fields=["name", "ref_doctype", "docname", "owner", "creation", "data"],
        order_by="creation desc",
        limit=int(limit) if limit else 200,
    )

    import json as _json
    out = []
    for r in rows:
        change_count = 0
        try:
            d = _json.loads(r.data or "{}")
            change_count = (
                len(d.get("changed") or [])
                + len(d.get("row_changed") or [])
                + len(d.get("added") or [])
                + len(d.get("removed") or [])
            )
        except Exception:
            pass
        out.append({
            "name": r.name,
            "doctype": r.ref_doctype,
            "docname": r.docname,
            "user": r.owner,
            "when": r.creation,
            "change_count": change_count,
        })
    return out


@frappe.whitelist()
def get_doc_versions(doctype, name, limit=50):
    """Trả lịch sử sửa từ tabVersion (track_changes=1) — diff field-level.

    Mỗi record là 1 lần save. data là JSON {changed: [[field, old, new], ...]}.
    Frontend hiển thị thành bảng "ai-sửa-gì-khi-nào".
    """
    block_portal()
    if not frappe.has_permission(doctype, "read", doc=name):
        frappe.throw(_("Không có quyền đọc {0}").format(doctype), frappe.PermissionError)

    import json as _json
    rows = frappe.db.get_all(
        "Version",
        filters={"ref_doctype": doctype, "docname": name},
        fields=["name", "owner", "creation", "data"],
        order_by="creation desc",
        limit=int(limit) if limit else 50,
    )
    out = []
    for r in rows:
        changed = []
        try:
            d = _json.loads(r.data or "{}")
            for entry in (d.get("changed") or []):
                if not entry or len(entry) < 3:
                    continue
                fld, old, new = entry[0], entry[1], entry[2]
                # Bỏ field hệ thống không cần show
                if fld in ("modified", "modified_by", "_user_tags", "_comments",
                           "_assign", "_liked_by"):
                    continue
                changed.append({"field": fld, "old": old, "new": new})
            # row_changed = [[childtable, idx, name, [[field, old, new], ...]], ...]
            for entry in (d.get("row_changed") or []):
                if not entry or len(entry) < 4:
                    continue
                ctable, idx, _cname, diffs = entry[0], entry[1], entry[2], entry[3]
                for fdiff in (diffs or []):
                    if not fdiff or len(fdiff) < 3:
                        continue
                    f, o, n = fdiff[0], fdiff[1], fdiff[2]
                    if f in ("modified", "modified_by"):
                        continue
                    changed.append({
                        "field": f"{ctable}[{idx}].{f}",
                        "old": o, "new": n,
                    })
            for added in (d.get("added") or []):
                if not added or len(added) < 2:
                    continue
                changed.append({"field": f"+ {added[0]}",
                                "old": None, "new": "(dòng mới)"})
            for removed in (d.get("removed") or []):
                if not removed or len(removed) < 2:
                    continue
                changed.append({"field": f"- {removed[0]}",
                                "old": "(đã xoá)", "new": None})
        except Exception:
            continue
        if not changed:
            continue
        out.append({
            "name": r.name,
            "owner": r.owner,
            "creation": str(r.creation),
            "changed": changed,
        })
    return out
