"""Smoke test M8 — SC PO → SC PR → SC PI 3-way match → SC PE → GL Entry."""

import frappe
from frappe.utils import today, add_days, flt, random_string


def run():
    supplier = frappe.db.get_value("SC Supplier", {"supplier_name": "Công ty CP Dược Hậu Giang"}, "name")
    item_code = "VTTH-MASK-3PLY"  # ít data hơn → ít FEFO conflict
    warehouse = "Kho Vật tư tiêu hao"
    if not all([supplier, frappe.db.exists("SC Item", item_code), frappe.db.exists("SC Warehouse", warehouse)]):
        return {"status": "skip", "reason": "Cần seed master data"}

    # Verify CoA seeded
    if not frappe.db.exists("SC GL Account", "152"):
        return {"status": "skip", "reason": "Cần seed GL Account (chạy seed_master_data)"}

    item_uom = frappe.db.get_value("SC Item", item_code, "uom")
    results = []

    # Cleanup test docs
    inv_no = "DHG-INV-M8-SMOKE-2026"
    for n in frappe.get_all("SC Payment Entry", filters={"remarks": "M8-SMOKE"}, fields=["name"]):
        d = frappe.get_doc("SC Payment Entry", n.name)
        if d.docstatus == 1: d.cancel()
        frappe.delete_doc("SC Payment Entry", n.name, force=True, ignore_permissions=True)
    for n in frappe.get_all("SC Purchase Invoice", filters={"supplier_invoice_no": inv_no}, fields=["name"]):
        d = frappe.get_doc("SC Purchase Invoice", n.name)
        if d.docstatus == 1: d.cancel()
        frappe.delete_doc("SC Purchase Invoice", n.name, force=True, ignore_permissions=True)
    frappe.db.commit()

    # 1. Tạo SC PO test
    po = frappe.new_doc("SC Purchase Order")
    po.supplier = supplier
    po.transaction_date = today()
    po.schedule_date = add_days(today(), 7)
    po.to_warehouse = warehouse
    po.append("items", {"item": item_code, "qty": 100, "uom": item_uom,
                          "rate": 1500, "schedule_date": add_days(today(), 7)})
    po.flags.ignore_permissions = True
    po.insert(); po.submit(); po.reload()
    results.append({"step": "PO submitted", "po": po.name, "grand_total": float(po.grand_total)})

    # 2. Tạo SC PR (qty đầy đủ)
    pr = frappe.new_doc("SC Purchase Receipt")
    pr.supplier = supplier
    pr.purchase_order = po.name
    pr.posting_date = today()
    pr.to_warehouse = warehouse
    pr.qc_required = 0  # bypass QC cho smoke
    pr.append("items", {"item": item_code, "qty": 100, "uom": item_uom,
                          "rate": 1500, "warehouse": warehouse,
                          "expiry_date": add_days(today(), 365),
                          "supplier_batch_no": f"DHG-{random_string(4)}"})
    pr.flags.ignore_permissions = True
    pr.insert(); pr.submit(); pr.reload()
    results.append({"step": "PR submitted", "pr": pr.name, "total_value": float(pr.total_value)})

    # 3. Tạo SC PI matched
    pi = frappe.new_doc("SC Purchase Invoice")
    pi.supplier = supplier
    pi.supplier_invoice_no = inv_no
    pi.invoice_date = today()
    pi.purchase_order = po.name
    pi.purchase_receipt = pr.name
    pi.vat_rate = 10
    pi.append("items", {"item": item_code, "qty": 100, "uom": item_uom, "rate": 1500})
    pi.flags.ignore_permissions = True
    pi.insert(); pi.reload()
    results.append({"step": "PI Match check", "match": pi.three_way_match_status,
                    "approval_by": pi.approval_required_by,
                    "subtotal": float(pi.subtotal), "vat": float(pi.vat_amount),
                    "grand_total": float(pi.grand_total)})
    assert pi.three_way_match_status == "Match", f"Match expected but got {pi.three_way_match_status}"

    pi.submit(); pi.reload()
    results.append({"step": "PI submitted", "status": pi.status,
                    "outstanding": float(pi.outstanding_amount)})

    # Verify GL Entries
    gl_count = frappe.db.count("SC GL Entry",
        {"voucher_type": "SC Purchase Invoice", "voucher_no": pi.name, "is_cancelled": 0})
    gl_balanced = frappe.db.sql("""
        SELECT COALESCE(SUM(debit), 0) - COALESCE(SUM(credit), 0)
        FROM `tabSC GL Entry`
        WHERE voucher_type = 'SC Purchase Invoice' AND voucher_no = %s AND is_cancelled = 0
    """, pi.name)[0][0]
    results.append({"step": "PI GL Entries", "count": gl_count, "balance": float(gl_balanced or 0)})
    assert flt(gl_balanced) == 0, f"GL không cân bằng: {gl_balanced}"
    assert gl_count >= 3, f"Phải có ≥3 GL entries (152, 1331, 331), got {gl_count}"

    # 4. Test 3-way mismatch via API
    from supplycore.api import accounting
    match_api = accounting.three_way_match(purchase_invoice=pi.name)
    results.append({"step": "API three_way_match", **match_api})

    # 5. Test mismatch: PI mới với rate cao hơn (vượt tolerance)
    pi_mismatch = frappe.new_doc("SC Purchase Invoice")
    pi_mismatch.supplier = supplier
    pi_mismatch.supplier_invoice_no = f"DHG-MM-{random_string(4)}"
    pi_mismatch.invoice_date = today()
    pi_mismatch.purchase_order = po.name
    pi_mismatch.vat_rate = 10
    # Giá tăng 3% — vượt tolerance 1%
    pi_mismatch.append("items", {"item": item_code, "qty": 100, "uom": item_uom, "rate": 1545})
    pi_mismatch.flags.ignore_permissions = True
    pi_mismatch.insert(); pi_mismatch.reload()
    results.append({"step": "PI Mismatch check", "match": pi_mismatch.three_way_match_status,
                    "approval_by": pi_mismatch.approval_required_by,
                    "variance": float(pi_mismatch.match_variance_amount)})
    assert pi_mismatch.three_way_match_status == "Mismatch"
    assert pi_mismatch.approval_required_by == "Executive"
    # Cleanup
    frappe.delete_doc("SC Purchase Invoice", pi_mismatch.name, force=True, ignore_permissions=True)

    # 6. Test hard cap +5%: PI rate gấp 1.1
    pi_overcap = frappe.new_doc("SC Purchase Invoice")
    pi_overcap.supplier = supplier
    pi_overcap.supplier_invoice_no = f"DHG-OC-{random_string(4)}"
    pi_overcap.invoice_date = today()
    pi_overcap.purchase_order = po.name
    pi_overcap.append("items", {"item": item_code, "qty": 100, "uom": item_uom, "rate": 1700})
    pi_overcap.flags.ignore_permissions = True
    threw = False
    try:
        pi_overcap.insert()
    except frappe.ValidationError as e:
        threw = "THREE_WAY_MISMATCH" in str(e) or "vượt PO" in str(e)
    results.append({"step": "Hard cap +5% throw", "threw": threw})

    # 7. Tạo SC Payment Entry thanh toán full
    pe = frappe.new_doc("SC Payment Entry")
    pe.supplier = supplier
    pe.payment_date = today()
    pe.payment_method = "Bank Transfer"
    pe.bank_account = "Vietcombank 0123456"
    pe.reference_no = f"BANK-{random_string(6)}"
    pe.amount = flt(pi.outstanding_amount)
    pe.remarks = "M8-SMOKE"
    pe.append("references", {
        "purchase_invoice": pi.name,
        "allocated_amount": flt(pi.outstanding_amount),
    })
    pe.flags.ignore_permissions = True
    pe.insert(); pe.reload()
    results.append({"step": "PE created", "pe": pe.name, "amount": float(pe.amount),
                    "approval_level": pe.approval_level})
    expected_lvl = "Manager" if flt(pi.grand_total) < 50_000_000 else "Executive"
    assert pe.approval_level == expected_lvl, f"Approval level sai: {pe.approval_level}"

    pe.submit(); pi.reload()
    results.append({"step": "PE submitted", "pi_status": pi.status,
                    "pi_outstanding": float(pi.outstanding_amount),
                    "pi_paid": float(pi.paid_amount)})
    assert pi.status == "Paid"
    assert flt(pi.outstanding_amount) <= 0.01

    # 8. supplier_balance API
    bal = accounting.supplier_balance(supplier)
    results.append({"step": "supplier_balance API", **bal})

    # 9. Trial balance check — tất cả GL Entry cân bằng
    total_balance = frappe.db.sql("""
        SELECT COALESCE(SUM(debit), 0) - COALESCE(SUM(credit), 0)
        FROM `tabSC GL Entry` WHERE is_cancelled = 0
    """)[0][0]
    results.append({"step": "Trial balance (Σ Nợ − Σ Có)", "balance": float(total_balance or 0)})
    assert abs(flt(total_balance)) < 1, f"Sổ cái không cân: {total_balance}"

    return {"status": "ok", "results": results}
