"""Test GĐ MVL — SC Purchase Receipt 2 bước (Tiếp nhận → Xác nhận nhập kho).

T1 submit -> chưa vào tồn khả dụng, receipt_status='Đã tiếp nhận', chưa có SLE.
T2 QC Pass + xác nhận -> SLE post, tồn tăng đúng, ngày ghi sổ = ngày xác nhận.
T3 xác nhận 2 lần -> chỉ ghi sổ 1 lần (idempotent).
T4 QC chưa Pass -> xác nhận bị chặn.
T5 role không có quyền -> chặn (PermissionError).
T6 huỷ phiếu đã nhập kho -> đảo SLE; huỷ khi đã tiêu thụ -> chặn.
T8 liên phân hệ: hàng chỉ mới tiếp nhận -> portal gọi hàng bị chặn hết tồn; sau xác nhận -> gọi được.

Run: bench --site supplycore-miyano.local execute supplycore.tests.mvl_pr_2step_test.run
"""

import frappe
from frappe.utils import today, add_days, flt, random_string


def _avail(item, wh=None, batch=None):
    from supplycore.supplycore.doctype.sc_stock_ledger_entry.sc_stock_ledger_entry import SCStockLedgerEntry
    return flt(SCStockLedgerEntry.get_available_qty(item, wh, batch))


def _supplier():
    name = frappe.db.get_value("SC Supplier", {}, "name")
    if name:
        return name
    d = frappe.new_doc("SC Supplier"); d.supplier_name = "PR2STEP NCC"; d.flags.ignore_permissions = True; d.insert()
    return d.name


def _warehouse():
    wh = frappe.db.get_value("SC Warehouse", {"is_group": 0, "disabled": 0}, "name")
    return wh


def _uom():
    return frappe.db.get_value("SC UOM", {}, "name")


def _item(suffix):
    code = f"PR2S-{suffix}-{random_string(4)}"
    d = frappe.new_doc("SC Item")
    d.item_code = code; d.item_name = f"PR2step {suffix}"; d.uom = _uom()
    d.is_stock_item = 1; d.has_batch_no = 1
    d.flags.ignore_permissions = True; d.insert()
    return code


def _make_pr(item, qty=50, qc_required=1):
    pr = frappe.new_doc("SC Purchase Receipt")
    pr.supplier = _supplier()
    pr.posting_date = today()
    pr.to_warehouse = _warehouse()
    pr.qc_required = qc_required
    pr.no_po_reason = "Test 2 bước - nhận không qua PO"
    pr.append("items", {
        "item": item, "qty": qty, "uom": _uom(), "rate": 1000,
        "warehouse": _warehouse(), "expiry_date": add_days(today(), 365),
        "manufacturing_date": today(), "supplier_batch_no": f"LOT-{random_string(4)}",
    })
    pr.flags.ignore_permissions = True
    pr.insert(); pr.submit(); pr.reload()
    return pr


def _pass_qc(pr):
    for qi in frappe.get_all("SC Quality Inspection", {"purchase_receipt": pr.name}, pluck="name"):
        d = frappe.get_doc("SC Quality Inspection", qi)
        for r in d.readings:
            r.status = "Accepted"
        d.overall_status = "Accepted"; d.action_taken = "Accept"
        d.flags.ignore_permissions = True
        d.save(ignore_permissions=True); d.submit()
    pr.reload()


def test_T1_receive_not_in_stock():
    try:
        item = _item("T1")
        before = _avail(item)
        pr = _make_pr(item, 50)
        sle = frappe.db.exists("SC Stock Ledger Entry", {"voucher_type": "SC Purchase Receipt", "voucher_no": pr.name})
        ok = (pr.receipt_status == "Đã tiếp nhận" and not sle and _avail(item) == before)
        return {"pass": ok, "msg": f"OK tiếp nhận: status={pr.receipt_status}, SLE={bool(sle)}, avail={_avail(item)}" if ok
                else f"X status={pr.receipt_status} SLE={bool(sle)} avail={_avail(item)}"}
    finally:
        frappe.db.rollback()


def test_T2_confirm_posts_stock():
    try:
        item = _item("T2")
        pr = _make_pr(item, 50)
        _pass_qc(pr)
        res = pr.confirm_warehouse_in()
        pr.reload()
        avail = _avail(item)
        sle_pd = frappe.db.get_value("SC Stock Ledger Entry",
            {"voucher_type": "SC Purchase Receipt", "voucher_no": pr.name}, "posting_date")
        ok = (pr.receipt_status == "Đã nhập kho" and avail == 50
              and str(sle_pd) == str(today()) and pr.confirmed_by and pr.warehouse_in_date)
        return {"pass": ok, "msg": f"OK nhập kho: avail={avail}, SLE posting={sle_pd}, confirmed_by={pr.confirmed_by}" if ok
                else f"X status={pr.receipt_status} avail={avail} sle_pd={sle_pd}"}
    finally:
        frappe.db.rollback()


