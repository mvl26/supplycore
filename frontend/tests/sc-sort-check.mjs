// Verify the WarehouseStockPanel sort control (hạn dùng works pre-restart)
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
const sortSel = panel.locator('select').nth(0)  // sort select (Pagination select is separate, in footer)
// the sort <select> is the one with option "Ngày nhập"
const sortSelect = panel.locator('select:has(option:text-is("Ngày nhập"))')
log('sort select present:', await sortSelect.count())
log('  options:', (await sortSelect.locator('option').allInnerTexts()).join(' / '))

// HD column index: # checkbox, Mã VT, Tên, Lô, Vị trí, KCS, Ngày nhập, HD(8th), SL...
// 1-based td: cb=1, MãVT=2, Tên=3, Lô=4, VịTrí=5, KCS=6, NgàyNhập=7, HD=8
const hdCol = async () => {
  const cells = await panel.locator('tbody tr td:nth-child(8)').allInnerTexts()
  return cells.map(s => s.trim())
}
log('HD column (mặc định FEFO):', (await hdCol()).join(', '))

// Sort by Hạn dùng, desc
await sortSelect.selectOption('expiry_date')
await page.waitForTimeout(400)
await panel.locator('button[title="Tăng dần"]').click()  // toggle → desc
await page.waitForTimeout(500)
log('HD column (Hạn dùng giảm dần):', (await hdCol()).join(', '))

await page.screenshot({ path: `${OUT}/tr-picker-sort.png`, fullPage: true })
await browser.close()
