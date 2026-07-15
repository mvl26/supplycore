# UC-30 — Thu hồi Vật tư (Recall Management) — Flow & Implementation

**Module:** M10 Traceability
**DocType chính:** SC Recall Notice (`SC-RCL-{YYYY}-{#####}`)
**Date:** 2026-05-11
**Source:** Phase 1 / UseCase_SupplyCore_v2.0.md UC-30

## Audit hiện trạng vs UC-30

| Spec | Trước UC-30 | Sau UC-30 |
|---|---|---|
| 1. Quản lý tạo Recall Notice (lý do, batch) | ✓ DocType + UI | ✓ |
| 2. Auto truy xuất batch liên quan | ✓ `populate_affected_items()` | ✓ + integrate UC-29 `get_batch_trace` |
| 3. Hiển thị Còn kho + Đã cấp khoa nào | ✓ qua affected_items | ✓ + group_by_department |
| 4. **Block tất cả giao dịch của batch** | ⚠ chỉ SC Stock Entry FEFO check, PD không check | ✓ thêm check ở Patient Dispensing; bypass cho recall_notice-driven SE |
| 5. **In phiếu gửi từng khoa** | ✗ | ✓ `get_department_recall_letter()` + Frappe Print Format |
| 6. **Theo dõi tình trạng thu hồi** | ⚠ field có nhưng không API | ✓ `update_recovery(row, recovered_qty, destroyed_qty, status)` |
| 7. **Tạo phiếu trả NCC / hủy** | ✗ | ✓ `create_return_to_supplier()` + `create_write_off()` |
| 8. Lưu hồ sơ recall | ✓ track_changes=1 | ✓ |
| 3a. Đã cấp BN một phần → báo bác sĩ + QL y tế | ✗ | ✓ `notify_clinical_staff()` |
| 7a. Hủy = Stock Entry 'Write Off' lý do 'Recall' | ✗ | ✓ via `create_write_off()` purpose=Write Off recall_notice link |
| Ngoại lệ: Không xác định khoa → audit toàn bộ cấp phát giai đoạn | ✗ | ✓ `audit_dispensings_in_period(start, end)` |

## Actor

- SC-MANAGER (chính), SC-STOREKEEPER (theo dõi)

## Pre-condition

- Thông báo recall từ NCC HOẶC phát hiện vấn đề nội bộ
- SC Batch đang active (batch_id, supplier)

## Luồng chính

| Bước | Action | Implementation |
|---|---|---|
| 1 | Tạo SC Recall Notice (Draft): batch_no, recall_type, severity, recall_reason | DocType — Draft |
| 2 | Click "Populate Affected Items" | `populate_affected_items()` query SLE + PD |
| 3 | Review affected_items grouped: Warehouse / Department / Patient | UI table (existing) |
| 4 | Submit → batch.blocked=1, block_reason="Recall {name}" | `on_submit()` (existing) |
| 5 | Click "Send to Departments" → in/email phiếu cho từng khoa | `notify_departments()` group by department |
| 6 | Khoa thu hồi → cập nhật từng row: recovered_qty, destroyed_qty, status | `update_recovery(row_name, ...)` |
| 7 | Khi outstanding=0 → chọn resolution → "Create Return PR" hoặc "Create Write Off SE" | `create_return_to_supplier()` / `create_write_off()` |
| 8 | Hồ sơ đầy đủ — track_changes + audit log | tự động |

## Luồng thay thế

### 3a — Một phần đã sử dụng cho BN

Khi `populate_affected_items` phát hiện `location_type=Patient` rows:
- `notify_clinical_staff()` gửi email/notification đến bác sĩ điều trị + role "SupplyCore Manager"
- `clinical_notified_at` field set timestamp
- Mỗi row Patient có status mặc định "Used (No Recovery)" nếu BN đã xuất viện

### 7a — Hủy vật tư

