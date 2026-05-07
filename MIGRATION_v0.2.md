# SupplyCore — Migration plan v0.1 → v0.2 (No-ERPNext)

**Ngày:** 2026-05-07. **Quyết định:** Bỏ ERPNext, chỉ dùng Frappe Framework. Tất cả ERP-domain DocType build lại với prefix `SC `.

## Bảng đối chiếu DocType

| ERPNext (cũ — không dùng nữa) | SC custom (mới) | Module |
|---|---|---|
| `Item` | **`SC Item`** | Supplycore |
| `Item Group` | **`SC Item Group`** (NestedSet) | Supplycore |
| `Item Barcode` | **`SC Item Barcode`** (child) | Supplycore |
| `UOM` | **`SC UOM`** | Supplycore |
| `Warehouse` | **`SC Warehouse`** (NestedSet 3-tier) | Supplycore |
| `Supplier` | **`SC Supplier`** | Supplycore |
| `Department` | **`SC Department`** | Supplycore |
| `Batch` | **`SC Batch`** | Supplycore |
| `Stock Ledger Entry` + `Bin` + `Serial and Batch Bundle` | **`SC Stock Ledger Entry`** | Supplycore |
| `Stock Entry` + `Stock Entry Detail` | **`SC Stock Entry`** + `SC Stock Entry Item` | Supplycore |
| `Material Request` + items | **`SC Material Request`** + `SC Material Request Item` | Supplycore |
| `Purchase Order` + items | **`SC Purchase Order`** + `SC Purchase Order Item` | Supplycore |
| `Purchase Receipt` + items | **`SC Purchase Receipt`** + `SC Purchase Receipt Item` | Supplycore |
| `Quality Inspection` + readings | **`SC Quality Inspection`** + `SC QI Reading` | Supplycore |

**Frappe-native (giữ nguyên dùng):** `User`, `Role`, `Has Role`, `Workflow*`, `Custom Field`, `Property Setter`, `Print Format`, `Email Template`, `Webhook`, `Notification`, `Currency`, `Country`, `Document Naming Rule`, `ToDo`, `Comment`, `Version`, `Audit Log`.

**SupplyCore-owned (custom built sẵn từ M1-M5, không thay đổi):** `Framework Contract`, `Release Order`, `FC Item`, `RO Item`, `Procurement Plan`, `Procurement Plan Item`, `QC Checklist Template`, `QC Checklist Item`, `Bin Location`, `FEFO Picker Rule`, `Batch Expiry Alert`, `SupplyCore Settings`.

## Hệ quả

1. `hooks.py.required_apps = ["frappe/frappe"]` — bỏ erpnext
2. Custom Field patches (M1-M5 v0_1) thêm vào ERPNext doctypes (Supplier/PO/MR/PR/QI/Item/Batch/SE Detail) đã chạy & lưu trong tabPatch Log → KHÔNG re-run, KHÔNG bị xoá. Chúng "đứng yên" trên ERPNext doctypes nếu ERPNext còn cài, vô hại.
3. Stock Ledger logic do controller `SC Stock Entry`, `SC Purchase Receipt` viết — không cần ERPNext built-in
4. Live data hiện tại dùng ERPNext Item/Supplier/etc → **cần migration script** nếu muốn giữ dữ liệu cũ. Hoặc reset site mới.

## Thay đổi field name khi migrate (link options)

| Trước | Sau |
|---|---|
| `Framework Contract.supplier` → "Supplier" | "SC Supplier" |
| `Framework Contract.payment_terms` → Link "Payment Terms Template" | Data string |
| `FC Item.item_code` → "Item" | "SC Item" |
| `FC Item.uom` → "UOM" | "SC UOM" |
| `RO Item.item_code` → "Item" | "SC Item" |
| `Release Order.supplier` → "Supplier" | "SC Supplier" |
| `Release Order.purchase_order` → "Purchase Order" | "SC Purchase Order" |
| `Procurement Plan.warehouse` → "Warehouse" | "SC Warehouse" |
| `Procurement Plan.material_request` → "Material Request" | "SC Material Request" |
| `Procurement Plan Item.item_code` → "Item" | "SC Item" |
| `Procurement Plan Item.preferred_supplier` → "Supplier" | "SC Supplier" |
| `QC Checklist Template.item_group` → "Item Group" | "SC Item Group" |
| `Bin Location.warehouse` → "Warehouse" | "SC Warehouse" |
| `Batch Expiry Alert.{batch_no, item_code, warehouse}` | "SC Batch", "SC Item", "SC Warehouse" |
| `FEFO Picker Rule.{warehouse, item_group}` | "SC Warehouse", "SC Item Group" |

