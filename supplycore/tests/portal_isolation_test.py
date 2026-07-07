"""Test GD3 M12 Task 2 -- Co lap du lieu khach hang Portal (RSK-01):
permission_query_conditions + has_permission tren 5 doctype ban hang.

Run individual: bench --site supplycore-miyano.local execute supplycore.tests.portal_isolation_test.test_<name>
Run all:        bench --site supplycore-miyano.local execute supplycore.tests.portal_isolation_test.run
"""

import frappe
from frappe.utils import today, add_days, random_string, flt


def _get_uom() -> str:
    return frappe.db.get_value("SC UOM", {}, "name")


def _pick_warehouse() -> str:
    rows = frappe.get_all("SC Warehouse", filters={"is_group": 0, "disabled": 0},
                           pluck="name", order_by="name", limit=1)
    if not rows:
        frappe.throw("portal_isolation_test: cần seed SC Warehouse")
    return rows[0]


def _make_item(suffix):
    item = frappe.new_doc("SC Item")
    item.item_code = f"ISO-{suffix}-{random_string(5)}"
    item.item_name = f"ISO test item {suffix}"
    item.uom = _get_uom()
    item.is_stock_item = 1
    item.flags.ignore_permissions = True
    item.insert()
    return item


def _make_portal_customer(suffix):
    """Tao SC Customer, provision tai khoan Portal, kich hoat (Hoat dong)."""
    from supplycore.api.portal import portal_provision

    c = frappe.new_doc("SC Customer")
    c.customer_name = f"KH ISO {suffix} {random_string(6)}"
    c.tax_code = f"TAX-ISO-{suffix}-{random_string(8)}"
    c.status = "Tạm ngưng"
    c.flags.ignore_permissions = True
    c.insert()

    email = f"portal_iso_{suffix.lower()}_{random_string(6)}@example.com"
    # portal_provision chuẩn hoá email về chữ thường (khớp User.name thật sau
    # validate) -- PHẢI dùng giá trị trả về, không dùng lại biến `email` gốc,
    # nếu không frappe.set_user(email) sau này sẽ set 1 session-user string
    # khác case với SC Customer.portal_user/frappe.session.user thật, khiến
    # portal_doc_permission từ chối nhầm cả chủ sở hữu hợp lệ.
    portal_email = portal_provision(c.name, email)

    c.reload()
    c.status = "Hoạt động"
    c.flags.ignore_permissions = True
    c.save()
    return c, portal_email


def _make_submitted_sfc(customer, item, contract_qty, unit_price):
    sfc = frappe.new_doc("SC Sales Framework Contract")
    sfc.customer = customer
    sfc.valid_from = today()
    sfc.valid_to = add_days(today(), 365)
    sfc.append("items", {
        "item": item, "uom": _get_uom(),
        "contract_qty": flt(contract_qty),
        "unit_price": flt(unit_price),
    })
    sfc.flags.ignore_permissions = True
    sfc.insert()
    sfc.submit()
    return sfc


def _make_approved_so(customer, framework_contract, item, qty):
    so = frappe.new_doc("SC Sales Order")
    so.customer = customer
    so.framework_contract = framework_contract
    so.order_date = today()
    so.append("items", {"item": item, "uom": _get_uom(), "qty": flt(qty)})
    so.flags.ignore_permissions = True
    so.insert()
    so.submit()
    so.approve()
    return so.name


def _seed_customer_with_order(suffix, qty=10, unit_price=1000):
    """Seed 1 khach (Portal, Hoat dong) + 1 SFC submitted + 1 SO da duyet."""
    cust, portal_email = _make_portal_customer(suffix)
    item = _make_item(suffix)
    sfc = _make_submitted_sfc(cust.name, item.name, contract_qty=100, unit_price=unit_price)
    so_name = _make_approved_so(cust.name, sfc.name, item.name, qty)
    return cust.name, portal_email, so_name


