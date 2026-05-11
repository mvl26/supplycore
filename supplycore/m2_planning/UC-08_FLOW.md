# UC-08 — Tạo và Phê duyệt Purchase Order — Flow & Implementation

**Module:** M2 Planning (UC) + Supplycore (DocType `SC Purchase Order` host)
**DocType:** SC Purchase Order (parent) + SC Purchase Order Item (child)
**Date:** 2026-05-11
**Source:** Phase 1 / UseCase_SupplyCore_v2.0.md UC-08
**Lưu ý:** dùng SC * doctypes (no-ERPNext).

## Audit hiện trạng (trước UC-08)

| Spec line | Trước | Sau UC-08 |
|---|---|---|
| 1. Tạo PO từ MR | ✓ `suggest_po_from_mr` | ✓ |
| 2. Chọn NCC + auto-load giá từ FC | ✓ FC unit_price | ✓ (giữ + thêm price variance flag) |
| 2. Auto-load từ Supplier Quotation | ✗ SQ doctype không có | Manual qua `quotation_attachment` (luồng 2a) |
| 2a. Không FC → nhập giá thủ công + attach báo giá | ✗ chỉ ghi unmatched | ✓ field `quotation_attachment` (Attach) |
| 3. Adjust qty/price/delivery terms | Partial: qty/price ✓; ✗ delivery_terms | ✓ field `delivery_terms` |
| 4. Check hạn mức HĐ | ✓ `_validate_against_framework_contract` | ✓ |
| 4a. Vượt FC → block | ✓ throws SC-E002 FC_EXCEEDED | ✓ |
| 5. Workflow theo giá trị (<50tr Manager, ≥50tr Lãnh đạo) | ✗ auto-Approved on submit | ✓ 2-tier workflow giống UC-03 |
| 6. Duyệt/từ chối | ✗ | ✓ `approve_as_manager`, `approve_as_executive`, `reject` |
| 7. Auto gửi email NCC sau duyệt | ✗ | ✓ on_submit → sendmail supplier.email_id |
| 8. Status "Sent to Supplier" | Status option có, ✗ không auto-set | ✓ set sau submit |
| Hậu: RO cập nhật | ✓ `_update_framework_contract` | ✓ |
| Hậu: PO email đến NCC | ✗ | ✓ |
| Ngoại lệ: NCC không phản hồi 3 ngày | ✗ | ✓ scheduler `check_po_response` daily |
| Ngoại lệ: giá NCC ≠ giá FC → flag | ✗ | ✓ `has_price_variance` flag + per-row `fc_unit_price`/`price_variance_pct` |

## Actor

- Kế toán (SupplyCore Accountant) — tạo, submit_for_review
- Quản lý (SupplyCore Manager) — approve_as_manager / reject
- Lãnh đạo (SupplyCore Executive) — approve_as_executive (khi ≥ threshold) / reject

## Pre-condition

- MR đã Approved (UC-07)
- NCC active (không disabled, không blacklist trừ executive override)
- FC còn hiệu lực (nếu có)

## Luồng chính

| Bước | User | Hệ thống |
|---|---|---|
| 1 | Kế toán mở MR Approved → click "Tạo Purchase Order" (hoặc tạo PO trực tiếp /app/sc-purchase-order/new) | `suggest_po_from_mr(auto_create=1)` group theo (supplier, FC) → 1 Draft PO/group. Items unmatched FC → trả về list |
| 2 | Chọn supplier (nếu tạo trực tiếp) | `validate()` auto-load `rate` từ FC Item.unit_price (đã có via _find_best_fc_for_item). Set `fc_unit_price` per row |
| 3 | Adjust qty/rate/delivery_terms | `_compute_totals()` + `_check_price_variance()` flag nếu rate ≠ fc_unit_price ±1% |
| 4 | Hệ thống tính `grand_total` + check `framework_contract.remaining_value` | `_validate_against_framework_contract` throw `SC-E002 FC_EXCEEDED` nếu vượt |
| 5 | Kế toán click **"Gửi duyệt (Manager)"** | `submit_for_review()` → stage=Manager Review |
| 5a | Manager click **"Manager duyệt"** | `approve_as_manager(comment)`: nếu `grand_total < po_approval_threshold` → stage=Approved; else stage=Executive Review |
| 5b | (≥threshold) Executive click **"Lãnh đạo duyệt"** | `approve_as_executive(comment)` → stage=Approved |
| 6 | Click Submit (Ctrl+S → Submit) | `on_submit()` require stage=Approved. Set status=Approved → `_send_po_to_supplier()` gửi email NCC → status=Sent to Supplier, sent_to_supplier_at=now |
| 7 | NCC nhận email | Quy trình ngoài hệ thống |
| 8 | Trạng thái cuối: Sent to Supplier | Chờ confirm giao hàng (UC-09 PR) |

