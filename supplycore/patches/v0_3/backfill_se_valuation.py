"""BUG-003: Backfill valuation_rate cho Material Transfer/Issue rows = 0.

Trước fix _source_valuation (3-level fallback), nhiều SE rows submit với
valuation = 0 → SLE balance value sai → báo cáo tồn kho sai.

Patch này tìm SE rows valuation=0 đã submit, tra lại theo logic mới,
update cả row + SLE liên quan. Idempotent: bỏ qua rows đã có valuation > 0.
"""

import frappe
from frappe.utils import flt


def _resolve_rate(item, warehouse):
    """Lookup rate theo thứ tự: warehouse SLE → any-WH SLE → PR → PO."""
    queries = [
        ("""SELECT valuation_rate FROM `tabSC Stock Ledger Entry`
            WHERE item=%s AND warehouse=%s AND is_cancelled=0 AND valuation_rate>0
            ORDER BY posting_date DESC, creation DESC LIMIT 1""", (item, warehouse)),
        ("""SELECT valuation_rate FROM `tabSC Stock Ledger Entry`
            WHERE item=%s AND is_cancelled=0 AND valuation_rate>0
            ORDER BY posting_date DESC, creation DESC LIMIT 1""", (item,)),
        ("""SELECT pri.rate FROM `tabSC Purchase Receipt Item` pri
            JOIN `tabSC Purchase Receipt` pr ON pr.name=pri.parent
            WHERE pri.item=%s AND pr.docstatus=1 AND pri.rate>0
            ORDER BY pr.posting_date DESC LIMIT 1""", (item,)),
        ("""SELECT poi.rate FROM `tabSC Purchase Order Item` poi
            JOIN `tabSC Purchase Order` po ON po.name=poi.parent
            WHERE poi.item=%s AND po.docstatus=1 AND poi.rate>0
            ORDER BY po.transaction_date DESC LIMIT 1""", (item,)),
    ]
    for sql, params in queries:
        v = frappe.db.sql(sql, params)
        if v and flt(v[0][0]) > 0:
            return flt(v[0][0])
    return 0.0


def execute():
    rows = frappe.db.sql("""
        SELECT sei.name AS row_name, sei.parent AS se_name, sei.item, sei.qty,
               se.entry_type, se.from_warehouse, se.to_warehouse
        FROM `tabSC Stock Entry Item` sei
        JOIN `tabSC Stock Entry` se ON se.name = sei.parent
        WHERE sei.valuation_rate = 0
          AND se.entry_type IN ('Material Transfer', 'Material Issue')
          AND se.docstatus = 1
    """, as_dict=True)

    fixed = 0
    unresolved = 0
    for r in rows:
        rate = _resolve_rate(r.item, r.from_warehouse)
        if rate <= 0:
            unresolved += 1
            print(f"  ↷ unresolved {r.se_name} {r.item}: không có valuation history")
            continue
        amount = flt(r.qty) * rate
        # Update SE Item row
        frappe.db.set_value("SC Stock Entry Item", r.row_name, {
            "valuation_rate": rate, "amount": amount,
        }, update_modified=False)
        # Update SLE rows tương ứng (voucher_detail_no = row.name)
        sle_updated = frappe.db.sql("""
            UPDATE `tabSC Stock Ledger Entry`
            SET valuation_rate = %s,
                stock_value = balance_qty * %s,
                stock_value_difference = qty_change * %s
            WHERE voucher_type = 'SC Stock Entry' AND voucher_no = %s
              AND voucher_detail_no = %s AND is_cancelled = 0
        """, (rate, rate, rate, r.se_name, r.row_name))
        fixed += 1
        print(f"  ✓ {r.se_name} {r.item}: rate={rate:.2f}, amount={amount:.2f}")

    # Rollup parent total_value cho mọi SE Transfer/Issue có total_value=0
    # nhưng row.amount > 0 (idempotent — chỉ update SE thực sự stale)
    frappe.db.sql("""
        UPDATE `tabSC Stock Entry` se
        SET total_value = (
            SELECT COALESCE(SUM(amount), 0)
            FROM `tabSC Stock Entry Item` sei
            WHERE sei.parent = se.name
        )
        WHERE se.docstatus = 1
          AND se.entry_type IN ('Material Transfer', 'Material Issue')
          AND se.total_value = 0
          AND EXISTS (
              SELECT 1 FROM `tabSC Stock Entry Item` sei
              WHERE sei.parent = se.name AND sei.amount > 0
          )
    """)
    frappe.db.commit()
    print(f"BUG-003 backfill: fixed={fixed}, unresolved={unresolved}")
