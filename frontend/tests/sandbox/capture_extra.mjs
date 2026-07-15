#!/usr/bin/env node
// Capture the few screens the main run couldn't: Snapshot dialog, SC Alert Rule form, Investigation Report form.
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
async function settle() {
  await page.waitForSelector('aside a[href^="/supplycore/m"]', { timeout: 8000 }).catch(() => null)
  await page.waitForSelector('.sc-card, table, form, [class*="grid"]', { timeout: 8000 }).catch(() => null)
  await page.waitForLoadState('networkidle', { timeout: 6000 }).catch(() => null)
  await page.waitForTimeout(2200)
}
async function go(path) {
  await page.goto(`${BASE}/supplycore${path}`, { waitUntil: 'domcontentloaded', timeout: 20000 })
  await settle()
}
const shot = async (f) => { await page.screenshot({ path: join(OUT, f + '.png') }); console.log('  ✓', f) }

await login()
console.log('logged in:', page.url())

// 1) Snapshot dialog
try {
  await go('/dashboard')
  await page.locator('button:has-text("Snapshot PDF")').first().click({ timeout: 8000 })
  await page.waitForSelector('text=Snapshot Dashboard', { timeout: 8000 }).catch(() => null)
  await page.waitForTimeout(1500)
  await shot('snapshot_dialog')
} catch (e) { console.log('  ✗ snapshot_dialog', e.message.split('\n')[0]) }

// 2) SC Alert Rule — open first record if any, else create form
try {
  await go('/list/' + encodeURIComponent('SC Alert Rule'))
  const row = page.locator('table tbody tr td a, table tbody tr').first()
  const has = await page.locator('table tbody tr').count().catch(() => 0)
  if (has > 0) {
    await row.click({ timeout: 5000 }).catch(() => null)
    await settle()
    if (page.url().includes('/doc/')) { await shot('alert_rule') }
    else { await go('/doc/' + encodeURIComponent('SC Alert Rule') + '/new'); await shot('alert_rule') }
  } else {
    await go('/doc/' + encodeURIComponent('SC Alert Rule') + '/new'); await shot('alert_rule')
  }
} catch (e) { console.log('  ✗ alert_rule', e.message.split('\n')[0]) }

// 3) Investigation Report — create form
try {
  await go('/doc/' + encodeURIComponent('SC Investigation Report') + '/new')
  await shot('investigation_form')
} catch (e) { console.log('  ✗ investigation_form', e.message.split('\n')[0]) }

await browser.close()
console.log('done')
