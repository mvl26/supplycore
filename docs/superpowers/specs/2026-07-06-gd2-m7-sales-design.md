# Spec GĐ2 — M7 Bán hàng & Bàn giao (Order-to-Cash) + Sổ cái phải thu

- **Ngày:** 2026-07-06 · **Nhánh:** `feat/mvl-distributor` (tiếp sau GĐ1)
- **Nguồn thiết kế:** BA SupplyCore MVL v2 (ERD #08, Workflow #16, Business Rules #04, API #11, SRS #05) + `docs/ba-miyano/PHAN_TICH_HUONG_THIET_KE_MVL.md`.
- **Phạm vi GĐ2:** dựng **chuỗi bán hàng backend** cho công ty phân phối. KHÔNG làm Portal khách (GĐ3), KHÔNG làm UI đầy đủ (chỉ Desk mặc định + API; UI Vue để GĐ3/GĐ4).

## 1. Mục tiêu (end-state kiểm chứng được)
1. 7 DocType chiều bán tạo mới, migrate sạch, xuất hiện trong Desk.
2. Chuỗi Order-to-Cash chạy được end-to-end qua API/test: Customer → Sales Framework Contract → Sales Order (duyệt) → Delivery Note (xuất kho, ghi **SC Stock Ledger Entry** âm) → Acceptance Record (nghiệm thu) → Sales Invoice (ghi **SC GL Entry** phải thu) → Sales Receipt (thu tiền, tất toán).
3. Các Business Rule bán hàng được **chặn** đúng (test đỏ trước, xanh sau — TDD).
4. Không hồi quy GĐ1: `bench migrate/build`, `frappe.ping`, và test M1–M6/M8–M11 hiện có vẫn pass.

## 2. DocType mới (prefix `SC `, theo ERD #08)

### 2.1 SC Customer (master)
- `customer_code` (autoname `field:customer_code` hoặc series `SC-CUS-{#####}`), `customer_name`, `tax_code` (Data, **unique** — BRU-SUP-style), `billing_address`, `shipping_address`, `credit_limit` (Currency VND, default 0 = không giới hạn), `payment_terms`, `status` (Select: Hoạt động/Tạm ngưng, default Hoạt động), `portal_user` (Link User, **optional ở GĐ2** — GĐ3/M12 sẽ ràng buộc bắt buộc + 1-1).
- BRU-CUS-002 (1 user ↔ 1 customer) enforce ở GĐ3. Ở GĐ2 chỉ validate unique nếu portal_user set.
- Không submittable (master).

### 2.2 SC Sales Framework Contract (+ child SFC Item) — submittable
- `contract_no` (SC-SFC-{YYYY}-{#####}), `customer` (Link SC Customer, reqd), `valid_from`, `valid_to`, `total_value` (Currency), `status` (Nháp/Chờ duyệt/Hiệu lực/Hết hạn/Thanh lý — WF tương tự Framework Contract mua), `approved_by`.
- **SFC Item**: `item` (Link SC Item), `uom`, `contract_qty` (Float), `unit_price` (Currency, **giá cố định**), `remaining_qty` (Float, read_only — giảm khi SO).
- BRU-SFC-001: SO chỉ đặt item thuộc SFC còn hiệu lực. BRU-SFC-002: đơn giá lấy từ SFC, không sửa ở SO.

### 2.3 SC Sales Order (+ child SO Item) — submittable, workflow WF-09
- `order_no` (SC-SO-{YYYY}-{#####}), `customer` (reqd), `framework_contract` (Link SC Sales Framework Contract, reqd), `order_date`, `status` (Chờ duyệt→Đã duyệt→Đang xử lý→Đã bàn giao→Hoàn tất / Từ chối), `approval_by`, `total_amount` (read_only, tính từ items).
- **SO Item**: `item`, `uom`, `qty`, `unit_price` (fetch từ SFC Item, read_only — BRU-SFC-002), `amount` (read_only = qty×unit_price).
- Validate: BRU-SO-001 (Σqty theo item ≤ remaining_qty của SFC Item trong kỳ), BRU-SFC-001 (item ∈ SFC còn hiệu lực), BRU-SO-002 (phải duyệt trước khi xuất kho — Delivery chỉ tạo được từ SO đã duyệt), BRU-AR-001 (khi duyệt, nếu công nợ phải thu của khách + giá trị đơn > credit_limit → cảnh báo/chặn chờ duyệt cấp cao).

### 2.4 SC Delivery Note (+ child DN Item) — submittable, workflow WF-10
- `dn_no` (SC-DN-{YYYY}-{#####}), `sales_order` (Link, reqd), `customer` (fetch), `from_warehouse` (Link SC Warehouse), `delivery_date`, `acceptance_ref` (Link SC Acceptance Record, read_only), `status` (Nháp→Đã giao→Đã nghiệm thu→Đã xuất HĐ).
- **DN Item**: `item`, `uom`, `qty`, `batch` (Link SC Batch — **gợi ý FEFO**, có thể ép), `warehouse`.
- on_submit: ghi **SC Stock Ledger Entry** (qty_change ÂM tại from_warehouse/batch/bin) — tái dùng hàm ghi SLE hiện có (xem overrides/stock_entry hoặc sc_stock_ledger_entry). Ép FEFO qua m5_fefo picker; chặn xuất lô hết hạn (BRU-EXP-001) & tồn âm (BRU-INV-001).

### 2.5 SC Acceptance Record — submittable
- `acceptance_no` (SC-ACC-{YYYY}-{#####}), `delivery_note` (Link, reqd), `customer` (fetch), `acceptance_date`, `accepted_by` (tên người nhận phía khách), `note`, `status` (Nháp/Đã nghiệm thu).
- on_submit: set Delivery Note.status = "Đã nghiệm thu" + acceptance_ref. BRU-DEL-001: chỉ sau bản ghi này mới cho xuất Sales Invoice.

### 2.6 SC Sales Invoice (+ child SI Item) — submittable, workflow WF-11
- `invoice_no` (SC-SI-{YYYY}-{#####}), `customer` (reqd), `delivery_note` (Link, reqd — phải đã nghiệm thu), `invoice_date`, `total_amount`, `tax_amount`, `grand_total`, `outstanding_amount` (read_only), `status` (Nháp→Đã phát hành→Đã thu một phần→Đã thu đủ→Hủy).
- **SI Item**: `item`, `qty`, `unit_price`, `amount` — **khớp DN đã nghiệm thu** (BRU-INVC-001).
- on_submit: BRU-DEL-001 (DN.status == "Đã nghiệm thu"); ghi **SC GL Entry**: Nợ TK Phải thu khách hàng / Có TK Doanh thu (+ thuế). outstanding = grand_total. Set DN.status="Đã xuất HĐ". BRU-PAY-001: không ghi vào kỳ đã khóa (fiscal_lock_date trong Settings).

### 2.7 SC Sales Receipt — submittable
- `receipt_no` (SC-RCPT-{YYYY}-{#####}), `customer` (reqd), `sales_invoice` (Link, reqd), `receipt_date`, `amount` (Currency, ≤ outstanding), `mode` (Select: Tiền mặt/Chuyển khoản).
- on_submit: ghi **SC GL Entry** (Nợ Tiền/Có Phải thu); giảm SI.outstanding_amount; cập nhật SI.status (Đã thu một phần/đủ). BRU-PAY-001 kỳ khóa.

## 3. Workflow / State (theo #16)
Dùng pattern hiện có của app: field `status` (Select) + logic controller (KHÔNG bắt buộc Frappe Workflow engine — nhất quán GĐ1). WF-09 (SO), WF-10 (DN), WF-11 (SI) hiện thực bằng transitions trong controller + kiểm quyền role.
- Quyền: `SupplyCore Purchaser` (Thương Mại) duyệt SO; `SupplyCore Storekeeper` lập DN/xuất kho; `SupplyCore Accountant` lập SI + thu tiền. (Ma trận #13.)

## 4. Sổ sách (tái dùng hạ tầng GĐ1)
- **SC Stock Ledger Entry**: DN.on_submit ghi dòng âm; DN.on_cancel đảo. Dùng đúng cơ chế ledger hiện có (immutable, voucher Dynamic Link).
- **SC GL Entry**: SI ghi phải thu, Receipt ghi thu tiền. Cần **SC GL Account** cho: Phải thu khách hàng (1131), Doanh thu bán VT (5111), Thuế GTGT đầu ra (33311), Tiền mặt/NH (111/112). Seed các account này nếu chưa có.

## 5. API (whitelisted, nhóm scm.* — theo #11)
`scm.customer.upsert`, `scm.sales_framework.create`, `scm.sales_order.approve`, `scm.delivery.create`, `scm.delivery.accept`, `scm.sales_invoice.create`, `scm.receipt.collect`. (Portal API M12 → GĐ3.) Mỗi API: kiểm quyền → kiểm business rule → ghi sổ/đổi trạng thái → audit.

## 6. Business Rules phải test (TDD — đỏ trước)
BRU-CUS-002 (portal_user unique nếu set), BRU-SFC-001 (item ∉ SFC → chặn), BRU-SFC-002 (sửa giá SO → chặn/ghi đè bằng giá SFC), BRU-SO-001 (vượt remaining_qty → chặn), BRU-SO-002 (DN từ SO chưa duyệt → chặn), BRU-DEL-001 (SI khi DN chưa nghiệm thu → chặn), BRU-INVC-001 (SI lệch DN → chặn), BRU-AR-001 (vượt credit_limit → cảnh báo/chờ duyệt), BRU-INV-001 (DN làm tồn âm → chặn), BRU-EXP-001 (DN xuất lô hết hạn → chặn), BRU-PAY-001 (ghi kỳ khóa → chặn).

## 7. Module & đăng ký
- Thêm module **"M7 Sales"** vào `modules.txt` (thay chỗ "M7 Dispensing" đã bỏ). Folder `supplycore/m7_sales/`.
- Cập nhật `api/users.py` role-guide: M7 = "Bán hàng & Bàn giao" (thay "Cấp phát BN").
- Fixtures/permissions: gán role theo ma trận #13.

## 8. Ngoài phạm vi GĐ2 (để phase sau)
- Portal khách + cô lập dữ liệu + 4 cột mốc + 7 API portal (GĐ3/M12).
- UI Vue cho màn Sales (SCR-22..26) — GĐ3/GĐ4.
- Rebrand seed data/warehouse-map sang Miyano (GĐ4) — nhưng GĐ2 seed customer/SFC demo tối thiểu để test.
- Dashboard công nợ phải thu nâng cao (GĐ4).

## 9. Định nghĩa Done
7 DocType + controllers + ledger/GL + 7 API + workflow + test TDD phủ 11 BRU ở mục 6, chuỗi O2C end-to-end pass, migrate/build/ping sạch, không hồi quy GĐ1, commit trên `feat/mvl-distributor`.
