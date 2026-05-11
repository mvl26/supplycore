# UC-22 — Ghi nhận sử dụng VT cho bệnh nhân — Flow & Implementation

**Module:** M7 Dispensing
**DocType:** SC Patient Dispensing + SC PD Item (existing)
**Date:** 2026-05-11
**Source:** Phase 1 / UseCase_SupplyCore_v2.0.md UC-22

## Audit hiện trạng

| Spec | Trước | Sau UC-22 |
|---|---|---|
| 1. Mở "Ghi nhận sử dụng" | ✓ /app/sc-patient-dispensing | ✓ |
| 2. **Chọn BN (mã / quét BHYT)** | ✓ patient Link; ✗ lookup by bhyt_card_no | ✓ `lookup_patient_by_bhyt()` |
| 3. **Chọn VT từ đã cấp khoa** | Partial: manual append; ✗ filter từ DR/SE | ✓ `get_dispensed_items_for_dr()` |
| 4. Nhập qty thực tế | ✓ | ✓ |
| 5. **Auto BHYT lookup** | ✓ `_calculate_bhyt` | ✓ + warn config thay đổi |
| 6. **Tính BHYT + BN tự trả** | ✓ | ✓ |
| 7. **Tổng hợp vào hồ sơ BN** | Partial: PD records, không có summary | ✓ `get_patient_dispense_history()` |
| 3a. **VT không BHYT → BN 100%** | ✓ cfg=None fallback | ✓ |
| 2a. **BN không thẻ BHYT → BN 100%** | Partial: chỉ check bhyt_payment_rate | ✓ check bhyt_card_no — nếu rỗng skip BHYT |
| **Ngoại lệ: Mã BHYT thay đổi** | ✗ | ✓ flag `bhyt_config_changed` khi config thay so với lần cấp gần nhất của item |

## Actor

- Nhân viên khoa phòng (Ward Staff)

## Pre-condition

- VT đã cấp khoa (DR Issued via UC-21)
- SC Patient có `patient_id` (mã BN); `bhyt_card_no` optional

## Luồng chính

| Bước | Action |
|---|---|
| 1 | Mở `/app/sc-patient-dispensing/new` (manual) HOẶC tạo từ DR Patient-Specific (`make_patient_dispensing`) |
| 2 | Chọn `patient` qua autocomplete OR `lookup_patient_by_bhyt(card_no)` |
| 3 | Append items từ `get_dispensed_items_for_dr(dr)` HOẶC manual chọn |
| 4 | Nhập `qty` thực tế |
| 5 | Save → `_calculate_bhyt` auto lookup BHYT config per item |
| 6 | Tính `bhyt_amount` + `patient_pays` per row + tổng |
| 7 | Submit → `on_submit` sync DR.status=Dispensed |

## Luồng thay thế

### 2a — BN không có thẻ BHYT

`_calculate_bhyt`:
- If `bhyt_card_no` empty → set all rows: bhyt_amount=0, patient_pays=total_cost
- Hiển thị msgprint cam: "BN không thẻ BHYT — chi phí tự trả 100%"

### 3a — VT không có cấu hình BHYT

Đã handled — `get_active_config` trả None → fallback patient_pays=100%.

## Xử lý ngoại lệ

### Mã BHYT thay đổi quy định

Trong `_calculate_bhyt`:
- So config hiện tại (cfg) với config dùng lần cấp gần nhất của item (last_pd_cfg)
- Nếu khác về `payment_rate` hoặc `ceiling_price` → set row flag `bhyt_config_changed=1` + msgprint warning
- KHÔNG block save — chỉ alert

## Field changes

### SC PD Item — ADD

| Field | Type | Note |
|---|---|---|
| `bhyt_config_changed` | Check, read_only | flag khi config khác lần cấp gần nhất |

## Error codes mới

KHÔNG có error codes mới — chỉ warning + alert.

## Logic — `sc_patient_dispensing.py`

