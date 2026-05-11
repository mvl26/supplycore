# UC-11 — Xử lý hàng trả lại NCC — Flow & Implementation

**Module:** M3 Receiving (UC) + Supplycore (DocType host)
**DocType:** SC Purchase Receipt (Return) + SC Purchase Invoice (Debit/Credit Note)
**Date:** 2026-05-11
**Source:** Phase 1 / UseCase_SupplyCore_v2.0.md UC-11

## Audit hiện trạng (trước UC-11)

| Spec line | Trước | Sau UC-11 |
|---|---|---|
| 1. Tạo Purchase Return từ PR | Partial: `_create_return_pr` auto UC-10. Manual qua PR.is_return=1. ✗ method whitelisted | ✓ `make_return_from_pr` whitelisted + button |
| 2. Chọn VT + qty + **lý do trả** | Partial: items có; `return_reason` thiếu | ✓ field `return_reason` |
| 3. Tính giá hoàn trả từ PO unit_price | ✓ rate copy từ PR.rate (= PO rate) | ✓ |
| 4. Submit → SLE -qty + **Debit Note** | Partial: SLE đã có; ✗ Debit Note doctype | ✓ `is_debit_note` trên SC PI + `make_debit_note()` |
| 5. Email NCC | ✗ | ✓ `send_return_notification()` + auto trên on_submit |
| 6. Track status: Pending → Replaced / Refunded / Closed | ✗ | ✓ field `return_status` Select |
| 7. Nhận hàng đổi → PR mới link Return | ✗ link | ✓ field `replacement_pr` + method `link_replacement` |
| 6a. NCC hoàn tiền → Credit Note | ✗ | ✓ `is_credit_note` trên SC PI + `make_credit_note()` |
| 6b. NCC đổi hàng → UC-09/10 | ✓ flow chuẩn nếu link đúng | ✓ |
| Ngoại lệ: NCC không phản hồi 7 ngày → escalate | ✗ | ✓ scheduler `check_return_responses` daily |

## Actor

- Thủ kho (Storekeeper) — flag QC Fail (đã có UC-10)
- Kế toán (Accountant) — tạo Return + Debit/Credit Note + theo dõi
- Quản lý (Manager) — escalation khi NCC im lặng

## Pre-condition

- QC Fail đã ghi nhận (UC-10 auto-tạo Draft Return PR HOẶC user manual)
- HOẶC user manual flag PR.is_return=1 để trả hàng không qua QC

## Luồng chính

| Bước | User | Hệ thống |
|---|---|---|
| 1 | Kế toán mở Draft Return PR (auto từ UC-10 hoặc tạo manual is_return=1) | Form load với items, supplier, rate |
| 2 | Chọn items + qty + nhập `return_reason` | validate reqd return_reason khi is_return=1 |
| 3 | rate per row đã có từ PR gốc (= PO unit price) | `_compute_totals` tính `total_value` |
| 4 | Submit | `on_submit()`: SLE -qty (đã có); `send_return_notification()` auto-email NCC; `return_status=Pending Supplier Response`; `notification_sent_at=now` |
| 5 | Email NCC tự gửi | – |
| 6 | Theo dõi: NCC phản hồi đổi hàng hoặc hoàn tiền | User update `return_status` qua action |
| 6a | NCC hoàn tiền → Kế toán click "Tạo Credit Note" | `make_credit_note()` tạo SC PI with `is_credit_note=1`, `return_against_pr=this`, items=PR items, grand_total=PR.total_value. Set `credit_note` link. Set `return_status=Refunded` |
| 6b | NCC đổi hàng → tạo PR mới (UC-09) → click "Link Replacement" trên Return PR | `link_replacement(pr_name)` set `replacement_pr` + `return_status=Replaced` |
| 7 | Auto Debit Note sau Submit | `on_submit` cũng auto-call `make_debit_note()` tạo SC PI `is_debit_note=1` để điều chỉnh AP |

## Luồng thay thế

### 6a — Credit Note (refund)

- SC PI với `is_credit_note=1`, `return_against_pr=Return PR.name`, grand_total = - PR.total_value (hoặc dương nhưng đánh dấu credit — accounting flag)
- AP điều chỉnh: Outstanding của NCC giảm tương ứng

### 6b — Đổi hàng

