# UC-20 — Tạo Phiếu Yêu cầu Cấp phát — Flow & Implementation

**Module:** M7 Dispensing
**DocType:** SC Dispensing Request + SC DR Item (existing) + SC Department (extend)
**Date:** 2026-05-11
**Source:** Phase 1 / UseCase_SupplyCore_v2.0.md UC-20

## Audit hiện trạng

| Spec | Trước | Sau UC-20 |
|---|---|---|
| 1. Mở "Yêu cầu cấp phát" | ✓ /app/sc-dispensing-request | ✓ |
| 2. **Auto khoa phòng từ user** | Partial: department reqd, không auto | Add note + auto-fill requested_by=session.user |
| 3. Items + qty | ✓ | ✓ |
| 3a. **Vật tư hết hàng → suggest thay thế** | ✗ | ✓ `check_stock_availability()` API |
| 4. **Gắn bệnh nhân (BHYT)** | ✓ patient Link, depends_on Patient-Specific | ✓ |
| 4a. Không gắn → cấp khoa | ✓ purpose Routine/Urgent | ✓ |
| 5. **Lý do + ngày cần** | Partial: required_by có, reason ✗ | ✓ thêm `reason` |
| 6. Submit gửi Thủ kho | ✓ status workflow | ✓ |
| 7. Theo dõi status | ✓ Draft/Pending/Approved/Issued/Dispensed/Cancelled | ✓ |
| **Ngoại lệ: Vượt hạn mức tháng → cần phê duyệt đặc biệt** | ✗ | ✓ `monthly_dispensing_quota` trên Department + quota check + ack flag |

## Actor

- Nhân viên khoa phòng (Ward Staff)
- Pharmacy Officer
- Thủ kho (Storekeeper) — process

## Pre-condition

- User login + có department
- SC Item có tồn kho

## Luồng chính

| Bước | Action |
|---|---|
| 1 | User mở `/app/sc-dispensing-request/new` |
| 2 | Chọn `department` (manual hoặc UI tự fetch user profile, sau này Phase 2) |
| 3 | Thêm items: `item`, `requested_qty`, `uom`. Optional check `check_stock_availability(item, qty, from_warehouse)` để biết thay thế |
| 4 | (Patient-Specific) chọn `patient` (link SC Patient) |
| 5 | Nhập `reason` + `required_by` |
| 6 | Submit → validate quota → `on_submit` set status=Approved (Thủ kho nhận thông báo) |
| 7 | Thủ kho `make_stock_entry()` → status=Issued; `make_patient_dispensing()` → status=Dispensed |

## Luồng thay thế

### 3a — Vật tư hết hàng

`check_stock_availability(item, qty, from_warehouse)`:
- Compute current_qty từ SLE
- If < qty: query SC Item cùng item_group với stock > 0 tại warehouse → suggest top 5
- Return: `{in_stock: bool, available: float, shortfall: float, alternatives: [{item, item_name, available_qty}, ...]}`

UI gọi trước save để hiển thị warning + danh sách alternatives. KHÔNG block save — chỉ inform; FEFO/picking sau xử lý insufficient at SE level.

### 4a — Không gắn bệnh nhân

Purpose=Routine/Urgent → patient hidden. Cấp cho khoa, không track per BN.

## Xử lý ngoại lệ

### Vượt hạn mức tháng

- SC Department có field `monthly_dispensing_quota` (Currency, default 0 = không limit)
- DR validate: tính `total_value` của tất cả DR submitted (status≠Cancelled) cùng department, cùng month
- If `total_consumed + this_dr_value > quota > 0` AND `quota_override_acknowledged=0` → throw `SC-E-DR-QUOTA-EXCEEDED`
- Manager tick `quota_override_acknowledged=1` → submit qua (phê duyệt đặc biệt)

## Field changes

### SC Department — ADD

| Field | Type | Note |
|---|---|---|
| `monthly_dispensing_quota` | Currency (VND), default 0 | 0 = không giới hạn |

### SC Dispensing Request — ADD

| Field | Type | Note |
|---|---|---|
| `reason` | Small Text | Lý do yêu cầu (UC step 5) |
| `quota_override_acknowledged` | Check, default 0 | Manager tick khi vượt quota |
| `total_estimated_value` | Currency (VND), read_only | computed từ items × _last_purchase_rate |

## Error codes mới

| Code | Trigger | Message |
|---|---|---|
| `SC-E-DR-QUOTA-EXCEEDED` | total_value tháng + this DR > quota; ack=0 | "Khoa {x} vượt hạn mức cấp phát tháng (đã dùng {y}, quota {z}). Cần Manager xác nhận." |

## Logic — `sc_dispensing_request.py`

### Validate extend

