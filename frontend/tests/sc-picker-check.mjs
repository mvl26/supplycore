// Verify the WarehouseStockPanel picker on a new Transfer Request
import { chromium } from 'playwright'
import { mkdirSync } from 'fs'
const OUT = '/tmp/sc-screenshots'; mkdirSync(OUT, { recursive: true })
const BASE = 'http://supplycore/supplycore'
const browser = await chromium.launch({ headless: true,
  args: ['--host-resolver-rules=MAP supplycore 127.0.0.1', '--disable-dev-shm-usage'] })
const page = await (await browser.newContext({ viewport: { width: 1440, height: 1700 }, locale: 'vi-VN' })).newPage()
const log = (...a) => console.log(' ', ...a)

await page.goto(`${BASE}/login`, { waitUntil: 'networkidle' })
await page.fill('input[autocomplete="username"]', 'Administrator')
await page.fill('input[autocomplete="current-password"]', 'admin')
await page.click('button[type="submit"]')
await page.waitForTimeout(2800)

// New Transfer Request
await page.goto(`${BASE}/doc/SC%20Transfer%20Request/new`, { waitUntil: 'networkidle' })
await page.waitForTimeout(1600)

// Set from_warehouse via the LinkAutocomplete near label "Kho nguồn"
const whInput = page.locator('div:has(> label:has-text("Kho nguồn")) input').first()
await whInput.click()
await page.waitForTimeout(900)
const opt = page.locator('.shadow-lg button').first()
if (await opt.count()) { await opt.click() } else { log('WARN: no warehouse option') }
await page.waitForTimeout(2200)

// Picker assertions
const panel = page.locator('.sc-card:has-text("tồn kho nguồn")').first()
const checkboxes = await panel.locator('tbody input[type="checkbox"]').count()
const fillBtn = panel.locator('button:has-text("Điền")')
const pageSizeSel = await panel.locator('select').count()
const filterInput = await panel.locator('input[placeholder*="Lọc"]').count()
log('checkboxes in panel:', checkboxes)
log('page-size <select> present:', pageSizeSel)
log('filter input present:', filterInput)
log('fill button present:', await fillBtn.count())
await page.screenshot({ path: `${OUT}/tr-picker.png`, fullPage: true })

// Tick first 2 rows, click fill
const detailBefore = await page.locator('h4:has-text("Chi tiết")').first().innerText().catch(() => '?')
let ticked = 0
for (const cb of (await panel.locator('tbody input[type="checkbox"]:not([disabled])').all()).slice(0, 2)) {
  await cb.click(); ticked++
}
log('ticked rows:', ticked)
if (await fillBtn.count()) { await fillBtn.click(); await page.waitForTimeout(1200) }
const detailAfter = await page.locator('h4:has-text("Chi tiết")').first().innerText().catch(() => '?')
log('detail table header before:', detailBefore, '| after:', detailAfter)
await page.screenshot({ path: `${OUT}/tr-picker-filled.png`, fullPage: true })

await browser.close()
