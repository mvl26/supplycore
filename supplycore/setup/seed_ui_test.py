"""Seed idempotent cho UI test (Playwright) — GĐ MVL.

Dựng dataset xác định cho 12 kịch bản UI:
- KH A (portal): HĐ khung SFC-A gồm 1 item CÓ TỒN + 1 item HẾT TỒN; hạn mức cao.
- KH B (portal): HĐ khung riêng — dùng kiểm cách ly dữ liệu.
- KH NỢ (portal): hạn mức thấp + 1 hoá đơn chưa thu → dư nợ VƯỢT ngưỡng (S5).
- Người duyệt: test.manager@sc.local (SupplyCore Manager) — seed_test_users.

Chạy: bench --site <site> execute supplycore.setup.seed_ui_test.run
Idempotent: xoá sạch chứng từ giao dịch của 3 KH test rồi tạo lại HĐ khung mới →
sold_qty/remaining/dư nợ về trạng thái gốc mỗi lần chạy.
"""

import frappe
from frappe.utils import today, add_days, flt

PASSWORD = "TestPass123!"

CUST = {
    "A":    {"email": "ui.custa@sc.local",    "name": "UITEST Khách Hàng A", "tax": "UITESTA01", "limit": 100000000},
    "B":    {"email": "ui.custb@sc.local",    "name": "UITEST Khách Hàng B", "tax": "UITESTB01", "limit": 100000000},
    "DEBT": {"email": "ui.custdebt@sc.local", "name": "UITEST Khách Nợ",     "tax": "UITESTD01", "limit": 50000},
}
WAREHOUSE = "UITEST-KHO"
ITEM_STOCK = "UITEST-ITEM-STOCK"   # có tồn
ITEM_EMPTY = "UITEST-ITEM-EMPTY"   # hết tồn (S6)
UNIT_PRICE = 10000
CONTRACT_QTY = 100


def _uom():
    u = frappe.db.get_value("SC UOM", {}, "name")
    if not u:
        d = frappe.new_doc("SC UOM"); d.uom_name = "Cái"; d.flags.ignore_permissions = True; d.insert()
        u = d.name
    return u


def _ensure_warehouse():
    if not frappe.db.exists("SC Warehouse", WAREHOUSE):
        d = frappe.new_doc("SC Warehouse")
        d.warehouse_name = WAREHOUSE
        d.is_group = 0
        d.flags.ignore_permissions = True
        d.insert()
    return WAREHOUSE


def _ensure_item(code, name, has_batch=1):
    if not frappe.db.exists("SC Item", code):
        d = frappe.new_doc("SC Item")
        d.item_code = code
        d.item_name = name
        d.uom = _uom()
        d.is_stock_item = 1
        d.has_batch_no = has_batch
        d.flags.ignore_permissions = True
        d.insert()
    else:
        # Ép has_batch_no đúng kỳ vọng (db.set_value bỏ qua validate — chỉ dùng cho
        # item test UITEST, đi kèm reset SLE bên dưới nên không lệch sổ kho thật).
        if frappe.db.get_value("SC Item", code, "has_batch_no") != has_batch:
            frappe.db.set_value("SC Item", code, "has_batch_no", has_batch)
    return code


def _reset_item_ledger(code):
    """Xoá sạch SLE + batch của item TEST để nạp lại tồn theo lô sạch (chỉ item
    UITEST-*, không đụng dữ liệu thật)."""
    frappe.db.sql("DELETE FROM `tabSC Stock Ledger Entry` WHERE item=%s", code)
    for b in frappe.get_all("SC Batch", {"item": code}, pluck="name"):
        frappe.delete_doc("SC Batch", b, ignore_permissions=True, force=True)


def _stock_on_hand(item, warehouse):
    from supplycore.supplycore.doctype.sc_stock_ledger_entry.sc_stock_ledger_entry import SCStockLedgerEntry
    return flt(SCStockLedgerEntry.get_available_qty(item, warehouse))


