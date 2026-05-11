# UC-21 — Xử lý và Cấp phát Vật tư — Flow & Implementation

**Module:** M7 Dispensing
**DocType:** SC Dispensing Request + SC DR Item + SC Stock Entry (existing)
**Date:** 2026-05-11
**Source:** Phase 1 / UseCase_SupplyCore_v2.0.md UC-21

## Audit hiện trạng

| Spec | Trước | Sau UC-21 |
|---|---|---|
| 1. List phiếu chờ | ✓ List view filter status | ✓ |
| 2. Chi tiết phiếu | ✓ | ✓ |
| 3. **Auto suggest FEFO trên DR** | Partial: FEFO enforce ở SE submit, không pre-suggest | ✓ `auto_pick_fefo_for_dr()` method |
| 3a. Override FEFO + Manager | ✓ UC-16 đã có | ✓ |
| 4. Xác nhận qty + batch | ✓ approved_qty + batch | ✓ |
| 4a. **Partial cấp + ghi chú thiếu** | Partial: approved_qty < requested, không có note | ✓ thêm `shortage_note` per row |
| 5. SE Material Issue | ✓ `make_stock_entry()` | ✓ |
| 6. **In phiếu cấp phát + barcode** | ✗ | ✓ `get_dispensing_slip_data()` |
| 7. SE submit → SLE | ✓ | ✓ |
| 8. **Notification khoa phòng** | ✗ | ✓ email department head trên make_stock_entry |
| **Ngoại lệ: tồn hệ thống ≠ thực → block + SR** | ✗ | ✓ `check_stock_match_for_dr()` warn before issue |

## Actor

- Thủ kho (Storekeeper) — process + issue

## Pre-condition

- DR đã submit (status=Approved) (UC-20)
- Tồn kho đủ tại from_warehouse

## Luồng chính

| Bước | Action |
|---|---|
| 1 | Mở list `/app/sc-dispensing-request?status=Approved` |
| 2 | Click DR → xem detail |
| 3 | Click "Auto FEFO" → `auto_pick_fefo_for_dr()` fill batch + approved_qty theo FEFO |
| 3a | (Override) chọn batch khác → ghi reason (UC-16 enforcement ở SE submit) |
| 4 | Xác nhận approved_qty + batch per row |
| 4a | (Partial) approved_qty < requested_qty → nhập `shortage_note` |
| 5 | Click "Tạo Stock Entry" → `make_stock_entry()` tạo SE Material Issue Draft |
| 6 | Click "In phiếu" → `get_dispensing_slip_data()` trả data cho Print Format |
| 7 | SE submit → SLE -qty; DR.status=Issued; notify department |

## Luồng thay thế

### 3 — Auto FEFO suggest cho DR

`auto_pick_fefo_for_dr()`:
- Loop items in DR
- Với mỗi item: gọi `get_suggested_batches(item, from_warehouse, requested_qty)`
- Set `batch` = batch FEFO đầu, `approved_qty` = min(requested, available)
- Nếu shortfall: set `shortage_note` auto

### 4a — Partial dispense

- User giảm `approved_qty` < `requested_qty`
- Nhập `shortage_note` (lý do thiếu)
- Submit DR + make_stock_entry → SE chỉ xuất phần approved
- DR remain status=Issued (kèm note shortage)

### 3a — Override FEFO

Đã handled ở UC-16 SE.before_submit (Manager role check + audit log).

## Hậu điều kiện

- DR.status=Issued + DR.stock_entry link
- SE submitted + SLE -qty
- Print slip data available
- Email department head

## Xử lý ngoại lệ

### Tồn hệ thống ≠ tồn thực

`check_stock_match_for_dr()`:
- Quét items trong DR: compute current_qty per (item, warehouse, batch)
- So với approved_qty
- If approved_qty > current_qty per row → flag mismatch
- Return list mismatches + suggest "Tạo Stock Reconciliation trước"
- Block make_stock_entry nếu có mismatch nghiêm trọng (deficit > 0)

## Field changes

### SC DR Item — ADD