## Master data migration (cho site đang có ERPNext data)

```python
# scripts/migrate_to_sc.py — placeholder, chạy thủ công khi cần
import frappe

# 1. Copy Item → SC Item
for it in frappe.get_all("Item", fields=["name", "item_name", "item_group", "stock_uom",
                                          "is_stock_item", "has_batch_no", "disabled"]):
    if not frappe.db.exists("SC Item", it.name):
        sc = frappe.new_doc("SC Item")
        sc.item_code = it.name
        sc.item_name = it.item_name
        sc.uom = it.stock_uom  # cần có SC UOM tương ứng
        sc.has_batch_no = it.has_batch_no
        sc.is_stock_item = it.is_stock_item
        sc.disabled = it.disabled
        sc.flags.ignore_permissions = True
        sc.insert()

# Tương tự cho Supplier, Warehouse, Batch...
# Stock Ledger Entry KHÔNG copy (immutable, sẽ replay từ SC PR/SE submit lại)
```

**Khuyến nghị:** với site test/staging, nên reset site mới + import master data bằng Data Import. Không thử migrate live data trừ khi cần thiết.

## Smoke test status

Smoke test M1-M5 cũ DEPRECATED — viết tham chiếu tabSupplier, tabPurchase Order, tabBatch ERPNext. Cần viết lại với SC* DocTypes.

## File map

```
supplycore/
├── MIGRATION_v0.2.md                          ← file này
├── supplycore/
│   ├── doctype/
│   │   ├── sc_uom/, sc_item_group/, sc_department/
│   │   ├── sc_supplier/, sc_warehouse/
│   │   ├── sc_item/, sc_item_barcode/
│   │   ├── sc_batch/, sc_stock_ledger_entry/
│   │   ├── sc_stock_entry/, sc_stock_entry_item/
│   │   ├── sc_material_request/, sc_material_request_item/
│   │   ├── sc_purchase_order/, sc_purchase_order_item/
│   │   ├── sc_purchase_receipt/, sc_purchase_receipt_item/
│   │   ├── sc_quality_inspection/, sc_qi_reading/
│   │   ├── supplycore_settings/, bhyt_config/, alert_rule/, audit_log/
│   ├── hooks.py                               ← required_apps = ["frappe/frappe"] (bỏ erpnext)
│   └── ...
├── m1_contract/                               ← Framework Contract + Release Order (refactored)
│   ├── README.md
│   └── doctype/...
├── m2_planning/                               ← Procurement Plan (refactored)
│   ├── README.md
│   └── doctype/...
├── m3_receiving/                              ← QC Checklist Template (refactored)
│   ├── README.md
│   └── doctype/...
├── m4_wms/                                    ← Bin Location (refactored)
│   ├── README.md
│   └── doctype/...
└── m5_fefo/                                   ← FEFO Picker Rule + Batch Expiry Alert (refactored)
    ├── README.md
    └── doctype/...
```

## TODO sau v0.2

1. ⏳ Smoke tests rewrite cho SC* (smoke_m1.py..smoke_m5.py)
2. ⏳ Override files (overrides/purchase_receipt.py, /qi.py, etc) → DEPRECATED, cleanup
3. ⏳ Custom field patches (v0_1) → archive nếu uninstall ERPNext
4. ⏳ JS client scripts cũ (public/js/purchase_receipt.js, ...) → port sang doctype folder của SC*
5. ⏳ M6-M11 build với SC* doctypes ngay từ đầu
6. ⏳ Migration script master data từ ERPNext nếu user muốn giữ data
7. ⏳ Print formats Jinja2 cho SC PR / SC PO / SC QI
