"""E2E test — Order-to-Cash (M7 Sales), GĐ2 Task 10 (cuối).

Dựng toàn bộ chuỗi bán hàng MVL: Customer -> SFC (submit) -> SO (submit+approve)
-> DN (submit, SLE âm) -> Acceptance (submit) -> SI (submit, GL AR/511/632)
-> Receipt (submit, tất toán AR). Assert sổ kho + sổ cái khớp ở từng bước.

Run individual: bench --site supplycore-miyano.local execute supplycore.tests.sales_e2e_test.test_<name>
Run all:        bench --site supplycore-miyano.local execute supplycore.tests.sales_e2e_test.run
"""

import frappe
from frappe.utils import today, add_days, random_string, flt

from supplycore.supplycore.doctype.sc_stock_ledger_entry.sc_stock_ledger_entry import SCStockLedgerEntry
from supplycore.supplycore.doctype.sc_gl_entry.sc_gl_entry import SCGLEntry


# ---------------------------------------------------------------------------
# Helpers — dựng dữ liệu cách ly cho từng lần chạy test (random suffix)
# ---------------------------------------------------------------------------

def _make_uom(suffix):
    name = f"E2E-UOM-{suffix}"
    u = frappe.new_doc("SC UOM")
    u.uom_name = name
    u.abbreviation = name[:10]
    u.flags.ignore_permissions = True
    u.insert()
    return u.name


def _make_warehouse(suffix):
    w = frappe.new_doc("SC Warehouse")
    w.warehouse_name = f"E2E WH {suffix}"
    w.warehouse_code = f"E2E-{suffix}"
    w.flags.ignore_permissions = True
    w.insert()
    return w.name


def _make_item(suffix, uom):
    item = frappe.new_doc("SC Item")
    item.item_code = f"E2E-{suffix}"
    item.item_name = f"E2E test item {suffix}"
    item.uom = uom
    item.is_stock_item = 1
    item.has_batch_no = 1
    item.flags.ignore_permissions = True
    item.insert()
    return item


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


def _make_customer(suffix, credit_limit):
    c = frappe.new_doc("SC Customer")
    c.customer_name = f"KH E2E {suffix}"
    c.tax_code = f"TAX-E2E-{suffix}"
    c.credit_limit = flt(credit_limit)
    c.flags.ignore_permissions = True
    c.insert()
    return c


# ---------------------------------------------------------------------------
# Test
# ---------------------------------------------------------------------------

