"""GĐ2 M7 Sales — seed SC GL Account 511 (Doanh thu bán hàng).

Chart of accounts hiện có (xem supplycore/setup/seed_master_data.py::GL_ACCOUNTS)
chưa có nhóm gốc "Income" (root_type Income) nào — chỉ có Asset/Liability/Expense.
Task 1 GĐ2 M7 Sales cần TK doanh thu để ghi nhận GL khi phát hành SC Sales Invoice.

Idempotent — chạy lại không tạo trùng (frappe.db.exists check trước insert).
"""

import frappe


def execute():
    if frappe.db.exists("SC GL Account", "511"):
        return

    d = frappe.new_doc("SC GL Account")
    d.account_code = "511"
    d.account_name = "Doanh thu bán hàng"
    d.account_type = "Income"
    d.parent_account = None
    d.is_group = 0
    d.root_type = "Income"
    d.vas_reference = "TT200"
    d.flags.ignore_permissions = True
    try:
        d.insert()
        frappe.db.commit()
        print("  ✓ SC GL Account 511 (Doanh thu bán hàng) created")
    except Exception as e:
        frappe.log_error(message=f"GL Account 511 failed: {e}", title="Seed sales GL accounts")
