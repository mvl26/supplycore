# M1 — Hợp đồng & Nhà cung cấp

Module quản lý **Framework Contract** (hợp đồng khung) và **Release Order** (lệnh gọi hàng) — cơ sở cho mọi giao dịch mua hàng trong SupplyCore.

> ⚠ **v0.2 — chỉ Frappe**: M1 không còn dùng ERPNext doctype. Nhà cung cấp = `SC Supplier`, đặt hàng = `SC Purchase Order`.

## DocTypes

| DocType | Loại | Mô tả |
|---|---|---|
| `Framework Contract` | Submittable | Hợp đồng khung với 1 NCC, có nhiều `FC Item` |
| `FC Item` | Child Table | Dòng vật tư trong hợp đồng — qty + đơn giá |
| `Release Order` | Submittable | Lệnh gọi hàng dựa trên FC; submit → tạo SC PO |
| `RO Item` | Child Table | Dòng vật tư trong Release Order |

**Master phụ thuộc:** `SC Supplier` · `SC Item` · `SC UOM` · `SC Purchase Order` (sinh ra)

## Naming series

- `SC-FC-YYYY-#####` — Framework Contract
- `SC-RO-YYYY-#####` — Release Order

## Trường giá trị

| Field | Ý nghĩa |
|---|---|
| `total_value` | Tổng giá trị HĐK do user nhập |
| `used_value` | Tổng `grand_total` của SC Purchase Order đã submit (docstatus=1) |
| `committed_value` | Tổng `total_amount` của Release Order Approved chưa convert |
| `remaining_value` | `total_value − used_value − committed_value` |

## Luồng hoạt động

```
[1] SC-ACCOUNTANT/MGR tạo Framework Contract
        │ append items (vật tư + đơn giá + SL hợp đồng)
        ▼
    Submit → status = Active (trừ khi today > valid_to → Expired)
        │
[2] User tạo Release Order
        │ chọn framework_contract → JS auto-fill items từ FC
        │ nhập qty cho item cần gọi
        │ Python validate: qty ≤ FC Item.remaining_qty, total ≤ FC.remaining_value
        ▼
    Submit → status = Approved
        │ FC.recalculate_used_value() → committed_value tăng
        ▼
[3] User click "Tạo Purchase Order"
        ▼
    Release Order.make_purchase_order()
        │ tạo SC Purchase Order draft với link framework_contract + release_order
        │ RO status → Converted, PO link gắn vào RO
        │ FC.recalculate_used_value() → committed giảm
        ▼
[4] SC PO submit → status Approved
        │ FC.recalculate_used_value() → used_value tăng = grand_total
        │ RO.status nếu chưa Converted → cập nhật
        ▼
[5] (M3) SC Purchase Receipt với purchase_order link
        │ ↳ trừ committed, ghi nhận received_qty trong PO Item
```

## Hooks & API

- **Daily scheduler** `m1_contract.tasks.check_contract_expiry`: cảnh báo email khi HĐ <30/15/7 ngày hết hạn (BR-M1-03)
- **Whitelisted method** `Framework Contract.recalculate_used_value()` — tính lại từ PO + RO
- **Whitelisted method** `Release Order.make_purchase_order()` — convert RO → SC PO

## Coverage Phase 1

| BR | Mô tả | Trạng thái |
|---|---|---|
| BR-M1-01 | Lưu thông tin NCC đầy đủ | ✓ `SC Supplier` schema |
| BR-M1-02 | Framework Contract với danh mục VT + đơn giá | ✓ |
| BR-M1-03 | Cảnh báo HĐ sắp hết hạn 30/15/7 | ✓ scheduler daily |
| BR-M1-04 | Lịch sử đánh giá NCC | ⚠ field `rating` có; auto-update từ QC fail rate (defer) |
| BR-M1-05 | Bảng giá NCC theo thời kỳ | ✓ FC Item.unit_price + amend_from chain |
| UC-01..04 | Tìm/quản lý NCC, FC, gia hạn | ✓ |

## Trace từ Connections panel

- Form **Framework Contract** cuối: hiển thị Connections sang **Release Order** + **SC Purchase Order**
- Form **Release Order** cuối: link sang **SC Purchase Order** sinh ra

## Error codes (M1)

- `SC-E002 FC_INACTIVE` — HĐK không Active khi tạo RO/PO
- `SC-E002 FC_EXCEEDED` — Tổng PO/RO vượt remaining_value
- `SC-E002 FC_ITEM_NOT_FOUND` — VT không thuộc HĐK
- `SC-E002 FC_EXPIRED` — Today > valid_to

## Vận hành

- `/app/sc-supplier` → master NCC trước khi tạo HĐK
- `/app/framework-contract/new` → tạo HĐK draft
- `/app/release-order/new` → gọi hàng từ HĐK đã Active
- `/app/sc-purchase-order` → đơn đặt hàng phát sinh từ RO

## Integration với module khác

**Incoming events (module này nhận trigger từ):**
- M2 `SC Material Request.create_purchase_orders()` → đọc FC để tìm cheapest unit_price
- M8 `SC Purchase Order.on_submit` → trigger `FC.recalculate_used_value()`

**Outgoing events (module này trigger / cung cấp data cho):**
- FC.remaining_value gate cho M2 PO suggest (SC-E002 nếu vượt)
- FC.unit_price làm rate mặc định cho SC PO Item
- Daily scheduler email cảnh báo 30/15/7 ngày → M11 Alert (contract_expiring)

Xem [`FLOW.md`](../../FLOW.md) cho sơ đồ tổng thể.
