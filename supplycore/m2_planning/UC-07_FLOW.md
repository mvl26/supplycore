# UC-07 — Tạo Material Request (Phiếu Đề Nghị Mua Hàng) — Flow & Implementation

**Module:** M2 Planning (UC) + Supplycore (DocType `SC Material Request` host)
**DocType:** SC Material Request (parent) + SC Material Request Item (child)
**Date:** 2026-05-11
**Source:** Phase 1 / UseCase_SupplyCore_v2.0.md UC-07
**Lưu ý:** dùng SC * doctypes mới (no-ERPNext shift 2026-05-07).

## Actor

- Thủ kho (SupplyCore Storekeeper)
- Nhân viên khoa phòng (SupplyCore Ward Staff)
- Quản lý (SupplyCore Manager) — duyệt/từ chối
- Kế toán (SupplyCore Accountant) — tạo PO sau duyệt

## Pre-condition

- User đã login
- Vật tư cần mua đã có trong SC Item
- Vật tư có ít nhất 1 NCC (default_supplier hoặc thuộc supplied_item_groups của 1 SC Supplier active hoặc có FC active) — nếu KHÔNG → block submit

## Luồng chính

| Bước | User | Hệ thống |
|---|---|---|
| 1 | Mở `/app/sc-material-request/new`, chọn `request_type`: `Purchase` (Mua hàng) hoặc `Urgent` (Đột xuất) | Form Draft |
| 2 | Thêm row item: chọn `item`, nhập `qty`, `uom` | `fetch_from` auto-fill `item_name` |
| 3 | Nhập `reason` (lý do đề nghị) + `schedule_date` (ngày cần giao) | Field optional cho reason, bắt buộc cho schedule_date |
| 4 | (Optional) Trên row chọn `framework_contract` | `validate()` auto-fetch `estimated_unit_cost` = unit_price từ Framework Contract Item khớp `item` |
| 5 | Submit (Ctrl+S → Submit) | `validate()` chạy guards (qty>0, schedule≥transaction, NCC check). `on_submit()` set `status=Pending`. `_notify_managers()` gửi email SupplyCore Manager |
| 6 | Manager mở MR, click **"Duyệt"** hoặc **"Từ chối"** | Method `approve()` → status=Approved + notify owner. Method `reject(reason)` → status=Rejected + lưu `rejection_reason` + notify owner |
| 7 | Sau Approved, Accountant click **"Tạo Purchase Order"** | `create_purchase_orders()` đã có (suggest theo FC, group theo supplier) |

## Luồng thay thế

### 1a — Tồn kho ≤ Reorder Level (auto-tạo Draft MR)

Daily scheduler `supplycore.m2_planning.tasks.check_reorder_levels` (đăng ký trong `hooks.py.scheduler_events.daily`):

1. Enumerate cặp (item, warehouse) có `reorder_level > 0`:
   - Per-warehouse override rows (SC Item Reorder)
   - Item-level (SC Item) cho mọi warehouse có SLE
2. Mỗi cặp: tính `current_qty` = SUM(SLE.qty_change). Nếu `current ≤ reorder_level` → ứng viên.
3. Group ứng viên theo warehouse: tạo 1 Draft MR / warehouse với:
   - `request_type=Purchase`, `auto_generated=1`, `transaction_date=today`, `schedule_date=today+14`
   - Items: qty = `standard_order_qty` (nếu set) else `max_stock - current` else `reorder*2 - current`
4. Dedup: skip warehouse đã có Draft auto_generated MR cùng `transaction_date=today`
5. Skip items không có NCC (log warning, không fail task)
6. Email summary cho Storekeeper/Manager (full danh sách + link Draft MR vừa tạo)

Helpers: `_find_reorder_candidates()`, `_get_current_qty()`, `_compute_qty()`, `_create_reorder_mr()`, `_send_reorder_summary()` — all in `m2_planning/tasks.py`.

User sau khi nhận email mở Draft MR → review qty → Submit → workflow chính tiếp tục từ bước 5.

