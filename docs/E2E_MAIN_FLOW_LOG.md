# E2E Luồng Chính — Test Log

**Scenario**: Tạo Hợp đồng khung → Gọi hàng (MR/PO) → Nhận hàng (PR) → QC → Tạo Lô → Xếp kho → Chuyển kho → Cấp phát BN

**Run command**: `cd frontend && npm run e2e`

**Date**: 2026-05-12

---

## Iterations log

(Auto-populated by E2E test runs — mỗi run append 1 section)

## Run 2026-05-12T02:29:16.298Z

**Result**: 6/7 pass · 1 fail
**Duration**: 4s

### Steps

| # | Step | Result | Detail | Time |
|---|------|--------|--------|------|
| 1 | PRE: Login | ✅ | URL: http://supplycore/supplycore/ | 3667ms |
| 2 | PRE: Pick master data (Supplier, Item, Warehouse, Patient) | ✅ | Sup=SC-SUP-03163, Item=DTRC-RL (Chai), WH1=Kho Khoa Dược, WH2=Kho Phòng Mổ, BN=BN010 | 50ms |
| 3 | 1.1 Tạo Framework Contract via API | ✅ | FC=SC-FC-2026-03297, contract_number=FC-E2E-38u0co | 29ms |
| 4 | 1.2 FC submit_for_review → Manager Review | ✅ | stage=Manager Review | 30ms |
| 5 | 1.3 FC approve_as_manager | ✅ | stage=Approved | 30ms |
| 6 | 1.4 FC approve_as_executive (nếu cần) | ✅ | stage=Approved | 27ms |
| 7 | 1.5 FC submit (docstatus 0→1, status=Active) | ❌ | page.evaluate: Error: frappe.exceptions.TimestampMismatchError: Error: Document has been modified after you have opened  | 15ms |

### Issues found

#### Issue 1: 1.5 FC submit (docstatus 0→1, status=Active)

**Error**: page.evaluate: Error: frappe.exceptions.TimestampMismatchError: Error: Document has been modified after you have opened it (2026-05-12 09:29:16.219691, 2026-05-12 09:29:16.274493). Please refresh to get the latest document.
    at eval (eval at evaluate (:302:30), <anonymous>:9:22)
    at async <anonymous>:328:30

### Console/JS errors

- [console] Failed to load resource: the server responded with a status of 403 (FORBIDDEN)
- [console] Failed to load resource: the server responded with a status of 417 (EXPECTATION FAILED)

### Context (created docs)

```json
{
  "supplier": "SC-SUP-03163",
  "item": "DTRC-RL",
  "itemUom": "Chai",
  "warehouse_main": "Kho Khoa Dược",
  "warehouse_to": "Kho Phòng Mổ",
  "patient": "BN010",
  "bhyt_card": "TT4-079-01234-567",
  "department": "Ban Giám đốc",
  "fc": "SC-FC-2026-03297"
}
```

## Run 2026-05-12T02:30:48.889Z

**Result**: 22/23 pass · 1 fail
**Duration**: 8s

### Steps