def _ensure_batch(item):
    """Lô Accepted, hạn xa — để get_available_qty không loại (Pending/Rejected)."""
    existing = frappe.db.get_value("SC Batch", {"item": item, "qc_status": "Accepted"}, "name")
    if existing:
        return existing
    b = frappe.new_doc("SC Batch")
    b.batch_id = f"{item}-UITEST"
    b.item = item
    b.expiry_date = add_days(today(), 365)
    b.manufacturing_date = today()
    b.qc_status = "Accepted"
    b.flags.ignore_permissions = True
    b.flags.ignore_short_expiry = True
    b.insert()
    return b.name


def _seed_stock(item, warehouse, target):
    """Nạp tồn (theo lô Accepted) cho đủ `target` tại kho."""
    have = _stock_on_hand(item, warehouse)
    need = flt(target) - have
    if need <= 0:
        return
    batch = _ensure_batch(item)
    from supplycore.supplycore.doctype.sc_stock_ledger_entry.sc_stock_ledger_entry import SCStockLedgerEntry
    SCStockLedgerEntry.post(
        item=item, warehouse=warehouse, qty_change=need, valuation_rate=UNIT_PRICE,
        voucher_type="SC Purchase Receipt", voucher_no=f"UITEST-IN-{frappe.generate_hash(length=6)}",
        batch=batch,
    )


def _ensure_user(email, full_name):
    # QUAN TRỌNG: KHÔNG reset mật khẩu / save lại user đã tồn tại — Frappe vô hiệu
    # hoá mọi session hiện có khi đổi mật khẩu, làm hỏng storageState mà UI test
    # đã đăng nhập (reseed giữa các spec sẽ đá KH ra guest). Chỉ set password khi
    # TẠO MỚI. User cũ chỉ đảm bảo enabled + có role Portal (không đổi password).
    want_roles = ["SC Customer Portal"]
    if frappe.db.exists("Role", "Khách hàng"):
        want_roles.append("Khách hàng")  # nhãn khách hàng (kèm role chức năng)
    if frappe.db.exists("User", email):
        u = frappe.get_doc("User", email)
        changed = False
        if not u.enabled:
            u.enabled = 1; changed = True
        have = [r.role for r in u.roles]
        for role in want_roles:
            if role not in have:
                u.append("roles", {"role": role}); changed = True
        if changed:
            u.flags.ignore_permissions = True
            u.save()
        return u.name

    u = frappe.new_doc("User")
    u.email = email
    u.first_name = full_name
    u.user_type = "Website User"
    u.send_welcome_email = 0
    u.new_password = PASSWORD
    u.flags.ignore_permissions = True
    u.insert()
    for role in want_roles:
        u.add_roles(role)
    from frappe.utils.password import update_password
    try:
        update_password(email, PASSWORD)
    except Exception:
        pass
    return u.name


def _ensure_customer(key):
    c = CUST[key]
    name = frappe.db.get_value("SC Customer", {"tax_code": c["tax"]}, "name")
    user = _ensure_user(c["email"], c["name"])
    if name:
        doc = frappe.get_doc("SC Customer", name)
    else:
        doc = frappe.new_doc("SC Customer")
        doc.customer_name = c["name"]
        doc.tax_code = c["tax"]
    doc.status = "Hoạt động"
    doc.credit_limit = c["limit"]
    doc.billing_address = "Số 1 Đường Test, Hà Nội"
    doc.portal_user = user
    doc.flags.ignore_permissions = True
    doc.save()
    return doc.name


def _cancel_delete(doctype, filters):
    for row in frappe.get_all(doctype, filters=filters, pluck="name"):
        try:
            doc = frappe.get_doc(doctype, row)
            if doc.docstatus == 1:
                doc.flags.ignore_permissions = True
                doc.cancel()
            frappe.delete_doc(doctype, row, ignore_permissions=True, force=True)
        except Exception as e:
            frappe.log_error(f"seed_ui_test cleanup {doctype} {row}: {e}")