### 6a — Từ chối

`reject(reason)`:
- Validate `reason` reqd
- Set `status="Rejected"`, lưu `rejection_reason`
- Email owner: subject "MR {name} đã bị từ chối", body include reason
- Block tạo PO khi status≠Approved

## Hậu điều kiện

- MR `docstatus=1`, `status` ∈ {Pending, Approved, Rejected, Ordered, Received, Cancelled}
- Khi Approved: `create_purchase_orders()` callable
- `track_changes=1` audit toàn bộ

## Xử lý ngoại lệ

- **Vật tư không có NCC** (chỉ áp dụng `request_type ∈ {Purchase, Urgent}`):
  - Check mỗi item: `SC Item.default_supplier` OR exists Framework Contract Item active liên kết item OR exists SC Supplier có item_group khớp item.item_group qua supplied_item_groups
  - Không có → throw `SC-E-NO-SUPPLIER: Vật tư {item} chưa có NCC. Vui lòng cấu hình NCC trước khi đề nghị mua.`
- **qty ≤ 0** → throw `SC-E-QTY: Số lượng phải > 0`
- **schedule_date < transaction_date** → throw `SC-E-DATE: Ngày cần phải ≥ ngày yêu cầu`

## Field changes

### SC Material Request parent

| Field | Type | Action | Note |
|---|---|---|---|
| `reason` | Small Text | **ADD** | Lý do đề nghị, optional |
| `rejection_reason` | Small Text | **ADD** | read_only, set khi reject |
| `status` options | Select | **MODIFY** | Thêm `Rejected` vào options: `Draft\nPending\nApproved\nRejected\nOrdered\nReceived\nCancelled` |

### SC Material Request Item child

| Field | Type | Action | Note |
|---|---|---|---|
| `framework_contract` | Link `Framework Contract` | **ADD** | Optional, fetch unit_price từ FC |

## Error codes

| Code | Trigger | Message |
|---|---|---|
| `SC-E-QTY` | row.qty ≤ 0 | "Số lượng phải > 0" |
| `SC-E-DATE` | schedule_date < transaction_date | "Ngày cần phải ≥ ngày yêu cầu" |
| `SC-E-NO-SUPPLIER` | Purchase/Urgent + item không có NCC | "Vật tư {item} chưa có NCC. Vui lòng cấu hình NCC trước khi đề nghị mua." |
| `SC-E-MR-NOT-APPROVED` | create_purchase_orders khi status≠Approved | "MR phải Approved trước khi tạo PO" |
| `SC-E-REJECT-REASON` | reject() không có reason | "Phải nhập lý do từ chối" |

## Logic changes — `sc_material_request.py`

### `validate()` (extend)

```python
def validate(self):
    total_qty = 0; total = 0
    for r in self.items:
        if flt(r.qty) <= 0:
            frappe.throw(_("SC-E-QTY: Số lượng phải > 0 (item {0})").format(r.item))
        # UC-07: auto-fetch unit_cost từ FC nếu có set
        if r.framework_contract:
            fc_price = self._get_fc_price(r.framework_contract, r.item)
            if fc_price > 0:
                r.estimated_unit_cost = fc_price
        r.estimated_amount = flt(r.qty) * flt(r.estimated_unit_cost)
        total_qty += flt(r.qty); total += flt(r.estimated_amount)
    self.total_qty = total_qty
    self.total_estimated_cost = total

    # UC-07: schedule >= transaction
    if self.schedule_date and self.transaction_date:
        from frappe.utils import getdate
        if getdate(self.schedule_date) < getdate(self.transaction_date):
            frappe.throw(_("SC-E-DATE: Ngày cần phải ≥ ngày yêu cầu"))

    # UC-07: NCC check cho Purchase/Urgent
    if self.request_type in ("Purchase", "Urgent"):
        self._validate_suppliers()

    if self.docstatus == 0:
        self.status = "Draft"
```

