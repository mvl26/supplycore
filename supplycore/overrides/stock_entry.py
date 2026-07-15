"""Hook vào ERPNext Stock Entry — M4 bin suggest + M5 FEFO."""

import frappe
from frappe import _
from frappe.utils import flt, getdate, today


# ---------------------------------------------------------------------------
# validate hook (M4 + M5)
# ---------------------------------------------------------------------------
def enforce_fefo(doc, method=None):
    _suggest_bin_for_items(doc)
    _validate_bin_consistency(doc)
    _enforce_fefo_rules(doc)


# ---------------------------------------------------------------------------
# M4 helpers — bin suggest + consistency
# ---------------------------------------------------------------------------
def _suggest_bin_for_items(doc):
    if doc.docstatus != 0:
        return
    for row in doc.items:
        if not row.get("sc_target_bin") and row.get("t_warehouse") and row.item_code:
            default_bin = frappe.db.get_value("Item", row.item_code, "sc_default_bin_location")
            if default_bin:
                bin_wh = frappe.db.get_value("Bin Location", default_bin, "warehouse")
                if bin_wh == row.t_warehouse:
                    row.sc_target_bin = default_bin


def _validate_bin_consistency(doc):
    for row in doc.items:
        if row.get("sc_source_bin"):
            bin_doc = frappe.db.get_value("Bin Location", row.sc_source_bin,
                                            ["warehouse", "is_quarantine", "enabled"], as_dict=True)
            if not bin_doc:
                continue
            if row.s_warehouse and bin_doc.warehouse != row.s_warehouse:
                frappe.throw(_("Source bin {0} không thuộc kho {1}")
                             .format(row.sc_source_bin, row.s_warehouse))
            if bin_doc.is_quarantine:
                frappe.msgprint(_("Source bin {0} là quarantine — chỉ xuất khi đã pass QC")
                                 .format(row.sc_source_bin), indicator="orange", alert=True)
            if not bin_doc.enabled:
                frappe.throw(_("Source bin {0} đã disable").format(row.sc_source_bin))

        if row.get("sc_target_bin"):
            bin_doc = frappe.db.get_value("Bin Location", row.sc_target_bin,
                                            ["warehouse", "enabled"], as_dict=True)
            if not bin_doc:
                continue
            if row.t_warehouse and bin_doc.warehouse != row.t_warehouse:
                frappe.throw(_("Target bin {0} không thuộc kho {1}")
                             .format(row.sc_target_bin, row.t_warehouse))
            if not bin_doc.enabled:
                frappe.throw(_("Target bin {0} đã disable").format(row.sc_target_bin))


# ---------------------------------------------------------------------------
# M5 — FEFO enforcement
# ---------------------------------------------------------------------------
ISSUE_TYPES = (
    "Material Issue",
    "Material Transfer",
    "Material Transfer for Manufacture",
    "Send to Subcontractor",
)


