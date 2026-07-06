# Task 10 Report — Purge leftover hospital ROLE strings

Scope: remove the 4 hospital role names (`BHYT Officer`, `Pharmacy Officer`,
`Department Requester`, `SupplyCore Ward Staff`) — and stray `Ward Staff`
mentions — from every source file inside `supplycore/` (doctype permission
JSONs, role-list `.py` files, the `v0_1` role-creation patch, seed scripts,
and UC/README docs), then add a DB-cleanup patch to drop the orphan `Role`
records.

## 1. Doctype permission JSONs — removed hospital-role permission entries

| File | Removed roles |
|---|---|
| `m6_transfer/doctype/sc_transfer_request/sc_transfer_request.json` | SupplyCore Ward Staff, Pharmacy Officer |
| `m10_traceability/doctype/sc_recall_notice/sc_recall_notice.json` | Pharmacy Officer |
| `m1_contract/doctype/framework_contract/framework_contract.json` | Pharmacy Officer |
| `m4_wms/doctype/bin_location/bin_location.json` | SupplyCore Ward Staff, Pharmacy Officer |
| `supplycore/doctype/sc_item/sc_item.json` | SupplyCore Ward Staff, Pharmacy Officer |
| `m5_fefo/doctype/batch_expiry_alert/batch_expiry_alert.json` | Pharmacy Officer |
| `supplycore/doctype/sc_warehouse/sc_warehouse.json` | SupplyCore Ward Staff, Pharmacy Officer |
| `supplycore/doctype/sc_department/sc_department.json` | SupplyCore Ward Staff, Pharmacy Officer |
| `m11_dashboard/doctype/sc_alert/sc_alert.json` | SupplyCore Ward Staff, Pharmacy Officer |
| `supplycore/doctype/sc_batch/sc_batch.json` | Pharmacy Officer, SupplyCore Ward Staff |
| `supplycore/doctype/sc_material_request/sc_material_request.json` | SupplyCore Ward Staff |
| `supplycore/doctype/sc_stock_entry/sc_stock_entry.json` | Pharmacy Officer, SupplyCore Ward Staff |

All entries for surviving roles were kept unchanged. No permission list was
emptied out (each doctype still has at least `System Manager` +
`SupplyCore Manager`).
`Department Requester` and `BHYT Officer` did not appear in any doctype
permissions array (grep confirmed) — only in `api/access.py` / `api/users.py`.

**JSON validity**: `python3 -c "import json,glob; [json.load(open(f)) for f in glob.glob('supplycore/**/*.json', recursive=True)]"` over all 59 non-backup/non-pycache JSON files → **0 errors**.

## 2. Role-list `.py` files

- **`api/access.py`** — removed `BHYT Officer` from `m0`; `Department Requester`
  from `m2` and `m6`; `Pharmacy Officer` from `m5`, `m10`, `alerts`,
  `data_io`, `batch_trace`; `Pharmacy Officer` + `SupplyCore Ward Staff` from
  `stock_balance` and `warehouse_map`. Checked every list stayed non-empty
  after removal (smallest is `m2`: `["System Manager","SupplyCore Manager","SupplyCore Purchaser","SupplyCore Auditor"]`) —
  no permission-check semantics changed (still `_has_any` over a non-empty
  set), no concerns.
- **`api/kpi.py`** — removed the `"Pharmacy Officer": [...]` entry from
  `ROLE_WIDGETS`, and removed it from the priority tuple in
  `get_dashboard_for_role()`. If no role matches, the existing fallback
  (`role = "SupplyCore Manager"`) still applies — behavior for a
  hypothetical Pharmacy-Officer-only user is now "default minimal view"
  instead of a dedicated widget set, which is correct post-pivot (role no
  longer exists).
