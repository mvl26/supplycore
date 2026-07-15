"""Rà soát list view — kiểm thử tầng dữ liệu nuôi bảng SPA (L1/L2/L3).

L2: mỗi doctype có field TÊN (fetch) → get_list trả về tên (không trống) cho bản
    ghi có link, và tên KHÁC mã (không phải mã thô).
L3: tìm theo MÃ đầy đủ và theo TÊN đều ra đúng bản ghi (or_filters name/name-field).

Chạy: bench --site ... execute supplycore.tests.listview_display_test.run
"""

import re
import frappe

CODE_RE = re.compile(r"^(SC-)?[A-Z]{2,}-\d{4}-\d+$")

# doctype, name_field, link_field
CASES = [
    ("SC Sales Order", "customer_name", "customer"),
    ("SC Delivery Note", "customer_name", "customer"),
    ("SC Sales Invoice", "customer_name", "customer"),
    ("SC Acceptance Record", "customer_name", "customer"),
    ("SC Sales Receipt", "customer_name", "customer"),
    ("SC Sales Framework Contract", "customer_name", "customer"),
    ("SC Purchase Order", "supplier_name", "supplier"),
    ("SC Purchase Receipt", "supplier_name", "supplier"),
    ("SC Purchase Invoice", "supplier_name", "supplier"),
    ("SC Payment Entry", "supplier_name", "supplier"),
    ("SC Quality Inspection", "supplier_name", "supplier"),
    ("SC Quality Inspection", "item_name", "item"),
    ("SC Stock Ledger Entry", "item_name", "item"),
]


def _one_with_link(dt, linkf):
    rows = frappe.get_list(dt, filters={linkf: ["is", "set"]},
                           fields=["name", linkf], limit=1, ignore_permissions=True)
    return rows[0] if rows else None


def test_l2_name_resolves():
    """L2: field tên có cột trong DB, get_list trả tên (không trống, khác mã)."""
    bad = []
    for dt, namef, linkf in CASES:
        if not frappe.get_meta(dt).has_field(namef):
            bad.append(f"{dt}.{namef} MISSING field"); continue
        row = _one_with_link(dt, linkf)
        if not row:
            continue  # chưa có dữ liệu — bỏ qua (không phải lỗi)
        r = frappe.get_list(dt, filters={"name": row["name"]},
                            fields=["name", namef], limit=1, ignore_permissions=True)[0]
        val = (r.get(namef) or "").strip()
        if not val:
            bad.append(f"{dt}.{namef} TRỐNG cho {row['name']}")
        elif CODE_RE.match(val):
            bad.append(f"{dt}.{namef} là MÃ THÔ ({val}) cho {row['name']}")
    return {"pass": not bad, "msg": "OK tên resolve đúng" if not bad else "; ".join(bad)}


def test_l3_search_by_name_and_code():
    """L3: tìm theo mã đầy đủ VÀ theo tên đều ra đúng bản ghi."""
    bad = []
    for dt, namef, linkf in CASES:
        row = _one_with_link(dt, linkf)
        if not row:
            continue
        name = row["name"]
        nameval = frappe.db.get_value(dt, name, namef)
        if not nameval:
            continue
        # tìm theo mã đầy đủ
        by_code = frappe.get_list(dt, or_filters=[["name", "like", f"%{name}%"]],
                                  fields=["name"], limit=5, ignore_permissions=True)
        if not any(x["name"] == name for x in by_code):
            bad.append(f"{dt}: tìm theo MÃ {name} không ra")
        # tìm theo tên (một phần)
        token = str(nameval)[:6]
        by_name = frappe.get_list(dt, or_filters=[[namef, "like", f"%{token}%"]],
                                  fields=["name"], limit=20, ignore_permissions=True)
        if not any(x["name"] == name for x in by_name):
            bad.append(f"{dt}: tìm theo TÊN '{token}' không ra {name}")
    return {"pass": not bad, "msg": "OK search theo mã & tên" if not bad else "; ".join(bad)}


TESTS = [test_l2_name_resolves, test_l3_search_by_name_and_code]


def run():
    results, passed = [], 0
    for t in TESTS:
        try:
            r = t()
        except Exception as e:
            r = {"pass": False, "msg": f"EXCEPTION: {repr(e)[:200]}"}
        results.append(r)
        passed += 1 if r.get("pass") else 0
        print(f"  {'✓' if r.get('pass') else '✗'} {t.__name__}: {r.get('msg')}")
    print(f"listview_display_test: {passed}/{len(TESTS)}")
    return {"passed": passed, "total": len(TESTS), "results": results}
