"""Scheduled tasks cho M2 Planning."""

import frappe
from frappe import _
from frappe.utils import today, add_days, flt


def check_reorder_levels():
    """Daily (UC-07 luồng 1a): scan items có tồn kho ≤ Reorder Level, auto-tạo
    Draft Material Request 1 cái/warehouse + email cảnh báo.

    Dùng SC * doctypes (no-ERPNext): SC Stock Ledger Entry + SC Item (.reorder_level)
    + SC Item Reorder (per-warehouse override via get_reorder_thresholds).
    """
    from supplycore.m2_planning.reorder import get_reorder_thresholds
    from supplycore.supplycore.doctype.sc_material_request.sc_material_request import SCMaterialRequest

    # 1. Find all (item, warehouse) where reorder set + below threshold
    pairs = _find_reorder_candidates()

    if not pairs:
        return {"checked": 0, "drafts_created": 0}

    # 2. Group by warehouse → 1 Draft MR per warehouse (only if not already created today)
    by_wh = {}
    for p in pairs:
        by_wh.setdefault(p["warehouse"], []).append(p)

    drafts_created = []
    skipped_no_supplier = []
    for warehouse, items in by_wh.items():
        # Dedup: skip if Draft auto_generated MR exists for this warehouse from today
        existing = frappe.db.exists("SC Material Request", {
            "warehouse": warehouse,
            "auto_generated": 1,
            "docstatus": 0,
            "transaction_date": today(),
        })
        if existing:
            continue

        # Filter items có supplier (UC-07 NCC check sẽ throw nếu không có)
        valid_rows = []
        for it in items:
            if SCMaterialRequest._item_has_supplier(it["item"]):
                valid_rows.append(it)
            else:
                skipped_no_supplier.append(it["item"])
        if not valid_rows:
            continue

        mr_name = _create_reorder_mr(warehouse, valid_rows)
        if mr_name:
            drafts_created.append(mr_name)

    # 3. Email summary
    _send_reorder_summary(pairs, drafts_created, skipped_no_supplier)

    return {
        "checked": len(pairs),
        "drafts_created": len(drafts_created),
        "skipped_no_supplier": len(skipped_no_supplier),
        "mr_names": drafts_created,
    }


def _find_reorder_candidates() -> list:
    """Return list of dicts: item, item_name, warehouse, current_qty, reorder_level,
    suggested_qty (= standard_order_qty or max-current or reorder*2-current).
    """
    from supplycore.m2_planning.reorder import get_reorder_thresholds

    # Strategy: enumerate (item, warehouse) pairs có thể có reorder.
    # Item-level: items có reorder_level > 0, scan tất cả warehouse có SLE.
    # Per-warehouse: items có SC Item Reorder row với reorder_level > 0.

    candidates = []

    # Per-warehouse rows
    wh_rows = frappe.db.sql("""
        SELECT r.parent AS item, i.item_name, r.warehouse, r.reorder_level
        FROM `tabSC Item Reorder` r
        JOIN `tabSC Item` i ON i.name = r.parent
        WHERE i.disabled = 0 AND i.is_stock_item = 1 AND i.is_purchase_item = 1
          AND r.parenttype = 'SC Item' AND COALESCE(r.reorder_level, 0) > 0
    """, as_dict=True)
    for r in wh_rows:
        th = get_reorder_thresholds(r.item, r.warehouse)
        current = _get_current_qty(r.item, r.warehouse)
        if current <= th["reorder_level"] and th["reorder_level"] > 0:
            candidates.append({
                "item": r.item, "item_name": r.item_name,
                "warehouse": r.warehouse,
                "current_qty": current, "reorder_level": th["reorder_level"],
                "suggested_qty": _compute_qty(th, current),
            })

    # Item-level (items không có per-WH override nhưng có reorder_level>0)
    # Scan tất cả warehouse có SLE cho item đó.
    item_rows = frappe.db.sql("""
        SELECT i.name AS item, i.item_name, i.reorder_level
        FROM `tabSC Item` i
        WHERE i.disabled = 0 AND i.is_stock_item = 1 AND i.is_purchase_item = 1
          AND COALESCE(i.reorder_level, 0) > 0
          AND NOT EXISTS (
              SELECT 1 FROM `tabSC Item Reorder` r
              WHERE r.parent = i.name AND r.parenttype = 'SC Item'
                AND COALESCE(r.reorder_level, 0) > 0
          )
    """, as_dict=True)
    for r in item_rows:
        warehouses = frappe.db.sql_list("""
            SELECT DISTINCT warehouse FROM `tabSC Stock Ledger Entry`
            WHERE item = %s AND is_cancelled = 0
        """, r.item) or []
        for wh in warehouses:
            th = get_reorder_thresholds(r.item, wh)
            current = _get_current_qty(r.item, wh)
            if current <= th["reorder_level"] and th["reorder_level"] > 0:
                candidates.append({
                    "item": r.item, "item_name": r.item_name,
                    "warehouse": wh,
                    "current_qty": current, "reorder_level": th["reorder_level"],
                    "suggested_qty": _compute_qty(th, current),
                })

    return candidates