def _make_batch(item, expiry_date):
    b = frappe.new_doc("SC Batch")
    b.batch_id = f"{item}-{random_string(6)}"
    b.item = item
    b.expiry_date = expiry_date
    b.manufacturing_date = add_days(expiry_date, -365)
    b.qc_status = "Accepted"
    b.flags.ignore_permissions = True
    b.flags.ignore_short_expiry = True
    b.insert()
    return b


def _seed_stock(item, warehouse, batch, qty, rate=1000):
    from supplycore.supplycore.doctype.sc_stock_ledger_entry.sc_stock_ledger_entry import SCStockLedgerEntry
    SCStockLedgerEntry.post(
        item=item, warehouse=warehouse, qty_change=flt(qty),
        voucher_type="SC Purchase Receipt", voucher_no=f"TEST-IN-{random_string(6)}",
        batch=batch, valuation_rate=rate,
    )


def _accept_dn(dn):
    ar = frappe.new_doc("SC Acceptance Record")
    ar.delivery_note = dn.name
    ar.acceptance_date = today()
    ar.accepted_by = "Nguyễn Văn A"
    ar.flags.ignore_permissions = True
    ar.insert()
    ar.submit()
    dn.reload()
    return ar


def _seed_customer_full_chain(suffix, qty=10, unit_price=1000):
    """Dung chuoi day du: khach Portal -> SFC(hieu luc) -> SO(duyet) ->
    DN(nghiem thu) -> SI(phat hanh), de co dong that o ca 4 child doctype
    ban hang (SFC Item/SO Item/DN Item/SI Item) dung cho test RSK-01
    Critical (frappe.client.get). Tra ve dict de goi noi don gian tai
    diem goi."""
    cust, portal_email = _make_portal_customer(suffix)
    item = _make_item(suffix)
    sfc = _make_submitted_sfc(cust.name, item.name, contract_qty=100, unit_price=unit_price)
    so_name = _make_approved_so(cust.name, sfc.name, item.name, qty)

    wh = _pick_warehouse()
    batch = _make_batch(item.name, add_days(today(), 200))
    _seed_stock(item.name, wh, batch.name, qty * 2, rate=unit_price)

    dn = frappe.new_doc("SC Delivery Note")
    dn.sales_order = so_name
    dn.from_warehouse = wh
    dn.delivery_date = today()
    dn.append("items", {"item": item.name, "uom": _get_uom(), "qty": flt(qty)})
    dn.flags.ignore_permissions = True
    dn.insert()
    dn.submit()
    dn.reload()
    _accept_dn(dn)

    si = frappe.new_doc("SC Sales Invoice")
    si.customer = cust.name
    si.delivery_note = dn.name
    si.invoice_date = today()
    si.append("items", {"item": item.name, "qty": flt(qty), "unit_price": flt(unit_price)})
    si.flags.ignore_permissions = True
    si.insert()
    si.submit()

    return {
        "customer": cust.name, "portal_email": portal_email, "item": item.name,
        "sfc": sfc.name, "so": so_name, "dn": dn.name, "si": si.name,
    }


def _make_manager_user():
    """Tao 1 System User noi bo voi role SupplyCore Manager (bench execute
    chay boi Administrator -- can 1 user noi bo KHONG phai Administrator de
    kiem tra khong hoi quy quyen noi bo qua permission_query_conditions)."""
    email = f"manager_iso_{random_string(8)}@example.com"
    u = frappe.new_doc("User")
    u.email = email
    u.first_name = "ISO Manager Test"
    u.user_type = "System User"
    u.send_welcome_email = 0
    u.append("roles", {"role": "SupplyCore Manager"})
    u.flags.ignore_permissions = True
    u.insert()
    return email


# ---------- Tests ----------

