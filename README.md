# SupplyCore MVL

Hệ thống **Quản lý Chuỗi Cung Ứng & Bán hàng Vật tư/Hóa chất Y tế** cho nhà
phân phối **Công ty Miyano Việt Nam (MVL)** — Custom Frappe app **(no ERPNext
dependency)**.

**Sản phẩm hoàn chỉnh (nhánh `feat/mvl-distributor`, GĐ1–GĐ4):** phủ trọn
vòng đời phân phối đầu-cuối —

`Hợp đồng khung NCC → Kế hoạch mua → Nhận hàng/QC → Nhập kho (FEFO/bin) →
Bán hàng (HĐ khung/Đơn hàng) → Giao hàng & nghiệm thu → Xuất hoá đơn → Thu
tiền (công nợ + credit limit) → Kế toán/GL → Kiểm kê → Truy xuất nguồn gốc &
thu hồi → Dashboard KPI/công nợ` — cộng thêm **Portal khách hàng** (`/portal`)
để khách tự xem bảng giá theo hợp đồng, đặt hàng, theo dõi đơn (tracker 4 cột
mốc) và tải chứng từ, dữ liệu cô lập chặt theo từng khách (RSK-01).

Giao diện: 1 SPA Vue nội bộ (`/supplycore`) cho toàn bộ 12 module nghiệp vụ +
1 trang web khách riêng (`/portal`, Frappe web page, mobile-first) — tách biệt
hoàn toàn, khách chỉ tiêu thụ qua `api/portal.py` (không chạm API/menu nội bộ).

> 🔄 Không phụ thuộc ERPNext. Mọi DocType ERP-domain (Item / Warehouse /
> Supplier / Batch / Stock Entry / PR / PO / MR / QI...) được build lại từ
> scratch với prefix `SC `. Xem [MIGRATION_v0.2.md](MIGRATION_v0.2.md) (lịch
> sử bỏ ERPNext) và `docs/ba-miyano/PHAN_TICH_HUONG_THIET_KE_MVL.md` (phân
> tích hướng thiết kế + tiến độ GĐ1–GĐ4).

## Cài đặt

```bash
cd ~/frappe-bench
bench get-app supplycore /path/to/supplycore
bench --site <site_name> install-app supplycore
bench --site <site_name> migrate
bench build --app supplycore
sudo supervisorctl restart all   # production
```

## Stack

- Frappe Framework v15+ (Python 3.11+, MariaDB 10.6+, Redis 7+)
- **KHÔNG cần ERPNext** — SupplyCore tự cung cấp Item/Warehouse/Stock Ledger/PO/PR/MR/QI

## Cấu trúc thư mục

| Thư mục | Vai trò |
|---|---|
| `supplycore/supplycore/doctype/sc_*` | 19 SC* DocTypes — masters + transactional |
| `supplycore/supplycore/doctype/supplycore_settings/` | Single doctype cấu hình hệ thống (10 fields) |
| `supplycore/m1_contract/` | M1 — Hợp đồng & NCC (FC + RO). [README](supplycore/m1_contract/README.md) |
| `supplycore/m2_planning/` | M2 — Kế hoạch & Gọi hàng (Procurement Plan). [README](supplycore/m2_planning/README.md) |
| `supplycore/m3_receiving/` | M3 — Tiếp nhận & QC (QC Checklist Template). [README](supplycore/m3_receiving/README.md) |
| `supplycore/m4_wms/` | M4 — WMS & PDA (Bin Location, /pda). [README](supplycore/m4_wms/README.md) |
| `supplycore/m5_fefo/` | M5 — Lô/Hạn dùng/FEFO (FEFO Picker Rule, Batch Expiry Alert). [README](supplycore/m5_fefo/README.md) |
| `supplycore/m6_transfer/` … `m11_dashboard/` | M6–M11 chưa build (planned) |
| `supplycore/api/` | Whitelisted REST endpoint xuyên module (`fefo`, `wms`, `webhook`, `mobile`) |
| `supplycore/overrides/` | (DEPRECATED v0.2) hooks vào ERPNext doc — không còn trigger |
| `supplycore/patches/v0_1/` | Patch v0.1: tạo roles + Custom Field cho ERPNext doctypes (đã chạy, archive) |
| `supplycore/fixtures/` | Roles, Workflows export theo migrate |
| `supplycore/public/js/` | (DEPRECATED v0.2) Client scripts inject vào form ERPNext |
| `supplycore/templates/print_formats/` | Print format Jinja2 |
| `supplycore/www/pda/` | PDA web app `/pda` |
| `supplycore/tests/` | Smoke tests (cần rewrite cho v0.2) |
| `SupplyCore/` | Tài liệu dự án (Phase 1–6) — không build vào Python package |
| `MIGRATION_v0.2.md` | Migration plan v0.1 → v0.2 |

