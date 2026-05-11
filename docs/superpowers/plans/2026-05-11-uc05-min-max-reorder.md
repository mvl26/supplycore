# UC-05 Min / Max / Reorder Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `reorder_level`, `max_stock`, `standard_order_qty` fields + child table `SC Item Reorder` (per-warehouse override) to `SC Item`; wire helper `get_reorder_thresholds()` into M11 `low_stock` alert (per-warehouse aware) and new Procurement Plan threshold-based auto-load.

**Architecture:** Hybrid — item-level fields are the default; child rows on `reorder_levels` (DocType `SC Item Reorder`) override per warehouse, per field. Single source of truth `supplycore.m2_planning.reorder.get_reorder_thresholds(item, warehouse)` is consumed by M11 alert scanner and Procurement Plan. Excel bulk-import via Frappe Data Import (zero custom code).

**Tech Stack:** Frappe v15, Python 3.10+, MariaDB 10.6, vanilla JS (`frappe.ui.form.on`).

**Spec:** `docs/superpowers/specs/2026-05-11-uc05-min-max-reorder-design.md`

**Site:** `supplycore` (bench commands use `bench --site supplycore ...`)
**Bench dir:** `/home/hoangvietyeuem/frappe-bench`
**App dir:** `/home/hoangvietyeuem/frappe-bench/apps/supplycore`

---

## File Structure

| File | Action | Responsibility |
|---|---|---|
| `supplycore/m2_planning/doctype/sc_item_reorder/__init__.py` | Create | Python package marker |
| `supplycore/m2_planning/doctype/sc_item_reorder/sc_item_reorder.json` | Create | Child DocType schema (istable=1) |
| `supplycore/m2_planning/doctype/sc_item_reorder/sc_item_reorder.py` | Create | `SCItemReorder(Document)` empty subclass |
| `supplycore/supplycore/doctype/sc_item/sc_item.json` | Modify | Add 3 Float fields + 1 Table field + collapsible section |
| `supplycore/supplycore/doctype/sc_item/sc_item.py` | Modify | Add 4 validate methods (`_validate_thresholds`, `_validate_lead_time`, `_validate_reorder_rows`) |
| `supplycore/m2_planning/reorder.py` | Create | `get_reorder_thresholds(item, warehouse=None) -> dict` |
| `supplycore/m11_dashboard/tasks.py` | Modify | Rewrite `_scan_low_stock` with 2-query merge (per-WH + item-level fallback) |
| `supplycore/m2_planning/doctype/procurement_plan/procurement_plan.py` | Modify | New `@frappe.whitelist() auto_load_reorder_items()` |
| `supplycore/m2_planning/doctype/procurement_plan/procurement_plan.js` | Modify | New button "Tự nạp theo Reorder Level" |
| `supplycore/patches/v0_2/init_uc05_fields.py` | Create | Patch: reload SC Item + SC Item Reorder |
| `supplycore/patches.txt` | Modify | Register new patch |
| `supplycore/tests/uc05_test.py` | Replace | Test functions per scenario (`run()` aggregator + individual `test_*` callable via `bench execute`) |
| `supplycore/m2_planning/UC_TEST.md` | Modify | Rewrite UC-05 section in detailed format |
| `docs/UC_COVERAGE.md` | Modify | Flip UC-05 row status |

**Test runner pattern (already used in repo, e.g. `uc04_test.py`):**
- Each test = function returning `{"pass": bool, "msg": str}`
- Run individually: `bench --site supplycore execute supplycore.tests.uc05_test.test_<name>`
- Run all: `bench --site supplycore execute supplycore.tests.uc05_test.run`

---

## Task 1: Create `SC Item Reorder` child DocType (skeleton)

**Files:**
- Create: `supplycore/m2_planning/doctype/sc_item_reorder/__init__.py`
- Create: `supplycore/m2_planning/doctype/sc_item_reorder/sc_item_reorder.json`
- Create: `supplycore/m2_planning/doctype/sc_item_reorder/sc_item_reorder.py`

- [ ] **Step 1: Create package marker**

```bash
mkdir -p /home/hoangvietyeuem/frappe-bench/apps/supplycore/supplycore/m2_planning/doctype/sc_item_reorder
```

Write `__init__.py` (empty file):

```python
```

- [ ] **Step 2: Write DocType JSON**

Path: `supplycore/m2_planning/doctype/sc_item_reorder/sc_item_reorder.json`

```json
{
 "actions": [], "creation": "2026-05-11 00:00:00", "doctype": "DocType",
 "engine": "InnoDB", "istable": 1, "track_changes": 0,
 "field_order": [
  "warehouse",
  "safety_stock", "reorder_level",
  "column_break_1",
  "max_stock", "standard_order_qty"
 ],
 "fields": [
  {"fieldname": "warehouse", "fieldtype": "Link", "options": "SC Warehouse",
   "label": "Kho", "reqd": 1, "in_list_view": 1, "columns": 3},
  {"fieldname": "safety_stock", "fieldtype": "Float", "label": "Safety stock",
   "in_list_view": 1, "columns": 2},
  {"fieldname": "reorder_level", "fieldtype": "Float", "label": "Reorder level",
   "in_list_view": 1, "columns": 2},
  {"fieldname": "column_break_1", "fieldtype": "Column Break"},
  {"fieldname": "max_stock", "fieldtype": "Float", "label": "Max stock",
   "in_list_view": 1, "columns": 2},
  {"fieldname": "standard_order_qty", "fieldtype": "Float",
   "label": "Số lượng đặt chuẩn (EOQ)", "in_list_view": 1, "columns": 2}
 ],
 "permissions": [],
 "owner": "Administrator", "modified_by": "Administrator", "modified": "2026-05-11 00:00:00",
 "module": "M2 Planning", "name": "SC Item Reorder"
}
```

- [ ] **Step 3: Write controller (empty subclass)**

Path: `supplycore/m2_planning/doctype/sc_item_reorder/sc_item_reorder.py`

```python
from frappe.model.document import Document


class SCItemReorder(Document):
    pass
```

- [ ] **Step 4: Verify module registration**

```bash
grep -n "M2 Planning" /home/hoangvietyeuem/frappe-bench/apps/supplycore/supplycore/modules.txt
```

Expected: line "M2 Planning" exists. If missing, add it.

- [ ] **Step 5: Commit**

```bash
cd /home/hoangvietyeuem/frappe-bench/apps/supplycore
git add supplycore/m2_planning/doctype/sc_item_reorder/
git commit -m "$(cat <<'EOF'
feat(UC-05): create SC Item Reorder child doctype skeleton

Child table (istable=1) for per-warehouse override of safety_stock,
reorder_level, max_stock, standard_order_qty. Empty controller —
validation lives on parent SC Item.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Add UC-05 fields + section to `SC Item` JSON

**Files:**
- Modify: `supplycore/supplycore/doctype/sc_item/sc_item.json`

- [ ] **Step 1: Update `field_order` (line 11)**

Find:
```json
  "section_planning", "safety_stock", "lead_time_days",
  "column_break_planning", "min_shelf_life_days", "default_supplier",
```

Replace with:
```json
  "section_planning", "safety_stock", "reorder_level", "max_stock",
  "column_break_planning", "standard_order_qty", "lead_time_days",
  "min_shelf_life_days", "default_supplier",
  "section_reorder_overrides", "reorder_levels",
```

- [ ] **Step 2: Update fields array — replace the section_planning block**

Find:
```json
  {"fieldname": "section_planning", "fieldtype": "Section Break", "label": "Kế hoạch & FEFO"},
  {"fieldname": "safety_stock", "fieldtype": "Float", "label": "Safety stock"},
  {"fieldname": "lead_time_days", "fieldtype": "Int", "label": "Lead time NCC (ngày)", "default": "30"},
  {"fieldname": "column_break_planning", "fieldtype": "Column Break"},
  {"fieldname": "min_shelf_life_days", "fieldtype": "Int", "label": "Hạn dùng tối thiểu khi nhập (ngày)", "default": "30"},
  {"fieldname": "default_supplier", "fieldtype": "Link", "options": "SC Supplier", "label": "NCC mặc định"},
