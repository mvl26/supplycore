app_name = "supplycore"
app_title = "SupplyCore"
app_publisher = "SupplyCore Project"
app_description = "Medical supply distribution management — Frappe-only custom app (no ERPNext dependency)"
app_email = "info@miyano.com.vn"
app_license = "MIT"
required_apps = ["frappe/frappe"]  # ERPNext không còn bắt buộc kể từ v0.2

# ---------------------------------------------------------------------------
# Includes
# ---------------------------------------------------------------------------
app_include_css = []
app_include_js = []
web_include_css = []
web_include_js = []
doctype_js = {}

# ---------------------------------------------------------------------------
# Document Events — chỉ trên SC* DocTypes (không còn target ERPNext)
# ---------------------------------------------------------------------------
doc_events = {
    "SC Purchase Receipt": {
        # Logic auto QI + SLE đã nằm trong sc_purchase_receipt.py controller
    },
    "SC Stock Entry": {
        # Logic FEFO + SLE đã nằm trong sc_stock_entry.py controller
    },
    "SC Quality Inspection": {
        # Logic rollup PR.qc_status đã nằm trong sc_quality_inspection.py controller
    },
    "SC Batch": {
        "after_insert": "supplycore.m5_fefo.api.fefo_picker.register_batch",
    },
    "SC Purchase Order": {
        # Logic FC validation đã nằm trong sc_purchase_order.py controller
    },
}

# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------
scheduler_events = {
    "daily": [
        "supplycore.m1_contract.tasks.check_contract_expiry",
        "supplycore.m2_planning.tasks.check_reorder_levels",
        "supplycore.m2_planning.tasks.check_po_response",
        "supplycore.m3_receiving.tasks.check_return_responses",
        "supplycore.m5_fefo.api.fefo_picker.scan_expiring_batches",
        "supplycore.m11_dashboard.tasks.scan_alerts",
        "supplycore.m11_dashboard.tasks.send_daily_kpi",
        "supplycore.m11_dashboard.tasks.auto_resolve_alerts",
        "supplycore.m11_dashboard.tasks.escalate_overdue_alerts",
    ],
    "weekly": [
        "supplycore.m2_planning.tasks.generate_procurement_forecast",
    ],
    "cron": {
        "0 1 * * *": ["supplycore.m9_stocktake.tasks.create_periodic_count"],
    },
}

# ---------------------------------------------------------------------------
# SPA route: tất cả /supplycore/* trả về same SPA shell (Vue Router xử lý)
# ---------------------------------------------------------------------------
website_route_rules = [
    {"from_route": "/supplycore/<path:app_path>", "to_route": "supplycore"},
]

# Phục vụ /sw.js ở gốc để service worker kiểm soát được scope /supplycore/
page_renderer = ["supplycore.pwa.ServiceWorkerRenderer"]

# Khi truy cập domain root → đưa thẳng vào SPA SupplyCore (ko show Frappe Desk).
website_redirects = [
    {"source": "/", "target": "/supplycore/", "redirect_http_status": 302},
]

# ---------------------------------------------------------------------------
# Permission hooks (target SC*)
# ---------------------------------------------------------------------------
permission_query_conditions = {
    "SC Stock Entry": "supplycore.utils.permissions.stock_entry_query",
    "SC Sales Order": "supplycore.utils.permissions.sales_order_portal_query",
    "SC Delivery Note": "supplycore.utils.permissions.delivery_note_portal_query",
    "SC Sales Invoice": "supplycore.utils.permissions.sales_invoice_portal_query",
    "SC Sales Receipt": "supplycore.utils.permissions.sales_receipt_portal_query",
    "SC Sales Framework Contract": "supplycore.utils.permissions.sales_fc_portal_query",
    # Child tables (RSK-01 caveat — xem permissions.py::_portal_child_scope):
    # permission_query_conditions tra theo doctype của truy vấn, không kế thừa
    # từ doctype cha, nên phải đăng ký riêng để chặn truy vấn thẳng child.
    "SO Item": "supplycore.utils.permissions.so_item_portal_query",
    "DN Item": "supplycore.utils.permissions.dn_item_portal_query",
    "SI Item": "supplycore.utils.permissions.si_item_portal_query",
    "SFC Item": "supplycore.utils.permissions.sfc_item_portal_query",
}