## DocType inventory v0.2

**19 SC* DocTypes (custom built):**
- Masters: `SC UOM`, `SC Item Group`, `SC Item`, `SC Item Barcode`, `SC Department`, `SC Warehouse`, `SC Supplier`, `SC Batch`
- Ledger: `SC Stock Ledger Entry` (immutable)
- Transactional: `SC Stock Entry`+Item, `SC Material Request`+Item, `SC Purchase Order`+Item, `SC Purchase Receipt`+Item, `SC Quality Inspection`+Reading

**12 SupplyCore-owned DocTypes (M1-M5):** Framework Contract, Release Order, FC Item, RO Item, Procurement Plan, Procurement Plan Item, QC Checklist Template, QC Checklist Item, Bin Location, FEFO Picker Rule, Batch Expiry Alert, SupplyCore Settings.

## Module status (GĐ1–GĐ4, nhánh `feat/mvl-distributor`)

| Module | Status |
|---|---|
| M1 Hợp đồng & NCC (Framework Contract) | ✅ |
| M2 Kế hoạch & Gọi hàng (Procurement Plan, PO suggest từ MR) | ✅ |
| M3 Tiếp nhận & QC (Purchase Receipt, auto-create QI) | ✅ |
| M4 WMS & PDA (Bin Location, putaway, /pda, quick-stock) | ✅ |
| M5 Lô/Hạn dùng/FEFO (FEFO Picker, Batch Expiry Alert) | ✅ |
| M6 Luân chuyển kho (Transfer Request, Stock Entry) | ✅ |
| M7 Bán hàng (SC Customer, Sales Framework Contract, Sales Order, Delivery Note, Acceptance Record, Sales Invoice, Sales Receipt) | ✅ — thay thế hoàn toàn M7 Cấp phát/BHYT/Patient (bản bệnh viện cũ) |
| M8 Kế toán (GL Entry, Purchase/Sales Invoice, Payment/Receipt, AP+AR aging) | ✅ |
| M9 Kiểm kê (Inventory Count Sheet, Stock Reconciliation) | ✅ |
| M10 Truy xuất nguồn gốc (batch trace, thu hồi/Recall, audit trail UC-31) | ✅ |
| M11 Dashboard (KPI điều hành, công nợ phải thu, cảnh báo) | ✅ |
| M12 Portal khách hàng (`/portal` + `api/portal.py`, cô lập RSK-01) | ✅ |

## Roles

Nội bộ: `SupplyCore Manager` · `SupplyCore Storekeeper` · `SupplyCore Accountant` ·
`SupplyCore Executive` · `SupplyCore Purchaser` · `SupplyCore Auditor` ·
`SupplyCore User` · `Warehouse Officer` · `QC Officer`.

Khách hàng: `SC Customer Portal` — chỉ tiêu thụ 7 API `api/portal.py`
(`portal_me/contracts/catalog/order_place/order_track/order_history/
document_download`), dữ liệu tự lọc theo khách hàng đăng nhập
(`SC Customer.portal_user`), không thấy menu/API/dữ liệu nội bộ (nhà cung cấp,
giá mua, kho, GL, KPI, audit — được sweep/gate ở `supplycore/utils/
permissions.py::block_portal` cho mọi API nội bộ thiếu permission check
riêng).

## Vận hành nhanh

```
/app/sc-supplier              → master NCC
/app/sc-item                  → master vật tư
/app/sc-warehouse             → master kho 3 tầng
/app/sc-batch                 → list lô hàng
/app/framework-contract/new   → tạo HĐK (M1)
/app/procurement-plan/new     → kế hoạch mua sắm (M2)
/app/sc-purchase-receipt/new  → tiếp nhận hàng + auto QC (M3)
/app/sc-stock-entry/new       → giao dịch kho (M4)
/app/batch-expiry-alert?resolved=0  → cảnh báo hết hạn (M5)
/pda                          → mobile PDA scan
/supplycore                   → SPA nội bộ (12 module, DocView generic)
/portal                       → trang khách (SC Customer Portal): catalog, đặt hàng, theo dõi đơn
```

## License

MIT
