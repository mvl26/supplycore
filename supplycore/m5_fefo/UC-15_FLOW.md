# UC-15 — Quản lý Thông tin Lô hàng (Batch Tracking) — Flow & Implementation

**Module:** M5 FEFO & Hạn dùng
**DocType:** SC Batch (existing)
**Date:** 2026-05-11
**Source:** Phase 1 / UseCase_SupplyCore_v2.0.md UC-15

## Audit hiện trạng

| Spec | Trước | Sau UC-15 |
|---|---|---|
| 1. PR nhập → yêu cầu thông tin lô | ✓ PR `_create_batches_if_needed` | ✓ |
| 2. Số lô NCC, ngày SX, hạn dùng, manufacturer | ✓ tất cả fields | ✓ |
| 3. Batch ID format `[ItemCode]-[YYYYMM]-[Seq]` | Partial: dùng random_string(4) thay Seq | ✓ `generate_batch_id` với Seq tăng dần per (item, year-month) |
| 4. **In nhãn barcode + Hạn dùng** | ✗ | ✓ `get_batch_label_data()` |
| 5. Danh sách lô theo VT | ✓ Frappe List view + filter | ✓ |
| 6. Tra cứu theo supplier_batch_no / Batch ID | Partial: search_fields có; thiếu API rich | ✓ `lookup_batch_by_no()` |
| 3a. **Trùng supplier_batch_no → cảnh báo merge/new** | ✗ | ✓ msgprint warning + return list existing batches |
| 4a. **Hạn dùng <6 tháng → cảnh báo + yêu cầu xác nhận** | Partial: PR-level warn | ✓ `is_short_expiry` flag + `expiry_warning_ack` requires ack at Batch insert |
| Ngoại lệ: Sai format ngày | ✓ Frappe Date field auto-validate | ✓ |

## Actor

- Thủ kho (Storekeeper, Warehouse Officer)

## Pre-condition

- SC Item.has_batch_no = 1

## Luồng chính

| Bước | User | Hệ thống |
|---|---|---|
| 1 | PR nhập kho (UC-09) → row có `expiry_date` + chưa có `batch_no` | `_create_batches_if_needed` tự tạo SC Batch |
| 2 | (Auto) supplier, supplier_batch_no, manufacturer (nếu có) fill từ PR + Item | – |
| 3 | (Auto) `batch_id` = generate_batch_id(item, expiry_date): `[ItemCode]-[YYYYMM]-[Seq]` | Seq từ SQL count batch cùng (item, prefix) + 1 |
| 4 | User mở Batch → click "In nhãn" → call `get_batch_label_data()` | Trả barcode + batch_id + item + expiry + manufacturer cho Print Format |
| 5 | List view `/app/sc-batch` filter theo `item` | – |
| 6 | API `lookup_batch_by_no(text)` search batch_id OR supplier_batch_no | – |

## Luồng thay thế

### 3a — Trùng supplier_batch_no

`validate()`: nếu supplier_batch_no set + có Batch khác cùng (item, supplier_batch_no) đang active:
- `msgprint` orange warning với list existing batch (batch_id, expiry, qc_status)
- User quyết định: dùng batch cũ (cancel insert, set PR.batch_no = existing) HOẶC tạo mới (cố insert; tên `batch_id` unique vẫn force tạo bản ghi mới)

### 4a — Hạn dùng <6 tháng (180 ngày)

`validate()` set `is_short_expiry=1` nếu `expiry_date - today < 180` ngày.

`before_insert()`:
- Nếu `is_short_expiry=1` AND `flags.ignore_short_expiry` không set AND `expiry_warning_ack != 1` → throw `SC-E-BATCH-SHORT-EXPIRY`
- PR auto-create đặt `batch.flags.ignore_short_expiry=1` (vì PR-level đã warn user trước đó)
- Manual create: user phải tick `expiry_warning_ack` (cần role Manager) để insert

## Hậu điều kiện

- SC Batch tạo với `batch_id` format đúng + linked tới PR (qua SLE)
- Nhãn ready để in qua Frappe Print Format
- FEFO picker (UC-16) sort theo batch.expiry_date ASC

## Xử lý ngoại lệ

### Sai format ngày

Frappe Date field auto-validate format `YYYY-MM-DD` (lưu DB) hoặc theo locale `DD/MM/YYYY` (UI). Nhập sai → Frappe throw native, không cần code thêm.

## Field changes

### SC Batch — ADD