## Luồng thay thế

### 2a — Không có FC

User để trống `framework_contract` → nhập `rate` thủ công + upload `quotation_attachment`. `_validate_against_framework_contract` skip khi không có FC. `_check_price_variance` skip.

### 4a — Vượt hạn mức FC

`_validate_against_framework_contract` throw `SC-E002 FC_EXCEEDED` ngay khi save Draft → user phải:
- Tăng FC.total_value (gia hạn) — UC-04 luồng renewal
- Hoặc tạo FC mới
- Hoặc chia nhỏ PO

### 5/6/7a — Reject

`reject(reason)`:
- Validate reason reqd → else `SC-E-REJECT-REASON`
- Stage phải ∈ {Manager Review, Executive Review}
- Set stage=Rejected, lưu rejection_reason
- Notify creator (Accountant) qua email

## Hậu điều kiện

- PO `docstatus=1`, `status=Sent to Supplier`, `sent_to_supplier_at=now`
- FC `used_value` += grand_total, `remaining_value` -= grand_total
- Release Order (nếu có) → status=Converted, purchase_order=this PO
- Email gửi NCC (subject "PO {name} - SupplyCore", body with items table)
- Email gửi creator notify Approved

## Xử lý ngoại lệ

### NCC không phản hồi sau 3 ngày

Daily scheduler `supplycore.m2_planning.tasks.check_po_response`:
- Find PO status="Sent to Supplier" AND sent_to_supplier_at < today-3
- Send reminder email to NCC + log activity
- Skip nếu `supplier_confirmation_received=1`

### Giá NCC khác giá FC

Trong `validate()`:
- Mỗi row, nếu parent `framework_contract` set: lookup `fc_unit_price` từ FC Item.unit_price
- Set `row.fc_unit_price`, tính `row.price_variance_pct = (rate - fc_unit_price) / fc_unit_price × 100`
- Nếu |variance| > 1% → set `row.has_price_variance=1` + parent `has_price_variance=1`
- `msgprint` cam warning, không throw

## Field changes

### SC PO parent — ADD

| Field | Type | Note |
|---|---|---|
| `approval_stage` | Select `Draft\nManager Review\nExecutive Review\nApproved\nRejected` | default Draft |
| `manager_approved_by` | Link User | read_only |
| `manager_approved_at` | Datetime | read_only |
| `executive_approved_by` | Link User | read_only |
| `executive_approved_at` | Datetime | read_only |
| `rejection_reason` | Small Text | read_only, depends_on stage=Rejected |
| `delivery_terms` | Small Text | điều khoản giao hàng |
| `quotation_attachment` | Attach | báo giá khi không FC |
| `sent_to_supplier_at` | Datetime | read_only |
| `supplier_confirmation_received` | Check | default 0 |
| `has_price_variance` | Check | read_only, depends_on docstatus=0 |
| `last_reminder_sent_at` | Datetime | read_only, dedup reminder |

### SC PO Item child — ADD

| Field | Type | Note |
|---|---|---|
| `fc_unit_price` | Currency (VND) | read_only, set khi parent có FC |
| `price_variance_pct` | Percent | read_only, computed |
| `has_price_variance` | Check | read_only, set khi \|variance\|>1% |

### SC PO status options — KHÔNG đổi (đã có Sent to Supplier)

## Error codes mới

