# M8 — Kế toán & Thanh toán NCC

Module quản lý **SC Purchase Invoice** (hóa đơn NCC + 3-way match) + **SC Payment Entry** (thanh toán có approval theo ngưỡng) + **SC GL Entry** (immutable bút toán theo VAS).

> ⚠ **v0.2 — chỉ Frappe**: GL/CoA build từ scratch (không dùng ERPNext).

## DocTypes

| DocType | Loại | Module | Mô tả |
|---|---|---|---|
| `SC GL Account` | Master tree | Supplycore | Chart of Accounts theo TT 200/2014/TT-BTC |
| `SC GL Entry` | Immutable log | Supplycore | Bút toán Nợ/Có, không sửa được |
| `SC Purchase Invoice` + PI Item | Submittable | M8 | Hóa đơn NCC + 3-way match logic |
| `SC Payment Entry` + Reference | Submittable | M8 | Thanh toán đa-PI với approval threshold |

## Naming series

- `<account_code>` — SC GL Account (autoname=field, vd "152", "331")
- `SC-GL-YYYY-########` — GL Entry
- `SC-PI-YYYY-#####` — Purchase Invoice
- `SC-PE-YYYY-#####` — Payment Entry

## Chart of Accounts (seeded)

```
100 TÀI SẢN
├── 110 Tiền
│   ├── 1111 Tiền mặt VND
│   └── 1121 Tiền gửi NH VND
├── 130 Phải thu KH → 131
├── 133 Thuế GTGT KT → 1331
└── 150 Hàng tồn kho
    ├── 152 Nguyên liệu vật liệu  ← VTYT tiêu hao
    ├── 153 Công cụ dụng cụ
    └── 156 Hàng hóa

300 NỢ PHẢI TRẢ
├── 330 Phải trả NCC → 331
└── 333 Thuế phải nộp → 3331

600 CHI PHÍ
├── 632 Giá vốn hàng bán
├── 641 Chi phí bán hàng
└── 642 Chi phí QLDN
```

## 3-way match logic (BR-M8-02)

```
Khi tạo SC Purchase Invoice:
  if not purchase_order:
    status = "Not Applicable"; return

  PO_total = SC PO.grand_total                   (đã submit)
  PR_total = SUM(SC PR.total_value)              (PR liên kết PO, docstatus=1, is_return=0)
  PI_total = self.subtotal                       (trước thuế)

  po_var_pct = |PI − PO| / PO × 100
  pr_var_pct = |PI − PR| / PR × 100

  Hard cap: PI > PO × 1.05 → throw SC-E009 THREE_WAY_MISMATCH
  
  if po_var_pct ≤ 1% AND (PR=0 OR pr_var_pct ≤ 1%):
    status = "Match" + approval_required_by = Manager (default)
  else:
    status = "Mismatch" + approval_required_by = Executive
    Cảnh báo orange với chi tiết var

Approval level theo amount:
  grand_total ≥ 50tr → Executive (đọc từ SupplyCore Settings.po_approval_threshold)
  grand_total < 50tr → Manager
  Mismatch luôn cần Executive
```

## Auto GL post (VAS pattern)

**Khi PI submit:**
```
Dr 152  Hàng tồn kho           subtotal
Dr 1331 Thuế GTGT KT           vat_amount  (nếu vat>0)
   Cr 331 Phải trả NCC         grand_total
```

**Khi PE submit (Bank Transfer):**
```
Dr 331 Phải trả NCC           allocated_amount  (mỗi PI 1 row riêng biệt)
   Cr 1121 Tiền gửi NH        amount  (tổng)
```

**Cancel:** `SCGLEntry.cancel_voucher` → insert đối ứng đảo Nợ↔Có + đánh dấu `is_cancelled=1`. Đảm bảo audit trail không xóa.

## Luồng hoạt động

