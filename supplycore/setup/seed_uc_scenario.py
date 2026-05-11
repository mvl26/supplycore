"""End-to-end UC-05..34 scenario seed.

Usage:
    bench --site supplycore execute supplycore.setup.seed_uc_scenario.run

Three phases:
    1. wipe_all()       — xóa transactional + master (giữ User/Role/Settings/Alert Rule)
    2. seed_master()    — UOM, Warehouses, Suppliers, Items, BHYT, Patients, FC, GL, Alert Rules
    3. seed_scenario()  — 11 phase transactional UC-05..34

See MAIN_FLOW.md cùng folder cho mô tả flow đầy đủ.
"""

import frappe
from frappe.utils import (
    today, add_days, add_months, add_to_date, flt, now, nowtime,
    random_string, getdate,
)
from datetime import date


# =====================================================================
# WIPE — FK-ordered (most-dependent first)
# =====================================================================
# Order matters chỉ cho readability + sanity; DB không enforce FK
WIPE_TABLES = [
    # === Investigation / Alert ===
    "SC Investigation Finding", "SC Investigation Report",
    "SC Recall Affected Item", "SC Recall Notice",
    "SC Alert",  # giữ SC Alert Rule (config)
    # === GL / Accounting ===
    "SC GL Entry",
    "SC Payment Reference", "SC Payment Entry",
    "SC PI Item", "SC Purchase Invoice",
    # === Stocktake ===
    "SC SR Item", "SC Stock Reconciliation",
    "SC ICS Item", "SC Inventory Count Sheet",
    # === Dispensing ===
    "SC PD Item", "SC Patient Dispensing",
    "SC DR Item", "SC Dispensing Request",
    # === Transfer ===
    "SC Stock Entry Item", "SC Stock Entry",
    "SC Transfer Request Item", "SC Transfer Request",
    # === Receiving / QI ===
    "SC QI Reading", "SC Quality Inspection",
    "SC Purchase Receipt Item", "SC Purchase Receipt",
    # === Procurement ===
    "SC Purchase Order Item", "SC Purchase Order",
    "SC Material Request Item", "SC Material Request",
    # === SLE (immutable log) ===
    "SC Stock Ledger Entry",
    # === Master — batches first then items ===
    "SC Batch",
    "FC Renewal History", "FC Item", "Framework Contract",
    "SC BHYT Code Config",
    "SC Patient",
    # GL accounts
    "SC GL Account",
    # Supplier
    "SC Supplier Item Group", "SC Supplier",
    # Item child tables
    "SC Item Reorder", "SC Item Barcode", "SC Item",
    # Warehouse (NestedSet)
    "Bin Location", "SC Warehouse",
    # Department
    "SC Department",
    # Item Group + UOM
    "SC Item Group", "SC UOM",
]


def wipe_all() -> dict:
    """Xóa transactional + master (giữ User/Role/Settings/Alert Rule)."""
    counts = {}
    for dt in WIPE_TABLES:
        try:
            n = frappe.db.count(dt)
            if n:
                frappe.db.sql(f"DELETE FROM `tab{dt}`")
                counts[dt] = n
        except Exception as e:
            counts[dt] = f"ERR: {str(e)[:80]}"
    # Reset naming series counters cho clean numbering
    naming_series_prefixes = [
        "SC-FC-", "SC-RO-", "SC-PP-", "SC-MR-", "SC-PO-", "SC-PR-",
        "SC-QI-", "SC-SE-", "SC-TR-", "SC-DR-", "SC-PD-", "SC-PI-",
        "SC-PE-", "SC-SR-", "SC-ICS-", "SC-BHYT-", "SC-ALR-", "SC-RCL-",
        "SC-INV-", "SC-AR-",
    ]
    for prefix in naming_series_prefixes:
        try:
            frappe.db.sql("DELETE FROM `tabSeries` WHERE name LIKE %s",
                          f"{prefix}%")
        except Exception:
            pass
    frappe.db.commit()
    return counts


# =====================================================================
# SEED MASTER
# =====================================================================
def seed_master() -> dict:
    """Master data: UOM, ItemGroup, Warehouse, Department, Supplier, Item,
    GLAccount, BHYT, Patient, Framework Contract, Alert Rules."""
    # Reuse existing seed_master_data cho UOM/Groups/Warehouses/Suppliers/Items/GL
    from supplycore.setup import seed_master_data
    base_counts = seed_master_data.run()

    counts = dict(base_counts)
    counts["bhyt_configs"] = _seed_bhyt_configs()
    counts["patients"] = _seed_patients()
    counts["framework_contracts"] = _seed_framework_contracts()
    counts["alert_rules"] = _seed_alert_rules()
    counts["item_safety_stock"] = _set_safety_stock_on_items()
    frappe.db.commit()
    return counts


