"""Verify 4 kịch bản chống mất dòng + thiếu lô.

bench --site supplycore execute supplycore.tests._verify_bugs_fix.run
"""
import frappe
from frappe.utils import today, add_days


def _create_mr(items_data):
    mr = frappe.new_doc("SC Material Request")
    mr.transaction_date = today()
    mr.schedule_date = add_days(today(), 7)
    mr.request_type = "Purchase"
    mr.warehouse = "Kho Trung chuyển"
    for item_code, qty in items_data:
        item = frappe.get_doc("SC Item", item_code)
        mr.append("items", {
            "item": item_code, "qty": qty, "uom": item.uom or "Cái",
            "schedule_date": add_days(today(), 7),
        })
    mr.flags.ignore_permissions = True
    mr.insert()
    mr.submit()
    return mr


def _scenario_1_item():
    """1 item only."""
    fc_items = frappe.db.sql("""
        SELECT DISTINCT fci.item_code FROM `tabFC Item` fci
        JOIN `tabFramework Contract` fc ON fc.name = fci.parent
        WHERE fc.docstatus = 1 AND fc.status = 'Active' AND fci.remaining_qty > 10
        LIMIT 1
    """, as_dict=True)
    if not fc_items:
        return {"skip": "no FC item"}
    mr = _create_mr([(fc_items[0].item_code, 5)])
    mr.approve()
    res = mr.create_purchase_orders()
    summary = res["summary"]
    return {
        "scenario": "1 item",
        "mr": mr.name,
        "mr_items": summary["mr_items"],
        "grouped": summary["grouped_items"],
        "unmatched": summary["unmatched_items"],
        "all_accounted": summary["all_accounted"],
        "pass": summary["all_accounted"] and summary["mr_items"] == 1,
    }


def _scenario_5_items():
    """5 items khác nhau."""
    fc_items = frappe.db.sql("""
        SELECT DISTINCT fci.item_code FROM `tabFC Item` fci
        JOIN `tabFramework Contract` fc ON fc.name = fci.parent
        WHERE fc.docstatus = 1 AND fc.status = 'Active' AND fci.remaining_qty > 10
        LIMIT 5
    """, as_dict=True)
    if len(fc_items) < 5:
        return {"skip": f"only {len(fc_items)} FC items"}
    mr = _create_mr([(fi.item_code, 5) for fi in fc_items])
    mr.approve()
    res = mr.create_purchase_orders()
    s = res["summary"]
    return {
        "scenario": "5 items",
        "mr_items": s["mr_items"],
        "grouped": s["grouped_items"],
        "unmatched": s["unmatched_items"],
        "all_accounted": s["all_accounted"],
        "pos": res["created_pos"],
        "pass": s["all_accounted"] and s["mr_items"] == 5,
    }


def _scenario_dup_item():
    """3 rows cùng item (test cache anti-double-allocate)."""
    fc_items = frappe.db.sql("""
        SELECT DISTINCT fci.item_code, fci.remaining_qty FROM `tabFC Item` fci
        JOIN `tabFramework Contract` fc ON fc.name = fci.parent
        WHERE fc.docstatus = 1 AND fc.status = 'Active' AND fci.remaining_qty > 30
        ORDER BY fci.remaining_qty DESC LIMIT 1
    """, as_dict=True)
    if not fc_items:
        return {"skip": "no FC item with remain >30"}
    item_code = fc_items[0].item_code
    # 3 rows of same item, each 5 units (total 15, FC has 30+)
    mr = _create_mr([(item_code, 5), (item_code, 5), (item_code, 5)])
    mr.approve()
    res = mr.create_purchase_orders()
    s = res["summary"]
    return {
        "scenario": "3 dup items",
        "mr_items": s["mr_items"],
        "grouped": s["grouped_items"],
        "unmatched": s["unmatched_items"],
        "all_accounted": s["all_accounted"],
        "pass": s["all_accounted"] and s["mr_items"] == 3,
    }


def _scenario_pr_batch_5_rows():
    """PR 5 rows, 3 cùng item+expiry — test batch seq cache."""
    pr = frappe.new_doc("SC Purchase Receipt")
    pr.supplier = frappe.db.get_value("SC Supplier", {"disabled": 0}, "name")
    pr.posting_date = today()
    pr.to_warehouse = "Kho Trung chuyển"
    pr.qc_required = 0
    pr.no_po_reason = "Verify fix test"
    items = frappe.db.sql(
        "SELECT name FROM `tabSC Item` WHERE has_batch_no=1 AND disabled=0 LIMIT 3",
        as_dict=True)
    if len(items) < 3:
        return {"skip": "need 3 batch items"}
    a = items[0].name
    b = items[1].name
    c = items[2].name
    exp = '2027-09-15'
    rows = [
        (a, 100, exp, "AB1"),
        (a, 50,  exp, "AB2"),    # same item+exp as row 1
        (b, 30,  '2027-12-31', "CD1"),
        (c, 20,  '2028-03-01', "EF1"),
        (a, 70,  exp, "AB3"),    # 3rd row same item+exp
    ]
    for it, q, e, sbn in rows:
        pr.append("items", {"item": it, "qty": q, "uom": "Cái", "rate": 10000,
                              "expiry_date": e, "supplier_batch_no": sbn})
    pr.flags.ignore_permissions = True
    pr.insert()
    pr.submit()
    pr.reload()
    missing = [r.idx for r in pr.items if not r.batch_no]
    return {
        "scenario": "PR 5 rows, 3 cùng item+exp",
        "pr": pr.name,
        "items": len(pr.items),
        "missing_batch": missing,
        "pass": len(missing) == 0,
    }


def _scenario_pr_missing_expiry():
    """PR có row thiếu expiry → expect throw, không silent skip."""
    pr = frappe.new_doc("SC Purchase Receipt")
    pr.supplier = frappe.db.get_value("SC Supplier", {"disabled": 0}, "name")
    pr.posting_date = today()
    pr.to_warehouse = "Kho Trung chuyển"
    pr.qc_required = 0
    pr.no_po_reason = "Test missing expiry"
    items = frappe.db.sql(
        "SELECT name FROM `tabSC Item` WHERE has_batch_no=1 AND disabled=0 LIMIT 2",
        as_dict=True)
    pr.append("items", {"item": items[0].name, "qty": 10, "uom": "Cái",
                          "rate": 1000, "expiry_date": '2027-12-31'})
    pr.append("items", {"item": items[1].name, "qty": 20, "uom": "Cái",
                          "rate": 1000})  # NO expiry → should fail
    pr.flags.ignore_permissions = True
    pr.insert()
    try:
        pr.submit()
        return {"scenario": "PR thiếu expiry", "pass": False,
                "note": "Expected throw but submit succeeded"}
    except frappe.ValidationError as e:
        err = str(e)
        return {"scenario": "PR thiếu expiry", "pass": "SC-E-PR-MISSING-EXPIRY" in err,
                "note": err[:200]}


def run():
    results = []
    for fn in (_scenario_1_item, _scenario_5_items, _scenario_dup_item,
                _scenario_pr_batch_5_rows, _scenario_pr_missing_expiry):
        try:
            r = fn()
        except Exception as e:
            r = {"scenario": fn.__name__, "error": str(e)[:300]}
        results.append(r)
    passed = sum(1 for r in results if r.get("pass"))
    return {"passed": passed, "total": len(results), "results": results}
