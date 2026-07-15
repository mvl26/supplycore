"""GĐ MVL — HĐ khung BÁN bổ sung trường giống HĐ khung MUA.

Thêm: contract_number (Số HĐ, reqd), contract_date (Ngày ký, reqd), customer_name,
điều khoản TT/giao hàng, theo dõi giá trị (used/committed/remaining), thanh lý, đính kèm.

Backfill bản ghi cũ để không vỡ khi sửa/amend (2 trường mới reqd):
  - contract_number = name (nếu trống)
  - contract_date   = valid_from hoặc ngày tạo
  - used/committed/remaining = tính lại từ sold_qty + SO 'Chờ duyệt'
Idempotent. Rollback: xoá cột mới (thường không cần).
"""

import frappe
from frappe.utils import flt


def execute():
    frappe.reload_doc("m7_sales", "doctype", "sc_sales_framework_contract")

    rows = frappe.get_all("SC Sales Framework Contract",
                          fields=["name", "valid_from", "creation", "contract_number",
                                  "contract_date", "customer", "total_value"])
    for r in rows:
        patch = {}
        if not r.contract_number:
            patch["contract_number"] = r.name
        if not r.contract_date:
            patch["contract_date"] = r.valid_from or str(r.creation)[:10]
        cname = frappe.db.get_value("SC Customer", r.customer, "customer_name")
        if cname:
            patch["customer_name"] = cname
        if patch:
            frappe.db.set_value("SC Sales Framework Contract", r.name, patch,
                                update_modified=False)

    # Tính lại theo dõi giá trị cho mọi HĐ (dùng logic canonical trong doctype).
    has_so = frappe.db.table_exists("SC Sales Order")
    for r in rows:
        doc = frappe.get_doc("SC Sales Framework Contract", r.name)
        used = sum(flt(it.sold_qty) * flt(it.unit_price) for it in doc.items)
        committed = doc._compute_committed_value() if has_so else 0
        frappe.db.set_value("SC Sales Framework Contract", r.name, {
            "used_value": used,
            "committed_value": committed,
            "remaining_value": flt(doc.total_value) - used - committed,
        }, update_modified=False)

    frappe.db.commit()
    print(f"  ✓ SFC: backfill {len(rows)} hợp đồng khung bán (số HĐ / ngày ký / giá trị)")