def _seed_bhyt_configs() -> int:
    """5 BHYT configs cho thuốc kê đơn — đại diện 5 nhóm N01-N05."""
    items_with_bhyt = frappe.get_all("SC Item",
        filters={"has_bhyt": 1, "disabled": 0},
        pluck="name", limit=8)
    if not items_with_bhyt:
        # fallback: lấy 5 items đầu
        items_with_bhyt = frappe.get_all("SC Item",
            filters={"disabled": 0, "is_stock_item": 1},
            pluck="name", limit=5)

    bhyt_specs = [
        ("N01", "BHYT Hộ gia đình", "N01", 80, 0),
        ("N02", "BHYT Hưu trí", "N02", 95, 50000),
        ("N03", "BHYT Trẻ em <6 tuổi", "N03", 100, 0),
        ("N04", "BHYT Người nghèo", "N04", 100, 0),
        ("N05", "BHYT Đối tượng đặc biệt", "N05", 100, 100000),
    ]
    count = 0
    for i, (code, name, group, rate, ceiling) in enumerate(bhyt_specs):
        if i >= len(items_with_bhyt):
            break
        if frappe.db.exists("SC BHYT Code Config", {"bhyt_code": code,
                                                      "item": items_with_bhyt[i]}):
            continue
        b = frappe.new_doc("SC BHYT Code Config")
        b.bhyt_code = code
        b.bhyt_name = name
        b.bhyt_group = group
        b.payment_rate = rate
        b.ceiling_price = ceiling
        b.item = items_with_bhyt[i]
        b.effective_from = add_days(today(), -90)
        b.is_active = 1
        b.flags.ignore_permissions = True
        b.insert()
        count += 1
    return count


def _seed_patients() -> int:
    """10 bệnh nhân với BHYT cards."""
    depts = frappe.get_all("SC Department", filters={"disabled": 0},
                            pluck="name", limit=6)
    if not depts:
        depts = [None]
    # bhyt_type options: Đúng tuyến / Trái tuyến / Không có BHYT
    patients = [
        ("BN001", "Nguyễn Văn An", "Nam", "1965-04-12", "DN4-001-12345-678", "Đúng tuyến", 95, depts[0]),
        ("BN002", "Trần Thị Bình", "Nữ", "1980-08-25", "GD4-079-23456-789", "Đúng tuyến", 80, depts[1 % len(depts)]),
        ("BN003", "Lê Hoàng Cường", "Nam", "2020-01-15", "TE4-079-34567-890", "Đúng tuyến", 100, depts[2 % len(depts)]),
        ("BN004", "Phạm Thị Dung", "Nữ", "1955-11-30", "DN4-079-45678-901", "Đúng tuyến", 95, depts[0]),
        ("BN005", "Hoàng Văn Em", "Nam", "1992-06-18", "GD4-079-56789-012", "Đúng tuyến", 80, depts[3 % len(depts)]),
        ("BN006", "Đặng Thị Phượng", "Nữ", "1973-03-22", "GD4-079-67890-123", "Đúng tuyến", 80, depts[4 % len(depts)]),
        ("BN007", "Bùi Minh Giang", "Nam", "1988-09-10", None, "Không có BHYT", 0, depts[1 % len(depts)]),
        ("BN008", "Vũ Thị Hà", "Nữ", "2015-12-05", "TE4-079-89012-345", "Đúng tuyến", 100, depts[2 % len(depts)]),
        ("BN009", "Đỗ Văn Inh", "Nam", "1948-07-20", "DN4-079-90123-456", "Đúng tuyến", 95, depts[0]),
        ("BN010", "Trương Thị Kim", "Nữ", "1995-02-14", "TT4-079-01234-567", "Trái tuyến", 60, depts[5 % len(depts)]),
    ]
    count = 0
    for pid, name, gender, dob, card, btype, rate, dept in patients:
        if frappe.db.exists("SC Patient", pid):
            continue
        p = frappe.new_doc("SC Patient")
        p.patient_id = pid
        p.patient_name = name
        p.gender = gender
        p.dob = dob
        p.bhyt_card_no = card
        p.bhyt_type = btype
        p.bhyt_payment_rate = rate
        p.bhyt_valid_to = add_days(today(), 365)
        p.current_department = dept
        p.admission_date = add_days(today(), -10)
        p.flags.ignore_permissions = True
        p.insert()
        count += 1
    return count