def _cleanup(customer):
    # Thứ tự đảo phụ thuộc để cancel không vướng ràng buộc.
    _cancel_delete("SC Sales Receipt", {"customer": customer})
    _cancel_delete("SC Sales Invoice", {"customer": customer})
    _cancel_delete("SC Acceptance Record", {"customer": customer})
    _cancel_delete("SC Delivery Note", {"customer": customer})
    _cancel_delete("SC Sales Order", {"customer": customer})
    _cancel_delete("SC Sales Framework Contract", {"customer": customer})


def _make_sfc(customer, items):
    """items: list of (item_code, contract_qty). Trả tên SFC đã submit."""
    sfc = frappe.new_doc("SC Sales Framework Contract")
    sfc.customer = customer
    sfc.valid_from = today()
    sfc.valid_to = add_days(today(), 365)
    for code, qty in items:
        sfc.append("items", {"item": code, "uom": _uom(),
                             "contract_qty": qty, "unit_price": UNIT_PRICE})
    sfc.flags.ignore_permissions = True
    sfc.insert()
    sfc.submit()
    return sfc.name


def _make_debt(customer, item, wh):
    """Tạo chuỗi order→DN→AR→SI (chưa thu) để KH có dư nợ vượt ngưỡng.

    Order value (100.000) đã VƯỢT hạn mức (50.000) nên rule BRU-AR-001 sẽ chặn
    chính bước seed → tạm TẮT credit_check khi dựng, bật lại sau. Kết quả: KH có
    dư nợ 100.000 > hạn mức 50.000 (đúng trạng thái cần cho S5)."""
    from supplycore.api import sales
    frappe.db.set_single_value("SupplyCore Settings", "credit_check_enabled", 0)
    try:
        return _make_debt_inner(customer, item, wh, sales)
    finally:
        frappe.db.set_single_value("SupplyCore Settings", "credit_check_enabled", 1)


def _make_debt_inner(customer, item, wh, sales):
    so = frappe.new_doc("SC Sales Order")
    so.customer = customer
    so.framework_contract = frappe.db.get_value("SC Sales Framework Contract",
                                               {"customer": customer, "docstatus": 1}, "name")
    so.order_date = today()
    so.append("items", {"item": item, "uom": _uom(), "qty": 10})
    so.flags.ignore_permissions = True
    so.insert()
    so.submit()
    so.approve()
    dn = sales.make_delivery(so.name, from_warehouse=wh)["name"]
    sales.delivery_accept(dn, accepted_by="Seed")
    si = sales.sales_invoice_create(dn, tax_rate=0)["name"]
    return si