def test_full_o2c():
    """Chuỗi O2C đầy đủ: assert sổ kho + sổ cái đúng ở từng bước."""
    try:
        suffix = random_string(6)
        uom = _make_uom(suffix)
        wh = _make_warehouse(suffix)
        item = _make_item(suffix, uom)
        batch = _make_batch(item.name, add_days(today(), 200))
        customer = _make_customer(suffix, credit_limit=1_000_000)

        before_511 = SCGLEntry.get_balance("511")
        before_632 = SCGLEntry.get_balance("632")
        before_156 = SCGLEntry.get_balance("156")

        # ---- Seed inbound stock: 100 @ giá vốn 600 ----
        SCStockLedgerEntry.post(
            item=item.name, warehouse=wh, qty_change=100, valuation_rate=600,
            voucher_type="SC Purchase Receipt", voucher_no=f"E2E-IN-{suffix}",
            batch=batch.name,
        )
        stock_in = flt(SCStockLedgerEntry.get_available_qty(item.name, wh, batch.name))
        assert stock_in == 100, f"stock sau nhập kho = {stock_in} (kỳ vọng 100)"

        # ---- SFC: contract_qty=100, unit_price=1000 ----
        sfc = frappe.new_doc("SC Sales Framework Contract")
        sfc.customer = customer.name
        sfc.valid_from = today()
        sfc.valid_to = add_days(today(), 365)
        sfc.append("items", {
            "item": item.name, "uom": uom, "contract_qty": 100, "unit_price": 1000,
        })
        sfc.flags.ignore_permissions = True
        sfc.insert()
        sfc.submit()
        sfc.reload()
        assert sfc.status == "Hiệu lực", f"SFC status={sfc.status}"
        assert flt(sfc.items[0].remaining_qty) == 100, \
            f"SFC remaining sau submit = {sfc.items[0].remaining_qty} (kỳ vọng 100)"

        # ---- SO qty=30 -> submit -> approve ----
        so = frappe.new_doc("SC Sales Order")
        so.customer = customer.name
        so.framework_contract = sfc.name
        so.order_date = today()
        so.append("items", {"item": item.name, "uom": uom, "qty": 30})
        so.flags.ignore_permissions = True
        so.insert()
        so.submit()
        so.approve()
        so.reload()
        assert so.status == "Đã duyệt", f"SO status={so.status}"

        sfc.reload()
        assert flt(sfc.items[0].remaining_qty) == 70, \
            f"SFC remaining sau SO approve = {sfc.items[0].remaining_qty} (kỳ vọng 70)"

        # ---- DN (from_warehouse) -> submit ----
        dn = frappe.new_doc("SC Delivery Note")
        dn.sales_order = so.name
        dn.from_warehouse = wh
        dn.delivery_date = today()
        dn.append("items", {"item": item.name, "uom": uom, "qty": 30, "batch": batch.name})
        dn.flags.ignore_permissions = True
        dn.insert()
        dn.submit()
        dn.reload()

        stock_after_dn = flt(SCStockLedgerEntry.get_available_qty(item.name, wh, batch.name))
        assert stock_after_dn == 70, f"stock sau DN = {stock_after_dn} (kỳ vọng 70, 100-30)"
        so.reload()
        assert so.status == "Đã bàn giao", f"SO status sau DN = {so.status}"

        # ---- Acceptance -> submit ----
        ar = frappe.new_doc("SC Acceptance Record")
        ar.delivery_note = dn.name
        ar.acceptance_date = today()
        ar.accepted_by = "Nguyễn Văn A"
        ar.flags.ignore_permissions = True
        ar.insert()
        ar.submit()
        dn.reload()
        assert dn.status == "Đã nghiệm thu", f"DN status sau AR = {dn.status}"

        # ---- SI tax_rate=0 -> submit ----
        si = frappe.new_doc("SC Sales Invoice")
        si.customer = customer.name
        si.delivery_note = dn.name
        si.invoice_date = today()
        si.tax_rate = 0
        si.append("items", {"item": item.name, "qty": 30, "unit_price": 1000})
        si.flags.ignore_permissions = True
        si.insert()
        si.submit()
        si.reload()

        assert flt(si.grand_total) == 30000, f"SI grand_total={si.grand_total} (kỳ vọng 30000)"
        ar_balance = flt(SCGLEntry.get_balance("131", customer.name))
        assert ar_balance == 30000, f"131 (AR) party={customer.name} = {ar_balance} (kỳ vọng 30000)"

        after_511 = flt(SCGLEntry.get_balance("511"))
        # 511 (Doanh thu, Income) chỉ ghi Có -> balance (Nợ-Có) giảm đúng total_amount
        assert flt(after_511 - before_511) == -30000, \
            f"511 delta={after_511 - before_511} (kỳ vọng -30000, credit 30000)"

        after_632 = flt(SCGLEntry.get_balance("632"))
        assert flt(after_632 - before_632) == 18000, \
            f"632 (COGS) delta={after_632 - before_632} (kỳ vọng +18000 = 30*600)"

        after_156 = flt(SCGLEntry.get_balance("156"))
        assert flt(after_156 - before_156) == -18000, \
            f"156 (Hàng hóa) delta={after_156 - before_156} (kỳ vọng -18000)"

        dn.reload()
        assert dn.status == "Đã xuất HĐ", f"DN status sau SI = {dn.status}"

        # ---- Receipt amount=30000 -> submit ----
        sr = frappe.new_doc("SC Sales Receipt")
        sr.customer = customer.name
        sr.sales_invoice = si.name
        sr.receipt_date = today()
        sr.amount = 30000
        sr.mode = "Chuyển khoản"
        sr.flags.ignore_permissions = True
        sr.insert()
        sr.submit()
        si.reload()

        assert flt(si.outstanding_amount) == 0, f"SI outstanding={si.outstanding_amount} (kỳ vọng 0)"
        assert si.status == "Đã thu đủ", f"SI status={si.status}"
        ar_balance_final = flt(SCGLEntry.get_balance("131", customer.name))
        assert ar_balance_final == 0, f"131 (AR) sau thu tiền = {ar_balance_final} (kỳ vọng 0)"

        # ---- Assert cuối: SFC remaining 70, stock 70, AR 0 ----
        sfc.reload()
        final_remaining = flt(sfc.items[0].remaining_qty)
        final_stock = flt(SCStockLedgerEntry.get_available_qty(item.name, wh, batch.name))

        ok = (final_remaining == 70 and final_stock == 70 and ar_balance_final == 0)
        frappe.db.rollback()
        if ok:
            return {"pass": True, "msg": (
                f"OK O2C full chain: SFC.remaining={final_remaining}, stock={final_stock}, "
                f"131={ar_balance_final}, 511Δ={after_511-before_511}, 632Δ={after_632-before_632}"
            )}
        return {"pass": False, "msg": (
            f"X final SFC.remaining={final_remaining} stock={final_stock} AR={ar_balance_final}"
        )}
    except Exception as e:
        frappe.db.rollback()
        return {"pass": False, "msg": f"X threw: {str(e)[:300]}"}


def run():
    tests = [
        test_full_o2c,
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