| # | Step | Result | Detail | Time |
|---|------|--------|--------|------|
| 1 | PRE: Login | ✅ | URL: http://supplycore/supplycore/ | 5219ms |
| 2 | PRE: Pick master data (Supplier, Item, Warehouse, Patient) | ✅ | Sup=SC-SUP-03163, Item=DTRC-RL (Chai), WH1=Kho Khoa Dược, WH2=Kho Phòng Mổ, BN=BN010 | 217ms |
| 3 | 1.1 Tạo Framework Contract via API | ✅ | FC=SC-FC-2026-03298, contract_number=FC-E2E-e70kcw | 166ms |
| 4 | 1.2 FC submit_for_review → Manager Review | ✅ | stage=Manager Review | 61ms |
| 5 | 1.3 FC approve_as_manager | ✅ | stage=Approved | 187ms |
| 6 | 1.4 FC approve_as_executive (nếu cần) | ✅ | stage=Approved | 163ms |
| 7 | 1.5 FC submit (docstatus 0→1, status=Active) | ✅ | docstatus=1, status=Active | 175ms |
| 8 | 2.1 Tạo Material Request | ✅ | MR=SC-MR-2026-03299 | 66ms |
| 9 | 2.2 MR submit (docstatus=1) | ✅ | docstatus=1, status=Pending | 114ms |
| 10 | 2.3 MR approve | ✅ | status=Approved | 37ms |
| 11 | 2.4 Tạo Purchase Order link FC | ✅ | PO=SC-PO-2026-03300, total=500000 | 78ms |
| 12 | 2.5 PO approval workflow + submit | ✅ | docstatus=1, status=Sent to Supplier | 275ms |
| 13 | 3.1 Tạo Purchase Receipt với batch info | ✅ | PR=SC-PR-2026-03301, supplier_batch_no=LOT-E2E-6azp1 | 115ms |
| 14 | 3.2 PR submit → batch + SLE auto-create | ✅ | batch=DTRC-RL-202805-001, SLE qty=100, balance=100 | 201ms |
| 15 | 3.3 Verify batch master created | ✅ | Batch DTRC-RL-202805-001: item=DTRC-RL, expiry=2028-05-11, qc=Pending | 12ms |
| 16 | 4.1 Tạo Quality Inspection cho batch | ✅ | QI=SC-QI-2026-03304 với 4 readings | 39ms |
| 17 | 4.2 QI submit → Accepted | ✅ | docstatus=1, overall=Accepted | 72ms |
| 18 | 5.1 Verify tồn kho qua SLE | ✅ | Tồn Kho Khoa Dược/DTRC-RL-202805-001: 100 | 15ms |
| 19 | 6.1 Tạo Stock Entry Material Transfer (30 units) | ✅ | SE=SC-SE-2026-03305, qty=30 batch=DTRC-RL-202805-001 | 93ms |
| 20 | 6.2 SE submit → SLE âm ở wh_main + dương ở wh_to | ✅ | SLE: 1 âm + 1 dương | 122ms |
| 21 | 6.3 Verify tồn 2 kho sau transfer (70 + 30 = 100) | ✅ | Kho Khoa Dược=70, Kho Phòng Mổ=30 | 60ms |
| 22 | 7.1 Tạo Patient Dispensing (BHYT) | ✅ | PD=SC-PD-2026-03308 cho BN BN010 | 85ms |
| 23 | 7.2 PD submit → BHYT calc + SLE âm | ❌ | page.evaluate: Error: frappe.exceptions.FrappeTypeError: Argument 'on_date' should be of type 'typing.Optional[str]' but | 66ms |

### Issues found

#### Issue 1: 7.2 PD submit → BHYT calc + SLE âm

**Error**: page.evaluate: Error: frappe.exceptions.FrappeTypeError: Argument 'on_date' should be of type 'typing.Optional[str]' but got 'datetime.date' instead.
    at eval (eval at evaluate (:302:30), <anonymous>:9:22)
    at async <anonymous>:328:30

### Console/JS errors

- [console] Failed to load resource: the server responded with a status of 403 (FORBIDDEN)
- [console] Failed to load resource: the server responded with a status of 417 (EXPECTATION FAILED)

### Context (created docs)

```json
{
  "supplier": "SC-SUP-03163",
  "item": "DTRC-RL",
  "itemUom": "Chai",
  "warehouse_main": "Kho Khoa Dược",
  "warehouse_to": "Kho Phòng Mổ",
  "patient": "BN010",
  "bhyt_card": "TT4-079-01234-567",
  "department": "Ban Giám đốc",
  "fc": "SC-FC-2026-03298",
  "mr": "SC-MR-2026-03299",
  "po": "SC-PO-2026-03300",
  "pr": "SC-PR-2026-03301",
  "supplier_batch_no": "LOT-E2E-6azp1",
  "batch": "DTRC-RL-202805-001",
  "sle_initial": {
    "name": "SC-SLE-2026-00003302",
    "qty_change": 100,
    "balance_qty": 100
  },
  "qi": "SC-QI-2026-03304",
  "se_transfer": "SC-SE-2026-03305",
  "pd": "SC-PD-2026-03308"
}
```

## Run 2026-05-12T02:31:35.486Z

**Result**: 23/24 pass · 1 fail
**Duration**: 7s

### Steps