def _get_current_qty(item: str, warehouse: str) -> float:
    return flt(frappe.db.sql("""
        SELECT COALESCE(SUM(qty_change), 0)
        FROM `tabSC Stock Ledger Entry`
        WHERE item = %s AND warehouse = %s AND is_cancelled = 0
    """, (item, warehouse))[0][0])


def _compute_qty(th: dict, current: float) -> float:
    """Suggested qty: standard_order_qty > max_stock-current > reorder*2-current."""
    if th["standard_order_qty"] > 0:
        return th["standard_order_qty"]
    if th["max_stock"] > 0:
        return max(0.0, th["max_stock"] - current)
    return max(0.0, th["reorder_level"] * 2 - current)


def _create_reorder_mr(warehouse: str, rows: list) -> str:
    """Tạo Draft SC Material Request auto-generated từ reorder candidates."""
    from frappe.utils import getdate

    mr = frappe.new_doc("SC Material Request")
    mr.request_type = "Purchase"
    mr.transaction_date = today()
    mr.schedule_date = add_days(today(), 14)
    mr.warehouse = warehouse
    mr.auto_generated = 1
    mr.reason = "Auto-tạo từ scheduler check_reorder_levels — tồn kho ≤ reorder level"
    mr.requested_by = "Administrator"

    for r in rows:
        item_uom = frappe.db.get_value("SC Item", r["item"], "uom")
        mr.append("items", {
            "item": r["item"],
            "qty": r["suggested_qty"],
            "uom": item_uom,
            "warehouse": warehouse,
            "schedule_date": add_days(today(), 14),
            "remarks": f"Tồn={r['current_qty']:.1f}, Reorder={r['reorder_level']:.1f}",
        })

    mr.flags.ignore_permissions = True
    try:
        mr.insert()
        return mr.name
    except Exception as e:
        frappe.log_error(
            message=f"warehouse={warehouse}, rows={len(rows)}, err={str(e)[:500]}",
            title="UC-07 check_reorder_levels _create_reorder_mr",
        )
        return None


def _send_reorder_summary(pairs: list, drafts: list, skipped: list):
    recipients = _get_alert_recipients()
    if not recipients:
        return
    rows = "".join(
        f"<tr><td>{p['item']}</td><td>{p['item_name'] or ''}</td>"
        f"<td>{p['warehouse']}</td><td>{p['current_qty']:.1f}</td>"
        f"<td>{p['reorder_level']:.1f}</td><td>{p['suggested_qty']:.1f}</td></tr>"
        for p in pairs[:100]
    )
    draft_links = "".join(
        f"<li><a href='/app/sc-material-request/{n}'>{n}</a></li>"
        for n in drafts
    )
    skipped_html = ""
    if skipped:
        skipped_html = (f"<p><b>Bỏ qua (chưa có NCC):</b> {', '.join(sorted(set(skipped))[:20])}</p>")
    message = f"""
        <h3>SupplyCore — Vật tư dưới Reorder Level</h3>
        <p>Đã quét {len(pairs)} cặp (item, warehouse). Tạo {len(drafts)} Draft MR.</p>
        <table border="1" cellpadding="6" cellspacing="0">
            <tr><th>Mã VT</th><th>Tên</th><th>Kho</th>
                <th>Tồn hiện tại</th><th>Reorder Level</th><th>SL đề xuất</th></tr>
            {rows}
        </table>
        <h4>Draft MR đã tạo</h4>
        <ul>{draft_links or '<li>—</li>'}</ul>
        {skipped_html}
    """
    try:
        frappe.sendmail(
            recipients=recipients,
            subject=f"[SupplyCore] {len(drafts)} Draft MR tự tạo từ Reorder Level",
            message=message,
            delayed=False,
        )
    except Exception as e:
        frappe.log_error(message=str(e)[:1000], title="UC-07 _send_reorder_summary")


def generate_procurement_forecast():
    """Weekly: placeholder cho auto Plan generation (defer Phase 2)."""
    frappe.logger().info("M2: generate_procurement_forecast scheduled placeholder")


def _get_alert_recipients() -> list:
    settings = frappe.get_single("SupplyCore Settings") if frappe.db.exists("DocType", "SupplyCore Settings") else None
    raw = settings.get("email_alert_recipients") if settings else None
    if raw:
        return [e.strip() for e in raw.split(",") if e.strip()]
    return frappe.db.sql_list("""
        SELECT DISTINCT u.email FROM `tabUser` u
        JOIN `tabHas Role` r ON r.parent = u.name
        WHERE r.role IN ('SupplyCore Storekeeper', 'SupplyCore Manager')
          AND u.enabled = 1 AND u.email IS NOT NULL AND u.email != ''
    """) or []
