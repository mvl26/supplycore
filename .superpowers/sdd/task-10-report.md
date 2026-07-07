# Task 10 Report — GĐ2 M7 Sales: E2E Order-to-Cash + seed demo + regression (cuối)

(Note: path này trước đó chứa báo cáo Task 10 của **GĐ1** — "Purge leftover hospital
ROLE strings". Bị thay thế ở đây theo brief GĐ2 Task 10 trỏ cùng file path này.)

## 1. E2E test — `supplycore/tests/sales_e2e_test.py::test_full_o2c()`

Dựng toàn bộ chuỗi Order-to-Cash trong 1 test, dữ liệu cách ly bằng
`random_string` suffix (SC UOM, SC Warehouse, SC Item batch-tracked, SC
Customer, SC Batch mới tạo mỗi lần chạy — không phụ thuộc dữ liệu có sẵn).

Chuỗi và assertion theo từng bước (đúng số liệu brief yêu cầu):

| Bước | Hành động | Assertion |
|---|---|---|
| 1 | `SCStockLedgerEntry.post(+100, valuation_rate=600, voucher_type="SC Purchase Receipt")` | `get_available_qty` = 100 |
| 2 | SFC (contract_qty=100, unit_price=1000) → submit | `status == "Hiệu lực"`; `SFC Item.remaining_qty == 100` |
| 3 | SO (qty=30) → submit → `approve()` | `SO.status == "Đã duyệt"`; sau approve **SFC Item.remaining_qty == 70** |
| 4 | DN (from_warehouse) → submit | stock 100→70 (`get_available_qty`); `SO.status == "Đã bàn giao"` |
| 5 | Acceptance Record → submit | `DN.status == "Đã nghiệm thu"` |
| 6 | SI (tax_rate=0) → submit | `SI.grand_total == 30000`; `get_balance("131", customer) == 30000`; 511 delta = **−30000** (credit 30000, no other 511 activity in test window); 632 delta = **+18000** (=30×600 COGS); 156 delta = **−18000**; `DN.status == "Đã xuất HĐ"` |
| 7 | Sales Receipt (amount=30000) → submit | `SI.outstanding_amount == 0`; `SI.status == "Đã thu đủ"`; `get_balance("131", customer) == 0` |
| Cuối | — | `SFC Item.remaining_qty == 70`, stock == 70, AR == 0 → `frappe.db.rollback()` |

511/632/156 dùng before/after **delta** (không assert giá trị tuyệt đối) vì các
account này không lọc theo `party` — an toàn trước dữ liệu global có sẵn từ
seed/test khác chạy song song trong cùng site. 131 (AR) dùng giá trị tuyệt
đối vì `get_balance` nhận `party=customer.name` nên cách ly tự nhiên theo
từng khách hàng test riêng.

Run:
```
bench --site supplycore-miyano.local execute supplycore.tests.sales_e2e_test.run
→ {"passed": 1, "total": 1, "results": [{"pass": true, "msg": "OK O2C full chain:
   SFC.remaining=70.0, stock=70.0, 131=0.0, 511Δ=-30000.0, 632Δ=18000.0",
   "test": "test_full_o2c"}]}
```

## 2. Seed demo — `supplycore/setup/seed_sales_demo.py`

`run()` idempotent, KHÔNG auto-chạy trong patch nào (gọi tay khi cần):
- Tạo 1 `SC Customer` demo: **"Công ty TNHH Thương mại ABC"** (tax_code cố
  định `0101888999-DEMO-ABC` dùng làm khóa idempotency), credit_limit
  500,000,000, payment_terms "Net 30" — hồ sơ công ty thương mại/phân phối,
  KHÔNG phải bệnh viện/khoa/BN.
- Tạo 1 `SC Sales Framework Contract` submitted (status "Hiệu lực") cho
  KH trên, 2 dòng dùng lại SC Item đã seed sẵn (`DTRC-NACL09`,
  `VTTH-IV-SET` — vật tư tiêu hao y tế MVL phân phối bán buôn, không phải
  cấp phát nội viện): contract_qty 500/300, unit_price 32000/13000.
- Idempotency check: SFC doctype không có field remarks/free-text, nên dò
  theo "khách hàng demo đã có SFC nào chưa" (1 KH demo chỉ có đúng 1 SFC do
  script này sinh).

Verify chạy 2 lần liên tiếp:
```
Lần 1: {"customer": "SC-CUS-00081", "sfc": "SC-SFC-2026-00082",
        "customer_created": true,  "sfc_created": true}
Lần 2: {"customer": "SC-CUS-00081", "sfc": "SC-SFC-2026-00082",
        "customer_created": false, "sfc_created": false}
```
→ đúng idempotent, không tạo trùng. Dữ liệu demo giữ nguyên trong DB
`supplycore-miyano.local` sau khi chạy (đây là mục đích của seed demo).

## 3. Regression

### 3.1 Invariant

| Lệnh | Kết quả |
|---|---|
| `bench --site supplycore-miyano.local migrate` | Sạch — không traceback, chạy hết "Updating Dashboard for supplycore" / `after_migrate` hooks |
| `bench build --app supplycore` | Sạch — "DONE Total Build Time" |
| `bench --site supplycore-miyano.local execute frappe.ping` | `"pong"` |

### 3.2 Bảng pass suite

| Suite | Pass/Total |
|---|---|
| `smoke_m8` | ok (12 bước, trial balance = 0) |
| `smoke_m10` | ok (8 bước, recall/block/audit đầy đủ) |
| `uc26_test` | 8/8 |
| `gd2_foundation_test` | 3/3 |
| `sc_customer_test` | 3/3 |
| `sc_sfc_test` | 2/2 |
| `sc_sales_order_test` | 5/5 |
| `sc_delivery_note_test` | 5/5 |
| `sc_acceptance_test` | 2/2 |
| `sc_sales_invoice_test` | 6/6 |
| `sc_sales_receipt_test` | 5/5 |
| `sales_api_test` | 6/6 |
| `sales_e2e_test` (Task 10, mới) | 1/1 |

Tổng các suite GĐ2 M7 Sales + smoke liên quan: **58/58 PASS**, không có suite
nào đỏ ngoài `uc24_test`/`uc25_test` (mục dưới).

### 3.3 uc24_test / uc25_test — lỗi biết trước, KHÔNG phải hồi quy

```
uc24_test: 3/10 pass — 7 test còn lại throw
  "SC-E-PR-MISSING-EXPIRY: Các dòng [1] chưa nhập Hạn dùng..."
uc25_test: 0/10 pass — cùng nguyên nhân SC-E-PR-MISSING-EXPIRY
```
Nguyên nhân: helper `_make_submitted_po_and_pr()` trong 2 file test này tạo
`SC Purchase Receipt` không set `expiry_date` trên item row; `SC Purchase
Receipt` hiện tại validate bắt buộc Hạn dùng (BRU không liên quan M7 Sales).
Đây là lỗi tiền-tồn tại của test fixture UC-24/UC-25 (đã ghi trong brief là
biết trước, không liên quan bán hàng) — **không phải hồi quy do Task 10**.
Không sửa (ngoài phạm vi M7 Sales; sửa fixture UC-24/25 thuộc phạm vi mua
hàng M8).

### 3.4 Grep-clean GĐ1 — 0 dòng code sống

Brief liệt kê exclude `/backups/, __pycache__, patches/v0_6, patches/v0_7,
public/frontend` nhưng **không giới hạn phần mở rộng file**. Grep-toàn-bộ
theo đúng nghĩa đen (`grep -rniE ... supplycore/` không giới hạn `--include`)
trả về **119 dòng**, TOÀN BỘ nằm trong tài liệu Markdown lịch sử
(`*_FLOW.md`, `README.md`, `LUONG_NHAN_VIEN.md`, `MAIN_FLOW.md`,
`UC_TEST.md` ở các module m6/m7/m8/m10/m11), 1 file dịch
(`translations/vi.csv`) và 1 print format cũ (`templates/print_formats/
dispensing_slip.html`) — các file này **tiền tồn tại từ trước GĐ2**, chưa
từng nằm trong phạm vi grep-clean GĐ1 gốc.

Đối chiếu `docs/superpowers/specs/2026-07-03-gd1-go-nghiep-vu-benh-vien-design.md`
(mục 4, dòng 100) và `docs/superpowers/plans/2026-07-06-gd1-go-nghiep-vu-benh-vien.md`
(dòng 391-393): grep-clean GĐ1 gốc luôn giới hạn
`--include=*.py --include=*.json --include=*.js --include=*.vue` (mã sống),
KHÔNG bao gồm `.md`/`.csv`/`.html`. Áp đúng scope đó (+ 4 loại trừ theo
brief Task 10):

```
grep -rniE "dispens|patient|bhyt|his_code|SC Patient" supplycore/ \
  --include=*.py --include=*.json --include=*.js --include=*.vue \
  --exclude-dir=backups --exclude-dir=__pycache__ --exclude-dir=frontend \
  | grep -vE "/patches/v0_6/|/patches/v0_7/|/public/"
→ 0 dòng (sau khi sửa 1 hồi quy tự gây ra — xem dưới)
```

**Hồi quy tự phát hiện & tự sửa**: bản nháp đầu tiên của
`seed_sales_demo.py` có comment tiếng Việt xuống dòng
`"— mảng phân phối, KHÔNG cấp\n# phát/BHYT: ..."` — chữ "BHYT" bị tách dòng
nhưng vẫn khớp regex `bhyt`. Grep code-scope phát hiện đúng 1 dòng vi phạm
(`supplycore/setup/seed_sales_demo.py:20`). Đã sửa lại comment thành
"— bán buôn phân phối B2B" (không còn thuật ngữ bệnh viện), grep lại → 0.
Đây là ví dụ đúng mục đích của check: bắt được leftover mới, không phải
false positive.

## Concerns

1. **Grep phạm vi rộng (không `--include`) vẫn còn 119 hit** trong tài liệu
   `.md`/`.csv`/`.html` — không phải hồi quy của Task 10 (pre-existing từ
   trước GĐ2, ngoài phạm vi mã sống mà GĐ1 đã verify), nhưng nếu có yêu cầu
   "MVL pivot hoàn chỉnh 100% kể cả tài liệu" thì đây là việc còn tồn đọng
   cho một task dọn tài liệu riêng (không mở rộng phạm vi ở đây theo đúng
   brief Task 10 chỉ yêu cầu code-scope).
2. `uc24_test`/`uc25_test` failing 0/10 và 3/10 là pre-existing (SC-E-PR-
   MISSING-EXPIRY), không thuộc M7 Sales — cần một task riêng ở phạm vi mua
   hàng/M3 Receiving để sửa fixture (thêm `expiry_date` khi tạo PR test) nếu
   muốn 2 suite này xanh 100%.
3. `seed_sales_demo.py` ghi `frappe.db.commit()` trực tiếp (không rollback)
   — đúng theo mục đích seed demo (dữ liệu giữ lại), khác với test pattern
   rollback-cuối. Đã chạy thực tế 1 lần trên site `supplycore-miyano.local`
   trong quá trình verify → để lại `SC-CUS-00081` / `SC-SFC-2026-00082`
   trong DB (không phải rác test, là demo data có chủ đích).

## Commit

`git status` xác nhận working tree chỉ có 2 file mới thuộc Task 10
(`supplycore/tests/sales_e2e_test.py`,
`supplycore/setup/seed_sales_demo.py`) + report này — không có file nào
khác bị thay đổi ngoài phạm vi task, an toàn để commit riêng.
