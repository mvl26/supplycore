# M9 — Kiểm kê & Đối soát

Module quản lý **SC Inventory Count Sheet** (phiếu kiểm kê) + **SC Stock Reconciliation** (điều chỉnh tồn kho + GL post theo VAS).

## DocTypes

| DocType | Loại | Mô tả |
|---|---|---|
| `SC Inventory Count Sheet` + ICS Item | Submittable | Phiếu kiểm kê — snapshot system_qty, nhập actual, auto variance |
| `SC Stock Reconciliation` + SR Item | Submittable | Điều chỉnh tồn kho + ghi SLE + GL Entry |

## Naming series

- `SC-ICS-YYYY-#####` — Inventory Count Sheet
- `SC-SR-YYYY-#####` — Stock Reconciliation

## Luồng hoạt động

```
[1] MGR tạo SC Inventory Count Sheet (status=Draft)
        │ chọn warehouse + count_scope (All / By Item Group / By Zone)
        │ recount_threshold_pct (default 5%)
        │
[2] Click "Auto-load items"
        │ Query SC SLE tổng qty > 0 ở warehouse
        │ snapshot system_qty + valuation_rate per row
        │ items table được nạp với actual_qty=null
        │
[3] In phiếu (hide_system_qty=1) → SK đếm thực tế
        │
[4] SK nhập actual_qty per row → save
        │ Auto compute:
        │   difference = actual − system
        │   variance_pct = |difference| / system × 100
        │   needs_recount = (variance_pct > threshold)
        │   variance_value = difference × valuation_rate
        │
[5] Đếm lại các row needs_recount → nhập recount_actual_qty
        │ Logic ưu tiên recount nếu có
        │
[6] Submit ICS → status=Counted
        │
[7] MGR review → click "Tạo Stock Reconciliation"
        │ make_stock_reconciliation() → SR draft với rows có chênh lệch
        │ ICS.stock_reconciliation = SR.name
        │
[8] ACCT review SR → set expense_account (default 642)
        │ Submit SR
        │   ├─ Post SC SLE per row (qty_change = difference)
        │   └─ Post SC GL Entry:
        │      Δ value > 0 (thừa): Dr 152 / Cr 642
        │      Δ value < 0 (thiếu): Dr 642 / Cr 152
        │ ICS.status = Reconciled
        ▼
    Tồn kho hệ thống đã khớp thực tế, sổ cái đã ghi nhận điều chỉnh
```

## Auto GL post (VAS pattern, M9)

| Trường hợp | Bút toán |
|---|---|
| **Thừa kho** (Δ > 0) | `Dr 152 Hàng tồn kho / Cr 642 CP QLDN (hoặc 711 TN khác)` |
| **Thiếu kho** (Δ < 0) | `Dr 642 CP QLDN / Cr 152 Hàng tồn kho` |
| **Cancel SR** | Đảo ngược SLE (qty_change đổi dấu) + đảo GL (Nợ ↔ Có) + `is_cancelled=1` |

## Coverage Phase 1

| BR / UC | Status |
|---|---|
| UC-27 Lập kế hoạch + thực hiện kiểm kê | ✓ Auto-load items + scope filtering |
| UC-28 Đối soát hệ thống vs thực tế | ✓ Recount flag + variance_pct + reason field |
| UC-19 Stock Reconciliation (M6 nói tới) | ✓ Đặt tại M9, link với ICS |
| Threshold đếm lại | ✓ recount_threshold_pct configurable |
| Hide system_qty khi in (chống bias) | ✓ hide_system_qty flag |
| GL Entry điều chỉnh giá trị tồn | ✓ Auto post 152 ↔ 642 |

## API endpoints

```
POST .../make_stock_reconciliation (method on doc)
POST .../auto_load_items (method on doc)
```

## Vận hành thực tế

```
1. /app/sc-inventory-count-sheet/new
   - warehouse: Kho Vật tư tiêu hao
   - count_scope: All Items
   - threshold: 5%
   → click "Auto-load items" → 30+ items với system_qty
2. In phiếu PDF (hide_system_qty=1) → đưa SK đếm
3. SK nhập actual_qty trên form/PDA
4. Save → auto variance, recount flags
5. Submit (status=Counted)
6. MGR click "Tạo Stock Reconciliation"
   - ACCT review chọn expense_account (642)
   - Submit SR → SLE adjustments + GL Entry
   - ICS.status = Reconciled
```

## Defer

1. PDA scan workflow cho mass counting (M4 PDA integration)
2. Recount escalation: yêu cầu 2 người ký xác nhận khi |Δ| > critical_threshold
3. Cycle counting (kiểm kê quay vòng theo nhóm thay vì 1 lần toàn kho)
4. Báo cáo lịch sử kiểm kê + tỷ lệ chính xác kho theo thời gian
5. Print format phiếu kiểm kê (chuẩn TT 200 form)

## Integration với module khác

**Incoming events (module này nhận trigger từ):**
- SK trigger ICS (manual hoặc cron `create_periodic_count`)
- M4 SLE → snapshot system_qty

**Outgoing events (module này trigger / cung cấp data cho):**
- ICS → SC Stock Reconciliation (SR draft)
- SR.on_submit → SLE adjustment (±diff_qty) + GL (Dr 152 / Cr 642 hoặc đảo)
- SR diff > recount_threshold_pct → recount workflow

Xem [`FLOW.md`](../../FLOW.md) cho sơ đồ tổng thể.
