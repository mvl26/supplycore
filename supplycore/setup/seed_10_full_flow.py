"""Seed E2E full-flow cho 10 HĐ khung — theo docs/E2E_MAIN_FLOW_SCENARIO.md.

Phải chạy `supplycore.setup.seed_10_framework_contracts.run` trước.

Mỗi FC sẽ sinh:
    YCMH (MR) → ĐM (PO) → Phiếu nhập (PR) → Lô + Phiếu KCS (auto)
    → YCCK (TR) → Phiếu chuyển kho (SE)
    → Cấp phát BN (PD) → Hoá đơn (PI) → Phiếu thanh toán (PE)

Cuối luồng tạo 1 Đối soát kho (SR) cho Kho Khoa Dược.

Usage:
    bench --site supplycore execute supplycore.setup.seed_10_full_flow.run
"""

import frappe
from frappe.utils import today, add_days, flt, now, random_string


# ---------------------------------------------------------------------
# Cấu hình
# ---------------------------------------------------------------------
MAIN_WH = "Kho Trung chuyển"       # Kho nhập đầu vào (PR)
DEPT_WH = "Kho Khoa Dược"          # Kho cấp phát (PD)

CONTRACT_NUMBERS = [
    "HD-2026-DHG-001", "HD-2026-TPC-002", "HD-2026-PMP-003", "HD-2026-IMX-004",
    "HD-2026-BSV-005", "HD-2026-MDT-006", "HD-2026-BBR-007", "HD-2026-3MV-008",
    "HD-2026-HHA-009", "HD-2026-RCH-010",
]

# Giới hạn SL mua/nhập trên 1 dòng để dữ liệu mẫu gọn
QTY_CAP_PER_ITEM = 100
# Tỷ lệ luân chuyển sang Kho Khoa Dược (% của qty nhận)
TRANSFER_PCT = 0.5
# Số lượng cấp phát mỗi PD (per item)
DISPENSE_QTY = 2
# Tỷ lệ thuế VAT
VAT_RATE = 8


def run() -> dict:
    result = {
        "fcs_processed": [],
        "mrs": [], "pos": [], "prs": [],
        "qis_submitted": 0, "batches_created": 0,
        "trs": [], "ses": [],
        "pds": [], "pis": [], "pes": [],
        "sr": None,
        "errors": [],
        "summary": {},
    }

    fcs = frappe.get_all(
        "Framework Contract",
        filters={"contract_number": ["in", CONTRACT_NUMBERS],
                  "docstatus": 1, "status": "Active"},
        fields=["name", "contract_number", "supplier", "valid_to"],
        order_by="contract_number",
    )

    if len(fcs) < len(CONTRACT_NUMBERS):
        return {
            "error": f"Cần đủ {len(CONTRACT_NUMBERS)} FC Active. Hiện có {len(fcs)}. "
                      f"Chạy supplycore.setup.seed_10_framework_contracts.run trước.",
            "found": [f.contract_number for f in fcs],
        }

    patients = frappe.get_all("SC Patient", filters={"disabled": 0},
                                fields=["name", "bhyt_card_no",
                                        "bhyt_payment_rate", "current_department"],
                                order_by="name")
    if not patients:
        result["errors"].append("Không có SC Patient nào để cấp phát")

    for idx, fc in enumerate(fcs):
        try:
            _process_one_fc(fc, idx, patients, result)
            result["fcs_processed"].append(fc.contract_number)
        except Exception as e:
            result["errors"].append({"fc": fc.contract_number, "stage": "top",
                                       "error": str(e)[:300]})
            frappe.log_error(
                message=f"seed_10_full_flow top {fc.name}: {str(e)[:500]}",
                title="seed_10_full_flow",
            )
            frappe.db.rollback()
            # Re-fetch fc after rollback
            continue

    # 1 SR cuối ở Kho Khoa Dược
    try:
        sr_name = _create_stock_reconciliation(DEPT_WH)
        result["sr"] = sr_name
    except Exception as e:
        result["errors"].append({"stage": "stock_reconciliation",
                                   "error": str(e)[:300]})
        frappe.log_error(message=str(e)[:500],
                          title="seed_10_full_flow SR")

    frappe.db.commit()

    result["summary"] = {
        "fcs": len(result["fcs_processed"]),
        "mrs": len(result["mrs"]),
        "pos": len(result["pos"]),
        "prs": len(result["prs"]),
        "qis_submitted": result["qis_submitted"],
        "batches_created": result["batches_created"],
        "trs": len(result["trs"]),
        "ses": len(result["ses"]),
        "pds": len(result["pds"]),
        "pis": len(result["pis"]),
        "pes": len(result["pes"]),
        "sr": 1 if result["sr"] else 0,
        "errors": len(result["errors"]),
    }
    return result