def _seed_framework_contracts() -> int:
    """3 Framework Contracts active với items (UC-01..02)."""
    suppliers = frappe.get_all("SC Supplier", filters={"disabled": 0},
                                 pluck="name", limit=5, order_by="name")
    items = frappe.get_all("SC Item",
        filters={"disabled": 0, "is_stock_item": 1},
        fields=["name", "uom"], limit=6, order_by="name")
    if len(suppliers) < 3 or len(items) < 6:
        return 0

    fcs = [
        ("FC-2026-001", suppliers[0], 5_000_000_000, today(), add_months(today(), 12), items[:3]),
        ("FC-2026-002", suppliers[1], 3_000_000_000, today(), add_months(today(), 12), items[2:5]),
        # FC-003: valid_to trong 25 ngày → contract_expiring_30d KPI (UC-32)
        ("FC-2026-003", suppliers[2], 2_000_000_000, add_days(today(), -300),
         add_days(today(), 25), items[3:6]),
    ]
    count = 0
    for cn, sup, total, vf, vt, fc_items in fcs:
        if frappe.db.exists("Framework Contract", {"contract_number": cn}):
            continue
        fc = frappe.new_doc("Framework Contract")
        fc.contract_number = cn
        fc.supplier = sup
        fc.contract_date = vf
        fc.valid_from = vf
        fc.valid_to = vt
        fc.total_value = total
        fc.remaining_value = total
        for it in fc_items:
            fc.append("items", {
                "item_code": it.name,
                "uom": it.uom,
                "contract_qty": 10000,
                "unit_price": 50000,
            })
        # Bypass 3-tier approval: set stage=Approved trước submit
        fc.approval_stage = "Approved"
        fc.manager_approved_by = "Administrator"
        fc.manager_approved_at = now()
        fc.executive_approved_by = "Administrator"
        fc.executive_approved_at = now()
        fc.flags.ignore_permissions = True
        try:
            fc.insert()
            try:
                fc.submit()
            except Exception as e:
                frappe.log_error(message=f"FC submit {cn}: {str(e)[:300]}",
                                  title="seed_uc FC submit")
            count += 1
        except Exception as e:
            frappe.log_error(message=f"FC insert {cn}: {str(e)[:300]}",
                              title="seed_uc FC")
    return count


def _seed_alert_rules() -> int:
    """6 alert rules cơ bản (idempotent)."""
    rules = [
        ("Lô sắp hết hạn", "expiring_batch", "Warning", 30, "days"),
        ("Tồn dưới safety stock", "low_stock", "Warning", 0, "qty"),
        ("HĐ sắp hết hạn", "contract_expiring", "Critical", 30, "days"),
        ("HĐ còn ít hạn mức", "fc_remaining_low", "Warning", 20, "percent"),
        ("PI quá hạn thanh toán", "overdue_payment", "Critical", 0, "days"),
        ("PR chờ QC quá hạn", "qc_pending", "Warning", 3, "days"),
    ]
    count = 0
    for title, atype, sev, thr, unit in rules:
        if frappe.db.exists("SC Alert Rule", {"title": title}):
            continue
        r = frappe.new_doc("SC Alert Rule")
        r.title = title
        r.alert_type = atype
        r.severity = sev
        r.enabled = 1
        r.frequency = "Daily"
        r.threshold_value = thr
        r.threshold_operator = "<="
        r.threshold_unit = unit
        r.channel_email = 1
        r.channel_inapp = 1
        r.channel_sms = 0
        r.recipient_roles = "SupplyCore Manager,SupplyCore Storekeeper"
        r.flags.ignore_permissions = True
        r.insert()
        count += 1
    return count


def _set_safety_stock_on_items() -> int:
    """Set safety_stock + reorder_level + has_batch_no mix cho items via raw SQL
    để bypass SC Item validate (có thể reject has_batch_no mutation)."""
    items = frappe.get_all("SC Item",
        filters={"is_stock_item": 1, "disabled": 0},
        fields=["name"], limit=12, order_by="name")
    count = 0
    for i, it in enumerate(items):
        safety = 50 + (i * 10)
        reorder = safety * 2
        has_batch = 1 if i < 6 else 0
        try:
            frappe.db.sql("""
                UPDATE `tabSC Item` SET
                    safety_stock = %s, reorder_level = %s,
                    has_batch_no = %s
                WHERE name = %s
            """, (safety, reorder, has_batch, it.name))
            count += 1
        except Exception:
            pass
    frappe.db.commit()
    return count


# =====================================================================
# SEED SCENARIO — 11 phases mapped to UCs
# =====================================================================
def seed_scenario() -> dict:
    """11 phases: Procurement → Receiving → Storage → Dispensing → Accounting
    → Stocktake → Recall → Investigation → Dashboard."""
    log = []
    ctx = {}  # context — pass docs across phases

    log.append(("Phase 1: FC submitted (UC-01-04)", _phase1_fc_already_done(ctx)))
    log.append(("Phase 2: PP + MR (UC-05-07)", _phase2_planning(ctx)))
    log.append(("Phase 3: PO + Approval (UC-08)", _phase3_purchase_orders(ctx)))
    log.append(("Phase 4: PR + QI + Return (UC-09-14)", _phase4_receiving(ctx)))
    log.append(("Phase 5: Initial stock + Transfer (UC-15-18)", _phase5_initial_stock(ctx)))
    log.append(("Phase 6: DR + Dispensing + BHYT (UC-19-23)", _phase6_dispensing(ctx)))
    log.append(("Phase 7: PI + 3-way + PE (UC-24-27)", _phase7_accounting(ctx)))
    log.append(("Phase 8: Stocktake (UC-28)", _phase8_stocktake(ctx)))
    log.append(("Phase 9: Recall (UC-30)", _phase9_recall(ctx)))
    log.append(("Phase 10: Investigation (UC-31)", _phase10_investigation(ctx)))
    log.append(("Phase 11: Scan alerts + lifecycle (UC-33-34)", _phase11_alerts(ctx)))

    frappe.db.commit()
    return {"phases": log, "ctx_keys": list(ctx.keys())}


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def _pick_warehouse(suffix: str = "") -> str:
    """Pick a non-group warehouse by name suffix."""
    if suffix:
        wh = frappe.db.get_value("SC Warehouse",
            {"is_group": 0, "disabled": 0, "warehouse_name": ["like", f"%{suffix}%"]},
            "name")
        if wh:
            return wh
    return frappe.db.get_value("SC Warehouse",
        {"is_group": 0, "disabled": 0}, "name")