- NCC giao hàng mới → tạo PR mới (UC-09) link `purchase_order` original
- Manual: trên Return PR click "Link Replacement" → chọn PR mới
- `return_status` chuyển Replaced

## Xử lý ngoại lệ

### NCC không phản hồi 7 ngày

Daily scheduler `supplycore.m3_receiving.tasks.check_return_responses`:
- Find Return PR docstatus=1, return_status=`Pending Supplier Response`, posting_date < today-7, escalated_at IS NULL
- Email Manager: "Return PR {name} chưa được NCC xử lý sau 7 ngày — cần escalate"
- Set `escalated_at = now`
- Dedup: chỉ escalate 1 lần / Return PR

## Field changes

### SC Purchase Receipt (Return PR) — ADD

| Field | Type | Note |
|---|---|---|
| `return_reason` | Small Text | Reqd khi is_return=1 |
| `return_status` | Select `Pending Supplier Response\nReplaced\nRefunded\nClosed` | default Pending |
| `debit_note` | Link `SC Purchase Invoice`, read_only | link đến PI Debit Note |
| `credit_note` | Link `SC Purchase Invoice`, read_only | link đến PI Credit Note |
| `replacement_pr` | Link `SC Purchase Receipt`, read_only | PR đổi hàng |
| `notification_sent_at` | Datetime, read_only | dedup email |
| `escalated_at` | Datetime, read_only | dedup escalation |

### SC Purchase Invoice — ADD

| Field | Type | Note |
|---|---|---|
| `is_debit_note` | Check, default 0 | flag Debit Note |
| `is_credit_note` | Check, default 0 | flag Credit Note |
| `return_against_pr` | Link `SC Purchase Receipt`, depends_on `is_debit_note OR is_credit_note` | trace lại Return PR |

## Error codes mới

| Code | Trigger | Message |
|---|---|---|
| `SC-E-RETURN-REASON` | submit Return PR không có return_reason | "Phải nhập 'Lý do trả hàng'" |
| `SC-E-RETURN-DN-EXISTS` | make_debit_note khi đã có debit_note | "Đã có Debit Note: {name}" |
| `SC-E-RETURN-CN-EXISTS` | make_credit_note khi đã có credit_note | "Đã có Credit Note: {name}" |
| `SC-E-RETURN-REPLACE-INVALID` | link_replacement với PR không phải PR thường (is_return=1) | "PR đổi hàng phải là PR thường (is_return=0)" |
| `SC-E-RETURN-NOT-SUBMITTED` | make_debit/credit_note khi Return PR chưa submitted | "Return PR phải submitted để tạo Debit/Credit Note" |

## Logic — `sc_purchase_receipt.py`

### Validate (extend)

```python
def validate(self):
    ...existing...
    self._validate_return_reason()
```

```python
def _validate_return_reason(self):
    if self.is_return and self.docstatus == 0:
        if not (self.return_reason and str(self.return_reason).strip()):
            # check trong validate là warning; reqd thực ở before_submit
            pass

def before_submit(self):
    ...existing (over_receipt, no_po_reason)...
    if self.is_return:
        if not (self.return_reason and str(self.return_reason).strip()):
            frappe.throw(_("SC-E-RETURN-REASON: Phải nhập 'Lý do trả hàng'"))
```

### on_submit (extend)

```python
def on_submit(self):
    ...existing...
    if self.is_return and not self.return_status:
        self.db_set("return_status", "Pending Supplier Response")
    if self.is_return:
        self._send_return_notification()
        # Auto-tạo Debit Note (skip nếu đã có)
        if not self.debit_note:
            try:
                self.make_debit_note()
            except Exception as e:
                frappe.log_error(message=str(e)[:1000], title="UC-11 auto make_debit_note")
```

### New whitelisted methods

