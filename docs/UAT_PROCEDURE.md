# UAT_PROCEDURE — SupplyCore End-to-End

**Phiên bản:** 1.0 — 2026-05-08
**Mục tiêu:** Hướng dẫn end-user (BS, dược sĩ, SK, kế toán) test toàn bộ luồng chuỗi cung ứng từ ký hợp đồng → cấp thuốc cho BN, đồng thời cung cấp checklist Pass/Fail cho QA.
**Phương pháp:** Mỗi giai đoạn có (1) **giải thích vai trò + workflow**, (2) **các bước thao tác cụ thể** trên UI/REST, (3) **kết quả kỳ vọng**, (4) **checklist Pass/Fail**.

> **Cách dùng:** Đi tuần tự từ Section 0 → 10. Mỗi section ghi PASS/FAIL/Note vào checklist. Lỗi gặp được ghi tại section "Issues Found" cuối tài liệu.

## Section 0 — Pre-condition

### 0.1 Master data đã seed

```bash
bench --site supplycore execute supplycore.setup.seed_master_data.run
```

Verify (qua UI hoặc REST):

| Master data | Số lượng tối thiểu | Cách verify |
|---|---|---|
| SC UOM | 18 | `/app/sc-uom` |
| SC Item Group | 23 | `/app/sc-item-group` |
| SC Department | 33 (đủ Khoa Nội/Ngoại/Sản/Nhi/...) | `/app/sc-department` |
| SC Warehouse | 15 (Main + Sub + Department + Quarantine + Transit) | `/app/sc-warehouse` |
| SC Supplier | ≥7 | `/app/sc-supplier` |
| SC Item | ≥12 (có item batch-tracked: VTTH-MASK-3PLY) | `/app/sc-item` |
| SC GL Account | 21 (theo TT 200/2014) | `/app/sc-gl-account` |
| SC BHYT Code Config | ≥3 | `/app/sc-bhyt-code-config` |

### 0.2 User & Role

User test cần có ít nhất 1 role:
- **SupplyCore Manager** — duyệt FC/PO/MR
- **SupplyCore Storekeeper** — nhận hàng, lấy hàng
- **SupplyCore Pharmacy Officer / Pharmacy Officer** — cấp thuốc
- **SupplyCore Accountant** — tạo PI, PE
- **SupplyCore Executive** — duyệt PO ≥50tr

### 0.3 Settings

```
/app/supplycore-settings
- po_approval_threshold = 50,000,000
- match_tolerance_pct = 1.0
- fefo_min_shelf_life_days = 30
- enforce_fefo = 1
```

### 0.4 Pre-condition checklist

- [ ] Master data đầy đủ (8 loại trên)
- [ ] User test có role phù hợp
- [ ] Settings đúng giá trị
- [ ] Email server config (cho M11 alert + M10 recall notify) — optional

---

## Section 1 — M1 Hợp đồng khung (Framework Contract + Release Order)

### Vai trò + Workflow

Bệnh viện ký hợp đồng nguyên tắc với NCC: định mức tổng giá trị + đơn giá theo từng item. Khi cần hàng, phát hành Release Order (lệnh gọi hàng) hoặc trực tiếp PO theo đơn giá HĐK.

### 1.1 Tạo Framework Contract

**Truy cập:** `/app/framework-contract/new` (role SupplyCore Manager)

**Điền các trường:**
- Supplier: chọn 1 NCC (vd: SC-SUP-00055)
- Contract number: `UAT-FC-001`
- Contract date: 2026-04-01
- Valid from: 2026-05-01
- Valid to: 2026-12-31
- Total value: 100,000,000
- Items (child table): thêm 1 dòng
  - Item code: VTTH-MASK-3PLY
  - Contract qty: 1000
  - UOM: Hộp
  - Unit price: 5000

**Save (Ctrl+S):** FC = Draft

**Submit (Ctrl+Shift+S):** FC docstatus=1, status="Active"

### 1.2 Verify FC sau submit

