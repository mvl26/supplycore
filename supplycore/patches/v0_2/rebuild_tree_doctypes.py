"""Patch (BUG-001): thêm nested-set fields cho SC Item Group + SC GL Account.

Cùng lỗi với SC Warehouse: doctype tree (is_tree=1, controller NestedSet)
nhưng JSON thiếu lft/rgt/old_parent → tạo bản ghi lỗi
"'SC...' object has no attribute 'lft'". Sau khi schema sync thêm cột,
rebuild nested-set cho các bản ghi đã tồn tại.
"""

import frappe
from frappe.utils.nestedset import rebuild_tree

TREES = [
    ("SC Item Group", "parent_group"),
    ("SC GL Account", "parent_account"),
]


def execute():
    for doctype, parent_field in TREES:
        frappe.reload_doc("supplycore", "doctype", frappe.scrub(doctype))
        rebuild_tree(doctype, parent_field)
    frappe.db.commit()