`create_write_off()`:
- Tạo SC Stock Entry: entry_type="Material Issue", purpose="Write Off — Recall {name}"
- recall_notice = self.name (bypass FEFO blocked check)
- Items = các row có location_type=Warehouse và status không phải "Recovered"
- On submit: SLE âm tại warehouse → batch về 0
- GL post: Dr 642 / Cr 152

## Xử lý ngoại lệ

### Không xác định khoa phòng đã nhận

`audit_dispensings_in_period(start_date, end_date)`:
- Trả tất cả SC Patient Dispensing có batch hoặc item match trong khoảng thời gian
- Bao gồm cả PD không có batch link (legacy)
- Output: list `{pd, patient, ward, dispensing_date, qty, has_batch_link}`
- UI hiển thị warning + cho phép manually add vào affected_items

## Field changes

### SC Recall Notice (.json)

Add fields:
- `clinical_notified_at` Datetime read_only — set khi `notify_clinical_staff()` chạy
- `return_pr` Link SC Purchase Receipt read_only — set khi tạo return PR
- `write_off_entry` Link SC Stock Entry read_only — set khi tạo write off

### SC Recall Affected Item (.json)

Add fields:
- `recovery_date` Date allow_on_submit — ngày khoa thu hồi
- `recovered_by` Link User allow_on_submit
- `clinical_notified` Check default=0 — flag cho 3a

### SC Stock Entry (.json)

Add field:
- `recall_notice` Link SC Recall Notice — khi set, bypass FEFO blocked check (vì SE này CHÍNH LÀ disposal của recall)

### SC Patient Dispensing (.py)

Add `validate()._enforce_no_blocked_batch()` — throw nếu bất cứ item batch nào blocked.

## Error codes

- `SC-E-RCL-BATCH-RECALLED` — PD cố submit với batch bị recall
- `SC-E-RCL-RESOLUTION-INVALID` — resolution không thuộc {Return to Supplier, Destroy}
- `SC-E-RCL-OUTSTANDING-EXISTS` — cố close recall khi outstanding > 0
- `SC-E-RCL-NO-AFFECTED` — populate trả 0 items (batch không có movement)
- `SC-E-RCL-MANAGER-REQUIRED` — submit cần role SupplyCore Manager

## Logic — `sc_recall_notice.py` (extensions)

