"""PERF-001: Thêm composite + secondary indexes cho các bảng query nóng.

Bug report yêu cầu DB index cho item_code, batch_no, warehouse, posting_date.
Đa số single-column index đã có qua field `search_index: 1` trong JSON.
Patch này bổ sung composite + index còn thiếu để tăng tốc:
  - Stock Balance report (warehouse + item + posting_date)
  - FEFO query (item + expiry_date + qty_after_transaction)
  - PO / MR list filter (transaction_date + status + supplier)
"""

import frappe


COMPOSITE_INDEXES = [
    # SC Stock Ledger Entry — stock balance, item ledger
    ("tabSC Stock Ledger Entry", "idx_sle_wh_posting", ["warehouse", "posting_date"]),
    ("tabSC Stock Ledger Entry", "idx_sle_item_wh_posting", ["item", "warehouse", "posting_date"]),
    ("tabSC Stock Ledger Entry", "idx_sle_batch_posting", ["batch", "posting_date"]),
    # SC Batch — FEFO query
    ("tabSC Batch", "idx_batch_item_expiry", ["item", "expiry_date"]),
    # SC Material Request — list filter & dashboard count
    ("tabSC Material Request", "idx_mr_date_status", ["transaction_date", "status"]),
    ("tabSC Material Request", "idx_mr_warehouse", ["warehouse"]),
    # SC Purchase Order — list filter
    ("tabSC Purchase Order", "idx_po_date_supplier", ["transaction_date", "supplier"]),
    ("tabSC Purchase Order", "idx_po_status_docstatus", ["status", "docstatus"]),
    # SC Purchase Receipt — list + dashboard
    ("tabSC Purchase Receipt", "idx_pr_posting_supplier", ["posting_date", "supplier"]),
    ("tabSC Purchase Receipt", "idx_pr_po", ["purchase_order"]),
    # SC Stock Entry — list + dashboard
    ("tabSC Stock Entry", "idx_se_posting_type", ["posting_date", "stock_entry_type"]),
    ("tabSC Stock Entry", "idx_se_from_wh", ["from_warehouse"]),
    ("tabSC Stock Entry", "idx_se_to_wh", ["to_warehouse"]),
]


def index_exists(table, name):
    rows = frappe.db.sql(
        f"SHOW INDEX FROM `{table}` WHERE Key_name=%s", (name,), as_dict=True
    )
    return bool(rows)


def table_exists(table):
    rows = frappe.db.sql(
        "SELECT TABLE_NAME FROM information_schema.TABLES "
        "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME=%s",
        (table,),
    )
    return bool(rows)


def column_exists(table, column):
    rows = frappe.db.sql(
        "SELECT COLUMN_NAME FROM information_schema.COLUMNS "
        "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME=%s AND COLUMN_NAME=%s",
        (table, column),
    )
    return bool(rows)


def execute():
    created = 0
    skipped = 0
    for table, idx_name, cols in COMPOSITE_INDEXES:
        if not table_exists(table):
            print(f"  ↷ skip {table} (table not found)")
            skipped += 1
            continue
        missing_cols = [c for c in cols if not column_exists(table, c)]
        if missing_cols:
            print(f"  ↷ skip {idx_name} (missing cols: {missing_cols})")
            skipped += 1
            continue
        if index_exists(table, idx_name):
            skipped += 1
            continue
        cols_sql = ", ".join(f"`{c}`" for c in cols)
        try:
            frappe.db.sql(f"CREATE INDEX `{idx_name}` ON `{table}` ({cols_sql})")
            print(f"  ✓ {idx_name} ON {table} ({', '.join(cols)})")
            created += 1
        except Exception as e:
            print(f"  ✗ {idx_name}: {e}")
    frappe.db.commit()
    print(f"PERF-001: created={created}, skipped={skipped}")
