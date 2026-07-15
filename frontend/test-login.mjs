import { chromium } from 'playwright'

const browser = await chromium.launch({
  headless: true,
  args: ['--host-resolver-rules=MAP supplycore 127.0.0.1', '--disable-dev-shm-usage'],
})
const ctx = await browser.newContext()
const page = await ctx.newPage()

page.on('console', m => console.log(`[console.${m.type()}]`, m.text()))
page.on('pageerror', e => console.log('[pageerror]', e.message))
page.on('requestfailed', r => console.log('[reqfail]', r.url(), r.failure()?.errorText))
page.on('response', async (r) => {
  if (r.url().includes('/api/') && r.status() >= 400) {
    console.log(`[HTTP ${r.status()}]`, r.url(), await r.text().then(t => t.slice(0, 200)).catch(() => ''))
  }
})

await page.goto('http://supplycore/supplycore', { waitUntil: 'networkidle' })
await page.waitForTimeout(800)
console.log('URL before login:', page.url())

await page.fill('input[type=text]', 'Administrator')
await page.fill('input[type=password]', 'admin')

// Patch fetch to log
await page.evaluate(() => {
  const origFetch = window.fetch
  window.fetch = function(url, opts) {
    console.log('FETCH', url, opts?.method || 'GET', opts?.headers ? Object.keys(opts.headers) : [])
    return origFetch.apply(this, arguments).then(r => {
      console.log('FETCH RESP', url, r.status)
      return r
    })
  }
})

await page.click('button[type=submit]')
await page.waitForTimeout(3000)
console.log('URL after login:', page.url())

await page.screenshot({ path: '/tmp/sc-screenshots/login-debug.png', fullPage: true })

// Check error msg displayed
const errEl = await page.locator('.bg-red-50').textContent().catch(() => null)
console.log('Login error displayed:', errEl)

await browser.close()
