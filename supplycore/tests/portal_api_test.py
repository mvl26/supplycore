"""Test GD3 M12 Task 3 -- 7 API Portal khach hang (api/portal.py).

Run individual: bench --site supplycore-miyano.local execute supplycore.tests.portal_api_test.test_<name>
Run all:        bench --site supplycore-miyano.local execute supplycore.tests.portal_api_test.run
"""

import frappe
from frappe.utils import today, add_days, random_string, flt


def _get_uom() -> str:
    return frappe.db.get_value("SC UOM", {}, "name")


def _pick_warehouse() -> str:
    rows = frappe.get_all("SC Warehouse", filters={"is_group": 0, "disabled": 0},
                           pluck="name", order_by="name", limit=1)
    if not rows:
        frappe.throw("portal_api_test: cần seed SC Warehouse")
    return rows[0]


def _make_item(suffix):
    item = frappe.new_doc("SC Item")
    item.item_code = f"PAPI-{suffix}-{random_string(5)}"
    item.item_name = f"Portal API test item {suffix}"
    item.uom = _get_uom()
    item.is_stock_item = 1
    item.has_batch_no = 1
    item.flags.ignore_permissions = True
    item.insert()
    return item


def _make_batch(item, expiry_date, qc_status="Accepted"):
    b = frappe.new_doc("SC Batch")
    b.batch_id = f"{item}-{random_string(6)}"
    b.item = item
    b.expiry_date = expiry_date
    b.manufacturing_date = add_days(expiry_date, -365)
    b.qc_status = qc_status
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


def _make_portal_customer(suffix, credit_limit=0):
    """Tao SC Customer, provision tai khoan Portal, kich hoat (Hoat dong).

    Mirror portal_isolation_test.py::_make_portal_customer -- portal_provision
    chuan hoa email ve chu thuong, PHAI dung gia tri tra ve (khong dung lai
    bien `email` goc) khi frappe.set_user() sau nay.
    """
    from supplycore.api.portal import portal_provision

    c = frappe.new_doc("SC Customer")
    c.customer_name = f"KH PortalAPI {suffix} {random_string(6)}"
    c.tax_code = f"TAX-PAPI-{suffix}-{random_string(8)}"
    c.status = "Tạm ngưng"
    c.credit_limit = flt(credit_limit)
    c.flags.ignore_permissions = True
    c.insert()

    email = f"portal_api_{suffix.lower()}_{random_string(6)}@example.com"
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


def _seed_customer_with_contract(suffix, contract_qty=100, unit_price=1000):
    """Seed 1 khach Portal (Hoat dong) + 1 item + 1 SFC Hieu luc."""
    cust, portal_email = _make_portal_customer(suffix)
    item = _make_item(suffix)
    sfc = _make_submitted_sfc(cust.name, item.name, contract_qty, unit_price)
    return cust.name, portal_email, sfc.name, item.name


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
    so.reload()
    return so


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


def _make_invoice_for_customer(suffix, qty=10, unit_price=1000):
    """Xay chuoi day du: khach Portal -> item -> SFC -> SO(duyet) -> DN(nghiem
    thu) -> SI(phat hanh). Dung cho test document_download."""
    cust, portal_email, sfc_name, item_name = _seed_customer_with_contract(
        suffix, contract_qty=100, unit_price=unit_price)
    so = _make_approved_so(cust, sfc_name, item_name, qty)

    wh = _pick_warehouse()
    batch = _make_batch(item_name, add_days(today(), 200))
    _seed_stock(item_name, wh, batch.name, qty * 2, rate=unit_price)

    dn = frappe.new_doc("SC Delivery Note")
    dn.sales_order = so.name
    dn.from_warehouse = wh
    dn.delivery_date = today()
    dn.append("items", {"item": item_name, "uom": _get_uom(), "qty": flt(qty)})
    dn.flags.ignore_permissions = True
    dn.insert()
    dn.submit()
    dn.reload()
    _accept_dn(dn)

    si = frappe.new_doc("SC Sales Invoice")
    si.customer = cust
    si.delivery_note = dn.name
    si.invoice_date = today()
    si.append("items", {"item": item_name, "qty": flt(qty), "unit_price": flt(unit_price)})
    si.flags.ignore_permissions = True
    si.insert()
    si.submit()

    return cust, portal_email, si.name


def _make_manager_user():
    """1 System User noi bo (SupplyCore Manager, khong phai portal, khong phai
    Administrator) -- de kiem tra internal user khong map customer bi tu choi."""
    email = f"manager_papi_{random_string(8)}@example.com"
    u = frappe.new_doc("User")
    u.email = email
    u.first_name = "PortalAPI Manager Test"
    u.user_type = "System User"
    u.send_welcome_email = 0
    u.append("roles", {"role": "SupplyCore Manager"})
    u.flags.ignore_permissions = True
    u.insert()
    return email


# ---------- Tests ----------

