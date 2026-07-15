#!/usr/bin/env node
/**
 * SupplyCore Sandbox Test Runner — Playwright E2E
 *
 * Usage:
 *   node tests/sandbox/runner.mjs               # chạy tất cả suites
 *   node tests/sandbox/runner.mjs login         # chạy 1 suite
 *   node tests/sandbox/runner.mjs login,m0,m11  # chạy nhiều suites
 *   node tests/sandbox/runner.mjs --headed      # mở browser thấy được
 *   node tests/sandbox/runner.mjs --base=http://supplycore  # đổi host
 *
 * Suites discovered từ tests/sandbox/suites/*.mjs
 */

import { chromium } from 'playwright'
import { readdirSync, mkdirSync, existsSync } from 'fs'
import { fileURLToPath } from 'url'
import { dirname, join, resolve } from 'path'

const __dirname = dirname(fileURLToPath(import.meta.url))
const SUITES_DIR = join(__dirname, 'suites')
const OUT = '/tmp/sc-sandbox'
mkdirSync(OUT, { recursive: true })

// === CLI args ===
const args = process.argv.slice(2)
const headed = args.includes('--headed')
const baseFlag = args.find(a => a.startsWith('--base='))
const BASE = baseFlag ? baseFlag.split('=')[1] : 'http://supplycore'
const positional = args.filter(a => !a.startsWith('--'))
const suiteFilter = positional[0]?.split(',').map(s => s.trim()).filter(Boolean) || null

// === Default creds ===
const USER = process.env.SC_USER || 'Administrator'
const PWD  = process.env.SC_PWD  || 'admin'

// === Discover suites ===
const suiteFiles = readdirSync(SUITES_DIR)
  .filter(f => f.endsWith('.mjs'))
  .filter(f => !suiteFilter || suiteFilter.some(s =>
    f.startsWith(s + '.') || f === s + '.mjs' || f.startsWith(s + '_') || f.startsWith(s)))

if (suiteFiles.length === 0) {
  console.error('No suites match', suiteFilter)
  process.exit(1)
}

console.log(`\n🧪 SupplyCore Sandbox`)
console.log(`   Base: ${BASE}`)
console.log(`   User: ${USER}`)
console.log(`   Suites: ${suiteFiles.join(', ')}`)
console.log(`   Output: ${OUT}\n`)

// === Browser ===
const browser = await chromium.launch({
  headless: !headed,
  args: ['--host-resolver-rules=MAP supplycore 127.0.0.1', '--disable-dev-shm-usage'],
})
const ctx = await browser.newContext({
  viewport: { width: 1440, height: 900 },
  locale: 'vi-VN',
})

// === Test utilities ===
function createPage(suiteName) {
  return ctx.newPage().then(async (page) => {
    const errors = []
    page.on('pageerror', e => errors.push({ type: 'pageerror', msg: e.message, suite: suiteName }))
    page.on('console', m => {
      if (m.type() === 'error') {
        const text = m.text()
        // Filter known harmless errors
        if (text.includes('frappe.auth.get_logged_user') && text.includes('403')) return
        errors.push({ type: 'console', msg: text, suite: suiteName })
      }
    })
    page.on('requestfailed', r => {
      const url = r.url()
      if (url.includes('favicon')) return
      errors.push({ type: 'reqfail', msg: `${url}: ${r.failure()?.errorText}`, suite: suiteName })
    })
    page._scErrors = errors
    return page
  })
}

async function login(page) {
  await page.goto(`${BASE}/supplycore`, { waitUntil: 'networkidle' })
  await page.waitForTimeout(500)
  if (page.url().includes('/login')) {
    await page.fill('input[type=text]', USER)
    await page.fill('input[type=password]', PWD)
    await Promise.all([
      page.waitForURL((u) => !u.toString().includes('/login'), { timeout: 10000 }).catch(() => null),
      page.click('button[type=submit]'),
    ])
    await page.waitForTimeout(800)
  }
}

const _summary = []

async function runSuite(filename) {
  const name = filename.replace(/\.mjs$/, '')
  console.log(`▸ Suite: ${name}`)
  const mod = await import(join(SUITES_DIR, filename))
  const tests = mod.tests || []
  const passed = []
  const failed = []
  const page = await createPage(name)
  await login(page)
  await page.waitForTimeout(500)

  for (const t of tests) {
    process.stdout.write(`   • ${t.name} ... `)
    try {
      const start = Date.now()
      const result = await Promise.race([
        t.run({ page, BASE, OUT, name: `${name}--${t.name.replace(/\s+/g, '_')}` }),
        new Promise((_, rej) => setTimeout(() => rej(new Error('Timeout 30s')), 30000)),
      ])
      const dt = Date.now() - start
      if (result?.ok === false) {
        console.log(`✗ ${result.detail || 'failed'} (${dt}ms)`)
        failed.push({ name: t.name, detail: result.detail })
      } else {
        console.log(`✓ ${result?.detail || 'OK'} (${dt}ms)`)
        passed.push({ name: t.name, detail: result?.detail })
      }
    } catch (e) {
      console.log(`✗ ${e.message}`)
      failed.push({ name: t.name, detail: e.message })
    }
  }

  if (page._scErrors.length) {
    console.log(`   ⚠ ${page._scErrors.length} console/pageerror events`)
    page._scErrors.slice(0, 5).forEach(e => console.log(`     [${e.type}] ${e.msg.slice(0, 140)}`))
  }

  await page.close()
  _summary.push({ name, passed: passed.length, failed: failed.length, errors: page._scErrors.length, tests: { passed, failed } })
}

// === Run all suites ===
for (const f of suiteFiles) {
  try {
    await runSuite(f)
  } catch (e) {
    console.error(`FATAL in suite ${f}:`, e.message)
    _summary.push({ name: f, passed: 0, failed: 999, errors: 0, error: e.message })
  }
}

await browser.close()

// === Summary ===
console.log('\n╔═══════════════ SUMMARY ═══════════════╗')
let totalPass = 0, totalFail = 0
for (const s of _summary) {
  totalPass += s.passed
  totalFail += s.failed
  console.log(`║ ${s.name.padEnd(20)} ${String(s.passed).padStart(3)} pass / ${String(s.failed).padStart(3)} fail ║`)
}
console.log(`╠═══════════════════════════════════════╣`)
console.log(`║ TOTAL                ${String(totalPass).padStart(3)} pass / ${String(totalFail).padStart(3)} fail ║`)
console.log(`╚═══════════════════════════════════════╝`)
console.log(`\nScreenshots: ${OUT}/`)

process.exit(totalFail === 0 ? 0 : 1)