```

Replace with:
```json
  {"fieldname": "section_planning", "fieldtype": "Section Break", "label": "Kế hoạch & FEFO"},
  {"fieldname": "safety_stock", "fieldtype": "Float", "label": "Safety stock"},
  {"fieldname": "reorder_level", "fieldtype": "Float", "label": "Reorder level (điểm tái đặt hàng)"},
  {"fieldname": "max_stock", "fieldtype": "Float", "label": "Max stock (mức tồn tối đa)"},
  {"fieldname": "column_break_planning", "fieldtype": "Column Break"},
  {"fieldname": "standard_order_qty", "fieldtype": "Float", "label": "Số lượng đặt hàng chuẩn (EOQ)"},
  {"fieldname": "lead_time_days", "fieldtype": "Int", "label": "Lead time NCC (ngày)", "default": "30"},
  {"fieldname": "min_shelf_life_days", "fieldtype": "Int", "label": "Hạn dùng tối thiểu khi nhập (ngày)", "default": "30"},
  {"fieldname": "default_supplier", "fieldtype": "Link", "options": "SC Supplier", "label": "NCC mặc định"},

  {"fieldname": "section_reorder_overrides", "fieldtype": "Section Break", "label": "Override theo kho", "collapsible": 1, "depends_on": "eval:!doc.__islocal"},
  {"fieldname": "reorder_levels", "fieldtype": "Table", "options": "SC Item Reorder", "label": "Reorder per warehouse"},
```

- [ ] **Step 3: Bump `modified` timestamp (line 75)**

Find:
```json
"modified_by": "Administrator", "modified": "2026-05-07 00:00:00",
```

Replace with:
```json
"modified_by": "Administrator", "modified": "2026-05-11 00:00:00",
```

- [ ] **Step 4: Run `bench migrate` to apply schema**

```bash
cd /home/hoangvietyeuem/frappe-bench
bench --site supplycore migrate
```

Expected: clean run, no SQL errors, `SC Item` table gets 3 new columns and `tabSC Item Reorder` table is created.

- [ ] **Step 5: Verify fields + doctype exist**

```bash
bench --site supplycore execute frappe.db.has_column --kwargs '{"doctype":"SC Item","fieldname":"reorder_level"}'
```

Expected output: `1` (column exists).

```bash
bench --site supplycore execute frappe.db.exists --args '["DocType","SC Item Reorder"]'
```

Expected output: `SC Item Reorder` (string — non-empty means exists).

- [ ] **Step 6: Commit**

```bash
cd /home/hoangvietyeuem/frappe-bench/apps/supplycore
git add supplycore/supplycore/doctype/sc_item/sc_item.json
git commit -m "$(cat <<'EOF'
feat(UC-05): add reorder/max/EOQ fields + per-warehouse table to SC Item

3 Float fields (reorder_level, max_stock, standard_order_qty) in
section_planning; new collapsible section with reorder_levels table
linked to SC Item Reorder. Item-level default + per-warehouse override
via child rows.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: TDD — Negative threshold validation

**Files:**
- Modify: `supplycore/supplycore/doctype/sc_item/sc_item.py`
- Replace: `supplycore/tests/uc05_test.py`

- [ ] **Step 1: Write failing test**

Replace contents of `supplycore/tests/uc05_test.py`:

```python
"""Test UC-05 — Min/Max/Reorder Level scenarios.

Run individual: bench --site supplycore execute supplycore.tests.uc05_test.test_<name>
Run all:        bench --site supplycore execute supplycore.tests.uc05_test.run
"""

import frappe
from frappe.utils import random_string


def _make_item(suffix: str, **kwargs) -> "frappe.model.document.Document":
    """Helper: build a draft SC Item with required fields, do not insert yet."""
    item = frappe.new_doc("SC Item")
    item.item_code = f"UC05-{suffix}-{random_string(5)}"
    item.item_name = f"UC-05 test {suffix}"
    item.uom = frappe.db.get_value("SC UOM", {}, "name") or "Cái"
    item.is_stock_item = 1
    item.is_purchase_item = 1
    item.flags.ignore_permissions = True
    for k, v in kwargs.items():
        setattr(item, k, v)
    return item


def test_negative_threshold_rejected():
    """safety_stock=-1 → throw SC-E-NEGATIVE."""
    item = _make_item("NEG", safety_stock=-1)
    try:
        item.insert()
        return {"pass": False, "msg": "X did not throw on negative safety_stock"}
    except frappe.ValidationError as e:
        msg = str(e)
        if "SC-E-NEGATIVE" in msg:
            return {"pass": True, "msg": f"OK: {msg[:120]}"}
        return {"pass": False, "msg": f"Wrong error code: {msg[:120]}"}


def run():
    """Run all UC-05 tests sequentially, return aggregate."""
    tests = [test_negative_threshold_rejected]
    results = []
    for t in tests:
        try:
            r = t()
            r["test"] = t.__name__
        except Exception as e:
            r = {"test": t.__name__, "pass": False, "msg": f"EXCEPTION: {str(e)[:200]}"}
        results.append(r)
    frappe.db.rollback()
    passed = sum(1 for r in results if r.get("pass"))
    return {"passed": passed, "total": len(results), "results": results}
```

- [ ] **Step 2: Run test, verify it FAILS**

```bash
cd /home/hoangvietyeuem/frappe-bench
bench --site supplycore execute supplycore.tests.uc05_test.test_negative_threshold_rejected
```

Expected output: `{'pass': False, 'msg': 'X did not throw on negative safety_stock'}`

- [ ] **Step 3: Add validation in `SCItem.validate()`**

Path: `supplycore/supplycore/doctype/sc_item/sc_item.py`

Replace entire file contents:

```python
import frappe
from frappe import _
from frappe.model.document import Document


class SCItem(Document):

    def validate(self):
        if self.has_bhyt and not self.bhyt_code:
            frappe.throw(_("Vật tư có BHYT phải nhập mã BHYT"))
        if self.uom_conversion_factor and self.uom_conversion_factor <= 0:
            frappe.throw(_("uom_conversion_factor phải > 0"))
        if not self.use_uom:
            self.use_uom = self.uom
        if not self.buy_uom:
            self.buy_uom = self.uom

        self._validate_thresholds()
        self._validate_lead_time()
        self._validate_reorder_rows()

    def _validate_thresholds(self):
        """UC-05: 4 ngưỡng + lead_time không âm; nếu max_stock>0 phải safety ≤ reorder ≤ max."""
        for fld in ("safety_stock", "reorder_level", "max_stock",
                    "standard_order_qty", "lead_time_days"):
            val = self.get(fld) or 0
            if val < 0:
                frappe.throw(_("SC-E-NEGATIVE: {0} không được âm").format(fld))

    def _validate_lead_time(self):
        # lead_time=0 → warning only, không throw (UC-05 yêu cầu nhập >0 nhưng không cản)
        pass

    def _validate_reorder_rows(self):
        # Per-warehouse rows — implemented in later tasks
        pass
```

- [ ] **Step 4: Run test, verify it PASSES**

```bash
bench --site supplycore execute supplycore.tests.uc05_test.test_negative_threshold_rejected
```

Expected: `{'pass': True, 'msg': 'OK: SC-E-NEGATIVE: safety_stock không được âm...'}`

- [ ] **Step 5: Commit**