def test_portal_me():
    """set_user(A) -> portal_me tra ve dung khach hang cua A + credit_limit + outstanding."""
    orig_user = frappe.session.user
    try:
        cust, portal_email, sfc, item = _seed_customer_with_contract("ME", contract_qty=50, unit_price=2000)
        frappe.db.set_value("SC Customer", cust, "credit_limit", 5_000_000)

        from supplycore.api.portal import portal_me

        frappe.set_user(portal_email)
        res = portal_me()

        ok = (res["customer"] == cust) and (flt(res["credit_limit"]) == 5_000_000) and ("outstanding" in res)
        if ok:
            return {"pass": True, "msg": f"OK portal_me: {res}"}
        return {"pass": False, "msg": f"X res={res}"}
    except Exception as e:
        return {"pass": False, "msg": f"X threw: {str(e)[:200]}"}
    finally:
        frappe.set_user(orig_user)
        frappe.db.rollback()


def test_portal_contracts_and_catalog():
    """set_user(A) -> portal_contracts/portal_catalog chi tra du lieu cua A, khong cua B."""
    orig_user = frappe.session.user
    try:
        cust_a, email_a, sfc_a, item_a = _seed_customer_with_contract("CONTA", contract_qty=100, unit_price=1500)
        cust_b, email_b, sfc_b, item_b = _seed_customer_with_contract("CONTB", contract_qty=100, unit_price=1500)

        from supplycore.api.portal import portal_contracts, portal_catalog

        frappe.set_user(email_a)
        contracts = portal_contracts()
        catalog = portal_catalog()

        contract_names = [c["name"] for c in contracts]
        catalog_items = [c["item"] for c in catalog]

        ok = (
            sfc_a in contract_names and sfc_b not in contract_names
            and item_a in catalog_items and item_b not in catalog_items
        )
        if ok:
            return {"pass": True, "msg": f"OK contracts={contract_names} catalog_items={catalog_items}"}
        return {"pass": False, "msg": f"X contracts={contract_names} catalog_items={catalog_items}"}
    except Exception as e:
        return {"pass": False, "msg": f"X threw: {str(e)[:200]}"}
    finally:
        frappe.set_user(orig_user)
        frappe.db.rollback()


def test_portal_order_place():
    """order_place tao SO 'Cho duyet' dung gia HD; qty vuot remaining -> throw BRU-SO-001."""
    orig_user = frappe.session.user
    try:
        cust, email, sfc, item = _seed_customer_with_contract("PLACE", contract_qty=50, unit_price=3000)

        from supplycore.api.portal import portal_order_place

        frappe.set_user(email)
        res = portal_order_place(sfc, [{"item": item, "qty": 10}])

        so = frappe.get_doc("SC Sales Order", res["order"])
        ok1 = (
            so.customer == cust and so.status == "Chờ duyệt"
            and flt(so.items[0].unit_price) == 3000
            and flt(res["total_amount"]) == 30000
        )
        if not ok1:
            return {"pass": False, "msg": f"X status={so.status} unit_price={so.items[0].unit_price} total={res.get('total_amount')}"}

        # qty vuot remaining (50 - 10 da dat = 40 con lai) -> throw BRU-SO-001
        try:
            portal_order_place(sfc, [{"item": item, "qty": 999}])
            return {"pass": False, "msg": "X qty vuot remaining khong throw"}
        except frappe.ValidationError as e:
            if "BRU-SO-001" not in str(e):
                return {"pass": False, "msg": f"X wrong error: {str(e)[:150]}"}

        return {"pass": True, "msg": f"OK order {so.name} Chờ duyệt, gia HD, over-qty throw BRU-SO-001"}
    except Exception as e:
        return {"pass": False, "msg": f"X threw: {str(e)[:200]}"}
    finally:
        frappe.set_user(orig_user)
        frappe.db.rollback()


def test_order_place_zero_qty_rejected():
    """BUG 2: portal_order_place voi qty<=0 phai bi tu choi -- khong the tao
    SO rac tong tien = 0 qua Portal. qty>0 van hoat dong binh thuong."""
    orig_user = frappe.session.user
    try:
        cust, email, sfc, item = _seed_customer_with_contract("ZEROQ", contract_qty=50, unit_price=1000)

        from supplycore.api.portal import portal_order_place

        frappe.set_user(email)
        try:
            portal_order_place(sfc, [{"item": item, "qty": 0}])
            return {"pass": False, "msg": "X qty=0 khong throw"}
        except frappe.ValidationError:
            pass

        # qty am cung phai bi chan
        try:
            portal_order_place(sfc, [{"item": item, "qty": -5}])
            return {"pass": False, "msg": "X qty=-5 khong throw"}
        except frappe.ValidationError:
            pass

        # qty > 0 van dat hang binh thuong
        res = portal_order_place(sfc, [{"item": item, "qty": 5}])
        so = frappe.get_doc("SC Sales Order", res["order"])
        ok = so.customer == cust and flt(res["total_amount"]) == 5000
        if ok:
            return {"pass": True, "msg": f"OK qty<=0 rejected, qty>0 order={so.name} total={res['total_amount']}"}
        return {"pass": False, "msg": f"X qty>0 order sai: {res}"}
    except Exception as e:
        return {"pass": False, "msg": f"X threw wrong exception: {str(e)[:200]}"}
    finally:
        frappe.set_user(orig_user)
        frappe.db.rollback()


