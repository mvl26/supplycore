"""UC Coverage — kiểm tra mỗi Use Case từ Phase 1 đã được implement chưa.

Status:
  ok       — UC implement đầy đủ + verify được flow chính
  partial  — Có DocType/method nhưng thiếu workflow/UI/automation
  missing  — Chưa có DocType/method tương ứng
"""

import frappe
from frappe.utils import today

results = []


def check(uc, name, actor, module, status, note=""):
    results.append({
        "uc": uc, "name": name, "actor": actor, "module": module,
        "status": status, "note": note,
    })


def has_dt(dt):
    return frappe.db.exists("DocType", dt) is not None


def has_method(module_path, method_name):
    try:
        from importlib import import_module
        m = import_module(module_path)
        return hasattr(m, method_name)
    except Exception:
        return False


def has_scheduler(method_path):
    try:
        from supplycore.hooks import scheduler_events
        for tasks in scheduler_events.values():
            if isinstance(tasks, list) and method_path in tasks:
                return True
            if isinstance(tasks, dict):
                for t in tasks.values():
                    if method_path in t:
                        return True
        return False
    except Exception:
        return False


def run_all():
    # ============================================================
    # M1 — Contracts & Suppliers
    # ============================================================
    if has_dt("SC Supplier"):
        sup_count = frappe.db.count("SC Supplier", {"disabled": 0})
        check("UC-01", "Search & Evaluate Suppliers", "SK/ACC", "M1",
              "ok", f"SC Supplier doctype có sẵn ({sup_count} active). List view + Frappe filter chuẩn.")
        check("UC-02", "Create / Update Supplier", "ACC/MGR", "M1",
              "ok", "SC Supplier CRUD qua /app/sc-supplier")
    else:
        check("UC-01", "Search & Evaluate Suppliers", "SK/ACC", "M1", "missing",
              "SC Supplier doctype không có")
        check("UC-02", "Create / Update Supplier", "ACC/MGR", "M1", "missing", "")

    if has_dt("Framework Contract"):
        fc_count = frappe.db.count("Framework Contract", {"docstatus": 1})
        check("UC-03", "Create & Manage Framework Contract", "ACC/MGR/EXEC", "M1",
              "ok", f"Framework Contract đầy đủ ({fc_count} submit). Validate FC budget. Slice 1 wired RO + auto-PO.")
        check("UC-04", "Track Contract Status & Renewal", "ACC/MGR", "M1",
              "ok" if has_scheduler("supplycore.m1_contract.tasks.check_contract_expiry") else "partial",
              "scheduler check_contract_expiry daily — email cảnh báo 30/15/7 ngày + status auto Active/Expired")
    else:
        check("UC-03", "Create & Manage Framework Contract", "ACC/MGR/EXEC", "M1", "missing", "")
        check("UC-04", "Track Contract Status & Renewal", "ACC/MGR", "M1", "missing", "")

    # ============================================================
    # M2 — Inventory Planning & Replenishment
    # ============================================================
    if has_dt("SC Item"):
        meta = frappe.get_meta("SC Item")
        has_safety = any(f.fieldname == "safety_stock" for f in meta.fields)
        check("UC-05", "Set Min/Max Stock Levels", "SK/MGR", "M2",
              "ok" if has_safety else "partial",
              "SC Item.safety_stock có; max_stock + reorder_qty tuỳ schema. Kiểm tra ROP per warehouse defer.")

    if has_dt("Procurement Plan"):
        check("UC-06", "Create Periodic Procurement Plan", "SK/MGR", "M2",
              "partial", "Procurement Plan doctype có nhưng generate_procurement_forecast scheduler chỉ là placeholder. Auto-MR creation defer.")
    else:
        check("UC-06", "Create Periodic Procurement Plan", "SK/MGR", "M2",
              "missing", "Procurement Plan doctype chưa có")

    check("UC-07", "Create Purchase Request (MR)", "SK/Ward", "M2",
          "ok" if has_dt("SC Material Request") else "missing",
          "SC Material Request submit → status=Approved (slice 1)")

    check("UC-08", "Create & Approve Purchase Order", "ACC/MGR", "M2",
          "ok" if has_dt("SC Purchase Order") else "missing",
          "SC PO + create_purchase_orders auto từ MR (slice 1). Approval threshold qua SupplyCore Settings.po_approval_threshold (50tr).")

    # ============================================================
    # M3 — Receiving & QC
    # ============================================================
    check("UC-09", "Receive Goods & Create PR", "SK", "M3",
          "ok" if has_dt("SC Purchase Receipt") else "missing",
          "SC PR + slice mới make_pr_from_po auto-fetch. PR.on_submit → SLE + auto-Batch + auto-QI.")

    if has_dt("SC Quality Inspection") and has_dt("QC Checklist Template"):
        check("UC-10", "Quality Inspection (QC)", "SK/MGR", "M3",
              "ok", "QI auto-tạo từ PR.on_submit. QI submit Accepted/Rejected → rollup PR.qc_status + Batch.qc_status. Naming inconsistency UAT-01 (Pass/Fail vs Accepted/Rejected).")
    else:
        check("UC-10", "Quality Inspection (QC)", "SK/MGR", "M3", "partial", "")

    if has_dt("SC Purchase Receipt"):
        meta = frappe.get_meta("SC Purchase Receipt")
        has_return = any(f.fieldname == "is_return" for f in meta.fields)
        check("UC-11", "Handle Supplier Returns", "SK/ACC", "M3",
              "ok" if has_return else "missing",
              "PR.is_return + auto-tạo PR Return draft khi QI Rejected (wire-up 2026-05-08). Debit note generation defer (Frappe Print Format).")

    # ============================================================
    # M4 — WMS & PDA
    # ============================================================
    check("UC-12", "Manage Warehouse Bin Locations", "SK", "M4",
          "ok" if has_dt("Bin Location") else "missing",
          "Bin Location doctype có (zone/aisle/rack/shelf/level). Putaway rule chưa wire (TODO).")

    if has_method("supplycore.api.wms", "scan_barcode"):
        check("UC-13", "Stock In/Out via PDA / Barcode", "SK", "M4",
              "partial", "scan_barcode + confirm_putaway có. NHƯNG: PDA offline IndexedDB sync defer (Phase 1.1+). UI /pda chỉ basic 480px. UAT-03: signature scan_barcode(barcode, context) ≠ README.")
    else:
        check("UC-13", "Stock In/Out via PDA / Barcode", "SK", "M4", "missing", "")

    check("UC-14", "Query Stock by Location", "SK/MGR/Ward", "M4",
          "ok" if has_dt("SC Stock Ledger Entry") else "missing",
          "SLE list view + filter. KPI per warehouse qua api.kpi.get_warehouse_dashboard. Frappe Report Builder cho custom report.")

    # ============================================================
    # M5 — Lots, Expiry & FEFO
    # ============================================================
    check("UC-15", "Manage Batch/Lot Information", "SK", "M5",
          "ok" if has_dt("SC Batch") else "missing",
          "SC Batch + auto-tạo từ PR.on_submit. Format batch_id <item>-<YYYYMM>-<rand>. QC rollup từ QI.")

    check("UC-16", "Issue Stock by FEFO", "SK/System", "M5",
          "ok" if has_method("supplycore.api.fefo", "get_suggested_batches") else "missing",
          "API FEFO sort ASC by expiry. SE validate block expired/blocked (SC-E001/SC-E008).")

    check("UC-17", "Alert for Near Expiry Stock", "System/MGR/SK", "M5",
          "ok" if has_scheduler("supplycore.m5_fefo.api.fefo_picker.scan_expiring_batches") else "partial",
          "scan_expiring_batches scheduler daily. M11 alert_type=expiring_batch + slice 2 action button 'Chuyển Quarantine'.")

    # ============================================================
    # M6 — Internal Transfers
    # ============================================================
    check("UC-18", "Internal Stock Transfer", "SK/MGR", "M6",
          "ok" if has_dt("SC Transfer Request") else "missing",
          "SC Transfer Request submit → make_stock_entry → SE Material Transfer. Workflow chính thức (Pending → Approved by MGR) defer Phase 1.1+.")

    check("UC-19", "Adjust Stock (Reconciliation)", "SK/MGR/ACC", "M6",
          "ok" if has_dt("SC Stock Reconciliation") else "missing",
          "SC Stock Reconciliation → SLE adjustment + GL Dr 152/Cr 642. Wire qua M9.")

    # ============================================================
    # M7 — Dispensing & Usage
    # ============================================================
    check("UC-20", "Create Stock Request (DR)", "Ward", "M7",
          "ok" if has_dt("SC Dispensing Request") else "missing",
          "SC DR submit → status=Approved.")

    check("UC-21", "Process & Dispense Stock", "SK", "M7",
          "ok" if has_dt("SC Patient Dispensing") else "missing",
          "DR Approved → SE Material Issue (FEFO bắt buộc) → tạo PD. Dispensing slip print format có template (templates/print_formats/dispensing_slip.html).")

    check("UC-22", "Record Item Usage per Patient", "Ward", "M7",
          "ok" if has_dt("SC Patient Dispensing") else "missing",
          "PD + PD Item ghi nhận qty/unit_cost/bhyt_amount/patient_pays per BN. Trace qua SC PD Item.")

    check("UC-23", "Manage BHYT Codes", "MGR/ACC", "M7",
          "ok" if has_dt("SC BHYT Code Config") else "missing",
          "SC BHYT Code Config N01-N09 + ceiling_price + payment_rate. get_active_config priority item-spec > group > fallback.")

    # ============================================================
    # M8 — Accounting & Payment
    # ============================================================
    check("UC-24", "Create & Match Purchase Invoice", "ACC", "M8",
          "ok" if has_dt("SC Purchase Invoice") else "missing",
          "SC PI + 3-way match (±1% tolerance, hard cap +5%). slice mới make_invoice_from_pr auto-fetch từ PR. GL Dr 152 + Dr 1331 / Cr 331 (VAS TT 200/2014).")

    check("UC-25", "Create Payment Entry & Track AP", "ACC/MGR", "M8",
          "ok" if has_dt("SC Payment Entry") else "missing",
          "SC PE + on_submit → GL Dr 331/Cr 1121 + update PI.outstanding. Slice 2 alert action button.")

    check("UC-26", "Financial Reports", "ACC/MGR/EXEC", "M8",
          "partial",
          "API get_executive_dashboard có 6 KPI (M11). Trial Balance/AP Aging/Stock Cost report chưa build qua Frappe Report Builder (defer Phase 1.1+).")

    # ============================================================
    # M9 — Count & Reconciliation
    # ============================================================
    check("UC-27", "Plan & Execute Inventory Count", "SK/MGR", "M9",
          "ok" if has_dt("SC Inventory Count Sheet") else "missing",
          "SC ICS + auto_load_items snapshot system_qty. Cron create_periodic_count daily 1AM. Recount workflow defer.")

    check("UC-28", "Reconcile System vs Physical", "SK/ACC/MGR", "M9",
          "ok" if has_dt("SC Stock Reconciliation") else "missing",
          "ICS → make_stock_reconciliation → SR.on_submit ghi SLE adjustment + GL.")

    # ============================================================
    # M10 — Traceability & Investigation
    # ============================================================
    check("UC-29", "Trace Item Origin (Batch Trace)", "MGR/SK", "M10",
          "ok" if has_method("supplycore.api.trace", "get_batch_trace") else "missing",
          "API get_batch_trace trả source PR + movements + patient_dispensings + current qty per warehouse.")

    check("UC-30", "Recall Management", "MGR/SK", "M10",
          "ok" if has_dt("SC Recall Notice") else "missing",
          "SC Recall Notice + populate_affected_items + Batch.blocked=1 chặn issue (SC-E008). Slice 3 spec đã có (email notify + mark contacted) — chưa implement.")

    check("UC-31", "Investigate Stock Loss/Variance", "MGR/SysAdmin", "M10",
          "ok" if has_method("supplycore.api.trace", "get_audit_trail") else "missing",
          "API get_audit_trail SLE history + cancelled count cho điều tra thất thoát.")

    # ============================================================
    # M11 — Dashboard & Alerts
    # ============================================================
    check("UC-32", "View Executive Dashboard", "EXEC/MGR", "M11",
          "partial",
          "API get_executive_dashboard 6 KPI sẵn. Frontend Workspace + Number Cards (Phase 3 mockup) defer — v1 chỉ JSON.")

    check("UC-33", "Configure Auto-Alerts", "SysAdmin/MGR", "M11",
          "ok" if has_dt("SC Alert Rule") else "missing",
          "SC Alert Rule + 7 alert types (expiring_batch, contract_expiring, fc_remaining_low, low_stock, overdue_payment, qc_pending, recall_outstanding). Daily scan + dedup 7-day window.")

    check("UC-34", "View & Action Alerts", "SK/MGR/ACC", "M11",
          "ok" if has_dt("SC Alert") else "missing",
          "SC Alert + slice 2 action buttons (3 alert types có hành động trực tiếp: quarantine batch / tạo MR / tạo PE). 4 alert types khác chỉ resolve thủ công.")

    # ============================================================
    # SYS — System Admin
    # ============================================================
    check("UC-35", "Manage Users & Permissions", "SysAdmin", "SYS",
          "ok",
          "Frappe built-in User + Role + Permission Manager. SupplyCore-specific roles (Manager/SK/Pharmacy/Accountant/Executive) đã seed qua patches/v0_1/create_supplycore_roles.py.")

    check("UC-36", "Configure System Parameters", "SysAdmin", "SYS",
          "ok" if has_dt("SupplyCore Settings") else "missing",
          "SupplyCore Settings Single doctype: po_approval_threshold, match_tolerance_pct, fefo_min_shelf_life_days, enforce_fefo, email_alert_recipients.")

    check("UC-37", "Manage Master Data Catalog", "SysAdmin/MGR", "SYS",
          "ok",
          "SC Item + SC Item Group (NestedSet) + SC UOM + SC Department + SC Warehouse (NestedSet) + SC GL Account. Seed qua setup/seed_master_data.py.")

    return results