# =====================================================================
# Chain cho 1 FC
# =====================================================================
def _process_one_fc(fc, idx, patients, result):
    fc_doc = frappe.get_doc("Framework Contract", fc.name)

    # --- Bước 2: YCMH ---
    mr_items = []
    for r in fc_doc.items:
        qty = min(flt(r.contract_qty), QTY_CAP_PER_ITEM)
        if qty > 0:
            mr_items.append({"item_code": r.item_code, "qty": qty})
    if not mr_items:
        raise ValueError("FC không có item nào với contract_qty > 0")

    mr_res = fc_doc.make_material_request(
        items=mr_items,
        schedule_date=add_days(today(), 14),
        warehouse=MAIN_WH,
    )
    mr_name = mr_res["material_request"]
    mr_doc = frappe.get_doc("SC Material Request", mr_name)
    mr_doc.flags.ignore_permissions = True
    mr_doc.submit()
    result["mrs"].append(mr_name)

    # --- Bước 3: ĐM ---
    po = frappe.new_doc("SC Purchase Order")
    po.supplier = fc.supplier
    po.transaction_date = today()
    po.schedule_date = add_days(today(), 14)
    po.framework_contract = fc.name
    po.material_request = mr_name
    po.to_warehouse = MAIN_WH
    po.payment_terms = fc_doc.payment_terms
    po.delivery_terms = fc_doc.delivery_terms
    po.remarks = f"Đơn mua auto từ YCMH {mr_name} (HĐ {fc.contract_number})"
    fc_price = {r.item_code: flt(r.unit_price) for r in fc_doc.items}
    fc_uom = {r.item_code: r.uom for r in fc_doc.items}
    for it in mr_items:
        po.append("items", {
            "item": it["item_code"],
            "uom": fc_uom.get(it["item_code"]),
            "qty": it["qty"],
            "rate": fc_price.get(it["item_code"], 0),
            "warehouse": MAIN_WH,
            "schedule_date": add_days(today(), 14),
        })
    # Bypass 2-tier approval
    po.approval_stage = "Approved"
    po.manager_approved_by = "Administrator"
    po.manager_approved_at = now()
    po.executive_approved_by = "Administrator"
    po.executive_approved_at = now()
    po.flags.ignore_permissions = True
    po.insert()
    po.submit()
    result["pos"].append(po.name)

    # --- Bước 4: Phiếu nhập (PR) ---
    pr = frappe.new_doc("SC Purchase Receipt")
    pr.supplier = fc.supplier
    pr.purchase_order = po.name
    pr.posting_date = today()
    pr.to_warehouse = MAIN_WH
    pr.qc_required = 1
    pr.remarks = f"Phiếu nhập auto từ Đơn mua {po.name}"
    po_reload = frappe.get_doc("SC Purchase Order", po.name)
    for poi in po_reload.items:
        has_batch = int(frappe.db.get_value("SC Item", poi.item, "has_batch_no") or 0)
        pr_row = {
            "item": poi.item,
            "uom": poi.uom,
            "qty": flt(poi.qty),
            "po_qty": flt(poi.qty),
            "rate": flt(poi.rate),
            "warehouse": poi.warehouse or MAIN_WH,
            "po_item_ref": poi.name,
        }
        if has_batch:
            pr_row.update({
                "supplier_batch_no": f"LOT-{idx+1:02d}-{poi.item[:6]}-{random_string(4)}",
                "manufacturing_date": add_days(today(), -60),
                "expiry_date": add_days(today(), 540),
            })
        pr.append("items", pr_row)
    pr.flags.ignore_permissions = True
    pr.insert()
    pr.submit()
    result["prs"].append(pr.name)

    # --- Bước 5: Lô + Bước 6: Phiếu KCS (auto-tạo, chỉ cần submit Accepted) ---
    pr_reload = frappe.get_doc("SC Purchase Receipt", pr.name)
    batch_names = set()
    for r in pr_reload.items:
        if r.batch_no:
            batch_names.add(r.batch_no)
    result["batches_created"] += len(batch_names)

    auto_qis = frappe.get_all(
        "SC Quality Inspection",
        filters={"purchase_receipt": pr.name, "docstatus": 0},
        pluck="name",
    )
    for qi_name in auto_qis:
        try:
            qi = frappe.get_doc("SC Quality Inspection", qi_name)
            if not qi.readings:
                # Fallback: bổ sung readings nếu template trống
                for spec in ("Cảm quan", "Bao bì", "Nhãn mác"):
                    qi.append("readings",
                                {"specification": spec, "status": "Accepted",
                                 "value": "Đạt"})
            else:
                for rd in qi.readings:
                    rd.status = "Accepted"
                    if not rd.value:
                        rd.value = "Đạt"
            qi.overall_status = "Accepted"
            qi.qty_inspected = flt(qi.received_qty)
            qi.qty_accepted = flt(qi.received_qty)
            qi.qty_rejected = 0
            qi.flags.ignore_permissions = True
            qi.save()
            qi.submit()
            result["qis_submitted"] += 1
        except Exception as e:
            result["errors"].append({
                "fc": fc.contract_number, "stage": "qi",
                "qi": qi_name, "error": str(e)[:200],
            })

    # --- Bước 8: YCCK (TR) ---
    tr = frappe.new_doc("SC Transfer Request")
    tr.request_date = today()
    tr.transfer_type = "Replenishment"
    tr.required_by = add_days(today(), 3)
    tr.from_warehouse = MAIN_WH
    tr.to_warehouse = DEPT_WH
    tr.remarks = f"Chuyển nội bộ từ PN {pr.name}"
    for poi in po_reload.items:
        qty = max(1, int(flt(poi.qty) * TRANSFER_PCT))
        tr.append("items", {
            "item": poi.item,
            "uom": poi.uom,
            "requested_qty": qty,
            "approved_qty": qty,
        })
    tr.flags.ignore_permissions = True
    tr.insert()
    tr.submit()
    result["trs"].append(tr.name)

    # --- Bước 9: Phiếu chuyển kho (SE) ---
    se_name = tr.make_stock_entry()
    se = frappe.get_doc("SC Stock Entry", se_name)
    se.flags.ignore_permissions = True
    se.submit()
    result["ses"].append(se_name)

    # --- Bước 10: Cấp phát BN (PD) ---
    if patients:
        try:
            patient = patients[idx % len(patients)]
            pd = frappe.new_doc("SC Patient Dispensing")
            pd.dispensing_date = today()
            pd.patient = patient.name
            pd.bhyt_card_no = patient.bhyt_card_no
            pd.bhyt_payment_rate = patient.bhyt_payment_rate or 0
            pd.ward = patient.current_department
            pd.remarks = f"Cấp phát từ HĐ {fc.contract_number}"
            added_any = False
            for poi in po_reload.items:
                avail = flt(frappe.db.sql("""
                    SELECT COALESCE(SUM(qty_change), 0)
                    FROM `tabSC Stock Ledger Entry`
                    WHERE item = %s AND warehouse = %s AND is_cancelled = 0
                """, (poi.item, DEPT_WH))[0][0])
                if avail < DISPENSE_QTY:
                    continue
                # Pick FEFO batch ở DEPT_WH
                batch = _pick_fefo_batch(poi.item, DEPT_WH)
                pd.append("items", {
                    "item": poi.item,
                    "uom": poi.uom,
                    "qty": DISPENSE_QTY,
                    "unit_cost": flt(poi.rate),
                    "warehouse": DEPT_WH,
                    "batch": batch,
                })
                added_any = True
            if added_any:
                pd.flags.ignore_permissions = True
                pd.insert()
                pd.submit()
                result["pds"].append(pd.name)
        except Exception as e:
            result["errors"].append({
                "fc": fc.contract_number, "stage": "pd",
                "error": str(e)[:200],
            })

    # --- Bước 11: Hoá đơn (PI) ---
    try:
        pi = frappe.new_doc("SC Purchase Invoice")
        pi.supplier = fc.supplier
        pi.supplier_invoice_no = f"INV-{fc.contract_number}-{random_string(4)}"
        pi.invoice_date = today()
        pi.due_date = add_days(today(), 30)
        pi.purchase_order = po.name
        pi.purchase_receipt = pr.name
        pi.vat_rate = VAT_RATE
        pi.payment_terms = fc_doc.payment_terms or "Net 30"
        for r in pr_reload.items:
            pi.append("items", {
                "item": r.item,
                "uom": r.uom,
                "qty": flt(r.qty),
                "rate": flt(r.rate),
                "po_item_ref": r.po_item_ref,
                "pr_item_ref": r.name,
            })
        pi.remarks = f"Hoá đơn auto từ PN {pr.name}"
        pi.flags.ignore_permissions = True
        pi.insert()
        pi.submit()
        result["pis"].append(pi.name)

        # --- Phiếu thanh toán (PE) full payment ---
        pe = frappe.new_doc("SC Payment Entry")
        pe.payment_date = today()
        pe.supplier = fc.supplier
        pe.payment_method = "Bank Transfer"
        pe.amount = flt(pi.grand_total)
        pe.reference_no = f"BANK-{random_string(6)}"
        pe.reference_date = today()
        pe.append("references", {
            "purchase_invoice": pi.name,
            "allocated_amount": flt(pi.grand_total),
        })
        pe.remarks = f"Thanh toán toàn bộ hoá đơn {pi.name}"
        pe.flags.ignore_permissions = True
        pe.insert()
        pe.submit()
        result["pes"].append(pe.name)
    except Exception as e:
        result["errors"].append({
            "fc": fc.contract_number, "stage": "pi_pe",
            "error": str(e)[:200],
        })