```python
@frappe.whitelist()
def make_debit_note(self):
    if self.docstatus != 1:
        frappe.throw(_("SC-E-RETURN-NOT-SUBMITTED: Return PR phải submitted"))
    if self.debit_note:
        frappe.throw(_("SC-E-RETURN-DN-EXISTS: Đã có Debit Note: {0}").format(self.debit_note))

    pi = frappe.new_doc("SC Purchase Invoice")
    pi.supplier = self.supplier
    pi.supplier_invoice_no = f"DN-{self.name}"
    pi.invoice_date = today()
    pi.due_date = today()
    pi.purchase_receipt = self.name
    pi.is_debit_note = 1
    pi.return_against_pr = self.name
    for r in self.items:
        pi.append("items", {
            "item": r.item, "qty": flt(r.qty), "uom": r.uom,
            "rate": flt(r.rate), "amount": flt(r.qty) * flt(r.rate),
        })
    pi.remarks = f"Debit Note for Return {self.name} — {self.return_reason or ''}"
    pi.flags.ignore_permissions = True
    pi.insert()
    self.db_set("debit_note", pi.name)
    return pi.name

@frappe.whitelist()
def make_credit_note(self):
    if self.docstatus != 1:
        frappe.throw(_("SC-E-RETURN-NOT-SUBMITTED: Return PR phải submitted"))
    if self.credit_note:
        frappe.throw(_("SC-E-RETURN-CN-EXISTS: Đã có Credit Note: {0}").format(self.credit_note))

    pi = frappe.new_doc("SC Purchase Invoice")
    pi.supplier = self.supplier
    pi.supplier_invoice_no = f"CN-{self.name}"
    pi.invoice_date = today()
    pi.due_date = today()
    pi.purchase_receipt = self.name
    pi.is_credit_note = 1
    pi.return_against_pr = self.name
    for r in self.items:
        pi.append("items", {
            "item": r.item, "qty": flt(r.qty), "uom": r.uom,
            "rate": flt(r.rate), "amount": flt(r.qty) * flt(r.rate),
        })
    pi.remarks = f"Credit Note (refund) for Return {self.name}"
    pi.flags.ignore_permissions = True
    pi.insert()
    self.db_set("credit_note", pi.name)
    self.db_set("return_status", "Refunded")
    return pi.name

@frappe.whitelist()
def link_replacement(self, replacement_pr_name: str):
    if self.docstatus != 1:
        frappe.throw(_("Return PR phải submitted"))
    rep = frappe.get_doc("SC Purchase Receipt", replacement_pr_name)
    if rep.is_return:
        frappe.throw(_(
            "SC-E-RETURN-REPLACE-INVALID: PR đổi hàng phải là PR thường (is_return=0)"
        ))
    self.db_set("replacement_pr", replacement_pr_name)
    self.db_set("return_status", "Replaced")
    return {"replacement_pr": replacement_pr_name, "return_status": "Replaced"}

@frappe.whitelist()
def send_return_notification(self):
    self._send_return_notification(force=1)
    return {"sent_to": frappe.db.get_value("SC Supplier", self.supplier, "email_id")}
```

### Helpers

```python
def _send_return_notification(self, force: int = 0):
    if not self.is_return:
        return
    if self.notification_sent_at and not force:
        return
    email = frappe.db.get_value("SC Supplier", self.supplier, "email_id")
    if not email:
        frappe.log_error(message=f"Return PR {self.name} supplier no email",
                          title="UC-11 _send_return_notification")
        return
    items_html = "".join(
        f"<tr><td>{r.item}</td><td>{r.qty}</td><td>{r.uom}</td></tr>"
        for r in self.items
    )
    msg = (f"<p>Kính gửi {frappe.db.get_value('SC Supplier', self.supplier, 'supplier_name') or self.supplier},</p>"
           f"<p>Bệnh viện trả hàng theo Phiếu trả <b>{self.name}</b>:</p>"
           f"<table border='1' cellpadding='6'>"
           f"<tr><th>Mã VT</th><th>SL</th><th>UOM</th></tr>{items_html}</table>"
           f"<p><b>Lý do:</b> {frappe.utils.escape_html(self.return_reason or '—')}</p>"
           f"<p>Tổng giá trị hoàn trả: {frappe.format(self.total_value, {'fieldtype':'Currency'})}</p>"
           f"<p>Vui lòng xác nhận đổi hàng / hoàn tiền trong 7 ngày làm việc.</p>")
    try:
        frappe.sendmail(
            recipients=[email],
            subject=f"[SupplyCore] Phiếu trả hàng {self.name}",
            message=msg, delayed=False,
        )
        self.db_set("notification_sent_at", frappe.utils.now())
    except Exception as e:
        frappe.log_error(message=str(e)[:1000], title="UC-11 _send_return_notification")
```

## Scheduler — `m3_receiving/tasks.py` (NEW)