def run() -> dict:
    # Đảm bảo cấu hình rule bật + có ngưỡng
    frappe.db.set_single_value("SupplyCore Settings", "credit_check_enabled", 1)
    frappe.db.set_single_value("SupplyCore Settings", "block_order_on_insufficient_stock", 1)
    if not frappe.db.get_single_value("SupplyCore Settings", "seller_tax_code"):
        frappe.db.set_single_value("SupplyCore Settings", "seller_tax_code", "0100686209")

    wh = _ensure_warehouse()
    _ensure_item(ITEM_STOCK, "UITEST Vật tư có tồn", has_batch=1)
    _ensure_item(ITEM_EMPTY, "UITEST Vật tư hết tồn", has_batch=0)

    # Customers + cleanup chứng từ cũ (cleanup cancel DN → post reversal SLE, nên
    # phải làm TRƯỚC khi reset ledger).
    ca = _ensure_customer("A")
    cb = _ensure_customer("B")
    cd = _ensure_customer("DEBT")
    for c in (ca, cb, cd):
        _cleanup(c)

    # Reset ledger tồn về 0 rồi nạp lại theo lô → trạng thái xác định mỗi lần seed.
    # ITEM_STOCK dư dả (1000), ITEM_EMPTY giữ 0 (S6 chặn hết tồn).
    _reset_item_ledger(ITEM_STOCK)
    _reset_item_ledger(ITEM_EMPTY)
    _seed_stock(ITEM_STOCK, wh, 1000)

    sfc_a = _make_sfc(ca, [(ITEM_STOCK, CONTRACT_QTY), (ITEM_EMPTY, CONTRACT_QTY)])
    sfc_b = _make_sfc(cb, [(ITEM_STOCK, CONTRACT_QTY)])
    sfc_d = _make_sfc(cd, [(ITEM_STOCK, CONTRACT_QTY)])

    si_debt = _make_debt(cd, ITEM_STOCK, wh)

    frappe.db.commit()
    return {
        "customer_a": ca, "customer_b": cb, "customer_debt": cd,
        "email_a": CUST["A"]["email"], "email_b": CUST["B"]["email"], "email_debt": CUST["DEBT"]["email"],
        "sfc_a": sfc_a, "sfc_b": sfc_b, "sfc_debt": sfc_d,
        "si_debt": si_debt, "warehouse": wh,
        "item_stock": ITEM_STOCK, "item_empty": ITEM_EMPTY,
        "contract_qty": CONTRACT_QTY, "unit_price": UNIT_PRICE,
        "password": PASSWORD,
    }


def make_pending_order():
    """Tạo 1 SC Sales Order 'Chờ duyệt' cho KH A (ITEM_STOCK qty 3) — tiền đề S7.
    In RESULT:<name> để Node đọc."""
    ca = frappe.db.get_value("SC Customer", {"tax_code": CUST["A"]["tax"]}, "name")
    sfc = frappe.db.get_value("SC Sales Framework Contract", {"customer": ca, "docstatus": 1}, "name")
    so = frappe.new_doc("SC Sales Order")
    so.customer = ca
    so.framework_contract = sfc
    so.order_date = today()
    so.append("items", {"item": ITEM_STOCK, "uom": _uom(), "qty": 3})
    so.flags.ignore_permissions = True
    so.insert()
    so.submit()
    frappe.db.commit()
    print("RESULT:" + so.name)
    return so.name


def make_delivered_dn():
    """Tạo chuỗi order→approve→DN (status 'Đã giao', CHƯA nghiệm thu) cho KH A —
    tiền đề S8. In RESULT:<dn_name>."""
    from supplycore.api import sales
    ca = frappe.db.get_value("SC Customer", {"tax_code": CUST["A"]["tax"]}, "name")
    sfc = frappe.db.get_value("SC Sales Framework Contract", {"customer": ca, "docstatus": 1}, "name")
    _seed_stock(ITEM_STOCK, WAREHOUSE, 1000)
    so = frappe.new_doc("SC Sales Order")
    so.customer = ca
    so.framework_contract = sfc
    so.order_date = today()
    so.append("items", {"item": ITEM_STOCK, "uom": _uom(), "qty": 4})
    so.flags.ignore_permissions = True
    so.insert()
    so.submit()
    so.approve()
    dn = sales.make_delivery(so.name, from_warehouse=WAREHOUSE)["name"]
    frappe.db.commit()
    print("RESULT:" + dn)
    return dn