# =====================================================================
# Helpers
# =====================================================================
def _pick_fefo_batch(item, warehouse):
    """Pick batch còn tồn sớm hết hạn nhất ở warehouse."""
    row = frappe.db.sql("""
        SELECT sle.batch,
                COALESCE(b.expiry_date, '9999-12-31') AS expiry,
                SUM(sle.qty_change) AS qty
        FROM `tabSC Stock Ledger Entry` sle
        LEFT JOIN `tabSC Batch` b ON b.name = sle.batch
        WHERE sle.item = %s AND sle.warehouse = %s
          AND sle.is_cancelled = 0 AND sle.batch IS NOT NULL
        GROUP BY sle.batch
        HAVING qty > 0
        ORDER BY expiry ASC
        LIMIT 1
    """, (item, warehouse), as_dict=True)
    return row[0].batch if row else None


def _create_stock_reconciliation(warehouse):
    """Tạo 1 SC Stock Reconciliation ở warehouse với toàn bộ item đang có tồn."""
    items_with_stock = frappe.db.sql("""
        SELECT item, SUM(qty_change) AS qty
        FROM `tabSC Stock Ledger Entry`
        WHERE warehouse = %s AND is_cancelled = 0
        GROUP BY item
        HAVING qty > 0
        LIMIT 10
    """, warehouse, as_dict=True)
    if not items_with_stock:
        return None

    sr = frappe.new_doc("SC Stock Reconciliation")
    sr.posting_date = today()
    sr.warehouse = warehouse
    for r in items_with_stock:
        uom = frappe.db.get_value("SC Item", r.item, "uom")
        # Đếm thực tế = system - 1 để tạo variance nhỏ
        actual = max(0, flt(r.qty) - 1)
        sr.append("items", {
            "item": r.item, "uom": uom,
            "actual_qty": actual,
            "system_qty": flt(r.qty),
            "valuation_rate": 10000,
            "reason": "Counting Error",
        })
    sr.flags.ignore_permissions = True
    sr.insert()
    sr.submit()
    return sr.name
