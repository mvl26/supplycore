# UC-17 — Cảnh báo sắp hết hạn — Flow & Implementation

**Module:** M5 FEFO & Hạn dùng
**DocType:** Batch Expiry Alert + SC Stock Entry (existing)
**Date:** 2026-05-11
**Source:** Phase 1 / UseCase_SupplyCore_v2.0.md UC-17

## Audit hiện trạng

| Spec | Trước | Sau UC-17 |
|---|---|---|
| 1. Daily scheduler check expiry | ✓ `scan_expiring_batches` hooks daily | ✓ + fix bug query ERPNext `tabStock Ledger Entry` → SC SLE |
| 2. **Phân loại Đỏ <30d / Vàng 30-90d / Xanh >90d** | Partial: Critical/Warning, ✗ Info "Green" | ✓ thêm Info severity (>90d, ít alert hơn — chỉ tạo cho monitoring) |
| 3. Email/notification | ✓ `_send_expiry_email` | ✓ |
| 4. **Dashboard widget + filter kho** | Partial: list view có; ✗ dashboard API | ✓ `get_expiring_dashboard(warehouse=None)` API |
| 5. Action: ưu tiên cấp / trả NCC / hủy | Partial: `resolution_action` Select có; ✗ method execute | ✓ `dispose_expired_batch()` + `mark_priority_issue()` whitelisted |
| 5a. **Hủy → SE Material Issue 'Expired'** | ✗ | ✓ `dispose_expired_batch(warehouse, qty)` tạo SE auto |
| 5b. Cấp phát ưu tiên → gắn batch | ✓ FEFO sort đã đặt batch gần hết hạn trước (UC-16) | ✓ alert flag + UI hint |
| Per-warehouse breakdown | Partial: alert có field warehouse nhưng scan không phân biệt | ✓ scan tạo 1 alert per (batch, warehouse) |
| Ngoại lệ: Email lỗi → retry | Partial: log_error, không retry | Note: Frappe sendmail có queue native; rely on `delayed=False` retry tự nhiên hoặc Frappe Email Queue retry |

## Actor

- Hệ thống — scheduler daily
- Thủ kho / Quản lý / Pharmacy Officer — review + action

## Pre-condition

- Batch có `expiry_date`
- Email config trong site_config

## Luồng chính

| Bước | Action |
|---|---|
| 1 | Scheduler daily `scan_expiring_batches` |
| 2 | Phân loại: days_left <30=Critical (Đỏ), 30-90=Warning (Vàng), 90-180=Info (Xanh khi >90 nhưng <window 180d) |
| 3 | Tạo Batch Expiry Alert per (batch, warehouse) với severity tương ứng. Skip dedup 7 ngày. |
| 4 | Email tổng hợp gửi Storekeeper/Manager với HTML table colored |
| 5 | User mở `/app/batch-expiry-alert` list, filter theo `warehouse` + `severity` |
| 6 | Click alert → click action: `dispose_expired_batch()` HOẶC `mark_priority_issue()` |

## Luồng thay thế

### 5a — Hủy batch hết hạn

`dispose_expired_batch(warehouse=None, qty=None)`:
- Default warehouse = `alert.warehouse`
- Default qty = current_qty của batch tại warehouse
- Tạo SC Stock Entry Material Issue:
  - `from_warehouse=warehouse`
  - `purpose="Expired Disposal"`
  - 1 row: `item=alert.item_code`, `qty`, `batch=alert.batch_no`
- Insert + Submit → SLE -qty
- Set `alert.resolved=1`, `resolution_action="Write Off"`, `resolved_by/at`
- Set `batch.disabled=1` (no further use)

### 5b — Cấp phát ưu tiên

`mark_priority_issue(notes=None)`:
- Set `alert.resolved=1`, `resolution_action="Priority Issue"`, `resolution_notes=notes`
- FEFO picker (UC-16) đã sort theo expiry ASC nên batch này tự được pick trước

## Dashboard API

`get_expiring_dashboard(warehouse=None)`:
- Aggregate Batch Expiry Alert chưa resolved theo severity
- Optional filter warehouse
- Trả `{critical: N, warning: N, info: N, total: N, batches: [top 10]}`

## Field changes

KHÔNG cần — current Batch Expiry Alert có đủ fields. severity `Info` đã có option.

## Error codes mới

| Code | Trigger | Message |
|---|---|---|
| `SC-E-DISPOSE-ZERO` | dispose với qty=0 | "Không có tồn kho để hủy" |
| `SC-E-DISPOSE-NO-WH` | alert không có warehouse + không truyền | "Phải truyền warehouse" |