### Validate — extend `_calculate_bhyt`

```python
def _calculate_bhyt(self):
    from supplycore.api.bhyt import get_active_config

    patient_rate = flt(self.bhyt_payment_rate) if self.bhyt_payment_rate else None
    # UC-22 2a: BN không thẻ BHYT → tự trả 100%
    no_bhyt_card = not (self.bhyt_card_no and str(self.bhyt_card_no).strip())

    for row in self.items:
        row.total_cost = flt(row.qty) * flt(row.unit_cost)

        if no_bhyt_card:
            row.bhyt_code = None
            row.bhyt_group = None
            row.bhyt_rate = 0
            row.ceiling_price = 0
            row.bhyt_amount = 0
            row.ceiling_overage = 0
            row.patient_pays = row.total_cost
            row.bhyt_config_changed = 0
            continue

        cfg = get_active_config(row.item, on_date=self.dispensing_date)
        if not cfg:
            # ... existing fallback (patient pays 100%)
            row.bhyt_code = None
            row.bhyt_rate = 0
            row.bhyt_amount = 0
            row.patient_pays = row.total_cost
            row.bhyt_config_changed = 0
            continue

        # Detect config change
        last_pd_item = frappe.db.sql("""
            SELECT bhyt_rate, ceiling_price FROM `tabSC PD Item`
            WHERE item = %s
              AND parent != %s
            ORDER BY creation DESC LIMIT 1
        """, (row.item, self.name or ""), as_dict=True)
        cfg_rate = flt(cfg.get("payment_rate") or 0)
        cfg_ceiling = flt(cfg.get("ceiling_price") or 0)
        config_changed = 0
        if last_pd_item:
            prev_rate = flt(last_pd_item[0]["bhyt_rate"])
            prev_ceiling = flt(last_pd_item[0]["ceiling_price"])
            if (prev_rate and prev_rate != cfg_rate) or (prev_ceiling and prev_ceiling != cfg_ceiling):
                config_changed = 1

        row.bhyt_code = cfg.get("bhyt_code")
        row.bhyt_group = cfg.get("bhyt_group")
        effective_rate = cfg_rate
        if patient_rate is not None and patient_rate < cfg_rate:
            effective_rate = patient_rate
        row.bhyt_rate = effective_rate
        row.ceiling_price = cfg_ceiling
        cap_unit = flt(row.unit_cost)
        ceiling_overage = 0
        if cfg_ceiling and flt(row.unit_cost) > cfg_ceiling:
            cap_unit = cfg_ceiling
            ceiling_overage = flt(row.qty) * (flt(row.unit_cost) - cfg_ceiling)
        bhyt_eligible = flt(row.qty) * cap_unit
        bhyt_amount = bhyt_eligible * effective_rate / 100.0
        row.bhyt_amount = round(bhyt_amount, 2)
        row.ceiling_overage = round(ceiling_overage, 2)
        row.patient_pays = round(flt(row.total_cost) - bhyt_amount, 2)
        row.bhyt_config_changed = config_changed

    if no_bhyt_card and self.docstatus == 0:
        frappe.msgprint(
            _("⚠ BN không có thẻ BHYT — chi phí tự trả 100%"),
            indicator="orange", alert=True,
        )

    if any(getattr(r, "bhyt_config_changed", 0) for r in self.items) and self.docstatus == 0:
        frappe.msgprint(
            _("⚠ Mã BHYT có thay đổi quy định — kiểm tra cấu hình"),
            indicator="orange", alert=True,
        )
```

### Whitelisted helpers

