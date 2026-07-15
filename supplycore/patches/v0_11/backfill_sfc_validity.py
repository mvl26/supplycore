"""GĐ MVL — backfill valid_from/valid_to cho SC Sales Framework Contract cũ.

`valid_from`/`valid_to` chuyển sang reqd=1 (BRU-SFC-001 dựa vào 2 ngày này). Bản
ghi cũ tạo trước khi reqd có thể còn NULL → set default an toàn để không vỡ khi
mở/lưu lại: valid_from = ngày tạo HĐ, valid_to = valid_from + 1 năm.

Idempotent: chỉ chạm bản ghi đang NULL. Ghi thẳng DB (không load doc) để không
kích hoạt validate/submit-hook trên HĐ đã submit.

Rollback: set lại về NULL các bản ghi này (không khuyến nghị — sẽ vi phạm reqd).
"""

import frappe
from frappe.utils import add_years, getdate


def execute():
    rows = frappe.db.sql("""
        SELECT name, creation, valid_from, valid_to
        FROM `tabSC Sales Framework Contract`
        WHERE valid_from IS NULL OR valid_to IS NULL
    """, as_dict=True)
    n = 0
    for r in rows:
        vf = r.valid_from or getdate(r.creation)
        vt = r.valid_to or add_years(vf, 1)
        frappe.db.set_value("SC Sales Framework Contract", r.name,
                            {"valid_from": vf, "valid_to": vt},
                            update_modified=False)
        n += 1
    if n:
        frappe.db.commit()
    print(f"  ✓ backfill SFC validity: {n} hợp đồng khung")