def _all_warehouses(limit=10):
    return frappe.get_all("SC Warehouse",
        filters={"is_group": 0, "disabled": 0},
        pluck="name", limit=limit, order_by="name")


def _pick_supplier(idx=0):
    rows = frappe.get_all("SC Supplier", filters={"disabled": 0},
                          pluck="name", order_by="name")
    return rows[idx] if idx < len(rows) else (rows[0] if rows else None)


def _pick_items(n=5, with_bhyt_only=False):
    filters = {"disabled": 0, "is_stock_item": 1}
    if with_bhyt_only:
        filters["has_bhyt"] = 1
    return frappe.get_all("SC Item", filters=filters,
                          pluck="name", order_by="name", limit=n)


def _seed_sle_raw(item, warehouse, qty, batch=None, vtype="Manual",
                   posting_date=None, valuation_rate=10000):
    """Manual SLE — for initial stock seeding only."""
    from supplycore.supplycore.doctype.sc_stock_ledger_entry.sc_stock_ledger_entry import SCStockLedgerEntry
    return SCStockLedgerEntry.post(
        item=item, warehouse=warehouse,
        qty_change=flt(qty), batch=batch,
        valuation_rate=flt(valuation_rate),
        voucher_type=vtype, voucher_no=f"SEED-{random_string(6)}",
        posting_date=posting_date or today(),
    )


# ---------------------------------------------------------------------
# PHASE 1 — FC đã tạo ở seed_master (UC-01..04)
# ---------------------------------------------------------------------
def _phase1_fc_already_done(ctx):
    fcs = frappe.get_all("Framework Contract",
        filters={"status": "Active"}, fields=["name", "supplier", "valid_to"])
    ctx["fcs"] = fcs
    return {"fc_count": len(fcs)}


# ---------------------------------------------------------------------
# PHASE 2 — Planning: 1 PP + 3 MR (UC-05, UC-07)
# ---------------------------------------------------------------------
def _phase2_planning(ctx):
    items = _pick_items(10)
    whs = _all_warehouses(limit=2)
    wh = whs[0] if whs else None
    ctx["wh_main"] = wh
    ctx["wh_secondary"] = whs[1] if len(whs) > 1 else wh
    sup = _pick_supplier(0)

    # 3 Material Requests
    mrs = []
    for i in range(3):
        mr = frappe.new_doc("SC Material Request")
        mr.request_type = "Purchase"
        mr.transaction_date = add_days(today(), -7 + i)
        mr.schedule_date = add_days(today(), 7)
        mr.warehouse = wh
        mr.remarks = f"MR scenario seed #{i+1}"
        for j, item in enumerate(items[i*2:(i*2)+2]):
            mr.append("items", {
                "item": item,
                "qty": 100 + (j * 50),
                "uom": frappe.db.get_value("SC Item", item, "uom"),
                "schedule_date": add_days(today(), 7),
            })
        mr.flags.ignore_permissions = True
        try:
            mr.insert()
            mr.submit()
            mrs.append(mr.name)
        except Exception as e:
            frappe.log_error(message=f"MR {i}: {str(e)[:300]}", title="seed_uc phase2")
    ctx["mrs"] = mrs
    return {"mrs_created": len(mrs)}


# ---------------------------------------------------------------------
# PHASE 3 — PO: 3 POs (1 from FC, 1 normal, 1 over-budget for alt flow)
# ---------------------------------------------------------------------
def _phase3_purchase_orders(ctx):
    fcs = ctx.get("fcs", [])
    items = _pick_items(10)
    sup_default = _pick_supplier(0)
    wh = ctx.get("wh_main") or _pick_warehouse()
    pos = []

    for i in range(3):
        po = frappe.new_doc("SC Purchase Order")
        po.supplier = fcs[i].supplier if i < len(fcs) else sup_default
        po.transaction_date = add_days(today(), -5 + i)
        po.schedule_date = add_days(today(), 10)
        if i < len(fcs):
            po.framework_contract = fcs[i].name
        # Use items[0:3], [3:6], [6:9] — only first 9 items
        slice_start = i * 3
        for j, item in enumerate(items[slice_start:slice_start + 3]):
            uom = frappe.db.get_value("SC Item", item, "uom")
            po.append("items", {
                "item": item, "uom": uom,
                "qty": 50 + (j * 25),
                "rate": 15000 + (j * 5000),
                "warehouse": wh,
                "schedule_date": add_days(today(), 10),
            })
        # Bypass 2-tier approval
        po.approval_stage = "Approved"
        po.flags.ignore_permissions = True
        try:
            po.insert()
            po.submit()
            pos.append(po.name)
        except Exception as e:
            frappe.log_error(message=f"PO {i}: {str(e)[:300]}", title="seed_uc phase3")
    ctx["pos"] = pos
    return {"pos_created": len(pos)}


