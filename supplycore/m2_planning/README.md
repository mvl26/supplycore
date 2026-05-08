# M2 — Kế hoạch tồn kho & Gọi hàng

Module quản lý **Procurement Plan** (kế hoạch mua sắm định kỳ) — đầu vào tự động cho M1/M3.

> ⚠ **v0.2 — chỉ Frappe**: Material Request giờ là `SC Material Request`, không còn ERPNext.

## DocTypes

| DocType | Loại | Mô tả |
|---|---|---|
| `Procurement Plan` | Submittable | Kế hoạch định kỳ (Monthly/Quarterly/Yearly) |
| `Procurement Plan Item` | Child Table | Vật tư trong plan với qty suggest từ consumption |
| `SC Material Request` | Submittable | Phiếu yêu cầu vật tư phát sinh từ Plan hoặc thủ công |
| `SC Material Request Item` | Child | Dòng VT trong MR |

**Master phụ thuộc:** `SC Item` · `SC UOM` · `SC Warehouse` · `SC Stock Ledger Entry` (đọc consumption)

## Naming series

- `SC-PP-YYYY-#####` — Procurement Plan
- `SC-MR-YYYY-#####` — SC Material Request

## Logic suggest qty (auto_load_items)

```
Cho mỗi SC Item is_stock_item=1, is_purchase_item=1:
   xuất kho 3 tháng gần nhất từ SC Stock Ledger Entry
   avg_monthly = SUM(|qty_change|) / lookback_months    (qty_change < 0 → xuất)
   base_demand = avg_monthly × (lead_time_days / 30)
   target_stock = base_demand × (1 + safety_factor%) + Item.safety_stock
   suggested_qty = max(0, target_stock − current_stock)

   current_stock = SUM(qty_change) từ SC Stock Ledger Entry tại warehouse

   nếu suggested ≤ 0 và không có lịch sử → bỏ qua
   ngược lại → append vào plan.items với:
     - planned_qty = suggested
     - estimated_unit_cost = đơn giá PO submit gần nhất
     - preferred_supplier = NCC giao nhiều nhất 12 tháng qua
```

## Luồng hoạt động

```
[1] SC-MGR/SK tạo Procurement Plan
        │ chọn warehouse + period (Monthly/Quarterly/Yearly)
        │ click "Tự nạp danh mục từ lịch sử tiêu thụ"
        ▼
    auto_load_items() → suggest items + qty + cost + preferred NCC
        │
[2] User review & adjust planned_qty per item
        ▼
    Submit Plan → status = Approved
        │
[3] Click "Tạo Material Request"
        ▼
    make_material_request() → tạo 1 SC MR draft với items hợp lệ (planned_qty > 0)
        │ MR.procurement_plan link, MR.auto_generated = 1
        │ Plan.status → Generated, Plan.material_request gắn link
        ▼
[4] SC-ACCOUNTANT/PURCHASER nhận email notification
        │ submit MR → status = Pending
        ▼
[5] Convert MR → SC Purchase Order (qua flow M1)
```

## Scheduler

- **daily** `m2_planning.tasks.check_reorder_levels`: cảnh báo email items có tồn ≤ ROP (BR-M2-02). Hiện tính ROP từ SC Item.safety_stock + lead_time, không dùng ERPNext Item Reorder
- **weekly** `m2_planning.tasks.generate_procurement_forecast`: tự tạo draft Plan đầu tuần (BR-M2-04, placeholder)

## Coverage Phase 1

| BR | Mô tả | Trạng thái |
|---|---|---|
| BR-M2-01 | Min/Max/ROP per item | ✓ Trên `SC Item` (safety_stock, lead_time_days) |
| BR-M2-02 | Auto cảnh báo ROP | ✓ Scheduler daily |
| BR-M2-03 | Tạo RO từ HĐK | ✓ Đã làm M1 |
| BR-M2-04 | Báo cáo dự báo nhu cầu 3-6-12 tháng | ✓ `_get_avg_monthly_consumption(months=N)` |
| UC-05..08 | Min/Max/ROP, Plan, MR, PO | ✓ |

## Trace

- Form Procurement Plan cuối: Connections sang `SC Material Request`
- Form SC MR cuối: Connections sang `SC Purchase Order` (filter procurement_plan)

## Vận hành

- `/app/procurement-plan/new` → tạo plan, click "Tự nạp" → review → submit → Tạo MR
- `/app/sc-material-request` → list MR phát sinh
- Email cảnh báo ROP gửi đến role `SupplyCore Storekeeper` + `SupplyCore Manager`

## Integration với module khác

**Incoming events (module này nhận trigger từ):**
- Khoa/SK tạo SC Material Request manual qua UI
- M5 SC Stock Ledger Entry → tính avg_monthly cho ROP

**Outgoing events (module này trigger / cung cấp data cho):**
- MR.on_submit → status=Approved (chờ user click 'Tạo PO')
- `MR.create_purchase_orders()` → SC Purchase Order draft (M1+M2 wiring)
- Daily scheduler `check_reorder_levels` → email + có thể tích hợp M11 alert

Xem [`FLOW.md`](../../FLOW.md) cho sơ đồ tổng thể.