```python
@frappe.whitelist()
def notify_departments(self):
    """UC-30 step 5: group affected_items theo department, trả data cho Print Format."""
    if self.docstatus != 1:
        frappe.throw(_("Chỉ notify khi Recall Notice đã Issued"))
    by_dept = {}
    for r in self.affected_items:
        if r.location_type != "Department":
            continue
        dept = r.department or "Unknown"
        by_dept.setdefault(dept, []).append({
            "item": r.warehouse or self.item,
            "voucher": r.voucher_no,
            "qty": flt(r.qty_dispensed),
            "outstanding": flt(r.outstanding_qty),
        })
    return {"by_department": by_dept, "letter_count": len(by_dept)}

@frappe.whitelist()
def notify_clinical_staff(self):
    """UC-30 3a: gửi alert tới SupplyCore Manager + Patient's prescribing doctor."""
    if self.docstatus != 1:
        frappe.throw(_("Chỉ notify khi Issued"))
    patient_rows = [r for r in self.affected_items if r.location_type == "Patient"]
    if not patient_rows:
        return {"notified": 0, "msg": "Không có BN bị ảnh hưởng"}
    recipients = frappe.get_all("User",
        filters={"enabled": 1},
        or_filters=[
            ["name", "in", frappe.get_all("Has Role",
                filters={"role": ["in", ["SupplyCore Manager"]]},
                pluck="parent")],
        ], pluck="name")
    if recipients:
        frappe.sendmail(
            recipients=recipients,
            subject=f"[RECALL] {self.name} — {len(patient_rows)} BN ảnh hưởng",
            message=f"Recall Notice {self.name} ảnh hưởng {len(patient_rows)} bệnh nhân. "
                    f"Vui lòng xem chi tiết tại /app/sc-recall-notice/{self.name}",
            now=False,
        )
    for r in patient_rows:
        r.clinical_notified = 1
    self.db_set("clinical_notified_at", frappe.utils.now())
    self.save(ignore_permissions=True)
    return {"notified": len(patient_rows), "recipients": len(recipients)}

@frappe.whitelist()
def update_recovery(self, row_name, recovered_qty=0, destroyed_qty=0,
                     status="In Progress", remarks=None):
    """UC-30 step 6: cập nhật recovery của 1 row affected_items (allow_on_submit)."""
    if self.docstatus != 1:
        frappe.throw(_("Chỉ update khi Issued"))
    row = next((r for r in self.affected_items if r.name == row_name), None)
    if not row:
        frappe.throw(_("Row {0} không tồn tại").format(row_name))
    row.recovered_qty = flt(recovered_qty)
    row.destroyed_qty = flt(destroyed_qty)
    row.status = status
    row.recovery_date = frappe.utils.today()
    row.recovered_by = frappe.session.user
    if remarks:
        row.remarks = remarks
    row.db_update()
    self._compute_summary()
    self.db_update()
    return {"outstanding_qty": flt(self.outstanding_qty),
            "resolution_pct": flt(self.recall_resolution_pct)}

@frappe.whitelist()
def create_return_to_supplier(self):
    """UC-30 step 7: tạo SC Purchase Receipt is_return=1 cho qty thu hồi từ kho."""
    if self.docstatus != 1:
        frappe.throw(_("Chỉ tạo khi Issued"))
    if self.return_pr:
        frappe.throw(_("Đã tạo Return PR {0}").format(self.return_pr))
    if not self.supplier:
        frappe.throw(_("Batch không có supplier — không thể trả NCC"))
    rows = [r for r in self.affected_items
            if r.location_type == "Warehouse" and flt(r.recovered_qty) > 0]
    if not rows:
        frappe.throw(_("SC-E-RCL-NO-AFFECTED: Không có qty thu hồi từ kho"))
    pr = frappe.new_doc("SC Purchase Receipt")
    pr.supplier = self.supplier
    pr.posting_date = frappe.utils.today()
    pr.is_return = 1
    pr.return_reason = f"Recall {self.name}: {self.recall_reason}"
    for r in rows:
        pr.append("items", {
            "item": self.item, "batch_no": self.batch_no,
            "warehouse": r.warehouse, "qty": flt(r.recovered_qty),
            "uom": frappe.db.get_value("SC Item", self.item, "uom"),
        })
    pr.flags.ignore_permissions = True
    pr.insert()
    self.db_set("return_pr", pr.name)
    self.db_set("resolution", "Return to Supplier")
    self.db_set("resolution_date", frappe.utils.today())
    return {"return_pr": pr.name, "url": f"/app/sc-purchase-receipt/{pr.name}"}

@frappe.whitelist()
def create_write_off(self):
    """UC-30 step 7a: tạo SC Stock Entry Material Issue purpose Write Off — Recall."""
    if self.docstatus != 1:
        frappe.throw(_("Chỉ tạo khi Issued"))
    if self.write_off_entry:
        frappe.throw(_("Đã tạo Write Off {0}").format(self.write_off_entry))
    rows = [r for r in self.affected_items
            if r.location_type == "Warehouse" and flt(r.destroyed_qty) > 0]
    if not rows:
        frappe.throw(_("SC-E-RCL-NO-AFFECTED: Không có qty destroyed từ kho"))
    se = frappe.new_doc("SC Stock Entry")
    se.entry_type = "Material Issue"
    se.posting_date = frappe.utils.today()
    se.from_warehouse = rows[0].warehouse
    se.purpose = f"Write Off — Recall {self.name}: {self.recall_reason}"
    se.recall_notice = self.name
    for r in rows:
        se.append("items", {
            "item": self.item, "batch": self.batch_no,
            "qty": flt(r.destroyed_qty),
        })
    se.flags.ignore_permissions = True
    se.insert()
    se.submit()
    self.db_set("write_off_entry", se.name)
    self.db_set("resolution", "Destroy")
    self.db_set("resolution_date", frappe.utils.today())
    return {"write_off_entry": se.name, "url": f"/app/sc-stock-entry/{se.name}"}

@frappe.whitelist()
def audit_dispensings_in_period(self, start_date=None, end_date=None):
    """UC-30 ngoại lệ: audit toàn bộ cấp phát giai đoạn không xác định khoa."""
    start_date = start_date or frappe.utils.add_days(frappe.utils.today(), -90)
    end_date = end_date or frappe.utils.today()
    rows = frappe.db.sql("""
        SELECT pd.name AS pd, pd.dispensing_date, pd.patient, pd.ward,
               pdi.batch, pdi.item, pdi.qty,
               CASE WHEN pdi.batch IS NOT NULL THEN 1 ELSE 0 END AS has_batch_link
        FROM `tabSC PD Item` pdi
        JOIN `tabSC Patient Dispensing` pd ON pd.name = pdi.parent
        WHERE pd.docstatus = 1
          AND pdi.item = %(item)s
          AND pd.dispensing_date BETWEEN %(start)s AND %(end)s
        ORDER BY pd.dispensing_date DESC
    """, {"item": self.item, "start": start_date, "end": end_date}, as_dict=True)
    return {"dispensings": rows, "count": len(rows),
            "period": f"{start_date} → {end_date}"}
```

