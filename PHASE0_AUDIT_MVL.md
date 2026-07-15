# PHASE 0 — AUDIT & GAP LIST: Flow bán hàng theo HĐ khung (MVL Distributor)

**Ngày:** 2026-07-13 · **App:** supplycore (Frappe v15, custom, no-ERPNext) · **Site test:** `supplycore-miyano.local`
**Nguyên tắc:** app ĐANG CHẠY — tái sử dụng tối đa, chỉ thêm mới, zero regression, patch idempotent.

> Nguồn: 6 audit song song (A HĐ khung/master · B Portal · C Chuỗi chứng từ · D Rule/công nợ · E Print TT99 · F QA).
> Đã verify trực tiếp mâu thuẫn A↔B: `sold_qty` **chỉ cập nhật khi `approve()`** (sc_sales_order.py:148) — không cập nhật lúc KH đặt. Chống oversell BRU-SO-001 tính LIVE nên vẫn chặn đúng; chỉ số HIỂN THỊ bị trễ.

---

## 1. BẢNG MAP — 6 bước flow mục tiêu ↔ hiện trạng

### Bước (1) — Ký & số hoá HĐ khung, nhập KH, tạo tài khoản portal

| Yêu cầu | Trạng thái | Chi tiết |
|---|---|---|
| Doctype HĐ khung số hoá | ĐÃ CÓ ĐỦ | `SC Sales Framework Contract` (submittable, track_changes) |
| Định mức SL + giá / item | ĐÃ CÓ ĐỦ | `SFC Item.contract_qty`, `unit_price` |
| Đã gọi / còn lại | CÓ NHƯNG THIẾU | `sold_qty`, `remaining_qty` (read_only) — chỉ recalc khi **duyệt** đơn, không khi đặt → số hiển thị trễ |
| Hiệu lực từ/đến | CÓ NHƯNG THIẾU | `valid_from`/`valid_to` **không `reqd` ở backend** (chỉ frontend) → có thể submit HĐ không hạn, BRU-SFC-001 bị bỏ qua |
| Trạng thái | CÓ NHƯNG THIẾU | `status` Select có `Hiệu lực/Hết hạn/Thanh lý` nhưng: (a) không scheduler tự "Hết hạn"; (b) không có "Hết định mức"; (c) "Chờ duyệt" là option chết |
| Nhập thông tin KH | ĐÃ CÓ ĐỦ | `SC Customer`: name, tax_code(unique), phone, địa chỉ, credit_limit, payment_terms, portal_user |
| Tạo user portal role Customer | CÓ NHƯNG THIẾU | Hàm `portal_provision(customer,email)` (portal.py:39) có sẵn — **KHÔNG có nút UI nào gọi** → nhân viên phải gọi API tay |
| Print HĐ khung ký/PDF | CHƯA CÓ | Không có print format nào |

### Bước (2) — KH gọi hàng trên cổng → đơn tham chiếu HĐ → duyệt nội bộ → sinh phiếu giao

| Yêu cầu | Trạng thái | Chi tiết |
|---|---|---|
| Form gọi hàng theo HĐ (portal) | ĐÃ CÓ ĐỦ | `portal_order_place(contract, items)` (portal.py:247), giá/định mức lấy từ HĐ |
| Đơn tham chiếu HĐ, lấy giá/SL còn lại | ĐÃ CÓ ĐỦ | `_apply_sfc_pricing_and_limits` — giá từ SFC, chặn item ngoài HĐ, chặn vượt remaining LIVE |
| Duyệt nội bộ | CÓ NHƯNG THIẾU | **Không có Frappe Workflow** — dùng docstatus + field `status` + `approve()`/`reject()`. Ai có quyền submit là duyệt được, không có role "người duyệt" riêng |
| Duyệt → **tự sinh** phiếu giao | CHƯA CÓ (auto) | `approve()` KHÔNG tạo DN. Phải gọi riêng `sales.py:124 delivery_create()` (thủ công) |

### Bước (3) — Hàng đến → KH xem PGH + biên bản nghiệm thu → xác nhận → tự sinh hoá đơn

| Yêu cầu | Trạng thái | Chi tiết |
|---|---|---|
| KH xem Phiếu giao hàng | CÓ NHƯNG THIẾU | Không có endpoint list PGH; chỉ tải bản in 1 PGH sau khi milestone done |
| KH xem Biên bản nghiệm thu | CHƯA CÓ | `SC Acceptance Record` KHÔNG trong `DOWNLOADABLE_DOCTYPES`; không endpoint list/download |
| KH xác nhận nhận hàng | CHƯA CÓ | Không endpoint/field/status cho KH tự xác nhận. Nghiệm thu hiện do **nội bộ** tạo (`delivery_accept`) |
| Xác nhận → **tự sinh** hoá đơn | CHƯA CÓ (auto) | `sc_acceptance_record.on_submit` KHÔNG tạo SI. Phải gọi riêng `sales.py:184 sales_invoice_create()` |