def make_invoiced_order():
    """Chuỗi ĐẦY ĐỦ cho KH A: order(qty 4)→approve→DN→nghiệm thu→hoá đơn (chưa
    thu) → KH A có: đã gọi 4, số lần gọi 1, công nợ 40.000. In RESULT:<si_name>."""
    from supplycore.api import sales
    ca = frappe.db.get_value("SC Customer", {"tax_code": CUST["A"]["tax"]}, "name")
    sfc = frappe.db.get_value("SC Sales Framework Contract", {"customer": ca, "docstatus": 1}, "name")
    _seed_stock(ITEM_STOCK, WAREHOUSE, 1000)
    so = frappe.new_doc("SC Sales Order")
    so.customer = ca
    so.framework_contract = sfc
    so.order_date = today()
    so.append("items", {"item": ITEM_STOCK, "uom": _uom(), "qty": 4})
    so.flags.ignore_permissions = True
    so.insert()
    so.submit()
    so.approve()
    dn = sales.make_delivery(so.name, from_warehouse=WAREHOUSE)["name"]
    sales.delivery_accept(dn, accepted_by="Seed S9")
    si = sales.sales_invoice_create(dn, tax_rate=0)["name"]
    frappe.db.commit()
    print("RESULT:" + si)
    return si


def make_invoice_from_dn():
    """Bước NHÂN VIÊN: xuất hoá đơn từ DN đã nghiệm thu gần nhất của KH A (dùng
    trong S8 sau khi khách xác nhận nhận hàng). In RESULT:<si_name>."""
    from supplycore.api import sales
    ca = frappe.db.get_value("SC Customer", {"tax_code": CUST["A"]["tax"]}, "name")
    dn = frappe.db.get_value("SC Delivery Note",
                             {"customer": ca, "status": "Đã nghiệm thu"},
                             "name", order_by="creation desc")
    if not dn:
        print("RESULT:NONE")
        return "NONE"
    si = sales.sales_invoice_create(dn, tax_rate=0)["name"]
    frappe.db.commit()
    print("RESULT:" + si)
    return si


def make_pr_ready_for_confirm():
    """Tạo SC Purchase Receipt (thường) đã submit + QC Pass, ở trạng thái
    'Đã tiếp nhận' (chưa nhập kho) — tiền đề T9 UI. In RESULT:<pr_name>."""
    from frappe.utils import add_days
    supplier = frappe.db.get_value("SC Supplier", {}, "name")
    if not supplier:
        s = frappe.new_doc("SC Supplier"); s.supplier_name = "UITEST NCC"
        s.flags.ignore_permissions = True; s.insert(); supplier = s.name
    item = _ensure_item(ITEM_STOCK, "UITEST Vật tư có tồn", has_batch=1)
    pr = frappe.new_doc("SC Purchase Receipt")
    pr.supplier = supplier
    pr.posting_date = today()
    pr.to_warehouse = WAREHOUSE
    pr.qc_required = 1
    pr.no_po_reason = "UITEST T9 - nhận không qua PO"
    pr.append("items", {
        "item": item, "qty": 30, "uom": _uom(), "rate": 1000, "warehouse": WAREHOUSE,
        "expiry_date": add_days(today(), 365), "manufacturing_date": today(),
        "supplier_batch_no": "UITEST-T9-" + frappe.generate_hash(length=4),
    })
    pr.flags.ignore_permissions = True
    pr.insert(); pr.submit(); pr.reload()
    # QC Pass
    for qi in frappe.get_all("SC Quality Inspection", {"purchase_receipt": pr.name}, pluck="name"):
        d = frappe.get_doc("SC Quality Inspection", qi)
        for r in d.readings:
            r.status = "Accepted"
        d.overall_status = "Accepted"; d.action_taken = "Accept"
        d.flags.ignore_permissions = True
        d.save(ignore_permissions=True); d.submit()
    frappe.db.commit()
    print("RESULT:" + pr.name)
    return pr.name


def write_state():
    """Chạy seed rồi ghi state ra ui_tests/seed-state.json cho Playwright đọc."""
    import json, os
    res = run()
    ui_dir = os.path.abspath(os.path.join(frappe.get_app_path("supplycore"), "..", "ui_tests"))
    os.makedirs(ui_dir, exist_ok=True)
    with open(os.path.join(ui_dir, "seed-state.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    print("SEED_STATE_WRITTEN", os.path.join(ui_dir, "seed-state.json"))
    return res
