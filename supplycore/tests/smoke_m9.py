"""Smoke test M9 — Inventory Count Sheet + Stock Reconciliation + GL adjustment."""

import frappe
from frappe.utils import today, add_days, flt, random_string


def run():
    item_code = "VTTH-MASK-3PLY"  # ít FEFO conflict
    warehouse = "Kho Vật tư tiêu hao"
    if not (frappe.db.exists("SC Item", item_code) and frappe.db.exists("SC Warehouse", warehouse)):
        return {"status": "skip", "reason": "Cần seed master data"}
    if not frappe.db.exists("SC GL Account", "152"):
        return {"status": "skip", "reason": "Cần seed GL Account"}

    item_uom = frappe.db.get_value("SC Item", item_code, "uom")
    results = []

    # Cleanup: clear ICS.stock_reconciliation links trước khi delete SR
    for n in frappe.get_all("SC Inventory Count Sheet", filters={"remarks": "M9-SMOKE"}, fields=["name"]):
        frappe.db.set_value("SC Inventory Count Sheet", n.name, "stock_reconciliation", None)
    frappe.db.commit()
    for n in frappe.get_all("SC Stock Reconciliation", filters={"remarks": "M9-SMOKE"}, fields=["name"]):
        d = frappe.get_doc("SC Stock Reconciliation", n.name)
        try:
            if d.docstatus == 1: d.cancel()
        except: pass
        try:
            frappe.delete_doc("SC Stock Reconciliation", n.name, force=True, ignore_permissions=True)
        except: pass
    for n in frappe.get_all("SC Inventory Count Sheet", filters={"remarks": "M9-SMOKE"}, fields=["name", "stock_reconciliation"]):
        if n.stock_reconciliation:
            frappe.db.set_value("SC Inventory Count Sheet", n.name, "stock_reconciliation", None)
        d = frappe.get_doc("SC Inventory Count Sheet", n.name)
        if d.docstatus == 1: d.cancel()
        frappe.delete_doc("SC Inventory Count Sheet", n.name, force=True, ignore_permissions=True)
    frappe.db.commit()

    # 1. Tạo batch + receipt 100 đơn vị để có stock cho test
    batch = frappe.new_doc("SC Batch")
    batch.batch_id = f"{item_code}-M9-{random_string(5)}"
    batch.item = item_code
    batch.expiry_date = add_days(today(), 365)
    batch.flags.ignore_permissions = True
    batch.insert()

    se_in = frappe.new_doc("SC Stock Entry")
    se_in.entry_type = "Material Receipt"
    se_in.posting_date = today()
    se_in.to_warehouse = warehouse
    se_in.append("items", {"item": item_code, "qty": 100, "uom": item_uom,
                            "batch": batch.name, "valuation_rate": 1500})
    se_in.flags.ignore_permissions = True
    se_in.insert(); se_in.submit()
    results.append({"step": "Setup stock", "qty_in": 100, "rate": 1500})

    # Snapshot tồn kho hiện tại trước khi count
    sys_qty_before = flt(frappe.db.sql("""
        SELECT COALESCE(SUM(qty_change), 0) FROM `tabSC Stock Ledger Entry`
        WHERE item = %s AND warehouse = %s AND batch = %s AND is_cancelled = 0
    """, (item_code, warehouse, batch.name))[0][0])

    # 2. Tạo SC Inventory Count Sheet
    ics = frappe.new_doc("SC Inventory Count Sheet")
    ics.count_date = today()
    ics.warehouse = warehouse
    ics.count_scope = "All Items"
    ics.recount_threshold_pct = 5
    ics.remarks = "M9-SMOKE"
    ics.flags.ignore_permissions = True
    ics.insert()

    # Auto-load items
    res = ics.auto_load_items()
    ics.reload()
    results.append({"step": "ICS auto-load", "items": res["items_loaded"],
                    "total_items": ics.total_items})

    # Tìm row của batch test + nhập actual_qty thiếu hụt 5 đơn vị
    row_idx = None
    for i, r in enumerate(ics.items):
        if r.item == item_code and r.batch == batch.name:
            row_idx = i
            break
    assert row_idx is not None, "Không tìm thấy row test"

    # Nhập actual_qty: thiếu 5 đơn vị (system=100, actual=95)
    actual_qty = max(0, flt(ics.items[row_idx].system_qty) - 5)
    ics.items[row_idx].actual_qty = actual_qty
    ics.items[row_idx].reason = "Counting Error"
    # Đặt actual_qty = system_qty cho mọi row khác (không chênh)
    for i, r in enumerate(ics.items):
        if i != row_idx:
            r.actual_qty = flt(r.system_qty)
    ics.save(); ics.reload()

    target = ics.items[row_idx]
    results.append({"step": "Variance computed",
                    "system_qty": float(target.system_qty),
                    "actual_qty": float(target.actual_qty),
                    "difference": float(target.difference),
                    "variance_pct": float(target.variance_pct),
                    "needs_recount": bool(target.needs_recount),
                    "variance_value": float(target.variance_value),
                    "mismatched_items": ics.mismatched_items})

    # 3. Submit ICS → status=Counted
    ics.submit(); ics.reload()
    results.append({"step": "ICS submitted", "status": ics.status})
    assert ics.status == "Counted"

    # 4. Make Stock Reconciliation
    sr_name = ics.make_stock_reconciliation()
    ics.reload()
    sr = frappe.get_doc("SC Stock Reconciliation", sr_name)
    sr.remarks = "M9-SMOKE"
    sr.save(); sr.reload()
    results.append({"step": "SR created", "sr": sr_name,
                    "items": len(sr.items),
                    "total_diff_qty": float(sr.total_difference_qty),
                    "total_diff_value": float(sr.total_difference_value)})
    assert sr.total_difference_qty == -5  # thiếu 5
    assert sr.total_difference_value == -7500  # 5 × 1500

    # 5. Submit SR → SLE adjustment + GL post
    sr.submit(); ics.reload()
    results.append({"step": "SR submitted", "sr_status": sr.status, "ics_status": ics.status})
    assert ics.status == "Reconciled"

    # 6. Verify SLE adjustment
    sle_adj = frappe.db.sql("""
        SELECT qty_change FROM `tabSC Stock Ledger Entry`
        WHERE voucher_type = 'SC Stock Reconciliation' AND voucher_no = %s AND is_cancelled = 0
    """, sr.name, as_dict=True)
    results.append({"step": "SLE adjustment", "rows": len(sle_adj),
                    "qty_change": float(sle_adj[0].qty_change) if sle_adj else None})
    assert len(sle_adj) == 1
    assert sle_adj[0].qty_change == -5

    # Verify tồn kho mới
    new_qty = flt(frappe.db.sql("""
        SELECT COALESCE(SUM(qty_change), 0) FROM `tabSC Stock Ledger Entry`
        WHERE item = %s AND warehouse = %s AND batch = %s AND is_cancelled = 0
    """, (item_code, warehouse, batch.name))[0][0])
    results.append({"step": "Tồn kho sau adjust",
                    "before": sys_qty_before, "after": new_qty,
                    "match_actual": new_qty == 95})
    assert new_qty == 95, f"Tồn kho phải = 95, got {new_qty}"

    # 7. Verify GL Entry adjustment (thiếu → Dr 642 / Cr 152)
    gl = frappe.get_all("SC GL Entry",
        {"voucher_type": "SC Stock Reconciliation", "voucher_no": sr.name, "is_cancelled": 0},
        ["account", "debit", "credit"])
    gl_balance = sum(flt(g.debit) - flt(g.credit) for g in gl)
    results.append({"step": "GL adjustment",
                    "rows": len(gl),
                    "balance": float(gl_balance),
                    "entries": [{"acc": g.account, "dr": float(g.debit), "cr": float(g.credit)} for g in gl]})
    assert len(gl) == 2, "Phải có 2 GL entries"
    assert abs(gl_balance) < 0.01, f"GL không cân: {gl_balance}"
    # Verify Dr 642 (thiếu kho)
    debit_642 = sum(flt(g.debit) for g in gl if g.account == "642")
    credit_152 = sum(flt(g.credit) for g in gl if g.account == "152")
    assert debit_642 == 7500, f"Dr 642 phải = 7500, got {debit_642}"
    assert credit_152 == 7500, f"Cr 152 phải = 7500, got {credit_152}"

    return {"status": "ok", "results": results}
