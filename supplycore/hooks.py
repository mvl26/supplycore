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

boot_session = "supplycore.boot.boot_session"
after_install = "supplycore.install.after_install"
before_uninstall = "supplycore.uninstall.before_uninstall"

# Outbound webhooks — runtime qua DocType "Webhook"
webhooks = []
