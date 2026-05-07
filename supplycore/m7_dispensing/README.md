# M7 — Cấp phát & BHYT

Module quản lý **SC Dispensing Request** (yêu cầu cấp phát) + **SC Patient Dispensing** (ghi nhận cấp phát cho BN có BHYT) + **SC BHYT Code Config** (tham số hóa N01-N09).

> ⚠ **v0.2 — chỉ Frappe**: SC* DocTypes, không dùng ERPNext.

## DocTypes

| DocType | Loại | Module | Mô tả |
|---|---|---|---|
| `SC BHYT Code Config` | Master | Supplycore | Mã BHYT N01-N09 + tỷ lệ + giá trần (BR-BH-01..04) |
| `SC Patient` | Master | Supplycore | Bệnh nhân + thẻ BHYT + bhyt_payment_rate |
| `SC Dispensing Request` + DR Item | Submittable | M7 | Phiếu yêu cầu cấp phát từ khoa |
| `SC Patient Dispensing` + PD Item | Submittable | M7 | Ghi nhận BN + BHYT calc tự động |

## Naming series

- `SC-BHYT-#####` — BHYT Code Config
- `<patient_id>` — SC Patient (autoname=field:patient_id)
- `SC-DR-YYYY-#####` — Dispensing Request
- `SC-PD-YYYY-#####` — Patient Dispensing

## Logic BHYT calc

```
Cho mỗi row trong SC PD Item:
  total_cost = qty × unit_cost

  cfg = supplycore.api.bhyt.get_active_config(item, on_date)
    Lookup priority:
      1. Config có `item = X` (item-specific)
      2. Config có `item_group = item.item_group`
      3. Fallback SC Item.has_bhyt + bhyt_payment_rate

  if cfg:
    cfg_rate = cfg.payment_rate            (vd 80%)
    effective_rate = min(cfg_rate, patient.bhyt_payment_rate)  (BN trái tuyến → giảm)
    ceiling = cfg.ceiling_price            (giá trần BHYT/đơn vị)

    if unit_cost > ceiling:
      cap_unit = ceiling
      ceiling_overage = qty × (unit_cost − ceiling)   ← BN tự trả phần vượt
    else:
      cap_unit = unit_cost
      ceiling_overage = 0

    bhyt_eligible = qty × cap_unit
    bhyt_amount = bhyt_eligible × effective_rate / 100
    patient_pays = total_cost − bhyt_amount   (gồm cả ceiling_overage)
  else:
    bhyt_amount = 0; patient_pays = total_cost

Header rollup:
  total_cost     = SUM(items.total_cost)
  bhyt_covered   = SUM(items.bhyt_amount)
  patient_pays   = SUM(items.patient_pays)
  ceiling_overage = SUM(items.ceiling_overage)
```

## Luồng hoạt động

```
[1] Setup masters (1 lần):
    /app/sc-bhyt-code-config/new — vd N05 / 80% / TT 04/2024/TT-BYT
    /app/sc-patient/new — BN-2026-001, thẻ BHYT 1234567890, type Đúng tuyến, rate 80
    Item.has_bhyt=1 + Item.bhyt_payment_rate (fallback)

[2] WARD-STAFF tạo SC Dispensing Request
    │ purpose: Routine (cấp khoa) hoặc Patient-Specific (gắn BN)
    │ from_warehouse, items với requested_qty
    │
[3] Submit DR → status = Approved
    │
[4] Click "Tạo Stock Entry" → SC Stock Entry Material Issue draft
    │ DR.status = Issued, DR.stock_entry = SE link
    │
[5] STOREKEEPER kiểm batch FEFO → submit SE
    │ Tạo SLE -qty ở from_warehouse (FEFO check + bin consistency)
    │
[6] (Patient-Specific) Click "Tạo Patient Dispensing"
    │ Tạo SC Patient Dispensing draft
    │   - patient (auto fetch tên + bhyt_card + type + rate)
    │   - items copy từ DR với unit_cost = last purchase rate
    │   - Auto-calc BHYT per row
    │
[7] Submit PD → DR.status = Dispensed
    │ Ghi nhận chi phí vào hồ sơ BN cho quyết toán BHYT định kỳ
```

## API endpoints

```
POST /api/method/supplycore.api.bhyt.get_active_config
  Args: item_code, on_date?
  Returns: {bhyt_code, bhyt_group, payment_rate, ceiling_price} | None

POST /api/method/supplycore.api.bhyt.calculate_cost
  Body: {items: [{item_code, qty, unit_cost}], bhyt_card?, patient?}
  Returns: {items: [...per-row breakdown...], total_cost, bhyt_covered, patient_pays, ceiling_overage}
```

## Coverage Phase 1

| Yêu cầu | Status |
|---|---|
| BR-M7-01 Cấp phát theo khoa hoặc theo BN | ✓ DR.purpose=Routine/Patient-Specific |
| BR-M7-02 Vật tư BN gắn mã BHYT | ✓ Auto-calc trong PD via get_active_config |
| BR-M7-03 Ghi nhận SL thực dùng (≠ cấp) | ✓ PD.qty độc lập với DR.approved_qty |
| BR-BH-01 Mã BHYT N01-N09 | ✓ SC BHYT Code Config schema |
| BR-BH-02 Tỷ lệ thanh toán theo nhóm + đối tượng | ✓ cfg.payment_rate + patient.bhyt_payment_rate (lấy min) |
| BR-BH-03 Đơn vị tính kép (mua/dùng) | ✓ SC Item.buy_uom / use_uom / uom_conversion_factor |
| BR-BH-04 Giá trần BHYT | ✓ ceiling_price + ceiling_overage |
| BR-BH-05 Báo cáo quyết toán | ⏳ Defer (tổng hợp PD theo period) |
| UC-20..23 | ✓ |

## Connections panel (sẽ thấy ở UI)

- Form **SC Patient** → Connections sang Patient Dispensing (theo patient_id)
- Form **SC Dispensing Request** → Connections sang SC Stock Entry + Patient Dispensing
- Form **SC BHYT Code Config** → có thể filter Patient Dispensing có bhyt_code khớp

## Vận hành thực tế

```
Bước 1: SC BHYT Code Config
  - Nhóm N05 / 80% / item_group = "Vật tư tiêu hao" / TT 04/2024
Bước 2: SC Patient (lúc nhập viện)
  - BN-2026-001, BHYT 1234567890, type Đúng tuyến, rate 80
Bước 3: WARD tạo Dispensing Request Patient-Specific
  - patient = BN-2026-001
  - items: VTTH-GLOVE-S qty=10
Bước 4: Submit DR → Approved → Tạo Stock Entry → SK submit SE (FEFO check)
Bước 5: Tạo Patient Dispensing → BHYT auto-calc:
  - 10 đôi × 30,000 = 300,000
  - rate 80% × 300,000 = 240,000 BHYT
  - 60,000 BN tự trả
  - 0 vượt giá trần (ceiling chưa set)
Bước 6: Submit PD → record vào hồ sơ BN
```

## Defer (sau v1)

1. Đơn vị tính kép thực tế: convert qty buy_uom → use_uom khi calc BHYT (BR-BH-03 advanced)
2. Báo cáo quyết toán BHYT (SUM PD theo nhóm BHYT × period × department) — BR-BH-05
3. Workflow phê duyệt DR: WARD draft → Pharmacy/MGR approve → SK issue
4. Print phiếu cấp phát + bảng kê BHYT
5. Auto-tạo PD từ SE Issue submit (hook trigger)