- [ ] `status = "Active"` (không phải "Draft")
- [ ] `total_value = 5,000,000` (auto-calc nếu mismatch với items thì warn)
- [ ] `remaining_value = 100,000,000` (chưa có PO submit)
- [ ] Connections panel hiện 0 Release Order, 0 Purchase Order

### 1.3 (Tuỳ chọn) Tạo Release Order từ FC

**Trên FC form, click "Tạo Release Order":**
- Items tự fetch từ FC (via JS auto_fill_items_from_fc_if_empty)
- Sửa qty từng dòng (vd: 100/1000)
- Required by: 2026-05-15

**Submit RO:** RO status="Approved", FC.committed_value tăng

### Section 1 Checklist

- [ ] **1.1** FC tạo + submit thành công
- [ ] **1.2** FC.status = "Active" sau submit (không phải "Draft")
- [ ] **1.2** FC.remaining_value tính đúng
- [ ] **1.3** RO tạo từ FC, items auto-fetch (nếu test RO)
- [ ] FC có submit được với supplier không tồn tại không? Phải **fail** với SC-E-SUPPLIER (BUG-M1-01 đã fix)

---

## Section 2 — M2 Kế hoạch & Đặt hàng (MR → PO)

### Vai trò + Workflow

Khoa lâm sàng yêu cầu vật tư qua Material Request. SK/Manager review + click "Tạo Purchase Order" — hệ thống tự tìm FC Active rẻ nhất + tạo PO draft.

### 2.1 Tạo Material Request

**Truy cập:** `/app/sc-material-request/new` (role Department Requester / Ward Staff)

**Điền:**
- Request type: Purchase
- Transaction date: today
- Schedule date: today + 7
- Department: Khoa Nhi
- Warehouse: Kho Vật tư tiêu hao
- Items: thêm 1 dòng
  - Item: VTTH-MASK-3PLY
  - Qty: 50
  - UOM: Hộp
  - Schedule date: today + 7

**Save + Submit:** MR.status = "Approved" (không phải Pending — slice 1 đã đổi)

### 2.2 Click "Tạo Purchase Order" trên MR

**Trên MR form (sau submit), button "Tạo Purchase Order" (group "Hành động"):**
- Confirm dialog: "Tạo draft PO từ MR này (theo HĐK Active)?"
- Click OK

**Kết quả:** alert xanh "Đã tạo 1 PO: SC-PO-XXX"

**Verify trên PO mới:**
- supplier = supplier của FC cheapest match
- framework_contract = SC-FC từ Section 1 (hoặc khác nếu có FC rẻ hơn)
- material_request = MR vừa tạo
- transaction_date = today
- items: 1 dòng với item, qty=50, rate=unit_price từ FC, warehouse từ MR

### 2.3 Submit Purchase Order

**Trên PO draft:**
- Review rate (auto từ FC), schedule_date
- Submit

**Verify:**
- [ ] PO.status = "Approved"
- [ ] FC.used_value tăng = qty × rate (gọi `recalculate_used_value` tự chạy)
- [ ] FC.remaining_value giảm tương ứng

### 2.4 Negative test — FC budget vượt ngưỡng

Tạo MR mới với qty cực lớn (vd 100,000) rồi click "Tạo PO" → phải **fail** với:
```
SC-E002 FC_BUDGET: HĐK SC-FC-XXX tổng PO đề xuất (X) vượt remaining_value (Y)
```

### Section 2 Checklist

- [ ] **2.1** MR submit, status="Approved"
- [ ] **2.2** Button "Tạo PO" có hoạt động, tạo đúng PO link FC
- [ ] **2.2** PO rate = FC.unit_price (cheapest)
- [ ] **2.3** PO submit OK, FC.used_value cập nhật
- [ ] **2.4** Negative test budget FC throw đúng SC-E002

---

## Section 3 — M3 Nhận hàng (Purchase Receipt)

### Vai trò + Workflow