| Field | Type | Note |
|---|---|---|
| `shortage_note` | Small Text | Lý do thiếu khi approved < requested (luồng 4a) |

## Error codes mới

| Code | Trigger | Message |
|---|---|---|
| `SC-E-DR-STOCK-MISMATCH` | check_stock_match phát hiện shortfall | "Item {x}: approved_qty {y} > tồn kho thực {z}. Tạo Stock Reconciliation trước." |

## Logic — `sc_dispensing_request.py`

### `auto_pick_fefo_for_dr` (NEW)

```python
@frappe.whitelist()
def auto_pick_fefo_for_dr(self):
    """UC-21 step 3: auto-fill batch theo FEFO + adjust approved_qty."""
    from supplycore.api.fefo import get_suggested_batches
    if self.docstatus != 0:
        frappe.throw(_("Chỉ auto-pick khi DR ở Draft"))
    if not self.from_warehouse:
        frappe.throw(_("Chọn from_warehouse trước"))

    picked = []
    for r in self.items:
        res = get_suggested_batches(r.item, self.from_warehouse, flt(r.requested_qty))
        if res["batches"]:
            first = res["batches"][0]
            r.batch = first["batch_no"]
            r.approved_qty = flt(first["suggested_qty"])
            if res["shortfall"] > 0:
                r.shortage_note = (
                    f"Thiếu {res['shortfall']} theo yêu cầu — chỉ cấp {r.approved_qty}"
                )
            picked.append({"item": r.item, "batch": r.batch,
                            "approved_qty": r.approved_qty})
        else:
            r.shortage_note = "Không có batch khả dụng (hết hàng / hết hạn / blocked)"
    self.save(ignore_permissions=False)
    return {"picked": picked, "rows": len(self.items)}
```

### `check_stock_match_for_dr` (NEW)

```python
@frappe.whitelist()
def check_stock_match_for_dr(self):
    """UC-21 ngoại lệ: phát hiện hệ thống ≠ thực tế."""
    mismatches = []
    for r in self.items:
        if not (r.item and self.from_warehouse):
            continue
        params = {"item": r.item, "wh": self.from_warehouse}
        cond = ""
        if r.batch:
            cond = "AND batch = %(batch)s"
            params["batch"] = r.batch
        sql = f"""
            SELECT COALESCE(SUM(qty_change), 0)
            FROM `tabSC Stock Ledger Entry`
            WHERE item = %(item)s AND warehouse = %(wh)s AND is_cancelled = 0
              {cond}
        """
        actual = flt(frappe.db.sql(sql, params)[0][0])
        if flt(r.approved_qty) > actual:
            mismatches.append({
                "row_idx": r.idx, "item": r.item, "batch": r.batch,
                "approved_qty": flt(r.approved_qty),
                "actual_qty": actual,
                "deficit": flt(r.approved_qty) - actual,
            })
    return {"mismatches": mismatches, "ok": len(mismatches) == 0}
```

### `make_stock_entry` extend — block khi mismatch + email department