```python
def check_return_responses():
    """Daily (UC-11 ngoại lệ): escalate Return PR Pending > 7 ngày."""
    rows = frappe.db.sql("""
        SELECT name, supplier, supplier_name, posting_date, total_value
        FROM `tabSC Purchase Receipt`
        WHERE docstatus = 1 AND is_return = 1
          AND return_status = 'Pending Supplier Response'
          AND escalated_at IS NULL
          AND DATEDIFF(CURDATE(), posting_date) >= 7
        LIMIT 50
    """, as_dict=True)

    if not rows:
        return {"escalated": 0}

    managers = frappe.db.sql_list("""
        SELECT DISTINCT u.email FROM `tabUser` u
        JOIN `tabHas Role` r ON r.parent = u.name
        WHERE r.role = 'SupplyCore Manager' AND u.enabled = 1
          AND u.email IS NOT NULL AND u.email != ''
    """) or []

    escalated = 0
    for r in rows:
        if managers:
            try:
                frappe.sendmail(
                    recipients=managers,
                    subject=f"[SupplyCore][ESCALATE] Return PR {r.name} chưa xử lý sau 7 ngày",
                    message=(f"<p>Return PR <a href='/app/sc-purchase-receipt/{r.name}'>{r.name}</a> "
                             f"gửi NCC <b>{r.supplier_name or r.supplier}</b> ngày {r.posting_date} "
                             f"chưa nhận phản hồi.</p>"
                             f"<p>Giá trị: {frappe.format(r.total_value, {'fieldtype':'Currency'})}</p>"
                             f"<p>Vui lòng liên hệ NCC để xử lý.</p>"),
                    delayed=False,
                )
            except Exception as e:
                frappe.log_error(message=f"PR={r.name}: {str(e)[:500]}",
                                  title="UC-11 check_return_responses")
        frappe.db.set_value("SC Purchase Receipt", r.name,
                             "escalated_at", frappe.utils.now())
        escalated += 1
    frappe.db.commit()
    return {"escalated": escalated, "candidates": len(rows)}
```

Đăng ký trong `hooks.py.scheduler_events.daily`.

## Migration

- 7 field mới Return PR + 3 field SC PI tự migrate
- Không cần patch riêng

## Test plan — `tests/uc11_test.py`

| Test | Scenario |
|---|---|
| `test_return_pr_requires_reason` | Return PR submit không reason → SC-E-RETURN-REASON |
| `test_return_pr_with_reason_submits` | Return PR submit + reason → OK, return_status=Pending Supplier Response |
| `test_return_pr_auto_creates_debit_note` | submit Return PR → auto-tạo SC PI is_debit_note=1, link debit_note |
| `test_make_credit_note_sets_refunded` | submit + make_credit_note() → PI is_credit_note=1, return_status=Refunded |
| `test_make_debit_note_idempotent` | gọi 2 lần → SC-E-RETURN-DN-EXISTS |
| `test_link_replacement_sets_replaced` | link PR thường (is_return=0) → replacement_pr set, return_status=Replaced |
| `test_link_replacement_rejects_return_pr` | link PR is_return=1 → SC-E-RETURN-REPLACE-INVALID |
| `test_send_notification_sets_timestamp` | submit Return PR → notification_sent_at populated |
| `test_check_return_responses_escalates_over_7d` | Return PR posting >7d không response → scheduler escalate, escalated_at set |

## Out-of-scope

- UI button JS (defer; whitelisted methods đủ)
- Full AP reconciliation logic của Debit/Credit Note vào outstanding (chỉ tạo PI record + flag)
- Multi-tier escalation (chỉ Manager, không Executive)

## File changes

1. `supplycore/m3_receiving/UC-11_FLOW.md` — this file
2. `supplycore/supplycore/doctype/sc_purchase_receipt/sc_purchase_receipt.json` — 7 fields mới
3. `supplycore/supplycore/doctype/sc_purchase_receipt/sc_purchase_receipt.py` — validate + on_submit + 4 whitelisted methods + helpers
4. `supplycore/m8_accounting/doctype/sc_purchase_invoice/sc_purchase_invoice.json` — 3 fields mới
5. `supplycore/m3_receiving/tasks.py` — NEW scheduler check_return_responses
6. `supplycore/hooks.py` — register scheduler
7. `supplycore/tests/uc11_test.py` — 9 test scenarios
