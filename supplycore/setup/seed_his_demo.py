"""DEMO UC-18B auto-submit: seed đủ 12 dòng phiếu mẫu PX050626-00021923
(item + lô + tồn) rồi nhập qua đường auto-submit (force_draft=False) → TR submit
→ Stock Entry → SLE chuyển tồn.

Chạy: bench --site <site> execute supplycore.setup.seed_his_demo.run
Re-runnable: xoá TR/SE cũ của phiếu rồi chạy lại.

CHỈ DÙNG ĐỂ DEMO — dữ liệu thuốc mẫu, không phải master data thật.
"""
import frappe
from frappe.utils import today
from supplycore.api.his_import import _process_extracted

SRC = "Kho Khoa Điều trị Cao Cấp"
DST = "Kho lẻ nội trú"
SLIP = "PX050626-00021923"
GRP = "Vật tư tiêu hao"

# tt, code, name, uom, lô, expiry(dd/mm/yyyy), expiry_iso, qty
LINES = [
    (1, "2025GE222", "Betahistin 24 24mg", "Viên", "2602620", "01/03/2029", "2029-03-01", 2),
    (2, "2024BD52", "Betaloc Zok 25mg 25mg", "Viên", "ZBDB", "02/04/2028", "2028-04-02", 1),
    (3, "2025GE40", "Cinnarizin Pharma 25mg", "Viên", "421225", "09/12/2027", "2027-12-09", 2),
    (4, "2025GE240", "Cồn xoa bóp Jamda 50ml", "Lọ", "3925", "07/12/2027", "2027-12-07", 1),
    (5, "2025GE240", "Cồn xoa bóp Jamda 50ml", "Lọ", "0126", "03/01/2028", "2028-01-03", 5),
    (6, "2025GE185", "COSYNDO B 175mg+175mg+125mcg", "Viên", "020126", "15/01/2029", "2029-01-15", 2),
    (7, "2025GE46", "Fenostad 200 200mg", "Viên", "120825", "07/08/2028", "2028-08-07", 1),
    (8, "2025TP22", "Haisamin 200mg", "Viên", "061225", "06/12/2028", "2028-12-06", 4),
    (9, "2026TPSX10", "Hoàn lục vị", "Gam", "080126", "30/04/2028", "2028-04-30", 24),
    (10, "2026TPSX06", "Hoàn phong thấp", "Viên", "010326", "30/11/2027", "2027-11-30", 3),
    (11, "2024BD01", "Xatral XL 10mg 10 mg", "Viên", "KT1297", "30/06/2027", "2027-06-30", 1),
    (12, "2025QG07", "Zhekof 40mg", "Viên", "252367", "03/11/2028", "2028-11-03", 1),
]


def _ensure_uom(u):
    if not frappe.db.exists("SC UOM", u):
        d = frappe.new_doc("SC UOM"); d.uom_name = u
        d.flags.ignore_permissions = True; d.flags.ignore_mandatory = True; d.insert()


def _ensure_item(code, name, uom):
    _ensure_uom(uom)
    if frappe.db.exists("SC Item", code):
        frappe.db.set_value("SC Item", code, {"his_code": code, "has_batch_no": 1})
        return
    d = frappe.new_doc("SC Item")
    d.item_code = code; d.item_name = name; d.his_code = code; d.uom = uom
    d.item_group = GRP; d.is_stock_item = 1; d.is_purchase_item = 1
    d.is_medical_supply = 1; d.has_batch_no = 1
    d.flags.ignore_permissions = True; d.insert()


def _ensure_batch(lot, item, exp_iso):
    if frappe.db.exists("SC Batch", lot):
        frappe.db.set_value("SC Batch", lot, "qc_status", "Accepted")
        return
    d = frappe.new_doc("SC Batch")
    d.batch_id = lot; d.item = item; d.expiry_date = exp_iso; d.qc_status = "Accepted"
    d.flags.ignore_permissions = True; d.flags.ignore_mandatory = True; d.insert()


def _seed_stock(item, wh, lot, qty):
    from supplycore.supplycore.doctype.sc_stock_ledger_entry.sc_stock_ledger_entry import (
        SCStockLedgerEntry)
    have = SCStockLedgerEntry.get_available_qty(item, wh, lot)
    need = (qty + 20) - have
    if need > 0:
        nm = frappe.generate_hash(length=12)
        frappe.db.sql(
            """INSERT INTO `tabSC Stock Ledger Entry`
               (name,creation,modified,modified_by,owner,docstatus,idx,posting_date,
                item,warehouse,batch,qty_change,is_cancelled)
               VALUES (%s,NOW(),NOW(),'Administrator','Administrator',1,0,%s,%s,%s,%s,%s,0)""",
            (nm, today(), item, wh, lot, need))


def _cleanup_existing():
    for r in frappe.get_all("SC Transfer Request", filters={"his_slip_no": SLIP},
                            fields=["name", "docstatus", "stock_entry"]):
        if r.stock_entry and frappe.db.exists("SC Stock Entry", r.stock_entry):
            se = frappe.get_doc("SC Stock Entry", r.stock_entry)
            if se.docstatus == 1:
                se.cancel()
            frappe.delete_doc("SC Stock Entry", r.stock_entry, force=1, ignore_permissions=True)
        if r.docstatus == 1:
            frappe.get_doc("SC Transfer Request", r.name).cancel()
        frappe.delete_doc("SC Transfer Request", r.name, force=1, ignore_permissions=True)


def run():
    for tt, code, name, uom, lot, exp, exp_iso, qty in LINES:
        _ensure_item(code, name, uom)
        _ensure_batch(lot, code, exp_iso)
        _seed_stock(code, SRC, lot, qty)
    _cleanup_existing()
    frappe.db.commit()

    data = {
        "slip_no": SLIP, "slip_date": "09/06/2026",
        "from_warehouse_name": SRC, "to_warehouse_name": DST,
        "lines": [{"tt": tt, "name": name, "his_code": code, "uom": uom, "batch_no": lot,
                   "expiry": exp, "qty": qty, "unit_price": 0, "amount": 0}
                  for tt, code, name, uom, lot, exp, exp_iso, qty in LINES],
    }
    # force_draft=False = đường máy-sinh (JSON) cho phép auto-submit khi khớp 100%
    r = _process_extracted(data, force_draft=False)
    frappe.db.commit()

    tr = frappe.get_doc("SC Transfer Request", r["transfer_request"])
    print("=== KẾT QUẢ ===")
    print("status:", r["status"], "| ok/err:", r["lines_ok"], "/", r["lines_error"])
    print("TR:", tr.name, "| docstatus:", tr.docstatus, "| status:", tr.status)
    print("Stock Entry:", tr.stock_entry)
    if tr.stock_entry:
        from supplycore.supplycore.doctype.sc_stock_ledger_entry.sc_stock_ledger_entry import (
            SCStockLedgerEntry)
        sample = LINES[0]
        print("Ví dụ tồn sau chuyển — Betahistin lô 2602620:",
              "nguồn", SCStockLedgerEntry.get_available_qty("2025GE222", SRC, "2602620"),
              "| đích", SCStockLedgerEntry.get_available_qty("2025GE222", DST, "2602620"))
