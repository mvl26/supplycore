"""QAv3-BUG-M11-UAT + M1-05 + M4-01: Cleanup test data còn lại.

QA v3 phát hiện thêm:
  - 18 SC Alert Rule UAT/SMOKE đang active (Daily) → tạo cảnh báo giả mỗi ngày
  - 7+ FC "TEST-LOG-xxx", "TEST-EDIT-xxx" trong production
  - Warehouse "kho tam", "kho 1" — tên không chuẩn

Cleanup:
  - Disable + rename UAT/SMOKE rule (KHÔNG xóa nếu có SC Alert children)
  - Cancel + rename TEST FC (KHÔNG xóa vì có thể có RO/PO history)
  - Disable test warehouse (giữ vì có SLE/Bin children)

Idempotent.
"""

import frappe


def execute():
    # 1. Disable UAT/SMOKE Alert Rules
    rules = frappe.db.sql("""
        SELECT name FROM `tabSC Alert Rule`
        WHERE name LIKE '%UAT%' OR name LIKE '%SMOKE%'
           OR COALESCE(title,'') LIKE '%UAT%' OR COALESCE(title,'') LIKE '%SMOKE%'
           OR COALESCE(title,'') LIKE '[TEST]%'
    """, as_dict=True)
    disabled_rules = 0
    for r in rules:
        # Disable (set enabled=0) — không xóa vì có thể có SC Alert children
        frappe.db.set_value("SC Alert Rule", r.name, "enabled", 0, update_modified=False)
        disabled_rules += 1
    print(f"  ✓ Disable {disabled_rules} UAT/SMOKE Alert Rules")

    # 2. Cancel + flag TEST FC
    fcs = frappe.db.sql("""
        SELECT name, contract_number, docstatus, status FROM `tabFramework Contract`
        WHERE contract_number LIKE 'TEST-%' OR contract_number LIKE '%-TEST%'
           OR contract_number LIKE 'TEST-LOG%' OR contract_number LIKE 'TEST-EDIT%'
    """, as_dict=True)
    cancelled_fcs = 0
    for f in fcs:
        # Đổi status sang Terminated nếu chưa cancel — đánh dấu test data
        if f.status != "Terminated":
            frappe.db.set_value("Framework Contract", f.name, {
                "status": "Terminated",
                "termination_reason": "Test data cleanup — QAv3-BUG-M1-05",
            }, update_modified=False)
            cancelled_fcs += 1
    print(f"  ✓ Terminate {cancelled_fcs} test FC")

    # 3. Disable test warehouses (giữ vì có thể có SLE)
    whs = frappe.db.sql("""
        SELECT name FROM `tabSC Warehouse`
        WHERE LOWER(warehouse_name) IN ('kho tam', 'kho 1', 'kho 2', 'kho test', 'test')
           OR warehouse_name LIKE 'test%' OR warehouse_name LIKE 'Test%'
    """, as_dict=True)
    disabled_whs = 0
    for w in whs:
        # Check không phải kho gốc (parent_warehouse)
        has_children = frappe.db.exists("SC Warehouse", {"parent_warehouse": w.name})
        if has_children:
            print(f"  ↷ skip {w.name} (có warehouse con)")
            continue
        frappe.db.set_value("SC Warehouse", w.name, "disabled", 1, update_modified=False)
        disabled_whs += 1
        print(f"  ✓ Disable warehouse '{w.name}'")
    print(f"QAv3 cleanup: rules={disabled_rules}, fcs={cancelled_fcs}, warehouses={disabled_whs}")
    frappe.db.commit()
