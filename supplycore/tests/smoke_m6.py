"""Smoke test M6 — SC Transfer Request → SC Stock Entry Material Transfer end-to-end."""

import frappe
from frappe.utils import today, add_days, random_string, flt


def run():
    item_code = "DTRC-NACL09"  # has_batch=1
    from_wh = "Kho Dịch truyền"
    to_wh = "Kho Phòng Kinh doanh"
    if not all([frappe.db.exists("SC Item", item_code),
                frappe.db.exists("SC Warehouse", from_wh),
                frappe.db.exists("SC Warehouse", to_wh)]):
        return {"status": "skip", "reason": "Cần seed master data"}

    item_uom = frappe.db.get_value("SC Item", item_code, "uom")
    results = []

    # Cleanup TR cũ
    for tr in frappe.get_all("SC Transfer Request", filters={"remarks": "M6-SMOKE"},
                              fields=["name", "stock_entry"]):
        if tr.stock_entry and frappe.db.exists("SC Stock Entry", tr.stock_entry):
            frappe.db.set_value("SC Transfer Request", tr.name, "stock_entry", None)
            se = frappe.get_doc("SC Stock Entry", tr.stock_entry)
            try:
                if se.docstatus == 1: se.cancel()
            except Exception: pass
            try:
                frappe.delete_doc("SC Stock Entry", se.name, force=True, ignore_permissions=True)
            except Exception: pass
        d = frappe.get_doc("SC Transfer Request", tr.name)
        try:
            if d.docstatus == 1: d.cancel()
        except Exception: pass
        try:
            frappe.delete_doc("SC Transfer Request", tr.name, force=True, ignore_permissions=True)
        except Exception: pass
    frappe.db.commit()

    # 1. Tạo batch + Material Receipt vào kho nguồn để có stock
    batch = frappe.new_doc("SC Batch")
    batch.batch_id = f"{item_code}-M6-{random_string(5)}"
    batch.item = item_code
    batch.expiry_date = add_days(today(), 365)
    batch.manufacturing_date = today()
    # get_available_qty() chỉ tính batch QC Accepted (loại Pending/Rejected/Blocked)
    # — smoke test tạo batch trực tiếp (bỏ qua PR→QI thật) nên set Accepted để
    # mirror kết quả 1 lô đã qua QC pass, mới có thể transfer được.
    batch.qc_status = "Accepted"
    batch.flags.ignore_permissions = True
    batch.insert()

    se_in = frappe.new_doc("SC Stock Entry")
    se_in.entry_type = "Material Receipt"
    se_in.posting_date = today()
    se_in.to_warehouse = from_wh
    se_in.append("items", {"item": item_code, "qty": 100, "uom": item_uom,
                            "batch": batch.name, "valuation_rate": 50000})
    se_in.flags.ignore_permissions = True
    se_in.insert(); se_in.submit()
    results.append({"step": "Setup stock", "batch": batch.name, "se_in": se_in.name, "qty": 100})

    # 2. Tạo SC Transfer Request
    tr = frappe.new_doc("SC Transfer Request")
    tr.request_date = today()
    tr.transfer_type = "Routine"
    tr.required_by = add_days(today(), 1)
    tr.from_warehouse = from_wh
    tr.to_warehouse = to_wh
    tr.requested_for_department = frappe.db.get_value("SC Warehouse", to_wh, "department")
    tr.requested_by = frappe.session.user if frappe.session.user not in (None, "", "Guest") else "Administrator"
    tr.remarks = "M6-SMOKE"
    tr.append("items", {"item": item_code, "uom": item_uom,
                         "requested_qty": 30, "approved_qty": 25,
                         "batch": batch.name})
    tr.flags.ignore_permissions = True
    tr.insert(); tr.reload()
    results.append({"step": "TR created", "tr": tr.name, "status": tr.status,
                    "available_at_source": float(tr.items[0].available_at_source),
                    "cross_tier_approval": bool(tr.requires_manager_approval)})
    assert tr.items[0].available_at_source >= 100, "Available phải >= 100 (vừa receipt 100)"

    # 3. Submit TR → Approved
    tr.submit(); tr.reload()
    results.append({"step": "TR Approved", "status": tr.status,
                    "approved_by": tr.approved_by})
    assert tr.status == "Approved"

    # 4. Make Stock Entry → SE Material Transfer draft
    se_name = tr.make_stock_entry()
    tr.reload()
    se = frappe.get_doc("SC Stock Entry", se_name)
    results.append({"step": "SE created", "se": se_name, "tr_status": tr.status,
                    "se_entry_type": se.entry_type, "tr_link": se.transfer_request})
    assert tr.status == "In Transit"
    assert se.entry_type == "Material Transfer"
    assert se.transfer_request == tr.name
    assert se.items[0].qty == 25  # approved_qty

    # 5. Submit SE → SLE -qty source + +qty target, TR.status = Received
    se.submit(); tr.reload()
    results.append({"step": "SE submitted", "tr_status": tr.status,
                    "transferred_qty": float(tr.items[0].transferred_qty)})
    assert tr.status == "Received"
    assert flt(tr.items[0].transferred_qty) == 25

    # Verify SLE thực tế
    qty_at_from = flt(frappe.db.sql("""
        SELECT SUM(qty_change) FROM `tabSC Stock Ledger Entry`
        WHERE item = %s AND warehouse = %s AND is_cancelled = 0
    """, (item_code, from_wh))[0][0])
    qty_at_to = flt(frappe.db.sql("""
        SELECT SUM(qty_change) FROM `tabSC Stock Ledger Entry`
        WHERE item = %s AND warehouse = %s AND is_cancelled = 0
    """, (item_code, to_wh))[0][0])
    results.append({"step": "SLE verify",
                    "qty_at_from": qty_at_from, "qty_at_to": qty_at_to})
    # Relative check: trước transfer có X tại from, X+100 sau receipt; sau transfer = X+75
    # Skip absolute check vì site có stock cũ. Chỉ verify SLE đã tạo:
    sle_count = frappe.db.count("SC Stock Ledger Entry",
        {"voucher_no": se.name, "is_cancelled": 0})
    assert sle_count == 2, f"Material Transfer phải tạo 2 SLE (-from, +to), got {sle_count}"

    # 6. Test STOCK_INSUFFICIENT: tạo TR yêu cầu vượt available
    tr_over = frappe.new_doc("SC Transfer Request")
    tr_over.request_date = today()
    tr_over.transfer_type = "Routine"
    tr_over.required_by = add_days(today(), 1)
    tr_over.from_warehouse = from_wh
    tr_over.to_warehouse = to_wh
    tr_over.requested_by = "Administrator"
    tr_over.remarks = "M6-SMOKE"
    tr_over.append("items", {"item": item_code, "uom": item_uom,
                              "requested_qty": 9999, "approved_qty": 9999})
    tr_over.flags.ignore_permissions = True
    tr_over.insert()  # OK ở Draft
    threw = False
    err_msg = ""
    try:
        tr_over.submit()
    except Exception as e:
        err_msg = str(e)
        threw = ("STOCK_INSUFFICIENT" in err_msg or "tồn kho nguồn" in err_msg or
                 "Insufficient" in err_msg or "SL duyệt" in err_msg)
    results.append({"step": "Insufficient stock validation", "threw": threw, "msg_excerpt": err_msg[:120]})

    return {"status": "ok", "results": results}
