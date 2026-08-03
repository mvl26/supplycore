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


def _resolve_item_fc(item: str):
    """Chọn HĐ khung NCC (Active) để gán cho dòng Yêu cầu mua — "gọi hàng theo
    HĐ khung của NCC". 1 HĐ khung chứa item → dùng luôn; nhiều HĐ khung → ưu tiên
    HĐ khớp NCC mặc định của item; vẫn mơ hồ → để TRỐNG cho người mua tự chọn
    (không đoán bừa). Item không thuộc HĐ khung nào → None (vẫn mua qua NCC mặc định)."""
    fcs = frappe.db.sql("""
        SELECT fc.name, fc.supplier
        FROM `tabFC Item` fci
        JOIN `tabFramework Contract` fc ON fc.name = fci.parent
        WHERE fci.item_code = %s AND fc.docstatus = 1 AND fc.status = 'Active'
    """, item, as_dict=True)
    if not fcs:
        return None
    if len(fcs) == 1:
        return fcs[0].name
    dsup = frappe.db.get_value("SC Item", item, "default_supplier")
    if dsup:
        match = [f.name for f in fcs if f.supplier == dsup]
        if len(match) == 1:
            return match[0]
    return None   # mơ hồ → để trống


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
            "framework_contract": _resolve_item_fc(r["item"]),  # gọi hàng theo HĐ khung NCC
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
    from supplycore.utils.emailer import role_emails
    recipients = list(_get_alert_recipients() or [])
    # + Quản lý (role SupplyCore Manager) — yêu cầu: thông báo tới quản lý
    for e in (role_emails("SupplyCore Manager") or []):
        if e not in recipients:
            recipients.append(e)
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
    from supplycore.utils.emailer import send_email, sc_list_url
    body = f"""
        <table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;font-size:13px">
            <tr style="background:#f3f6fb"><th>Mã VT</th><th align="left">Tên</th><th>Kho</th>
                <th align="right">Tồn hiện tại</th><th align="right">Mức tối thiểu</th><th align="right">SL đề xuất</th></tr>
            {rows}
        </table>
        <p style="margin:12px 0 4px;font-weight:600;color:#111827">Yêu cầu mua nháp đã tạo:</p>
        <ul style="margin:0">{draft_links or '<li>—</li>'}</ul>
        {skipped_html}
    """
    try:
        send_email(
            recipients=recipients,
            subject=f"[SupplyCore] {len(drafts)} Yêu cầu mua tự tạo (dưới tồn tối thiểu)",
            title="Vật tư dưới mức tồn tối thiểu",
            intro=f"Đã quét {len(pairs)} cặp (vật tư, kho) và tạo <b>{len(drafts)}</b> Yêu cầu mua nháp:",
            body_html=body, note_kind="warn",
            cta_url=sc_list_url("SC Material Request"), cta_label="Mở danh sách Yêu cầu mua",
        )
    except Exception as e:
        frappe.log_error(message=str(e)[:1000], title="UC-07 _send_reorder_summary")


def check_po_response():
    """Daily (UC-08 ngoại lệ): nhắc NCC nếu PO Sent to Supplier > X ngày không phản hồi.

    Settings.po_response_reminder_days (default 3) quy định ngưỡng.
    Dedup: chỉ gửi reminder cách lần trước ≥ ngưỡng ngày.
    """
    days = int(frappe.db.get_single_value("SupplyCore Settings", "po_response_reminder_days") or 3)
    rows = frappe.db.sql("""
        SELECT po.name, po.supplier, po.supplier_name, po.sent_to_supplier_at,
               po.last_reminder_sent_at, s.email_id
        FROM `tabSC Purchase Order` po
        JOIN `tabSC Supplier` s ON s.name = po.supplier
        WHERE po.docstatus = 1
          AND po.status = 'Sent to Supplier'
          AND COALESCE(po.supplier_confirmation_received, 0) = 0
          AND po.sent_to_supplier_at IS NOT NULL
          AND DATEDIFF(NOW(), po.sent_to_supplier_at) >= %s
          AND s.email_id IS NOT NULL AND s.email_id != ''
          AND (
              po.last_reminder_sent_at IS NULL
              OR DATEDIFF(NOW(), po.last_reminder_sent_at) >= %s
          )
        LIMIT 100
    """, (days, days), as_dict=True)

    sent = 0
    for po in rows:
        try:
            from supplycore.utils.emailer import send_email
            send_email(
                recipients=[po.email_id],
                subject=f"[SupplyCore] Nhắc xác nhận Đơn mua {po.name}",
                title=f"Nhắc xác nhận Đơn mua {po.name}",
                intro=f"Kính gửi <b>{po.supplier_name or po.supplier}</b>,",
                info_rows=[("Mã đơn mua", po.name),
                           ("Ngày gửi", frappe.format(po.sent_to_supplier_at, {'fieldtype': 'Datetime'}))],
                note="Đơn mua đã gửi nhưng chưa nhận được xác nhận từ Quý công ty. "
                     "Vui lòng phản hồi sớm nhất có thể.", note_kind="warn",
            )
            frappe.db.set_value("SC Purchase Order", po.name,
                                 "last_reminder_sent_at", frappe.utils.now())
            sent += 1
        except Exception as e:
            frappe.log_error(message=f"po={po.name}: {str(e)[:500]}",
                              title="UC-08 check_po_response")
    frappe.db.commit()
    return {"reminders_sent": sent, "candidates": len(rows)}


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