# ---------------------------------------------------------------------
# PHASE 4 — PR + QI + Return (UC-09..14)
# ---------------------------------------------------------------------
def _phase4_receiving(ctx):
    pos = ctx.get("pos", [])
    prs = []
    qis = []
    return_prs = []

    for i, po_name in enumerate(pos[:2]):  # 2 normal PRs
        try:
            po = frappe.get_doc("SC Purchase Order", po_name)
            pr = frappe.new_doc("SC Purchase Receipt")
            pr.supplier = po.supplier
            pr.purchase_order = po.name
            pr.posting_date = add_days(today(), -3 + i)
            pr.to_warehouse = po.items[0].warehouse
            pr.qc_required = 1
            for r in po.items:
                has_batch = int(frappe.db.get_value("SC Item", r.item, "has_batch_no") or 0)
                pr_item = {
                    "item": r.item, "uom": r.uom,
                    "qty": flt(r.qty),  # full receive
                    "po_qty": flt(r.qty),
                    "rate": flt(r.rate),
                    "warehouse": r.warehouse,
                }
                if has_batch:
                    pr_item.update({
                        "supplier_batch_no": f"LOT-{i}-{r.idx}-{random_string(4)}",
                        "manufacturing_date": add_days(today(), -90),
                        "expiry_date": add_days(today(), 365 if i == 0 else 100),
                    })
                pr.append("items", pr_item)
            pr.flags.ignore_permissions = True
            pr.insert()
            pr.submit()
            prs.append(pr.name)

            # Tạo QI cho mỗi item của PR đầu (QI là per-item, not list)
            if i == 0:
                pr_reload = frappe.get_doc("SC Purchase Receipt", pr.name)
                for r in pr_reload.items:
                    if not r.batch_no:
                        continue  # only batch items
                    try:
                        qi = frappe.new_doc("SC Quality Inspection")
                        qi.purchase_receipt = pr.name
                        qi.item = r.item
                        qi.batch = r.batch_no
                        qi.inspection_date = today()
                        qi.inspected_by = "Administrator"
                        qi.overall_status = "Accepted"
                        qi.qty_inspected = flt(r.qty)
                        qi.qty_accepted = flt(r.qty)
                        qi.qty_rejected = 0
                        # SC QI Reading: ≥1 reading bắt buộc trước submit
                        for spec in ("Cảm quan", "Bao bì", "Nhãn mác"):
                            qi.append("readings", {
                                "specification": spec,
                                "status": "Accepted",
                                "value": "Đạt",
                            })
                        qi.flags.ignore_permissions = True
                        qi.insert()
                        try:
                            qi.submit()
                        except Exception as e:
                            frappe.log_error(message=f"QI submit: {str(e)[:200]}",
                                              title="seed_uc phase4 qi submit")
                        qis.append(qi.name)
                    except Exception as e:
                        frappe.log_error(message=f"QI: {str(e)[:200]}",
                                          title="seed_uc phase4 qi")
        except Exception as e:
            frappe.log_error(message=f"PR {po_name}: {str(e)[:300]}",
                              title="seed_uc phase4 pr")

    # 1 Return PR — UC-11
    if prs:
        try:
            ref_pr = frappe.get_doc("SC Purchase Receipt", prs[0])
            rpr = frappe.new_doc("SC Purchase Receipt")
            rpr.supplier = ref_pr.supplier
            rpr.posting_date = today()
            rpr.is_return = 1
            rpr.return_reason = "Phát hiện sai quy cách"
            rpr.to_warehouse = ref_pr.to_warehouse
            r0 = ref_pr.items[0]
            rpr.append("items", {
                "item": r0.item, "uom": r0.uom,
                "batch_no": r0.batch_no,
                "qty": flt(r0.qty) * 0.1,  # return 10%
                "rate": flt(r0.rate),
                "warehouse": r0.warehouse,
            })
            rpr.flags.ignore_permissions = True
            rpr.insert()
            rpr.submit()
            return_prs.append(rpr.name)
        except Exception as e:
            frappe.log_error(message=f"Return PR: {str(e)[:300]}",
                              title="seed_uc phase4 return")

    ctx["prs"] = prs
    ctx["qis"] = qis
    ctx["return_prs"] = return_prs
    return {"prs": len(prs), "qis": len(qis), "return_prs": len(return_prs)}