## Logic — `fefo_picker.py` `scan_expiring_batches`

```python
def scan_expiring_batches():
    settings = frappe.get_single("SupplyCore Settings")
    critical = int(settings.get("expiry_alert_days_critical") or 30)
    warning = int(settings.get("expiry_alert_days_warning") or 90)
    info_window = 180  # alert "Info" green cho 90-180d

    # Aggregate qty per (batch, warehouse) qua SC SLE
    rows = frappe.db.sql("""
        SELECT b.name AS batch_no, b.item AS item_code, i.item_name,
               b.expiry_date,
               DATEDIFF(b.expiry_date, CURDATE()) AS days_left,
               sle.warehouse,
               COALESCE(SUM(sle.qty_change), 0) AS current_qty
        FROM `tabSC Batch` b
        JOIN `tabSC Item` i ON i.name = b.item
        LEFT JOIN `tabSC Stock Ledger Entry` sle
            ON sle.batch = b.name AND sle.is_cancelled = 0
        WHERE b.disabled = 0
          AND COALESCE(b.blocked, 0) = 0
          AND b.expiry_date IS NOT NULL
          AND b.expiry_date >= CURDATE()
          AND b.expiry_date <= DATE_ADD(CURDATE(), INTERVAL %s DAY)
        GROUP BY b.name, sle.warehouse
        HAVING current_qty > 0
        ORDER BY b.expiry_date ASC
        LIMIT 500
    """, info_window, as_dict=True)

    created_count = 0
    for r in rows:
        if r.days_left < critical:
            severity = "Critical"
        elif r.days_left < warning:
            severity = "Warning"
        else:
            severity = "Info"
        # Dedup: alert cùng (batch, warehouse, severity) trong 7 ngày
        if frappe.db.exists("Batch Expiry Alert", {
            "batch_no": r.batch_no, "warehouse": r.warehouse,
            "severity": severity, "resolved": 0,
            "alert_date": [">=", frappe.utils.add_days(today(), -7)],
        }):
            continue
        try:
            a = frappe.new_doc("Batch Expiry Alert")
            a.alert_date = today()
            a.batch_no = r.batch_no
            a.item_code = r.item_code
            a.item_name = r.item_name
            a.expiry_date = r.expiry_date
            a.days_to_expiry = r.days_left
            a.severity = severity
            a.warehouse = r.warehouse
            a.current_qty = flt(r.current_qty)
            a.flags.ignore_permissions = True
            a.insert()
            created_count += 1
        except Exception as e:
            frappe.log_error(message=f"BatchExpiryAlert failed batch={r.batch_no}: {e}",
                              title="UC-17 scan_expiring_batches")

    if created_count:
        _send_expiry_email(rows, critical)
    return {"created": created_count, "scanned": len(rows)}
```

## Logic — `batch_expiry_alert.py` action methods

```python
@frappe.whitelist()
def dispose_expired_batch(self, warehouse: str = None, qty: float = None) -> dict:
    """UC-17 5a: tạo SC Stock Entry Material Issue purpose Expired Disposal."""
    wh = warehouse or self.warehouse
    if not wh:
        frappe.throw(_("SC-E-DISPOSE-NO-WH: Phải truyền warehouse"))

    # Compute qty mặc định = current at warehouse
    if qty is None or flt(qty) <= 0:
        qty = flt(frappe.db.sql("""
            SELECT COALESCE(SUM(qty_change), 0)
            FROM `tabSC Stock Ledger Entry`
            WHERE batch = %s AND warehouse = %s AND is_cancelled = 0
        """, (self.batch_no, wh))[0][0])

    if flt(qty) <= 0:
        frappe.throw(_("SC-E-DISPOSE-ZERO: Không có tồn kho để hủy ({0} = 0)").format(self.batch_no))

    item_uom = frappe.db.get_value("SC Item", self.item_code, "uom")
    se = frappe.new_doc("SC Stock Entry")
    se.entry_type = "Material Issue"
    se.posting_date = today()
    se.from_warehouse = wh
    se.purpose = "Expired Disposal (UC-17)"
    se.remarks = (f"Hủy lô hết hạn {self.batch_no} per Batch Expiry Alert "
                  f"{self.name}. Expiry: {self.expiry_date}")
    se.append("items", {
        "item": self.item_code, "qty": flt(qty), "uom": item_uom,
        "batch": self.batch_no, "source_bin": None,
    })
    se.flags.ignore_permissions = True
    se.insert()
    se.submit()

    self.db_set("resolved", 1)
    self.db_set("resolution_action", "Write Off")
    self.db_set("resolution_notes", f"Hủy qua SE {se.name}, qty={qty}")
    self.db_set("resolved_by", frappe.session.user)
    self.db_set("resolved_at", frappe.utils.now())
    frappe.db.set_value("SC Batch", self.batch_no, "disabled", 1)
    return {"stock_entry": se.name, "qty": flt(qty), "status": "disposed"}


@frappe.whitelist()
def mark_priority_issue(self, notes: str = None) -> dict:
    """UC-17 5b: mark batch để FEFO ưu tiên cấp phát tiếp theo."""
    self.db_set("resolved", 1)
    self.db_set("resolution_action", "Priority Issue")
    self.db_set("resolution_notes", notes or "Ưu tiên cấp phát đợt tiếp theo")
    self.db_set("resolved_by", frappe.session.user)
    self.db_set("resolved_at", frappe.utils.now())
    return {"status": "marked_priority"}
```

