"""Smoke test M1 — SC Supplier + SC Item + Framework Contract + Release Order + SC PO."""

import frappe
from frappe.utils import today, add_days, flt


SUPPLIER = "Công ty CP Dược Hậu Giang"
ITEMS = [("VTTH-GLOVE-S", 100, 30000), ("VTTH-MASK-3PLY", 200, 1500)]
CONTRACT_NO = "TEST-M1-SMOKE-2026"


def run():
    if not frappe.db.exists("SC Supplier", {"supplier_name": SUPPLIER}):
        return {"status": "skip", "reason": f"Cần seed master data trước"}
    supplier = frappe.db.get_value("SC Supplier", {"supplier_name": SUPPLIER}, "name")
    results = []

    _cleanup()

    fc = frappe.new_doc("Framework Contract")
    fc.supplier = supplier
    fc.contract_number = CONTRACT_NO
    fc.contract_date = today()
    fc.valid_from = today()
    fc.valid_to = add_days(today(), 365)
    fc.payment_terms = "Net 30"
    total = 0
    for code, qty, price in ITEMS:
        if not frappe.db.exists("SC Item", code): continue
        uom = frappe.db.get_value("SC Item", code, "uom")
        fc.append("items", {"item_code": code, "uom": uom,
                            "contract_qty": qty, "unit_price": price})
        total += qty * price
    fc.total_value = total
    fc.flags.ignore_permissions = True
    fc.insert(); fc.reload()
    # UC-03 3-tier approval (Administrator có System Manager role bypass)
    fc.submit_for_review(); fc.reload()
    fc.approve_as_manager(comment="smoke"); fc.reload()
    if fc.approval_stage == "Executive Review":
        fc.approve_as_executive(comment="smoke"); fc.reload()
    fc.submit(); fc.reload()
    results.append({"step": "FC", "fc": fc.name, "status": fc.status,
                    "total": float(fc.total_value), "remaining": float(fc.remaining_value)})

    ro = frappe.new_doc("Release Order")
    ro.framework_contract = fc.name
    ro.release_date = today()
    ro.required_by = add_days(today(), 7)
    ro.remarks = "M1-SMOKE"
    ro.flags.ignore_permissions = True
    ro.insert(); ro.reload()
    ro.items[0].qty = 10
    ro.save(); ro.submit(); ro.reload(); fc.reload()
    results.append({"step": "RO", "ro": ro.name, "ro_total": float(ro.total_amount),
                    "fc_committed": float(fc.committed_value)})

    po_name = ro.make_purchase_order()
    fc.reload()
    po = frappe.get_doc("SC Purchase Order", po_name)
    po.submit(); fc.reload()
    results.append({"step": "PO", "po": po_name, "po_total": float(po.grand_total),
                    "fc_used": float(fc.used_value), "fc_remaining": float(fc.remaining_value)})

    return {"status": "ok", "results": results}


def _cleanup():
    # Strict cleanup: clear links trước khi cancel
    for ro in frappe.get_all("Release Order", filters={"remarks": "M1-SMOKE"},
                             fields=["name", "purchase_order"]):
        if ro.purchase_order and frappe.db.exists("SC Purchase Order", ro.purchase_order):
            frappe.db.set_value("Release Order", ro.name, "purchase_order", None)
            po = frappe.get_doc("SC Purchase Order", ro.purchase_order)
            try:
                if po.docstatus == 1: po.cancel()
            except Exception: pass
            try:
                frappe.delete_doc("SC Purchase Order", po.name, force=True, ignore_permissions=True)
            except Exception: pass
        d = frappe.get_doc("Release Order", ro.name)
        try:
            if d.docstatus == 1: d.cancel()
        except Exception: pass
        try:
            frappe.delete_doc("Release Order", ro.name, force=True, ignore_permissions=True)
        except Exception: pass
    for fc in frappe.get_all("Framework Contract", filters={"contract_number": CONTRACT_NO}):
        d = frappe.get_doc("Framework Contract", fc.name)
        try:
            if d.docstatus == 1: d.cancel()
        except Exception: pass
        try:
            frappe.delete_doc("Framework Contract", fc.name, force=True, ignore_permissions=True)
        except Exception: pass
    frappe.db.commit()
