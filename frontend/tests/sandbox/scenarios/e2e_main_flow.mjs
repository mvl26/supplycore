#!/usr/bin/env node
/**
 * E2E Main Flow Scenario
 *
 * Luồng chính cuối-cuối qua sandbox SPA:
 *   1. Tạo Framework Contract (HĐ khung)
 *   2. Gọi hàng: Material Request → Purchase Order
 *   3. Nhận hàng: Purchase Receipt với batch info
 *   4. QC: Quality Inspection + readings → Accepted
 *   5. Tạo Lô tự động qua PR submit
 *   6. Xếp hàng vào kho (Bin Location qua PR)
 *   7. Chuyển kho: Stock Entry Material Transfer
 *   (PHASE 8 Cấp phát/BHYT đã bỏ — GĐ1 gỡ M7 Dispensing/BHYT khỏi backend)
 *
 * Mỗi step có Issue logging vào docs/E2E_MAIN_FLOW_LOG.md
 *
 * Usage:
 *   node tests/sandbox/scenarios/e2e_main_flow.mjs [--headed]
 */

import { chromium } from 'playwright'
import { appendFileSync, mkdirSync } from 'fs'
import { fileURLToPath } from 'url'
import { dirname, resolve } from 'path'

const __dirname = dirname(fileURLToPath(import.meta.url))
const ROOT = resolve(__dirname, '../../../..')
const LOG_FILE = resolve(ROOT, 'docs/E2E_MAIN_FLOW_LOG.md')
const SCREENSHOTS = '/tmp/sc-e2e'
mkdirSync(SCREENSHOTS, { recursive: true })

const BASE = 'http://supplycore'
const USER = 'Administrator'
const PWD = 'admin'
const headed = process.argv.includes('--headed')

const ctx = {}        // Shared context across tests
const issues = []     // Issues found in this run
const stepResults = [] // Step result summary

// ===========================================================
// Helpers
// ===========================================================
async function api(page, method, args = {}) {
  return page.evaluate(async ({ method, args }) => {
    const csrf = window.sc_csrf || ''
    const r = await fetch(`/api/method/${method}`, {
      method: 'POST', credentials: 'include',
      headers: { 'Content-Type': 'application/json', 'X-Frappe-CSRF-Token': csrf },
      body: JSON.stringify(args),
    })
    const d = await r.json().catch(() => ({}))
    if (!r.ok) throw new Error(d.exception || d._server_messages || `HTTP ${r.status}`)
    return d.message
  }, { method, args })
}

async function runDocMethod(page, doctype, name, method, args = {}) {
  return page.evaluate(async ({ doctype, name, method, args }) => {
    const csrf = window.sc_csrf || ''
    const usp = new URLSearchParams({ method, dt: doctype, dn: name })
    if (Object.keys(args).length) usp.set('args', JSON.stringify(args))
    const r = await fetch(`/api/method/run_doc_method?${usp}`, {
      method: 'POST', credentials: 'include',
      headers: { 'X-Frappe-CSRF-Token': csrf, Accept: 'application/json' },
    })
    const d = await r.json().catch(() => ({}))
    if (!r.ok) throw new Error(d.exception || `HTTP ${r.status}`)
    return d.message
  }, { doctype, name, method, args })
}

async function createDocViaAPI(page, doctype, fields) {
  return page.evaluate(async ({ doctype, fields }) => {
    const csrf = window.sc_csrf || ''
    const r = await fetch(`/api/resource/${encodeURIComponent(doctype)}`, {
      method: 'POST', credentials: 'include',
      headers: { 'Content-Type': 'application/json', 'X-Frappe-CSRF-Token': csrf },
      body: JSON.stringify({ doctype, ...fields }),
    })
    const d = await r.json().catch(() => ({}))
    if (!r.ok) throw new Error(d.exception || d._server_messages || `HTTP ${r.status}`)
    return d.data
  }, { doctype, fields })
}

async function getDoc(page, doctype, name) {
  return api(page, 'supplycore.api.frontend.get_doc', { doctype, name })
}

