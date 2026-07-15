# SupplyCore Frontend

Vue 3 + Vite + Tailwind + Chart.js SPA cho SupplyCore, serve qua Frappe.

## Tech stack

- **Vue 3** Composition API + `<script setup>`
- **Vite** build
- **Tailwind CSS** v3 — design tokens: navy `#1F4E79`, royal `#2E75B6`, Inter font
- **Vue Router** v4 — history mode at base `/supplycore/`
- **Pinia** state
- **Chart.js + vue-chartjs** — KPI trends
- **frappe-ui** (optional) — Frappe component lib

## Routes

| Path | Page | Component |
|---|---|---|
| `/` `/dashboard` | SCR-01 Executive Dashboard | `pages/Dashboard.vue` |
| `/alerts` | SCR-13 Alert Center | `pages/AlertCenter.vue` |
| `/m1..m11` | Module hubs (M1..M11) | `pages/ModuleHub.vue` |

## API

`src/api.js` — Frappe REST + whitelisted method:
- `call(method, args)` — `/api/method/<dotted-path>`
- `getList(doctype, params)` — `/api/resource/<doctype>`
- `getDoc`, `count`, `getCurrentUser`

CSRF token injected via `<meta name="csrf-token" content="{{ csrf_token }}">` in `www/supplycore.html`.

## Dev

```bash
cd apps/supplycore/frontend
npm install
npm run dev   # localhost:8080, proxy /api → :8000
```

## Build

```bash
npm run build  # → ../supplycore/public/frontend/{index.css, index.js, chunks/}
cd ../..
bench build --app supplycore  # symlink sites/assets/supplycore
```

Access via Frappe site: `http://supplycore/supplycore` (proxied through nginx on port 80).
Login required — Guest redirect to `/login`.

## Design tokens (from Phase 3)

```css
--sc-primary-dark: #1F4E79   /* Navy */
--sc-primary:      #2E75B6   /* Royal Blue */
--sc-primary-light:#5B9BD5
--sc-bg:           #F7F9FC
--sc-surface:      #FFFFFF
--sc-border:       #E5E9F0
```

Severity colors:
- Critical: `#DC2626` (red-600)
- Warning:  `#F59E0B` (amber-500)
- Info:     `#0EA5E9` (sky-500)
- Success:  `#16A34A` (green-600)

Type scale: xs 11px / sm 13px / base 14px / lg 16px / xl 20px / 2xl 24px / 3xl 32px / kpi 36px.
Font: Inter (Google Fonts CDN), mono: Roboto Mono.

## File structure

```
frontend/
├── index.html
├── package.json
├── postcss.config.js
├── tailwind.config.js
├── vite.config.js
└── src/
    ├── main.js               # app entry
    ├── App.vue               # root
    ├── router.js
    ├── api.js                # Frappe REST client
    ├── modules.js            # 11 module definitions + DocType map
    ├── assets/main.css       # Tailwind + design tokens
    ├── components/
    │   ├── AppShell.vue      # sidebar + topbar layout
    │   └── KpiCard.vue       # KPI card with variant
    └── pages/
        ├── Dashboard.vue     # SCR-01
        ├── AlertCenter.vue   # SCR-13
        ├── ModuleHub.vue     # M1..M11 generic
        └── NotFound.vue
```

## Phase 3 screen coverage

| Screen | Status |
|---|---|
| SCR-01 Executive Dashboard | ✓ Built |
| SCR-02 Warehouse Dashboard | TODO — extend ModuleHub for M4 |
| SCR-03..04 PO list/form | TODO — link to Frappe Desk for now |
| SCR-05..06 PR + QI | TODO |
| SCR-07 Framework Contract | Link to Desk |
| SCR-08 FEFO Picker | TODO |
| SCR-09..10 Dispensing | Link to Desk |
| SCR-11 Stock Balance | TODO — custom page |
| SCR-12 Batch Trace | TODO — uses get_batch_trace API |
| SCR-13 Alert Center | ✓ Built |
| SCR-14 Mobile PDA | TODO — separate /pda PWA |