| Field | Type | Note |
|---|---|---|
| `is_short_expiry` | Check, read_only | flag tự compute khi expiry < today+180d |
| `expiry_warning_ack` | Check | Manager tick để insert batch hạn ngắn |
| `acknowledged_by` | Link User, read_only | ai tick ack |
| `acknowledged_at` | Datetime, read_only | thời điểm ack |

## Error codes mới

| Code | Trigger | Message |
|---|---|---|
| `SC-E-BATCH-SHORT-EXPIRY` | insert batch is_short_expiry=1 chưa ack | "Hạn dùng còn <6 tháng — Manager xác nhận (tick 'Xác nhận nhập lô hạn ngắn') trước khi tạo" |

## Logic — `sc_batch.py`

### Validate (extend)

```python
def validate(self):
    # existing checks (manuf < exp, blocked reason)
    if self.expiry_date and self.manufacturing_date:
        if getdate(self.expiry_date) <= getdate(self.manufacturing_date):
            frappe.throw(_("Hạn dùng phải sau ngày sản xuất"))
    if self.blocked and not self.block_reason:
        frappe.throw(_("Phải ghi lý do khi block batch"))
    if self.blocked and not self.blocked_by:
        self.blocked_by = frappe.session.user
        self.blocked_at = now()
    if not self.blocked:
        self.blocked_by = None
        self.blocked_at = None

    # UC-15 4a: short expiry flag
    self._compute_short_expiry()
    # UC-15 3a: dup supplier_batch_no warning (non-blocking)
    self._warn_duplicate_supplier_batch_no()

def before_insert(self):
    if self.is_short_expiry:
        if (not self.flags.get("ignore_short_expiry")
                and not self.expiry_warning_ack):
            frappe.throw(_(
                "SC-E-BATCH-SHORT-EXPIRY: Hạn dùng còn <6 tháng — "
                "Manager xác nhận (tick 'Xác nhận nhập lô hạn ngắn') trước khi tạo"
            ))
        if self.expiry_warning_ack:
            self.acknowledged_by = frappe.session.user
            self.acknowledged_at = now()

def _compute_short_expiry(self):
    from frappe.utils import date_diff
    if not self.expiry_date:
        self.is_short_expiry = 0
        return
    days = date_diff(self.expiry_date, today())
    self.is_short_expiry = 1 if days < 180 else 0
    if self.is_short_expiry and self.is_new():
        frappe.msgprint(
            _("⚠ Hạn dùng còn {0} ngày (<6 tháng) — cần Manager xác nhận").format(days),
            indicator="red", alert=True,
        )

def _warn_duplicate_supplier_batch_no(self):
    if not self.supplier_batch_no or not self.item:
        return
    if not self.is_new():
        return
    existing = frappe.db.sql("""
        SELECT name, batch_id, expiry_date, qc_status
        FROM `tabSC Batch`
        WHERE item = %s AND supplier_batch_no = %s
          AND disabled = 0
          AND name != %s
        LIMIT 5
    """, (self.item, self.supplier_batch_no, self.name or ""), as_dict=True)
    if existing:
        names = ", ".join(b.batch_id for b in existing)
        frappe.msgprint(
            _("⚠ Số lô NCC '{0}' đã tồn tại với batch: {1}. "
              "Cân nhắc dùng lô cũ thay vì tạo mới.").format(
                self.supplier_batch_no, names),
            indicator="orange", alert=True,
        )
```

### `get_batch_label_data` whitelisted

```python
@frappe.whitelist()
def get_batch_label_data(self):
    return {
        "batch_id": self.batch_id,
        "barcode": self.batch_id,  # batch_id dùng làm barcode value (no GS1 generator)
        "item": self.item,
        "item_name": self.item_name,
        "manufacturer": self.manufacturer,
        "supplier_batch_no": self.supplier_batch_no,
        "manufacturing_date": str(self.manufacturing_date) if self.manufacturing_date else "",
        "expiry_date": str(self.expiry_date) if self.expiry_date else "",
        "qc_status": self.qc_status,
        "url": f"/app/sc-batch/{self.name}",
    }
```

## API — `m5_fefo/api/batch_helpers.py` (NEW)

