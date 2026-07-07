"""Test GD3 M12 Task 2 -- Co lap du lieu khach hang Portal (RSK-01):
permission_query_conditions + has_permission tren 5 doctype ban hang.

Run individual: bench --site supplycore-miyano.local execute supplycore.tests.portal_isolation_test.test_<name>
Run all:        bench --site supplycore-miyano.local execute supplycore.tests.portal_isolation_test.run
"""

import frappe
from frappe.utils import today, add_days, random_string, flt


def _get_uom() -> str:
    return frappe.db.get_value("SC UOM", {}, "name")


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


def run():
    tests = [
        test_portal_A_lists_only_own_orders,
        test_portal_A_cannot_read_B_order,
        test_portal_blocked_internal_doctypes,
        test_internal_manager_sees_all,
        test_portal_child_table_isolation,
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