def test_portal_A_lists_only_own_orders():
    """Portal A: get_list('SC Sales Order') chi chua don cua A, khong co don cua B."""
    orig_user = frappe.session.user
    try:
        _, a_email, a_so = _seed_customer_with_order("LISTA")
        _, b_email, b_so = _seed_customer_with_order("LISTB")

        frappe.set_user(a_email)
        names = frappe.get_list("SC Sales Order", pluck="name", limit_page_length=0)

        ok = (a_so in names) and (b_so not in names)
        if ok:
            return {"pass": True, "msg": f"OK A chi thay {a_so}, khong thay {b_so}"}
        return {"pass": False, "msg": f"X a_in={a_so in names} b_in={b_so in names} names={names}"}
    except Exception as e:
        return {"pass": False, "msg": f"X threw: {str(e)[:200]}"}
    finally:
        frappe.set_user(orig_user)
        frappe.db.rollback()


def test_portal_A_cannot_read_B_order():
    """Portal A: frappe.has_permission('SC Sales Order','read',doc=B_order) == False."""
    orig_user = frappe.session.user
    try:
        _, a_email, a_so = _seed_customer_with_order("READA")
        _, b_email, b_so = _seed_customer_with_order("READB")

        frappe.set_user(a_email)
        can_read_own = frappe.has_permission("SC Sales Order", "read", doc=a_so)
        can_read_other = frappe.has_permission("SC Sales Order", "read", doc=b_so)

        ok = (can_read_own is True) and (can_read_other is False)
        if ok:
            return {"pass": True, "msg": f"OK A doc duoc {a_so}, khong doc duoc {b_so}"}
        return {"pass": False, "msg": f"X can_read_own={can_read_own} can_read_other={can_read_other}"}
    except Exception as e:
        return {"pass": False, "msg": f"X threw: {str(e)[:200]}"}
    finally:
        frappe.set_user(orig_user)
        frappe.db.rollback()


def test_portal_blocked_internal_doctypes():
    """Portal A: bi chan doctype noi bo (SC Supplier, SC Purchase Order) + chan write tren chinh don cua minh."""
    orig_user = frappe.session.user
    try:
        _, a_email, a_so = _seed_customer_with_order("BLOCK")

        frappe.set_user(a_email)
        supplier_denied = frappe.has_permission("SC Supplier", "read") is False
        po_denied = frappe.has_permission("SC Purchase Order", "read") is False
        write_denied = frappe.has_permission("SC Sales Order", "write", doc=a_so) is False

        ok = supplier_denied and po_denied and write_denied
        if ok:
            return {"pass": True, "msg": "OK bi chan SC Supplier/SC Purchase Order + write tren SO cua minh"}
        return {"pass": False, "msg": (
            f"X supplier_denied={supplier_denied} po_denied={po_denied} write_denied={write_denied}"
        )}
    except Exception as e:
        return {"pass": False, "msg": f"X threw: {str(e)[:200]}"}
    finally:
        frappe.set_user(orig_user)
        frappe.db.rollback()


def test_internal_manager_sees_all():
    """User noi bo (SupplyCore Manager, khong phai Administrator): get_list thay ca A va B (khong hoi quy)."""
    orig_user = frappe.session.user
    try:
        _, a_email, a_so = _seed_customer_with_order("MGRA")
        _, b_email, b_so = _seed_customer_with_order("MGRB")
        manager_email = _make_manager_user()

        frappe.set_user(manager_email)
        names = frappe.get_list("SC Sales Order", pluck="name", limit_page_length=0)

        ok = (a_so in names) and (b_so in names)
        if ok:
            return {"pass": True, "msg": "OK Manager noi bo thay ca don A va don B"}
        return {"pass": False, "msg": f"X a_in={a_so in names} b_in={b_so in names}"}
    except Exception as e:
        return {"pass": False, "msg": f"X threw: {str(e)[:200]}"}
    finally:
        frappe.set_user(orig_user)
        frappe.db.rollback()


