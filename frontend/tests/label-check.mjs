// Test in nhãn lô 50×30mm: mở lô, bấm "In nhãn", bắt popup, chụp .label
import { chromium } from 'playwright'
import { mkdirSync } from 'node:fs'
mkdirSync('/tmp/sc-mobile', { recursive: true })

const BATCH = 'DTRC-GLU5-202705-001'
const browser = await chromium.launch({
  headless: true,
  args: ['--host-resolver-rules=MAP supplycore 127.0.0.1', '--disable-dev-shm-usage'],
})
const ctx = await browser.newContext({ deviceScaleFactor: 3 })
// Ngăn popup tự in + tự đóng để kịp chụp
await ctx.addInitScript(() => { window.print = () => {}; window.close = () => {} })
const page = await ctx.newPage()

await page.goto('http://supplycore/supplycore', { waitUntil: 'networkidle' })
await page.waitForTimeout(600)
if (await page.locator('input[type=password]').count()) {
  await page.fill('input[type=text]', 'Administrator')
  await page.fill('input[type=password]', 'admin')
  await page.click('button[type=submit]')
  await page.waitForTimeout(2500)
}

await page.goto('http://supplycore/supplycore/doc/SC%20Batch/' + encodeURIComponent(BATCH), { waitUntil: 'networkidle' })
await page.waitForTimeout(1500)

const popupP = ctx.waitForEvent('page', { timeout: 10000 })
await page.click('button:has-text("In nhãn")')
const popup = await popupP
await popup.waitForLoadState('domcontentloaded')
await popup.waitForTimeout(800)

const label = popup.locator('.label')
await label.waitFor({ timeout: 5000 })
const box = await label.boundingBox()
console.log('label box (px):', box ? `${Math.round(box.width)}x${Math.round(box.height)}` : 'none',
  '→ kỳ vọng ~189x113px (50×30mm @96dpi)')
await label.screenshot({ path: '/tmp/sc-mobile/label.png' })
// chụp thêm nguyên trang popup để thấy mép nhãn
await popup.screenshot({ path: '/tmp/sc-mobile/label-page.png' })
console.log('saved /tmp/sc-mobile/label.png')
await browser.close()
