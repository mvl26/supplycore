import frappe
from frappe.utils import today, add_days

def run():
    print("=== BUG 2: PR auto-batch ===")
    pr = frappe.new_doc("SC Purchase Receipt")
    pr.supplier = frappe.db.get_value("SC Supplier", {"disabled":0}, "name")
    pr.posting_date = today()
    pr.to_warehouse = "Kho Trung chuyển"
    pr.qc_required = 0
    pr.no_po_reason = "Test repro — no PO"
    batch_items = frappe.db.sql("""SELECT name FROM `tabSC Item` WHERE has_batch_no = 1 AND disabled = 0 LIMIT 3""", as_dict=True)
    if not batch_items:
        print("No items with has_batch_no=1")
        return
    print(f"Batch items: {[b.name for b in batch_items]}")
    a = batch_items[0].name
    b_item = batch_items[1].name if len(batch_items)>1 else a
    c_item = batch_items[2].name if len(batch_items)>2 else a
    exp = '2027-06-15'
    rows = [
        (a, 100, exp, "AB1"),
        (a, 50,  exp, "AB2"),
        (b_item, 30, '2027-12-31', "CD1"),
        (c_item, 20, '2028-03-01', "EF1"),
        (a, 70,  exp, "AB3"),
    ]
    for it, q, e, sbn in rows:
        pr.append("items", {"item": it, "qty": q, "uom": "Cái", "rate": 10000,
                              "expiry_date": e, "supplier_batch_no": sbn})
    pr.flags.ignore_permissions = True
    try:
        pr.insert()
        pr.submit()
        pr.reload()
        print(f"PR: {pr.name}")
        missing = []
        for r in pr.items:
            print(f"  row{r.idx}: item={r.item} exp={r.expiry_date} batch={r.batch_no or '❌ MISSING'}")
            if not r.batch_no: missing.append(r.idx)
        result = {"pr": pr.name, "missing_rows": missing, "total_rows": len(pr.items)}
        if missing:
            print(f"\n❌ BUG: rows {missing} missing batch!")
        return result
    except Exception as ex:
        return {"error": str(ex)[:500]}