has_permission = {
    "SC Sales Order": "supplycore.utils.permissions.portal_doc_permission",
    "SC Delivery Note": "supplycore.utils.permissions.portal_doc_permission",
    "SC Sales Invoice": "supplycore.utils.permissions.portal_doc_permission",
    "SC Sales Receipt": "supplycore.utils.permissions.portal_doc_permission",
    "SC Sales Framework Contract": "supplycore.utils.permissions.portal_doc_permission",
    # Defense-in-depth (Task 2 review, Minor 1) — KHÔNG phải đường đi
    # enforcement chính, xem docstring `portal_child_permission`: Frappe
    # resolve has_permission của child doctype thẳng về cha thật qua
    # has_child_permission() TRƯỚC KHI hook này có cơ hội chạy.
    "SO Item": "supplycore.utils.permissions.portal_child_permission",
    "DN Item": "supplycore.utils.permissions.portal_child_permission",
    "SI Item": "supplycore.utils.permissions.portal_child_permission",
    "SFC Item": "supplycore.utils.permissions.portal_child_permission",
}

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
fixtures = [
    {"dt": "Role", "filters": [["name", "in", [
        "SupplyCore Manager", "SupplyCore User", "SupplyCore Auditor",
        "SupplyCore Storekeeper",
        "SupplyCore Accountant", "SupplyCore Executive", "SupplyCore Purchaser",
        "Warehouse Officer", "QC Officer",
    ]]]},
    {"dt": "Workflow",       "filters": [["name", "like", "SupplyCore%"]]},
    {"dt": "Workflow State", "filters": [["name", "like", "SupplyCore%"]]},
    {"dt": "Workflow Action Master", "filters": [["name", "like", "SupplyCore%"]]},
    {"dt": "Print Format",   "filters": [["module", "in", [
        "Supplycore", "M1 Contract", "M2 Planning", "M3 Receiving",
        "M4 WMS", "M5 FEFO", "M6 Transfer",
        "M8 Accounting", "M9 Stocktake", "M10 Traceability", "M11 Dashboard"]]]},
    {"dt": "Email Template", "filters": [["module", "like", "%Supplycore%"]]},
]

# ---------------------------------------------------------------------------
# Override whitelisted methods (RSK-01 Critical — rò rỉ chéo child-row)
# ---------------------------------------------------------------------------
# `frappe.client.get` (dùng bởi `/api/method/frappe.client.get` + FrappeClient)
# đi qua `doc.check_permission()` trên CHÍNH dòng con vừa load đơn lẻ (không
# nằm trong parent doc đầy đủ) — `has_child_permission()` của Frappe resolve
# `doc=getattr(child_doc, "parent_doc", child_doc.parent)`, và child doc độc
# lập luôn có sẵn thuộc tính `parent_doc` (property, mặc định None) nên
# `getattr` trả về None thay vì fallback về `child_doc.parent` như tưởng —
# `has_permission(parent_doctype, doc=None, ...)` chỉ còn kiểm tra doctype-level
# (luôn True với role Portal đã có read=1 trên 5 doctype cha), bỏ qua hoàn
# toàn `portal_doc_permission`. Xem `supplycore/api/portal.py::guarded_client_get`
# + `supplycore/utils/permissions.py::portal_child_permission` (docstring) để
# trace chi tiết. `permission_query_conditions` (list-query) đã lọc đúng —
# hole này CHỈ nằm ở đường `frappe.client.get` theo tên/filter đơn lẻ.
override_whitelisted_methods = {
    "frappe.client.get": "supplycore.api.portal.guarded_client_get",
}

boot_session = "supplycore.boot.boot_session"
after_install = "supplycore.install.after_install"
before_uninstall = "supplycore.uninstall.before_uninstall"

# Outbound webhooks — runtime qua DocType "Webhook"
webhooks = []