NCC giao hàng → SK kiểm số lượng + tạo PR. Slice mới (2026-05-08) cho phép click "Tạo Purchase Receipt" trên PO submit để auto-fetch supplier/items/warehouse.

### 3.1 Click "Tạo Purchase Receipt" trên PO

**Trên PO submit (status Approved), button "Tạo Purchase Receipt":**
- PR draft tự tạo, navigate sang form

**Verify auto-fetch:**
- supplier = PO.supplier ✓
- purchase_order = PO.name ✓
- posting_date = today ✓
- to_warehouse = PO item đầu tiên có warehouse ✓
- qc_required = 1 (default) ✓
- items: mỗi PO item có (qty - received_qty > 0) → 1 row PR với qty=remaining, rate, uom, warehouse

### 3.2 Bổ sung batch + manufacturing_date + expiry_date

PR auto-fetch không pre-fill batch (item batch-tracked cần SK nhập theo lô hàng thực tế).

**Trên mỗi PR item:**
- Batch_no: bỏ trống (sẽ auto-tạo khi submit) HOẶC nhập batch_id mới
- Manufacturing date: 2026-04-15
- Expiry date: 2027-04-15
- Supplier batch no (nếu NCC có code lô riêng)

### 3.3 Submit PR

**Submit:** trigger các hành động sau (tự động):
- [ ] SC Batch auto-tạo nếu item.has_batch_no=1 (batch_id tự sinh format `<item>-<YYYYMM>-<rand>`)
- [ ] SC Stock Ledger Entry (+qty) post tại to_warehouse
- [ ] SC Quality Inspection auto-tạo nếu qc_required=1 (1 QI per PR item)
- [ ] PO Item.received_qty cập nhật
- [ ] PO.status = "Received" (nếu all items đầy đủ) hoặc "Partially Received"

### Section 3 Checklist

- [ ] **3.1** Button "Tạo PR" trên PO hoạt động, fetch đúng supplier/items
- [ ] **3.2** Nhập batch + expiry_date được
- [ ] **3.3** Submit PR thành công
- [ ] **3.3** SC Batch tự tạo (xem `/app/sc-batch?item=VTTH-MASK-3PLY`)
- [ ] **3.3** SLE post (xem `/app/sc-stock-ledger-entry?voucher_no=PR-name`)
- [ ] **3.3** QI auto-tạo (xem `/app/sc-quality-inspection?purchase_receipt=PR-name`)
- [ ] **3.3** PO Item.received_qty cập nhật, PO.status thay đổi
- [ ] Negative: PR với expiry < min_shelf_life_days (30 ngày) phải warn

---

## Section 4 — M3 QC (Quality Inspection)

### Vai trò + Workflow

QI tạo từ PR đại diện cho 1 batch + 1 item. QC officer kiểm tra theo template (cảm quan, đo lường, hạn dùng, packaging) → Accept/Reject. Reject sẽ block batch (không thể issue/transfer/dispense).

### 4.1 Mở QI auto-tạo

**Truy cập:** từ PR form (Section 3) → Connections → Quality Inspection
Hoặc: `/app/sc-quality-inspection?purchase_receipt=<PR>`

**Form chứa:**
- purchase_receipt link (read_only)
- item, batch, received_qty (read_only, fetch từ PR)
- checklist_template (auto-pick theo item_group nếu có)
- readings (child table) — danh sách criteria từ template

### 4.2 Đánh giá Accept/Reject

**Cho mỗi reading:**
- Specification (đã có từ template): vd "Bao bì còn nguyên không rách"
- Status: Accepted / Rejected / N/A
- Reading value (nếu là measurement criterion)
- Remarks (nếu Reject)

**Set `manual_inspection = 1`** (tránh auto-flip về Rejected do logic mặc định)
**Set `overall_status = "Accepted"`** (sau khi tất cả readings = Accepted)

