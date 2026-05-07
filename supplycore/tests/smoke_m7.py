"""Smoke test M7 — BHYT Code Config + SC Patient + Dispensing Request + Patient Dispensing."""

import frappe
from frappe.utils import today, add_days, random_string, flt


BHYT_CODE = "BHYT-N05-VTTH-2026"
PATIENT_ID = "BN-M7-SMOKE-001"


def run():
    item_code = "VTTH-GLOVE-S"  # has_batch + has_bhyt
    warehouse = "Kho Vật tư tiêu hao"
    if not (frappe.db.exists("SC Item", item_code) and frappe.db.exists("SC Warehouse", warehouse)):
        return {"status": "skip", "reason": "Cần seed master data"}

    item_uom = frappe.db.get_value("SC Item", item_code, "uom")
    item_group = frappe.db.get_value("SC Item", item_code, "item_group")
    department = frappe.db.get_value("SC Department", "Khoa Cấp cứu", "name")
    results = []

    # Cleanup: clear DR.patient_dispensing trước, rồi delete PD, rồi DR
    for n in frappe.get_all("SC Dispensing Request", filters={"remarks": "M7-SMOKE"},
                              fields=["name"]):
        frappe.db.set_value("SC Dispensing Request", n.name, "patient_dispensing", None)
    frappe.db.commit()
    for n in frappe.get_all("SC Patient Dispensing", filters={"remarks": "M7-SMOKE"}, fields=["name"]):
        d = frappe.get_doc("SC Patient Dispensing", n.name)
        try:
            if d.docstatus == 1: d.cancel()
        except: pass
        try:
            frappe.delete_doc("SC Patient Dispensing", n.name, force=True, ignore_permissions=True)
        except: pass
    for n in frappe.get_all("SC Dispensing Request", filters={"remarks": "M7-SMOKE"},
                              fields=["name", "stock_entry", "patient_dispensing"]):
        if n.stock_entry and frappe.db.exists("SC Stock Entry", n.stock_entry):
            frappe.db.set_value("SC Dispensing Request", n.name, "stock_entry", None)
            se = frappe.get_doc("SC Stock Entry", n.stock_entry)
            try:
                if se.docstatus == 1: se.cancel()
            except: pass
            frappe.delete_doc("SC Stock Entry", se.name, force=True, ignore_permissions=True)
        d = frappe.get_doc("SC Dispensing Request", n.name)
        if d.docstatus == 1: d.cancel()
        frappe.delete_doc("SC Dispensing Request", n.name, force=True, ignore_permissions=True)
    for n in frappe.get_all("SC Patient", filters={"patient_id": PATIENT_ID}):
        frappe.delete_doc("SC Patient", n.name, force=True, ignore_permissions=True)
    for n in frappe.get_all("SC BHYT Code Config", filters={"bhyt_code": BHYT_CODE}):
        frappe.delete_doc("SC BHYT Code Config", n.name, force=True, ignore_permissions=True)
    frappe.db.commit()

    # 1. Tạo BHYT Code Config — N05, 80%, ceiling 25000 (giá trần)
    cfg = frappe.new_doc("SC BHYT Code Config")
    cfg.bhyt_code = BHYT_CODE
    cfg.bhyt_name = "Vật tư tiêu hao Y tế (N05)"
    cfg.bhyt_group = "N05"
    cfg.payment_rate = 80
    cfg.ceiling_price = 25000   # Giá trần — 25k/đôi (item cost = 30k → vượt)
    cfg.item_group = item_group
    cfg.is_active = 1
    cfg.effective_from = today()
    cfg.legal_basis = "TT 04/2024/TT-BYT"
    cfg.flags.ignore_permissions = True
    cfg.insert()
    results.append({"step": "BHYT Config", "name": cfg.name, "rate": float(cfg.payment_rate),
                    "ceiling": float(cfg.ceiling_price), "group": cfg.bhyt_group})

    # 2. Tạo Patient
    p = frappe.new_doc("SC Patient")
    p.patient_id = PATIENT_ID
    p.patient_name = "Nguyễn Văn Smoke"
    p.bhyt_card_no = "1234567890"
    p.bhyt_type = "Đúng tuyến"
    p.bhyt_payment_rate = 80
    p.current_department = department
    p.flags.ignore_permissions = True
    p.insert()
    results.append({"step": "Patient", "name": p.name, "bhyt_card": p.bhyt_card_no,
                    "type": p.bhyt_type, "rate": float(p.bhyt_payment_rate)})

    # 3. Test API get_active_config + calculate_cost
    from supplycore.api import bhyt
    cfg_lookup = bhyt.get_active_config(item_code)
    results.append({"step": "API get_active_config", "found": cfg_lookup is not None,
                    "code": cfg_lookup.get("bhyt_code") if cfg_lookup else None,
                    "rate": float(cfg_lookup.get("payment_rate") or 0) if cfg_lookup else None})
    assert cfg_lookup, "BHYT config phải tìm thấy qua item_group lookup"

    calc = bhyt.calculate_cost(
        items=[{"item_code": item_code, "qty": 10, "unit_cost": 30000}],
        patient=p.name,
    )
    results.append({"step": "API calculate_cost", "total_cost": calc["total_cost"],
                    "bhyt_covered": calc["bhyt_covered"],
                    "patient_pays": calc["patient_pays"],
                    "ceiling_overage": calc["ceiling_overage"]})
    # Verify: 10 × 30000 = 300000; cap = 25000; bhyt = 10 × 25000 × 80% = 200000
    # ceiling_overage = 10 × (30000-25000) = 50000; patient_pays = 300000 - 200000 = 100000
    assert calc["total_cost"] == 300000
    assert calc["bhyt_covered"] == 200000, f"BHYT covered sai: {calc['bhyt_covered']}"
    assert calc["ceiling_overage"] == 50000
    assert calc["patient_pays"] == 100000

    # 4. Tạo batch + receipt để có stock — disable batch cũ tránh FEFO conflict
    for ob in frappe.get_all("SC Batch", filters={"item": item_code, "disabled": 0}):
        frappe.db.set_value("SC Batch", ob.name, "disabled", 1)
    frappe.db.commit()
    batch = frappe.new_doc("SC Batch")
    batch.batch_id = f"{item_code}-M7-{random_string(5)}"
    batch.item = item_code
    batch.expiry_date = add_days(today(), 365)
    batch.flags.ignore_permissions = True
    batch.insert()

    se_in = frappe.new_doc("SC Stock Entry")
    se_in.entry_type = "Material Receipt"
    se_in.posting_date = today()
    se_in.to_warehouse = warehouse
    se_in.append("items", {"item": item_code, "qty": 50, "uom": item_uom,
                            "batch": batch.name, "valuation_rate": 30000})
    se_in.flags.ignore_permissions = True
    se_in.insert(); se_in.submit()

    # 5. Tạo Dispensing Request Patient-Specific
    dr = frappe.new_doc("SC Dispensing Request")
    dr.request_date = today()
    dr.purpose = "Patient-Specific"
    dr.required_by = today()
    dr.department = department
    dr.patient = p.name
    dr.from_warehouse = warehouse
    dr.requested_by = "Administrator"
    dr.remarks = "M7-SMOKE"
    dr.append("items", {"item": item_code, "uom": item_uom,
                          "requested_qty": 10, "approved_qty": 10, "batch": batch.name})
    dr.flags.ignore_permissions = True
    dr.insert(); dr.submit(); dr.reload()
    results.append({"step": "DR submitted", "dr": dr.name, "status": dr.status})

    # 6. Make Stock Entry from DR
    se_name = dr.make_stock_entry()
    dr.reload()
    se = frappe.get_doc("SC Stock Entry", se_name)
    se.submit()
    dr.reload()
    results.append({"step": "SE Issue", "se": se_name, "dr_status": dr.status})

    # 7. Make Patient Dispensing
    pd_name = dr.make_patient_dispensing()
    dr.reload()
    pd = frappe.get_doc("SC Patient Dispensing", pd_name)
    pd.remarks = "M7-SMOKE"
    pd.save()
    pd.reload()
    results.append({"step": "PD created", "pd": pd_name,
                    "total_cost": float(pd.total_cost),
                    "bhyt_covered": float(pd.bhyt_covered),
                    "patient_pays": float(pd.patient_pays),
                    "ceiling_overage": float(pd.ceiling_overage)})
    # Verify auto-calc khớp API
    assert flt(pd.total_cost) == 300000, f"PD total_cost: {pd.total_cost}"
    assert flt(pd.bhyt_covered) == 200000, f"PD bhyt: {pd.bhyt_covered}"
    assert flt(pd.ceiling_overage) == 50000

    # 8. Submit PD
    pd.submit()
    dr.reload()
    results.append({"step": "PD submitted", "pd_status": "Submitted" if pd.docstatus == 1 else "Draft",
                    "dr_status": dr.status,
                    "row_bhyt": [{"item": r.item, "code": r.bhyt_code, "rate": float(r.bhyt_rate),
                                  "amount": float(r.bhyt_amount)} for r in pd.items]})

    return {"status": "ok", "results": results}
