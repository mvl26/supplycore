"""Patch: thêm nested-set fields (lft/rgt/old_parent) cho SC Warehouse + rebuild cây.

SC Warehouse là doctype tree (is_tree=1, controller NestedSet) nhưng JSON
thiếu field lft/rgt/old_parent → tạo kho lỗi
'SCWarehouse object has no attribute lft'. Sau khi schema sync thêm cột,
rebuild lại nested-set cho các kho đã tồn tại.
"""

import frappe
from frappe.utils.nestedset import rebuild_tree


def execute():
    # Đảm bảo doctype (đã có lft/rgt/old_parent) được sync xuống DB
    frappe.reload_doc("supplycore", "doctype", "sc_warehouse")
    # Tính lại lft/rgt cho toàn bộ cây kho theo parent_warehouse
    rebuild_tree("SC Warehouse", "parent_warehouse")
    frappe.db.commit()