def _enforce_fefo_rules(doc):
    """Block expired / blocked batches + enforce FEFO order on outgoing stock."""
    if doc.docstatus != 0:
        return
    if doc.stock_entry_type not in ISSUE_TYPES:
        return

    today_d = getdate(today())
    # Aggregate user-selected batches per (item, source_warehouse)
    selected_per_item_wh = {}
    for row in doc.items:
        if row.batch_no and row.s_warehouse and row.item_code:
            key = (row.item_code, row.s_warehouse)
            selected_per_item_wh.setdefault(key, set()).add(row.batch_no)

    for row in doc.items:
        if not (row.s_warehouse and row.batch_no and row.item_code):
            continue

        batch = frappe.db.get_value("Batch", row.batch_no,
                                     ["expiry_date", "sc_blocked", "sc_block_reason"],
                                     as_dict=True)
        if not batch:
            continue

        # 1. Block expired
        if batch.expiry_date and getdate(batch.expiry_date) < today_d:
            frappe.throw(_("Batch {0} đã hết hạn ngày {1}")
                         .format(row.batch_no, batch.expiry_date),
                         title="SC-E003 EXPIRY_TOO_CLOSE")

        # 2. Block recalled / blocked batches
        if batch.sc_blocked:
            frappe.throw(_("Batch {0} đang bị block: {1}")
                         .format(row.batch_no, batch.sc_block_reason or "—"),
                         title="SC-E008 BATCH_RECALLED")

        # 3. FEFO check — có batch nào hết hạn sớm hơn còn hàng + chưa chọn?
        if not batch.expiry_date:
            continue

        used_in_se = selected_per_item_wh.get((row.item_code, row.s_warehouse), set())

        earlier = frappe.db.sql("""
            SELECT b.name AS batch_no, b.expiry_date,
                   COALESCE(legacy.qty, 0) + COALESCE(bundle.qty, 0) AS qty
            FROM `tabBatch` b
            LEFT JOIN (
                SELECT batch_no, SUM(actual_qty) AS qty
                FROM `tabStock Ledger Entry`
                WHERE warehouse = %(wh)s AND is_cancelled = 0 AND batch_no IS NOT NULL
                GROUP BY batch_no
            ) legacy ON legacy.batch_no = b.name
            LEFT JOIN (
                SELECT sabe.batch_no, SUM(sabe.qty) AS qty
                FROM `tabSerial and Batch Entry` sabe
                JOIN `tabSerial and Batch Bundle` sabb ON sabb.name = sabe.parent
                WHERE sabb.item_code = %(item)s AND sabb.warehouse = %(wh)s AND sabb.docstatus = 1
                GROUP BY sabe.batch_no
            ) bundle ON bundle.batch_no = b.name
            WHERE b.item = %(item)s
              AND b.disabled = 0
              AND COALESCE(b.sc_blocked, 0) = 0
              AND b.name != %(curr)s
              AND b.expiry_date IS NOT NULL
              AND b.expiry_date < %(curr_exp)s
              AND b.expiry_date >= CURDATE()
            HAVING qty > 0
            ORDER BY b.expiry_date ASC LIMIT 5
        """, {"wh": row.s_warehouse, "item": row.item_code,
              "curr": row.batch_no, "curr_exp": batch.expiry_date}, as_dict=True)

        # Lọc bỏ batch đã được dùng trong các row khác của SE này
        unused_earlier = [b for b in earlier if b.batch_no not in used_in_se]

        if not unused_earlier:
            continue  # OK — user dùng FEFO đúng

        # Có vi phạm — kiểm tra override flag + reason
        if not row.get("sc_fefo_override"):
            strict = _is_fefo_strict(row.s_warehouse, row.item_code)
            msg = _("Item {0} batch {1} (hạn {2}): còn lô hết hạn sớm hơn — {3}").format(
                row.item_code, row.batch_no, batch.expiry_date,
                ", ".join(f"{b.batch_no} (hạn {b.expiry_date})" for b in unused_earlier[:3])
            )
            if strict:
                frappe.throw(msg + "\n\n" + _("Cần tick 'FEFO Override' và ghi lý do."),
                             title="SC-E001 FEFO_OVERRIDE")
            else:
                frappe.msgprint(msg, indicator="orange", alert=True)
        elif not row.get("sc_fefo_override_reason"):
            frappe.throw(_("Override FEFO cho batch {0} cần ghi lý do (sc_fefo_override_reason)")
                         .format(row.batch_no), title="SC-E001 FEFO_OVERRIDE")
        else:
            # Có override + lý do — log audit (M5 spec yêu cầu Manager approval)
            frappe.msgprint(_("FEFO override cho batch {0}: '{1}' — đã ghi nhận audit")
                             .format(row.batch_no, row.sc_fefo_override_reason),
                             indicator="orange", alert=True)


def _is_fefo_strict(warehouse: str, item_code: str) -> bool:
    """Resolve fefo_strict_mode theo FEFO Picker Rule → fallback Settings."""
    item_group = frappe.db.get_value("Item", item_code, "item_group")
    rules = frappe.db.sql("""
        SELECT strict_mode, priority
        FROM `tabFEFO Picker Rule`
        WHERE enabled = 1
          AND (warehouse IS NULL OR warehouse = '' OR warehouse = %(wh)s)
          AND (item_group IS NULL OR item_group = '' OR item_group = %(ig)s)
        ORDER BY priority DESC LIMIT 1
    """, {"wh": warehouse, "ig": item_group}, as_dict=True)
    if rules:
        return bool(rules[0].strict_mode)
    # Fallback SupplyCore Settings — thử cả 2 field name (Phase 2 spec vs scaffolding)
    for fname in ("fefo_strict_mode", "enforce_fefo"):
        try:
            v = frappe.db.get_single_value("SupplyCore Settings", fname)
            if v is not None:
                return bool(v)
        except Exception:
            pass
    return False