```
[1] SC PR submit (M3)            ← qty + value đã có
[2] ACCT tạo SC Purchase Invoice
        │ supplier + supplier_invoice_no + invoice_date
        │ purchase_order link
        │ items (rate, qty từ HĐ NCC)
        ▼
    Validate:
        - 3-way match: PO ↔ PR ↔ PI variance
        - Hard cap PI > PO+5% → throw
        - Determine approval_required_by (Manager/Executive)
        - Auto due_date = invoice_date + 30
        ▼
[3] Submit PI
        │ Auto GL post (Dr 152 + Dr 1331 / Cr 331)
        │ status = Approved
        │ outstanding_amount = grand_total
        ▼
[4] ACCT tạo SC Payment Entry
        │ supplier + amount + payment_method
        │ references: chọn PI(s) + allocated_amount
        │ allocated_total = SUM(refs.allocated_amount) phải = amount
        ▼
    Validate:
        - PI thuộc đúng supplier
        - allocated ≤ outstanding của từng PI
        - approval_level = Manager/Executive theo amount vs threshold
        ▼
[5] Submit PE
        │ Auto GL post (Dr 331 / Cr 1121)
        │ Update PI.paid_amount + outstanding_amount + status
        │   - outstanding = 0 → Paid
        │   - outstanding > 0 → Partly Paid
        ▼
[6] ACCT báo cáo:
        - api.accounting.supplier_balance(supplier) → outstanding/overdue/credit_limit
        - SC GL Entry filter theo period → trial balance
```

## API endpoints

```
POST /api/method/supplycore.api.accounting.three_way_match
  Args: purchase_invoice OR (purchase_order, pi_subtotal)
  Returns: {status, po_total, pr_total, pi_total, po_var_pct, pr_var_pct, variance_amount}

GET /api/method/supplycore.api.accounting.supplier_balance?supplier=X
  Returns: {outstanding, overdue, credit_limit, limit_used_pct, exceeds_limit}
```

## Coverage Phase 1

| BR / UC | Status |
|---|---|
| BR-M8-01 Auto GL Entry theo VAS | ✓ PI/PE submit → SCGLEntry.post_journal cân bằng Nợ=Có |
| BR-M8-02 3-way match PO↔PR↔PI ±1% | ✓ tolerance + hard cap +5% |
| BR-M8-03 Hạn mức tín dụng NCC + cảnh báo công nợ vượt | ✓ supplier_balance API + SC Supplier.credit_limit field |
| UC-24 Tạo + đối chiếu PI | ✓ |
| UC-25 Payment Entry + theo dõi công nợ | ✓ |
| UC-26 Báo cáo tài chính | ⏳ Cần Script Report (trial balance, AP aging) |

## Error codes

- `SC-E007 DUPLICATE_INVOICE` — supplier_invoice_no trùng (TODO)
- `SC-E009 THREE_WAY_MISMATCH` — PI > PO + 5% hoặc supplier mismatch

## Vận hành

```
1. Setup CoA (auto qua seed_master_data hoặc bench execute supplycore.setup.seed_master_data.run)
2. /app/sc-purchase-invoice/new
   - supplier + supplier_invoice_no + invoice_date
   - purchase_order link → 3-way match auto-run
   - items + vat_rate
   - save → submit (GL post 152/1331/331)
3. /app/sc-payment-entry/new
   - supplier + amount + payment_method
   - references: chọn PI có outstanding > 0
   - submit → GL post 331/1121, PI.status = Paid
4. /app/sc-gl-entry — view bút toán + filter theo voucher_type/account
5. /app/sc-gl-account — view CoA tree với balance
```

## Defer (sau v1)

1. Script Report: Trial Balance + AP Aging (UC-26 chi tiết)
2. Workflow phê duyệt PE Manager → Executive với multi-stage approval
4. Foreign currency support
5. Bank reconciliation

## Integration với module khác

**Incoming events (module này nhận trigger từ):**
- M3 PR + M1 PO → 3-way match input
- PI button từ M3 PR form (`make_invoice_from_pr`)

**Outgoing events (module này trigger / cung cấp data cho):**
- PI.on_submit → SC GL Entry (Dr 152 + Dr 1331 / Cr 331) — VAS
- PE.on_submit → SC GL Entry (Dr 331 / Cr 1121)
- PE update PI.outstanding + status
- API `three_way_match`, `supplier_balance` → M11 KPI

Xem [`FLOW.md`](../../FLOW.md) cho sơ đồ tổng thể.