### Bước (4) — Cổng hiển thị HĐ, tổng đã gọi, số lần gọi, biên bản, hoá đơn, công nợ

| Yêu cầu | Trạng thái | Chi tiết |
|---|---|---|
| HĐ khung | ĐÃ CÓ ĐỦ | `portal_contracts` (lọc Hiệu lực + còn hạn) |
| Tổng SL đã gọi | THIẾU (chỉ dữ liệu, chưa hiển thị) | Có `sold_qty` per-item, chưa tổng hợp/hiển thị |
| Số lần gọi | THIẾU | Không endpoint đếm |
| Danh sách biên bản | CHƯA CÓ | — |
| Danh sách hoá đơn | CHƯA CÓ | Không `portal_invoices` |
| Công nợ phải trả | CÓ NHƯNG THIẾU | `portal_me.outstanding` = tổng dư nợ 131; chưa chi tiết theo HĐ/tuổi nợ |

### Bước (5) — RULE chặn gọi: nợ / định mức / tồn kho

| Rule | Trạng thái | Chi tiết |
|---|---|---|
| Nợ vượt ngưỡng → chặn + hiện min phải trả | CÓ NHƯNG THIẾU (nghiêm trọng) | `_check_credit_limit` (SO on_submit). **FAIL-OPEN** nếu `default_receivable_account` trống (bal=0). `credit_limit<=0` = vô hạn. `portal_register` default credit_limit=0 → KH tự đăng ký lọt. **Không hiện "số tối thiểu phải trả"** |
| Hết định mức → chặn + báo SL còn lại | CÓ NHƯNG THIẾU | BRU-SO-001 chặn đúng (LIVE) nhưng message không hiện thẳng "SL còn lại" |
| Hết tồn → chặn | CHƯA CÓ ở bước gọi | Chỉ chặn ở khâu giao DN (BRU-INV-001), không ở portal order-place |
| Ngưỡng trong Settings (không hard-code) | CÓ NHƯNG THIẾU | Ngưỡng nằm ở `SC Customer.credit_limit` per-KH; **không có ngưỡng nợ toàn cục trong Settings** |
| **1 hàm công nợ chuẩn duy nhất** | CHƯA CÓ | 2 nguồn: Rule/Portal dùng GL `get_balance(131)`; Report dùng `SI.outstanding_amount` → có thể lệch. Rule & Portal cùng gọi get_balance nhưng resolve account riêng (Portal có fallback, Rule fail-open) |

### Bước (6) — Print Format TT99, PDF đối soát, số liên tục

| Yêu cầu | Trạng thái | Chi tiết |
|---|---|---|
| Print format mọi phiếu | CHƯA CÓ | **KHÔNG có print format nào trong toàn app** |
| Yếu tố TT99 | CHƯA CÓ | Thiếu MST người bán, tiền-bằng-chữ, block chữ ký. `hooks.py` fixtures Print Format **bỏ sót module "M7 Sales"** |
| Số chứng từ liên tục | CÓ NHƯNG THIẾU | autoname `format:{#####}` — không gapless (nhảy số khi rollback/xoá nháp); `{YYYY}` theo ngày tạo, không theo kỳ kế toán |

---

## 2. GAP LIST (phân loại + mức độ)

### (a) Field / doctype / settings
| # | Gap | Mức | File |
|---|---|---|---|
| a1 | `valid_from`/`valid_to` đặt `reqd:1` (backfill bản ghi cũ nếu thiếu) | **BLOCKER** | sc_sales_framework_contract.json |
| a2 | Ngưỡng nợ toàn cục + cờ bật/tắt rule vào `SupplyCore Settings` (theo yêu cầu "ngưỡng trong Settings") | BLOCKER-theo-Q3 (per-KH credit_limit có thể đã đủ "không hard-code") | supplycore_settings.json |
| a3 | `default_receivable_account` bắt buộc set (chặn fail-open) | **BLOCKER** | patch + validate |
| a4 | Field KH xác nhận nhận hàng (dùng SC Acceptance Record làm bằng chứng, hoặc `customer_confirmed` trên DN) | **BLOCKER** | quyết định thiết kế |
| a5 | MST + tên + địa chỉ người bán vào Settings (in TT99) | NÊN CÓ | supplycore_settings.json |
| a6 | Trạng thái "Hết định mức"/cờ exhausted trên SFC | NÊN CÓ | sc_sales_framework_contract |
| a7 | consumed_value/remaining_value theo tiền ở header SFC | NICE | — |

