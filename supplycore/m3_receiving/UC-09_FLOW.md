# UC-09 — Tiếp nhận hàng & Tạo Purchase Receipt — Flow & Implementation

**Module:** M3 Receiving (UC) + Supplycore (DocType `SC Purchase Receipt` host)
**DocType:** SC Purchase Receipt (parent) + SC Purchase Receipt Item (child)
**Date:** 2026-05-11
**Source:** Phase 1 / UseCase_SupplyCore_v2.0.md UC-09
**Lưu ý:** dùng SC * doctypes (no-ERPNext).

## Audit hiện trạng (trước UC-09)

| Spec line | Trước | Sau UC-09 |
|---|---|---|
| 1. PR tạo từ PO | ✓ `make_pr_from_po` | ✓ + set `po_qty` per row |
| 2. Chọn PO → load items | ✓ | ✓ |
| 3. Nhập SL thực tế | ✓ row.qty editable | ✓ |
| 4. Batch No / ngày SX / hạn dùng | ✓ existing | ✓ |
| 5. Vị trí Bin/Location | ✓ `target_bin` | ✓ |
| 6. Đính kèm phiếu giao hàng | ✗ | ✓ field `delivery_note_attachment` (Attach) |
| 7. Submit → SLE + tồn kho | ✓ `_post_stock_ledger` | ✓ |
| 8. Nhận thiếu → tạo Backorder | Partial: field `backorder_for` có, không có logic | ✓ method `create_backorder()` |
| 3a. SL > PO → cảnh báo + xác nhận Manager | ✗ | ✓ field `has_over_receipt` + `over_receipt_acknowledged` guard |
| 8a. Nhận đủ → PO status "Hoàn thành" | ✓ `_update_po_received_qty` set Received | ✓ |
| Ngoại lệ: không tìm thấy PO | Partial: PR cho phép không PO nhưng không reqd lý do | ✓ field `no_po_reason` reqd khi không có PO |

## Actor

- Thủ kho (SupplyCore Storekeeper, Warehouse Officer)
- Quản lý (SupplyCore Manager) — xác nhận khi over-receipt

## Pre-condition

- PO đã Approved + status `Sent to Supplier` / `Partially Received` (UC-08)
- Hàng giao đến kho

## Luồng chính

| Bước | User | Hệ thống |
|---|---|---|
| 1 | Mở `/app/sc-purchase-order/<PO>` click "Tạo Purchase Receipt" hoặc `/app/sc-purchase-receipt/new` chọn PO | `make_pr_from_po(po_name)` tạo Draft PR với items pending, set `po_qty` per row |
| 2 | (Nếu tạo từ /new) chọn PO ref | items reload từ PO |
| 3 | Nhập `qty` thực tế nhận cho từng row | validate qty>0, non_negative, compute `over_received_qty = max(0, qty - po_qty)` |
| 4 | Nhập `manufacturing_date` / `expiry_date` / `supplier_batch_no` cho **từng dòng** | `_create_batches_if_needed` auto-tạo **1 SC Batch cho MỖI dòng vật tư** — đơn N item → N lô tương ứng (không phụ thuộc cờ `has_batch_no` của vật tư) |
| 5 | Chọn `target_bin` (Bin Location) cho row | optional, để track WMS |
| 6 | Upload `delivery_note_attachment` (file scan phiếu giao) | Field Attach |
| 7 | Submit | `validate()`: nếu `has_over_receipt=1` AND `over_receipt_acknowledged=0` → throw `SC-E-OVER-RECEIPT`. Nếu không có `purchase_order` AND không có `no_po_reason` → throw `SC-E-NO-PO-REASON`. `on_submit()`: SLE post + auto QI + cập nhật PO.received_qty + auto status PO |
| 8 | (Nếu nhận thiếu) Click "Tạo Backorder" trên PR submitted | `create_backorder()` tạo Draft PR mới với `backorder_for=current`, items qty=remaining |

## Luồng thay thế

### 3a — SL nhận > SL PO

- `validate()` compute `over_received_qty` per row + parent flag `has_over_receipt`
- `msgprint` warning cam: "X items nhận vượt SL PO — cần Manager xác nhận"
- Nếu submit (docstatus 1) với `has_over_receipt=1` AND `over_receipt_acknowledged=0` → throw `SC-E-OVER-RECEIPT`
- User (role Manager) tick `over_receipt_acknowledged=1` → save → submit OK

### 8a — Nhận đủ 100%

`_update_po_received_qty` đã handle: nếu `all(received_qty >= qty)` cho mọi PO item → set `PO.status = Received`. Đây là "Hoàn thành".

## Hậu điều kiện