### `on_submit()` (replace)

```python
def on_submit(self):
    """UC-07: submit → Pending (chờ duyệt). KHÔNG auto-approve."""
    self.db_set("status", "Pending")
    self._notify_managers()
```

### New methods

```python
@frappe.whitelist()
def approve(self):
    """Manager duyệt MR."""
    if self.docstatus != 1:
        frappe.throw(_("Phải submit trước khi duyệt"))
    if self.status != "Pending":
        frappe.throw(_("MR không ở trạng thái Pending (hiện: {0})").format(self.status))
    self.db_set("status", "Approved")
    self._notify_owner("Approved")
    return {"status": "Approved"}

@frappe.whitelist()
def reject(self, reason: str):
    if not reason:
        frappe.throw(_("SC-E-REJECT-REASON: Phải nhập lý do từ chối"))
    if self.docstatus != 1:
        frappe.throw(_("Phải submit trước khi reject"))
    if self.status != "Pending":
        frappe.throw(_("MR không ở trạng thái Pending (hiện: {0})").format(self.status))
    self.db_set("status", "Rejected")
    self.db_set("rejection_reason", reason)
    self._notify_owner("Rejected", reason=reason)
    return {"status": "Rejected"}
```

### Helpers

```python
@staticmethod
def _get_fc_price(fc_name: str, item_code: str) -> float:
    """Lookup unit_price từ Framework Contract Item."""
    result = frappe.db.sql("""
        SELECT unit_price FROM `tabFramework Contract Item`
        WHERE parent = %s AND item_code = %s
        LIMIT 1
    """, (fc_name, item_code))
    return flt(result[0][0]) if result else 0.0

def _validate_suppliers(self):
    """UC-07: mỗi item phải có ít nhất 1 NCC khả dụng."""
    for r in self.items:
        if not self._item_has_supplier(r.item):
            frappe.throw(_(
                "SC-E-NO-SUPPLIER: Vật tư {0} chưa có NCC. "
                "Vui lòng cấu hình NCC trước khi đề nghị mua."
            ).format(r.item))

@staticmethod
def _item_has_supplier(item_code: str) -> bool:
    # Check 1: default_supplier
    if frappe.db.get_value("SC Item", item_code, "default_supplier"):
        return True
    # Check 2: active FC có item
    fc_exists = frappe.db.sql("""
        SELECT 1 FROM `tabFramework Contract Item` fci
        JOIN `tabFramework Contract` fc ON fc.name = fci.parent
        WHERE fci.item_code = %s AND fc.docstatus = 1 AND fc.status = 'Active'
        LIMIT 1
    """, item_code)
    if fc_exists:
        return True
    # Check 3: supplier có item_group khớp (qua SC Supplier Item Group child)
    item_group = frappe.db.get_value("SC Item", item_code, "item_group")
    if item_group:
        sg = frappe.db.sql("""
            SELECT 1 FROM `tabSC Supplier Item Group` sg
            JOIN `tabSC Supplier` s ON s.name = sg.parent
            WHERE sg.item_group = %s AND s.disabled = 0 AND s.blacklist_flag = 0
            LIMIT 1
        """, item_group)
        if sg:
            return True
    return False

def _notify_managers(self):
    recipients = self._get_recipients_by_role("SupplyCore Manager")
    if not recipients:
        return
    try:
        frappe.sendmail(
            recipients=recipients,
            subject=f"[SupplyCore] MR {self.name} chờ duyệt",
            message=f"<p>MR <a href='/app/sc-material-request/{self.name}'>{self.name}</a> "
                    f"({self.request_type}) chờ phê duyệt.</p>"
                    f"<p>Tổng: {frappe.format(self.total_estimated_cost, {'fieldtype':'Currency'})}</p>",
            delayed=False,
        )
    except Exception as e:
        frappe.log_error(message=str(e)[:1000], title="UC-07 _notify_managers")

def _notify_owner(self, status: str, reason: str = None):
    if not self.owner or self.owner in ("Administrator", "Guest"):
        return
    body = f"<p>MR <a href='/app/sc-material-request/{self.name}'>{self.name}</a> đã được {status}.</p>"
    if reason:
        body += f"<p><b>Lý do:</b> {frappe.utils.escape_html(reason)}</p>"
    try:
        frappe.sendmail(
            recipients=[self.owner],
            subject=f"[SupplyCore] MR {self.name} {status}",
            message=body,
            delayed=False,
        )
    except Exception as e:
        frappe.log_error(message=str(e)[:1000], title="UC-07 _notify_owner")

@staticmethod
def _get_recipients_by_role(role: str) -> list:
    return frappe.db.sql_list("""
        SELECT DISTINCT u.email FROM `tabUser` u
        JOIN `tabHas Role` r ON r.parent = u.name
        WHERE r.role = %s AND u.enabled = 1 AND u.email IS NOT NULL AND u.email != ''
    """, role) or []
```