| Code | Trigger | Message |
|---|---|---|
| `SC-E-PO-NOT-APPROVED` | submit khi stage≠Approved | "PO phải Approved (qua workflow) trước khi submit" |
| `SC-E-PO-WRONG-STAGE` | approve_as_manager khi stage≠Manager Review | "PO không ở trạng thái Manager Review (hiện: {stage})" |
| `SC-E-PO-WRONG-STAGE-EXEC` | approve_as_executive khi stage≠Executive Review | "PO không ở trạng thái Executive Review (hiện: {stage})" |
| `SC-E-REJECT-REASON` | reject() không reason | "Phải nhập lý do từ chối" |
| `SC-E-PO-NO-SUPPLIER-EMAIL` | submit khi supplier không có email_id | "NCC không có email_id — không thể gửi PO" |

## Logic — `sc_purchase_order.py`

### Lifecycle

```python
def validate(self):
    self._compute_totals()
    self._validate_supplier()
    self._check_price_variance()     # NEW
    self._validate_against_framework_contract()
    if self.docstatus == 0 and not self.approval_stage:
        self.approval_stage = "Draft"
    if self.docstatus == 0:
        self.status = "Draft"

def before_submit(self):
    if self.approval_stage != "Approved":
        frappe.throw(_("SC-E-PO-NOT-APPROVED: PO phải Approved trước submit (hiện: {0})")
                     .format(self.approval_stage))
    supplier_email = frappe.db.get_value("SC Supplier", self.supplier, "email_id")
    if not supplier_email:
        frappe.throw(_("SC-E-PO-NO-SUPPLIER-EMAIL: NCC {0} không có email_id").format(self.supplier))

def on_submit(self):
    self.db_set("status", "Approved")
    self._update_framework_contract()
    self._send_po_to_supplier()     # NEW
    self.db_set("status", "Sent to Supplier")
    self.db_set("sent_to_supplier_at", frappe.utils.now())
```

### Workflow methods

```python
@frappe.whitelist()
def submit_for_review(self):
    if self.approval_stage not in ("Draft", "Rejected"):
        frappe.throw(_("Chỉ submit_for_review khi Draft/Rejected"))
    if self.docstatus != 0:
        frappe.throw(_("Phải Draft (chưa submit)"))
    self.db_set("approval_stage", "Manager Review")
    self.db_set("rejection_reason", None)
    return {"stage": "Manager Review"}

@frappe.whitelist()
def approve_as_manager(self, comment: str = None):
    if self.approval_stage != "Manager Review":
        frappe.throw(_("SC-E-PO-WRONG-STAGE: PO không ở Manager Review (hiện: {0})")
                     .format(self.approval_stage))
    threshold = flt(frappe.db.get_single_value("SupplyCore Settings", "po_approval_threshold") or 50_000_000)
    self.db_set("manager_approved_by", frappe.session.user)
    self.db_set("manager_approved_at", frappe.utils.now())
    if flt(self.grand_total) < threshold:
        self.db_set("approval_stage", "Approved")
    else:
        self.db_set("approval_stage", "Executive Review")
    return {"stage": self.approval_stage, "comment": comment}

@frappe.whitelist()
def approve_as_executive(self, comment: str = None):
    if self.approval_stage != "Executive Review":
        frappe.throw(_("SC-E-PO-WRONG-STAGE-EXEC: PO không ở Executive Review (hiện: {0})")
                     .format(self.approval_stage))
    self.db_set("executive_approved_by", frappe.session.user)
    self.db_set("executive_approved_at", frappe.utils.now())
    self.db_set("approval_stage", "Approved")
    return {"stage": "Approved", "comment": comment}

@frappe.whitelist()
def reject(self, reason: str = None):
    if not reason or not str(reason).strip():
        frappe.throw(_("SC-E-REJECT-REASON: Phải nhập lý do từ chối"))
    if self.approval_stage not in ("Manager Review", "Executive Review"):
        frappe.throw(_("Chỉ reject khi đang review (hiện: {0})").format(self.approval_stage))
    self.db_set("approval_stage", "Rejected")
    self.db_set("rejection_reason", reason)
    self._notify_creator_rejected(reason)
    return {"stage": "Rejected"}
```

### Helpers (new)

