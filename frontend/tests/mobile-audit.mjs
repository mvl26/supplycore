// Audit responsive mobile: đăng nhập, ghé từng trang ở viewport điện thoại,
// đo tràn ngang + chụp ảnh. Chạy: node tests/mobile-audit.mjs
import { chromium } from 'playwright'
import { mkdirSync } from 'node:fs'

const OUT = '/tmp/sc-mobile'
mkdirSync(OUT, { recursive: true })

const ROUTES = [
  ['dashboard', '/supplycore/dashboard'],
  ['stock-balance', '/supplycore/stock-balance'],
  ['warehouses', '/supplycore/warehouses'],
  ['putaway', '/supplycore/putaway'],
  ['batch-trace', '/supplycore/batch-trace'],
  ['financial-reports', '/supplycore/financial-reports'],
  ['users', '/supplycore/users'],
  ['alerts', '/supplycore/alerts'],
  ['warehouse-map', '/supplycore/warehouse-map'],
  ['map-editor', '/supplycore/map-editor'],
  ['module-m1', '/supplycore/m1'],
]

const browser = await chromium.launch({
  headless: true,
  args: ['--host-resolver-rules=MAP supplycore 127.0.0.1', '--disable-dev-shm-usage'],
})
const ctx = await browser.newContext({
  viewport: { width: 390, height: 844 },
  deviceScaleFactor: 2,
  isMobile: true,
  hasTouch: true,
})
const page = await ctx.newPage()

// Đăng nhập
await page.goto('http://supplycore/supplycore', { waitUntil: 'networkidle' })
await page.waitForTimeout(600)
if (await page.locator('input[type=password]').count()) {
  await page.fill('input[type=text]', 'Administrator')
  await page.fill('input[type=password]', 'admin')
  await page.click('button[type=submit]')
  await page.waitForTimeout(2500)
}
console.log('after login URL:', page.url())

const VW = 390
const report = []
for (const [name, path] of ROUTES) {
  try {
    await page.goto('http://supplycore' + path, { waitUntil: 'networkidle', timeout: 20000 })
    await page.waitForTimeout(1200)
    const m = await page.evaluate(() => {
      const de = document.documentElement
      // tìm các phần tử tràn ra ngoài bề ngang viewport
      const vw = window.innerWidth
      const offenders = []
      document.querySelectorAll('*').forEach((el) => {
        const r = el.getBoundingClientRect()
        if (r.width > 0 && r.right > vw + 2) {
          offenders.push({
            tag: el.tagName.toLowerCase(),
            cls: (el.className && el.className.toString ? el.className.toString() : '').slice(0, 80),
            right: Math.round(r.right),
            w: Math.round(r.width),
          })
        }
      })
      return {
        scrollW: de.scrollWidth, clientW: de.clientWidth,
        overflow: de.scrollWidth - de.clientWidth,
        offenders: offenders.slice(0, 6),
      }
    })
    await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
    const bad = m.overflow > 2
    report.push({ name, ...m, bad })
    console.log(`${bad ? 'XXX' : 'ok '} ${name.padEnd(18)} overflow=${m.overflow}px scrollW=${m.scrollW} (vw=${VW})`)
    if (bad) m.offenders.forEach((o) => console.log(`      ↳ <${o.tag}> right=${o.right} w=${o.w} "${o.cls}"`))
  } catch (e) {
    console.log(`ERR ${name}: ${e.message.slice(0, 100)}`)
  }
}
console.log('\nBROKEN:', report.filter(r => r.bad).map(r => r.name).join(', ') || 'none')
await browser.close()
