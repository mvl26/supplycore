# UC-10 — Kiểm tra Chất lượng (QC) Hàng nhập — Flow & Implementation

**Module:** M3 Receiving
**DocType:** SC Quality Inspection + SC QI Reading + QC Checklist Template
**Date:** 2026-05-11
**Source:** Phase 1 / UseCase_SupplyCore_v2.0.md UC-10

## Audit hiện trạng (trước UC-10)

| Spec line | Trước | Sau UC-10 |
|---|---|---|
| 1. QI từ PR | ✓ auto-create trên PR.on_submit | ✓ |
| 2. Checklist theo loại VT | ✓ `QC Checklist Template` per `item_group` | ✓ + seed default template với 5 tiêu chí spec |
| 3. 5 tiêu chí cụ thể | Cấu hình động | ✓ seed default global template |
| 4. Đạt/Không đạt | ✓ row.status Accepted/Rejected | ✓ |
| 5. All Đạt → QC Pass + nhập kho chính thức | Partial: qc_status=Pass; FEFO không lọc qc_status nên hàng Pending vẫn pick được | ✓ thêm filter FEFO + flag `officially_received_at` trên PR |
| 6. Tiêu chí Fail → 3 lựa chọn | Partial: `action_taken` 3 options khác wording (Accept/Conditional Accept/Return to Supplier) | ✓ rename options match spec + add "Request Replacement" |
| 5a. PR sang "Đã nhập kho" | Implicit qua qc_status=Pass | ✓ field `officially_received_at` |
| 6a. Trả hàng → Supplier Return | ✓ `_create_return_pr()` | ✓ |
| Ngoại lệ: Thiếu thiết bị → "Chờ xử lý" | ✗ | ✓ `equipment_unavailable` Check + state `On Hold` |

## Actor

- Thủ kho (Storekeeper) / QC Officer / Manager

## Pre-condition

- SC Purchase Receipt đã submitted với `qc_required=1`
- QI auto-tạo, ở `overall_status=Pending`

## Luồng chính

| Bước | User | Hệ thống |
|---|---|---|
| 1 | Mở `/app/sc-quality-inspection/<QI>` (mở từ PR hoặc list) | Form load checklist template (default cho item_group) |
| 2 | Hệ thống hiển thị `readings` checklist theo template | Auto-rendered từ `QC Checklist Template.criteria` khi QI auto-created |
| 3 | Kiểm tra từng tiêu chí trong default template:<br>• Bao bì nguyên vẹn<br>• Nhãn mác đúng<br>• Hạn dùng ≥6 tháng<br>• Số lô khớp chứng từ<br>• Quy cách đúng hợp đồng | Template seed sẵn qua patch |
| 4 | Set `status` (Accepted/Rejected) cho từng row + `value` đo (nếu có) + `remarks` | – |
| 5 | (All Accepted) → Save → Submit | `validate()` auto-set `overall_status=Accepted`. `on_submit()`: rollup `PR.qc_status=Pass` + set `PR.officially_received_at=now`. Batch.qc_status=Accepted. FEFO bắt đầu cho phép pick batch này. |
| 6 | (Có Rejected) → chọn `action_taken`: `Return to Supplier` / `Request Replacement` / `Conditional Accept` | Submit → `_handle_rejected()`: nếu Return → tạo Draft Return PR; Conditional → batch.qc_status=Conditional (vẫn issuable); Request Replacement → batch.blocked=1 + log |

## Luồng thay thế

### 5a — QC Pass

`on_submit` set `PR.officially_received_at = now`. FEFO/Dispense respect `Batch.qc_status IN ('Accepted', 'Conditional')`, block `Pending` + `Rejected`.

### 6a — Trả hàng (Return to Supplier)

`_create_return_pr()` tạo Draft `SC Purchase Receipt` với `is_return=1`. ACC review + submit → SLE -qty (giảm tồn) + `batch.blocked=1`.

## Xử lý ngoại lệ

### Thiếu thiết bị kiểm tra

- User tick `equipment_unavailable=1` + nhập `equipment_note`
- `validate()` set `overall_status=On Hold` (override auto-derive)
- `on_submit()` skip rollup + skip _handle_rejected — chỉ lưu trạng thái On Hold
- PR.qc_status không update — vẫn Pending
- Manager re-open QI sau khi có thiết bị → uncheck `equipment_unavailable` → set readings → resubmit

## Field changes

### SC Quality Inspection — ADD/MODIFY

| Field | Action | Note |
|---|---|---|
| `overall_status` | MODIFY options | Thêm `On Hold` |
| `action_taken` | MODIFY options | Đổi options theo spec: `Pending\nAccept\nConditional Accept\nReturn to Supplier\nRequest Replacement` |
| `equipment_unavailable` | ADD Check | flag thiếu thiết bị |
| `equipment_note` | ADD Small Text | ghi chú khi On Hold |
| `supplier` | ADD Link `SC Supplier` read_only | NCC của lô hàng — `fetch_from purchase_receipt.supplier`; `_auto_create_qi` gán sẵn `qi.supplier = pr.supplier` để phần kiểm tra QC hiển thị nhà cung cấp (2026-05-21) |