def test_T3_confirm_idempotent():
    try:
        item = _item("T3")
        pr = _make_pr(item, 40); _pass_qc(pr)
        pr.confirm_warehouse_in(); pr.reload()
        try:
            pr.confirm_warehouse_in()
            return {"pass": False, "msg": "X xác nhận lần 2 không bị chặn"}
        except frappe.ValidationError:
            pass
        cnt = frappe.db.count("SC Stock Ledger Entry",
            {"voucher_type": "SC Purchase Receipt", "voucher_no": pr.name})
        ok = (cnt == 1 and _avail(item) == 40)
        return {"pass": ok, "msg": f"OK idempotent: {cnt} SLE, avail={_avail(item)}" if ok else f"X {cnt} SLE avail={_avail(item)}"}
    finally:
        frappe.db.rollback()


def test_T4_confirm_blocked_before_qc():
    try:
        item = _item("T4")
        pr = _make_pr(item, 30)  # chưa QC
        try:
            pr.confirm_warehouse_in()
            return {"pass": False, "msg": "X xác nhận được khi chưa QC Pass"}
        except frappe.ValidationError as e:
            ok = "QC" in str(e)
            return {"pass": ok, "msg": "OK chặn xác nhận khi QC chưa Pass" if ok else f"X {str(e)[:120]}"}
    finally:
        frappe.db.rollback()


def test_T5_role_denied():
    orig = frappe.session.user
    try:
        item = _item("T5")
        pr = _make_pr(item, 20); _pass_qc(pr)
        # user portal (không có role thủ kho/quản lý)
        email = frappe.db.get_value("SC Customer", {"tax_code": "UITESTA01"}, "portal_user") or "ui.custa@sc.local"
        frappe.set_user(email)
        try:
            pr.confirm_warehouse_in()
            frappe.set_user(orig)
            return {"pass": False, "msg": "X user không quyền vẫn xác nhận được"}
        except frappe.PermissionError:
            return {"pass": True, "msg": "OK chặn role không có quyền (PermissionError)"}
    finally:
        frappe.set_user(orig)
        frappe.db.rollback()


def test_T6_cancel_reverses():
    try:
        item = _item("T6")
        pr = _make_pr(item, 25); _pass_qc(pr); pr.confirm_warehouse_in(); pr.reload()
        assert _avail(item) == 25
        pr.cancel()
        ok = _avail(item) == 0
        return {"pass": ok, "msg": f"OK huỷ đảo SLE, avail={_avail(item)}" if ok else f"X avail={_avail(item)}"}
    finally:
        frappe.db.rollback()


def test_T8_cross_subsystem_sales_block():
    orig = frappe.session.user
    try:
        frappe.db.set_single_value("SupplyCore Settings", "block_order_on_insufficient_stock", 1)
        frappe.db.set_single_value("SupplyCore Settings", "credit_check_enabled", 0)
        # item mới, đưa vào HĐ khung của KH A
        cust = frappe.db.get_value("SC Customer", {"tax_code": "UITESTA01"}, "name")
        email = frappe.db.get_value("SC Customer", cust, "portal_user")
        item = _item("T8")
        sfc = frappe.new_doc("SC Sales Framework Contract")
        sfc.customer = cust; sfc.valid_from = today(); sfc.valid_to = add_days(today(), 365)
        sfc.append("items", {"item": item, "uom": _uom(), "contract_qty": 100, "unit_price": 1000})
        sfc.flags.ignore_permissions = True; sfc.insert(); sfc.submit()
        # PR tiếp nhận (CHƯA xác nhận) -> tồn khả dụng vẫn 0
        pr = _make_pr(item, 50); _pass_qc(pr)
        from supplycore.api.portal import portal_order_place
        frappe.set_user(email)
        blocked = False
        try:
            portal_order_place(sfc.name, [{"item": item, "qty": 5}])
        except frappe.ValidationError as e:
            blocked = "BRU-INV-002" in str(e)
        frappe.set_user(orig)
        if not blocked:
            return {"pass": False, "msg": "X hàng chưa nhập kho nhưng KH gọi được"}
        # Xác nhận nhập kho -> giờ gọi được
        pr.confirm_warehouse_in()
        frappe.set_user(email)
        res = portal_order_place(sfc.name, [{"item": item, "qty": 5}])
        frappe.set_user(orig)
        ok = bool(res.get("order"))
        return {"pass": ok, "msg": "OK chờ QC->chặn hết tồn; xác nhận nhập kho->gọi được" if ok
                else f"X sau nhập kho vẫn không gọi được: {res}"}
    finally:
        frappe.set_user(orig)
        frappe.db.rollback()


