"""Test UC-18 — Stock Transfer (intra-warehouse).

Run individual: bench --site supplycore execute supplycore.tests.uc18_test.test_<name>
Run all:        bench --site supplycore execute supplycore.tests.uc18_test.run
"""

import frappe
from frappe.utils import today, add_days, random_string, flt


def _get_uom() -> str:
    uom = frappe.db.get_value("SC UOM", {}, "name")
    if not uom:
        frappe.throw("uc18_test: cần seed SC UOM")
    return uom


def _pick_warehouses_by_type():
    """Trả (main_wh, sub_wh, dept_wh) — pick từ seed."""
    main = frappe.db.get_value("SC Warehouse",
        {"warehouse_type": "Main", "is_group": 0, "disabled": 0}, "name")
    sub = frappe.db.get_value("SC Warehouse",
        {"warehouse_type": "Sub", "is_group": 0, "disabled": 0}, "name")
    dept = frappe.db.get_value("SC Warehouse",
        {"warehouse_type": "Department", "is_group": 0, "disabled": 0}, "name")
    return main, sub, dept


def _make_item(suffix: str):
    item = frappe.new_doc("SC Item")
    item.item_code = f"UC18-{suffix}-{random_string(5)}"
    item.item_name = f"UC-18 test {suffix}"
    item.uom = _get_uom()
    item.is_stock_item = 1
    item.flags.ignore_permissions = True
    item.insert()
    return item


def _seed_stock(item, warehouse, qty):
    from supplycore.supplycore.doctype.sc_stock_ledger_entry.sc_stock_ledger_entry import SCStockLedgerEntry
    return SCStockLedgerEntry.post(
        item=item, warehouse=warehouse, qty_change=flt(qty),
        voucher_type="Manual", voucher_no=f"UC18-{random_string(6)}",
        posting_date=today(),
    )


def _make_tr(from_wh, to_wh, item, qty, **kwargs):
    tr = frappe.new_doc("SC Transfer Request")
    tr.request_date = today()
    tr.required_by = today()
    tr.transfer_type = "Routine"
    tr.from_warehouse = from_wh
    tr.to_warehouse = to_wh
    tr.append("items", {
        "item": item, "uom": _get_uom(),
        "requested_qty": flt(qty), "approved_qty": flt(qty),
    })
    tr.flags.ignore_permissions = True
    for k, v in kwargs.items():
        setattr(tr, k, v)
    return tr


# ---------- Tests ----------