### SC Purchase Receipt — ADD

| Field | Action | Note |
|---|---|---|
| `officially_received_at` | ADD Datetime read_only | set khi QI Accept rollup → PR.qc_status=Pass |

### FEFO `get_suggested_batches` — MODIFY

Thêm filter `(b.qc_status IS NULL OR b.qc_status IN ('Accepted', 'Conditional'))` để skip Pending + Rejected.

## Error codes mới

| Code | Trigger | Message |
|---|---|---|
| `SC-E-QI-ONHOLD` | submit QI có equipment_unavailable=1 mà không có equipment_note | "Phải nhập 'Ghi chú thiết bị' khi đánh dấu thiếu thiết bị" |
| `SC-E-QI-READINGS` | submit không có reading nào set status | "Phải nhập kết quả cho ít nhất 1 tiêu chí trước khi submit" |

## Logic — `sc_quality_inspection.py`

### Validate (extend)

```python
def validate(self):
    # UC-10: equipment unavailable → On Hold
    if self.equipment_unavailable:
        if not (self.equipment_note and str(self.equipment_note).strip()):
            frappe.throw(_(
                "SC-E-QI-ONHOLD: Phải nhập 'Ghi chú thiết bị' khi đánh dấu thiếu thiết bị"
            ))
        self.overall_status = "On Hold"
        return  # skip auto-derive

    # Auto-derive overall_status từ readings
    if self.readings:
        statuses = [r.status for r in self.readings if r.status]
        if not self.overall_status or self.overall_status == "Pending":
            if any(s == "Rejected" for s in statuses):
                self.overall_status = "Rejected"
            elif all(s == "Accepted" for s in statuses) and len(statuses) == len(self.readings):
                self.overall_status = "Accepted"
```

### before_submit (new)

```python
def before_submit(self):
    if self.equipment_unavailable:
        # On Hold submit OK — skip readings check
        return
    if not self.readings:
        frappe.throw(_("SC-E-QI-READINGS: Phải nhập kết quả cho ít nhất 1 tiêu chí trước khi submit"))
    set_count = sum(1 for r in self.readings if r.status)
    if set_count == 0:
        frappe.throw(_("SC-E-QI-READINGS: Phải nhập kết quả cho ít nhất 1 tiêu chí trước khi submit"))
```

### on_submit (extend)

```python
def on_submit(self):
    # UC-10: On Hold → skip mọi rollup, chỉ lưu trạng thái
    if self.overall_status == "On Hold":
        return

    # Update Batch.qc_status
    if self.batch:
        new_qc = "Accepted" if self.overall_status == "Accepted" else (
            "Rejected" if self.overall_status == "Rejected" else "Conditional")
        frappe.db.set_value("SC Batch", self.batch, "qc_status", new_qc)

    # Rollup PR.qc_status
    if self.purchase_receipt:
        self._rollup_pr_status()
        if self.overall_status == "Rejected":
            self._handle_rejected()
        if self.overall_status == "Accepted" and self.action_taken == "Conditional Accept":
            # Conditional: batch qc_status đã set Conditional ở trên, không tạo return
            pass

    # UC-10: action Request Replacement → block batch + ghi log
    if self.action_taken == "Request Replacement" and self.batch:
        frappe.db.set_value("SC Batch", self.batch, {
            "blocked": 1,
            "block_reason": f"QI {self.name} Request Replacement: {self.failure_reason or '—'}",
        })
```

### _rollup_pr_status (extend — set officially_received_at)

```python
def _rollup_pr_status(self):
    pr = frappe.get_doc("SC Purchase Receipt", self.purchase_receipt)
    qis = frappe.get_all("SC Quality Inspection",
                          filters={"purchase_receipt": pr.name},
                          fields=["name", "overall_status", "docstatus"])
    submitted = [q for q in qis if q.docstatus == 1 and q.overall_status != "On Hold"]
    expected = len(pr.items)
    if len(submitted) < expected:
        new_status = "Pending"
    elif all(q.overall_status == "Accepted" for q in submitted):
        new_status = "Pass"
    elif all(q.overall_status == "Rejected" for q in submitted):
        new_status = "Fail"
    else:
        new_status = "Partial Pass"
    frappe.db.set_value("SC Purchase Receipt", pr.name, "qc_status", new_status)
    if new_status == "Pass":
        frappe.db.set_value("SC Purchase Receipt", pr.name,
                             "officially_received_at", frappe.utils.now())
```

## FEFO patch — `supplycore/api/fefo.py`

