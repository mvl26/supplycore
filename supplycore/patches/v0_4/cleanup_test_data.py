"""QA-BUG-M11-01 + M5-01 + M5-02: Cleanup test data trong production.

Xóa hoặc disable:
  - SC Alert có title chứa '[TEST]' hoặc '%UAT%'
  - SC Batch test ('asdasd', 'TEST-BC-*')
  - Rename SC Batch có '/' trong batch_id thành dấu '-'

Idempotent. KHÔNG xóa data có sub-document (SLE) liên kết — chỉ disable.
"""

import frappe


def execute():
    # 1. Xóa SC Alert có [TEST] / UAT trong title
    test_alerts = frappe.db.sql("""
        SELECT name FROM `tabSC Alert`
        WHERE title LIKE '%[TEST]%' OR title LIKE '%UAT Alert%'
    """, as_dict=True)
    for a in test_alerts:
        frappe.db.delete("SC Alert", {"name": a.name})
    print(f"  ✓ Xóa {len(test_alerts)} test alert")

    # 2. Disable test batches (KHÔNG xóa nếu có SLE — chỉ disable + add note)
    test_batches = frappe.db.sql("""
        SELECT name FROM `tabSC Batch`
        WHERE batch_id LIKE 'asd%' OR batch_id LIKE 'TEST-%' OR batch_id = 'asdasd'
    """, as_dict=True)
    disabled_batch = 0
    for b in test_batches:
        # Check có SLE không
        has_sle = frappe.db.exists("SC Stock Ledger Entry", {"batch": b.name})
        if has_sle:
            frappe.db.set_value("SC Batch", b.name, {
                "disabled": 1,
                "blocked": 1,
                "block_reason": "Test data — disabled by QA-BUG-M5-01 cleanup",
            }, update_modified=False)
            disabled_batch += 1
        else:
            try:
                frappe.db.delete("SC Batch", {"name": b.name})
                disabled_batch += 1
            except Exception:
                pass
    print(f"  ✓ Disable/xóa {disabled_batch} test batch")

    # 3. Rename batch_id có '/' (lo/19/05/2026) → lo-19-05-2026.
    # SC Batch không allow_rename → fallback SQL trực tiếp (cập nhật name +
    # batch_id + cascade FK trong SLE/PR Item/etc.). Idempotent.
    slash_batches = frappe.db.sql("""
        SELECT name, batch_id FROM `tabSC Batch`
        WHERE batch_id LIKE '%/%' OR batch_id LIKE '%\\\\%'
    """, as_dict=True)
    renamed = 0
    for b in slash_batches:
        new_id = b.batch_id.replace("/", "-").replace("\\", "-")
        # Tránh trùng nếu new_id đã tồn tại
        if frappe.db.exists("SC Batch", new_id):
            new_id = f"{new_id}-RENAMED"
        try:
            # Update SC Batch chính
            frappe.db.sql("UPDATE `tabSC Batch` SET name=%s, batch_id=%s WHERE name=%s",
                          (new_id, new_id, b.name))
            # Cascade các foreign key thường gặp
            for table_field in [
                ("tabSC Stock Ledger Entry", "batch"),
                ("tabSC Purchase Receipt Item", "batch_no"),
                ("tabSC Stock Entry Item", "batch"),
                ("tabSC Transfer Request Item", "batch"),
                ("tabSC Quality Inspection", "batch"),
                ("tabSC Recall Notice", "batch_no"),
            ]:
                try:
                    frappe.db.sql(
                        f"UPDATE `{table_field[0]}` SET `{table_field[1]}`=%s WHERE `{table_field[1]}`=%s",
                        (new_id, b.name))
                except Exception:
                    pass  # Bảng không tồn tại
            print(f"  ✓ SQL rename batch '{b.batch_id}' → '{new_id}' + cascade FK")
            renamed += 1
        except Exception as e:
            print(f"  ✗ Lỗi rename '{b.batch_id}': {e}")

    frappe.db.commit()
    print(f"QA cleanup: alerts={len(test_alerts)}, batches={disabled_batch}, "
          f"renamed={renamed}")