### (b) Logic / hook / workflow
| # | Gap | Mức | File |
|---|---|---|---|
| b1 | **1 hàm công nợ chuẩn** `get_customer_outstanding(customer)` — Rule + Portal + Report + Print gọi chung; throw khi account trống (bỏ fail-open) | **BLOCKER** | mới: utils, sửa sc_sales_order/portal/financial_reports |
| b2 | Rule nợ hiện "số tối thiểu phải trả" = `bal + total − limit` | **BLOCKER** | sc_sales_order.py:124 |
| b3 | Sửa `credit_limit<=0` bỏ qua + `portal_register` default 0 (migration set hạn mức trước) | **BLOCKER** | sc_sales_order.py:114, portal.py:477 |
| b4 | Endpoint KH xác nhận nhận hàng `portal_confirm_delivery(dn)` → tạo SC Acceptance Record (scope customer) | **BLOCKER** | portal.py |
| b5 | Sinh DN khi duyệt + sinh SI khi nghiệm thu xác nhận (bọc lỗi tồn/FEFO để approve không rollback ngoài ý) | BLOCKER-theo-Q2 (auto hoàn toàn vs nút bấm) | sc_sales_order/sc_acceptance_record |
| b6 | Đăng ký `permission_query_conditions` + `has_permission` cho SC Acceptance Record TRƯỚC khi lộ cho portal (chống rò rỉ chéo) | **BLOCKER** | hooks.py + permissions.py |
| b7 | Kiểm tồn kho ở bước gọi hàng portal (nếu chốt chặn sớm) | NÊN CÓ (chờ quyết định) | portal.py/sc_sales_order |
| b8 | BRU-SO-001 hiện thẳng "SL còn lại" | NÊN CÓ | sc_sales_order.py:100 |
| b9 | Scheduler daily "Hiệu lực"→"Hết hạn" theo valid_to | NÊN CÓ | tasks + hooks scheduler |
| b10 | Cập nhật `sold_qty` sớm hơn (hoặc tách "đã đặt" vs "đã duyệt") | NÊN CÓ | sc_sales_order |
| b11 | AR phân bổ 1 phiếu thu cho nhiều hoá đơn (giống PE) | NICE | sc_sales_receipt |
| b12 | Ràng buộc chống tạo trùng DN/SI cấp DB (TOCTOU) | NÊN CÓ | controller |

### (c) Portal / Print
| # | Gap | Mức | File |
|---|---|---|---|
| c1 | `portal_deliveries()` + `portal_acceptance_records()` + `portal_invoices()` (scope customer) | **BLOCKER** | portal.py |
| c2 | Thêm SC Acceptance Record vào `DOWNLOADABLE_DOCTYPES` (kèm b6) | **BLOCKER** | portal.py:23 |
| c3 | Tab portal "Giao nhận & Nghiệm thu" (list + nút xác nhận) + "Hoá đơn & Công nợ" | **BLOCKER** | www/portal/index.html |
| c4 | 7 Print Format TT99: SFC, SO, DN, Acceptance, SI, Sales Receipt, (PE) | **BLOCKER** | mới |
| c5 | Sửa `hooks.py` fixtures thêm module "M7 Sales" cho Print Format | CAO | hooks.py:125 |
| c6 | Helper "số tiền bằng chữ" tiếng Việt (VND) | CAO | utils |
| c7 | Hiện "tổng đã gọi" + "số lần gọi" trên portal | NÊN CÓ | portal.py + html |
| c8 | Cơ chế số gapless / neo {YYYY} theo kỳ kế toán | NÊN CÓ | doctype naming |

---

## 3. DIỆN BẢO VỆ REGRESSION (không được làm hỏng)
- Toàn bộ module procurement M1–M6, M8–M11 (mua NCC, kho, FEFO, kế toán mua, kiểm kê, recall, dashboard) — **không đụng**.
- 4 lớp phân quyền portal đang kín (query cond / has_permission / before_request / guarded_client_get) — mọi doctype mới lộ cho portal PHẢI mirror đủ.
- Chuỗi status tiếng Việt là điểm chịu lực chống trùng — **không đổi tên** giá trị status.
- Reversal SLE append-only + COGS filter — không đổi pattern.
- `credit_hold` side-effect từ `_check_credit_limit` — giữ khi refactor.
- Frontend SPA nội bộ vẫn trỏ vài chỗ sang doctype CŨ `Framework Contract` (m1) — rà nhưng không phá.