## Dashboard API — `fefo.py` extend

```python
@frappe.whitelist()
def get_expiring_dashboard(warehouse: str = None, limit: int = 10) -> dict:
    """UC-17 step 4: dashboard widget data."""
    cond = "AND warehouse = %(wh)s" if warehouse else ""
    counts = frappe.db.sql(f"""
        SELECT severity, COUNT(*) AS cnt
        FROM `tabBatch Expiry Alert`
        WHERE resolved = 0 {cond}
        GROUP BY severity
    """, {"wh": warehouse} if warehouse else {}, as_dict=True)
    by_sev = {r["severity"]: r["cnt"] for r in counts}

    batches = frappe.db.sql(f"""
        SELECT name, batch_no, item_code, item_name, expiry_date,
               days_to_expiry, severity, warehouse, current_qty
        FROM `tabBatch Expiry Alert`
        WHERE resolved = 0 {cond}
        ORDER BY days_to_expiry ASC LIMIT %(lim)s
    """, {"wh": warehouse, "lim": int(limit)} if warehouse else {"lim": int(limit)},
       as_dict=True)

    return {
        "critical":  by_sev.get("Critical", 0),
        "warning":   by_sev.get("Warning", 0),
        "info":      by_sev.get("Info", 0),
        "total":     sum(by_sev.values()),
        "batches":   batches,
    }
```

## Migration

- KHÔNG cần — chỉ thêm logic + methods.

## Test plan — `tests/uc17_test.py`

| Test | Scenario |
|---|---|
| `test_scan_critical_severity` | Batch expiry+20d → alert severity=Critical |
| `test_scan_warning_severity` | Batch expiry+60d → alert severity=Warning |
| `test_scan_info_severity` | Batch expiry+120d → alert severity=Info |
| `test_scan_skips_no_stock` | Batch không có SLE → không tạo alert |
| `test_scan_per_warehouse` | Batch ở 2 warehouse → 2 alerts riêng |
| `test_scan_dedup_within_7d` | Run scan 2 lần liên tiếp → không tạo duplicate alert |
| `test_dispose_expired_batch_creates_se` | dispose_expired_batch → SE Material Issue submitted + qty đúng |
| `test_dispose_sets_alert_resolved` | dispose → alert.resolved=1, resolution_action=Write Off |
| `test_dispose_disables_batch` | dispose → batch.disabled=1 |
| `test_mark_priority_issue` | mark_priority_issue → alert.resolved=1, action=Priority Issue |
| `test_dashboard_counts_by_severity` | 3 alerts severity khác nhau → dashboard trả counts |
| `test_dashboard_filter_warehouse` | Filter warehouse → chỉ count alerts của warehouse đó |

## Out-of-scope

- Email retry queue custom (rely on Frappe Email Queue builtin retry)
- Dashboard JS widget (defer; API đủ cho future UI)
- Bulk dispose action (process từng alert)

## File changes

1. `supplycore/m5_fefo/UC-17_FLOW.md` — this file
2. `supplycore/m5_fefo/api/fefo_picker.py` — rewrite scan với SC SLE + per-warehouse + Info severity
3. `supplycore/m5_fefo/doctype/batch_expiry_alert/batch_expiry_alert.py` — add dispose + mark_priority methods
4. `supplycore/api/fefo.py` — add `get_expiring_dashboard()`
5. `supplycore/tests/uc17_test.py` — 12 test scenarios