```bash
cd /home/hoangvietyeuem/frappe-bench/apps/supplycore
git add supplycore/supplycore/doctype/sc_item/sc_item.py supplycore/tests/uc05_test.py
git commit -m "$(cat <<'EOF'
feat(UC-05): reject negative thresholds on SC Item

Add _validate_thresholds: safety_stock, reorder_level, max_stock,
standard_order_qty, lead_time_days must be >= 0. Throw SC-E-NEGATIVE.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: TDD — `safety ≤ reorder ≤ max` validation

**Files:**
- Modify: `supplycore/supplycore/doctype/sc_item/sc_item.py`
- Modify: `supplycore/tests/uc05_test.py`

- [ ] **Step 1: Add failing tests to `uc05_test.py`**

Add after `test_negative_threshold_rejected`:

```python
def test_min_max_inversion_rejected():
    """safety=10, reorder=5, max=20 → throw SC-E-MIN-MAX."""
    item = _make_item("INV", safety_stock=10, reorder_level=5, max_stock=20)
    try:
        item.insert()
        return {"pass": False, "msg": "X did not throw on safety>reorder"}
    except frappe.ValidationError as e:
        msg = str(e)
        if "SC-E-MIN-MAX" in msg:
            return {"pass": True, "msg": f"OK: {msg[:120]}"}
        return {"pass": False, "msg": f"Wrong error: {msg[:120]}"}


def test_valid_thresholds_pass():
    """safety=5, reorder=10, max=20 → save OK."""
    item = _make_item("OK", safety_stock=5, reorder_level=10, max_stock=20)
    try:
        item.insert()
        frappe.db.rollback()
        return {"pass": True, "msg": f"OK item {item.name} saved"}
    except Exception as e:
        return {"pass": False, "msg": f"X threw: {str(e)[:120]}"}
```

Update `run()` `tests` list:
```python
    tests = [
        test_negative_threshold_rejected,
        test_min_max_inversion_rejected,
        test_valid_thresholds_pass,
    ]
```

- [ ] **Step 2: Run new tests, verify failure mode**

```bash
bench --site supplycore execute supplycore.tests.uc05_test.test_min_max_inversion_rejected
```

Expected: `{'pass': False, 'msg': 'X did not throw on safety>reorder'}`

```bash
bench --site supplycore execute supplycore.tests.uc05_test.test_valid_thresholds_pass
```

Expected: `{'pass': True, 'msg': 'OK item UC05-OK-... saved'}` (passes even without the inversion check)

- [ ] **Step 3: Extend `_validate_thresholds()`**

In `sc_item.py`, replace `_validate_thresholds` method:

```python
    def _validate_thresholds(self):
        """UC-05: 4 ngưỡng + lead_time không âm; nếu max_stock>0 phải safety ≤ reorder ≤ max."""
        for fld in ("safety_stock", "reorder_level", "max_stock",
                    "standard_order_qty", "lead_time_days"):
            val = self.get(fld) or 0
            if val < 0:
                frappe.throw(_("SC-E-NEGATIVE: {0} không được âm").format(fld))

        safety = self.safety_stock or 0
        reorder = self.reorder_level or 0
        max_s = self.max_stock or 0
        if max_s > 0:
            if not (safety <= reorder <= max_s):
                frappe.throw(_(
                    "SC-E-MIN-MAX: Phải thỏa Safety ({0}) ≤ Reorder ({1}) ≤ Max ({2})"
                ).format(safety, reorder, max_s))
```

- [ ] **Step 4: Run both tests, verify PASS**

```bash
bench --site supplycore execute supplycore.tests.uc05_test.test_min_max_inversion_rejected
```

Expected: `{'pass': True, 'msg': 'OK: SC-E-MIN-MAX...'}`

```bash
bench --site supplycore execute supplycore.tests.uc05_test.test_valid_thresholds_pass
```

Expected: `{'pass': True, 'msg': 'OK item UC05-OK-... saved'}`

- [ ] **Step 5: Commit**

```bash
cd /home/hoangvietyeuem/frappe-bench/apps/supplycore
git add supplycore/supplycore/doctype/sc_item/sc_item.py supplycore/tests/uc05_test.py
git commit -m "$(cat <<'EOF'
feat(UC-05): enforce safety<=reorder<=max when max_stock set

Add SC-E-MIN-MAX check on SC Item validate when max_stock>0.
Items without max_stock (default 0) skip the rule — allows partial
config.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: TDD — Duplicate warehouse + row inversion in child table

**Files:**
- Modify: `supplycore/supplycore/doctype/sc_item/sc_item.py`
- Modify: `supplycore/tests/uc05_test.py`

- [ ] **Step 1: Add failing tests**

Add to `uc05_test.py`:

```python
def _ensure_test_warehouse(name: str) -> str:
    """Get or create a stub SC Warehouse for tests."""
    if frappe.db.exists("SC Warehouse", name):
        return name
    wh = frappe.new_doc("SC Warehouse")
    wh.warehouse_name = name
    wh.is_group = 0
    wh.flags.ignore_permissions = True
    wh.insert()
    return wh.name


def test_child_warehouse_duplicate_rejected():
    """2 row override cùng warehouse → throw SC-E-DUPLICATE-WAREHOUSE."""
    wh = _ensure_test_warehouse("UC05 Test WH A")
    item = _make_item("DUP")
    item.append("reorder_levels", {"warehouse": wh, "safety_stock": 5})
    item.append("reorder_levels", {"warehouse": wh, "safety_stock": 10})
    try:
        item.insert()
        return {"pass": False, "msg": "X did not throw on duplicate warehouse"}
    except frappe.ValidationError as e:
        msg = str(e)
        if "SC-E-DUPLICATE-WAREHOUSE" in msg:
            return {"pass": True, "msg": f"OK: {msg[:120]}"}
        return {"pass": False, "msg": f"Wrong error: {msg[:120]}"}


def test_child_row_inversion_rejected():
    """Row safety=10, reorder=5, max=20 → throw SC-E-MIN-MAX."""
    wh = _ensure_test_warehouse("UC05 Test WH B")
    item = _make_item("ROWINV")
    item.append("reorder_levels", {
        "warehouse": wh, "safety_stock": 10,
        "reorder_level": 5, "max_stock": 20,
    })
    try:
        item.insert()
        return {"pass": False, "msg": "X did not throw on row safety>reorder"}
    except frappe.ValidationError as e:
        msg = str(e)
        if "SC-E-MIN-MAX" in msg:
            return {"pass": True, "msg": f"OK: {msg[:120]}"}
        return {"pass": False, "msg": f"Wrong error: {msg[:120]}"}
```

Update `run()` tests list:
```python
    tests = [
        test_negative_threshold_rejected,
        test_min_max_inversion_rejected,
        test_valid_thresholds_pass,
        test_child_warehouse_duplicate_rejected,
        test_child_row_inversion_rejected,
    ]
```

- [ ] **Step 2: Run tests, verify they FAIL**

```bash
bench --site supplycore execute supplycore.tests.uc05_test.test_child_warehouse_duplicate_rejected
```

Expected: `{'pass': False, 'msg': 'X did not throw on duplicate warehouse'}`

```bash
bench --site supplycore execute supplycore.tests.uc05_test.test_child_row_inversion_rejected
```

Expected: `{'pass': False, 'msg': 'X did not throw on row safety>reorder'}`

- [ ] **Step 3: Implement `_validate_reorder_rows()`**

In `sc_item.py`, replace `_validate_reorder_rows` method:

```python
    def _validate_reorder_rows(self):
        """UC-05: per-warehouse override rows. Warehouse unique trong table;
        mỗi row có max_stock>0 phải safety ≤ reorder ≤ max."""
        seen = set()
        for row in (self.get("reorder_levels") or []):
            if not row.warehouse:
                continue
            if row.warehouse in seen:
                frappe.throw(_(
                    "SC-E-DUPLICATE-WAREHOUSE: Kho {0} đã có override — không trùng"
                ).format(row.warehouse))
            seen.add(row.warehouse)

            for fld in ("safety_stock", "reorder_level",
                        "max_stock", "standard_order_qty"):
                val = row.get(fld) or 0
                if val < 0:
                    frappe.throw(_(
                        "SC-E-NEGATIVE: row {0}.{1} không được âm"
                    ).format(row.warehouse, fld))

            safety = row.safety_stock or 0
            reorder = row.reorder_level or 0
            max_s = row.max_stock or 0
            if max_s > 0 and not (safety <= reorder <= max_s):
                frappe.throw(_(
                    "SC-E-MIN-MAX: Row kho {0} — Safety ({1}) ≤ Reorder ({2}) ≤ Max ({3})"
                ).format(row.warehouse, safety, reorder, max_s))
```

