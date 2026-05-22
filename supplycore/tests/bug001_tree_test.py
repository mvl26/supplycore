"""Test BUG-001 — Hierarchical CRUD trên các DocType cấu trúc cây (NestedSet).

SC Warehouse / SC Item Group / SC GL Account là doctype tree. Test tạo node
cha (is_group) + node con, kiểm tra lft/rgt được tính đúng — chặn tái xuất
lỗi "'SC...' object has no attribute 'lft'".

Run all:        bench --site supplycore execute supplycore.tests.bug001_tree_test.run
Run individual: bench --site supplycore execute supplycore.tests.bug001_tree_test.test_warehouse_tree
"""

import frappe
from frappe.utils import random_string

# Mỗi tree doctype: parent field + hàm dựng các field bắt buộc theo tên node
TREES = [
    {"doctype": "SC Warehouse", "parent_field": "parent_warehouse",
     "fields": lambda nm: {"warehouse_name": nm, "warehouse_type": "Main"}},
    {"doctype": "SC Item Group", "parent_field": "parent_group",
     "fields": lambda nm: {"group_name": nm}},
    {"doctype": "SC GL Account", "parent_field": "parent_account",
     "fields": lambda nm: {"account_code": nm, "account_name": nm, "root_type": "Asset"}},
]


def _make(spec, name, is_group, parent=None):
    doc = frappe.new_doc(spec["doctype"])
    for k, v in spec["fields"](name).items():
        doc.set(k, v)
    doc.is_group = 1 if is_group else 0
    if parent:
        doc.set(spec["parent_field"], parent)
    doc.flags.ignore_permissions = True
    doc.insert()
    return doc


def _check_tree(spec):
    """Tạo cha (group) + con → kiểm nested-set invariant → dọn dẹp."""
    dt = spec["doctype"]
    sfx = random_string(6)
    parent = _make(spec, f"BUG001-P-{sfx}", is_group=True)
    child = _make(spec, f"BUG001-C-{sfx}", is_group=False, parent=parent.name)
    parent.reload()
    child.reload()

    assert parent.lft is not None and parent.rgt is not None, f"{dt}: node cha thiếu lft/rgt"
    assert child.lft is not None and child.rgt is not None, f"{dt}: node con thiếu lft/rgt"
    # Con phải nằm gọn trong khoảng [lft, rgt] của cha
    assert parent.lft < child.lft < child.rgt < parent.rgt, (
        f"{dt}: nested-set sai — cha[{parent.lft},{parent.rgt}] con[{child.lft},{child.rgt}]")

    frappe.delete_doc(dt, child.name, force=True, ignore_permissions=True)
    frappe.delete_doc(dt, parent.name, force=True, ignore_permissions=True)
    return f"{dt}: cha[{parent.lft},{parent.rgt}] ⊃ con[{child.lft},{child.rgt}]"


def test_warehouse_tree():
    print("✓", _check_tree(TREES[0]))


def test_item_group_tree():
    print("✓", _check_tree(TREES[1]))


def test_gl_account_tree():
    print("✓", _check_tree(TREES[2]))


def run():
    results = []
    for spec in TREES:
        try:
            results.append("✓ " + _check_tree(spec))
        except Exception as e:
            results.append(f"✗ {spec['doctype']}: {e}")
    frappe.db.rollback()
    for r in results:
        print(r)
    if any(r.startswith("✗") for r in results):
        frappe.throw("BUG-001 tree CRUD test FAILED")
    print("BUG-001 OK — hierarchical CRUD chạy được trên mọi tree doctype")