- **`api/users.py`** — removed the 4 whole `ROLE_GUIDE` dict entries
  (`SupplyCore Ward Staff`, `Pharmacy Officer`, `BHYT Officer`,
  `Department Requester`) including their `vn_name`/`duties`/`limits`/`modules`
  blocks. `list_roles()`, `_user_to_row()`, `update_user_roles()` all key off
  `ROLE_GUIDE` dynamically — no code-path assumed a fixed role count, so
  nothing else needed touching.
- **`m5_fefo/api/fefo_picker.py`** — removed `'Pharmacy Officer'` from the
  SQL `role IN (...)` clause in `_send_expiry_email()`'s recipient lookup;
  `'SupplyCore Storekeeper', 'SupplyCore Manager'` remain, so the alert
  email still has recipients.

## 3. `patches/v0_1/create_supplycore_roles.py`

Removed `"SupplyCore Ward Staff"` from `URS_ROLES`. This was the only one
of the 4 hospital roles created by this patch (`BHYT Officer`,
`Pharmacy Officer`, `Department Requester` were never in this list — grepped
the whole `patches/` tree to confirm no other patch created them). Patch
already ran historically; this edit is source-cleanliness only, confirmed
by task brief and not re-triggered (frappe patch log already has this patch
marked executed).

## 4. Hospital seed files

- **`setup/seed_hospital_users.py`** — **deleted** (`git rm`). Inspected: the
  entire file seeds 6 `@bv.local` hospital job-title accounts (Trưởng phòng
  Vật tư, NV Mua sắm, Thủ kho Trung tâm, Điều dưỡng trưởng, Kế toán Thanh
  toán, Dược sĩ/KCS) with hospital passwords (`BvVattu@2026` etc.) and one
  of them is hard-assigned the `Pharmacy Officer` role and another
  `SupplyCore Ward Staff`. Nothing generic in it (no reusable helper, not
  imported anywhere else — grepped). Confirmed no other file imports
  `seed_hospital_users`.
- **`setup/seed_test_users.py`** — removed the `test.pharmacy@sc.local` /
  `"Pharmacy Officer"` row from `TEST_USERS`. The other 8 rows (storekeeper,
  accountant, executive, purchaser, auditor, warehouse, qc, manager) are all
  surviving roles and were left untouched.

## 5. DB-cleanup patch `v0_7.remove_hospital_roles`

Created:
- `supplycore/patches/v0_7/__init__.py` (empty)
- `supplycore/patches/v0_7/remove_hospital_roles.py` — idempotent, per spec:
  loops `HOSPITAL_ROLES`, `frappe.delete_doc("Role", role, force=True, ignore_missing=True)` + commit if the Role exists.

Registered in `patches.txt`: appended
`supplycore.patches.v0_7.remove_hospital_roles` after
`v0_6.remove_hospital_domain`.

**Reference that could have blocked deletion**: before migrate, `tabDocPerm`
still had ~19 rows referencing the 4 roles (stale — synced from the
doctype JSONs *before* this task's edits). Because the patch runs (in the
normal `bench migrate` patch phase) before the DocType-JSON→DB sync phase,
and `force=True` bypasses Frappe's link-integrity check on delete, the
`Role` docs deleted cleanly despite those still-stale `DocPerm` rows; the
subsequent DocType sync in the same `migrate` run then removed the stale
`DocPerm` rows itself (verified empty afterwards — see below). No manual
DocPerm cleanup was required. `tabHas Role` had 0 rows for these roles (no
user had them assigned), so no user-role cleanup was needed either.

## Verify

- `python3 -m compileall -q supplycore/api supplycore/m5_fefo supplycore/patches supplycore/setup` → clean, exit 0.
- All doctype JSONs parse via `json.load` → 0 errors (59 files).
- `bench --site supplycore-miyano.local migrate` → completed, reached
  "Updating Dashboard for supplycore" / "Executing `after_migrate` hooks..."
  with no traceback; `v0_7.remove_hospital_roles` patch printed
  `Success: Done in 0.163s`.