# ---------------------------------------------------------------------
# PHASE 5 — Initial stock + Transfer + Quarantine batch (UC-15..18)
# ---------------------------------------------------------------------
def _phase5_initial_stock(ctx):
    """Tạo:
    - SLE seed cho 5 items chưa qua PR (initial stock direct)
    - 1 SE Material Transfer (Kho Tổng → Kho Khoa Dược)
    - 1 batch short-expiry với ack (UC-15a)
    - 1 batch blocked manual (cho UC-30)
    """
    items_no_batch = frappe.get_all("SC Item",
        filters={"disabled": 0, "is_stock_item": 1, "has_batch_no": 0},
        pluck="name", limit=5)
    items_with_batch = frappe.get_all("SC Item",
        filters={"disabled": 0, "is_stock_item": 1, "has_batch_no": 1},
        pluck="name", limit=5)
    wh_main = ctx.get("wh_main") or _pick_warehouse()
    wh_dept = ctx.get("wh_secondary") or wh_main
    # Make sure they differ for transfer
    if wh_main == wh_dept:
        whs = _all_warehouses(limit=2)
        if len(whs) > 1:
            wh_dept = whs[1]

    # Initial stock SLE
    sle_count = 0
    for item in items_no_batch:
        _seed_sle_raw(item, wh_main, 500, valuation_rate=20000,
                       posting_date=add_days(today(), -30))
        sle_count += 1

    # Short-expiry batch (UC-15 alt 4a)
    short_batches = []
    if items_with_batch:
        from supplycore.m5_fefo.api.batch_helpers import generate_batch_id
        item = items_with_batch[0]
        expiry = add_days(today(), 90)  # <6 tháng = short
        batch = frappe.new_doc("SC Batch")
        batch.batch_id = generate_batch_id(item, str(expiry))
        batch.item = item
        batch.expiry_date = expiry
        batch.manufacturing_date = add_days(expiry, -730)
        batch.qc_status = "Accepted"
        batch.supplier = _pick_supplier(0)
        batch.supplier_batch_no = f"SHORTLOT-{random_string(5)}"
        batch.is_short_expiry = 1
        batch.short_expiry_ack = 1
        batch.short_expiry_ack_by = "Administrator"
        batch.flags.ignore_permissions = True
        batch.flags.ignore_short_expiry = 1
        try:
            batch.insert()
            short_batches.append(batch.name)
            _seed_sle_raw(item, wh_main, 200, batch=batch.name,
                           valuation_rate=15000)
        except Exception as e:
            frappe.log_error(message=f"short batch: {str(e)[:200]}",
                              title="seed_uc phase5")

    # SE Material Transfer
    transfers = []
    try:
        if items_no_batch:
            se = frappe.new_doc("SC Stock Entry")
            se.entry_type = "Material Transfer"
            se.posting_date = today()
            se.from_warehouse = wh_main
            se.to_warehouse = wh_dept
            se.purpose = "Phân kho từ Kho Tổng xuống Kho Khoa Dược"
            for item in items_no_batch[:3]:
                uom = frappe.db.get_value("SC Item", item, "uom")
                se.append("items", {
                    "item": item, "uom": uom, "qty": 100,
                    "valuation_rate": 20000,
                    "s_warehouse": wh_main, "t_warehouse": wh_dept,
                })
            se.flags.ignore_permissions = True
            se.insert()
            se.submit()
            transfers.append(se.name)
    except Exception as e:
        frappe.log_error(message=f"SE transfer: {str(e)[:300]}",
                          title="seed_uc phase5 se")

    ctx["short_batches"] = short_batches
    ctx["transfers"] = transfers
    return {"initial_sle": sle_count, "short_batches": len(short_batches),
            "transfers": len(transfers)}


# ---------------------------------------------------------------------
# PHASE 6 — DR + Patient Dispensing + BHYT (UC-19..23)
# ---------------------------------------------------------------------
def _phase6_dispensing(ctx):
    patients = frappe.get_all("SC Patient", filters={"disabled": 0},
                                pluck="name", limit=5)
    items_bhyt = _pick_items(3, with_bhyt_only=True)
    if not items_bhyt:
        items_bhyt = _pick_items(3)
    # Phase 6: dispense FROM where stock exists (= wh_main where PR + Transfer landed)
    wh_dept = ctx.get("wh_main") or _pick_warehouse()
    depts = frappe.get_all("SC Department", filters={"disabled": 0},
                            pluck="name", limit=3)

    drs = []
    pds = []

    # 3 Dispensing Requests
    for i in range(3):
        try:
            dr = frappe.new_doc("SC Dispensing Request")
            dr.request_date = add_days(today(), -1)
            dr.from_warehouse = wh_dept
            dr.department = depts[i % len(depts)] if depts else None
            dr.priority = "Normal"
            for item in items_bhyt[:2]:
                uom = frappe.db.get_value("SC Item", item, "uom")
                dr.append("items", {
                    "item": item, "uom": uom,
                    "requested_qty": 10,
                })
            dr.flags.ignore_permissions = True
            dr.insert()
            dr.submit()
            drs.append(dr.name)
        except Exception as e:
            frappe.log_error(message=f"DR {i}: {str(e)[:300]}",
                              title="seed_uc phase6 dr")

    # 4 PD: 3 with BHYT, 1 alt (no card)
    for i, p in enumerate(patients[:4]):
        try:
            pd = frappe.new_doc("SC Patient Dispensing")
            pd.dispensing_date = today()
            pd.patient = p
            patient_doc = frappe.db.get_value("SC Patient", p,
                ["bhyt_card_no", "bhyt_payment_rate", "current_department"],
                as_dict=True)
            pd.bhyt_card_no = patient_doc.bhyt_card_no if i < 3 else None
            pd.bhyt_payment_rate = patient_doc.bhyt_payment_rate or 80
            pd.ward = patient_doc.current_department or (depts[0] if depts else None)
            # Find item with stock available
            for item in items_bhyt[:2]:
                qty_available = flt(frappe.db.sql("""
                    SELECT COALESCE(SUM(qty_change), 0)
                    FROM `tabSC Stock Ledger Entry`
                    WHERE item = %s AND warehouse = %s AND is_cancelled = 0
                """, (item, wh_dept))[0][0])
                if qty_available < 2:
                    continue
                uom = frappe.db.get_value("SC Item", item, "uom")
                pd.append("items", {
                    "item": item,
                    "uom": uom,
                    "qty": 2,
                    "unit_cost": 25000,
                    "warehouse": wh_dept,
                })
            if not pd.items:
                continue
            pd.flags.ignore_permissions = True
            pd.insert()
            pd.submit()
            pds.append(pd.name)
        except Exception as e:
            frappe.log_error(message=f"PD {i}: {str(e)[:300]}",
                              title="seed_uc phase6 pd")

    ctx["drs"] = drs
    ctx["pds"] = pds
    return {"drs": len(drs), "pds": len(pds)}


