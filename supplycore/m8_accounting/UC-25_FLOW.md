# UC-25 — Thanh toán NCC (Payment Entry) — Flow & Implementation

**Module:** M8 Accounting
**DocType:** SC Payment Entry + SC Payment Reference (existing)
**Date:** 2026-05-11
**Source:** Phase 1 / UseCase_SupplyCore_v2.0.md UC-25

## Audit hiện trạng

| Spec | Trước | Sau UC-25 |
|---|---|---|
| 1. Mở PE Pay + NCC | ✓ | ✓ |
| 2. **Chọn HĐ outstanding** | Partial: manual append; ✗ auto-load | ✓ `auto_load_outstanding_invoices()` |
| 3. Số tiền + ngày + bank | ✓ | ✓ |
| 4. Số chứng từ chuyển khoản | ✓ `reference_no` + `reference_date` | ✓ |
| 5. **Submit + Manager duyệt khi ≥ ngưỡng** | Partial: approval_level computed; ✗ enforce role | ✓ before_submit role check |
| 5a. **≥ ngưỡng → Executive** | ✓ existing | ✓ + role enforce |
| 6. GL Entry Dr331/Cr1121 | ✓ existing | ✓ |
| 7. PI Paid/Partly Paid | ✓ `update_outstanding` | ✓ |
| 3a. **Partial + lý do** | Partial: allocated < outstanding OK; ✗ reason field | ✓ thêm `partial_reason` |
| **UC-24 carry: PI payment_hold** | ✗ | ✓ block ref khi PI.payment_hold=1 → SC-E-PE-PAYMENT-HOLD |
| **Bank balance không đủ → cảnh báo cho submit** | ✗ | ✓ `check_bank_balance()` msgprint warning |

## Actor

- Kế toán (Accountant) — tạo PE
- Manager (<50tr) / Executive (≥50tr) — duyệt qua role-based submit

## Pre-condition

- PI đã submit (UC-24) + payment_hold=0 (hoặc release sau giải trình)

## Luồng chính

| Bước | Action |
|---|---|
| 1 | Mở `/app/sc-payment-entry/new`, chọn `supplier` |
| 2 | Click "Tải HĐ outstanding" → `auto_load_outstanding_invoices(supplier)` append refs với allocated_amount = outstanding mỗi PI |
| 3 | Nhập `amount`, `payment_date`, `bank_account`, `payment_method` |
| 4 | Nhập `reference_no` + `reference_date` (số chứng từ NH) |
| 5 | Save → validate refs + computed approval_level. Submit → before_submit check role |
| 6 | on_submit post GL (Dr 331/Cr 1121 hoặc 1111) |
| 7 | `update_outstanding` per PI → status=Paid/Partly Paid |

## Luồng thay thế

### 3a — Partial payment

- User set `allocated_amount` < `outstanding_before`
- Nhập `partial_reason` (Small Text) trên ref hoặc parent
- Submit OK; PI status=Partly Paid

### 5a — ≥ ngưỡng → Executive

`before_submit`:
- Nếu `approval_level=Executive` → check user role có "SupplyCore Executive" OR "System Manager"
- Else throw `SC-E-PE-EXECUTIVE-REQUIRED`

## Xử lý ngoại lệ

### PI payment_hold → block

`_validate_references` thêm check: nếu PI.payment_hold=1 → throw `SC-E-PE-PAYMENT-HOLD` "PI {x} đang hold thanh toán (3-way mismatch chưa release)".

### Bank balance không đủ

`check_bank_balance` whitelisted: query SC GL Entry tính balance hiện tại của bank account → so với `amount`. Nếu < amount → `msgprint` orange warning (KHÔNG block — UC explicit "cảnh báo nhưng vẫn cho phép submit").

## Field changes

### SC Payment Entry — ADD

| Field | Type | Note |
|---|---|---|
| `partial_reason` | Small Text | Optional — UC 3a partial payment lý do |

## Error codes mới

| Code | Trigger | Message |
|---|---|---|
| `SC-E-PE-PAYMENT-HOLD` | Ref PI có payment_hold=1 | "PI {x} đang hold thanh toán (3-way mismatch chưa release)" |
| `SC-E-PE-MANAGER-REQUIRED` | approval_level=Manager + user thiếu Manager role | "Submit PE yêu cầu role SupplyCore Manager" |
| `SC-E-PE-EXECUTIVE-REQUIRED` | approval_level=Executive + user thiếu Executive role | "Submit PE ≥ ngưỡng yêu cầu role SupplyCore Executive" |

## Logic — `sc_payment_entry.py`

### `_validate_references` extend

```python
def _validate_references(self):
    for ref in self.references:
        pi = frappe.db.get_value("SC Purchase Invoice", ref.purchase_invoice,
                                   ["supplier", "grand_total", "outstanding_amount",
                                    "docstatus", "payment_hold"], as_dict=True)
        if not pi or pi.docstatus != 1:
            frappe.throw(_("PI {0} không tồn tại hoặc chưa submit").format(ref.purchase_invoice))
        if pi.supplier != self.supplier:
            frappe.throw(_("PI {0} thuộc NCC khác: {1}").format(ref.purchase_invoice, pi.supplier))
        # UC-25 ngoại lệ: PI hold → block
        if pi.payment_hold:
            frappe.throw(_(
                "SC-E-PE-PAYMENT-HOLD: PI {0} đang hold thanh toán "
                "(3-way mismatch chưa release)"
            ).format(ref.purchase_invoice))
        ref.invoice_total = flt(pi.grand_total)
        ref.outstanding_before = flt(pi.outstanding_amount)
        if flt(ref.allocated_amount) > flt(pi.outstanding_amount) + 0.01:
            frappe.throw(_("Phân bổ {0} cho PI {1} > còn phải trả {2}").format(
                ref.allocated_amount, ref.purchase_invoice, pi.outstanding_amount))
        ref.outstanding_after = flt(pi.outstanding_amount) - flt(ref.allocated_amount)
```