- `bench --site supplycore-miyano.local execute frappe.ping` → `"pong"`.
- Role-gone query:
  `bench --site supplycore-miyano.local execute frappe.client.get_list --kwargs '{"doctype":"Role","filters":{"name":["in",["BHYT Officer","Pharmacy Officer","Department Requester","SupplyCore Ward Staff"]]},"fields":["name"]}'`
  → empty result (`[]`).
- Direct SQL confirms both `tabRole` and `tabDocPerm` have zero rows for the
  4 names after migrate.
- Patch re-run manually (`bench execute supplycore.patches.v0_7.remove_hospital_roles.execute`) a second time → no error, confirms idempotency.
- App-wide grep `grep -rl "BHYT Officer\|Pharmacy Officer\|Department Requester\|SupplyCore Ward Staff\|Ward Staff" supplycore/` (excl. `/backups/`, `__pycache__`) → **2 hits, both expected/out-of-scope**:
  1. `supplycore/public/frontend/index.js` — a **gitignored, untracked**
     Vite build artifact (`git ls-files` confirms it is not in the repo;
     `.gitignore` line 12 covers `supplycore/public/frontend/`). It's a
     stale local build of the separate `frontend/` Vue SPA (which lives
     outside `supplycore/` and was out of this task's file list). Not part
     of the committed source, regenerated by `yarn build`; left untouched.
  2. `supplycore/patches/v0_7/remove_hospital_roles.py` itself — necessarily
     contains the 4 role-name string literals as the `HOSPITAL_ROLES` list
     it deletes by name (same pattern as the existing
     `v0_6/remove_hospital_domain.py`, which still lists hospital doctype
     names for the same reason). This is the intended exception.
  All other in-repo, tracked files are clean.

## Scope note: docs beyond the original 19-file list

While confirming the grep-zero requirement, 9 tracked Markdown docs (UC flow
specs / module READMEs) inside `supplycore/` also had stray mentions of
`Pharmacy Officer` / `SupplyCore Ward Staff` / `Ward Staff` in actor lists,
permission tables, or embedded code excerpts (not in the original 19-file
list, which only covered `.json`/`.py`): `m6_transfer/UC-18_FLOW.md`,
`m6_transfer/README.md`, `m10_traceability/UC-29_FLOW.md`,
`m10_traceability/UC-30_FLOW.md`, `m4_wms/UC_TEST.md`,
`m2_planning/UC-07_FLOW.md`, `m11_dashboard/UC-32_FLOW.md`,
`m5_fefo/UC-17_FLOW.md`, `m11_dashboard/UC_TEST.md`. These were given
minimal, same-meaning edits (drop/replace the role mention) to satisfy the
"app-wide grep → ZERO" verify criterion, without rewriting the surrounding
hospital-flavored spec prose (e.g. `UC-30_FLOW.md` still describes a
patient/dispensing recall flow — that content is out of this task's scope,
which was strictly the 4 role *names*).

## Concerns

1. **`frontend/` (Vue SPA source, sibling dir to `supplycore/`) was not
   audited** — it's outside this task's declared scope (`supplycore/`
   package tree) and its built output is gitignored, but
   `frontend/src/{version.js,stores/auth.js,personas.js,pages/Dashboard.vue,pages/Forbidden.vue}`
   and 3 files under `frontend/tests/` still reference these role names. If
   a later task rebuilds the frontend, the hospital role strings will
   reappear in `supplycore/public/frontend/index.js`. Flagging for whoever
   owns frontend cleanup.
2. Removing `Pharmacy Officer` narrowed `MODULE_ROLES["m5"]` and
   `["m10"]`, and `FEATURE_ROLES["alerts"/"batch_trace"/"data_io"/
   "stock_balance"/"warehouse_map"]` in `api/access.py`, and shrank
   `ROLE_GUIDE`/`ROLE_WIDGETS` in `users.py`/`kpi.py` — all intentional
   per spec, verified none became empty, no other behavior change expected.
