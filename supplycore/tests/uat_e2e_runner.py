"""UAT E2E — execute từng section trong UAT_PROCEDURE.md, ghi issues."""

import frappe
from frappe.utils import today, add_days, flt, random_string

issues = []
def note(section, desc, severity="Medium", status="Open"):
    issues.append({"section": section, "desc": desc[:200],
                    "severity": severity, "status": status})


def run_all():
    ts = random_string(6)
    sup = frappe.db.get_value("SC Supplier", {"supplier_name": "Công ty CP Dược Hậu Giang"}, "name") \
          or frappe.get_all("SC Supplier", limit=1)[0].name
    item = "DTRC-NACL09"  # batch-tracked item để chạy đầy đủ FEFO section
    item_uom = frappe.db.get_value("SC Item", item, "uom")
    main_wh = "Kho Vật tư tiêu hao"
    dept_wh = frappe.db.get_value("SC Warehouse", {"warehouse_type": "Department", "disabled": 0}, "name") \
              or "Kho Khoa Nhi"

    print("\n=== Section 1: M1 Hợp đồng khung ===")
    # 1.1-1.2: Tạo + submit FC
    fc = frappe.new_doc("Framework Contract")
    fc.supplier = sup
    fc.contract_number = f"UAT-DOC-{ts}"
    fc.contract_date = add_days(today(), -60)
    fc.valid_from = add_days(today(), -30)
    fc.valid_to = add_days(today(), 365)
    fc.total_value = 100_000_000
    fc.append("items", {"item_code": item, "contract_qty": 1000,
                          "uom": item_uom, "unit_price": 1})
    fc.flags.ignore_permissions = True
    try:
        fc.insert(); fc.reload()
        fc.submit_for_review(); fc.reload()
        fc.approve_as_manager(comment="UAT"); fc.reload()
        if fc.approval_stage == "Executive Review":
            fc.approve_as_executive(comment="UAT"); fc.reload()
        fc.submit(); fc.reload()
        print(f"  ✓ FC {fc.name} submit, status={fc.status}")
        if fc.status != "Active":
            note("1.2", f"FC.status={fc.status} sau submit, expected Active", "High")
    except Exception as e:
        note("1.1", f"FC submit fail: {str(e)[:150]}", "Critical")
        return

    # 1.3 RO from FC
    try:
        ro = frappe.new_doc("Release Order")
        ro.framework_contract = fc.name
        ro.supplier = sup
        ro.release_date = today()
        ro.required_by = add_days(today(), 7)
        ro.append("items", {"item_code": item, "qty": 100, "uom": item_uom, "unit_price": 1})
        ro.flags.ignore_permissions = True
        ro.insert(); ro.submit()
        print(f"  ✓ RO {ro.name} submit")
    except Exception as e:
        note("1.3", f"RO submit fail: {str(e)[:150]}", "High")

    print("\n=== Section 2: M2 Kế hoạch + PO auto-suggest ===")
    mr = frappe.new_doc("SC Material Request")
    mr.request_type = "Purchase"
    mr.transaction_date = today()
    mr.schedule_date = add_days(today(), 7)
    mr.warehouse = main_wh
    mr.append("items", {"item": item, "qty": 50, "uom": item_uom,
                          "schedule_date": add_days(today(), 7)})
    mr.flags.ignore_permissions = True
    try:
        mr.insert(); mr.submit(); mr.reload()
        if mr.status == "Pending":
            mr.approve(); mr.reload()
        if mr.status != "Approved":
            note("2.1", f"MR.status={mr.status} sau approve, expected Approved", "Medium")
        print(f"  ✓ MR {mr.name} submit + approve, status={mr.status}")
    except Exception as e:
        note("2.1", f"MR submit fail: {str(e)[:150]}", "Critical")
        return

    # 2.2 create_purchase_orders
    try:
        out = mr.create_purchase_orders()
        if not out.get("created_pos"):
            note("2.2", f"create_purchase_orders không tạo PO: unmatched={out.get('unmatched_items')}", "High")
            return
        po_name = out["created_pos"][0]
        print(f"  ✓ PO {po_name} tạo từ MR (auto-suggest)")
    except Exception as e:
        note("2.2", f"create_purchase_orders fail: {str(e)[:150]}", "Critical")
        return

    # 2.3 Submit PO — simplified flow: submit → Sent to Supplier
    po = frappe.get_doc("SC Purchase Order", po_name)
    try:
        po.submit(); po.reload()
        if po.status != "Sent to Supplier":
            note("2.3", f"PO.status={po.status} sau submit, expected Sent to Supplier", "Medium")
        print(f"  ✓ PO submit, status={po.status}")
    except Exception as e:
        note("2.3", f"PO submit fail: {str(e)[:150]}", "Critical")

    print("\n=== Section 3: M3 PR auto-fetch từ PO ===")
    try:
        from supplycore.supplycore.doctype.sc_purchase_order.sc_purchase_order import make_pr_from_po
        pr_name = make_pr_from_po(po.name)
        pr = frappe.get_doc("SC Purchase Receipt", pr_name)
        print(f"  ✓ PR {pr_name} auto-fetch từ PO")
        # Nhập batch + expiry
        for r in pr.items:
            r.batch_no = ""  # auto-tạo khi submit
            r.manufacturing_date = today()
            r.expiry_date = add_days(today(), 365)
        pr.qc_required = 1
        pr.save()
    except Exception as e:
        note("3.1", f"make_pr_from_po fail: {str(e)[:150]}", "Critical")
        return

    # 3.3 Submit PR
    try:
        pr.submit(); pr.reload()
        # Verify auto SC Batch + SLE + QI
        batches = frappe.get_all("SC Batch", filters={"item": item},
                                   order_by="creation desc", limit=1)
        sle_count = frappe.db.count("SC Stock Ledger Entry",
                                       {"voucher_no": pr.name})
        qi_count = frappe.db.count("SC Quality Inspection",
                                      {"purchase_receipt": pr.name})
        po.reload()
        print(f"  ✓ PR submit. SLE={sle_count}, QI={qi_count}, latest batch={batches[0].name if batches else None}")
        print(f"    PO.received_qty totals={sum(flt(p.received_qty) for p in po.items)}, status={po.status}")
        if sle_count == 0:
            note("3.3", "PR submit không tạo SLE", "Critical")
        if pr.qc_required and qi_count == 0:
            note("3.3", "qc_required=1 nhưng không auto-tạo QI", "High")
    except Exception as e:
        note("3.3", f"PR submit fail: {str(e)[:150]}", "Critical")
        return

    print("\n=== Section 4: M3 QC submit Accepted ===")
    qis = frappe.get_all("SC Quality Inspection",
                           filters={"purchase_receipt": pr.name, "docstatus": 0},
                           fields=["name"])
    if not qis:
        note("4.1", "Không có QI draft sau PR submit", "High")
    else:
        try:
            qi = frappe.get_doc("SC Quality Inspection", qis[0].name)
            for r in qi.readings:
                r.status = "Accepted"
            qi.manual_inspection = 1
            qi.overall_status = "Accepted"
            qi.flags.ignore_permissions = True
            qi.save(); qi.submit(); qi.reload()
            pr.reload()
            print(f"  ✓ QI {qi.name} submit, overall_status={qi.overall_status}")
            print(f"    PR.qc_status={pr.qc_status} (PR options: Pass/Fail/Partial Pass)")
            if pr.qc_status != "Pass":
                note("4.2", f"PR.qc_status={pr.qc_status} sau QI Accepted, expected Pass", "Medium")
            if batches:
                bqc = frappe.db.get_value("SC Batch", batches[0].name, "qc_status")
                print(f"    Batch.qc_status={bqc} (Batch options: Accepted/Rejected/Conditional)")
                if bqc != "Accepted":
                    note("4.2", f"Batch.qc_status={bqc} sau QI Accepted, expected Accepted", "Medium")
        except Exception as e:
            note("4.2", f"QI submit fail: {str(e)[:150]}", "High")

    print("\n=== Section 5: SC Batch metadata + Putaway ===")
    if batches:
        b = frappe.get_doc("SC Batch", batches[0].name)
        print(f"  Batch {b.name}: mfg={b.manufacturing_date}, exp={b.expiry_date}, "
               f"qc={b.qc_status}, blocked={b.blocked}")
        if not b.expiry_date:
            note("5.1", f"Batch {b.name} thiếu expiry_date", "High")
        if b.blocked:
            note("5.1", f"Batch {b.name} bị blocked dù QI Accepted", "High")
        if not b.supplier:
            note("5.1", f"Batch {b.name} thiếu supplier link", "Low")
        # Test API scan_barcode (chỉ check không throw)
        try:
            from supplycore.api import wms
            r = wms.scan_barcode(barcode=item, context="receive") \
                if hasattr(wms, 'scan_barcode') else None
            print(f"  scan_barcode result: {bool(r)}")
        except Exception as e:
            note("5.3", f"scan_barcode API fail: {str(e)[:120]}", "Medium")

    print("\n=== Section 6: M5 FEFO ===")
    try:
        from supplycore.api.fefo import get_suggested_batches
        r = get_suggested_batches(item_code=item, warehouse=main_wh, qty=10)
        print(f"  FEFO: {len(r['batches'])} batches, fully_satisfied={r['fully_satisfied']}, "
               f"shortfall={r['shortfall']}")
        if r['batches']:
            # Verify ASC by expiry
            exps = [b['expiry_date'] for b in r['batches'] if b['expiry_date']]
            if exps != sorted(exps):
                note("6.2", f"FEFO không sắp xếp ASC theo expiry: {exps}", "High")
        else:
            note("6.2", "FEFO trả 0 batches dù vừa nhập kho", "Critical")
    except Exception as e:
        note("6.2", f"FEFO API fail: {str(e)[:150]}", "High")

    print("\n=== Section 7: M6 Transfer Request ===")
    try:
        tr = frappe.new_doc("SC Transfer Request")
        tr.from_warehouse = main_wh
        tr.to_warehouse = dept_wh
        tr.request_date = today()
        tr.transfer_type = "Replenishment"
        tr.required_by = add_days(today(), 3)
        tr.append("items", {"item": item, "requested_qty": 5, "uom": item_uom})
        tr.flags.ignore_permissions = True
        tr.insert(); tr.submit(); tr.reload()
        print(f"  ✓ TR {tr.name} submit, status={tr.status}")
    except Exception as e:
        note("7.1", f"TR submit fail: {str(e)[:150]}", "High")

    print("\n=== Section 8: M7 Dispensing + BHYT ===")
    try:
        pat = frappe.new_doc("SC Patient")
        pat.patient_id = f"BN-DOC-{ts}"
        pat.patient_name = "Nguyễn Văn UAT-DOC"
        pat.gender = "Nam"
        pat.bhyt_card_no = f"DN1{ts}"
        pat.bhyt_payment_rate = 80
        pat.flags.ignore_permissions = True
        pat.insert()

        dr = frappe.new_doc("SC Dispensing Request")
        dr.request_date = today()
        dr.purpose = "Patient-Specific"
        dr.department = "Khoa Nhi"
        dr.from_warehouse = main_wh
        dr.patient = pat.name
        dr.append("items", {"item": item, "requested_qty": 2, "uom": item_uom})
        dr.flags.ignore_permissions = True
        dr.insert(); dr.submit(); dr.reload()
        print(f"  ✓ DR {dr.name} submit, status={dr.status}")
    except Exception as e:
        note("8.2", f"DR submit fail: {str(e)[:150]}", "High")

    print("\n=== Section 10: M11 Dashboard ===")
    try:
        from supplycore.api.kpi import get_executive_dashboard
        kpi = get_executive_dashboard("this_month")
        ks = kpi["kpis"]
        print(f"  KPIs: stock_value={ks['stock_value']}, monthly_cost={ks['monthly_cost']}, "
               f"pending_pos={ks['pending_pos']}, expiring_soon={ks['expiring_soon']}")
        if not all(k in ks for k in ('stock_value', 'monthly_cost', 'ap_outstanding',
                                       'pending_pos', 'expiring_soon', 'low_stock_items')):
            note("10.1", "Dashboard thiếu KPI keys", "Medium")
    except Exception as e:
        note("10.1", f"Dashboard API fail: {str(e)[:150]}", "High")


    return issues
