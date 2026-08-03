"""Seed 10 Hợp đồng khung (Framework Contract) mẫu cho sandbox.

Mục đích: tạo nhanh 10 HĐ khung Active để demo / E2E test M1.
Bypass workflow 3-tier (giống pattern seed_uc_scenario._seed_framework_contracts).

Usage:
    bench --site supplycore execute supplycore.setup.seed_10_framework_contracts.run

Tham chiếu nghiệp vụ: docs/ba-miyano/SupplyCore_MVL_BA.html (§M1).
"""

import frappe
from frappe.utils import today, add_days, add_months, flt, now


# Cấu hình 10 HĐ khung (đa dạng NCC, vật tư, kỳ hạn).
# Định dạng mỗi dòng:
#   (contract_number, supplier, valid_from, valid_to, payment_terms,
#    delivery_terms, contract_type, items=[(item_code, qty, unit_price)])
FC_DATASET = [
    # 1. Dược Hậu Giang — dịch truyền khối lượng lớn, vừa ký 1 tháng
    ("HD-2026-DHG-001", "SC-SUP-03152",
     add_days(today(), -30), add_days(today(), 335),
     "Net 30", "Giao tận Kho Tổng, lead time 5 ngày", "Thường quy",
     [("DTRC-GLU5", 500, 38000), ("DTRC-NACL09", 800, 30000)]),

    # 2. Traphaco — sát trùng, kỳ hạn 12 tháng
    ("HD-2026-TPC-002", "SC-SUP-03153",
     add_days(today(), -20), add_days(today(), 345),
     "Net 30", "Giao tận kho, lead time 7 ngày", "Thường quy",
     [("VTPT-COND-70", 200, 25000), ("VTPT-IODINE", 150, 45000)]),

    # 3. Pymepharco — dịch truyền
    ("HD-2026-PMP-003", "SC-SUP-03154",
     add_days(today(), -45), add_days(today(), 320),
     "Net 45", "Giao tận Kho Tổng, lead time 7 ngày", "Thường quy",
     [("DTRC-RL", 600, 35000), ("DTRC-GLU5", 400, 38000)]),

    # 4. Imexpharm — bảo hộ
    ("HD-2026-IMX-004", "SC-SUP-03155",
     add_days(today(), -90), add_days(today(), 275),
     "Net 30", "Giao tận kho, lead time 3 ngày", "Thường quy",
     [("VTTH-GLOVE-S", 2000, 8000), ("VTTH-MASK-3PLY", 10000, 1500)]),

    # 5. Boston Scientific — bộ truyền dịch + bơm tiêm
    ("HD-2026-BSV-005", "SC-SUP-03156",
     add_days(today(), -60), add_days(today(), 305),
     "Net 30", "Giao tận Kho Trung chuyển, lead time 10 ngày", "Thường quy",
     [("VTTH-IV-SET", 3000, 12000), ("VTTH-SYR-5ML", 5000, 3000)]),

    # 6. Medtronic — kim + bơm tiêm
    ("HD-2026-MDT-006", "SC-SUP-03157",
     add_days(today(), -10), add_days(today(), 355),
     "Net 45", "Giao tận kho, lead time 14 ngày", "Thường quy",
     [("VTTH-NEEDLE-23", 8000, 1200), ("VTTH-SYR-5ML", 8000, 3000)]),

    # 7. B. Braun — dịch truyền, HĐ lớn 3 mặt hàng
    ("HD-2026-BBR-007", "SC-SUP-03158",
     today(), add_months(today(), 12),
     "Net 60", "Giao tận Kho Tổng, lead time 5 ngày", "Thường quy",
     [("DTRC-NACL09", 1500, 30000),
      ("DTRC-RL", 800, 35000),
      ("DTRC-GLU5", 500, 38000)]),

    # 8. 3M Vietnam — khẩu trang + găng tay khối lượng lớn
    ("HD-2026-3MV-008", "SC-SUP-03159",
     today(), add_months(today(), 12),
     "Net 30", "Giao tận kho, lead time 4 ngày", "Thường quy",
     [("VTTH-MASK-3PLY", 30000, 1500), ("VTTH-GLOVE-S", 5000, 8000)]),

    # 9. TBYT Hồng Hà — bông + gạc, sắp hết hạn (≤30 ngày) để test cờ expiring_soon
    ("HD-2026-HHA-009", "SC-SUP-03160",
     add_days(today(), -340), add_days(today(), 25),
     "Net 30", "Giao tận Kho Giao hàng, lead time 3 ngày", "Thường quy",
     [("VTTH-COTTON", 1500, 18000), ("VTTH-GAUZE-5", 2000, 9500)]),

    # 10. Roche Diagnostics — bộ truyền + sát trùng
    ("HD-2026-RCH-010", "SC-SUP-03163",
     add_days(today(), -60), add_days(today(), 305),
     "Net 45", "Giao tận Kho Trung chuyển, lead time 10 ngày", "Thường quy",
     [("VTTH-IV-SET", 5000, 12000), ("VTPT-IODINE", 500, 45000)]),
]


def run() -> dict:
    """Tạo 10 HĐ khung mẫu. Skip nếu contract_number đã tồn tại.

    Returns: dict tóm tắt {created, skipped, errors, contracts:[...]}.
    """
    created = []
    skipped = []
    errors = []

    for row in FC_DATASET:
        cn, supplier, vf, vt, pay_terms, del_terms, ctype, items = row

        if frappe.db.exists("Framework Contract", {"contract_number": cn}):
            skipped.append(cn)
            continue

        try:
            fc = frappe.new_doc("Framework Contract")
            fc.contract_number = cn
            fc.supplier = supplier
            fc.contract_date = vf
            fc.valid_from = vf
            fc.valid_to = vt
            fc.payment_terms = pay_terms
            fc.delivery_terms = del_terms

            total = 0.0
            for item_code, qty, price in items:
                uom = frappe.db.get_value("SC Item", item_code, "uom")
                if not uom:
                    raise ValueError(f"Item {item_code} không có UOM")
                fc.append("items", {
                    "item_code": item_code,
                    "uom": uom,
                    "contract_qty": qty,
                    "unit_price": price,
                })
                total += qty * price

            fc.total_value = total
            fc.remaining_value = total

            # Bypass 3-tier — set Approved trước khi submit
            fc.approval_stage = "Approved"
            fc.manager_approved_by = "Administrator"
            fc.manager_approved_at = now()
            fc.manager_comment = "Auto-approved by seed script"
            fc.executive_approved_by = "Administrator"
            fc.executive_approved_at = now()
            fc.executive_comment = "Auto-approved by seed script"
            fc.remarks = (
                f"HĐ khung mẫu sinh bằng seed_10_framework_contracts. "
                f"Loại: {ctype}."
            )

            fc.flags.ignore_permissions = True
            fc.insert()
            fc.submit()

            created.append({
                "name": fc.name,
                "contract_number": cn,
                "supplier": supplier,
                "total_value": fc.total_value,
                "status": fc.status,
                "valid_from": str(fc.valid_from),
                "valid_to": str(fc.valid_to),
                "items": len(fc.items),
            })
        except Exception as e:
            errors.append({"contract_number": cn, "error": str(e)[:300]})
            frappe.log_error(
                message=f"FC seed lỗi {cn}: {str(e)[:500]}",
                title="seed_10_framework_contracts",
            )

    frappe.db.commit()
    return {
        "created": len(created),
        "skipped": len(skipped),
        "errors": len(errors),
        "contracts": created,
        "skipped_list": skipped,
        "error_details": errors,
    }