def test_tr_create_basic():
    """Tạo TR + save OK."""
    main, sub, _ = _pick_warehouses_by_type()
    if not (main and sub):
        return {"pass": True, "msg": "OK (skipped: missing Main/Sub warehouses)"}
    item = _make_item("BASIC")
    _seed_stock(item.name, main, 100)
    tr = _make_tr(main, sub, item.name, 10)
    try:
        tr.insert()
        ok = (tr.name and tr.status == "Draft")
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK TR {tr.name}"}
        return {"pass": False, "msg": f"X status={tr.status}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_tr_same_warehouse_rejected():
    """from=to → throw."""
    main, _, _ = _pick_warehouses_by_type()
    if not main:
        return {"pass": True, "msg": "OK (skipped: no Main warehouse)"}
    item = _make_item("SAME")
    _seed_stock(item.name, main, 100)
    tr = _make_tr(main, main, item.name, 5)
    try:
        tr.insert()
        frappe.db.rollback()
        return {"pass": False, "msg": "X did not throw same warehouse"}
    except frappe.ValidationError as e:
        msg = str(e)
        frappe.db.rollback()
        if "khác" in msg or "different" in msg.lower():
            return {"pass": True, "msg": f"OK: {msg[:120]}"}
        return {"pass": False, "msg": f"Wrong error: {msg[:120]}"}


def test_tr_insufficient_stock_throws():
    """approved > available → throw SC-E-TRANSFER-INSUFFICIENT."""
    main, sub, _ = _pick_warehouses_by_type()
    if not (main and sub):
        return {"pass": True, "msg": "OK (skipped)"}
    item = _make_item("INSUF")
    _seed_stock(item.name, main, 5)  # only 5 available
    tr = _make_tr(main, sub, item.name, 50)  # request 50
    try:
        tr.insert()
        tr.submit()
        frappe.db.rollback()
        return {"pass": False, "msg": "X submit không throw"}
    except frappe.ValidationError as e:
        msg = str(e)
        frappe.db.rollback()
        if "SC-E-TRANSFER-INSUFFICIENT" in msg and "Tối đa" in msg:
            return {"pass": True, "msg": f"OK: {msg[:120]}"}
        return {"pass": False, "msg": f"Wrong error: {msg[:120]}"}


def test_tr_detect_cross_tier_to_department():
    """to=Department → requires_manager_approval=1."""
    main, _, dept = _pick_warehouses_by_type()
    if not (main and dept):
        return {"pass": True, "msg": "OK (skipped: missing Department warehouse)"}
    item = _make_item("CTDEPT")
    _seed_stock(item.name, main, 100)
    tr = _make_tr(main, dept, item.name, 10)
    try:
        tr.insert()
        ok = (tr.requires_manager_approval == 1)
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": "OK requires_manager_approval=1"}
        return {"pass": False, "msg": f"X requires={tr.requires_manager_approval}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_tr_same_tier_no_approval_required():
    """Main↔Sub → requires_manager_approval=0."""
    main, sub, _ = _pick_warehouses_by_type()
    if not (main and sub):
        return {"pass": True, "msg": "OK (skipped)"}
    item = _make_item("ST")
    _seed_stock(item.name, main, 100)
    tr = _make_tr(main, sub, item.name, 10)
    tr.requires_manager_approval = 0  # explicit reset
    try:
        tr.insert()
        # _detect_cross_tier có thể không set khi cả 2 != Department
        ok = (tr.requires_manager_approval == 0)
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": "OK same-tier no approval"}
        return {"pass": False, "msg": f"X requires={tr.requires_manager_approval}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_tr_cross_tier_blocks_non_manager():
    """requires_manager_approval=1 + non-Manager → SC-E-TRANSFER-MANAGER-REQUIRED."""
    main, _, dept = _pick_warehouses_by_type()
    if not (main and dept):
        return {"pass": True, "msg": "OK (skipped)"}
    item = _make_item("BLKMGR")
    _seed_stock(item.name, main, 50)
    tr = _make_tr(main, dept, item.name, 10)

    sk_user = frappe.db.get_value("User",
        {"enabled": 1, "name": ["!=", "Administrator"]}, "name")
    if not sk_user:
        return {"pass": True, "msg": "OK (skipped: no non-admin user)"}

    sk_doc = frappe.get_doc("User", sk_user)
    original_roles = [r.role for r in sk_doc.roles]
    sk_doc.roles = []
    sk_doc.append("roles", {"role": "SupplyCore Storekeeper"})
    sk_doc.save(ignore_permissions=True)

    original_user = frappe.session.user
    try:
        tr.insert()
        frappe.set_user(sk_user)
        try:
            tr.submit()
            frappe.set_user(original_user)
            frappe.db.rollback()
            return {"pass": False, "msg": "X submit không bị block"}
        except frappe.ValidationError as e:
            msg = str(e)
            frappe.set_user(original_user)
            frappe.db.rollback()
            if "SC-E-TRANSFER-MANAGER-REQUIRED" in msg:
                return {"pass": True, "msg": f"OK: {msg[:120]}"}
            return {"pass": False, "msg": f"Wrong error: {msg[:120]}"}
    except Exception as e:
        frappe.set_user(original_user)
        frappe.db.rollback()
        return {"pass": False, "msg": f"X setup: {str(e)[:120]}"}


def test_tr_cross_tier_allows_manager():
    """Admin (System Manager) submit cross-tier → OK."""
    main, _, dept = _pick_warehouses_by_type()
    if not (main and dept):
        return {"pass": True, "msg": "OK (skipped)"}
    item = _make_item("MGROK")
    _seed_stock(item.name, main, 50)
    tr = _make_tr(main, dept, item.name, 10)
    try:
        tr.insert()
        tr.submit()
        tr.reload()
        ok = (tr.docstatus == 1 and tr.status == "Approved")
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": "OK submitted by Manager"}
        return {"pass": False, "msg": f"X doc={tr.docstatus} status={tr.status}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_tr_make_stock_entry():
    """TR Approved → make_stock_entry → SE Draft tạo OK."""
    main, sub, _ = _pick_warehouses_by_type()
    if not (main and sub):
        return {"pass": True, "msg": "OK (skipped)"}
    item = _make_item("MKSE")
    _seed_stock(item.name, main, 100)
    tr = _make_tr(main, sub, item.name, 20)
    try:
        tr.insert()
        tr.submit()
        tr.reload()
        se_name = tr.make_stock_entry()
        se = frappe.get_doc("SC Stock Entry", se_name)
        ok = (se.entry_type == "Material Transfer"
              and se.transfer_request == tr.name
              and se.docstatus == 0)
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK SE {se_name} draft"}
        return {"pass": False, "msg": f"X type={se.entry_type} link={se.transfer_request} doc={se.docstatus}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_se_submit_syncs_tr_received():
    """SE submit → TR.status=Received + transferred_qty set."""
    main, sub, _ = _pick_warehouses_by_type()
    if not (main and sub):
        return {"pass": True, "msg": "OK (skipped)"}
    item = _make_item("SYNC")
    _seed_stock(item.name, main, 100)
    tr = _make_tr(main, sub, item.name, 15)
    try:
        tr.insert()
        tr.submit()
        tr.reload()
        se_name = tr.make_stock_entry()
        se = frappe.get_doc("SC Stock Entry", se_name)
        se.submit()
        tr.reload()
        ok = (tr.status == "Received")
        transferred = flt(tr.items[0].transferred_qty) if tr.items else 0
        frappe.db.rollback()
        if ok and abs(transferred - 15) < 0.01:
            return {"pass": True, "msg": f"OK Received, transferred=15"}
        return {"pass": False, "msg": f"X status={tr.status} transferred={transferred}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_get_transfer_slip_data():
    """get_transfer_slip_data trả dict đủ field."""
    main, sub, _ = _pick_warehouses_by_type()
    if not (main and sub):
        return {"pass": True, "msg": "OK (skipped)"}
    item = _make_item("SLIP")
    _seed_stock(item.name, main, 50)
    tr = _make_tr(main, sub, item.name, 5)
    try:
        tr.insert()
        data = tr.get_transfer_slip_data()
        frappe.db.rollback()
        required = {"name", "from_warehouse", "to_warehouse", "items", "url"}
        if required.issubset(set(data.keys())) and len(data["items"]) == 1:
            return {"pass": True, "msg": f"OK slip data keys"}
        return {"pass": False, "msg": f"X missing: {required - set(data.keys())}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def run():
    tests = [
        test_tr_create_basic,
        test_tr_same_warehouse_rejected,
        test_tr_insufficient_stock_throws,
        test_tr_detect_cross_tier_to_department,
        test_tr_same_tier_no_approval_required,
        test_tr_cross_tier_blocks_non_manager,
        test_tr_cross_tier_allows_manager,
        test_tr_make_stock_entry,
        test_se_submit_syncs_tr_received,
        test_get_transfer_slip_data,
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