```python
def _check_price_variance(self):
    """Flag rows có rate ≠ FC unit_price ±1%."""
    if not self.framework_contract:
        return
    has_any = False
    for r in self.items:
        fc_price = self._get_fc_unit_price(self.framework_contract, r.item)
        if not fc_price:
            r.fc_unit_price = 0; r.price_variance_pct = 0; r.has_price_variance = 0
            continue
        r.fc_unit_price = fc_price
        if fc_price > 0:
            r.price_variance_pct = (flt(r.rate) - fc_price) / fc_price * 100
            r.has_price_variance = 1 if abs(r.price_variance_pct) > 1.0 else 0
            if r.has_price_variance:
                has_any = True
    self.has_price_variance = 1 if has_any else 0
    if has_any:
        frappe.msgprint(
            _("⚠ Một số item có giá lệch FC > 1% — cần xem xét"),
            indicator="orange", alert=True,
        )

@staticmethod
def _get_fc_unit_price(fc_name: str, item_code: str) -> float:
    r = frappe.db.sql("""
        SELECT unit_price FROM `tabFC Item`
        WHERE parent = %s AND item_code = %s LIMIT 1
    """, (fc_name, item_code))
    return flt(r[0][0]) if r else 0.0

def _send_po_to_supplier(self):
    email = frappe.db.get_value("SC Supplier", self.supplier, "email_id")
    if not email:
        return
    items_html = "".join(
        f"<tr><td>{r.item}</td><td>{r.qty}</td><td>{r.uom}</td>"
        f"<td>{frappe.format(r.rate, {'fieldtype':'Currency'})}</td>"
        f"<td>{frappe.format(r.amount, {'fieldtype':'Currency'})}</td></tr>"
        for r in self.items
    )
    msg = f"""
        <p>Kính gửi {self.supplier_name},</p>
        <p>Bệnh viện đặt hàng theo PO <b>{self.name}</b>:</p>
        <table border="1" cellpadding="6" cellspacing="0">
            <tr><th>Mã VT</th><th>SL</th><th>UOM</th><th>Đơn giá</th><th>Thành tiền</th></tr>
            {items_html}
        </table>
        <p><b>Tổng:</b> {frappe.format(self.grand_total, {'fieldtype':'Currency'})}</p>
        <p><b>Ngày giao dự kiến:</b> {self.schedule_date}</p>
        <p><b>Điều khoản giao hàng:</b> {self.delivery_terms or '—'}</p>
        <p><b>Điều khoản thanh toán:</b> {self.payment_terms or '—'}</p>
        <p>Vui lòng xác nhận đơn hàng trong vòng 3 ngày làm việc.</p>
    """
    try:
        frappe.sendmail(
            recipients=[email],
            subject=f"[SupplyCore] Purchase Order {self.name}",
            message=msg,
            delayed=False,
        )
    except Exception as e:
        frappe.log_error(message=str(e)[:1000], title="UC-08 _send_po_to_supplier")

def _notify_creator_rejected(self, reason: str):
    if not self.owner or self.owner in ("Administrator", "Guest"):
        return
    body = (f"<p>PO <a href='/app/sc-purchase-order/{self.name}'>{self.name}</a> "
            f"đã bị <b>từ chối</b>.</p>"
            f"<p><b>Lý do:</b> {frappe.utils.escape_html(reason)}</p>")
    try:
        frappe.sendmail(
            recipients=[self.owner],
            subject=f"[SupplyCore] PO {self.name} bị từ chối",
            message=body, delayed=False,
        )
    except Exception as e:
        frappe.log_error(message=str(e)[:1000], title="UC-08 _notify_creator_rejected")
```

## Scheduler — `m2_planning/tasks.py`