- [ ] **Step 4: Run tests, verify PASS**

```bash
bench --site supplycore execute supplycore.tests.uc05_test.test_child_warehouse_duplicate_rejected
```

Expected: `{'pass': True, 'msg': 'OK: SC-E-DUPLICATE-WAREHOUSE...'}`

```bash
bench --site supplycore execute supplycore.tests.uc05_test.test_child_row_inversion_rejected
```

Expected: `{'pass': True, 'msg': 'OK: SC-E-MIN-MAX...'}`

- [ ] **Step 5: Commit**

```bash
cd /home/hoangvietyeuem/frappe-bench/apps/supplycore
git add supplycore/supplycore/doctype/sc_item/sc_item.py supplycore/tests/uc05_test.py
git commit -m "$(cat <<'EOF'
feat(UC-05): validate per-warehouse reorder rows

Enforce unique warehouse per parent (SC-E-DUPLICATE-WAREHOUSE) and
safety<=reorder<=max within each row (SC-E-MIN-MAX). Also re-check
negative thresholds at row level.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: Lead time = 0 warning (no throw)

**Files:**
- Modify: `supplycore/supplycore/doctype/sc_item/sc_item.py`
- Modify: `supplycore/tests/uc05_test.py`

- [ ] **Step 1: Add test**

Add to `uc05_test.py`:

```python
def test_lead_time_zero_warns_not_throws():
    """lead_time_days=0 → save OK (msgprint warning, no throw)."""
    item = _make_item("LT0", lead_time_days=0)
    try:
        item.insert()
        frappe.db.rollback()
        return {"pass": True, "msg": f"OK item {item.name} saved with lead_time=0"}
    except frappe.ValidationError as e:
        return {"pass": False, "msg": f"X threw on lead_time=0: {str(e)[:120]}"}
```

Add to `run()` tests list.

- [ ] **Step 2: Run test**

```bash
bench --site supplycore execute supplycore.tests.uc05_test.test_lead_time_zero_warns_not_throws
```

Expected: `{'pass': True, 'msg': 'OK ...'}`  (already passes because negative check `< 0` doesn't reject 0)

- [ ] **Step 3: Implement msgprint warning**

In `sc_item.py`, replace `_validate_lead_time`:

```python
    def _validate_lead_time(self):
        """UC-05: lead_time=0 → msgprint warning màu cam, không throw."""
        if self.lead_time_days is not None and self.lead_time_days == 0:
            frappe.msgprint(
                _("Lead time = 0 — nên cập nhật giá trị > 0"),
                indicator="orange", alert=True,
            )
```

- [ ] **Step 4: Re-run test (verify still passes)**

```bash
bench --site supplycore execute supplycore.tests.uc05_test.test_lead_time_zero_warns_not_throws
```

Expected: `{'pass': True, ...}` (warning printed to stdout but no throw)

- [ ] **Step 5: Commit**

```bash
cd /home/hoangvietyeuem/frappe-bench/apps/supplycore
git add supplycore/supplycore/doctype/sc_item/sc_item.py supplycore/tests/uc05_test.py
git commit -m "$(cat <<'EOF'
feat(UC-05): warn (not throw) when lead_time_days = 0

Orange msgprint encourages user to set lead time, but does not block
save — Excel imports with missing lead time still succeed.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 7: Migration patch + register

**Files:**
- Create: `supplycore/patches/v0_2/init_uc05_fields.py`
- Modify: `supplycore/patches.txt`

- [ ] **Step 1: Write patch**

Path: `supplycore/patches/v0_2/init_uc05_fields.py`

```python
"""Patch: reload SC Item + SC Item Reorder để UC-05 fields apply trên môi trường
đã migrate trước commit này. Idempotent (reload_doc tự kiểm tra)."""

import frappe


def execute():
    frappe.reload_doc("supplycore", "doctype", "sc_item")
    frappe.reload_doc("m2_planning", "doctype", "sc_item_reorder")
```

- [ ] **Step 2: Register patch in `patches.txt`**

Append a new line at end of `supplycore/patches.txt`:

```
supplycore.patches.v0_2.init_uc05_fields
```

- [ ] **Step 3: Run migrate (idempotency check)**

```bash
cd /home/hoangvietyeuem/frappe-bench
bench --site supplycore migrate
```

Expected: patch executes once, no errors. Subsequent `bench migrate` is no-op (Frappe tracks executed patches in `tabPatch Log`).

- [ ] **Step 4: Verify patch logged**

```bash
bench --site supplycore execute frappe.db.exists --args '["Patch Log",{"patch":"supplycore.patches.v0_2.init_uc05_fields"}]'
```

Expected output: non-empty string (the Patch Log name) — confirms patch ran.

- [ ] **Step 5: Commit**

```bash
cd /home/hoangvietyeuem/frappe-bench/apps/supplycore
git add supplycore/patches/v0_2/init_uc05_fields.py supplycore/patches.txt
git commit -m "$(cat <<'EOF'
chore(UC-05): patch v0_2.init_uc05_fields — reload doctypes

Idempotent reload of SC Item + SC Item Reorder so existing sites pick
up the new fields and child table on next migrate.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 8: TDD — `get_reorder_thresholds()` helper (item-level fallback)

**Files:**
- Create: `supplycore/m2_planning/reorder.py`
- Modify: `supplycore/tests/uc05_test.py`

- [ ] **Step 1: Add failing test**

Add to `uc05_test.py`:

```python
def test_get_reorder_thresholds_item_fallback():
    """No override → return item-level values."""
    from supplycore.m2_planning.reorder import get_reorder_thresholds
    item = _make_item("FB", safety_stock=10, reorder_level=15,
                      max_stock=30, standard_order_qty=20, lead_time_days=7)
    item.insert()
    result = get_reorder_thresholds(item.name)
    frappe.db.rollback()
    expected = {"safety_stock": 10, "reorder_level": 15, "max_stock": 30,
                "standard_order_qty": 20, "lead_time_days": 7}
    for k, v in expected.items():
        if float(result.get(k, -1)) != float(v):
            return {"pass": False, "msg": f"X {k}: expected {v}, got {result.get(k)}"}
    return {"pass": True, "msg": f"OK fallback returns item-level: {result}"}
```

Add to `run()` tests list.

- [ ] **Step 2: Run test, verify it FAILS with ImportError**

```bash
bench --site supplycore execute supplycore.tests.uc05_test.test_get_reorder_thresholds_item_fallback
```

Expected output contains: `ModuleNotFoundError: No module named 'supplycore.m2_planning.reorder'` (or `ImportError`).

- [ ] **Step 3: Write helper**

Path: `supplycore/m2_planning/reorder.py`

```python
"""UC-05: single source of truth for reorder thresholds.

Precedence per field: child row (SC Item Reorder) matching warehouse
with field > 0 → item-level field > 0 → 0.

Consumers: M11 _scan_low_stock, Procurement Plan auto_load_reorder_items.
"""

import frappe
from frappe.utils import flt

FIELDS = ("safety_stock", "reorder_level", "max_stock",
          "standard_order_qty", "lead_time_days")


def get_reorder_thresholds(item: str, warehouse: str = None) -> dict:
    """Return dict with FIELDS keys for given (item, warehouse).

    If warehouse=None → returns item-level only.
    Per-field fallback: row override field=0 → fallback item-level.
    lead_time_days never overrides per-warehouse (UC-05 decision 2).
    """
    item_doc = frappe.db.get_value(
        "SC Item", item,
        ["safety_stock", "reorder_level", "max_stock",
         "standard_order_qty", "lead_time_days"],
        as_dict=True,
    ) or {}
    result = {k: flt(item_doc.get(k) or 0) for k in FIELDS}

    if warehouse:
        row = frappe.db.get_value(
            "SC Item Reorder",
            {"parent": item, "parenttype": "SC Item", "warehouse": warehouse},
            ["safety_stock", "reorder_level", "max_stock", "standard_order_qty"],
            as_dict=True,
        )
        if row:
            for k in ("safety_stock", "reorder_level",
                      "max_stock", "standard_order_qty"):
                v = flt(row.get(k) or 0)
                if v > 0:
                    result[k] = v
    return result
