"""QA-BUG-M1-02: Backfill FC remaining_value <= 0 → status='Exhausted'.

Logic _compute_active_or_expired đã cập nhật trả 'Exhausted' khi
remaining <= 0. Patch này áp dụng vào FC đã submitted hiện đang 'Active'
nhưng đã hết hạn mức.

Idempotent.
"""

import frappe
from frappe.utils import flt


def execute():
    rows = frappe.db.sql("""
        SELECT name, total_value, remaining_value FROM `tabFramework Contract`
        WHERE docstatus = 1 AND status = 'Active'
          AND total_value > 0 AND remaining_value <= 0
    """, as_dict=True)
    for r in rows:
        frappe.db.set_value("Framework Contract", r.name, "status", "Exhausted",
                            update_modified=False)
        print(f"  ✓ {r.name}: Active → Exhausted (remaining={r.remaining_value})")
    frappe.db.commit()
    print(f"QA-BUG-M1-02 backfill: {len(rows)} FC chuyển Exhausted")