```python
def check_po_response():
    """Daily (UC-08 ngoại lệ): nhắc NCC nếu PO Sent to Supplier > 3 ngày không phản hồi."""
    days = int(frappe.db.get_single_value("SupplyCore Settings", "po_response_reminder_days") or 3)
    rows = frappe.db.sql("""
        SELECT po.name, po.supplier, po.supplier_name, po.sent_to_supplier_at,
               po.last_reminder_sent_at, s.email_id
        FROM `tabSC Purchase Order` po
        JOIN `tabSC Supplier` s ON s.name = po.supplier
        WHERE po.docstatus = 1
          AND po.status = 'Sent to Supplier'
          AND COALESCE(po.supplier_confirmation_received, 0) = 0
          AND DATEDIFF(NOW(), po.sent_to_supplier_at) >= %s
          AND s.email_id IS NOT NULL AND s.email_id != ''
          AND (
              po.last_reminder_sent_at IS NULL
              OR DATEDIFF(NOW(), po.last_reminder_sent_at) >= %s
          )
        LIMIT 100
    """, (days, days), as_dict=True)

    sent = 0
    for po in rows:
        try:
            frappe.sendmail(
                recipients=[po.email_id],
                subject=f"[SupplyCore] Nhắc nhở PO {po.name} chờ xác nhận",
                message=(f"<p>Kính gửi {po.supplier_name},</p>"
                         f"<p>PO <b>{po.name}</b> đã gửi {po.sent_to_supplier_at} chưa nhận được xác nhận. "
                         f"Vui lòng phản hồi sớm nhất.</p>"),
                delayed=False,
            )
            frappe.db.set_value("SC Purchase Order", po.name,
                                 "last_reminder_sent_at", frappe.utils.now())
            sent += 1
        except Exception as e:
            frappe.log_error(message=f"po={po.name}: {str(e)[:500]}",
                              title="UC-08 check_po_response")
    frappe.db.commit()
    return {"reminders_sent": sent}
```

Đăng ký trong `hooks.py.scheduler_events.daily`.

## Settings field mới

Trong `supplycore_settings.json` add:
```json
{"fieldname": "po_response_reminder_days", "fieldtype": "Int",
 "label": "Nhắc NCC sau (ngày)", "default": "3",
 "description": "PO Sent to Supplier quá X ngày chưa confirm → email reminder"}
```

## Migration

- Tất cả field mới Frappe tự migrate
- Không cần patch riêng

## Test plan — `tests/uc08_test.py`

| Test | Scenario |
|---|---|
| `test_submit_blocked_when_not_approved` | docstatus 0 + stage=Draft → submit → SC-E-PO-NOT-APPROVED |
| `test_workflow_below_threshold_manager_only` | grand_total=10tr → submit_for_review → approve_as_manager → stage=Approved (skip Executive) |
| `test_workflow_above_threshold_two_tier` | grand_total=100tr → submit_for_review → approve_as_manager → stage=Executive Review → approve_as_executive → Approved |
| `test_reject_requires_reason` | reject() no reason → SC-E-REJECT-REASON |
| `test_reject_in_manager_review` | reject() at Manager Review → stage=Rejected + rejection_reason set |
| `test_submit_sends_email_and_status_sent` | full flow approve → submit → status=Sent to Supplier + sent_to_supplier_at set |
| `test_submit_blocked_no_supplier_email` | supplier không có email_id + submit → SC-E-PO-NO-SUPPLIER-EMAIL |
| `test_fc_exceeded_blocks` | grand_total > FC.remaining_value → SC-E002 FC_EXCEEDED |
| `test_price_variance_flagged` | row.rate ≠ fc_unit_price > 1% → row.has_price_variance=1, parent.has_price_variance=1 |
| `test_check_po_response_sends_reminder` | PO Sent > 3 ngày không confirm → scheduler send reminder + set last_reminder_sent_at |

## Out-of-scope (KHÔNG làm)

- Supplier Quotation doctype mới (covered bằng `quotation_attachment`)
- UI button trên form (defer JS — method whitelisted đủ)
- PDF render PO trong email (text only)
- NCC confirm qua portal/API (chỉ check manual qua field supplier_confirmation_received)

## File changes

1. `supplycore/m2_planning/UC-08_FLOW.md` — this file
2. `supplycore/supplycore/doctype/sc_purchase_order/sc_purchase_order.json` — 12 fields parent
3. `supplycore/supplycore/doctype/sc_purchase_order_item/sc_purchase_order_item.json` — 3 fields child
4. `supplycore/supplycore/doctype/sc_purchase_order/sc_purchase_order.py` — workflow methods + email + price variance
5. `supplycore/supplycore/doctype/supplycore_settings/supplycore_settings.json` — `po_response_reminder_days` field
6. `supplycore/m2_planning/tasks.py` — `check_po_response()` scheduler
7. `supplycore/hooks.py` — register scheduler in daily
8. `supplycore/tests/uc08_test.py` — 10 test scenarios