| # | Step | Result | Detail | Time |
|---|------|--------|--------|------|
| 1 | PRE: Login | ✅ | URL: http://supplycore/supplycore/ | 5140ms |
| 2 | PRE: Pick master data (Supplier, Item, Warehouse, Patient) | ✅ | Sup=SC-SUP-03163, Item=DTRC-RL (Chai), WH1=Kho Khoa Dược, WH2=Kho Phòng Mổ, BN=BN010 | 192ms |
| 3 | 1.1 Tạo Framework Contract via API | ✅ | FC=SC-FC-2026-03309, contract_number=FC-E2E-0ihl0f | 151ms |
| 4 | 1.2 FC submit_for_review → Manager Review | ✅ | stage=Manager Review | 45ms |
| 5 | 1.3 FC approve_as_manager | ✅ | stage=Approved | 80ms |
| 6 | 1.4 FC approve_as_executive (nếu cần) | ✅ | stage=Approved | 73ms |
| 7 | 1.5 FC submit (docstatus 0→1, status=Active) | ✅ | docstatus=1, status=Active | 68ms |
| 8 | 2.1 Tạo Material Request | ✅ | MR=SC-MR-2026-03310 | 48ms |
| 9 | 2.2 MR submit (docstatus=1) | ✅ | docstatus=1, status=Pending | 120ms |
| 10 | 2.3 MR approve | ✅ | status=Approved | 54ms |
| 11 | 2.4 Tạo Purchase Order link FC | ✅ | PO=SC-PO-2026-03311, total=500000 | 96ms |
| 12 | 2.5 PO approval workflow + submit | ✅ | docstatus=1, status=Sent to Supplier | 251ms |
| 13 | 3.1 Tạo Purchase Receipt với batch info | ✅ | PR=SC-PR-2026-03312, supplier_batch_no=LOT-E2E-j4pth | 80ms |
| 14 | 3.2 PR submit → batch + SLE auto-create | ✅ | batch=DTRC-RL-202805-002, SLE qty=100, balance=100 | 253ms |
| 15 | 3.3 Verify batch master created | ✅ | Batch DTRC-RL-202805-002: item=DTRC-RL, expiry=2028-05-11, qc=Pending | 10ms |
| 16 | 4.1 Tạo Quality Inspection cho batch | ✅ | QI=SC-QI-2026-03315 với 4 readings | 40ms |
| 17 | 4.2 QI submit → Accepted | ✅ | docstatus=1, overall=Accepted | 96ms |
| 18 | 5.1 Verify tồn kho qua SLE | ✅ | Tồn Kho Khoa Dược/DTRC-RL-202805-002: 100 | 12ms |
| 19 | 6.1 Tạo Stock Entry Material Transfer (30 units) | ✅ | SE=SC-SE-2026-03316, qty=30 batch=DTRC-RL-202805-002 | 82ms |
| 20 | 6.2 SE submit → SLE âm ở wh_main + dương ở wh_to | ✅ | SLE: 1 âm + 1 dương | 86ms |
| 21 | 6.3 Verify tồn 2 kho sau transfer (70 + 30 = 100) | ✅ | Kho Khoa Dược=70, Kho Phòng Mổ=30 | 42ms |
| 22 | 7.1 Tạo Patient Dispensing (BHYT) | ✅ | PD=SC-PD-2026-03319 cho BN BN010 | 117ms |
| 23 | 7.2 PD submit → BHYT calc + SLE âm | ✅ | total_cost=25000, bhyt=undefined, patient_pays=10000 | 53ms |
| 24 | 7.3 Verify tồn sau cấp phát (70 - 5 = 65) | ❌ | Tồn=70, expected 65 (70-5) | 20ms |

### Issues found

#### Issue 1: 7.3 Verify tồn sau cấp phát (70 - 5 = 65)

**Error**: Tồn=70, expected 65 (70-5)

### Console/JS errors

- [console] Failed to load resource: the server responded with a status of 403 (FORBIDDEN)

### Context (created docs)

```json
{
  "supplier": "SC-SUP-03163",
  "item": "DTRC-RL",
  "itemUom": "Chai",
  "warehouse_main": "Kho Khoa Dược",
  "warehouse_to": "Kho Phòng Mổ",
  "patient": "BN010",
  "bhyt_card": "TT4-079-01234-567",
  "department": "Ban Giám đốc",
  "fc": "SC-FC-2026-03309",
  "mr": "SC-MR-2026-03310",
  "po": "SC-PO-2026-03311",
  "pr": "SC-PR-2026-03312",
  "supplier_batch_no": "LOT-E2E-j4pth",
  "batch": "DTRC-RL-202805-002",
  "sle_initial": {
    "name": "SC-SLE-2026-00003313",
    "qty_change": 100,
    "balance_qty": 100
  },
  "qi": "SC-QI-2026-03315",
  "se_transfer": "SC-SE-2026-03316",
  "pd": "SC-PD-2026-03319"
}
```