## TIẾN ĐỘ TRIỂN KHAI (cập nhật realtime)
- ✅ **Baseline**: 86/86 xanh (chốt trước khi code).
- ✅ **D (rule/công nợ)**: hàm chuẩn `utils/receivables.py` (get_customer_outstanding/credit_limit/min_payment); `_check_credit_limit` hiện min-phải-trả + hết fail-open; ngưỡng Settings (credit_check_enabled/default_credit_limit); BRU-INV-002 chặn tồn lúc gọi (Settings block_order...). Patch v0_11. **+7 test mvl_rule.**
- ✅ **A (master/HĐ)**: valid_from/to reqd + validate thứ tự ngày + backfill patch; nút "Cấp tài khoản Portal" (portal_provision + send_invite email đặt mật khẩu).
- ✅ **C (chuỗi chứng từ)**: nút "Tạo phiếu giao" (sales.make_delivery). Các nút nghiệm thu/hoá đơn/thu tiền đã có sẵn.
- ✅ **B (portal)**: mirror phân quyền SC Acceptance Record (query+has_permission+DocPerm+DOWNLOADABLE); endpoint portal_deliveries/acceptance_records/invoices; portal_confirm_delivery (KH tự xác nhận→biên bản); order_count+total_ordered_qty. **+6 test mvl_portal.**
- ✅ **E (print TT99)**: 6 print format (Hoá đơn/Phiếu giao/Biên bản/HĐ khung/Phiếu thu/Đơn gọi hàng) qua patch v0_11; helper `dong_in_words` (số tiền bằng chữ VN); jinja hook `sc_seller_info`/`sc_dong_in_words`; field MST người bán trong Settings; fixtures + M7 Sales. **+2 test mvl_print.**
- ✅ **F (e2e)**: mvl_e2e_test — chuỗi O2C đầy đủ + quota/stock block. **+2 test.**
- ✅ **Portal HTML**: 2 tab KH (Giao nhận & Nghiệm thu — có nút xác nhận nhận hàng + tải phiếu/biên bản; Hoá đơn & Công nợ) trong www/portal/index.html.
- ✅ **Frontend SPA build**: yarn build OK (nút "Cấp tài khoản Portal", "Tạo phiếu giao").
- 🔟 **Tổng test: 103/103 XANH** (86 baseline + 17 mới). Migrate sạch 5 lần.
- ⏳ **Cần user điền dữ liệu vận hành** (không phải code): SupplyCore Settings → MST/tên/địa chỉ người bán (in TT99), default_credit_limit nếu muốn ngưỡng toàn cục, credit_limit từng KH.

### Kiểm chứng regression mở rộng (theo review)
- `get_available_qty` (dùng chung M4/M5/M6) đổi thành warehouse tùy chọn — **chứng minh non-regression**: monkeypatch về bản CŨ, smoke_m2 lỗi Y HỆT ("cần 60, còn 0") → lỗi do QC-Pending exclusion có sẵn, KHÔNG do thay đổi. Mọi caller cũ truyền warehouse → SQL không đổi. 86/86 sales (dùng nhiều get_available_qty) xanh.
- Smoke tests M1/M2/M5/M11 đỏ do **business rule pre-pivot có sẵn** (comment duyệt ≥10 ký tự, QC-Pending, hạn ngắn cần xác nhận, alert cần recipient) — đỏ TỪ TRƯỚC, không phải baseline sales, không phải regression của đợt này.

### Prerequisite deploy (hạ tầng, không phải code)
- **PDF chứng từ**: `get_print(as_pdf=True)` lỗi do wkhtmltopdf bản qt CHƯA VÁ trên máy (switch --print-media-type/--disable-smart-shrinking). Đường in HTML (`portal_document_download`, KH in từ trình duyệt) render ĐÚNG (tiêu đề+MST+tiền bằng chữ). Go-live cần cài **wkhtmltopdf 0.12.6 patched-qt** để xuất PDF server-side.

## 4. BASELINE TEST — ✅ CHỐT 2026-07-13: 17 file, **86/86 XANH**
> Lệnh chạy đã verify. Mọi vòng sau KHÔNG được để đỏ thêm bất kỳ test nào trong 86 test này.