### Gate create_purchase_orders

```python
@frappe.whitelist()
def create_purchase_orders(self):
    if self.status != "Approved":
        frappe.throw(_("SC-E-MR-NOT-APPROVED: MR phải Approved trước khi tạo PO (hiện: {0})").format(self.status))
    from supplycore.m2_planning.api.po_suggest import suggest_po_from_mr
    return suggest_po_from_mr(self.name, auto_create=1)
```

## Migration

- 3 field mới (reason, rejection_reason parent + framework_contract child) Frappe tự migrate
- Status option `Rejected` thêm vào select — Frappe migrate cập nhật

## Test plan — `supplycore/tests/uc07_test.py`

| Test | Scenario |
|---|---|
| `test_qty_zero_rejected` | row qty=0 → throw SC-E-QTY |
| `test_schedule_before_transaction_rejected` | schedule_date < transaction → throw SC-E-DATE |
| `test_no_supplier_purchase_rejected` | request_type=Purchase, item không có NCC → throw SC-E-NO-SUPPLIER |
| `test_no_supplier_internal_transfer_ok` | request_type=Internal Transfer, không cần NCC → save OK |
| `test_submit_goes_to_pending` | submit MR → status=Pending (không phải Approved) |
| `test_approve_changes_status` | submit → approve() → status=Approved |
| `test_reject_requires_reason` | reject() không reason → SC-E-REJECT-REASON |
| `test_reject_with_reason_ok` | reject("lý do") → status=Rejected + rejection_reason populated |
| `test_create_po_blocked_when_pending` | submit (Pending) + create_purchase_orders → SC-E-MR-NOT-APPROVED |
| `test_auto_create_mr_when_below_reorder` | item tồn ≤ reorder + run check_reorder_levels → Draft MR auto-tạo với qty=standard_order_qty |
| `test_fc_price_auto_fetched` | row.framework_contract set → estimated_unit_cost = FC unit_price |

## Out-of-scope (KHÔNG làm trong UC-07)

- UI button "Duyệt"/"Từ chối" trên form (JS — defer; method whitelisted đủ)
- Workflow approver tier (Manager vs Executive) — chỉ 1 Manager role
- In-app realtime notification (chỉ email)
- Auto-link FC khi user chọn item (UX nice-to-have, defer)

## File changes

1. `supplycore/m2_planning/UC-07_FLOW.md` — this file
2. `supplycore/supplycore/doctype/sc_material_request/sc_material_request.json` — 2 fields + status options
3. `supplycore/supplycore/doctype/sc_material_request_item/sc_material_request_item.json` — `framework_contract` field
4. `supplycore/supplycore/doctype/sc_material_request/sc_material_request.py` — validate guards + on_submit Pending + approve/reject + helpers + gate PO
5. `supplycore/m2_planning/tasks.py` — rewrite `check_reorder_levels` dùng SC * doctypes + auto-tạo Draft MR (UC-07 luồng 1a)
6. `supplycore/tests/uc07_test.py` — 11 test scenarios
