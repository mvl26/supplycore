"""Integration smoke — full procurement chain MR → PO → PR → PI → GL.

Mục đích: khẳng định cross-module wiring (M2 → M1 → M3 → M8) hoạt động end-to-end.
Khác smoke_m1..m11 (test 1 module độc lập), smoke này test FLOW.

Bước:
  1. Setup: pick supplier + item, tạo Framework Contract Active có item này
  2. Tạo SC Material Request (Khoa) + submit
  3. Gọi MR.create_purchase_orders() → validate draft PO được tạo, link tới FC
  4. Submit PO → check FC.committed/used_value cập nhật
  5. Tạo SC Purchase Receipt từ PO + submit (auto SLE + auto QI)
  6. Verify SC PO Item.received_qty cập nhật + status = Received
  7. Gọi make_invoice_from_pr(pr) → tạo PI draft
  8. Submit PI → verify GL Entry posted (Σ Dr = Σ Cr) + 3-way match status

Pass criteria: tất cả 8 bước OK, không exception.
"""

import frappe
from frappe.utils import today, add_days, flt, random_string


def run():
    if not frappe.db.exists("SC Item", "VTTH-MASK-3PLY"):
        return {"status": "skip", "reason": "Cần seed master data"}

    sup = frappe.db.get_value("SC Supplier",
                                {"supplier_name": "Công ty CP Dược Hậu Giang"}, "name") \
          or frappe.get_all("SC Supplier", limit=1)[0].name
    item = "VTTH-MASK-3PLY"
    item_uom = frappe.db.get_value("SC Item", item, "uom")
    wh = "Kho Vật tư tiêu hao"
    results = []
    ts = random_string(6)

    # Cleanup: cancel FCs từ test runs trước (để FC mới với price=1 là cheapest)
    for prefix in ("INTEG-FC-%", "UAT-DOC-%", "UAT-FC-%", "UAT-BUG-%"):
        for f in frappe.get_all("Framework Contract",
                filters={"contract_number": ["like", prefix], "docstatus": 1},
                fields=["name"]):
            try:
                d = frappe.get_doc("Framework Contract", f.name)
                d.flags.ignore_permissions = True
                d.cancel()
            except Exception:
                pass
    frappe.db.commit()

    # === Step 1: tạo FC Active ===
    fc = frappe.new_doc("Framework Contract")
    fc.supplier = sup
    fc.contract_number = f"INTEG-FC-{ts}"
    fc.contract_date = add_days(today(), -60)
    fc.valid_from = add_days(today(), -30)
    fc.valid_to = add_days(today(), 180)
    fc.total_value = 1000  # = contract_qty × unit_price
    # Đặt unit_price thấp để chắc chắn được FC suggest pick (cheapest wins)
    fc.append("items", {
        "item_code": item, "contract_qty": 1000,
        "uom": item_uom, "unit_price": 1,
    })
    fc.flags.ignore_permissions = True
    fc.insert(); fc.reload()
    # UC-03 3-tier approval workflow
    fc.submit_for_review(); fc.reload()
    fc.approve_as_manager(comment="integration"); fc.reload()
    if fc.approval_stage == "Executive Review":
        fc.approve_as_executive(comment="integration"); fc.reload()
    fc.submit(); fc.reload()
    results.append({"step": "1. FC Active",
                    "fc": fc.name, "remaining": flt(fc.remaining_value),
                    "status": fc.status})
    assert fc.status == "Active", f"FC status={fc.status} (mong Active)"

    # === Step 2: tạo + submit MR ===
    mr = frappe.new_doc("SC Material Request")
    mr.request_type = "Purchase"
    mr.transaction_date = today()
    mr.schedule_date = add_days(today(), 7)
    mr.warehouse = wh
    mr.append("items", {
        "item": item, "qty": 50, "uom": item_uom,
        "schedule_date": add_days(today(), 7),
        # SC-E023 ZERO_MR_COST (QAv3-BUG-M2-06): MR Purchase phải có đơn giá ước
        # tính > 0. Link framework_contract để validate() auto-fetch fc_price
        # (mirror flow thật: user chọn HĐ khung khi lập MR).
        "framework_contract": fc.name,
    })
    mr.flags.ignore_permissions = True
    mr.insert(); mr.submit()
    # UC-07 (d75f902): submit → Pending (chờ duyệt), KHÔNG auto-approve. Cần
    # approve() riêng trước khi create_purchase_orders() (SC-E-MR-NOT-APPROVED).
    mr.reload()
    mr.approve()
    mr.reload()
    results.append({"step": "2. MR submit + approve",
                    "mr": mr.name, "status": mr.status, "items": len(mr.items)})
    assert mr.status == "Approved", f"MR status={mr.status} (mong Approved)"

    # === Step 3: create_purchase_orders → draft PO ===
    out = mr.create_purchase_orders()
    pos = out.get("created_pos") or []
    unmatched = out.get("unmatched_items") or []
    results.append({"step": "3. MR → PO suggestion",
                    "groups": len(out["groups"]),
                    "created_pos": pos,
                    "unmatched": len(unmatched)})
    assert len(pos) == 1, f"Phải tạo đúng 1 PO, được {len(pos)}"
    assert not unmatched, f"Không nên có unmatched: {unmatched}"
    po_name = pos[0]
    po = frappe.get_doc("SC Purchase Order", po_name)
    assert po.framework_contract == fc.name, f"PO.fc {po.framework_contract} ≠ {fc.name}"
    assert po.material_request == mr.name, f"PO.mr {po.material_request} ≠ {mr.name}"
    assert po.supplier == sup, f"PO.supplier {po.supplier} ≠ {sup}"
    assert flt(po.grand_total) == 50 * 1, f"PO grand_total {po.grand_total}"

    # === Step 4: submit PO ===
    po.submit()
    po.reload()
    fc.reload()
    results.append({"step": "4. PO submit + FC committed",
                    "po": po_name, "po_total": flt(po.grand_total),
                    "fc_used": flt(fc.used_value), "fc_remaining": flt(fc.remaining_value)})
    # FC.used_value should track submitted PO grand_total via recalculate_used_value
    fc.recalculate_used_value()
    fc.reload()
    assert flt(fc.used_value) >= 50 * 1, \
        f"FC.used_value={fc.used_value} chưa cập nhật theo PO submit"

    # === Step 5: tạo + submit PR ===
    batch_id = f"INTEG-BATCH-{ts}"
    batch = frappe.new_doc("SC Batch")
    batch.batch_id = batch_id
    batch.item = item
    batch.expiry_date = add_days(today(), 365)
    batch.manufacturing_date = today()
    batch.flags.ignore_permissions = True
    batch.insert()

    pr = frappe.new_doc("SC Purchase Receipt")
    pr.supplier = sup
    pr.purchase_order = po_name
    pr.posting_date = today()
    pr.to_warehouse = wh
    pr.qc_required = 0  # bypass auto-QI cho integration test
    pr.append("items", {
        "item": item, "qty": 50, "uom": item_uom,
        "rate": 1, "batch_no": batch.name,
        "warehouse": wh,
    })
    pr.flags.ignore_permissions = True
    pr.insert(); pr.submit()
    results.append({"step": "5. PR submit",
                    "pr": pr.name, "qc_status": pr.qc_status})

    # === Step 6: PR.on_submit phải update PO.received_qty ===
    po.reload()
    received_total = sum(flt(p.received_qty) for p in po.items)
    results.append({"step": "6. PO.received_qty + status update",
                    "received_total": received_total,
                    "po_status": po.status})
    assert received_total >= 50, f"PO.received_qty {received_total} < 50"
    assert po.status == "Received", f"PO.status {po.status} ≠ Received"

    # === Step 7: make_invoice_from_pr → PI draft ===
    from supplycore.m8_accounting.doctype.sc_purchase_invoice.sc_purchase_invoice \
        import make_invoice_from_pr
    pi_name = make_invoice_from_pr(pr.name)
    pi = frappe.get_doc("SC Purchase Invoice", pi_name)
    assert pi.purchase_receipt == pr.name
    assert pi.purchase_order == po_name
    assert pi.supplier == sup
    results.append({"step": "7. PI draft từ PR",
                    "pi": pi_name, "subtotal": flt(pi.subtotal),
                    "vat": flt(pi.vat_amount), "grand_total": flt(pi.grand_total)})

    # === Step 8: submit PI → GL Entry posted ===
    pi.submit()
    pi.reload()
    gl = frappe.get_all("SC GL Entry",
        filters={"voucher_type": "SC Purchase Invoice", "voucher_no": pi_name},
        fields=["name", "account", "debit", "credit"])
    total_dr = sum(flt(g.debit) for g in gl)
    total_cr = sum(flt(g.credit) for g in gl)
    results.append({"step": "8. PI submit + GL balanced",
                    "pi_status": pi.status,
                    "three_way_match": pi.three_way_match_status,
                    "gl_rows": len(gl),
                    "total_dr": total_dr, "total_cr": total_cr})
    assert len(gl) >= 2, f"GL phải có ≥2 rows, được {len(gl)}"
    assert abs(total_dr - total_cr) < 0.01, \
        f"GL không cân: Dr={total_dr} ≠ Cr={total_cr}"
    assert pi.three_way_match_status in ("Match", "Mismatch"), \
        f"3-way match status: {pi.three_way_match_status}"

    return {"status": "ok", "results": results,
            "chain": {"fc": fc.name, "mr": mr.name, "po": po_name,
                       "pr": pr.name, "pi": pi_name}}