async function listDocs(page, doctype, params = {}) {
  return api(page, 'supplycore.api.frontend.list_docs', {
    doctype,
    fields: params.fields || ['name'],
    filters: params.filters || {},
    order_by: params.order_by || 'modified desc',
    limit: params.limit || 20,
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
    await page.waitForTimeout(1500)
  }
}

function rand(n = 5) { return Math.random().toString(36).slice(2, 2 + n) }
function today() { return new Date().toISOString().slice(0, 10) }
function addDays(d, n) {
  const dt = new Date(d)
  dt.setDate(dt.getDate() + n)
  return dt.toISOString().slice(0, 10)
}

function logIssue(step, issue, rootCause = null, fix = null) {
  issues.push({ step, issue, rootCause, fix })
}

async function step(name, fn) {
  const start = Date.now()
  console.log(`\n▸ ${name}`)
  try {
    const result = await fn()
    const dt = Date.now() - start
    console.log(`  ✓ ${result?.detail || 'OK'} (${dt}ms)`)
    stepResults.push({ name, ok: true, detail: result?.detail, dt })
    return result
  } catch (e) {
    const dt = Date.now() - start
    console.log(`  ✗ ${e.message.slice(0, 250)} (${dt}ms)`)
    stepResults.push({ name, ok: false, detail: e.message.slice(0, 300), dt })
    logIssue(name, e.message)
    throw e
  }
}

// ===========================================================
// Main
// ===========================================================
const browser = await chromium.launch({
  headless: !headed,
  args: ['--host-resolver-rules=MAP supplycore 127.0.0.1', '--disable-dev-shm-usage'],
})
const browserCtx = await browser.newContext({ viewport: { width: 1440, height: 900 }, locale: 'vi-VN' })
const page = await browserCtx.newPage()

const errors = []
page.on('pageerror', e => errors.push(`[pageerror] ${e.message}`))
page.on('console', m => {
  if (m.type() === 'error') {
    const t = m.text()
    if (t.includes('get_logged_user') && t.includes('403')) return
    errors.push(`[console] ${t.slice(0, 200)}`)
  }
})

const RUN_ID = new Date().toISOString().replace(/[:.]/g, '-')
console.log(`\n╔══════════════════════════════════════════════╗`)
console.log(`║  E2E Main Flow — Run ${RUN_ID.slice(0, 19)}    ║`)
console.log(`╚══════════════════════════════════════════════╝`)

try {
  // ============================================================
  await step('PRE: Login', async () => {
    await login(page)
    if (page.url().includes('/login')) throw new Error('Login failed')
    return { detail: `URL: ${page.url()}` }
  })

  // Pick master data
  await step('PRE: Pick master data (Supplier, Item, Warehouse, Department)', async () => {
    const suppliers = await listDocs(page, 'SC Supplier', { fields: ['name', 'supplier_name'], limit: 1 })
    const items = await listDocs(page, 'SC Item', {
      fields: ['name', 'item_name', 'uom', 'has_batch_no'],
      filters: { is_stock_item: 1, disabled: 0, has_batch_no: 1 },
      limit: 1,
    })
    const warehouses = await listDocs(page, 'SC Warehouse',
      { fields: ['name'], filters: { is_group: 0, disabled: 0 }, limit: 2 })
    const depts = await listDocs(page, 'SC Department', { fields: ['name'], limit: 1 })

    if (!suppliers.length || !items.length || warehouses.length < 2 || !depts.length) {
      throw new Error(`Missing master: sup=${suppliers.length}, item=${items.length}, wh=${warehouses.length}, dept=${depts.length}`)
    }

    ctx.supplier = suppliers[0].name
    ctx.item = items[0].name
    ctx.itemUom = items[0].uom
    ctx.warehouse_main = warehouses[0].name
    ctx.warehouse_to = warehouses[1].name
    ctx.department = depts[0].name

    return { detail: `Sup=${ctx.supplier}, Item=${ctx.item} (${ctx.itemUom}), WH1=${ctx.warehouse_main}, WH2=${ctx.warehouse_to}` }
  })

  // ============================================================
  // PHASE 1: FRAMEWORK CONTRACT
  // ============================================================
  await step('1.1 Tạo Framework Contract via API', async () => {
    const cn = `FC-E2E-${rand(6)}`
    const fc = await createDocViaAPI(page, 'Framework Contract', {
      contract_number: cn,
      supplier: ctx.supplier,
      contract_date: today(),
      valid_from: today(),
      valid_to: addDays(today(), 365),
      total_value: 5_000_000,
      items: [
        { item_code: ctx.item, uom: ctx.itemUom, contract_qty: 1000, unit_price: 5000 },
      ],
    })
    ctx.fc = fc.name
    return { detail: `FC=${fc.name}, contract_number=${cn}` }
  })

  await step('1.2 FC submit_for_review → Manager Review', async () => {
    await runDocMethod(page, 'Framework Contract', ctx.fc, 'submit_for_review')
    const fc = await getDoc(page, 'Framework Contract', ctx.fc)
    if (fc.approval_stage !== 'Manager Review') {
      throw new Error(`Expected stage=Manager Review, got ${fc.approval_stage}`)
    }
    return { detail: `stage=${fc.approval_stage}` }
  })

  await step('1.3 FC approve_as_manager', async () => {
    await runDocMethod(page, 'Framework Contract', ctx.fc, 'approve_as_manager',
      { comment: 'E2E test manager approval' })
    const fc = await getDoc(page, 'Framework Contract', ctx.fc)
    return { detail: `stage=${fc.approval_stage}` }
  })

  await step('1.4 FC approve_as_executive (nếu cần)', async () => {
    const fc1 = await getDoc(page, 'Framework Contract', ctx.fc)
    if (fc1.approval_stage === 'Executive Review') {
      await runDocMethod(page, 'Framework Contract', ctx.fc, 'approve_as_executive',
        { comment: 'E2E test executive approval' })
    }
    const fc = await getDoc(page, 'Framework Contract', ctx.fc)
    if (fc.approval_stage !== 'Approved') {
      throw new Error(`Expected Approved, got ${fc.approval_stage}`)
    }
    return { detail: `stage=${fc.approval_stage}` }
  })

  await step('1.5 FC submit (docstatus 0→1, status=Active)', async () => {
    await api(page, 'supplycore.api.frontend.submit_doc', { doctype: 'Framework Contract', name: ctx.fc })
    const fc = await getDoc(page, 'Framework Contract', ctx.fc)
    if (fc.docstatus !== 1) throw new Error(`docstatus=${fc.docstatus}`)
    if (fc.status !== 'Active') throw new Error(`status=${fc.status}`)
    return { detail: `docstatus=1, status=${fc.status}` }
  })

  // ============================================================
  // PHASE 2: GỌI HÀNG — Material Request + Purchase Order
  // ============================================================
  await step('2.1 Tạo Material Request', async () => {
    const mr = await createDocViaAPI(page, 'SC Material Request', {
      request_type: 'Purchase',
      transaction_date: today(),
      schedule_date: addDays(today(), 14),
      warehouse: ctx.warehouse_main,
      items: [
        { item: ctx.item, uom: ctx.itemUom, qty: 100, schedule_date: addDays(today(), 14) },
      ],
    })
    ctx.mr = mr.name
    return { detail: `MR=${mr.name}` }
  })

  await step('2.2 MR submit (docstatus=1)', async () => {
    await api(page, 'supplycore.api.frontend.submit_doc', { doctype: 'SC Material Request', name: ctx.mr })
    const mr = await getDoc(page, 'SC Material Request', ctx.mr)
    if (mr.docstatus !== 1) throw new Error(`docstatus=${mr.docstatus}`)
    return { detail: `docstatus=1, status=${mr.status}` }
  })

  await step('2.3 MR approve', async () => {
    try {
      await runDocMethod(page, 'SC Material Request', ctx.mr, 'approve')
      const mr = await getDoc(page, 'SC Material Request', ctx.mr)
      return { detail: `status=${mr.status}` }
    } catch (e) {
      if (e.message.includes('already') || e.message.includes('Approved')) {
        return { detail: 'Đã ở Approved' }
      }
      throw e
    }
  })

  await step('2.4 Tạo Purchase Order link FC', async () => {
    const po = await createDocViaAPI(page, 'SC Purchase Order', {
      supplier: ctx.supplier,
      transaction_date: today(),
      schedule_date: addDays(today(), 10),
      framework_contract: ctx.fc,
      items: [
        { item: ctx.item, uom: ctx.itemUom, qty: 100, rate: 5000,
          warehouse: ctx.warehouse_main, schedule_date: addDays(today(), 10) },
      ],
    })
    ctx.po = po.name
    return { detail: `PO=${po.name}, total=500000` }
  })

  await step('2.5 PO approval workflow + submit', async () => {
    await runDocMethod(page, 'SC Purchase Order', ctx.po, 'submit_for_review')
    let po = await getDoc(page, 'SC Purchase Order', ctx.po)
    if (po.approval_stage === 'Manager Review') {
      await runDocMethod(page, 'SC Purchase Order', ctx.po, 'approve_as_manager',
        { comment: 'E2E approval' })
    }
    po = await getDoc(page, 'SC Purchase Order', ctx.po)
    if (po.approval_stage === 'Executive Review') {
      await runDocMethod(page, 'SC Purchase Order', ctx.po, 'approve_as_executive',
        { comment: 'E2E approval' })
    }
    po = await getDoc(page, 'SC Purchase Order', ctx.po)
    if (po.approval_stage !== 'Approved') {
      throw new Error(`approval_stage=${po.approval_stage}`)
    }
    await api(page, 'supplycore.api.frontend.submit_doc', { doctype: 'SC Purchase Order', name: ctx.po })
    po = await getDoc(page, 'SC Purchase Order', ctx.po)
    if (po.docstatus !== 1) throw new Error(`docstatus=${po.docstatus}`)
    return { detail: `docstatus=1, status=${po.status}` }
  })

  // ============================================================
  // PHASE 3: NHẬN HÀNG — Purchase Receipt
  // ============================================================
  await step('3.1 Tạo Purchase Receipt với batch info', async () => {
    const supplierBatchNo = `LOT-E2E-${rand(5)}`
    const expiryDate = addDays(today(), 730)  // 2 years from now (long expiry)
    const mfgDate = addDays(today(), -30)
    const pr = await createDocViaAPI(page, 'SC Purchase Receipt', {
      supplier: ctx.supplier,
      purchase_order: ctx.po,
      posting_date: today(),
      to_warehouse: ctx.warehouse_main,
      qc_required: 1,
      items: [{
        item: ctx.item, uom: ctx.itemUom,
        qty: 100, po_qty: 100, rate: 5000,
        warehouse: ctx.warehouse_main,
        supplier_batch_no: supplierBatchNo,
        manufacturing_date: mfgDate,
        expiry_date: expiryDate,
      }],
    })
    ctx.pr = pr.name
    ctx.supplier_batch_no = supplierBatchNo
    return { detail: `PR=${pr.name}, supplier_batch_no=${supplierBatchNo}` }
  })

  await step('3.2 PR submit → batch + SLE auto-create', async () => {
    await api(page, 'supplycore.api.frontend.submit_doc', { doctype: 'SC Purchase Receipt', name: ctx.pr })
    const pr = await getDoc(page, 'SC Purchase Receipt', ctx.pr)
    if (pr.docstatus !== 1) throw new Error(`docstatus=${pr.docstatus}`)

    // Verify batch created
    const prItems = pr.items || []
    const itemBatch = prItems[0]?.batch_no
    if (!itemBatch) throw new Error('Batch không được auto-create trên PR Item')
    ctx.batch = itemBatch

    // Verify SLE created
    const sle = await listDocs(page, 'SC Stock Ledger Entry', {
      fields: ['name', 'qty_change', 'balance_qty'],
      filters: { voucher_type: 'SC Purchase Receipt', voucher_no: ctx.pr },
    })
    if (!sle.length) throw new Error('SLE không được tạo')
    ctx.sle_initial = sle[0]

    return { detail: `batch=${itemBatch}, SLE qty=${sle[0].qty_change}, balance=${sle[0].balance_qty}` }
  })

  await step('3.3 Verify batch master created', async () => {
    const batch = await getDoc(page, 'SC Batch', ctx.batch)
    if (batch.item !== ctx.item) throw new Error(`Batch item mismatch: ${batch.item}`)
    if (batch.supplier !== ctx.supplier) throw new Error(`Batch supplier mismatch: ${batch.supplier}`)
    if (batch.supplier_batch_no !== ctx.supplier_batch_no) {
      throw new Error(`supplier_batch_no mismatch: ${batch.supplier_batch_no}`)
    }
    return { detail: `Batch ${ctx.batch}: item=${batch.item}, expiry=${batch.expiry_date}, qc=${batch.qc_status}` }
  })

  // ============================================================
  // PHASE 4: QC — Quality Inspection
  // ============================================================
  await step('4.1 Tạo Quality Inspection cho batch', async () => {
    const qi = await createDocViaAPI(page, 'SC Quality Inspection', {
      purchase_receipt: ctx.pr,
      item: ctx.item,
      batch: ctx.batch,
      inspection_date: today(),
      inspected_by: 'Administrator',
      overall_status: 'Accepted',
      qty_inspected: 100,
      qty_accepted: 100,
      qty_rejected: 0,
      readings: [
        { specification: 'Cảm quan',    status: 'Accepted', value: 'Đạt' },
        { specification: 'Bao bì',      status: 'Accepted', value: 'Nguyên vẹn' },
        { specification: 'Nhãn mác',    status: 'Accepted', value: 'Đầy đủ' },
        { specification: 'Hạn dùng',    status: 'Accepted', value: 'Còn 2 năm' },
      ],
    })
    ctx.qi = qi.name
    return { detail: `QI=${qi.name} với 4 readings` }
  })

  await step('4.2 QI submit → Accepted', async () => {
    await api(page, 'supplycore.api.frontend.submit_doc', { doctype: 'SC Quality Inspection', name: ctx.qi })
    const qi = await getDoc(page, 'SC Quality Inspection', ctx.qi)
    if (qi.docstatus !== 1) throw new Error(`docstatus=${qi.docstatus}`)
    if (qi.overall_status !== 'Accepted') throw new Error(`status=${qi.overall_status}`)
    return { detail: `docstatus=1, overall=${qi.overall_status}` }
  })

  // ============================================================
  // PHASE 5: VERIFY STOCK
  // ============================================================
  await step('5.1 Verify tồn kho qua SLE', async () => {
    const balance = await api(page, 'supplycore.api.frontend.list_docs', {
      doctype: 'SC Stock Ledger Entry',
      fields: ['qty_change'],
      filters: { item: ctx.item, warehouse: ctx.warehouse_main, batch: ctx.batch, is_cancelled: 0 },
      limit: 100,
    })
    const total = balance.reduce((s, r) => s + (r.qty_change || 0), 0)
    if (total < 100) throw new Error(`Stock=${total}, expected 100`)
    return { detail: `Tồn ${ctx.warehouse_main}/${ctx.batch}: ${total}` }
  })

  // ============================================================
  // PHASE 6: CHUYỂN KHO — Stock Entry Material Transfer
  // ============================================================
  await step('6.1 Tạo Stock Entry Material Transfer (30 units)', async () => {
    const se = await createDocViaAPI(page, 'SC Stock Entry', {
      entry_type: 'Material Transfer',
      posting_date: today(),
      from_warehouse: ctx.warehouse_main,
      to_warehouse: ctx.warehouse_to,
      purpose: 'E2E test transfer',
      items: [{
        item: ctx.item, uom: ctx.itemUom,
        qty: 30, batch: ctx.batch,
        valuation_rate: 5000,
        s_warehouse: ctx.warehouse_main,
        t_warehouse: ctx.warehouse_to,
      }],
    })
    ctx.se_transfer = se.name
    return { detail: `SE=${se.name}, qty=30 batch=${ctx.batch}` }
  })

  await step('6.2 SE submit → SLE âm ở wh_main + dương ở wh_to', async () => {
    await api(page, 'supplycore.api.frontend.submit_doc', { doctype: 'SC Stock Entry', name: ctx.se_transfer })
    const se = await getDoc(page, 'SC Stock Entry', ctx.se_transfer)
    if (se.docstatus !== 1) throw new Error(`docstatus=${se.docstatus}`)
    const sle = await listDocs(page, 'SC Stock Ledger Entry', {
      fields: ['warehouse', 'qty_change'],
      filters: { voucher_type: 'SC Stock Entry', voucher_no: ctx.se_transfer },
    })
    const negative = sle.filter(s => s.qty_change < 0).length
    const positive = sle.filter(s => s.qty_change > 0).length
    if (negative < 1 || positive < 1) throw new Error(`pos=${positive}, neg=${negative}`)
    return { detail: `SLE: ${negative} âm + ${positive} dương` }
  })

  await step('6.3 Verify tồn 2 kho sau transfer (70 + 30 = 100)', async () => {
    const sleMain = await listDocs(page, 'SC Stock Ledger Entry', {
      fields: ['qty_change'],
      filters: { item: ctx.item, warehouse: ctx.warehouse_main, batch: ctx.batch, is_cancelled: 0 },
      limit: 100,
    })
    const sleTo = await listDocs(page, 'SC Stock Ledger Entry', {
      fields: ['qty_change'],
      filters: { item: ctx.item, warehouse: ctx.warehouse_to, batch: ctx.batch, is_cancelled: 0 },
      limit: 100,
    })
    const totMain = sleMain.reduce((s, r) => s + (r.qty_change || 0), 0)
    const totTo = sleTo.reduce((s, r) => s + (r.qty_change || 0), 0)
    if (totMain !== 70 || totTo !== 30) throw new Error(`Main=${totMain}, To=${totTo}, expected 70+30`)
    return { detail: `${ctx.warehouse_main}=${totMain}, ${ctx.warehouse_to}=${totTo}` }
  })

  // PHASE 7 (Cấp phát Bệnh nhân / Patient Dispensing + BHYT) đã bỏ — GĐ1 gỡ
  // M7 Dispensing/BHYT khỏi backend. Verify tồn cuối cùng dùng số dư sau
  // PHASE 6 (70 ở wh_main).

  // ============================================================
  // VERIFY UI VISIBILITY
  // ============================================================
  await step('8.1 UI: FC visible trong list', async () => {
    await page.goto(`${BASE}/supplycore/list/Framework%20Contract`)
    await page.waitForTimeout(1500)
    const fcCell = await page.locator(`text=${ctx.fc}`).count()
    await page.screenshot({ path: `${SCREENSHOTS}/fc_list.png` })
    if (fcCell < 1) throw new Error(`FC ${ctx.fc} không visible trong list`)
    return { detail: `${ctx.fc} visible` }
  })

  await step('8.2 UI: PR detail page render', async () => {
    await page.goto(`${BASE}/supplycore/doc/SC%20Purchase%20Receipt/${encodeURIComponent(ctx.pr)}`)
    await page.waitForTimeout(2000)
    await page.screenshot({ path: `${SCREENSHOTS}/pr_detail.png`, fullPage: true })
    const title = await page.locator('h1').first().textContent()
    if (!title?.includes(ctx.pr)) throw new Error(`Title không chứa PR name: ${title}`)
    return { detail: `Title="${title}"` }
  })

} catch (e) {
  console.log(`\n❌ FATAL at step: ${e.message.slice(0, 300)}`)
} finally {
  await browser.close()
}

// ===========================================================
// SUMMARY + LOG MD
// ===========================================================
const passed = stepResults.filter(s => s.ok).length
const failed = stepResults.filter(s => !s.ok).length
const totalDuration = stepResults.reduce((s, r) => s + r.dt, 0)

console.log(`\n╔═══════════════ SUMMARY ═══════════════╗`)
console.log(`║ Passed: ${String(passed).padStart(3)} / ${stepResults.length}                  ║`)
console.log(`║ Failed: ${String(failed).padStart(3)}                          ║`)
console.log(`║ Duration: ${Math.round(totalDuration / 1000)}s                        ║`)
console.log(`╚═══════════════════════════════════════╝`)
console.log(`\nContext:`, JSON.stringify(ctx, null, 2))

// Append to log MD
const ts = new Date().toISOString()
const block = [
  ``,
  `## Run ${ts}`,
  ``,
  `**Result**: ${passed}/${stepResults.length} pass${failed ? ` · ${failed} fail` : ' ✅'}`,
  `**Duration**: ${Math.round(totalDuration / 1000)}s`,
  ``,
  `### Steps`,
  ``,
  `| # | Step | Result | Detail | Time |`,
  `|---|------|--------|--------|------|`,
  ...stepResults.map((s, i) => `| ${i + 1} | ${s.name} | ${s.ok ? '✅' : '❌'} | ${(s.detail || '').replace(/\|/g, '\\|').slice(0, 120)} | ${s.dt}ms |`),
  ``,
]

if (issues.length) {
  block.push(`### Issues found`, ``)
  issues.forEach((iss, i) => {
    block.push(`#### Issue ${i + 1}: ${iss.step}`, ``)
    block.push(`**Error**: ${iss.issue}`, ``)
    if (iss.rootCause) block.push(`**Root cause**: ${iss.rootCause}`, ``)
    if (iss.fix) block.push(`**Fix**: ${iss.fix}`, ``)
  })
}

if (errors.length) {
  block.push(`### Console/JS errors`, ``)
  errors.slice(0, 10).forEach(e => block.push(`- ${e.replace(/\|/g, '\\|').slice(0, 200)}`))
  block.push(``)
}

block.push(`### Context (created docs)`, ``)
block.push('```json')
block.push(JSON.stringify(ctx, null, 2))
block.push('```')
block.push(``)

appendFileSync(LOG_FILE, block.join('\n'))

console.log(`\nLog appended: ${LOG_FILE}`)
console.log(`Screenshots: ${SCREENSHOTS}/`)

process.exit(failed === 0 ? 0 : 1)