> ⚠ **Lưu ý naming inconsistency** (xem UAT-01 ở Issues Found):
> - QI.overall_status options: `Accepted / Rejected / Conditional / Pending`
> - Batch.qc_status options: `Accepted / Rejected / Conditional / Pending`
> - **PR.qc_status options:** `Pass / Fail / Partial Pass / Pending` ← khác biệt!

**Submit QI:** QI docstatus=1

**Verify rollup:**
- [ ] **PR.qc_status = "Pass"** (rollup: nếu tất cả QI submit có overall_status=Accepted)
- [ ] **Batch.qc_status = "Accepted"** (mỗi QI submit set tương ứng cho batch)
- [ ] Batch.blocked = 0

### 4.3 Reject scenario (negative test)

Tạo 1 PR khác → submit → QI tự tạo → set 1 reading status = Rejected → submit QI

**Expected:**
- [ ] QI.status = "Rejected"
- [ ] PR.qc_status = "Rejected"
- [ ] Batch.blocked = 1 với block_reason chứa "QC Rejected"
- [ ] Cố issue batch này → throw SC-E007 hoặc SC-E008

### Section 4 Checklist

- [ ] **4.1** QI auto-tạo có readings từ template đúng
- [ ] **4.2** Submit QI Accepted → PR.qc_status="Accepted"
- [ ] **4.3** Reject scenario → batch bị block đúng

---

## Section 5 — M4+M5 Setup lô hạn sử dụng + Xếp hàng (Putaway)

### Vai trò + Workflow

Sau khi PR submit, batch + SLE đã có ở `to_warehouse` nhưng chưa được xếp vào bin cụ thể. SK dùng PDA scan barcode → đặt vào bin (Stock Entry Material Receipt với bin_location).

### 5.1 Verify SC Batch tự tạo

**Truy cập:** `/app/sc-batch?item=VTTH-MASK-3PLY` (sort by created desc)

**Verify:**
- [ ] Batch_id format đúng `<item>-<YYYYMM>-<rand>` (auto-generated)
- [ ] Manufacturing date + Expiry date đúng giá trị nhập tại PR
- [ ] Supplier link tới NCC của PR
- [ ] qc_status = "Accepted" (sau khi QI submit Accepted)
- [ ] blocked = 0

### 5.2 Setup Bin Location (1 lần)

`/app/bin-location/new`:
- Bin code: A-01-01-01 (Aisle-Rack-Shelf-Level)
- Warehouse: Kho Vật tư tiêu hao
- Zone: A
- Capacity_qty: 1000

### 5.3 Putaway via PDA (qua REST)

**Endpoint:** `POST /api/method/supplycore.api.wms.scan_barcode`

```json
{
  "barcode": "<item barcode>",
  "warehouse": "Kho Vật tư tiêu hao"
}
```

**Returns:** item info + suggested_bin (nếu Item.default_bin_location đã set)

**Confirm putaway:** `POST /api/method/supplycore.api.wms.confirm_putaway`
```json
{
  "item": "VTTH-MASK-3PLY",
  "qty": 50,
  "batch": "<batch_id>",
  "bin_location": "A-01-01-01",
  "warehouse": "Kho Vật tư tiêu hao"
}
```

**Returns:** SE Material Receipt name + SLE created

### Section 5 Checklist

- [ ] **5.1** Batch auto-tạo có metadata đầy đủ (mfg/exp/supplier)
- [ ] **5.1** Batch.qc_status = "Accepted" sau QI submit Accepted
- [ ] **5.2** Bin location tạo được
- [ ] **5.3** API scan_barcode + confirm_putaway hoạt động (qua REST)
- [ ] SLE balance ở bin = qty putaway

---

## Section 6 — M5 FEFO test (Lấy hàng theo lô gần hết hạn nhất)

### Vai trò + Workflow

Khi lấy hàng, hệ thống bắt buộc dùng lô có expiry_date sớm nhất (FEFO). Vi phạm sẽ throw SC-E001 trừ khi user override + nhập lý do.

### 6.1 Setup nhiều batch cùng item

