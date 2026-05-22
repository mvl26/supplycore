// Verify filled detail rows carry UOM (resolved per item)
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

await page.goto(`${BASE}/doc/SC%20Transfer%20Request/new`, { waitUntil: 'networkidle' })
await page.waitForTimeout(1600)
const whInput = page.locator('div:has(> label:has-text("Kho nguồn")) input').first()
await whInput.click()
await page.waitForTimeout(900)
const opt = page.locator('.shadow-lg button').first()
if (await opt.count()) await opt.click()
await page.waitForTimeout(2200)

const panel = page.locator('.sc-card:has-text("tồn kho nguồn")').first()
let ticked = 0
for (const cb of (await panel.locator('tbody input[type="checkbox"]:not([disabled])').all()).slice(0, 3)) {
  await cb.click(); ticked++
}
log('ticked rows:', ticked)
await panel.locator('button:has-text("Điền")').click()
await page.waitForTimeout(2000)

const detail = page.locator('div:has(> div > h4:has-text("Chi tiết"))').first()
const rows = detail.locator('tbody tr')
const n = await rows.count()
log('detail rows:', n)
let withUom = 0
for (let i = 0; i < n; i++) {
  const tds = rows.nth(i).locator('td')
  const item = await tds.nth(1).locator('input').inputValue().catch(() => '?')
  const uom = await tds.nth(2).locator('input').inputValue().catch(() => '?')
  if (uom && uom !== '?') withUom++
  log(`  row ${i}: item=${item} | uom=${uom}`)
}
log(`VERDICT: ${withUom}/${n} dòng chi tiết có UOM`)
await page.screenshot({ path: `${OUT}/tr-picker-uom.png`, fullPage: true })
await browser.close()
