# UC Coverage — Phase 1 Use Cases vs Hệ thống

**Cập nhật:** 2026-05-08
**Source:** `SupplyCore/Phase1_Yeu-Cau-va-Phan-Tich/03_Use-Case-Diagram-and-Descriptions/UseCase_SupplyCore_v2.0.md`
**Test method:** `tests/uc_coverage.py` — kiểm tra existence + wiring của DocType + method + scheduler cho mỗi UC.

## Kết quả tổng hợp

| Status | Count | UCs |
|---|---|---|
| ✅ **OK** (đầy đủ flow chính) | **33/37** | UC-01..05, UC-07..12, UC-14..25, UC-27..31, UC-33..37, UC-11 (vừa fix) |
| ⚠️ **PARTIAL** (DocType có nhưng workflow/UI thiếu) | **4/37** | UC-06, UC-13, UC-26, UC-32 |
| ❌ **MISSING** | **0/37** | — |

**89% coverage** sau khi wire UC-11. Tất cả 4 partials còn lại là defer items đã document trong `FLOW.md` Phase 1.1+.

## Bảng coverage chi tiết

| UC | Tên | Module | Status | Note |
|---|---|---|---|---|
| UC-01 | Search & Evaluate Suppliers | M1 | ✅ | SC Supplier list view + Frappe filter |
| UC-02 | Create / Update Supplier | M1 | ✅ | SC Supplier CRUD |
| UC-03 | Create & Manage Framework Contract | M1 | ✅ | FC + slice 1 wired RO + auto-PO |
| UC-04 | Track Contract Status & Renewal | M1 | ✅ | Daily scheduler check_contract_expiry + email 30/15/7d |
| UC-05 | Set Min/Max Stock Levels | M2 | ✅ | SC Item.safety_stock |
| UC-06 | Create Periodic Procurement Plan | M2 | ⚠️ Partial | Doctype có nhưng `generate_procurement_forecast` scheduler là placeholder. Auto-MR creation defer (cần trend analysis/ML) |
| UC-07 | Create Purchase Request (MR) | M2 | ✅ | SC MR submit → status=Approved (slice 1) |
| UC-08 | Create & Approve PO | M2 | ✅ | create_purchase_orders auto từ MR; approval threshold qua Settings.po_approval_threshold (50tr) |
| UC-09 | Receive Goods & Create PR | M3 | ✅ | SC PR + slice mới make_pr_from_po auto-fetch + on_submit auto-Batch + auto-QI |
| UC-10 | Quality Inspection (QC) | M3 | ✅ | QI auto-tạo từ PR + rollup PR.qc_status + Batch.qc_status |
| **UC-11** | **Handle Supplier Returns** | **M3** | **✅ vừa fix** | **PR.is_return + auto-tạo Return PR draft khi QI Rejected (commit 2026-05-08)** |
| UC-12 | Manage Bin Locations | M4 | ✅ | Bin Location doctype |
| UC-13 | PDA Stock In/Out | M4 | ⚠️ Partial | scan_barcode + confirm_putaway có. PDA offline IndexedDB sync defer Phase 1.1+. UAT-03: signature scan_barcode(barcode, context) ≠ README mô tả |
| UC-14 | Query Stock by Location | M4 | ✅ | SLE list + KPI per warehouse API + Frappe Report Builder cho custom |
| UC-15 | Manage Batch/Lot | M5 | ✅ | SC Batch auto-tạo từ PR.on_submit, format `<item>-<YYYYMM>-<rand>` |
| UC-16 | Issue Stock by FEFO | M5 | ✅ | API get_suggested_batches + SE validate block expired/blocked |
| UC-17 | Alert Near Expiry | M5 | ✅ | scan_expiring_batches scheduler + M11 alert + slice 2 quarantine action |
| UC-18 | Internal Stock Transfer | M6 | ✅ | SC TR + make_stock_entry → SE Material Transfer |
| UC-19 | Adjust Stock | M6 | ✅ | SC Stock Reconciliation + GL adjustment (wire qua M9) |
| UC-20 | Create DR | M7 | ✅ | SC DR submit → status=Approved |
| UC-21 | Process & Dispense | M7 | ✅ | DR Approved → SE Issue (FEFO) → PD; print format dispensing_slip.html có |
| UC-22 | Record Patient Usage | M7 | ✅ | PD + PD Item ghi qty/cost/BHYT/patient_pays |
| UC-23 | Manage BHYT Codes | M7 | ✅ | SC BHYT Code Config N01-N09 + ceiling_price + payment_rate |
| UC-24 | Create & Match PI | M8 | ✅ | SC PI + 3-way match ±1% tolerance + slice 1 make_invoice_from_pr |
| UC-25 | Create PE & Track AP | M8 | ✅ | SC PE + GL Dr 331/Cr 1121 + slice 2 alert action |
| UC-26 | Financial Reports | M8 | ⚠️ Partial | Có API get_executive_dashboard 6 KPI. Trial Balance / AP Aging / Stock Cost report cần build qua Frappe Report Builder UI (defer Phase 1.1+) |
| UC-27 | Plan Inventory Count | M9 | ✅ | SC ICS + cron create_periodic_count daily 1AM |
| UC-28 | Reconcile Stock | M9 | ✅ | ICS → SR → SLE adjustment + GL |
| UC-29 | Trace Item Origin | M10 | ✅ | API get_batch_trace |
| UC-30 | Recall Management | M10 | ✅ | SC Recall Notice + populate + Batch.blocked. Slice 3 spec (email notify + mark contacted) committed nhưng chưa implement code |
| UC-31 | Investigate Stock Loss | M10 | ✅ | API get_audit_trail |
| UC-32 | Executive Dashboard | M11 | ⚠️ Partial | API get_executive_dashboard 6 KPI sẵn. Frontend Workspace + Number Cards (Phase 3 mockup) defer — v1 chỉ JSON |
| UC-33 | Configure Auto-Alerts | M11 | ✅ | SC Alert Rule + 7 alert types + dedup 7-day window |
| UC-34 | View & Action Alerts | M11 | ✅ | Slice 2: 3 alert types có action button (quarantine/MR/PE), 4 types khác resolve thủ công |
| UC-35 | Manage Users & Permissions | SYS | ✅ | Frappe built-in + SupplyCore roles seed |
| UC-36 | Configure System Parameters | SYS | ✅ | SupplyCore Settings (10 fields) |
| UC-37 | Manage Master Data | SYS | ✅ | SC Item + Group + UOM + Department + Warehouse + GL Account + seed_master_data.py |