def test_portal_child_table_isolation():
    """RSK-01 caveat: truy van THANG vao child doctype (SO Item) voi
    parent_doctype ro rang phai KHONG tra ve dong cua khach khac, du role
    Portal co quyen doc-level tren SC Sales Order (doctype cha). Neu chi dang
    ky permission_query_conditions cho "SC Sales Order" ma khong dang ky rieng
    cho "SO Item", Frappe se khong loc theo customer khi query thang child
    table -> ro ri item/qty cua khach khac (has_child_permission chi kiem tra
    quyen doctype-level tren cha, khong loc theo tung dong)."""
    orig_user = frappe.session.user
    try:
        _, a_email, a_so = _seed_customer_with_order("CHILDA")
        _, b_email, b_so = _seed_customer_with_order("CHILDB")

        frappe.set_user(a_email)
        rows_b = frappe.get_list(
            "SO Item", filters={"parent": b_so}, fields=["item", "qty", "parent"],
            parent_doctype="SC Sales Order",
        )
        rows_a = frappe.get_list(
            "SO Item", filters={"parent": a_so}, fields=["item", "qty", "parent"],
            parent_doctype="SC Sales Order",
        )

        ok = (len(rows_b) == 0) and (len(rows_a) == 1)
        if ok:
            return {"pass": True, "msg": f"OK child SO Item: rows_a={len(rows_a)} rows_b(other)={len(rows_b)}"}
        return {"pass": False, "msg": f"X rows_a={rows_a} rows_b={rows_b}"}
    except Exception as e:
        return {"pass": False, "msg": f"X threw: {str(e)[:200]}"}
    finally:
        frappe.set_user(orig_user)
        frappe.db.rollback()


def test_portal_child_read_scoped():
    """`SO Item` khong the bi liet ke chua qua filter -- ke ca KHONG truyen
    filter `parent` nao (khong chi truong hop da biet parent nhu
    `test_portal_child_table_isolation`) -- permission_query_conditions vao
    thang doctype con van luon ap dung. Day la bao dam THAT SU dang giu:
    khong the DISCOVER docname dong cua khach khac qua bat ky truy van
    list-based nao (list/report) tren "SO Item".

    LUU Y (phat hien khi vet nguon Frappe, xem `portal_child_permission` +
    concerns trong task-3-report.md): mot lan doc DON LE bang dung docname
    da biet truoc -- `frappe.get_doc("SO Item", <name_da_biet>)` roi
    `frappe.has_permission("SO Item", doc=...)` (hoac REST
    `frappe.client.get("SO Item", <name>, parent="SC Sales Order")`) --
    KHONG duoc `has_child_permission()` cua Frappe loc theo customer, vi no
    resolve `doc=getattr(child_doc, "parent_doc", child_doc.parent)` va
    child doc doc lap luon co san thuoc tinh `parent_doc=None` (khong phai
    thieu) nen `getattr` tra ve None thay vi fallback ve `child_doc.parent`
    nhu ky vong -- ca `portal_doc_permission` (cha) lan `portal_child_permission`
    (con, moi dang ky task nay) deu KHONG duoc goi trong duong nay, chi con
    lai kiem tra quyen doctype-level tho (luon True voi role Portal da co
    read=1 tren "SC Sales Order"). Da xac minh thuc nghiem: A doc duoc dong
    "SO Item" cua B qua duong nay neu biet dung docname. Rui ro thuc te thap
    (docname la hash ngau nhien, khong enumerable qua bat ky API portal nao
    -- test nay chinh la bang chung cho dieu do) nhung VAN LA MOT GAP THAT,
    khong the dong bang hook cap child -- can nhan dien va risk-accept o
    muc con nguoi (xem task-3-report.md Concerns), khong phai task nay tu
    "vá" duoc."""
    orig_user = frappe.session.user
    try:
        _, a_email, a_so = _seed_customer_with_order("CHSGA")
        _, b_email, b_so = _seed_customer_with_order("CHSGB")

        frappe.set_user(a_email)
        # KHONG truyen filter parent -- permission_query_conditions vao
        # thang "SO Item" (Task 2) phai tu loc, khong dua vao caller cung
        # cap dung filter.
        rows = frappe.get_list(
            "SO Item", fields=["name", "item", "qty", "parent"],
            parent_doctype="SC Sales Order", limit_page_length=0,
        )
        parents = {r["parent"] for r in rows}

        ok = (a_so in parents) and (b_so not in parents)
        if ok:
            return {"pass": True, "msg": f"OK khong the liet ke/enumerate dong SO Item cua B qua truy van khong filter: parents={parents}"}
        return {"pass": False, "msg": f"X parents={parents}"}
    except Exception as e:
        return {"pass": False, "msg": f"X threw: {str(e)[:200]}"}
    finally:
        frappe.set_user(orig_user)
        frappe.db.rollback()