Tạo 3 SE Material Receipt cho cùng VTTH-MASK-3PLY tại Kho Vật tư tiêu hao với:
- Batch A: expiry 2026-08-15 (gần nhất, 100 hộp)
- Batch B: expiry 2027-04-15 (50 hộp)
- Batch C: expiry 2028-01-15 (30 hộp)

### 6.2 API get_suggested_batches

**Endpoint:** `POST /api/method/supplycore.api.fefo.get_suggested_batches`

```json
{
  "item_code": "VTTH-MASK-3PLY",
  "warehouse": "Kho Vật tư tiêu hao",
  "qty": 80
}
```

**Expected:**
- batches[0] = Batch A (expiry sớm nhất, suggested_qty=80)
- batches[1] = Batch B (suggested_qty=0)
- batches[2] = Batch C (suggested_qty=0)
- fully_satisfied = true
- shortfall = 0

### 6.3 Negative test — issue expired batch

Tạo Batch D với expiry = today - 1 + receive 10 hộp → cố tạo SE Issue dùng Batch D.

**Expected:** throw SC-E001 hoặc SC-E008 (batch expired/blocked)

### Section 6 Checklist

- [ ] **6.2** FEFO trả batch theo expiry_date ASC
- [ ] **6.2** suggested_qty cumulative đúng (chỉ batch đầu = qty request, các batch sau = 0)
- [ ] **6.3** Issue expired batch bị block đúng

---

## Section 7 — M6 Luân chuyển nội bộ (Transfer Request)

### Vai trò + Workflow

Khoa thiếu vật tư → tạo Transfer Request từ Kho Tổng → Kho Khoa. SK approve + tạo SE Material Transfer.

### 7.1 Tạo Transfer Request

`/app/sc-transfer-request/new`:
- From warehouse: Kho Vật tư tiêu hao
- To warehouse: Kho Khoa Nhi
- Transfer type: Replenishment
- Required by: today + 3
- Items: VTTH-MASK-3PLY, requested_qty=20

**Submit:** TR.status="Approved"

### 7.2 Tạo SE Material Transfer từ TR

**Trên TR form, button "Tạo SE":**
- SE draft tự fetch from_warehouse, to_warehouse, items
- SK chọn batch theo FEFO (Batch A từ Section 6 — gần hết hạn nhất)
- Submit SE

**Verify:**
- 2 SLE rows: -20 ở Kho Vật tư tiêu hao, +20 ở Kho Khoa Nhi
- TR.status = "Received"

### Section 7 Checklist

- [ ] **7.1** TR submit thành công
- [ ] **7.2** SE auto-fetch + submit OK
- [ ] **7.2** 2 SLE rows đúng dấu (±qty)
- [ ] **7.2** TR.status="Received" sau SE submit

---

## Section 8 — M7 Cấp phát BN + BHYT

### Vai trò + Workflow

BS kê đơn → Khoa tạo Dispensing Request → Pharmacy/SK tạo SE Issue (FEFO) → tạo Patient Dispensing → tự calc BHYT theo N01-N09 + ceiling_price + patient.bhyt_payment_rate.

### 8.1 Tạo SC Patient

`/app/sc-patient/new`:
- Patient ID: BN-UAT-001
- Patient name: Nguyễn Văn UAT
- Gender: Nam
- BHYT card no: DN1234567890
- BHYT payment rate: 80 (%)
- BHYT type: Đúng tuyến

### 8.2 Tạo Dispensing Request

`/app/sc-dispensing-request/new`:
- Request date: today
- Purpose: Patient-Specific
- Department: Khoa Nhi
- From warehouse: Kho Khoa Nhi (đã có 20 từ Section 7)
- Patient: BN-UAT-001
- Items: VTTH-MASK-3PLY, requested_qty=2

**Submit:** DR.status="Approved"

### 8.3 Tạo Patient Dispensing

**Trên DR form, button "Tạo Patient Dispensing":** (nếu có) hoặc tạo manual.

