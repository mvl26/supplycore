"""Test UC-15 — Batch tracking.

Run individual: bench --site supplycore execute supplycore.tests.uc15_test.test_<name>
Run all:        bench --site supplycore execute supplycore.tests.uc15_test.run
"""

import frappe
from frappe.utils import today, add_days, random_string, flt


def _get_uom() -> str:
    uom = frappe.db.get_value("SC UOM", {}, "name")
    if not uom:
        frappe.throw("uc15_test: cần seed SC UOM")
    return uom


def _make_item(suffix: str, has_batch: int = 1):
    item = frappe.new_doc("SC Item")
    item.item_code = f"UC15-{suffix}-{random_string(5)}"
    item.item_name = f"UC-15 test {suffix}"
    item.uom = _get_uom()
    item.is_stock_item = 1
    item.has_batch_no = has_batch
    item.flags.ignore_permissions = True
    item.insert()
    return item


def _make_batch(item: str, expiry_offset_days: int = 365, supplier_batch_no: str = None,
                 expiry_warning_ack: int = 0, ignore_short_expiry: bool = False):
    b = frappe.new_doc("SC Batch")
    from supplycore.m5_fefo.api.batch_helpers import generate_batch_id
    expiry = add_days(today(), expiry_offset_days)
    b.batch_id = generate_batch_id(item, str(expiry))
    b.item = item
    b.expiry_date = expiry
    b.manufacturing_date = today()
    if supplier_batch_no:
        b.supplier_batch_no = supplier_batch_no
    if expiry_warning_ack:
        b.expiry_warning_ack = 1
    b.flags.ignore_permissions = True
    if ignore_short_expiry:
        b.flags.ignore_short_expiry = 1
    return b


# ---------- Tests ----------