def test_portal_child_get_denied():
    """RSK-01 Critical: `frappe.client.get` (whitelisted, dùng bởi REST
    `/api/method/frappe.client.get` và FrappeClient) trên 4 child doctype bán
    hàng (SO Item/DN Item/SI Item/SFC Item) PHẢI bị chặn cho Portal caller,
    kể cả khi biết chính xác docname của dòng khách khác (gap đã flag ở
    `test_portal_child_read_scoped`/task-3-report.md, nay đóng lại ở mức
    Critical qua `guarded_client_get`).

    Kiểm cả 3 dạng gọi (per RSK-01 brief): theo `name` đã biết, theo
    `filters={"parent": ...}` (không cần biết docname), theo
    `filters={"item": ...}` (không cần biết parent) -- cho cả 4 doctype.
    Đồng thời kiểm 2 regression bắt buộc: Portal A vẫn đọc được dữ liệu CỦA
    CHÍNH MÌNH qua Portal API (không over-block), và internal Manager vẫn
    `frappe.client.get` được dòng con bình thường (delegation nguyên vẹn).

    QUAN TRỌNG: gọi qua `frappe.override_whitelisted_method("frappe.client.get")`
    + `frappe.get_attr(...)` -- ĐÚNG cơ chế resolve mà `frappe.handler.execute_cmd`
    dùng khi 1 request thật tới `/api/method/frappe.client.get` -- KHÔNG gọi
    thẳng `frappe.client.get` (import trực tiếp sẽ bỏ qua override hoàn toàn,
    test sẽ luôn "pass" giả -- không phản ánh đúng đường đi thật)."""
    from supplycore.api.portal import portal_order_track

    def client_get(doctype, **kwargs):
        method_path = frappe.override_whitelisted_method("frappe.client.get")
        method = frappe.get_attr(method_path)
        return method(doctype, **kwargs)

    orig_user = frappe.session.user
    try:
        _, a_email, a_so = _seed_customer_with_order("CGETA")
        b = _seed_customer_full_chain("CGETB")
        manager_email = _make_manager_user()

        b_so_item = frappe.db.get_value("SO Item", {"parent": b["so"]}, "name")
        b_sfc_item = frappe.db.get_value("SFC Item", {"parent": b["sfc"]}, "name")
        b_dn_item = frappe.db.get_value("DN Item", {"parent": b["dn"]}, "name")
        b_si_item = frappe.db.get_value("SI Item", {"parent": b["si"]}, "name")

        forms = [
            ("SO Item", {"name": b_so_item, "parent": "SC Sales Order"}),
            ("SO Item", {"filters": {"parent": b["so"]}, "parent": "SC Sales Order"}),
            ("SO Item", {"filters": {"item": b["item"]}, "parent": "SC Sales Order"}),
            ("DN Item", {"name": b_dn_item, "parent": "SC Delivery Note"}),
            ("DN Item", {"filters": {"parent": b["dn"]}, "parent": "SC Delivery Note"}),
            ("DN Item", {"filters": {"item": b["item"]}, "parent": "SC Delivery Note"}),
            ("SI Item", {"name": b_si_item, "parent": "SC Sales Invoice"}),
            ("SI Item", {"filters": {"parent": b["si"]}, "parent": "SC Sales Invoice"}),
            ("SI Item", {"filters": {"item": b["item"]}, "parent": "SC Sales Invoice"}),
            ("SFC Item", {"name": b_sfc_item, "parent": "SC Sales Framework Contract"}),
            ("SFC Item", {"filters": {"parent": b["sfc"]}, "parent": "SC Sales Framework Contract"}),
            ("SFC Item", {"filters": {"item": b["item"]}, "parent": "SC Sales Framework Contract"}),
        ]

        frappe.set_user(a_email)
        leaks = []
        for doctype, kwargs in forms:
            try:
                res = client_get(doctype, **kwargs)
                leaks.append(f"{doctype} {kwargs} -> LEAKED {res}")
            except frappe.PermissionError:
                pass
            except Exception as e:
                leaks.append(f"{doctype} {kwargs} -> unexpected {type(e).__name__}: {str(e)[:120]}")

        # Regression 1: A vẫn đọc được đơn CỦA CHÍNH MÌNH qua Portal API.
        own = portal_order_track(a_so)
        own_ok = own.get("order") == a_so

        # Regression 2: internal Manager (không phải Portal) vẫn frappe.client.get
        # được dòng con bình thường -- delegation nguyên vẹn, không over-block.
        frappe.set_user(manager_email)
        internal_res = client_get("SO Item", name=b_so_item, parent="SC Sales Order")
        internal_ok = internal_res.get("parent") == b["so"]

        ok = (not leaks) and own_ok and internal_ok
        if ok:
            return {"pass": True, "msg": (
                f"OK {len(forms)} dạng gọi đều PermissionError, A đọc được đơn "
                f"của mình, Manager nội bộ vẫn frappe.client.get được"
            )}
        return {"pass": False, "msg": (
            f"X leaks={leaks} own_ok={own_ok} internal_ok={internal_ok}"
        )}
    except Exception as e:
        return {"pass": False, "msg": f"X threw: {str(e)[:300]}"}
    finally:
        frappe.set_user(orig_user)
        frappe.db.rollback()