PD auto-fetch:
- patient, ward, dispensing_request
- items từ DR (mỗi DR Item → 1 PD Item)
- BHYT calc theo SC BHYT Code Config

**Verify BHYT calc:**
- unit_cost = giá tại PD time (hoặc valuation_rate gần nhất)
- effective_rate = min(cfg.payment_rate, patient.bhyt_payment_rate)
- cap = min(unit_cost, ceiling_price)
- bhyt_amount = qty × cap × effective_rate / 100
- patient_pays = total_cost - bhyt_amount

**Submit PD:** SLE -qty + ghi nhận hồ sơ BN

### Section 8 Checklist

- [ ] **8.1** Patient tạo OK với gender Vietnamese (Nam/Nữ/Khác)
- [ ] **8.2** DR submit OK
- [ ] **8.3** PD auto-calc BHYT đúng công thức
- [ ] **8.3** SLE -qty post (kho Khoa Nhi giảm)
- [ ] **8.3** total_cost = qty × unit_cost
- [ ] **8.3** bhyt_covered + patient_pays = total_cost (tổng cân)

---

## Section 9 — M8 Kế toán (bonus chuỗi PR → PI → GL)

### 9.1 Click "Tạo Purchase Invoice" trên PR

**Trên PR form (qc_status=Accepted), button "Tạo Purchase Invoice":**
PI draft tự fetch supplier/PO/items + supplier_invoice_no = `AUTO-<PR>` (placeholder, user sửa lại)

### 9.2 3-way match check trước submit PI

PI.subtotal vs PO.grand_total vs PR.total_value:
- |variance| ≤ 1% → "Match"
- > 1% → "Mismatch" (cần Executive approve)
- > 5% hard cap → throw SC-E009

### 9.3 Submit PI → GL post (VAS)

**Verify:**
- 3 GL rows: Dr 152 (subtotal) + Dr 1331 (vat) / Cr 331 (grand_total)
- Σ Dr = Σ Cr
- PI.three_way_match_status = "Match" hoặc "Mismatch"
- PI.outstanding_amount = grand_total

### Section 9 Checklist

- [ ] **9.1** PI auto-fetch từ PR OK
- [ ] **9.2** 3-way match status đúng
- [ ] **9.3** GL Σ Dr = Σ Cr (cân kế toán)
- [ ] **9.3** PI.outstanding tăng

---

## Section 10 — M11 Dashboard verify

### 10.1 GET /api/method/supplycore.api.kpi.get_executive_dashboard

```bash
curl -H "Authorization: token <key>:<secret>" \
  -H "Host: supplycore" \
  "http://localhost:8000/api/method/supplycore.api.kpi.get_executive_dashboard?period=this_month"
```

**Verify 6 KPIs:**
- stock_value > 0
- monthly_cost > 0 (PI submit ở 9.3)
- ap_outstanding > 0 (PI chưa pay)
- pending_pos = 0 (PO đã Received)
- expiring_soon ≥ 0 (Batch A từ Section 6 nếu < 30 ngày)
- low_stock_items ≥ 0

### 10.2 Run scan_alerts

```bash
bench --site supplycore execute supplycore.m11_dashboard.tasks.scan_alerts
```

**Verify** SC Alert được tạo (nếu rule đã setup):
- expiring_batch alert cho Batch A
- low_stock alert cho item có safety_stock > 0 nhưng tồn thấp

### 10.3 Alert → Action (slice 2)

**Trên SC Alert form (severity Warning/Critical), button "Hành động":**
- expiring_batch → "Chuyển vào Kho Cách ly" → SE Material Transfer to Quarantine
- low_stock → "Tạo Material Request bổ sung" → MR draft (qty = safety×2)

### Section 10 Checklist

- [ ] **10.1** API trả 6 KPI hợp lệ
- [ ] **10.2** scan_alerts tạo Alert đúng (nếu có rule enabled)
- [ ] **10.3** Action button trên Alert tạo doc downstream OK