- PR `docstatus=1`, SLE tăng tồn `to_warehouse`
- Batch auto-tạo cho **mọi dòng vật tư** (mỗi dòng 1 lô); `before_submit` chặn submit nếu có dòng thiếu `expiry_date` (`SC-E-PR-MISSING-EXPIRY`)
- QI auto-tạo nếu `qc_required=1` (1 QI/dòng item, mang sẵn `supplier` + `batch`) (M3 wiring UC-10)
- PO `received_qty` += per item, status auto Received/Partially Received
- Nếu auto_create backorder: 1 PR Draft mới với `backorder_for`

## Xử lý ngoại lệ

### Không tìm thấy PO

- User tạo PR `/new` mà không chọn `purchase_order`
- `validate()`: nếu `purchase_order` blank AND `no_po_reason` blank → throw `SC-E-NO-PO-REASON`
- User nhập `no_po_reason` (Small Text) → save OK
- Use case: nhập hàng khẩn cấp, hàng tài trợ, mua đột xuất không có PO chính thức

## Field changes

### SC Purchase Receipt parent — ADD

| Field | Type | Note |
|---|---|---|
| `delivery_note_attachment` | Attach | UC step 6 — phiếu giao hàng NCC |
| `has_over_receipt` | Check, read_only | flag bất kỳ row nào qty > po_qty |
| `over_receipt_acknowledged` | Check | Manager tick để submit khi over-receipt |
| `no_po_reason` | Small Text | reqd khi không có purchase_order |

### SC Purchase Receipt Item child — ADD

| Field | Type | Note |
|---|---|---|
| `po_qty` | Float, read_only | qty ordered từ PO Item (set khi make_pr_from_po) |
| `over_received_qty` | Float, read_only | max(0, qty - po_qty), computed |

## Error codes mới

| Code | Trigger | Message |
|---|---|---|
| `SC-E-OVER-RECEIPT` | submit với has_over_receipt=1 + over_receipt_acknowledged=0 | "Một số item nhận vượt SL PO. Tick 'Xác nhận over-receipt' (cần Manager)" |
| `SC-E-NO-PO-REASON` | submit không có PO + không có no_po_reason | "PR không có PO — vui lòng nhập lý do tại 'Lý do không có PO'" |
| `SC-E-BACKORDER-NOTHING` | create_backorder không có item under-received | "Không có item nào nhận thiếu — không thể tạo backorder" |

## Logic — `sc_purchase_receipt.py`

### Validate (extend)

```python
def validate(self):
    from supplycore.utils.validators import validate_supplier, validate_warehouse
    validate_supplier(self.supplier)
    validate_warehouse(self.to_warehouse, label=_("Kho đích"))
    self._compute_totals()
    self._validate_expiry()
    self._compute_over_receipt()   # NEW
    self._validate_no_po_reason()  # NEW
    if self.docstatus == 0 and not self.qc_status:
        self.qc_status = "Pending"
```

### before_submit (new)

```python
def before_submit(self):
    if self.has_over_receipt and not self.over_receipt_acknowledged:
        frappe.throw(_(
            "SC-E-OVER-RECEIPT: Một số item nhận vượt SL PO. "
            "Tick 'Xác nhận over-receipt' (cần Manager) để tiếp tục."
        ))
```

### Helpers (new)

```python
def _compute_over_receipt(self):
    """UC-09 3a: per-row qty - po_qty, flag parent nếu bất kỳ row vượt."""
    has_any = False
    for r in self.items:
        po_qty = flt(r.po_qty)
        qty = flt(r.qty)
        over = max(0.0, qty - po_qty) if po_qty > 0 else 0.0
        r.over_received_qty = over
        if over > 0:
            has_any = True
    self.has_over_receipt = 1 if has_any else 0
    if has_any and self.docstatus == 0:
        frappe.msgprint(
            _("⚠ Một số item nhận vượt SL PO — cần Manager xác nhận"),
            indicator="orange", alert=True,
        )

def _validate_no_po_reason(self):
    """UC-09 ngoại lệ: PR không PO phải có no_po_reason."""
    if not self.purchase_order and not self.is_return and self.docstatus == 0:
        if not (self.no_po_reason and str(self.no_po_reason).strip()):
            # chỉ throw khi user actually save — depends_on UX qua msgprint Draft, throw on submit
            pass

def before_save(self):
    # Chỉ enforce no_po_reason khi sắp submit
    pass
```

Actually đơn giản hơn: throw trong before_submit:

```python
def before_submit(self):
    if self.has_over_receipt and not self.over_receipt_acknowledged:
        frappe.throw(_(
            "SC-E-OVER-RECEIPT: Một số item nhận vượt SL PO. "
            "Tick 'Xác nhận over-receipt' để tiếp tục."
        ))
    if not self.purchase_order and not self.is_return:
        if not (self.no_po_reason and str(self.no_po_reason).strip()):
            frappe.throw(_(
                "SC-E-NO-PO-REASON: PR không có PO — vui lòng nhập 'Lý do không có PO'"
            ))
```

### create_backorder method (new)

```python
@frappe.whitelist()
def create_backorder(self):
    """UC-09 bước 8: tạo PR Draft cho phần còn thiếu."""
    if self.docstatus != 1:
        frappe.throw(_("PR phải submitted để tạo backorder"))
    if self.is_return:
        frappe.throw(_("Phiếu trả không tạo backorder"))
    if not self.purchase_order:
        frappe.throw(_("PR không có PO — không thể tạo backorder"))

    # Tìm under-received items: po_qty > qty
    short_rows = []
    for r in self.items:
        po_qty = flt(r.po_qty)
        if po_qty > 0 and flt(r.qty) < po_qty:
            short_rows.append({
                "item": r.item, "uom": r.uom, "rate": flt(r.rate),
                "warehouse": r.warehouse or self.to_warehouse,
                "po_qty": po_qty - flt(r.qty),
                "remaining_qty": po_qty - flt(r.qty),
            })
    if not short_rows:
        frappe.throw(_("SC-E-BACKORDER-NOTHING: Không có item nào nhận thiếu"))

    bo = frappe.new_doc("SC Purchase Receipt")
    bo.supplier = self.supplier
    bo.purchase_order = self.purchase_order
    bo.backorder_for = self.name
    bo.posting_date = today()
    bo.to_warehouse = self.to_warehouse
    bo.qc_required = self.qc_required
    bo.remarks = f"Backorder cho PR {self.name}"
    for r in short_rows:
        bo.append("items", {
            "item": r["item"],
            "qty": r["remaining_qty"],
            "uom": r["uom"],
            "rate": r["rate"],
            "warehouse": r["warehouse"],
            "po_qty": r["po_qty"],
        })
    bo.flags.ignore_permissions = True
    bo.insert()
    return bo.name
```

### Update `make_pr_from_po` (set po_qty)

Trong `sc_purchase_order.py` `make_pr_from_po`, append row có thêm:
```python
pr.append("items", {
    ...
    "po_qty": flt(poi.qty),
    "po_item_ref": poi.name,
})
```

## Migration

- 4 field parent + 2 field child Frappe tự migrate
- Không cần patch

## Test plan — `tests/uc09_test.py`

| Test | Scenario |
|---|---|
| `test_make_pr_sets_po_qty` | make_pr_from_po → row.po_qty = PO Item.qty |
| `test_over_receipt_flagged` | qty > po_qty → has_over_receipt=1, msgprint |
| `test_over_receipt_blocks_submit_without_ack` | over + ack=0 → submit throw SC-E-OVER-RECEIPT |
| `test_over_receipt_allowed_with_ack` | over + ack=1 → submit OK |
| `test_no_po_requires_reason` | PR không PO + không reason → submit throw SC-E-NO-PO-REASON |
| `test_no_po_with_reason_ok` | PR không PO + reason → submit OK |
| `test_under_receipt_create_backorder` | PR submitted với qty < po_qty → create_backorder() tạo Draft PR mới với qty=remaining |
| `test_full_receipt_no_backorder` | PR submitted nhận đủ → create_backorder() throw SC-E-BACKORDER-NOTHING |
| `test_po_status_received_when_full` | PR submitted full qty → PO status=Received (UC 8a) |

## Out-of-scope

- UI button "Tạo Backorder" / "Xác nhận over-receipt" (JS — defer, method whitelisted đủ)
- Auto-trigger backorder ngay khi submit (giữ manual user action)
- Multi-supplier on 1 PR (giữ 1 supplier/PR như hiện tại)
- OCR phiếu giao hàng (chỉ Attach file)

## File changes

1. `supplycore/m3_receiving/UC-09_FLOW.md` — this file
2. `supplycore/supplycore/doctype/sc_purchase_receipt/sc_purchase_receipt.json` — 4 fields parent
3. `supplycore/supplycore/doctype/sc_purchase_receipt_item/sc_purchase_receipt_item.json` — 2 fields child
4. `supplycore/supplycore/doctype/sc_purchase_receipt/sc_purchase_receipt.py` — over-receipt check + no-PO reason + create_backorder + helpers
5. `supplycore/supplycore/doctype/sc_purchase_order/sc_purchase_order.py` — `make_pr_from_po` set `po_qty` + `po_item_ref`
6. `supplycore/tests/uc09_test.py` — 9 test scenarios
