# SupplyCore Sandbox — Playwright E2E

Sandbox test riêng cho SupplyCore SPA — chạy headless Chromium, mock dữ liệu sandbox-aware, screenshot mỗi step.

## Quick run

```bash
cd frontend
npm test                  # all suites
npm run test:login        # suite 00 login
npm run test:m0           # suite 01 M0 master data
npm run test:modules      # 11 module hubs M0..M11
npm run test:forms        # 20 form schemas
npm run test:crud         # CRUD: create + list filter
npm run test:actions      # ActionPanel + Alert filter
npm run test:headed       # mở browser thấy được
```

## Suites

| File | Coverage |
|---|---|
| `00_login.mjs` | Login flow + Dashboard + Sidebar 12 modules + Logout |
| `01_m0_master.mjs` | M0 Master Data: Item/UOM/Supplier/GL Account |
| `02_modules.mjs` | M0..M11 hub titles |
| `03_forms.mjs` | 20 doctype form schemas (sections + inputs) |
| `04_crud.mjs` | Tạo UOM/ItemGroup qua UI → cleanup REST |
| `05_actions.mjs` | ActionPanel, Alert filter, LinkAutocomplete |

## Output

Screenshots → `/tmp/sc-sandbox/<suite>--<test>.png`

## Custom

```bash
# Run specific suites
node tests/sandbox/runner.mjs 00_login,01_m0_master

# Override creds
SC_USER=Administrator SC_PWD=admin node tests/sandbox/runner.mjs

# Custom base
node tests/sandbox/runner.mjs --base=http://localhost:8080
```

## Adding new tests

Tạo `tests/sandbox/suites/<NN>_<name>.mjs`:

```js
export const tests = [
  {
    name: 'Test description',
    run: async ({ page, BASE, OUT, name }) => {
      await page.goto(`${BASE}/supplycore/...`)
      // assertions
      return { ok: true, detail: 'passed' }
      // or { ok: false, detail: 'why failed' }
    },
  },
]
```

Runner tự discover. Default timeout 30s/test. Auto-screenshot mỗi test.
