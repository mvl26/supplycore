# UC-24 — Tạo và đối chiếu Purchase Invoice — Flow & Implementation

**Module:** M8 Accounting
**DocType:** SC Purchase Invoice + SC PI Item (existing)
**Date:** 2026-05-11
**Source:** Phase 1 / UseCase_SupplyCore_v2.0.md UC-24

## Audit hiện trạng

| Spec | Trước | Sau UC-24 |
|---|---|---|
| 1. Tạo PI từ PR | ✓ `make_invoice_from_pr` | ✓ |
| 2. Auto load items | ✓ copy PR items | ✓ |
| 3. Nhập số HĐ NCC + ngày + tổng | ✓ supplier_invoice_no + invoice_date | ✓ |
| 4. 3-way match | ✓ `_three_way_match` PO ↔ PR ↔ PI | ✓ |
| 5. **Match → xanh + auto approve** | Partial: status=Match, không auto submit | ✓ approval_required_by=Auto khi Match + below threshold |
| 6. **Mismatch → đỏ + yêu cầu giải trình** | Partial: msgprint; ✗ field giải trình | ✓ `mismatch_explanation` reqd khi Mismatch/Force Approved |
| 7. Submit → GL + công nợ | ✓ `_post_gl_entries` Dr152/Dr1331/Cr331 | ✓ |
| 5a. Chênh lệch ≤1% → Accept | ✓ tolerance=1% | ✓ |
| 6a. **Chênh lệch lớn → escalate + hold thanh toán** | Partial: approval_required_by=Executive; ✗ payment_hold flag | ✓ `payment_hold` auto-set Check |
| **Ngoại lệ: trùng số HĐ NCC** | Partial: existing check qua make_invoice_from_pr (PR duplicate); ✗ unique (supplier, supplier_invoice_no) | ✓ validate duplicate |

## Actor

- Kế toán (Accountant) — tạo + submit PI

## Pre-condition

- PR đã submit (qc_status không Rejected) (UC-09/10)
- Có HĐ NCC giấy

## Luồng chính

| Bước | Action |
|---|---|
| 1 | Mở PR submitted → click "Tạo Purchase Invoice" → `make_invoice_from_pr(pr)` |
| 2 | Items copy từ PR (item, qty, uom, rate) |
| 3 | Nhập `supplier_invoice_no` thực tế, `invoice_date`, sửa rate nếu khác |
| 4 | Save → `_three_way_match` compare PI subtotal vs PO grand_total vs PR total_value |
| 5 | Match → `three_way_match_status=Match`, `approval_required_by=Auto/Manager` |
| 6 | Mismatch → `three_way_match_status=Mismatch`, `approval_required_by=Executive`, `payment_hold=1`; user nhập `mismatch_explanation` reqd để submit |
| 7 | Submit → `on_submit` post GL Entry (Dr 152 + Dr 1331 / Cr 331) + status=Approved |

## Luồng thay thế

### 5a — Chênh lệch ≤1%

Tolerance 1% trong `_three_way_match`. Trong tolerance → status=Match, không cần explanation.

### 6a — Chênh lệch lớn → hold

`_three_way_match` set `payment_hold=1` khi status=Mismatch. UC-25 Payment Entry sẽ check `payment_hold` trước khi tạo (defer kiểm tra UC-25).

## Xử lý ngoại lệ

### Trùng số HĐ NCC

`validate`: check tồn tại PI khác cùng (supplier, supplier_invoice_no, docstatus != 2) → throw `SC-E-PI-DUPLICATE`.

## Field changes

### SC Purchase Invoice — ADD

| Field | Type | Note |
|---|---|---|
| `mismatch_explanation` | Small Text | reqd khi 3-way match Mismatch/Force Approved |
| `payment_hold` | Check, read_only | auto-set khi Mismatch; UC-25 sẽ check |

## Error codes mới

| Code | Trigger | Message |
|---|---|---|
| `SC-E-PI-DUPLICATE` | (supplier, supplier_invoice_no) đã tồn tại trong PI khác | "HĐ NCC số '{x}' của NCC {y} đã có trong PI {z}" |
| `SC-E-PI-MISMATCH-EXPLANATION` | submit với match=Mismatch/Force Approved không có explanation | "Phải nhập 'Giải trình chênh lệch' khi 3-way match không khớp" |

## Logic — `sc_purchase_invoice.py`

### Validate extend

