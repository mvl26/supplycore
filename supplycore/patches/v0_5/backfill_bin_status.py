"""QAv3-BUG-BIN-05: Backfill Bin Location.status + current_qty + occupancy_pct.

Trước khi thêm _refresh_bin_status hook, bin.status không update mỗi SLE.
Patch này dùng helper _refresh_bin_status cho mọi bin có ≥1 SLE.

Idempotent.
"""

import frappe


def execute():
    from supplycore.supplycore.doctype.sc_stock_ledger_entry.sc_stock_ledger_entry import _refresh_bin_status
    bins = frappe.db.sql("""
        SELECT DISTINCT bin_location FROM `tabSC Stock Ledger Entry`
        WHERE bin_location IS NOT NULL AND bin_location != ''
          AND is_cancelled = 0
    """, as_dict=True)
    fixed = 0
    for b in bins:
        try:
            _refresh_bin_status(b.bin_location)
            fixed += 1
        except Exception as e:
            print(f"  ✗ {b.bin_location}: {e}")
    frappe.db.commit()
    print(f"QAv3-BUG-BIN-05 backfill: refreshed {fixed} bin status")
