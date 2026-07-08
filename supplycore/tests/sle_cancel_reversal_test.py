"""Test SLE cancel double-reversal bugfix.

Bug: cancel routine của SC Purchase Receipt / SC Stock Entry / SC Stock
Reconciliation vừa post SLE đối ứng, vừa set is_cancelled=1 trên dòng gốc.
SCStockLedgerEntry.get_qty/get_available_qty SUM(qty_change) WHERE
is_cancelled=0 — loại dòng gốc (+qty) NHƯNG vẫn cộng dòng đối ứng (-qty)
→ đảo KÉP: nhập 50 rồi cancel → tồn -50 thay vì 0.

Fix: append-only — post đối ứng, KHÔNG set is_cancelled (mirror SC Delivery
Note._reverse_stock_ledger, đã sửa ở GĐ2).

Run individual: bench --site supplycore-miyano.local execute \
    supplycore.tests.sle_cancel_reversal_test.test_stock_entry_cancel_restores_stock
Run all:        bench --site supplycore-miyano.local execute \
    supplycore.tests.sle_cancel_reversal_test.run
"""

import frappe
from frappe.utils import today, add_days, random_string, flt


def _get_uom() -> str:
    uom = frappe.db.get_value("SC UOM", {}, "name")
    if not uom:
        frappe.throw("sle_cancel_reversal_test: cần seed SC UOM")
    return uom


def _pick_warehouse() -> str:
    rows = frappe.get_all("SC Warehouse", filters={"is_group": 0, "disabled": 0},
                           pluck="name", order_by="name", limit=1)
    if not rows:
        frappe.throw("sle_cancel_reversal_test: cần seed SC Warehouse")
    return rows[0]


def _make_item(suffix: str, has_batch_no=0):
    item = frappe.new_doc("SC Item")
    item.item_code = f"SLECR-{suffix}-{random_string(5)}"
    item.item_name = f"SLE cancel-reversal test {suffix}"
    item.uom = _get_uom()
    item.is_stock_item = 1
    item.has_batch_no = has_batch_no
    item.flags.ignore_permissions = True
    item.insert()
    return item


def _get_qty(item, warehouse):
    from supplycore.supplycore.doctype.sc_stock_ledger_entry.sc_stock_ledger_entry import SCStockLedgerEntry
    return SCStockLedgerEntry.get_qty(item, warehouse)


# ---------- Tests ----------

def test_stock_entry_cancel_restores_stock():
    """Material Receipt +50 → cancel → tồn phải về lại mức trước submit (0), KHÔNG âm."""
    wh = _pick_warehouse()
    item = _make_item("SE")
    before = _get_qty(item.name, wh)
    try:
        se = frappe.new_doc("SC Stock Entry")
        se.entry_type = "Material Receipt"
        se.posting_date = today()
        se.to_warehouse = wh
        se.append("items", {"item": item.name, "qty": 50, "uom": item.uom,
                             "valuation_rate": 1000})
        se.flags.ignore_permissions = True
        se.insert()
        se.submit()
        after_submit = _get_qty(item.name, wh)

        se.cancel()
        after_cancel = _get_qty(item.name, wh)

        frappe.db.rollback()

        if abs(after_submit - (before + 50)) > 0.01:
            return {"pass": False, "msg": f"X after_submit={after_submit} expected {before + 50}"}
        if abs(after_cancel - before) > 0.01:
            return {"pass": False, "msg": f"X after_cancel={after_cancel} expected {before} "
                                           f"(double-reversal bug if negative)"}
        return {"pass": True, "msg": f"OK before={before} after_submit={after_submit} "
                                      f"after_cancel={after_cancel}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:200]}"}


def test_purchase_receipt_cancel_restores_stock():
    """PR inbound +50 → cancel → tồn phải về lại mức trước submit (0), KHÔNG âm."""
    wh = _pick_warehouse()
    supplier = frappe.db.get_value("SC Supplier", {}, "name")
    if not supplier:
        return {"pass": False, "msg": "SKIP: cần seed SC Supplier"}
    item = _make_item("PR")
    before = _get_qty(item.name, wh)
    try:
        pr = frappe.new_doc("SC Purchase Receipt")
        pr.supplier = supplier
        pr.posting_date = today()
        pr.to_warehouse = wh
        pr.qc_required = 0
        pr.no_po_reason = "sle_cancel_reversal_test"
        pr.append("items", {
            "item": item.name, "qty": 50, "uom": item.uom,
            "rate": 1000, "warehouse": wh,
            "expiry_date": add_days(today(), 365),
            "manufacturing_date": today(),
        })
        pr.flags.ignore_permissions = True
        pr.insert()
        pr.submit()
        after_submit = _get_qty(item.name, wh)

        pr.cancel()
        after_cancel = _get_qty(item.name, wh)

        frappe.db.rollback()

        if abs(after_submit - (before + 50)) > 0.01:
            return {"pass": False, "msg": f"X after_submit={after_submit} expected {before + 50}"}
        if abs(after_cancel - before) > 0.01:
            return {"pass": False, "msg": f"X after_cancel={after_cancel} expected {before} "
                                           f"(double-reversal bug if negative)"}
        return {"pass": True, "msg": f"OK before={before} after_submit={after_submit} "
                                      f"after_cancel={after_cancel}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:200]}"}


def test_stock_reconciliation_cancel_restores():
    """Seed 50 → SR đếm được 60 (+10 diff) → cancel SR → tồn trả về 50 (KHÔNG âm/lệch)."""
    from supplycore.supplycore.doctype.sc_stock_ledger_entry.sc_stock_ledger_entry import SCStockLedgerEntry

    wh = _pick_warehouse()
    item = _make_item("SR")
    before = _get_qty(item.name, wh)

    SCStockLedgerEntry.post(
        item=item.name, warehouse=wh, qty_change=50,
        voucher_type="Manual", voucher_no=f"SLECR-SEED-{random_string(6)}",
        posting_date=today(), valuation_rate=1000,
    )
    after_seed = _get_qty(item.name, wh)

    try:
        sr = frappe.new_doc("SC Stock Reconciliation")
        sr.posting_date = today()
        sr.warehouse = wh
        sr.append("items", {
            "item": item.name, "uom": item.uom,
            "actual_qty": 60, "valuation_rate": 1000,
            "reason": "Counting Error",
        })
        sr.flags.ignore_permissions = True
        sr.insert()
        sr.submit()
        after_submit = _get_qty(item.name, wh)

        sr.cancel()
        after_cancel = _get_qty(item.name, wh)

        frappe.db.rollback()

        if abs(after_seed - (before + 50)) > 0.01:
            return {"pass": False, "msg": f"X after_seed={after_seed} expected {before + 50}"}
        if abs(after_submit - (before + 60)) > 0.01:
            return {"pass": False, "msg": f"X after_submit={after_submit} expected {before + 60}"}
        if abs(after_cancel - (before + 50)) > 0.01:
            return {"pass": False, "msg": f"X after_cancel={after_cancel} expected {before + 50} "
                                           f"(double-reversal bug if it drifts by the diff again)"}
        return {"pass": True, "msg": f"OK before={before} after_seed={after_seed} "
                                      f"after_submit={after_submit} after_cancel={after_cancel}"}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:200]}"}


def run():
    tests = [
        test_stock_entry_cancel_restores_stock,
        test_purchase_receipt_cancel_restores_stock,
        test_stock_reconciliation_cancel_restores,
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