```python
def validate(self):
    from supplycore.utils.validators import validate_supplier
    validate_supplier(self.supplier)
    self._compute_totals()
    self._auto_due_date()
    self._three_way_match()
    self._set_payment_hold()           # NEW
    self._determine_approval_level()
    self._validate_duplicate_invoice() # NEW
    if self.docstatus == 0:
        self.status = "Draft"

def before_submit(self):
    if self.three_way_match_status in ("Mismatch", "Force Approved"):
        if not (self.mismatch_explanation and str(self.mismatch_explanation).strip()):
            frappe.throw(_(
                "SC-E-PI-MISMATCH-EXPLANATION: Phải nhập 'Giải trình chênh lệch' "
                "khi 3-way match không khớp"
            ))

def _validate_duplicate_invoice(self):
    """UC-24 ngoại lệ: unique (supplier, supplier_invoice_no)."""
    if not (self.supplier and self.supplier_invoice_no):
        return
    existing = frappe.db.sql("""
        SELECT name FROM `tabSC Purchase Invoice`
        WHERE supplier = %s AND supplier_invoice_no = %s
          AND name != %s AND docstatus != 2
        LIMIT 1
    """, (self.supplier, self.supplier_invoice_no, self.name or ""))
    if existing:
        frappe.throw(_(
            "SC-E-PI-DUPLICATE: HĐ NCC số '{0}' của NCC {1} đã có trong PI {2}"
        ).format(self.supplier_invoice_no, self.supplier, existing[0][0]))

def _set_payment_hold(self):
    """UC-24 6a: auto-hold thanh toán khi Mismatch."""
    if self.three_way_match_status == "Mismatch":
        self.payment_hold = 1
    elif self.three_way_match_status in ("Match", "Force Approved", "Not Applicable"):
        # Force Approved: user đã giải trình, không hold
        if self.three_way_match_status != "Force Approved":
            self.payment_hold = 0
```

### Update `_determine_approval_level`

```python
def _determine_approval_level(self):
    threshold = _get_exec_threshold()
    if self.three_way_match_status == "Mismatch":
        self.approval_required_by = "Executive"
    elif flt(self.grand_total) >= threshold:
        self.approval_required_by = "Executive"
    elif self.three_way_match_status == "Match":
        # UC-24 step 5: Match → Auto (kế toán submit không cần thêm duyệt)
        self.approval_required_by = "Auto"
    elif self.three_way_match_status == "Not Applicable":
        self.approval_required_by = "Manager"
    else:
        self.approval_required_by = "Auto"
```

## Migration

- 2 fields mới Frappe tự migrate

## Test plan — `tests/uc24_test.py`

| Test | Scenario |
|---|---|
| `test_pi_create_basic` | Tạo PI manual với supplier + items → save OK |
| `test_pi_duplicate_invoice_no_blocked` | 2 PI cùng (supplier, supplier_invoice_no) → SC-E-PI-DUPLICATE |
| `test_pi_3way_match_no_po_na` | PI không có PO → status=Not Applicable |
| `test_pi_3way_match_exact` | PI subtotal = PO grand_total = PR total → status=Match, variance=0 |
| `test_pi_3way_match_within_tolerance` | Chênh 0.5% → status=Match |
| `test_pi_3way_match_mismatch` | Chênh 5% → status=Mismatch + payment_hold=1 |
| `test_pi_submit_blocked_without_explanation_on_mismatch` | Mismatch + no explanation + submit → SC-E-PI-MISMATCH-EXPLANATION |
| `test_pi_submit_with_explanation_on_mismatch` | Mismatch + explanation + submit → OK + status=Approved |
| `test_pi_auto_approval_when_match_below_threshold` | Match + below 50tr → approval_required_by=Auto |
| `test_pi_executive_required_above_threshold` | Match + ≥50tr → approval_required_by=Executive |

## Out-of-scope

- Auto-create PI từ scheduler khi PR submit (defer; user manual click)
- OCR HĐ NCC PDF (defer)
- Multi-currency (chỉ VND)
- Tax withholding (defer)

## File changes

1. `supplycore/m8_accounting/UC-24_FLOW.md` — this file
2. `supplycore/m8_accounting/doctype/sc_purchase_invoice/sc_purchase_invoice.json` — 2 fields mới
3. `supplycore/m8_accounting/doctype/sc_purchase_invoice/sc_purchase_invoice.py` — validate dedup + explanation reqd + payment_hold + Auto approval
4. `supplycore/tests/uc24_test.py` — 10 test scenarios