## Run 2026-05-12T02:32:28.502Z

**Result**: 22/23 pass · 1 fail
**Duration**: 7s

### Steps

| # | Step | Result | Detail | Time |
|---|------|--------|--------|------|
| 1 | PRE: Login | ✅ | URL: http://supplycore/supplycore/ | 5028ms |
| 2 | PRE: Pick master data (Supplier, Item, Warehouse, Patient) | ✅ | Sup=SC-SUP-03163, Item=DTRC-RL (Chai), WH1=Kho Khoa Dược, WH2=Kho Phòng Mổ, BN=BN010 | 196ms |
| 3 | 1.1 Tạo Framework Contract via API | ✅ | FC=SC-FC-2026-03320, contract_number=FC-E2E-l0wk26 | 132ms |
| 4 | 1.2 FC submit_for_review → Manager Review | ✅ | stage=Manager Review | 56ms |
| 5 | 1.3 FC approve_as_manager | ✅ | stage=Approved | 94ms |
| 6 | 1.4 FC approve_as_executive (nếu cần) | ✅ | stage=Approved | 45ms |
| 7 | 1.5 FC submit (docstatus 0→1, status=Active) | ✅ | docstatus=1, status=Active | 65ms |
| 8 | 2.1 Tạo Material Request | ✅ | MR=SC-MR-2026-03321 | 82ms |
| 9 | 2.2 MR submit (docstatus=1) | ✅ | docstatus=1, status=Pending | 143ms |
| 10 | 2.3 MR approve | ✅ | status=Approved | 49ms |
| 11 | 2.4 Tạo Purchase Order link FC | ✅ | PO=SC-PO-2026-03322, total=500000 | 87ms |
| 12 | 2.5 PO approval workflow + submit | ✅ | docstatus=1, status=Sent to Supplier | 255ms |
| 13 | 3.1 Tạo Purchase Receipt với batch info | ✅ | PR=SC-PR-2026-03323, supplier_batch_no=LOT-E2E-8284j | 72ms |
| 14 | 3.2 PR submit → batch + SLE auto-create | ✅ | batch=DTRC-RL-202805-003, SLE qty=100, balance=100 | 194ms |
| 15 | 3.3 Verify batch master created | ✅ | Batch DTRC-RL-202805-003: item=DTRC-RL, expiry=2028-05-11, qc=Pending | 17ms |
| 16 | 4.1 Tạo Quality Inspection cho batch | ✅ | QI=SC-QI-2026-03326 với 4 readings | 35ms |
| 17 | 4.2 QI submit → Accepted | ✅ | docstatus=1, overall=Accepted | 51ms |
| 18 | 5.1 Verify tồn kho qua SLE | ✅ | Tồn Kho Khoa Dược/DTRC-RL-202805-003: 100 | 9ms |
| 19 | 6.1 Tạo Stock Entry Material Transfer (30 units) | ✅ | SE=SC-SE-2026-03327, qty=30 batch=DTRC-RL-202805-003 | 62ms |
| 20 | 6.2 SE submit → SLE âm ở wh_main + dương ở wh_to | ✅ | SLE: 1 âm + 1 dương | 80ms |
| 21 | 6.3 Verify tồn 2 kho sau transfer (70 + 30 = 100) | ✅ | Kho Khoa Dược=70, Kho Phòng Mổ=30 | 28ms |
| 22 | 7.1 Tạo Patient Dispensing (BHYT) | ✅ | PD=SC-PD-2026-03330 cho BN BN010 | 57ms |
| 23 | 7.2 PD submit → BHYT calc + SLE âm | ❌ | page.evaluate: Error: AttributeError: 'SCPDItem' object has no attribute 'warehouse'
    at eval (eval at evaluate (:302 | 140ms |

### Issues found

#### Issue 1: 7.2 PD submit → BHYT calc + SLE âm

**Error**: page.evaluate: Error: AttributeError: 'SCPDItem' object has no attribute 'warehouse'
    at eval (eval at evaluate (:302:30), <anonymous>:9:22)
    at async <anonymous>:328:30

### Console/JS errors

- [console] Failed to load resource: the server responded with a status of 403 (FORBIDDEN)
- [console] Failed to load resource: the server responded with a status of 500 (INTERNAL SERVER ERROR)

### Context (created docs)

```json
{
  "supplier": "SC-SUP-03163",
  "item": "DTRC-RL",
  "itemUom": "Chai",
  "warehouse_main": "Kho Khoa Dược",
  "warehouse_to": "Kho Phòng Mổ",
  "patient": "BN010",
  "bhyt_card": "TT4-079-01234-567",
  "department": "Ban Giám đốc",
  "fc": "SC-FC-2026-03320",
  "mr": "SC-MR-2026-03321",
  "po": "SC-PO-2026-03322",
  "pr": "SC-PR-2026-03323",
  "supplier_batch_no": "LOT-E2E-8284j",
  "batch": "DTRC-RL-202805-003",
  "sle_initial": {
    "name": "SC-SLE-2026-00003324",
    "qty_change": 100,
    "balance_qty": 100
  },
  "qi": "SC-QI-2026-03326",
  "se_transfer": "SC-SE-2026-03327",
  "pd": "SC-PD-2026-03330"
}
```

## Run 2026-05-12T02:34:06.984Z

**Result**: 27/27 pass ✅
**Duration**: 12s

### Steps

| # | Step | Result | Detail | Time |
|---|------|--------|--------|------|
| 1 | PRE: Login | ✅ | URL: http://supplycore/supplycore/ | 4019ms |
| 2 | PRE: Pick master data (Supplier, Item, Warehouse, Patient) | ✅ | Sup=SC-SUP-03163, Item=DTRC-RL (Chai), WH1=Kho Khoa Dược, WH2=Kho Phòng Mổ, BN=BN010 | 180ms |
| 3 | 1.1 Tạo Framework Contract via API | ✅ | FC=SC-FC-2026-03331, contract_number=FC-E2E-cpis7v | 138ms |
| 4 | 1.2 FC submit_for_review → Manager Review | ✅ | stage=Manager Review | 68ms |
| 5 | 1.3 FC approve_as_manager | ✅ | stage=Approved | 77ms |
| 6 | 1.4 FC approve_as_executive (nếu cần) | ✅ | stage=Approved | 53ms |
| 7 | 1.5 FC submit (docstatus 0→1, status=Active) | ✅ | docstatus=1, status=Active | 94ms |
| 8 | 2.1 Tạo Material Request | ✅ | MR=SC-MR-2026-03332 | 97ms |
| 9 | 2.2 MR submit (docstatus=1) | ✅ | docstatus=1, status=Pending | 113ms |
| 10 | 2.3 MR approve | ✅ | status=Approved | 37ms |
| 11 | 2.4 Tạo Purchase Order link FC | ✅ | PO=SC-PO-2026-03333, total=500000 | 78ms |
| 12 | 2.5 PO approval workflow + submit | ✅ | docstatus=1, status=Sent to Supplier | 197ms |
| 13 | 3.1 Tạo Purchase Receipt với batch info | ✅ | PR=SC-PR-2026-03334, supplier_batch_no=LOT-E2E-v477j | 100ms |
| 14 | 3.2 PR submit → batch + SLE auto-create | ✅ | batch=DTRC-RL-202805-004, SLE qty=100, balance=100 | 241ms |
| 15 | 3.3 Verify batch master created | ✅ | Batch DTRC-RL-202805-004: item=DTRC-RL, expiry=2028-05-11, qc=Pending | 13ms |
| 16 | 4.1 Tạo Quality Inspection cho batch | ✅ | QI=SC-QI-2026-03337 với 4 readings | 50ms |
| 17 | 4.2 QI submit → Accepted | ✅ | docstatus=1, overall=Accepted | 81ms |
| 18 | 5.1 Verify tồn kho qua SLE | ✅ | Tồn Kho Khoa Dược/DTRC-RL-202805-004: 100 | 35ms |
| 19 | 6.1 Tạo Stock Entry Material Transfer (30 units) | ✅ | SE=SC-SE-2026-03338, qty=30 batch=DTRC-RL-202805-004 | 96ms |
| 20 | 6.2 SE submit → SLE âm ở wh_main + dương ở wh_to | ✅ | SLE: 1 âm + 1 dương | 88ms |
| 21 | 6.3 Verify tồn 2 kho sau transfer (70 + 30 = 100) | ✅ | Kho Khoa Dược=70, Kho Phòng Mổ=30 | 52ms |
| 22 | 7.1 Tạo Patient Dispensing (BHYT) | ✅ | PD=SC-PD-2026-03341 cho BN BN010 | 80ms |
| 23 | 7.2 PD submit → BHYT calc + SLE âm | ✅ | total_cost=25000, bhyt=undefined, patient_pays=10000 | 64ms |
| 24 | 7.3 Verify tồn sau cấp phát (70 - 5 = 65) | ✅ | Kho Khoa Dược/DTRC-RL-202805-004: 65 | 20ms |
| 25 | 8.1 UI: FC visible trong list | ✅ | SC-FC-2026-03331 visible | 1683ms |
| 26 | 8.2 UI: PR detail page render | ✅ | Title="Phiếu nhập SC-PR-2026-03334" | 2151ms |
| 27 | 8.3 UI: PD detail có items + BHYT info | ✅ | PD SC-PD-2026-03341 rendered (BHYT match=1) | 2131ms |

### Console/JS errors

- [console] Failed to load resource: the server responded with a status of 403 (FORBIDDEN)

### Context (created docs)

```json
{
  "supplier": "SC-SUP-03163",
  "item": "DTRC-RL",
  "itemUom": "Chai",
  "warehouse_main": "Kho Khoa Dược",
  "warehouse_to": "Kho Phòng Mổ",
  "patient": "BN010",
  "bhyt_card": "TT4-079-01234-567",
  "department": "Ban Giám đốc",
  "fc": "SC-FC-2026-03331",
  "mr": "SC-MR-2026-03332",
  "po": "SC-PO-2026-03333",
  "pr": "SC-PR-2026-03334",
  "supplier_batch_no": "LOT-E2E-v477j",
  "batch": "DTRC-RL-202805-004",
  "sle_initial": {
    "name": "SC-SLE-2026-00003335",
    "qty_change": 100,
    "balance_qty": 100
  },
  "qi": "SC-QI-2026-03337",
  "se_transfer": "SC-SE-2026-03338",
  "pd": "SC-PD-2026-03341"
}
```

## Run 2026-05-12T02:34:29.111Z

**Result**: 27/27 pass ✅
**Duration**: 11s

### Steps

| # | Step | Result | Detail | Time |
|---|------|--------|--------|------|
| 1 | PRE: Login | ✅ | URL: http://supplycore/supplycore/ | 3718ms |
| 2 | PRE: Pick master data (Supplier, Item, Warehouse, Patient) | ✅ | Sup=SC-SUP-03163, Item=DTRC-RL (Chai), WH1=Kho Khoa Dược, WH2=Kho Phòng Mổ, BN=BN010 | 71ms |
| 3 | 1.1 Tạo Framework Contract via API | ✅ | FC=SC-FC-2026-03343, contract_number=FC-E2E-6qqjvq | 32ms |
| 4 | 1.2 FC submit_for_review → Manager Review | ✅ | stage=Manager Review | 56ms |
| 5 | 1.3 FC approve_as_manager | ✅ | stage=Approved | 36ms |
| 6 | 1.4 FC approve_as_executive (nếu cần) | ✅ | stage=Approved | 30ms |
| 7 | 1.5 FC submit (docstatus 0→1, status=Active) | ✅ | docstatus=1, status=Active | 79ms |
| 8 | 2.1 Tạo Material Request | ✅ | MR=SC-MR-2026-03344 | 38ms |
| 9 | 2.2 MR submit (docstatus=1) | ✅ | docstatus=1, status=Pending | 61ms |
| 10 | 2.3 MR approve | ✅ | status=Approved | 29ms |
| 11 | 2.4 Tạo Purchase Order link FC | ✅ | PO=SC-PO-2026-03345, total=500000 | 49ms |
| 12 | 2.5 PO approval workflow + submit | ✅ | docstatus=1, status=Sent to Supplier | 201ms |
| 13 | 3.1 Tạo Purchase Receipt với batch info | ✅ | PR=SC-PR-2026-03346, supplier_batch_no=LOT-E2E-um8p1 | 39ms |
| 14 | 3.2 PR submit → batch + SLE auto-create | ✅ | batch=DTRC-RL-202805-005, SLE qty=100, balance=100 | 105ms |
| 15 | 3.3 Verify batch master created | ✅ | Batch DTRC-RL-202805-005: item=DTRC-RL, expiry=2028-05-11, qc=Pending | 10ms |
| 16 | 4.1 Tạo Quality Inspection cho batch | ✅ | QI=SC-QI-2026-03349 với 4 readings | 29ms |
| 17 | 4.2 QI submit → Accepted | ✅ | docstatus=1, overall=Accepted | 78ms |
| 18 | 5.1 Verify tồn kho qua SLE | ✅ | Tồn Kho Khoa Dược/DTRC-RL-202805-005: 100 | 11ms |
| 19 | 6.1 Tạo Stock Entry Material Transfer (30 units) | ✅ | SE=SC-SE-2026-03350, qty=30 batch=DTRC-RL-202805-005 | 23ms |
| 20 | 6.2 SE submit → SLE âm ở wh_main + dương ở wh_to | ✅ | SLE: 1 âm + 1 dương | 62ms |
| 21 | 6.3 Verify tồn 2 kho sau transfer (70 + 30 = 100) | ✅ | Kho Khoa Dược=70, Kho Phòng Mổ=30 | 25ms |
| 22 | 7.1 Tạo Patient Dispensing (BHYT) | ✅ | PD=SC-PD-2026-03353 cho BN BN010 | 24ms |
| 23 | 7.2 PD submit → BHYT calc + SLE âm | ✅ | total_cost=25000, bhyt=undefined, patient_pays=10000 | 51ms |
| 24 | 7.3 Verify tồn sau cấp phát (70 - 5 = 65) | ✅ | Kho Khoa Dược/DTRC-RL-202805-005: 65 | 33ms |
| 25 | 8.1 UI: FC visible trong list | ✅ | SC-FC-2026-03343 visible | 1690ms |
| 26 | 8.2 UI: PR detail page render | ✅ | Title="Phiếu nhập SC-PR-2026-03346" | 2144ms |
| 27 | 8.3 UI: PD detail có items + BHYT info | ✅ | PD SC-PD-2026-03353 rendered (BHYT match=1) | 2149ms |

### Console/JS errors

- [console] Failed to load resource: the server responded with a status of 403 (FORBIDDEN)

### Context (created docs)

```json
{
  "supplier": "SC-SUP-03163",
  "item": "DTRC-RL",
  "itemUom": "Chai",
  "warehouse_main": "Kho Khoa Dược",
  "warehouse_to": "Kho Phòng Mổ",
  "patient": "BN010",
  "bhyt_card": "TT4-079-01234-567",
  "department": "Ban Giám đốc",
  "fc": "SC-FC-2026-03343",
  "mr": "SC-MR-2026-03344",
  "po": "SC-PO-2026-03345",
  "pr": "SC-PR-2026-03346",
  "supplier_batch_no": "LOT-E2E-um8p1",
  "batch": "DTRC-RL-202805-005",
  "sle_initial": {
    "name": "SC-SLE-2026-00003347",
    "qty_change": 100,
    "balance_qty": 100
  },
  "qi": "SC-QI-2026-03349",
  "se_transfer": "SC-SE-2026-03350",
  "pd": "SC-PD-2026-03353"
}
```

## Run 2026-05-12T02:34:40.166Z

**Result**: 27/27 pass ✅
**Duration**: 11s

### Steps

| # | Step | Result | Detail | Time |
|---|------|--------|--------|------|
| 1 | PRE: Login | ✅ | URL: http://supplycore/supplycore/ | 3690ms |
| 2 | PRE: Pick master data (Supplier, Item, Warehouse, Patient) | ✅ | Sup=SC-SUP-03163, Item=DTRC-RL (Chai), WH1=Kho Khoa Dược, WH2=Kho Phòng Mổ, BN=BN010 | 59ms |
| 3 | 1.1 Tạo Framework Contract via API | ✅ | FC=SC-FC-2026-03355, contract_number=FC-E2E-cztp80 | 25ms |
| 4 | 1.2 FC submit_for_review → Manager Review | ✅ | stage=Manager Review | 30ms |
| 5 | 1.3 FC approve_as_manager | ✅ | stage=Approved | 40ms |
| 6 | 1.4 FC approve_as_executive (nếu cần) | ✅ | stage=Approved | 34ms |
| 7 | 1.5 FC submit (docstatus 0→1, status=Active) | ✅ | docstatus=1, status=Active | 59ms |
| 8 | 2.1 Tạo Material Request | ✅ | MR=SC-MR-2026-03356 | 21ms |
| 9 | 2.2 MR submit (docstatus=1) | ✅ | docstatus=1, status=Pending | 43ms |
| 10 | 2.3 MR approve | ✅ | status=Approved | 27ms |
| 11 | 2.4 Tạo Purchase Order link FC | ✅ | PO=SC-PO-2026-03357, total=500000 | 25ms |
| 12 | 2.5 PO approval workflow + submit | ✅ | docstatus=1, status=Sent to Supplier | 150ms |
| 13 | 3.1 Tạo Purchase Receipt với batch info | ✅ | PR=SC-PR-2026-03358, supplier_batch_no=LOT-E2E-v5mom | 26ms |
| 14 | 3.2 PR submit → batch + SLE auto-create | ✅ | batch=DTRC-RL-202805-006, SLE qty=100, balance=100 | 81ms |
| 15 | 3.3 Verify batch master created | ✅ | Batch DTRC-RL-202805-006: item=DTRC-RL, expiry=2028-05-11, qc=Pending | 11ms |
| 16 | 4.1 Tạo Quality Inspection cho batch | ✅ | QI=SC-QI-2026-03361 với 4 readings | 37ms |
| 17 | 4.2 QI submit → Accepted | ✅ | docstatus=1, overall=Accepted | 58ms |
| 18 | 5.1 Verify tồn kho qua SLE | ✅ | Tồn Kho Khoa Dược/DTRC-RL-202805-006: 100 | 11ms |
| 19 | 6.1 Tạo Stock Entry Material Transfer (30 units) | ✅ | SE=SC-SE-2026-03362, qty=30 batch=DTRC-RL-202805-006 | 19ms |
| 20 | 6.2 SE submit → SLE âm ở wh_main + dương ở wh_to | ✅ | SLE: 1 âm + 1 dương | 71ms |
| 21 | 6.3 Verify tồn 2 kho sau transfer (70 + 30 = 100) | ✅ | Kho Khoa Dược=70, Kho Phòng Mổ=30 | 20ms |
| 22 | 7.1 Tạo Patient Dispensing (BHYT) | ✅ | PD=SC-PD-2026-03365 cho BN BN010 | 23ms |
| 23 | 7.2 PD submit → BHYT calc + SLE âm | ✅ | total_cost=25000, bhyt=undefined, patient_pays=10000 | 55ms |
| 24 | 7.3 Verify tồn sau cấp phát (70 - 5 = 65) | ✅ | Kho Khoa Dược/DTRC-RL-202805-006: 65 | 11ms |
| 25 | 8.1 UI: FC visible trong list | ✅ | SC-FC-2026-03355 visible | 1652ms |
| 26 | 8.2 UI: PR detail page render | ✅ | Title="Phiếu nhập SC-PR-2026-03358" | 2162ms |
| 27 | 8.3 UI: PD detail có items + BHYT info | ✅ | PD SC-PD-2026-03365 rendered (BHYT match=1) | 2149ms |

### Console/JS errors

- [console] Failed to load resource: the server responded with a status of 403 (FORBIDDEN)

### Context (created docs)

```json
{
  "supplier": "SC-SUP-03163",
  "item": "DTRC-RL",
  "itemUom": "Chai",
  "warehouse_main": "Kho Khoa Dược",
  "warehouse_to": "Kho Phòng Mổ",
  "patient": "BN010",
  "bhyt_card": "TT4-079-01234-567",
  "department": "Ban Giám đốc",
  "fc": "SC-FC-2026-03355",
  "mr": "SC-MR-2026-03356",
  "po": "SC-PO-2026-03357",
  "pr": "SC-PR-2026-03358",
  "supplier_batch_no": "LOT-E2E-v5mom",
  "batch": "DTRC-RL-202805-006",
  "sle_initial": {
    "name": "SC-SLE-2026-00003359",
    "qty_change": 100,
    "balance_qty": 100
  },
  "qi": "SC-QI-2026-03361",
  "se_transfer": "SC-SE-2026-03362",
  "pd": "SC-PD-2026-03365"
}
```
