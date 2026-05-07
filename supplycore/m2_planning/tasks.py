"""Scheduled tasks cho M2 Planning."""

import frappe
from frappe.utils import today


def check_reorder_levels():
    """Daily: cảnh báo items có tồn kho dưới Reorder Level (BR-M2-02).

    ERPNext built-in `erpnext.stock.reorder_item.reorder_item` cũng tự tạo
    Material Request draft. Task này chỉ thêm notification cho SC team.
    """
    low_stock = frappe.db.sql("""
        SELECT bin.item_code, i.item_name, bin.warehouse, bin.actual_qty,
               ir.warehouse_reorder_level, ir.warehouse_reorder_qty
        FROM `tabBin` bin
        JOIN `tabSC Item` i ON i.name = bin.item_code
        JOIN `tabItem Reorder` ir ON ir.parent = i.name AND ir.warehouse = bin.warehouse
        WHERE bin.actual_qty <= ir.warehouse_reorder_level
          AND i.disabled = 0
          AND i.is_stock_item = 1
        ORDER BY (ir.warehouse_reorder_level - bin.actual_qty) DESC
        LIMIT 100
    """, as_dict=True)

    if not low_stock:
        return

    # Recipients: từ Settings hoặc fallback theo role
    recipients = _get_alert_recipients()
    if not recipients:
        return

    rows = "".join(
        f"<tr><td>{x.item_code}</td><td>{x.item_name or ''}</td>"
        f"<td>{x.warehouse}</td><td>{x.actual_qty}</td>"
        f"<td>{x.warehouse_reorder_level}</td><td>{x.warehouse_reorder_qty}</td></tr>"
        for x in low_stock
    )
    message = f"""
        <h3>SupplyCore — Vật tư dưới Reorder Point</h3>
        <p>Cần xử lý: tạo Material Request hoặc kiểm tra Procurement Plan định kỳ.</p>
        <table border="1" cellpadding="6" cellspacing="0">
            <tr>
                <th>Mã VT</th><th>Tên</th><th>Kho</th>
                <th>Tồn hiện tại</th><th>Reorder Level</th><th>Reorder Qty (gợi ý)</th>
            </tr>
            {rows}
        </table>
        <p>
            <a href="/app/material-request/new?material_request_type=Purchase">Tạo Material Request</a>
            &nbsp;|&nbsp;
            <a href="/app/procurement-plan/new">Tạo Procurement Plan</a>
        </p>
    """
    frappe.sendmail(
        recipients=recipients,
        subject=f"[SupplyCore] {len(low_stock)} vật tư dưới Reorder Point",
        message=message,
        delayed=False,
    )


def generate_procurement_forecast():
    """Weekly: tạo draft Procurement Plan tự động (BR-M2-04, optional).

    TODO Phase 2: tự tạo draft Plan cho mỗi warehouse main + nạp items qua auto_load_items.
    Hiện tại chỉ log để monitoring thấy task chạy.
    """
    frappe.logger().info("M2: generate_procurement_forecast scheduled placeholder")


def _get_alert_recipients() -> list:
    settings = frappe.get_single("SupplyCore Settings")
    raw = settings.get("email_alert_recipients") if settings else None
    if raw:
        return [e.strip() for e in raw.split(",") if e.strip()]
    return frappe.db.sql_list("""
        SELECT DISTINCT u.email FROM `tabUser` u
        JOIN `tabHas Role` r ON r.parent = u.name
        WHERE r.role IN ('SupplyCore Storekeeper', 'SupplyCore Manager')
          AND u.enabled = 1 AND u.email IS NOT NULL AND u.email != ''
    """) or []
