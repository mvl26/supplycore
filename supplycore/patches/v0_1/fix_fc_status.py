"""Patch: sửa Framework Contract đã submit nhưng status còn 'Draft' do bug logic cũ."""

import frappe


def execute():
    frappe.db.sql("""
        UPDATE `tabFramework Contract`
        SET status = CASE
            WHEN docstatus = 2 THEN 'Terminated'
            WHEN docstatus = 1 AND DATE(valid_to) < CURDATE() THEN 'Expired'
            WHEN docstatus = 1 THEN 'Active'
            ELSE 'Draft'
        END
        WHERE docstatus IN (1, 2)
          AND status NOT IN ('Active', 'Expired', 'Terminated')
    """)
    frappe.db.commit()
