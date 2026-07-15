"""BUG-008: Backfill last_name/middle_name cho user có first_name = full_name.

Trước fix users.create_user, code set first_name = parts[0] only → full_name
tự compute chỉ còn first word. Patch tách lại từ first_name nếu chứa space,
hoặc combine first_name nếu user đã có last_name riêng.

Idempotent: bỏ qua user đã có last_name hợp lý.
"""

import frappe


def execute():
    users = frappe.db.sql("""
        SELECT name, first_name, middle_name, last_name, full_name
        FROM `tabUser`
        WHERE enabled = 1
          AND (last_name IS NULL OR last_name = '')
          AND first_name IS NOT NULL
          AND first_name LIKE '% %'
    """, as_dict=True)

    fixed = 0
    for u in users:
        # first_name dạng "Nguyễn Thị Thu Hương" → split
        parts = (u.first_name or "").strip().split()
        if len(parts) < 2:
            continue
        if len(parts) >= 3:
            first, middle, last = parts[0], " ".join(parts[1:-1]), parts[-1]
        else:
            first, middle, last = parts[0], "", parts[1]
        frappe.db.set_value("User", u.name, {
            "first_name": first,
            "middle_name": middle or None,
            "last_name": last,
        }, update_modified=False)
        fixed += 1
        print(f"  ✓ {u.name}: {first}|{middle}|{last}")

    frappe.db.commit()
    # Reload Frappe sẽ tự re-compute full_name lần lưu kế. Force tính lại:
    if fixed > 0:
        frappe.db.sql("""
            UPDATE `tabUser`
            SET full_name = TRIM(CONCAT_WS(' ',
                NULLIF(first_name,''), NULLIF(middle_name,''), NULLIF(last_name,'')))
            WHERE last_name IS NOT NULL AND last_name != ''
        """)
        frappe.db.commit()
    print(f"BUG-008 backfill: fixed={fixed}")