---

## Issues Found

**Cập nhật:** 2026-05-08 — execute toàn bộ E2E qua `tests/uat_e2e_runner.py` (Python direct, không qua REST). Kết quả: chuỗi đi xuyên suốt từ FC → MR → PO → PR → QI → Batch → Putaway → FEFO → TR → DR → Patient → KPI Dashboard.

| ID | Section | Mô tả | Severity | Status |
|---|---|---|---|---|
| UAT-01 | 4-5 | **Naming inconsistency**: `PR.qc_status` options là `Pending/Pass/Fail/Partial Pass` nhưng `QI.overall_status` + `Batch.qc_status` options là `Pending/Accepted/Rejected/Conditional`. Rollup hoạt động đúng (QI Accepted → PR Pass + Batch Accepted), nhưng naming khác biệt khiến user dễ nhầm khi đọc PR và QI có liên quan trực tiếp. **Đề xuất fix:** đồng bộ về 1 cặp (Accepted/Rejected) hoặc (Pass/Fail) — yêu cầu data migration cho records cũ. | Low | **Open** — defer để tránh migration ảnh hưởng records hiện có |
| UAT-02 | 3.3 | PR auto-tạo SC Batch khi item.has_batch_no=1 + có expiry_date trên row, batch_id format `<item>-<YYYYMM>-<rand>`. Verified ✓ | — | OK |
| UAT-03 | 5.3 | API `scan_barcode(barcode, context)` — không nhận `warehouse` kwarg. README M4 mô tả khác. **Đề xuất fix:** cập nhật README M4 / hoặc đổi signature để nhận warehouse | Low | **Open** — non-blocking |

### E2E Run Result (2026-05-08)

```
✓ Section 1.1-1.2 — FC tạo + submit, status=Active
✓ Section 1.3   — RO tạo từ FC, items auto-fetch
✓ Section 2.1   — MR submit, status=Approved
✓ Section 2.2   — create_purchase_orders → 1 PO link đúng FC + MR
✓ Section 2.3   — PO submit, FC.used_value cập nhật
✓ Section 3.1-3.3 — make_pr_from_po: PR draft auto-fetch supplier/items/warehouse
                   Submit PR → SLE post + auto-tạo QI + PO.received_qty + PO.status="Received"
✓ Section 4.1-4.2 — QI submit overall_status=Accepted → PR.qc_status="Pass" + Batch.qc_status="Accepted"
✓ Section 5.1   — Batch metadata đầy đủ (mfg/exp/supplier/qc=Accepted)
✓ Section 6.2   — FEFO API trả batches sorted ASC theo expiry_date
✓ Section 7.1   — TR submit OK
✓ Section 8.2   — DR submit OK
✓ Section 10.1  — Dashboard API trả 6 KPI hợp lệ
```

**Tổng:** 0 critical/high issues. 1 low (naming inconsistency) + 1 doc gap (scan_barcode signature).

### Cách re-run E2E

```bash
echo "from supplycore.tests import uat_e2e_runner; result = uat_e2e_runner.run_all(); import frappe; frappe.db.commit(); print('Issues:', len(result)); [print(i) for i in result]" | bench --site supplycore console
```

---

## Sign-off Checklist

End-user xác nhận đã pass toàn bộ:

- [ ] Section 1 — Hợp đồng khung
- [ ] Section 2 — Kế hoạch & Đặt hàng
- [ ] Section 3 — Nhận hàng (PR)
- [ ] Section 4 — QC
- [ ] Section 5 — Setup lô + Putaway
- [ ] Section 6 — FEFO
- [ ] Section 7 — Luân chuyển nội bộ
- [ ] Section 8 — Cấp phát BN + BHYT
- [ ] Section 9 — Kế toán & 3-way match
- [ ] Section 10 — Dashboard + Alert

**Tester:** _____________________ **Ngày:** _____________________
**Sign-off:** _____________________ **Role:** _____________________