## Migration

- Add fields qua DocType JSON — `bench --site supplycore migrate` auto-handles
- Existing recall notices không bị ảnh hưởng (mới fields nullable)

## Test plan — `tests/uc30_test.py`

| Test | Scenario |
|---|---|
| `test_create_recall_notice_blocks_batch` | Submit RN → batch.blocked=1 |
| `test_cancel_recall_unblocks_batch` | Cancel RN → batch.blocked=0 |
| `test_populate_affected_items_warehouse` | Batch có SLE 100 ở 2 kho → 2 affected_items Warehouse |
| `test_populate_affected_items_patient` | PD submitted với batch → affected_items Patient |
| `test_blocked_batch_rejects_patient_dispensing` | PD submit với batch blocked → throw SC-E-RCL-BATCH-RECALLED |
| `test_blocked_batch_rejects_stock_entry` | SE Material Issue batch blocked → throw |
| `test_recall_se_bypasses_blocked_check` | SE với recall_notice set → bypass check |
| `test_update_recovery_updates_outstanding` | update_recovery(row, recovered=50) → outstanding giảm |
| `test_create_return_to_supplier` | recovered_qty=80 → tạo PR is_return=1 với qty 80 |
| `test_create_write_off` | destroyed_qty=20 → tạo SE Material Issue purpose Write Off |
| `test_notify_clinical_staff_marks_rows` | PD-affected → notify → clinical_notified=1 |
| `test_audit_dispensings_in_period` | tìm PD trong period → trả list có has_batch_link flag |

## Out-of-scope (defer)

- Multi-batch recall trong cùng 1 notice (mỗi notice = 1 batch) — UC-30 spec không yêu cầu rõ multi-batch
- Auto-recall trigger từ HIS/BHYT alert
- Patient SMS notification (chỉ email staff)

## File changes

1. `supplycore/m10_traceability/UC-30_FLOW.md` — this file
2. `supplycore/m10_traceability/doctype/sc_recall_notice/sc_recall_notice.json` — +3 fields
3. `supplycore/m10_traceability/doctype/sc_recall_notice/sc_recall_notice.py` — +5 methods
4. `supplycore/m10_traceability/doctype/sc_recall_affected_item/sc_recall_affected_item.json` — +3 fields
5. `supplycore/supplycore/doctype/sc_stock_entry/sc_stock_entry.json` — +recall_notice field
6. `supplycore/supplycore/doctype/sc_stock_entry/sc_stock_entry.py` — bypass blocked when recall_notice set
7. `supplycore/m7_dispensing/doctype/sc_patient_dispensing/sc_patient_dispensing.py` — block submit if batch blocked
8. `supplycore/tests/uc30_test.py` — 12 test scenarios