### `before_submit` (NEW)

```python
def before_submit(self):
    user_roles = set(frappe.get_roles(frappe.session.user))
    if self.approval_level == "Executive":
        allowed = {"SupplyCore Executive", "System Manager"}
        if not (user_roles & allowed):
            frappe.throw(_(
                "SC-E-PE-EXECUTIVE-REQUIRED: Submit PE ≥ ngưỡng yêu cầu role "
                "SupplyCore Executive"
            ))
    elif self.approval_level == "Manager":
        allowed = {"SupplyCore Manager", "SupplyCore Executive", "System Manager"}
        if not (user_roles & allowed):
            frappe.throw(_(
                "SC-E-PE-MANAGER-REQUIRED: Submit PE yêu cầu role SupplyCore Manager"
            ))
    self._check_bank_balance()
```

### Helpers (new)

```python
def _check_bank_balance(self):
    """UC-25 ngoại lệ: cảnh báo nếu số dư bank < amount (KHÔNG block)."""
    if self.payment_method != "Bank Transfer":
        return
    acc = _resolve_account("1121")
    if not acc:
        return
    # Compute balance from SC GL Entry
    balance = flt(frappe.db.sql("""
        SELECT COALESCE(SUM(debit) - SUM(credit), 0)
        FROM `tabSC GL Entry`
        WHERE account = %s AND is_cancelled = 0
    """, acc)[0][0])
    if balance < flt(self.amount):
        frappe.msgprint(
            _("⚠ Số dư tài khoản {0} hiện tại {1} thấp hơn số tiền PE ({2}). "
              "Tiếp tục submit nhưng cần kiểm tra dòng tiền.").format(
                acc,
                frappe.format(balance, {"fieldtype": "Currency"}),
                frappe.format(self.amount, {"fieldtype": "Currency"})),
            indicator="orange", alert=True,
        )


@frappe.whitelist()
def auto_load_outstanding_invoices(supplier: str, limit: int = 50) -> list:
    """UC-25 step 2: list PI outstanding của supplier (sorted by due_date ASC)."""
    rows = frappe.db.sql("""
        SELECT name, supplier_invoice_no, invoice_date, due_date,
               grand_total, paid_amount, outstanding_amount,
               three_way_match_status, payment_hold
        FROM `tabSC Purchase Invoice`
        WHERE supplier = %s
          AND docstatus = 1
          AND outstanding_amount > 0
          AND COALESCE(payment_hold, 0) = 0
        ORDER BY due_date ASC LIMIT %s
    """, (supplier, int(limit)), as_dict=True)
    return rows
```

## Migration

- 1 field mới Frappe tự migrate

## Test plan — `tests/uc25_test.py`

| Test | Scenario |
|---|---|
| `test_pe_create_basic` | Tạo PE + ref PI outstanding → save OK |
| `test_pe_ref_pi_different_supplier_blocked` | Ref PI khác supplier → throw |
| `test_pe_ref_pi_payment_hold_blocked` | Ref PI có payment_hold=1 → SC-E-PE-PAYMENT-HOLD |
| `test_pe_allocated_exceeds_outstanding_blocked` | allocated > PI.outstanding → throw |
| `test_pe_allocated_total_must_equal_amount` | Submit với allocated_total ≠ amount → throw |
| `test_pe_manager_below_threshold` | amount<50tr → approval_level=Manager |
| `test_pe_executive_above_threshold` | amount≥50tr → approval_level=Executive |
| `test_pe_submit_blocks_non_executive_for_high_amount` | Executive level + non-Exec user → SC-E-PE-EXECUTIVE-REQUIRED |
| `test_pe_submit_updates_pi_to_paid` | PE full amount → PI.status=Paid + outstanding=0 |
| `test_pe_partial_keeps_pi_partly_paid` | PE half amount → PI.status=Partly Paid |
| `test_auto_load_outstanding_invoices` | Supplier có 2 PI outstanding → API trả 2 |
| `test_pe_cancel_reverts_pi_outstanding` | Cancel PE → PI outstanding restore |

## Out-of-scope

- Multi-bank batch payment (defer)
- FX (chỉ VND)
- Auto-create PE từ aging report (defer Phase 2)
- Cheque clearance workflow (Cleared status existing nhưng manual)

## File changes

1. `supplycore/m8_accounting/UC-25_FLOW.md` — this file
2. `supplycore/m8_accounting/doctype/sc_payment_entry/sc_payment_entry.json` — `partial_reason` field
3. `supplycore/m8_accounting/doctype/sc_payment_entry/sc_payment_entry.py` — payment_hold block + role enforce + bank balance + auto-load
4. `supplycore/tests/uc25_test.py` — 12 test scenarios