# ---------------------------------------------------------------------
# PHASE 7 — PI + 3-way match + PE (UC-24..27)
# ---------------------------------------------------------------------
def _phase7_accounting(ctx):
    prs = ctx.get("prs", [])
    pis = []
    pes = []

    for pr_name in prs[:2]:
        try:
            pr = frappe.get_doc("SC Purchase Receipt", pr_name)
            pi = frappe.new_doc("SC Purchase Invoice")
            pi.supplier = pr.supplier
            pi.invoice_date = today()
            pi.due_date = add_days(today(), 30)
            pi.purchase_receipt = pr.name
            pi.supplier_invoice_no = f"INV-{random_string(6)}"
            for r in pr.items:
                pi.append("items", {
                    "item": r.item, "uom": r.uom,
                    "qty": flt(r.qty),
                    "rate": flt(r.rate),
                    "warehouse": r.warehouse,
                    "purchase_receipt_item": r.name,
                })
            pi.flags.ignore_permissions = True
            pi.insert()
            pi.submit()
            pis.append(pi.name)
        except Exception as e:
            frappe.log_error(message=f"PI {pr_name}: {str(e)[:300]}",
                              title="seed_uc phase7 pi")

    # 1 Payment cho PI đầu (partial)
    if pis:
        try:
            pi_doc = frappe.get_doc("SC Purchase Invoice", pis[0])
            pe = frappe.new_doc("SC Payment Entry")
            pe.payment_date = today()
            pe.supplier = pi_doc.supplier
            pe.amount = flt(pi_doc.outstanding_amount) * 0.5
            pe.payment_method = "Bank Transfer"
            pe.append("references", {
                "purchase_invoice": pi_doc.name,
                "allocated_amount": flt(pi_doc.outstanding_amount) * 0.5,
            })
            pe.flags.ignore_permissions = True
            pe.insert()
            pe.submit()
            pes.append(pe.name)
        except Exception as e:
            frappe.log_error(message=f"PE: {str(e)[:300]}",
                              title="seed_uc phase7 pe")

    ctx["pis"] = pis
    ctx["pes"] = pes
    return {"pis": len(pis), "pes": len(pes)}


# ---------------------------------------------------------------------
# PHASE 8 — Stocktake (UC-28)
# ---------------------------------------------------------------------
def _phase8_stocktake(ctx):
    wh = _pick_warehouse("Khoa Dược") or _pick_warehouse()
    items = _pick_items(3)
    ics_count = 0
    sr_count = 0

    # 1 ICS + 1 SR
    try:
        ics = frappe.new_doc("SC Inventory Count Sheet")
        ics.posting_date = today()
        ics.warehouse = wh
        ics.count_type = "Cycle"
        for item in items:
            sys_qty = flt(frappe.db.sql("""
                SELECT COALESCE(SUM(qty_change), 0)
                FROM `tabSC Stock Ledger Entry`
                WHERE item = %s AND warehouse = %s AND is_cancelled = 0
            """, (item, wh))[0][0])
            uom = frappe.db.get_value("SC Item", item, "uom")
            counted = max(0, sys_qty - 2)  # variance -2 nhưng floor=0
            ics.append("items", {
                "item": item, "uom": uom,
                "system_qty": sys_qty,
                "counted_qty": counted,
                "valuation_rate": 10000,
            })
        ics.flags.ignore_permissions = True
        ics.insert()
        ics.submit()
        ics_count += 1

        # SR từ ICS — load items manual để tránh load_from_count_sheet edge cases
        sr = frappe.new_doc("SC Stock Reconciliation")
        sr.posting_date = today()
        sr.warehouse = wh
        sr.count_sheet = ics.name
        for ci in ics.items:
            sr.append("items", {
                "item": ci.item, "uom": ci.uom,
                "actual_qty": flt(ci.counted_qty),
                "system_qty": flt(ci.system_qty),
                "valuation_rate": flt(ci.valuation_rate or 10000),
                "reason": "Counting Error",
            })
        sr.flags.ignore_permissions = True
        sr.insert()
        try:
            sr.submit()
            sr_count += 1
        except Exception as e:
            frappe.log_error(message=f"SR submit: {str(e)[:200]}",
                              title="seed_uc phase8 sr")
    except Exception as e:
        frappe.log_error(message=f"Stocktake: {str(e)[:300]}",
                          title="seed_uc phase8")

    return {"ics": ics_count, "sr": sr_count}