```python
def validate(self):
    if self.purpose == "Patient-Specific" and not self.patient:
        frappe.throw(_("Mục đích Patient-Specific phải gắn bệnh nhân"))
    for r in self.items:
        if not r.approved_qty:
            r.approved_qty = r.requested_qty
    self.total_qty = sum(flt(r.requested_qty) for r in self.items)
    self._compute_estimated_value()
    if not self.requested_by and frappe.session.user not in (None, "", "Guest"):
        self.requested_by = frappe.session.user
    if self.docstatus == 0:
        self.status = "Draft"

def before_submit(self):
    self._validate_quota()

def _compute_estimated_value(self):
    total = 0
    for r in self.items:
        rate = _last_purchase_rate(r.item)
        total += flt(r.approved_qty or r.requested_qty) * rate
    self.total_estimated_value = total

def _validate_quota(self):
    if not self.department:
        return
    quota = flt(frappe.db.get_value("SC Department", self.department,
                                      "monthly_dispensing_quota"))
    if quota <= 0:
        return  # không kiểm soát
    if self.quota_override_acknowledged:
        return  # Manager đã xác nhận
    # Compute total this month except cancelled, except this DR
    from frappe.utils import get_first_day, get_last_day, getdate
    month_start = get_first_day(self.request_date or today())
    month_end = get_last_day(self.request_date or today())
    consumed = flt(frappe.db.sql("""
        SELECT COALESCE(SUM(total_estimated_value), 0)
        FROM `tabSC Dispensing Request`
        WHERE department = %s
          AND request_date BETWEEN %s AND %s
          AND docstatus = 1
          AND status != 'Cancelled'
          AND name != %s
    """, (self.department, month_start, month_end, self.name or ""))[0][0])
    projected = consumed + flt(self.total_estimated_value)
    if projected > quota:
        frappe.throw(_(
            "SC-E-DR-QUOTA-EXCEEDED: Khoa {0} vượt hạn mức cấp phát tháng "
            "(đã dùng {1}, DR này {2}, quota {3}). Cần Manager tick "
            "'Xác nhận vượt hạn mức' để submit."
        ).format(
            self.department,
            frappe.format(consumed, {"fieldtype": "Currency"}),
            frappe.format(self.total_estimated_value, {"fieldtype": "Currency"}),
            frappe.format(quota, {"fieldtype": "Currency"}),
        ))
```

## API — `m7_dispensing/api/dispense_helpers.py` (NEW)

```python
@frappe.whitelist()
def check_stock_availability(item: str, qty: float, warehouse: str) -> dict:
    """UC-20 3a: check stock + suggest alternatives same item_group."""
    qty = flt(qty)
    available = flt(frappe.db.sql("""
        SELECT COALESCE(SUM(qty_change), 0)
        FROM `tabSC Stock Ledger Entry`
        WHERE item = %s AND warehouse = %s AND is_cancelled = 0
    """, (item, warehouse))[0][0])

    in_stock = available >= qty
    alternatives = []
    if not in_stock:
        item_group = frappe.db.get_value("SC Item", item, "item_group")
        if item_group:
            alternatives = frappe.db.sql("""
                SELECT i.name AS item, i.item_name,
                       COALESCE(SUM(sle.qty_change), 0) AS available_qty
                FROM `tabSC Item` i
                LEFT JOIN `tabSC Stock Ledger Entry` sle
                    ON sle.item = i.name AND sle.warehouse = %(wh)s AND sle.is_cancelled = 0
                WHERE i.disabled = 0
                  AND i.item_group = %(ig)s
                  AND i.name != %(item)s
                GROUP BY i.name
                HAVING available_qty > 0
                ORDER BY available_qty DESC LIMIT 5
            """, {"wh": warehouse, "ig": item_group, "item": item}, as_dict=True)

    return {
        "item": item,
        "warehouse": warehouse,
        "requested_qty": qty,
        "available_qty": available,
        "in_stock": in_stock,
        "shortfall": max(0.0, qty - available),
        "alternatives": alternatives,
    }
```

## Migration

- 1 field SC Department + 3 fields SC DR Frappe tự migrate
- Không cần patch

## Test plan — `tests/uc20_test.py`

| Test | Scenario |
|---|---|
| `test_dr_create_basic` | Tạo DR với department + items → save OK |
| `test_dr_patient_specific_requires_patient` | purpose=Patient-Specific, no patient → throw |
| `test_dr_auto_fill_requested_by` | Insert DR → requested_by = session.user |
| `test_dr_compute_estimated_value` | items có rate → total_estimated_value tính đúng |
| `test_check_stock_availability_in_stock` | item có 100 qty, request 50 → in_stock=True |
| `test_check_stock_availability_shortfall` | item có 30 qty, request 50 → shortfall=20 + alternatives |
| `test_check_stock_availability_alternatives_same_group` | item hết, item khác cùng group có stock → suggest |
| `test_dr_quota_no_limit_skipped` | dept.quota=0 → submit OK dù total cao |
| `test_dr_quota_exceeded_blocks` | quota=1tr, total=2tr, ack=0 → SC-E-DR-QUOTA-EXCEEDED |
| `test_dr_quota_exceeded_with_ack_passes` | quota=1tr, total=2tr, ack=1 → submit OK |
| `test_dr_make_stock_entry_after_submit` | Approved DR → make_stock_entry → SE Material Issue Draft |

## Out-of-scope

- Auto-fill department từ User profile (Phase 2 — cần User custom field)
- In-app notification cho Thủ kho (defer; chỉ email/status change)
- Multi-month quota tracking (chỉ current month)

## File changes

1. `supplycore/m7_dispensing/UC-20_FLOW.md` — this file
2. `supplycore/supplycore/doctype/sc_department/sc_department.json` — `monthly_dispensing_quota`
3. `supplycore/m7_dispensing/doctype/sc_dispensing_request/sc_dispensing_request.json` — 3 fields
4. `supplycore/m7_dispensing/doctype/sc_dispensing_request/sc_dispensing_request.py` — validate quota + estimated value + auto requested_by
5. `supplycore/m7_dispensing/api/__init__.py` — package marker
6. `supplycore/m7_dispensing/api/dispense_helpers.py` — `check_stock_availability()`
7. `supplycore/tests/uc20_test.py` — 11 test scenarios