```python
@frappe.whitelist()
def make_stock_entry(self):
    if self.docstatus != 1:
        frappe.throw(_("DR phải submit trước"))
    if self.stock_entry:
        frappe.throw(_("DR đã có Stock Entry: {0}").format(self.stock_entry))
    # UC-21 ngoại lệ: check stock match before issue
    check = self.check_stock_match_for_dr()
    if check["mismatches"]:
        details = ", ".join(f"{m['item']} (deficit {m['deficit']})"
                              for m in check["mismatches"][:3])
        frappe.throw(_(
            "SC-E-DR-STOCK-MISMATCH: Tồn kho hệ thống không khớp ({0}). "
            "Tạo SC Stock Reconciliation trước khi cấp phát."
        ).format(details))

    valid = [r for r in self.items if flt(r.approved_qty) > 0]
    if not valid:
        frappe.throw(_("Không có item nào có approved_qty > 0"))

    se = frappe.new_doc("SC Stock Entry")
    se.entry_type = "Material Issue"
    se.posting_date = today()
    se.from_warehouse = self.from_warehouse
    se.purpose = f"Dispensing Request {self.name}"
    for row in valid:
        se.append("items", {
            "item": row.item, "qty": flt(row.approved_qty),
            "uom": row.uom, "batch": row.batch,
            "valuation_rate": _last_purchase_rate(row.item),
        })
    se.flags.ignore_permissions = True
    se.insert()
    self.db_set("stock_entry", se.name)
    self.db_set("status", "Issued")
    self._notify_department()  # UC-21 step 8
    return se.name

def _notify_department(self):
    """UC-21 step 8: email department head khi DR Issued."""
    if not self.department:
        return
    head = frappe.db.get_value("SC Department", self.department, "head_user")
    if not head:
        return
    email = frappe.db.get_value("User", head, "email")
    if not email:
        return
    try:
        frappe.sendmail(
            recipients=[email],
            subject=f"[SupplyCore] DR {self.name} — vật tư sẵn sàng",
            message=(f"<p>Phiếu cấp phát <b>{self.name}</b> đã được xử lý.</p>"
                     f"<p>Stock Entry: {self.stock_entry}</p>"
                     f"<p><a href='/app/sc-dispensing-request/{self.name}'>Mở phiếu</a></p>"),
            delayed=False,
        )
    except Exception as e:
        frappe.log_error(message=str(e)[:1000], title="UC-21 _notify_department")
```

### `get_dispensing_slip_data` (NEW)

```python
@frappe.whitelist()
def get_dispensing_slip_data(self):
    """UC-21 step 6: data in phiếu cấp phát có barcode."""
    return {
        "name": self.name,
        "barcode": self.name,  # DR name dùng làm barcode value
        "request_date": str(self.request_date) if self.request_date else "",
        "department": self.department,
        "from_warehouse": self.from_warehouse,
        "patient": self.patient,
        "requested_by": self.requested_by,
        "purpose": self.purpose,
        "items": [{
            "item": r.item, "item_name": r.item_name, "uom": r.uom,
            "requested_qty": flt(r.requested_qty),
            "approved_qty": flt(r.approved_qty),
            "batch": r.batch,
            "shortage_note": r.shortage_note,
        } for r in self.items],
        "stock_entry": self.stock_entry,
        "url": f"/app/sc-dispensing-request/{self.name}",
    }
```

## Migration

- 1 field SC DR Item Frappe tự migrate

## Test plan — `tests/uc21_test.py`

| Test | Scenario |
|---|---|
| `test_auto_pick_fefo_fills_batch` | DR + items có batch FEFO trong stock → auto_pick fill batch + approved_qty |
| `test_auto_pick_fefo_partial_shortage` | Stock < requested → approved_qty = available, shortage_note set |
| `test_check_stock_match_ok` | DR với approved_qty ≤ stock → mismatches=[] |
| `test_check_stock_match_deficit` | DR approved > stock → mismatches có deficit > 0 |
| `test_make_stock_entry_blocks_on_mismatch` | DR approved > stock + make_stock_entry → SC-E-DR-STOCK-MISMATCH |
| `test_make_stock_entry_succeeds_normal` | Đủ stock → SE created OK |
| `test_make_stock_entry_sets_status_issued` | SE created → DR.status=Issued |
| `test_partial_dispense_with_shortage_note` | approved < requested + shortage_note → save OK + note saved |
| `test_get_dispensing_slip_data` | Method trả dict đủ field (barcode, items, ...) |
| `test_notify_department_on_issue` | make_stock_entry → email sent (or notification timestamp recorded) |

## Out-of-scope

- JS form button (defer; whitelisted API đủ)
- Real-time notification (chỉ email)
- Auto-create SC Stock Reconciliation khi mismatch (chỉ block + suggest user manual)

## File changes

1. `supplycore/m7_dispensing/UC-21_FLOW.md` — this file
2. `supplycore/m7_dispensing/doctype/sc_dr_item/sc_dr_item.json` — `shortage_note` field
3. `supplycore/m7_dispensing/doctype/sc_dispensing_request/sc_dispensing_request.py` — extend make_stock_entry + 3 new methods + notify
4. `supplycore/tests/uc21_test.py` — 10 test scenarios
