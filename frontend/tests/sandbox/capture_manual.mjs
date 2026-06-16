#!/usr/bin/env node
/**
 * Capture screenshots of real SupplyCore screens for the user manual.
 * Reuses the sandbox harness conventions (base http://supplycore, Administrator/admin).
 * Output PNGs -> docs/_manual_build/img/
 */
import { chromium } from 'playwright'
import { mkdirSync } from 'fs'
import { fileURLToPath } from 'url'
import { dirname, join } from 'path'

const __dirname = dirname(fileURLToPath(import.meta.url))
const OUT = join(__dirname, '../../../docs/_manual_build/img')
mkdirSync(OUT, { recursive: true })

const BASE = 'http://supplycore'
const USER = process.env.SC_USER || 'Administrator'
const PWD = process.env.SC_PWD || 'admin'

const browser = await chromium.launch({
  headless: true,
  args: ['--host-resolver-rules=MAP supplycore 127.0.0.1', '--disable-dev-shm-usage'],
})
const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, locale: 'vi-VN' })

const log = (...a) => console.log(...a)
const done = []
const failed = []

async function settle(page, file) {
  // wait for SPA hydration (sidebar module links) then for page content
  await page.waitForSelector('aside a[href^="/supplycore/m"]', { timeout: 8000 }).catch(() => null)
  await page.waitForSelector('.sc-card, table, form, [class*="grid"], .sc-table', { timeout: 8000 }).catch(() => null)
  // dashboards/lists fetch async — give KPI/data time and let charts paint
  await page.waitForLoadState('networkidle', { timeout: 6000 }).catch(() => null)
  await page.waitForTimeout(2200)
}

async function shoot(page, file, { full = false } = {}) {
  await settle(page, file)
  await page.screenshot({ path: join(OUT, file + '.png'), fullPage: full })
  done.push(file)
  log('  ✓', file)
}

// --- main authed page ---
const page = await ctx.newPage()
async function login() {
  await page.goto(`${BASE}/supplycore`, { waitUntil: 'domcontentloaded' })
  await page.waitForTimeout(1200)
  if (page.url().includes('/login')) {
    await page.fill('input[type=text]', USER)
    await page.fill('input[type=password]', PWD)
    await Promise.all([
      page.waitForURL((u) => !u.toString().includes('/login'), { timeout: 15000 }).catch(() => null),
      page.click('button[type=submit]'),
    ])
    await page.waitForTimeout(1500)
  }
}

// --- 1) Login screen (no auth) in a separate, throwaway context ---
{
  const c2 = await browser.newContext({ viewport: { width: 1440, height: 900 }, locale: 'vi-VN' })
  const p2 = await c2.newPage()
  try {
    await p2.goto(`${BASE}/supplycore`, { waitUntil: 'domcontentloaded' })
    await p2.waitForTimeout(1500)
    await p2.screenshot({ path: join(OUT, 'login.png') })
    done.push('login'); log('  ✓ login')
  } catch (e) { failed.push(['login', e.message]); log('  ✗ login', e.message) }
  await c2.close()
}

await login()
log('Logged in at:', page.url())

async function go(path, file, opts = {}) {
  for (let attempt = 0; attempt < 2; attempt++) {
    try {
      await page.goto(`${BASE}/supplycore${path}`, { waitUntil: 'domcontentloaded', timeout: 20000 })
      await page.waitForTimeout(1600)
      const u = page.url()
      if (u.includes('/403')) { failed.push([file, 'blocked ' + u]); log('  ✗', file, '->403'); return false }
      if (u.includes('/login')) {            // session lost -> re-login and retry once
        log('  … re-login for', file); await login(); continue
      }
      await shoot(page, file, opts)
      return true
    } catch (e) {
      if (attempt === 1) { failed.push([file, e.message]); log('  ✗', file, String(e.message).split('\n')[0]) }
    }
  }
  return false
}

async function apiList(doctype) {
  return page.evaluate(async (dt) => {
    const csrf = window.sc_csrf || document.querySelector('meta[name="csrf-token"]')?.content || ''
    const r = await fetch('/api/method/supplycore.api.frontend.list_docs', {
      method: 'POST', credentials: 'include',
      headers: { 'Content-Type': 'application/json', 'X-Frappe-CSRF-Token': csrf },
      body: JSON.stringify({ doctype: dt, fields: ['name'], order_by: 'modified desc', limit: 1 }),
    })
    const d = await r.json().catch(() => ({}))
    return (d.message && d.message[0] && d.message[0].name) || null
  }, doctype)
}

// --- 2) Global screens ---
log('Global screens:')
await go('/dashboard', 'dashboard')
await go('/alerts', 'alerts')
await go('/stock-balance', 'stock_balance')
await go('/warehouses', 'warehouses')
await go('/putaway', 'putaway')
await go('/warehouse-map', 'warehouse_map')
await go('/map-editor', 'map_editor')
await go('/batch-trace', 'batch_trace')
await go('/financial-reports', 'financial_reports')
await go('/his-import', 'his_import')
await go('/users', 'users')

// --- 3) Module hubs m0..m11 ---
log('Module hubs:')
for (let i = 0; i <= 11; i++) await go('/m' + i, 'hub_m' + i)

// --- 4) Lists + details for key doctypes ---
const DTS = {
  item: 'SC Item', supplier: 'SC Supplier', fc: 'Framework Contract', ro: 'Release Order',
  pp: 'Procurement Plan', mr: 'SC Material Request', po: 'SC Purchase Order',
  pr: 'SC Purchase Receipt', qi: 'SC Quality Inspection', batch: 'SC Batch',
  fefo: 'FEFO Picker Rule', bin: 'Bin Location', tr: 'SC Transfer Request',
  dr: 'SC Dispensing Request', pd: 'SC Patient Dispensing', bhyt: 'SC BHYT Code Config',
  pi: 'SC Purchase Invoice', pe: 'SC Payment Entry', ics: 'SC Inventory Count Sheet',
  sr: 'SC Stock Reconciliation', recall: 'SC Recall Notice', inv: 'SC Investigation Report',
}
log('Lists + details:')
for (const [key, dt] of Object.entries(DTS)) {
  await go('/list/' + encodeURIComponent(dt), 'list_' + key)
  let name = null
  try { name = await apiList(dt) } catch (e) {}
  if (name) {
    await go('/doc/' + encodeURIComponent(dt) + '/' + encodeURIComponent(name), 'doc_' + key)
  } else {
    log('  (no record for', dt + ', skip detail)')
  }
}

await browser.close()
log('\n=== CAPTURED', done.length, 'screenshots ===')
if (failed.length) { log('FAILED', failed.length + ':'); failed.forEach(f => log('  -', f[0], '|', f[1])) }