def test_order_place_other_contract_denied():
    """set_user(A), contract=SFC cua B -> PermissionError."""
    orig_user = frappe.session.user
    try:
        cust_a, email_a, sfc_a, item_a = _seed_customer_with_contract("OPDA", contract_qty=50, unit_price=1000)
        cust_b, email_b, sfc_b, item_b = _seed_customer_with_contract("OPDB", contract_qty=50, unit_price=1000)

        from supplycore.api.portal import portal_order_place

        frappe.set_user(email_a)
        try:
            portal_order_place(sfc_b, [{"item": item_b, "qty": 5}])
            return {"pass": False, "msg": "X khong throw khi dat hang tren HD cua khach khac"}
        except frappe.PermissionError:
            return {"pass": True, "msg": "OK PermissionError khi dat hang tren HD cua khach khac"}
    except Exception as e:
        return {"pass": False, "msg": f"X threw wrong exception: {str(e)[:200]}"}
    finally:
        frappe.set_user(orig_user)
        frappe.db.rollback()


def test_order_track_and_history_own_only():
    """set_user(A) -> track don cua A ok; track don cua B -> PermissionError; history chi co don cua A."""
    orig_user = frappe.session.user
    try:
        cust_a, email_a, sfc_a, item_a = _seed_customer_with_contract("TRKA", contract_qty=100, unit_price=1000)
        cust_b, email_b, sfc_b, item_b = _seed_customer_with_contract("TRKB", contract_qty=100, unit_price=1000)

        so_a = _make_approved_so(cust_a, sfc_a, item_a, 10)
        so_b = _make_approved_so(cust_b, sfc_b, item_b, 10)

        from supplycore.api.portal import portal_order_track, portal_order_history

        frappe.set_user(email_a)
        track_a = portal_order_track(so_a.name)
        ok_track_a = (track_a["order"] == so_a.name and track_a["status"] == "Đã duyệt"
                      and len(track_a["milestones"]) >= 1)

        try:
            portal_order_track(so_b.name)
            return {"pass": False, "msg": "X track don cua B khong throw"}
        except frappe.PermissionError:
            pass

        history = portal_order_history()
        history_names = [h["name"] for h in history]
        ok_history = (so_a.name in history_names) and (so_b.name not in history_names)

        if ok_track_a and ok_history:
            return {"pass": True, "msg": f"OK track={track_a} history={history_names}"}
        return {"pass": False, "msg": f"X ok_track_a={ok_track_a} ok_history={ok_history} history={history_names}"}
    except Exception as e:
        return {"pass": False, "msg": f"X threw: {str(e)[:200]}"}
    finally:
        frappe.set_user(orig_user)
        frappe.db.rollback()


def test_document_download_other_customer_denied():
    """set_user(A), tai xuong hoa don cua B -> PermissionError; doctype khong hop le -> throw."""
    orig_user = frappe.session.user
    try:
        cust_a, email_a, sfc_a, item_a = _seed_customer_with_contract("DLA", contract_qty=100, unit_price=1000)
        cust_b, email_b, si_b = _make_invoice_for_customer("DLB", qty=10, unit_price=1000)

        from supplycore.api.portal import portal_document_download

        frappe.set_user(email_a)
        try:
            portal_document_download("SC Sales Invoice", si_b)
            return {"pass": False, "msg": "X tai xuong hoa don cua B khong throw"}
        except frappe.PermissionError:
            pass

        try:
            portal_document_download("SC Item", item_a)
            return {"pass": False, "msg": "X doctype khong hop le khong throw"}
        except frappe.PermissionError:
            return {"pass": False, "msg": "X doctype khong hop le nen throw ValidationError, khong phai PermissionError"}
        except Exception:
            pass

        return {"pass": True, "msg": "OK PermissionError cho hoa don khac khach + throw cho doctype khong hop le"}
    except Exception as e:
        return {"pass": False, "msg": f"X threw: {str(e)[:200]}"}
    finally:
        frappe.set_user(orig_user)
        frappe.db.rollback()


def test_portal_api_internal_user_denied():
    """set_user(Manager noi bo, khong phai portal) -> portal_me raise PermissionError."""
    orig_user = frappe.session.user
    try:
        manager_email = _make_manager_user()

        from supplycore.api.portal import portal_me

        frappe.set_user(manager_email)
        try:
            portal_me()
            return {"pass": False, "msg": "X internal user goi portal_me khong throw"}
        except frappe.PermissionError:
            return {"pass": True, "msg": "OK PermissionError cho internal user"}
    except Exception as e:
        return {"pass": False, "msg": f"X threw wrong exception: {str(e)[:200]}"}
    finally:
        frappe.set_user(orig_user)
        frappe.db.rollback()


def run():
    tests = [
        test_portal_me,
        test_portal_contracts_and_catalog,
        test_portal_order_place,
        test_order_place_zero_qty_rejected,
        test_order_place_other_contract_denied,
        test_order_track_and_history_own_only,
        test_document_download_other_customer_denied,
        test_portal_api_internal_user_denied,
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
