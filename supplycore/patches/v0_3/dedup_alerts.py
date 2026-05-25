"""BUG-012: Cleanup SC Alert duplicate hiện có.

Trước fix dedup (theo alert_type + reference + date), 2 rule khác nhau có
thể tạo alert cùng reference trong cùng ngày. Patch giữ alert có
modified mới nhất, mark resolved các alert cũ trùng với note "duplicate".

Idempotent: chạy lại không thay đổi gì nếu không còn duplicate.
"""

import frappe


def execute():
    # Tìm group duplicate theo (alert_type, ref_dt, ref_nm, DATE(alert_date))
    groups = frappe.db.sql("""
        SELECT alert_type, reference_doctype, reference_name,
               DATE(alert_date) AS d, COUNT(*) AS c
        FROM `tabSC Alert`
        WHERE resolved = 0 AND reference_name IS NOT NULL
        GROUP BY alert_type, reference_doctype, reference_name, DATE(alert_date)
        HAVING c > 1
    """, as_dict=True)

    resolved = 0
    for g in groups:
        # Sort theo modified DESC; giữ row[0], resolve row[1:]
        dups = frappe.db.sql("""
            SELECT name FROM `tabSC Alert`
            WHERE alert_type = %s AND reference_doctype = %s AND reference_name = %s
              AND DATE(alert_date) = %s AND resolved = 0
            ORDER BY modified DESC
        """, (g.alert_type, g.reference_doctype, g.reference_name, g.d))
        keep = dups[0][0]
        for (dup_name,) in dups[1:]:
            frappe.db.set_value("SC Alert", dup_name, {
                "resolved": 1,
                "resolution_action": "Acknowledged",
                "remarks": f"Auto-resolved duplicate (kept {keep}) — BUG-012",
            }, update_modified=False)
            resolved += 1
            print(f"  ↷ {dup_name} resolved duplicate of {keep}")

    frappe.db.commit()
    print(f"BUG-012 dedup: {len(groups)} groups, resolved {resolved} duplicates")