Trong query `get_suggested_batches`, sửa WHERE:

```sql
WHERE b.item = %(item)s
  AND b.disabled = 0
  AND COALESCE(b.blocked, 0) = 0
  AND (b.expiry_date IS NULL OR b.expiry_date >= CURDATE())
  AND (b.qc_status IS NULL OR b.qc_status = '' OR b.qc_status IN ('Accepted', 'Conditional'))
```

## Default Template Seed

Patch `supplycore/patches/v0_2/seed_uc10_default_qc_template.py`:

```python
import frappe

def execute():
    name = "Default Hospital Supply QC"
    if frappe.db.exists("QC Checklist Template", {"title": name}):
        return
    tpl = frappe.new_doc("QC Checklist Template")
    tpl.title = name
    tpl.item_group = None  # global fallback
    tpl.is_default_for_group = 0
    tpl.enabled = 1
    tpl.description = "Default template UC-10 — 5 tiêu chí QC cơ bản"
    criteria = [
        ("Bao bì nguyên vẹn", "Không rách, hỏng, bóp méo", 1),
        ("Nhãn mác đúng", "Tên VT, số lô, hạn dùng đầy đủ rõ ràng", 1),
        ("Hạn dùng ≥6 tháng", "Hạn dùng còn ≥180 ngày kể từ ngày nhập", 1),
        ("Số lô khớp chứng từ", "Số lô trên hàng = số lô trên phiếu giao", 1),
        ("Quy cách đúng hợp đồng", "Đúng đặc tả + đơn vị + đóng gói theo PO/FC", 0),
    ]
    for i, (n, exp, crit) in enumerate(criteria, 1):
        tpl.append("criteria", {
            "criterion_name": n, "expected_value": exp,
            "is_critical": crit, "sequence": i,
        })
    tpl.flags.ignore_permissions = True
    tpl.insert()
```

Đăng ký trong `supplycore/patches.txt`.

## Migration

- Field mới tự migrate
- Patch seed template chạy 1 lần qua `bench migrate`

## Test plan — `tests/uc10_test.py`

| Test | Scenario |
|---|---|
| `test_default_template_exists_after_migrate` | Patch chạy → QC Checklist Template "Default Hospital Supply QC" tồn tại với 5 criteria |
| `test_qi_auto_created_from_pr` | PR submit + qc_required=1 → QI auto-tạo per item |
| `test_qi_all_accepted_sets_pr_pass` | QI all readings Accepted → submit → PR.qc_status=Pass + officially_received_at set |
| `test_qi_any_rejected_sets_pr_fail` | QI có 1 reading Rejected → overall=Rejected → PR.qc_status=Fail + batch.blocked + Return PR auto-tạo |
| `test_qi_equipment_unavailable_onhold` | tick equipment_unavailable + note → submit → overall=On Hold, PR.qc_status không đổi |
| `test_qi_equipment_unavailable_requires_note` | tick equipment_unavailable không note → validate throw SC-E-QI-ONHOLD |
| `test_qi_empty_readings_blocks_submit` | submit không readings → SC-E-QI-READINGS |
| `test_qi_conditional_accept_batch_conditional` | overall=Accepted + action=Conditional Accept → batch.qc_status=Conditional |
| `test_qi_request_replacement_blocks_batch` | action=Request Replacement → batch.blocked=1 với reason |
| `test_fefo_skips_pending_qc_batch` | Batch qc_status=Pending → get_suggested_batches không trả batch đó |
| `test_fefo_includes_accepted_batch` | Batch qc_status=Accepted → batch xuất hiện trong FEFO |
| `test_fefo_includes_conditional_batch` | Batch qc_status=Conditional → batch xuất hiện trong FEFO |

## Out-of-scope

- UI workflow buttons (defer JS)
- Multi-QI per (PR, item) tracking (giữ 1-1)
- QC photo evidence upload (defer — chỉ có Attach trên Reading.remarks nếu cần Phase 2)
- Auto-email NCC khi Reject (đã có gián tiếp qua _create_return_pr)

## File changes

1. `supplycore/m3_receiving/UC-10_FLOW.md` — this file
2. `supplycore/supplycore/doctype/sc_quality_inspection/sc_quality_inspection.json` — 2 new fields + modify status options
3. `supplycore/supplycore/doctype/sc_quality_inspection/sc_quality_inspection.py` — equipment handling + Conditional + Request Replacement
4. `supplycore/supplycore/doctype/sc_purchase_receipt/sc_purchase_receipt.json` — `officially_received_at` field
5. `supplycore/api/fefo.py` — qc_status filter
6. `supplycore/patches/v0_2/seed_uc10_default_qc_template.py` — NEW patch
7. `supplycore/patches.txt` — register patch
8. `supplycore/tests/uc10_test.py` — 12 test scenarios