def test_portal_rest_child_guard():
    """GĐ4 Task 2 -- đóng residual RSK-01 còn lại: hàm guard
    `portal_block_rest_child` (đăng ký làm `before_request` hook ở hooks.py)
    phải chặn role Portal đọc REST resource/document endpoint cho 4 child
    doctype bán hàng (SO Item/DN Item/SI Item/SFC Item), CẢ 2 router version
    của Frappe -- vector RSK-01 duy nhất còn hở sau `test_portal_child_get_denied`
    (xem docstring `test_portal_child_read_scoped`): 2 route này đi qua
    `frappe/api/v1.py::read_doc` và `frappe/api/v2.py::read_doc`
    (`frappe/api/__init__.py::API_URL_MAP` submount CẢ HAI song song, không
    phải 1 route duy nhất), KHÔNG qua `override_whitelisted_methods` (chỉ áp
    dụng `/api/method/frappe.client.get`) nên không bị `guarded_client_get`
    chặn -- nếu biết đúng docname (hash) của dòng con khách khác, Portal
    caller vẫn đọc được qua 1 trong 2 route REST này.

    Gọi THẲNG hàm guard (không dựng HTTP request thật -- `bench execute`
    không có WSGI/Werkzeug request context để spin 1 request HTTP đầy đủ; xem
    ghi chú giới hạn trong task-2-report.md), mô phỏng `frappe.local.request`
    bằng 1 fake object chỉ có thuộc tính `.path` (đúng thuộc tính hàm guard
    đọc, xem docstring `portal_block_rest_child`).

    Kiểm cả 3 prefix REST (`/api/resource/`, `/api/v1/resource/`,
    `/api/v2/document/`) với path child của B -> PermissionError cho Portal
    A; rồi thêm 2 nhánh trên path `/api/resource/`: internal Manager với
    CÙNG path -> không raise (không hồi quy nội bộ); Portal A với path REST
    resource của doctype CHA (SC Sales Order) -- đã được gate ở nhánh khác
    (`portal_doc_permission`), KHÔNG thuộc phạm vi guard này -> không raise."""
    from supplycore.utils.permissions import portal_block_rest_child

    class _FakeRequest:
        def __init__(self, path):
            self.path = path

    orig_user = frappe.session.user
    orig_request = getattr(frappe.local, "request", None)
    try:
        _, a_email, a_so = _seed_customer_with_order("RESTG")
        manager_email = _make_manager_user()

        child_name = "some-hash-name-doesnt-need-to-exist"
        child_paths = [
            f"/api/resource/SO Item/{child_name}",
            f"/api/v1/resource/SO Item/{child_name}",
            f"/api/v2/document/SO Item/{child_name}/",
        ]
        parent_path = f"/api/resource/SC Sales Order/{a_so}"

        # 1) Portal A doc REST child cua khach khac qua CA 3 prefix (v1 qua
        # submount "/api" va "/api/v1", v2 qua "/api/v2/document") -> phai bi
        # chan o muc path, khong can doc thuc DB.
        frappe.set_user(a_email)
        child_blocked_per_path = {}
        for p in child_paths:
            frappe.local.request = _FakeRequest(p)
            try:
                portal_block_rest_child()
                child_blocked_per_path[p] = False
            except frappe.PermissionError:
                child_blocked_per_path[p] = True
        child_blocked = all(child_blocked_per_path.values())

        # 2) Internal Manager (khong phai Portal) voi CUNG path v1 -> khong bi
        # chan (guard chi nham role Portal, khong hoi quy noi bo).
        frappe.local.request = _FakeRequest(child_paths[0])
        frappe.set_user(manager_email)
        manager_ok = True
        try:
            portal_block_rest_child()
        except Exception:
            manager_ok = False

        # 3) Portal A voi REST resource cua doctype CHA chinh minh -> khong
        # thuoc pham vi guard nay (da duoc gate rieng qua
        # portal_doc_permission/has_permission) -> khong raise tu day.
        frappe.local.request = _FakeRequest(parent_path)
        frappe.set_user(a_email)
        parent_ok = True
        try:
            portal_block_rest_child()
        except Exception:
            parent_ok = False

        ok = child_blocked and manager_ok and parent_ok
        if ok:
            return {"pass": True, "msg": (
                "OK guard chan Portal tren ca 3 prefix REST child (v1 /api, "
                "v1 /api/v1, v2 /api/v2/document), khong chan Manager noi bo "
                "hay path REST cua doctype cha"
            )}
        return {"pass": False, "msg": (
            f"X child_blocked_per_path={child_blocked_per_path} "
            f"manager_ok={manager_ok} parent_ok={parent_ok}"
        )}
    except Exception as e:
        return {"pass": False, "msg": f"X threw: {str(e)[:300]}"}
    finally:
        frappe.local.request = orig_request
        frappe.set_user(orig_user)
        frappe.db.rollback()


def run():
    tests = [
        test_portal_A_lists_only_own_orders,
        test_portal_A_cannot_read_B_order,
        test_portal_blocked_internal_doctypes,
        test_internal_manager_sees_all,
        test_portal_child_table_isolation,
        test_portal_child_read_scoped,
        test_portal_child_get_denied,
        test_portal_rest_child_guard,
    ]
    results = []
    for t in tests:
        try:
            r = t()
            r["test"] = t.__name__
        except Exception as e:
            r = {"test": t.__name__, "pass": False, "msg": f"EXCEPTION: {str(e)[:200]}"}
        results.append(r)
    frappe.db.rollback()
    passed = sum(1 for r in results if r.get("pass"))
    return {"passed": passed, "total": len(results), "results": results}