# ---------------------------------------------------------------------
# PHASE 9 — Recall (UC-30)
# ---------------------------------------------------------------------
def _phase9_recall(ctx):
    short_batches = ctx.get("short_batches", [])
    # Use first short batch as recalled (already has stock from phase5)
    if not short_batches:
        return {"recall_notices": 0}
    batch_name = short_batches[0]
    batch_doc = frappe.db.get_value("SC Batch", batch_name,
        ["item", "supplier"], as_dict=True)
    if not batch_doc:
        return {"recall_notices": 0}

    try:
        rn = frappe.new_doc("SC Recall Notice")
        rn.recall_date = today()
        rn.recall_type = "Voluntary"
        rn.severity = "Class II (High)"
        rn.item = batch_doc.item
        rn.batch_no = batch_name
        rn.supplier = batch_doc.supplier
        rn.recall_reason = "NCC phát hiện nguy cơ ô nhiễm vi sinh — thu hồi tự nguyện"
        rn.flags.ignore_permissions = True
        rn.insert()
        rn.populate_affected_items()
        rn.submit()
        ctx["recall"] = rn.name
        return {"recall_notices": 1, "name": rn.name}
    except Exception as e:
        frappe.log_error(message=f"Recall: {str(e)[:300]}",
                          title="seed_uc phase9")
        return {"recall_notices": 0, "error": str(e)[:100]}


# ---------------------------------------------------------------------
# PHASE 10 — Investigation (UC-31)
# ---------------------------------------------------------------------
def _phase10_investigation(ctx):
    items = _pick_items(1)
    wh = _pick_warehouse()
    if not items or not wh:
        return {"investigations": 0}
    try:
        inv = frappe.new_doc("SC Investigation Report")
        inv.investigation_date = today()
        inv.investigation_type = "Discrepancy"
        inv.item = items[0]
        inv.warehouse = wh
        inv.period_start = add_days(today(), -30)
        inv.period_end = today()
        inv.description = "Phát hiện chênh lệch tồn kho sau stocktake — điều tra nguyên nhân"
        inv.actual_qty = 50  # giả định count
        inv.flags.ignore_permissions = True
        inv.insert()
        try:
            inv.compare_stock()
            inv.detect_anomalies(large_qty_threshold=100)
        except Exception:
            pass
        inv.reload()
        inv.recommendation = "Tăng cường kiểm kê chu kỳ + train lại nhân viên"
        inv.conclusion = "Variance nằm trong ngưỡng hao hụt thông thường"
        inv.save(ignore_permissions=True)
        inv.submit()
        ctx["investigation"] = inv.name
        return {"investigations": 1, "name": inv.name}
    except Exception as e:
        frappe.log_error(message=f"Investigation: {str(e)[:300]}",
                          title="seed_uc phase10")
        return {"investigations": 0, "error": str(e)[:100]}


# ---------------------------------------------------------------------
# PHASE 11 — Scan alerts + lifecycle (UC-33, UC-34)
# ---------------------------------------------------------------------
def _phase11_alerts(ctx):
    from supplycore.m11_dashboard.tasks import scan_alerts
    try:
        created = scan_alerts()
    except Exception as e:
        frappe.log_error(message=str(e)[:300], title="seed_uc phase11 scan")
        created = 0

    # Pick 1 alert, resolve it; pick another snooze; pick another assign
    alerts = frappe.get_all("SC Alert", filters={"resolved": 0},
                            fields=["name"], limit=3)
    resolved = snoozed = assigned = 0
    for i, a in enumerate(alerts):
        doc = frappe.get_doc("SC Alert", a.name)
        try:
            if i == 0:
                doc.mark_resolved(action="Acted Upon",
                                    remarks="Đã xử lý — refill stock")
                resolved = 1
            elif i == 1:
                doc.snooze_alert(4, "Đang chờ NCC xác nhận")
                snoozed = 1
            elif i == 2:
                doc.assign_alert("Administrator", note="Xin xử lý gấp")
                assigned = 1
        except Exception as e:
            frappe.log_error(message=f"Alert action {i}: {str(e)[:200]}",
                              title="seed_uc phase11 action")

    return {"alerts_created": created, "resolved": resolved,
            "snoozed": snoozed, "assigned": assigned}


# =====================================================================
# Orchestrator
# =====================================================================
def run():
    """Wipe + seed master + seed scenario."""
    wipe_counts = wipe_all()
    master_counts = seed_master()
    scenario = seed_scenario()
    return {
        "wipe": wipe_counts,
        "master": master_counts,
        "scenario": scenario,
    }