```

- [ ] **Step 4: Run test, verify PASS**

```bash
bench --site supplycore execute supplycore.tests.uc05_test.test_get_reorder_thresholds_item_fallback
```

Expected: `{'pass': True, 'msg': 'OK fallback returns item-level: ...'}`

- [ ] **Step 5: Commit**

```bash
cd /home/hoangvietyeuem/frappe-bench/apps/supplycore
git add supplycore/m2_planning/reorder.py supplycore/tests/uc05_test.py
git commit -m "$(cat <<'EOF'
feat(UC-05): add get_reorder_thresholds helper (item-level fallback)

Single source of truth for reorder lookup. Item-level only when
warehouse=None or no matching override row. Per-field fallback when
override field is 0.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 9: TDD — `get_reorder_thresholds()` per-warehouse override + partial

**Files:**
- Modify: `supplycore/tests/uc05_test.py`

(No source change — Task 8 helper already implements override; this task verifies behavior.)

- [ ] **Step 1: Add test for full override**

```python
def test_get_reorder_thresholds_full_override():
    """Override row > 0 cho mọi field → return override values."""
    from supplycore.m2_planning.reorder import get_reorder_thresholds
    wh = _ensure_test_warehouse("UC05 Test WH C")
    item = _make_item("FULL", safety_stock=10, reorder_level=15, max_stock=30)
    item.append("reorder_levels", {
        "warehouse": wh, "safety_stock": 50, "reorder_level": 70,
        "max_stock": 100, "standard_order_qty": 25,
    })
    item.insert()
    result = get_reorder_thresholds(item.name, warehouse=wh)
    frappe.db.rollback()
    if (float(result["safety_stock"]) == 50.0
        and float(result["reorder_level"]) == 70.0
        and float(result["max_stock"]) == 100.0
        and float(result["standard_order_qty"]) == 25.0):
        return {"pass": True, "msg": f"OK full override: {result}"}
    return {"pass": False, "msg": f"X mismatch: {result}"}


def test_get_reorder_thresholds_partial_override():
    """Override row chỉ set safety_stock; reorder_level/max_stock=0 →
       fallback item-level cho field bỏ trống."""
    from supplycore.m2_planning.reorder import get_reorder_thresholds
    wh = _ensure_test_warehouse("UC05 Test WH D")
    item = _make_item("PART", safety_stock=10, reorder_level=15, max_stock=30)
    item.append("reorder_levels", {"warehouse": wh, "safety_stock": 99})
    item.insert()
    result = get_reorder_thresholds(item.name, warehouse=wh)
    frappe.db.rollback()
    if (float(result["safety_stock"]) == 99.0       # override
        and float(result["reorder_level"]) == 15.0  # fallback
        and float(result["max_stock"]) == 30.0):    # fallback
        return {"pass": True, "msg": f"OK partial override: {result}"}
    return {"pass": False, "msg": f"X mismatch: {result}"}
```

Add both to `run()` tests list.

- [ ] **Step 2: Run tests, verify PASS**

```bash
bench --site supplycore execute supplycore.tests.uc05_test.test_get_reorder_thresholds_full_override
```

Expected: `{'pass': True, 'msg': 'OK full override: ...'}`

```bash
bench --site supplycore execute supplycore.tests.uc05_test.test_get_reorder_thresholds_partial_override
```

Expected: `{'pass': True, 'msg': 'OK partial override: ...'}`

- [ ] **Step 3: Run aggregate to confirm no regression**

```bash
bench --site supplycore execute supplycore.tests.uc05_test.run
```

Expected: `{'passed': N, 'total': N, ...}` where N = all tests (8 at this point), all `pass: True`.

- [ ] **Step 4: Commit**

```bash
cd /home/hoangvietyeuem/frappe-bench/apps/supplycore
git add supplycore/tests/uc05_test.py
git commit -m "$(cat <<'EOF'
test(UC-05): verify per-warehouse override (full + partial)

Confirm helper returns override values when row provides them, and
falls back to item-level field by field when row leaves a field at 0.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 10: TDD — M11 `_scan_low_stock` per-warehouse override

**Files:**
- Modify: `supplycore/m11_dashboard/tasks.py`
- Modify: `supplycore/tests/uc05_test.py`

- [ ] **Step 1: Add failing integration test**

Add to `uc05_test.py`:

```python
def _ensure_low_stock_rule():
    """Get or create an active SC Alert Rule for low_stock."""
    existing = frappe.db.exists("SC Alert Rule", {"alert_type": "low_stock", "enabled": 1})
    if existing:
        return frappe.get_doc("SC Alert Rule", existing)
    rule = frappe.new_doc("SC Alert Rule")
    rule.title = "UC-05 Low Stock Test"
    rule.alert_type = "low_stock"
    rule.severity = "Medium"
    rule.enabled = 1
    rule.flags.ignore_permissions = True
    rule.insert()
    return rule


def test_low_stock_alert_per_warehouse():
    """Item có override WH-X safety=50, qty WH-X=30 → alert chỉ tạo cho (item, WH-X)."""
    from supplycore.m11_dashboard.tasks import _scan_low_stock
    from frappe.utils import today, add_days

    wh_a = _ensure_test_warehouse("UC05 Alert WH A")
    wh_b = _ensure_test_warehouse("UC05 Alert WH B")
    item = _make_item("ALERTWH", safety_stock=0)  # item-level=0, only override matters
    item.append("reorder_levels", {"warehouse": wh_a, "safety_stock": 50})
    item.insert()

    # Seed SLE: WH-A has 30 (below safety 50), WH-B has 200 (no override)
    for (wh, qty) in [(wh_a, 30), (wh_b, 200)]:
        sle = frappe.new_doc("SC Stock Ledger Entry")
        sle.item = item.name
        sle.warehouse = wh
        sle.qty_change = qty
        sle.posting_date = today()
        sle.is_cancelled = 0
        sle.flags.ignore_permissions = True
        sle.insert()

    # Clean previous alerts for this item
    frappe.db.delete("SC Alert", {"reference_doctype": "SC Item", "reference_name": item.name})

    rule = _ensure_low_stock_rule()
    rule_proxy = frappe._dict({
        "name": rule.name, "alert_type": "low_stock", "severity": "Medium"
    })
    created = _scan_low_stock(rule_proxy)
    alerts = frappe.get_all("SC Alert",
        filters={"reference_doctype": "SC Item", "reference_name": item.name, "resolved": 0},
        fields=["message"])
    frappe.db.rollback()

    if len(alerts) == 1 and "UC05 Alert WH A" in alerts[0].message:
        return {"pass": True, "msg": f"OK 1 alert for WH-A only: {alerts[0].message[:120]}"}
    return {"pass": False, "msg": f"X expected 1 alert WH-A, got {len(alerts)}: {[a.message[:60] for a in alerts]}"}
