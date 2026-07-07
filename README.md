# SupplyCore

Hệ thống Quản lý Chuỗi Cung Ứng & Bán hàng Vật Tư/Hóa Chất Y Tế cho nhà phân phối (Công ty Miyano Việt Nam — MVL) — Custom Frappe app **(no ERPNext dependency, v0.2)**.

> 🔄 **Cập nhật 2026-05-07:** Bỏ ERPNext khỏi `required_apps`. Mọi DocType ERP-domain (Item / Warehouse / Supplier / Batch / Stock Entry / PR / PO / MR / QI) được build lại từ scratch với prefix `SC `. Xem [MIGRATION_v0.2.md](MIGRATION_v0.2.md).

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

## Module status

| Module | Phase | Status |
|---|---|---|
| M1 Hợp đồng & NCC | v0.2 | ✅ DocTypes + business logic + README |
| M2 Kế hoạch & Gọi hàng | v0.2 | ✅ Procurement Plan + auto-load + README |
| M3 Tiếp nhận & QC | v0.2 | ✅ Auto-create QI + README |
| M4 WMS & PDA | v0.2 | ✅ Bin + /pda + APIs + README |
| M5 Lô/FEFO | v0.2 | ✅ FEFO + Batch Expiry Alert + README |
| M6 Luân chuyển | — | Planned (folder scaffolded) |
| M7 Bán hàng (Sales) | — | Planned |
| M8 Kế toán | — | Planned (cần tự build GL nếu dùng) |
| M9 Kiểm kê | — | Planned |
| M10 Truy xuất | — | Planned |
| M11 Dashboard | — | Planned |

## Roles SupplyCore

`SupplyCore Manager` · `SupplyCore Storekeeper` · `SupplyCore Accountant` · `SupplyCore Executive` · `SupplyCore Purchaser` · `SupplyCore Auditor` · `SupplyCore User` · `SC Customer Portal` (khách hàng) + legacy: `Warehouse Officer`, `QC Officer`.

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
```

## License

MIT