```python
@frappe.whitelist()
def generate_batch_id(item: str, expiry_date: str) -> str:
    """UC-15 step 3: format [ItemCode]-[YYYYMM]-[Seq] với Seq tăng dần per
    (item, year-month). Atomic SQL count + 1."""
    from frappe.utils import getdate
    if not item or not expiry_date:
        frappe.throw(_("item và expiry_date required"))
    ym = getdate(expiry_date).strftime("%Y%m")
    prefix = f"{item}-{ym}-"
    cnt = frappe.db.sql("""
        SELECT COUNT(*) FROM `tabSC Batch`
        WHERE batch_id LIKE %s
    """, prefix + "%")[0][0]
    seq = (cnt or 0) + 1
    return f"{prefix}{seq:03d}"


@frappe.whitelist()
def lookup_batch_by_no(text: str, limit: int = 20) -> list:
    """UC-15 step 6: search batch_id OR supplier_batch_no LIKE.
    Cross-item (không filter item)."""
    return frappe.db.sql("""
        SELECT b.name, b.batch_id, b.item, i.item_name,
               b.supplier_batch_no, b.manufacturer,
               b.expiry_date, b.manufacturing_date,
               b.qc_status, b.blocked, b.disabled
        FROM `tabSC Batch` b
        JOIN `tabSC Item` i ON i.name = b.item
        WHERE b.disabled = 0
          AND (b.batch_id LIKE %(t)s OR COALESCE(b.supplier_batch_no, '') LIKE %(t)s)
        ORDER BY b.expiry_date ASC
        LIMIT %(lim)s
    """, {"t": f"%{text}%", "lim": int(limit)}, as_dict=True)
```

## Update SC Purchase Receipt `_create_batches_if_needed`

Replace random_string với generate_batch_id; set `flags.ignore_short_expiry=1`:

```python
def _create_batches_if_needed(self):
    from supplycore.m5_fefo.api.batch_helpers import generate_batch_id
    for r in self.items:
        has_batch = frappe.db.get_value("SC Item", r.item, "has_batch_no")
        if not has_batch:
            continue
        if not r.batch_no and r.expiry_date:
            bid = generate_batch_id(r.item, str(r.expiry_date))
            b = frappe.new_doc("SC Batch")
            b.batch_id = bid
            b.item = r.item
            b.expiry_date = r.expiry_date
            b.manufacturing_date = r.manufacturing_date
            b.supplier = self.supplier
            b.supplier_batch_no = r.supplier_batch_no
            b.flags.ignore_permissions = True
            b.flags.ignore_short_expiry = 1  # PR-level warn đã có
            b.insert()
            r.db_set("batch_no", b.name, update_modified=False)
```

## Migration

- 4 field mới Frappe tự migrate
- Không cần patch

## Test plan — `tests/uc15_test.py`

| Test | Scenario |
|---|---|
| `test_generate_batch_id_format` | Item ABC + expiry 2027-03-15 → "ABC-202703-001" |
| `test_generate_batch_id_sequence` | Tạo 2 batches cùng (item, ym) → seq 001, 002 |
| `test_batch_short_expiry_flag` | Expiry today+90 → is_short_expiry=1 |
| `test_batch_short_expiry_blocks_insert` | Manual insert short expiry không ack → SC-E-BATCH-SHORT-EXPIRY |
| `test_batch_short_expiry_allowed_with_ack` | expiry_warning_ack=1 → insert OK + acknowledged_by populated |
| `test_batch_long_expiry_no_flag` | Expiry today+365 → is_short_expiry=0, insert OK |
| `test_batch_duplicate_supplier_batch_no_warns` | Tạo 2 batch cùng item + supplier_batch_no → msgprint warn nhưng vẫn save (batch_id unique) |
| `test_lookup_batch_by_id` | lookup_batch_by_no(prefix) → trả batches matching |
| `test_lookup_batch_by_supplier_no` | lookup_batch_by_no(supplier_batch_no) → trả batches matching |
| `test_get_batch_label_data` | Method trả dict đủ field cho in nhãn |
| `test_pr_auto_create_batch_uses_seq_format` | PR submit → batch tạo với seq format chuẩn |

## Out-of-scope

- GS1 barcode generator (chỉ dùng batch_id làm barcode value)
- Merge batch UI (chỉ warning, user manual quyết định)
- Auto-link existing batch khi user chọn supplier_batch_no đã có (defer Phase 2)

## File changes

1. `supplycore/m5_fefo/UC-15_FLOW.md` — this file
2. `supplycore/supplycore/doctype/sc_batch/sc_batch.json` — 4 fields mới
3. `supplycore/supplycore/doctype/sc_batch/sc_batch.py` — validate + before_insert + get_batch_label_data
4. `supplycore/m5_fefo/api/batch_helpers.py` — NEW generate_batch_id + lookup_batch_by_no
5. `supplycore/supplycore/doctype/sc_purchase_receipt/sc_purchase_receipt.py` — update `_create_batches_if_needed` dùng generate_batch_id
6. `supplycore/tests/uc15_test.py` — 11 test scenarios