- **86 test-function TÌM THẤY** trong 17 file sales/portal/AR/fiscal (CHƯA chạy → chưa xác nhận xanh; baseline xanh chốt ở bước 1). Chạy: `bench --site supplycore-miyano.local execute supplycore.tests.<module>.run` (KHÔNG dùng `bench run-tests` — test là script `run()`).
- Cần seed: SC UOM, SC Warehouse (is_group=0), Role "SC Customer Portal".
- 2 runner cũ `uat_e2e_runner`/`uc_coverage` = procurement pre-pivot, **loại khỏi baseline sales**.
- Gap test chính: chuỗi **thu một phần → chặn nợ → thu đủ → gọi tiếp** (cả portal); "min phải trả"; chặn tồn lúc gọi; auto-DN/auto-SI; e2e full O2C nhiều đợt.

## 5. KẾ HOẠCH CODE (sau khi duyệt) — theo workstream
1. **F (gác cổng)** chốt baseline: chạy 17 file, ghi pass/fail thực tế, khoá số xanh.
2. **A** master/HĐ: a1,a6,b9,b10 + nút provision UI (a-portal).
3. **D** rule/công nợ: b1(hàm chuẩn),b2,b3,a2,a3 — nền cho mọi nơi.
4. **C** chuỗi chứng từ: b4,b5,b12,a4 + workflow duyệt.
5. **B** portal: c1,c2,c3,c7,b6,b7.
6. **E** print TT99: c4,c5,c6,a5,c8.
7. **F** viết test flow mới + e2e, chạy vòng lặp ≤12, regression sửa trước.

## 6. QUYẾT ĐỊNH SẢN PHẨM — ĐÃ CHỐT (2026-07-13)
- **Q4 Giao từng phần: KHÔNG** → giữ 1 SO → 1 DN full-qty → 1 SI. Không đụng status-gating chống trùng. (Thiết kế hiện tại giữ nguyên → giảm regression.)
- **Q2 Tự động hoá: BÁN TỰ ĐỘNG (nút bấm)** → duyệt xong nhân viên bấm "Tạo phiếu giao"; nghiệm thu xong bấm "Tạo hoá đơn". API `delivery_create`/`sales_invoice_create` ĐÃ CÓ → chủ yếu thêm nút UI + wire, KHÔNG auto-hook (an toàn tồn/FEFO). **b5 hạ mức: không cần auto-hook, chỉ cần nút UI.**
- **Q1 Chặn tồn: CHẶN SỚM lúc gọi hàng** → thêm kiểm tồn vào `portal_order_place`/SO validate. **b7 nâng lên BLOCKER.**
- **Q3 Ngưỡng nợ: GLOBAL Settings mặc định + override per-KH** → thêm `default_credit_limit` vào SupplyCore Settings, `_check_credit_limit` fallback về Settings khi `SC Customer.credit_limit` trống/0. **a2 xác nhận BLOCKER.**
- **Q5 Công nợ chuẩn: GL-based (TK 131)** làm nguồn chân lý duy nhất — `get_customer_outstanding()` bọc `get_balance(131, party)`; Report `ar_aging` chuyển sang gọi hàm này (cập nhật test theo). (Khuyến nghị của tôi; báo nếu muốn dùng `SI.outstanding_amount`.)

## 7. KẾ HOẠCH CODE CUỐI (chờ duyệt để bắt đầu)
Thứ tự theo dependency; regression là ưu tiên tối cao mỗi vòng.
0. **F** chốt baseline: chạy 17 file test (read-only, auto-rollback) → ghi pass/fail thực, khoá số xanh. (Đề nghị làm NGAY như bước cuối audit.)
1. **D** nền công nợ/rule: `get_customer_outstanding()` (b1), min-phải-trả (b2), vá `credit_limit≤0`+register (b3), Settings `default_credit_limit`+`default_receivable_account` reqd (a2,a3), chặn tồn lúc gọi (b7).
2. **A** master/HĐ: `valid_from/to` reqd + backfill (a1), scheduler hết hạn (b9), trạng thái hết định mức (a6), nút provision KH trên UI.
3. **C** chuỗi chứng từ: nút "Tạo phiếu giao"/"Tạo hoá đơn" (b5), field KH-xác-nhận (a4), chống trùng DB (b12).
4. **B** portal: endpoint + mirror phân quyền SC Acceptance Record (b6,c2), list PGH/biên bản/hoá đơn (c1), endpoint KH xác nhận (b4), tab UI mới (c3), tổng đã gọi/số lần gọi (c7).
5. **E** print TT99: 7 print format (c4), helper tiền-bằng-chữ (c6), MST người bán (a5), fixtures M7 Sales (c5).
6. **F** test flow mới + e2e (chuỗi thu một phần→chặn nợ→thu đủ→gọi tiếp→vượt định mức→hết tồn), vòng lặp ≤12.