def test_T10_partial_pass_confirm():
    """QC Partial Pass (1 đạt, 1 từ chối) -> vẫn xác nhận nhập kho được; dòng ĐẠT
    vào tồn khả dụng, dòng HỎNG bị cách ly (không khả dụng) + có phiếu trả NCC."""
    try:
        item_ok = _item("T10OK"); item_bad = _item("T10BAD")
        pr = frappe.new_doc("SC Purchase Receipt")
        pr.supplier = _supplier(); pr.posting_date = today(); pr.to_warehouse = _warehouse()
        pr.qc_required = 1; pr.no_po_reason = "Test partial"
        for it in (item_ok, item_bad):
            pr.append("items", {"item": it, "qty": 10, "uom": _uom(), "rate": 1000,
                "warehouse": _warehouse(), "expiry_date": add_days(today(), 365),
                "manufacturing_date": today(), "supplier_batch_no": f"L-{random_string(4)}"})
        pr.flags.ignore_permissions = True; pr.insert(); pr.submit(); pr.reload()
        # QC: item_ok Accepted, item_bad Rejected
        for qi in frappe.get_all("SC Quality Inspection", {"purchase_receipt": pr.name}, ["name", "item"]):
            d = frappe.get_doc("SC Quality Inspection", qi.name)
            acc = qi.item == item_ok
            for r in d.readings:
                r.status = "Accepted" if acc else "Rejected"
            d.overall_status = "Accepted" if acc else "Rejected"
            d.action_taken = "Accept" if acc else "Return to Supplier"
            d.failure_reason = None if acc else "Hỏng bao bì"
            d.flags.ignore_permissions = True; d.save(ignore_permissions=True); d.submit()
        pr.reload()
        if pr.qc_status != "Partial Pass":
            return {"pass": False, "msg": f"X qc_status={pr.qc_status} (kỳ vọng Partial Pass)"}
        pr.confirm_warehouse_in(); pr.reload()
        ok_avail = _avail(item_ok)      # đạt -> khả dụng
        bad_avail = _avail(item_bad)    # hỏng -> cách ly (0)
        ret = pr.find_return_pr().get("return_pr")
        ok = (pr.receipt_status == "Đã nhập kho" and ok_avail == 10 and bad_avail == 0 and ret)
        return {"pass": ok, "msg": f"OK Partial: đạt avail={ok_avail}, hỏng avail={bad_avail} (cách ly), trả NCC={ret}" if ok
                else f"X status={pr.receipt_status} ok={ok_avail} bad={bad_avail} ret={ret}"}
    finally:
        frappe.db.rollback()


def test_T11_invoice_excludes_rejected():
    """PR Partial Pass -> hoá đơn mua CHỈ gồm dòng ĐẠT; dòng bị QC từ chối (đã trả
    NCC) KHÔNG có trong hoá đơn (không trả tiền hàng đã trả lại)."""
    from supplycore.m8_accounting.doctype.sc_purchase_invoice.sc_purchase_invoice import make_invoice_from_pr
    try:
        item_ok = _item("T11OK"); item_bad = _item("T11BAD")
        pr = frappe.new_doc("SC Purchase Receipt")
        pr.supplier = _supplier(); pr.posting_date = today(); pr.to_warehouse = _warehouse()
        pr.qc_required = 1; pr.no_po_reason = "Test invoice exclude"
        for it in (item_ok, item_bad):
            pr.append("items", {"item": it, "qty": 10, "uom": _uom(), "rate": 1000,
                "warehouse": _warehouse(), "expiry_date": add_days(today(), 365),
                "manufacturing_date": today(), "supplier_batch_no": f"L-{random_string(4)}"})
        pr.flags.ignore_permissions = True; pr.insert(); pr.submit(); pr.reload()
        for qi in frappe.get_all("SC Quality Inspection", {"purchase_receipt": pr.name}, ["name", "item"]):
            d = frappe.get_doc("SC Quality Inspection", qi.name)
            acc = qi.item == item_ok
            for r in d.readings:
                r.status = "Accepted" if acc else "Rejected"
            d.overall_status = "Accepted" if acc else "Rejected"
            d.action_taken = "Accept" if acc else "Return to Supplier"
            d.failure_reason = None if acc else "Hỏng"
            d.flags.ignore_permissions = True; d.save(ignore_permissions=True); d.submit()
        pr.reload(); pr.confirm_warehouse_in()
        pi_name = make_invoice_from_pr(pr.name)
        pi = frappe.get_doc("SC Purchase Invoice", pi_name)
        pi_items = [r.item for r in pi.items]
        ok = (item_ok in pi_items and item_bad not in pi_items and len(pi.items) == 1)
        return {"pass": ok, "msg": f"OK HĐ chỉ có dòng đạt: {pi_items}" if ok
                else f"X HĐ items={pi_items} (kỳ vọng chỉ [{item_ok}])"}
    finally:
        frappe.db.rollback()


TESTS = [test_T1_receive_not_in_stock, test_T2_confirm_posts_stock, test_T3_confirm_idempotent,
         test_T4_confirm_blocked_before_qc, test_T5_role_denied, test_T6_cancel_reverses,
         test_T8_cross_subsystem_sales_block, test_T10_partial_pass_confirm,
         test_T11_invoice_excludes_rejected]


def run():
    results = []; passed = 0
    for t in TESTS:
        try:
            r = t()
        except Exception as e:
            r = {"pass": False, "msg": f"EXCEPTION: {repr(e)[:200]}"}
        results.append(r)
        if r.get("pass"):
            passed += 1
        print(f"  {'✓' if r.get('pass') else '✗'} {t.__name__}: {r.get('msg')}")
    print(f"mvl_pr_2step_test: {passed}/{len(TESTS)}")
    return {"passed": passed, "total": len(TESTS), "results": results}