```

Add to `run()` tests list.

- [ ] **Step 2: Run test, verify it FAILS**

```bash
bench --site supplycore execute supplycore.tests.uc05_test.test_low_stock_alert_per_warehouse
```

Expected: `{'pass': False, 'msg': 'X expected 1 alert WH-A, got 0: []'}` (current `_scan_low_stock` requires item-level `safety_stock > 0` — our test sets item-level to 0).

- [ ] **Step 3: Rewrite `_scan_low_stock`**

In `supplycore/m11_dashboard/tasks.py`, replace the entire `_scan_low_stock` function (lines 135-150):

```python
def _scan_low_stock(rule) -> int:
    """Scan items below safety_stock.

    UC-05: support per-warehouse override via SC Item Reorder child rows.
    - Items với override rows (safety_stock>0) → scan per (item, warehouse)
    - Items KHÔNG có override rows → fallback item-level (logic cũ)
    """
    rows_wh = frappe.db.sql("""
        SELECT r.parent AS item, i.item_name, r.warehouse,
               COALESCE(SUM(sle.qty_change), 0) AS qty,
               r.safety_stock
        FROM `tabSC Item Reorder` r
        JOIN `tabSC Item` i ON i.name = r.parent
        LEFT JOIN `tabSC Stock Ledger Entry` sle
            ON sle.item = r.parent AND sle.warehouse = r.warehouse
           AND sle.is_cancelled = 0
        WHERE i.disabled = 0 AND i.is_stock_item = 1
          AND r.parenttype = 'SC Item'
          AND COALESCE(r.safety_stock, 0) > 0
        GROUP BY r.parent, r.warehouse, r.safety_stock, i.item_name
        HAVING qty < r.safety_stock
        LIMIT 50
    """, as_dict=True)

    rows_item = frappe.db.sql("""
        SELECT i.name AS item, i.item_name, NULL AS warehouse,
               COALESCE(SUM(sle.qty_change), 0) AS qty,
               i.safety_stock
        FROM `tabSC Item` i
        LEFT JOIN `tabSC Stock Ledger Entry` sle
            ON sle.item = i.name AND sle.is_cancelled = 0
        WHERE i.disabled = 0 AND i.is_stock_item = 1
          AND i.safety_stock > 0
          AND NOT EXISTS (
              SELECT 1 FROM `tabSC Item Reorder` r
              WHERE r.parent = i.name AND r.parenttype = 'SC Item'
                AND COALESCE(r.safety_stock, 0) > 0
          )
        GROUP BY i.name, i.item_name, i.safety_stock
        HAVING qty < i.safety_stock
        LIMIT 50
    """, as_dict=True)

    def _title(r):
        if r.warehouse:
            return f"Item {r.item} dưới safety stock @ {r.warehouse}"
        return f"Item {r.item} dưới safety stock"

    def _msg(r):
        if r.warehouse:
            return f"{r.item_name} @ {r.warehouse}: tồn {r.qty} < safety {r.safety_stock}"
        return f"{r.item_name}: tồn {r.qty} < safety {r.safety_stock}"

    return _create_alerts_dedup(rule, rows_wh + rows_item, _title, _msg,
                                  lambda r: ("SC Item", r.item))
```

- [ ] **Step 4: Run test, verify PASS**

```bash
bench --site supplycore execute supplycore.tests.uc05_test.test_low_stock_alert_per_warehouse
```

Expected: `{'pass': True, 'msg': 'OK 1 alert for WH-A only: ...UC05 Alert WH A...'}`

- [ ] **Step 5: Regression test — verify item-level still works**

Add to `uc05_test.py`:

```python
def test_low_stock_alert_item_level_regression():
    """Item KHÔNG có override + safety_stock=10 + qty=5 → alert tạo (logic cũ)."""
    from supplycore.m11_dashboard.tasks import _scan_low_stock
    from frappe.utils import today

    wh = _ensure_test_warehouse("UC05 Alert WH C")
    item = _make_item("ALERTLEG", safety_stock=10)  # no override rows
    item.insert()

    sle = frappe.new_doc("SC Stock Ledger Entry")
    sle.item = item.name
    sle.warehouse = wh
    sle.qty_change = 5
    sle.posting_date = today()
    sle.is_cancelled = 0
    sle.flags.ignore_permissions = True
    sle.insert()

    frappe.db.delete("SC Alert", {"reference_doctype": "SC Item", "reference_name": item.name})
    rule = _ensure_low_stock_rule()
    rule_proxy = frappe._dict({
        "name": rule.name, "alert_type": "low_stock", "severity": "Medium"
    })
    _scan_low_stock(rule_proxy)
    alerts = frappe.get_all("SC Alert",
        filters={"reference_doctype": "SC Item", "reference_name": item.name, "resolved": 0},
        fields=["message"])
    frappe.db.rollback()

    if len(alerts) == 1 and "@ " not in alerts[0].message:
        return {"pass": True, "msg": f"OK item-level alert: {alerts[0].message[:120]}"}
    return {"pass": False, "msg": f"X expected 1 item-level alert, got {len(alerts)}"}
```

Add to `run()`.

```bash
bench --site supplycore execute supplycore.tests.uc05_test.test_low_stock_alert_item_level_regression
```

Expected: `{'pass': True, 'msg': 'OK item-level alert: ...'}`

- [ ] **Step 6: Commit**

```bash
cd /home/hoangvietyeuem/frappe-bench/apps/supplycore
git add supplycore/m11_dashboard/tasks.py supplycore/tests/uc05_test.py
git commit -m "$(cat <<'EOF'
feat(UC-05): _scan_low_stock per-warehouse override aware

Two-query merge: items with SC Item Reorder rows (safety_stock>0) scan
per (item, warehouse); items without override fall back to item-level
(legacy behavior). Alert message includes warehouse when per-WH.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 11: TDD — Procurement Plan `auto_load_reorder_items`

**Files:**
- Modify: `supplycore/m2_planning/doctype/procurement_plan/procurement_plan.py`
- Modify: `supplycore/tests/uc05_test.py`

- [ ] **Step 1: Add failing test**

Add to `uc05_test.py`:

```python
def test_procurement_plan_auto_load_reorder():
    """UC-06 button: item with reorder_level=20, current=10 → load to plan,
    suggested_qty = standard_order_qty when set."""
    from frappe.utils import today, add_days

    wh = _ensure_test_warehouse("UC05 PP WH")
    item = _make_item("PPRO",
                       safety_stock=5, reorder_level=20, max_stock=100,
                       standard_order_qty=40)
    item.insert()

    sle = frappe.new_doc("SC Stock Ledger Entry")
    sle.item = item.name
    sle.warehouse = wh
    sle.qty_change = 10  # below reorder_level (20)
    sle.posting_date = today()
    sle.is_cancelled = 0
    sle.flags.ignore_permissions = True
    sle.insert()

    plan = frappe.new_doc("Procurement Plan")
    plan.plan_date = today()
    plan.period_type = "Monthly"
    plan.from_date = today()
    plan.to_date = add_days(today(), 30)
    plan.warehouse = wh
    plan.required_by = add_days(today(), 14)
    plan.remarks = "UC05-AUTO-LOAD"
    plan.flags.ignore_permissions = True
    plan.insert()

    res = plan.auto_load_reorder_items()
    plan.reload()
    matching = [r for r in plan.items if r.item_code == item.name]
    frappe.db.rollback()

    if not matching:
        return {"pass": False, "msg": f"X item not loaded. items={[r.item_code for r in plan.items]}"}
    row = matching[0]
    if abs(float(row.planned_qty) - 40.0) < 0.01:
        return {"pass": True, "msg": f"OK loaded with qty=40 (EOQ): {row.item_code}"}
    return {"pass": False, "msg": f"X qty mismatch: expected 40, got {row.planned_qty}"}
```

Add to `run()`.

- [ ] **Step 2: Run test, verify FAIL**

```bash
bench --site supplycore execute supplycore.tests.uc05_test.test_procurement_plan_auto_load_reorder
```

Expected: `AttributeError: 'ProcurementPlan' object has no attribute 'auto_load_reorder_items'`

- [ ] **Step 3: Add method to `procurement_plan.py`**

In `supplycore/m2_planning/doctype/procurement_plan/procurement_plan.py`, add this method to the `ProcurementPlan` class (after `make_material_request` at line 161):