```python
@frappe.whitelist()
def lookup_patient_by_bhyt(card_no: str) -> dict:
    """UC-22 step 2: search SC Patient by bhyt_card_no LIKE."""
    if not card_no:
        return {"patients": []}
    rows = frappe.db.sql("""
        SELECT name, patient_id, patient_name, bhyt_card_no,
               bhyt_type, bhyt_payment_rate
        FROM `tabSC Patient`
        WHERE disabled = 0 AND bhyt_card_no LIKE %s
        LIMIT 10
    """, f"%{card_no}%", as_dict=True)
    return {"patients": rows}


@frappe.whitelist()
def get_dispensed_items_for_dr(dr_name: str) -> list:
    """UC-22 step 3: list items đã cấp từ DR (qua SE linked)."""
    dr = frappe.db.get_value("SC Dispensing Request", dr_name,
                               ["stock_entry"], as_dict=True)
    if not dr or not dr.stock_entry:
        return []
    return frappe.db.sql("""
        SELECT sei.item, i.item_name, sei.uom,
               sei.qty AS dispensed_qty, sei.batch,
               sei.valuation_rate AS unit_cost
        FROM `tabSC Stock Entry Item` sei
        JOIN `tabSC Item` i ON i.name = sei.item
        WHERE sei.parent = %s
    """, dr.stock_entry, as_dict=True)


@frappe.whitelist()
def get_patient_dispense_history(patient: str, from_date: str = None,
                                   to_date: str = None) -> dict:
    """UC-22 step 7: summary chi phí của BN per period."""
    cond = []
    params = {"patient": patient}
    if from_date:
        cond.append("pd.dispensing_date >= %(fd)s")
        params["fd"] = from_date
    if to_date:
        cond.append("pd.dispensing_date <= %(td)s")
        params["td"] = to_date
    where = "AND " + " AND ".join(cond) if cond else ""
    rows = frappe.db.sql(f"""
        SELECT pd.name, pd.dispensing_date,
               pd.total_cost, pd.bhyt_covered, pd.patient_pays,
               pd.docstatus
        FROM `tabSC Patient Dispensing` pd
        WHERE pd.patient = %(patient)s AND pd.docstatus != 2 {where}
        ORDER BY pd.dispensing_date DESC
    """, params, as_dict=True)
    return {
        "patient": patient,
        "count": len(rows),
        "total_cost": sum(flt(r["total_cost"]) for r in rows),
        "bhyt_covered": sum(flt(r["bhyt_covered"]) for r in rows),
        "patient_pays": sum(flt(r["patient_pays"]) for r in rows),
        "records": rows,
    }
```

## Migration

- 1 field SC PD Item Frappe tự migrate

## Test plan — `tests/uc22_test.py`

| Test | Scenario |
|---|---|
| `test_pd_calculate_bhyt_with_card` | BN có thẻ + item có BHYT config → bhyt_amount > 0 |
| `test_pd_no_bhyt_card_pays_100` | BN không thẻ → patient_pays = total_cost, bhyt_amount=0 |
| `test_pd_item_no_bhyt_config` | Item không BHYT → patient_pays = total_cost (existing behavior) |
| `test_pd_compute_totals` | 2 items → total_cost = sum |
| `test_pd_submit_syncs_dr_status` | PD submit + linked DR → DR.status=Dispensed |
| `test_lookup_patient_by_bhyt` | search by partial bhyt_card_no → trả patient |
| `test_get_dispensed_items_for_dr` | DR có SE → trả list items |
| `test_get_patient_dispense_history` | 2 PD submitted → history trả 2 records + sum |
| `test_pd_config_changed_flag` | Submit PD, sửa config item, tạo PD mới → bhyt_config_changed=1 |

## Out-of-scope

- Real-time BHYT API call (defer; chỉ local config)
- BHYT claim file generation (UC-24)
- Patient ledger doctype (defer — query qua history API)

## File changes

1. `supplycore/m7_dispensing/UC-22_FLOW.md` — this file
2. `supplycore/m7_dispensing/doctype/sc_pd_item/sc_pd_item.json` — `bhyt_config_changed` field
3. `supplycore/m7_dispensing/doctype/sc_patient_dispensing/sc_patient_dispensing.py` — extend _calculate_bhyt + 3 helpers
4. `supplycore/tests/uc22_test.py` — 9 test scenarios