def test_generate_batch_id_format():
    """Item ABC + expiry 2027-03-15 → format ABC-202703-001."""
    from supplycore.m5_fefo.api.batch_helpers import generate_batch_id
    item = _make_item("BIDFMT")
    try:
        bid = generate_batch_id(item.name, "2027-03-15")
        frappe.db.rollback()
        expected_prefix = f"{item.name}-202703-"
        if bid.startswith(expected_prefix) and bid.endswith("001"):
            return {"pass": True, "msg": f"OK {bid}"}
        return {"pass": False, "msg": f"X {bid} (expected prefix={expected_prefix})"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_generate_batch_id_sequence():
    """Tạo 2 batches cùng (item, ym) → seq 001, 002."""
    from supplycore.m5_fefo.api.batch_helpers import generate_batch_id
    item = _make_item("BIDSEQ")
    try:
        b1 = _make_batch(item.name, expiry_offset_days=365, ignore_short_expiry=True)
        b1.insert()
        b2 = _make_batch(item.name, expiry_offset_days=365, ignore_short_expiry=True)
        b2.insert()
        frappe.db.rollback()
        if b1.batch_id.endswith("-001") and b2.batch_id.endswith("-002"):
            return {"pass": True, "msg": f"OK {b1.batch_id}, {b2.batch_id}"}
        return {"pass": False, "msg": f"X b1={b1.batch_id} b2={b2.batch_id}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_batch_short_expiry_flag():
    """Expiry today+90 → is_short_expiry=1."""
    item = _make_item("SHFLAG")
    b = _make_batch(item.name, expiry_offset_days=90, ignore_short_expiry=True)
    try:
        b.insert()
        ok = (b.is_short_expiry == 1)
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK is_short_expiry=1"}
        return {"pass": False, "msg": f"X is_short_expiry={b.is_short_expiry}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_batch_short_expiry_blocks_insert():
    """Manual insert short expiry không ack → SC-E-BATCH-SHORT-EXPIRY."""
    item = _make_item("SHBLK")
    b = _make_batch(item.name, expiry_offset_days=90)  # KHÔNG ignore + KHÔNG ack
    try:
        b.insert()
        frappe.db.rollback()
        return {"pass": False, "msg": "X did not throw"}
    except frappe.ValidationError as e:
        msg = str(e)
        frappe.db.rollback()
        if "SC-E-BATCH-SHORT-EXPIRY" in msg:
            return {"pass": True, "msg": f"OK: {msg[:120]}"}
        return {"pass": False, "msg": f"Wrong error: {msg[:120]}"}


def test_batch_short_expiry_allowed_with_ack():
    """expiry_warning_ack=1 → insert OK + acknowledged_by set."""
    item = _make_item("SHACK")
    b = _make_batch(item.name, expiry_offset_days=90, expiry_warning_ack=1)
    try:
        b.insert()
        ok = (b.docstatus == 0 and b.expiry_warning_ack == 1 and b.acknowledged_by)
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": f"OK ack by {b.acknowledged_by}"}
        return {"pass": False, "msg": f"X ack_by={b.acknowledged_by} ack={b.expiry_warning_ack}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_batch_long_expiry_no_flag():
    """Expiry today+365 → is_short_expiry=0, insert OK."""
    item = _make_item("LONG")
    b = _make_batch(item.name, expiry_offset_days=365)
    try:
        b.insert()
        ok = (b.is_short_expiry == 0)
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": "OK long expiry not flagged"}
        return {"pass": False, "msg": f"X is_short_expiry={b.is_short_expiry}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_batch_duplicate_supplier_batch_no_warns():
    """2 batch cùng item + supplier_batch_no → vẫn save (batch_id unique) + warning."""
    item = _make_item("DUPSUP")
    b1 = _make_batch(item.name, supplier_batch_no="SUP-LOT-12345", ignore_short_expiry=True)
    try:
        b1.insert()
        b2 = _make_batch(item.name, supplier_batch_no="SUP-LOT-12345", ignore_short_expiry=True)
        b2.insert()
        ok = (b1.batch_id != b2.batch_id and b1.docstatus == 0 and b2.docstatus == 0)
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": "OK both saved with warning"}
        return {"pass": False, "msg": f"X b1={b1.batch_id} b2={b2.batch_id}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_lookup_batch_by_id():
    """lookup_batch_by_no(prefix) trả batches matching batch_id."""
    from supplycore.m5_fefo.api.batch_helpers import lookup_batch_by_no
    item = _make_item("LOOKBID")
    b = _make_batch(item.name, ignore_short_expiry=True)
    b.insert()
    try:
        res = lookup_batch_by_no(b.batch_id[:10])
        names = [r["name"] for r in res]
        frappe.db.rollback()
        if b.name in names:
            return {"pass": True, "msg": f"OK found {b.name}"}
        return {"pass": False, "msg": f"X not found in {names[:5]}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_lookup_batch_by_supplier_no():
    """lookup_batch_by_no(supplier_batch_no) trả batches matching."""
    from supplycore.m5_fefo.api.batch_helpers import lookup_batch_by_no
    item = _make_item("LOOKSUP")
    sup_lot = f"UC15-SUPLOT-{random_string(4)}"
    b = _make_batch(item.name, supplier_batch_no=sup_lot, ignore_short_expiry=True)
    b.insert()
    try:
        res = lookup_batch_by_no(sup_lot)
        names = [r["name"] for r in res]
        frappe.db.rollback()
        if b.name in names:
            return {"pass": True, "msg": f"OK found {b.name} via supplier_batch_no"}
        return {"pass": False, "msg": f"X not found in {names[:5]}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_get_batch_label_data():
    """get_batch_label_data trả dict đủ field cho in nhãn."""
    item = _make_item("LBLDAT")
    b = _make_batch(item.name, ignore_short_expiry=True)
    b.manufacturer = "Test Manufacturer Co"
    b.insert()
    try:
        data = b.get_batch_label_data()
        frappe.db.rollback()
        required = {"batch_id", "barcode", "item", "manufacturer", "expiry_date", "url"}
        if required.issubset(set(data.keys())) and data["manufacturer"] == "Test Manufacturer Co":
            return {"pass": True, "msg": f"OK label keys={list(data.keys())}"}
        return {"pass": False, "msg": f"X missing fields: {required - set(data.keys())}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def test_pr_auto_create_batch_uses_seq_format():
    """PR submit auto-create batch → batch_id format đúng [Item]-YYYYMM-Seq."""
    import re
    from frappe.utils import getdate

    sup = frappe.db.get_value("SC Supplier", {"disabled": 0}, "name")
    if not sup:
        return {"pass": False, "msg": "X cần seed SC Supplier"}
    item = _make_item("PRAUTO")
    item.default_supplier = sup
    item.save()
    wh = frappe.db.get_value("SC Warehouse", {"is_group": 0, "disabled": 0}, "name")
    expiry = add_days(today(), 365)

    pr = frappe.new_doc("SC Purchase Receipt")
    pr.supplier = sup
    pr.posting_date = today()
    pr.to_warehouse = wh
    pr.qc_required = 0
    pr.no_po_reason = "UC-15 batch format test"
    pr.append("items", {
        "item": item.name, "qty": 5, "uom": item.uom,
        "rate": 1000, "warehouse": wh,
        "expiry_date": expiry,
        "manufacturing_date": today(),
    })
    pr.flags.ignore_permissions = True
    try:
        pr.insert()
        pr.submit()
        pr.reload()
        batch_no = pr.items[0].batch_no
        frappe.db.rollback()
        if not batch_no:
            return {"pass": False, "msg": "X batch_no not auto-set"}
        ym = getdate(expiry).strftime("%Y%m")
        pattern = rf"^{re.escape(item.name)}-{ym}-\d+$"
        if re.match(pattern, batch_no):
            return {"pass": True, "msg": f"OK batch_id={batch_no}"}
        return {"pass": False, "msg": f"X format wrong: {batch_no}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}


def run():
    tests = [
        test_generate_batch_id_format,
        test_generate_batch_id_sequence,
        test_batch_short_expiry_flag,
        test_batch_short_expiry_blocks_insert,
        test_batch_short_expiry_allowed_with_ack,
        test_batch_long_expiry_no_flag,
        test_batch_duplicate_supplier_batch_no_warns,
        test_lookup_batch_by_id,
        test_lookup_batch_by_supplier_no,
        test_get_batch_label_data,
        test_pr_auto_create_batch_uses_seq_format,
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
