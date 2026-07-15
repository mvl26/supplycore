"""Patch UC-10: seed default global QC Checklist Template với 5 tiêu chí theo spec."""

import frappe


def execute():
    title = "Default Hospital Supply QC"
    if frappe.db.exists("QC Checklist Template", {"title": title}):
        return
    tpl = frappe.new_doc("QC Checklist Template")
    tpl.title = title
    tpl.is_default_for_group = 0
    tpl.enabled = 1
    tpl.description = "Default template UC-10 — 5 tiêu chí QC cơ bản cho VT bệnh viện"
    criteria = [
        ("Bao bì nguyên vẹn", "Không rách, hỏng, bóp méo", 1),
        ("Nhãn mác đúng", "Tên VT, số lô, hạn dùng đầy đủ rõ ràng", 1),
        ("Hạn dùng ≥6 tháng", "Hạn dùng còn ≥180 ngày kể từ ngày nhập", 1),
        ("Số lô khớp chứng từ", "Số lô trên hàng = số lô trên phiếu giao", 1),
        ("Quy cách đúng hợp đồng", "Đúng đặc tả + đơn vị + đóng gói theo PO/FC", 0),
    ]
    for i, (n, exp, crit) in enumerate(criteria, 1):
        tpl.append("criteria", {
            "criterion_name": n,
            "expected_value": exp,
            "is_critical": crit,
            "sequence": i,
        })
    tpl.flags.ignore_permissions = True
    tpl.insert()