## 4 Partial UCs — Đề xuất

### UC-06 Procurement Plan (forecast)

**Hiện tại:** `Procurement Plan` doctype có schema, `generate_procurement_forecast` scheduler chỉ log placeholder.

**Đề xuất:**
- **Slice ngắn:** Wire `generate_procurement_forecast` để compute avg consumption 3 tháng từ SLE, tạo MR draft cho item dưới reorder + đủ history. Không cần ML — heuristic đơn giản đủ MVP.
- **Slice dài:** Trend analysis với seasonality (cần dataset 1+ năm). Defer.

**Effort:** 1-2 ngày cho heuristic version.

### UC-13 PDA Offline Sync

**Hiện tại:** `/pda` UI 480px hoạt động online. `scan_barcode` + `confirm_putaway` API OK. UAT-03: signature mismatch với README.

**Đề xuất:**
- **Quick fix:** Update README M4 + alias signature `scan_barcode(barcode, context=None, warehouse=None)` để cả 2 cách gọi đều work.
- **PDA offline IndexedDB:** Major work (IndexedDB store + sync queue + conflict resolution). Defer Phase 1.1+ unless yêu cầu kinh doanh cấp bách.

**Effort quick fix:** 30 phút. **Effort full offline:** 2 tuần.

### UC-26 Financial Reports (Trial Balance, AP Aging, Stock Cost)

**Hiện tại:** API M11 đã có 6 KPI realtime. Chi tiết-level reports chưa.

**Đề xuất:**
- **Frappe Report Builder UI (no code):** ACC tự cấu hình 3 reports qua `/app/report-builder/new`:
  - Trial Balance — query SC GL Entry group by account
  - AP Aging — query SC PI filter docstatus=1, group by aging buckets
  - Stock Cost by Item — query SC SLE × valuation_rate
- **Code-based Script Report:** chỉ cần khi cần aggregation phức tạp + filter động — defer.

**Effort no-code:** 2-4h cho 3 reports (config thuần).

### UC-32 Executive Dashboard Frontend

**Hiện tại:** API `get_executive_dashboard` trả 6 KPI JSON.

**Đề xuất:**
- **Frappe Workspace + Number Cards (no code):** SysAdmin tạo Workspace `/app/build` với 6 Number Card mỗi card gọi API endpoint khác nhau. Phase 3 mockup design system (Navy/Royal palette) áp dụng qua CSS custom.
- **Custom Vue/React frontend:** Phase 3 mockup compliance đầy đủ — defer Phase 2.

**Effort no-code Workspace:** 2-3h.

## Cải tiến đã thực hiện trong session này

### UC-11 wire-up — auto-tạo Return PR khi QI Rejected (commit 2026-05-08)

**File:** `m3_receiving/...sc_quality_inspection.py:_handle_rejected()` + `_create_return_pr()`

**Logic:**
- Khi QI submit overall_status="Rejected"
- Block batch (đã có sẵn)
- **MỚI:** Tạo SC Purchase Receipt draft với:
  - `is_return=1` (qty_sign=-1 trong _post_stock_ledger sẽ trừ kho khi submit)
  - Link supplier + purchase_order + original PR (qua remarks)
  - Items chỉ row tương ứng QI.pr_item_ref + batch
  - qc_required=0 (Return không cần QC lại)
  - **Draft only** — ACC review + adjust + submit để trừ kho thực
- Idempotent: skip nếu đã có PR Return draft cho QI này
- frappe.msgprint với link tới PR Return mới

**Verified:** test thực tế cho QI Reject → Return PR auto-tạo với `SC-PR-2026-01336`, items đầy đủ, link đúng.

## Cách re-run coverage check

```bash
echo "from supplycore.tests import uc_coverage; r=uc_coverage.run_all(); print(f'OK={sum(1 for x in r if x[\"status\"]==\"ok\")} PARTIAL={sum(1 for x in r if x[\"status\"]==\"partial\")} MISSING={sum(1 for x in r if x[\"status\"]==\"missing\")}')" | bench --site supplycore console
```