```python
    @frappe.whitelist()
    def auto_load_reorder_items(self):
        """UC-05/UC-06 hybrid: load items whose current_qty <= reorder_level
        (threshold-based, complements consumption-based auto_load_items)."""
        from supplycore.m2_planning.reorder import get_reorder_thresholds

        if self.docstatus != 0:
            frappe.throw(_("Chỉ load items khi Plan ở Draft"))
        if not self.warehouse:
            frappe.throw(_("Chọn Warehouse trước"))

        candidates = frappe.db.sql("""
            SELECT i.name AS item_code, i.item_name, i.uom AS stock_uom,
                   COALESCE(i.lead_time_days, 30) AS lead_time_days
            FROM `tabSC Item` i
            WHERE i.disabled = 0
              AND i.is_stock_item = 1
              AND i.is_purchase_item = 1
              AND (
                  i.reorder_level > 0
                  OR EXISTS (
                      SELECT 1 FROM `tabSC Item Reorder` r
                      WHERE r.parent = i.name AND r.parenttype = 'SC Item'
                        AND r.warehouse = %(warehouse)s AND r.reorder_level > 0
                  )
              )
            ORDER BY i.item_code
            LIMIT 500
        """, {"warehouse": self.warehouse}, as_dict=True)

        self.items = []
        added = 0
        for it in candidates:
            th = get_reorder_thresholds(it.item_code, self.warehouse)
            reorder = th["reorder_level"]
            if reorder <= 0:
                continue
            current = self._get_current_stock(it.item_code, self.warehouse)
            if current > reorder:
                continue

            if th["standard_order_qty"] > 0:
                qty = th["standard_order_qty"]
            elif th["max_stock"] > 0:
                qty = max(0.0, th["max_stock"] - current)
            else:
                qty = max(0.0, reorder * 2 - current)

            self.append("items", {
                "item_code": it.item_code,
                "item_name": it.item_name,
                "uom": it.stock_uom,
                "current_stock": current,
                "avg_monthly_consumption": 0,
                "lead_time_days": it.lead_time_days,
                "safety_stock_qty": th["safety_stock"],
                "planned_qty": round(qty, 2),
                "estimated_unit_cost": self._get_last_purchase_rate(it.item_code),
                "preferred_supplier": self._get_preferred_supplier(it.item_code),
            })
            added += 1

        self._compute_amounts()
        self.save(ignore_permissions=False)
        return {"items_loaded": added, "total_estimated_cost": self.total_estimated_cost}
```

- [ ] **Step 4: Run test, verify PASS**

```bash
bench --site supplycore execute supplycore.tests.uc05_test.test_procurement_plan_auto_load_reorder
```

Expected: `{'pass': True, 'msg': 'OK loaded with qty=40 (EOQ): UC05-PPRO-...'}`

- [ ] **Step 5: Commit**

```bash
cd /home/hoangvietyeuem/frappe-bench/apps/supplycore
git add supplycore/m2_planning/doctype/procurement_plan/procurement_plan.py supplycore/tests/uc05_test.py
git commit -m "$(cat <<'EOF'
feat(UC-05/06): auto_load_reorder_items — threshold-based loader

Complements consumption-based auto_load_items. Suggested qty
precedence: standard_order_qty > max_stock-current > reorder*2-current.
Uses get_reorder_thresholds helper for per-warehouse override.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 12: JS button on Procurement Plan form

**Files:**
- Modify: `supplycore/m2_planning/doctype/procurement_plan/procurement_plan.js`

- [ ] **Step 1: Read existing button code**

```bash
grep -n "add_custom_button" /home/hoangvietyeuem/frappe-bench/apps/supplycore/supplycore/m2_planning/doctype/procurement_plan/procurement_plan.js
```

Locate the existing "Tự nạp danh mục từ lịch sử tiêu thụ" button block.

- [ ] **Step 2: Add new button immediately after existing auto-load button**

In `procurement_plan.js`, find the block:
```js
        if (frm.doc.docstatus === 0 && frm.doc.warehouse) {
            frm.add_custom_button(__("Tự nạp danh mục từ lịch sử tiêu thụ"), () => {
                ...
            });
        }
```

Add a sibling block immediately after the closing `});` of that existing button (still inside `refresh(frm)`):

```js
        if (frm.doc.docstatus === 0 && frm.doc.warehouse) {
            frm.add_custom_button(__("Tự nạp theo Reorder Level (UC-05)"), () => {
                frappe.confirm(
                    __("Sẽ tự nạp items có tồn ≤ reorder_level tại kho {0}. Tiếp tục?",
                       [frm.doc.warehouse]),
                    () => {
                        frm.call({
                            method: "auto_load_reorder_items",
                            doc: frm.doc,
                            freeze: true,
                            freeze_message: __("Đang quét reorder level..."),
                            callback: (r) => {
                                if (r.message) {
                                    frappe.show_alert({
                                        message: __("Đã nạp {0} items, tổng ước tính {1}",
                                            [r.message.items_loaded,
                                             format_currency(r.message.total_estimated_cost, "VND")]),
                                        indicator: "green",
                                    });
                                    frm.reload_doc();
                                }
                            },
                        });
                    },
                );
            });
        }
```

- [ ] **Step 3: Clear browser cache + run bench build**

```bash
cd /home/hoangvietyeuem/frappe-bench
bench --site supplycore clear-cache
bench build --app supplycore
```

Expected: build completes (~10-30s), no JS errors in output.

- [ ] **Step 4: Manual verify in browser**

1. Open `https://<site>/app/procurement-plan/new`
2. Fill: warehouse, plan_date, from_date, to_date
3. Save (Ctrl+S) — Plan in Draft
4. Confirm button "Tự nạp theo Reorder Level (UC-05)" appears in menu
5. Click → confirm dialog → if items below reorder exist, plan rows populate

Record outcome:

```bash
# After manual test, note pass/fail in this checklist
```

- [ ] **Step 5: Commit**

```bash
cd /home/hoangvietyeuem/frappe-bench/apps/supplycore
git add supplycore/m2_planning/doctype/procurement_plan/procurement_plan.js
git commit -m "$(cat <<'EOF'
feat(UC-05): JS button — Tự nạp theo Reorder Level

Calls auto_load_reorder_items whitelisted method. Confirms before
clearing existing rows; shows green toast with item count + total cost.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 13: Rewrite UC-05 section in `m2_planning/UC_TEST.md`

**Files:**
- Modify: `supplycore/m2_planning/UC_TEST.md`

- [ ] **Step 1: Replace UC-05 section**

In `supplycore/m2_planning/UC_TEST.md`, find the block starting `## UC-05 — Cấu hình Min/Max & Reorder Level` (line 9) up to (but not including) `## UC-06 — Procurement Plan định kỳ` (line 34).

Replace with:

```markdown
## UC-05 — Cấu hình Min/Max & Reorder Level

**Actor:** Storekeeper / Manager
**Status:** ✅ OK (enhanced 2026-05-11 — full per-warehouse override + 4 thresholds + EOQ)
**Pre-condition:** SC Item đã có; SC Warehouse seed sẵn.

### Test scenario (6 bước theo Phase 1)

1. **Mở SC Item**: `/app/sc-item/<code>` (item hiện có) hoặc `/app/sc-item/new`.
2. **Section "Kế hoạch & FEFO"** — set 5 field item-level:
   - `safety_stock` (mức an toàn — trigger M11 alert `low_stock`)
   - `reorder_level` (điểm tái đặt hàng — trigger UC-06 auto-load)
   - `max_stock` (mức tối đa)
   - `standard_order_qty` (số lượng đặt hàng chuẩn — EOQ)
   - `lead_time_days` (mặc định 30; = 0 → warning màu cam)
3. **Section "Override theo kho"** (collapsible) — optional:
   - Add row: chọn warehouse + override 4 ngưỡng (field bỏ trống = fallback item-level)
   - Mỗi kho chỉ 1 row (validate dedup)
4. **Save (Ctrl+S)** — validate:
   - Tất cả ngưỡng ≥ 0 (`SC-E-NEGATIVE`)
   - Nếu `max_stock > 0`: phải `safety ≤ reorder ≤ max` (`SC-E-MIN-MAX`)
   - Child rows: cùng quy tắc + warehouse unique (`SC-E-DUPLICATE-WAREHOUSE`)
5. **Verify M11 alert**: thiết lập SC Alert Rule `low_stock` enabled → `bench execute supplycore.m11_dashboard.tasks.run_alert_scan` (hoặc đợi daily scheduler) → SC Alert tạo cho item có `qty < safety_stock` (per-warehouse nếu có override row).
6. **Verify UC-06 auto-load**: mở Procurement Plan draft → chọn warehouse → click **"Tự nạp theo Reorder Level (UC-05)"** → items có `current_qty ≤ reorder_level` tự fill vào plan với `planned_qty = standard_order_qty` (nếu set).

### Luồng thay thế

- **3a — Excel import hàng loạt:**
  - `/app/data-import/new` → Document Type = `SC Item`, Import Type = `Update Existing Records`
  - Cols: `id, safety_stock, reorder_level, max_stock, standard_order_qty, lead_time_days`
  - Upload → Frappe gọi `validate()` per row → lỗi vào import log
  - Per-warehouse: Document Type = `SC Item Reorder` với cols `parent, parenttype, parentfield, warehouse, safety_stock, reorder_level, max_stock, standard_order_qty`
  - Permissions: Frappe Data Import default = `System Manager` only

### Negative tests

- `safety_stock=-1` → throw `SC-E-NEGATIVE`
- `safety=10, reorder=5, max=20` → throw `SC-E-MIN-MAX`
- Child rows 2 row cùng warehouse → throw `SC-E-DUPLICATE-WAREHOUSE`
- Child row `safety=10, reorder=5, max=20` → throw `SC-E-MIN-MAX`

### Xử lý ngoại lệ

- `lead_time_days = 0` → msgprint warning màu cam "Lead time = 0 — nên cập nhật giá trị > 0" (KHÔNG throw, save OK)

### Hậu điều kiện

- Ngưỡng lưu trên `SC Item` + child `SC Item Reorder`.
- M11 `_scan_low_stock` quét daily — tạo SC Alert per (item, warehouse) nếu có override, hoặc item-level fallback.
- Procurement Plan có thể auto-load items theo reorder_level qua button mới.

### Checklist Pass/Fail

- [ ] Set 5 thresholds item-level cho 1 SC Item → save OK
- [ ] Set per-warehouse override row → save OK
- [ ] Negative: `safety_stock=-1` → SC-E-NEGATIVE
- [ ] Negative: safety>reorder hoặc reorder>max → SC-E-MIN-MAX
- [ ] Negative: 2 row override cùng warehouse → SC-E-DUPLICATE-WAREHOUSE
- [ ] `lead_time_days=0` → warning màu cam, không cản save
- [ ] Excel import SC Item với 5 thresholds → import log success
- [ ] M11 `_scan_low_stock`: item có override WH-A safety=50, qty=30 → alert chỉ tạo cho (item, WH-A)
- [ ] M11 `_scan_low_stock`: item không có override + safety=10 + qty=5 → alert item-level (regression)
- [ ] Procurement Plan button "Tự nạp theo Reorder Level" → items dưới reorder_level fill với qty=standard_order_qty

---

```

- [ ] **Step 2: Commit**

```bash
cd /home/hoangvietyeuem/frappe-bench/apps/supplycore
git add supplycore/m2_planning/UC_TEST.md
git commit -m "$(cat <<'EOF'
docs(UC-05): rewrite UC_TEST section — full Phase 1 detail

6-step scenario, Excel import alt flow, 4 negative cases, lead_time=0
exception, 10-item checklist. Status flip to ✅ enhanced 2026-05-11.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 14: Update `docs/UC_COVERAGE.md` UC-05 row

**Files:**
- Modify: `docs/UC_COVERAGE.md`

- [ ] **Step 1: Find UC-05 row in coverage doc**

```bash
grep -n "UC-05" /home/hoangvietyeuem/frappe-bench/apps/supplycore/docs/UC_COVERAGE.md
```

- [ ] **Step 2: Update status column**

Identify the UC-05 row (typically a markdown table row). Update its status column from `⚠ Partial` / `✅ OK (stub)` (or whatever current value) to:

```
| UC-05 | Min/Max/Reorder Level | M2 | Storekeeper/Manager | ✅ OK | 2026-05-11 — full per-WH + 4 thresholds + EOQ |
```

Match the exact column count and separator format of surrounding rows. If unsure of layout, read the file first:

```bash
grep -B2 -A1 "UC-05" /home/hoangvietyeuem/frappe-bench/apps/supplycore/docs/UC_COVERAGE.md
```

- [ ] **Step 3: Commit**

```bash
cd /home/hoangvietyeuem/frappe-bench/apps/supplycore
git add docs/UC_COVERAGE.md
git commit -m "$(cat <<'EOF'
docs(UC_COVERAGE): flip UC-05 to ✅ OK after Phase 1 implementation

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 15: Final verification gate

**Files:** none modified

- [ ] **Step 1: Run full UC-05 test aggregate**

```bash
cd /home/hoangvietyeuem/frappe-bench
bench --site supplycore execute supplycore.tests.uc05_test.run
```

Expected: `{'passed': 10, 'total': 10, 'results': [...]}` — all tests pass.

If any test fails: open the failing test result, fix the code, re-run. Do NOT proceed until all pass.

- [ ] **Step 2: Run smoke_m2 regression**

```bash
bench --site supplycore execute supplycore.tests.smoke_m2.run
```

Expected: `{'status': 'ok', 'results': [...]}` — Procurement Plan + MR flow still works after our changes.

- [ ] **Step 3: Run smoke_integration**

```bash
bench --site supplycore execute supplycore.tests.smoke_integration.run
```

Expected: end-to-end flow still passes; no regression in M1/M3/M11.

- [ ] **Step 4: Manual smoke — fresh SC Item form load**

1. Open browser: `https://<site>/app/sc-item/new`
2. Fill required fields (item_code, item_name, uom)
3. Confirm section "Kế hoạch & FEFO" shows 5 fields (safety, reorder, max, EOQ, lead_time)
4. Save → confirm "Override theo kho" section now appears (was hidden when `__islocal`)
5. Expand it → add 1 override row → save again → confirm validate runs

- [ ] **Step 5: Manual smoke — Frappe Data Import**

1. Open `/app/data-import/new`
2. Document Type = `SC Item`, Import Type = `Update Existing Records`
3. Download template
4. Edit 1 row with `id=<existing item>`, `safety_stock=5`, `reorder_level=10`, `max_stock=20`, `standard_order_qty=15`, `lead_time_days=7`
5. Save xlsx, upload, click Start Import
6. Expected: import log shows "Updated 1 record" with no errors

- [ ] **Step 6: Manual smoke — M11 alert scan**

```bash
bench --site supplycore execute supplycore.m11_dashboard.tasks.scan_alerts
```

Expected: returns total alerts created (integer). Open `/app/sc-alert?resolved=0` and confirm low_stock alerts include warehouse info for items with per-WH overrides.

- [ ] **Step 7: Final check — git status clean**

```bash
cd /home/hoangvietyeuem/frappe-bench/apps/supplycore
git status
```

Expected: branch ahead of `origin/main` by 12+ commits, no uncommitted changes.

- [ ] **Step 8: Tag completion**

Print summary to confirm done:

```bash
git log --oneline origin/main..HEAD | head -20
```

Confirm commits cover: SC Item Reorder skeleton, SC Item fields, 4 validation tasks, patch, helper, M11 wiring, Procurement Plan method + button, UC_TEST update, UC_COVERAGE flip.

---

## Out-of-scope (defer Phase 1.1+)

Documented in spec section 14. Do not implement in this plan:
- Dedicated Reorder Level Manager screen
- Auto-EOQ formula calculation
- Lead time per-supplier override
- Custom bulk import UI
- Excel template mẫu lưu repo
- Granting SC Storekeeper access to Data Import
