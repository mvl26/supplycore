// E2E browser test — login + navigate + screenshot key pages
import { chromium } from 'playwright'
import { mkdirSync } from 'fs'

const BASE = 'http://supplycore'
const USER = 'Administrator'
const PWD = 'admin'
const OUT = '/tmp/sc-screenshots'

mkdirSync(OUT, { recursive: true })

const results = []
function step(name, ok, detail = '') {
  results.push({ name, ok, detail })
  console.log(`  ${ok ? '✓' : '✗'} ${name}${detail ? ' — ' + detail : ''}`)
}

;(async () => {
  // Resolve "supplycore" hostname to 127.0.0.1
  const browser = await chromium.launch({
    headless: true,
    args: ['--host-resolver-rules=MAP supplycore 127.0.0.1', '--disable-dev-shm-usage'],
  })
  const ctx = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    locale: 'vi-VN',
  })
  const page = await ctx.newPage()

  // Console / pageerror collectors
  const errors = []
  page.on('pageerror', (err) => errors.push({ type: 'pageerror', msg: err.message }))
  page.on('console', (msg) => {
    if (msg.type() === 'error') errors.push({ type: 'console', msg: msg.text() })
  })
  page.on('requestfailed', (req) => errors.push({ type: 'requestfailed', msg: `${req.url()}: ${req.failure()?.errorText}` }))

  try {
    console.log('\n=== TEST 1: GET /supplycore (Guest → redirect /login) ===')
    await page.goto(`${BASE}/supplycore`, { waitUntil: 'networkidle' })
    await page.waitForTimeout(800)
    const url1 = page.url()
    step('GET /supplycore redirect to /login', url1.endsWith('/login') || url1.includes('?redirect'), `URL: ${url1}`)
    await page.screenshot({ path: `${OUT}/01-login.png`, fullPage: true })

    console.log('\n=== TEST 2: Login với Administrator/admin ===')
    await page.fill('input[type=text]', USER)
    await page.fill('input[type=password]', PWD)
    await page.screenshot({ path: `${OUT}/02-login-filled.png` })
    await Promise.all([
      page.waitForURL((u) => !u.toString().includes('/login'), { timeout: 10000 }).catch(() => null),
      page.click('button[type=submit]'),
    ])
    await page.waitForTimeout(1500)
    const url2 = page.url()
    step('Login submit → redirect dashboard', !url2.includes('/login'), `URL: ${url2}`)
    await page.screenshot({ path: `${OUT}/03-dashboard.png`, fullPage: true })

    // Check KPI cards present
    const kpiCount = await page.locator('.sc-card').filter({ hasText: /Tổng giá trị|Chi phí|Công nợ/ }).count()
    step('Dashboard KPI cards loaded', kpiCount >= 3, `${kpiCount} matching cards`)

    console.log('\n=== TEST 3: Alert Center ===')
    await page.click('a[href="/supplycore/alerts"]').catch(async () => {
      await page.goto(`${BASE}/supplycore/alerts`)
    })
    await page.waitForTimeout(1200)
    await page.screenshot({ path: `${OUT}/04-alerts.png`, fullPage: true })
    const alertCards = await page.locator('.sc-card').filter({ hasText: /Critical|Warning|Info/ }).count()
    step('Alert Center hiển thị alerts', alertCards >= 1, `${alertCards} alerts`)

    console.log('\n=== TEST 4: Module M3 Receiving ===')
    await page.goto(`${BASE}/supplycore/m3`)
    await page.waitForTimeout(1200)
    await page.screenshot({ path: `${OUT}/05-m3-receiving.png`, fullPage: true })
    const m3title = await page.locator('h1').first().textContent()
    step('M3 hub loaded', m3title?.includes('Tiếp nhận'), `Title: "${m3title}"`)

    console.log('\n=== TEST 5: List SC Purchase Receipt ===')
    await page.goto(`${BASE}/supplycore/list/SC%20Purchase%20Receipt`)
    await page.waitForTimeout(1200)
    await page.screenshot({ path: `${OUT}/06-list-pr.png`, fullPage: true })
    const tableRows = await page.locator('table tbody tr').count()
    step('SC PR list loaded', tableRows >= 1, `${tableRows} rows`)

    console.log('\n=== TEST 6: Form tạo SC Material Request ===')
    await page.goto(`${BASE}/supplycore/doc/SC%20Material%20Request/new`)
    await page.waitForTimeout(1500)
    await page.screenshot({ path: `${OUT}/07-form-new-mr.png`, fullPage: true })
    const fieldCount = await page.locator('input, select, textarea').count()
    const sectionTitles = await page.locator('h3').allTextContents()
    step('Form MR có fields', fieldCount >= 4, `${fieldCount} inputs, sections: ${sectionTitles.join('|')}`)
    step('Has + Thêm dòng button', (await page.getByText('+ Thêm dòng').count()) > 0)

    console.log('\n=== TEST 7: Form M10 Recall Notice ===')
    await page.goto(`${BASE}/supplycore/doc/SC%20Recall%20Notice/new`)
    await page.waitForTimeout(1200)
    await page.screenshot({ path: `${OUT}/08-form-new-recall.png`, fullPage: true })
    const recallFields = await page.locator('input, select, textarea').count()
    step('Form Recall có fields', recallFields >= 5, `${recallFields} inputs`)

    console.log('\n=== TEST 8: Form M11 Alert Rule ===')
    await page.goto(`${BASE}/supplycore/doc/SC%20Alert%20Rule/new`)
    await page.waitForTimeout(1200)
    await page.screenshot({ path: `${OUT}/09-form-new-rule.png`, fullPage: true })
    const ruleFields = await page.locator('input, select, textarea').count()
    step('Form Alert Rule có fields', ruleFields >= 8, `${ruleFields} inputs`)

    console.log('\n=== TEST 9: View existing alert + ActionPanel ===')
    await page.goto(`${BASE}/supplycore/list/SC%20Alert`)
    await page.waitForTimeout(1200)
    const firstAlertRow = page.locator('table tbody tr').first()
    if (await firstAlertRow.count()) {
      await firstAlertRow.click()
      await page.waitForTimeout(1500)
      await page.screenshot({ path: `${OUT}/10-alert-view.png`, fullPage: true })
      const actionPanelBtns = await page.locator('button').filter({ hasText: /Resolve|Snooze|Assign/ }).count()
      step('Alert detail có ActionPanel buttons', actionPanelBtns >= 1, `${actionPanelBtns} action buttons`)
    } else {
      step('Alert detail skipped', true, 'No alerts in list')
    }

    console.log('\n=== TEST 10: M1 Framework Contract list ===')
    await page.goto(`${BASE}/supplycore/list/Framework%20Contract`)
    await page.waitForTimeout(1200)
    await page.screenshot({ path: `${OUT}/11-list-fc.png`, fullPage: true })
    const fcRows = await page.locator('table tbody tr').count()
    step('FC list loaded', fcRows >= 1, `${fcRows} rows`)

    console.log('\n=== Errors detected ===')
    if (errors.length === 0) {
      console.log('  ✓ Không có JS errors')
    } else {
      errors.slice(0, 15).forEach(e => console.log(`  ✗ [${e.type}] ${e.msg.slice(0, 150)}`))
      step('No JS console errors', false, `${errors.length} errors`)
    }
  } catch (e) {
    console.error('FATAL:', e.message)
    step('Fatal error', false, e.message)
  } finally {
    await browser.close()
  }

  // Summary
  console.log('\n========== SUMMARY ==========')
  const passed = results.filter(r => r.ok).length
  console.log(`${passed}/${results.length} pass`)
  console.log(`Screenshots: ${OUT}/`)
  process.exit(passed === results.length ? 0 : 1)
})()
