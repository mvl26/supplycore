// Suite 30: Data Import/Export — Frappe-style trên SPA
//
// Test:
//  1. Sidebar link → navigate vào /data-io
//  2. DataIO page render, select module + doctype, schema load
//  3. Download template CSV (intercept network response)
//  4. Download template + dữ liệu mẫu (XLSX)
//  5. Upload CSV → dry-run → preview hiện "create"
//  6. Commit → tạo bản ghi thật, badge "Đã tạo"
//  7. SC Stock Ledger Entry → hiện banner export-only, không có form Import
//  8. DocList "📥 Nhập / Xuất" button → deep-link vào /data-io?dt=...

const RUN_ID = Date.now().toString(36)
const TEST_UOM = `iotest-${RUN_ID}`

export const tests = [
  {
    name: 'Sidebar có link "Nhập / Xuất"',
    run: async ({ page, BASE, OUT, name }) => {
      await page.goto(`${BASE}/supplycore/`)
      await page.waitForTimeout(800)
      const link = page.locator('aside a[href*="/data-io"]')
      const count = await link.count()
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      return count >= 1
        ? { ok: true, detail: `link found` }
        : { ok: false, detail: 'sidebar link missing' }
    },
  },
  {
    name: 'DataIO page render + chọn SC UOM',
    run: async ({ page, BASE, OUT, name }) => {
      await page.goto(`${BASE}/supplycore/data-io`)
      await page.waitForTimeout(1200)
      const h1 = (await page.locator('h1').first().textContent()) || ''
      const moduleSelect = page.locator('select').first()
      const doctypeSelect = page.locator('select').nth(1)
      await moduleSelect.selectOption('m0')
      await page.waitForTimeout(300)
      await doctypeSelect.selectOption('SC UOM')
      await page.waitForTimeout(800)
      // Schema info hiện ra 4 ô (Trường, writable, submittable, autoname)
      const writableLabel = await page.locator('text=Trường writable').count()
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      return h1.includes('Nhập') && writableLabel >= 1
        ? { ok: true, detail: `h1="${h1}", schema loaded` }
        : { ok: false, detail: `h1="${h1}", schema=${writableLabel}` }
    },
  },
  {
    name: 'Tải template CSV rỗng',
    run: async ({ page, BASE, OUT, name }) => {
      await page.goto(`${BASE}/supplycore/data-io?m=m0&dt=SC%20UOM`)
      await page.waitForTimeout(1000)
      // Chọn CSV
      const fmtSelect = page.locator('select').filter({ has: page.locator('option[value="xlsx"]') }).first()
      await fmtSelect.selectOption('csv')
      // Intercept response
      const respP = page.waitForResponse(r => r.url().includes('data_io.get_template') && r.status() === 200, { timeout: 8000 })
      await page.click('button:has-text("Template rỗng")')
      const resp = await respP
      const body = await resp.json()
      const file = body.message
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      // Decode base64 và parse header
      const csv = Buffer.from(file.content_b64, 'base64').toString('utf-8').replace(/^﻿/, '')
      const headers = csv.split(/\r?\n/)[0].split(',')
      return file.filename === 'SC_UOM.csv' && headers.includes('name') && headers.includes('uom_name')
        ? { ok: true, detail: `headers=${headers.join(',')}` }
        : { ok: false, detail: `bad file: ${JSON.stringify(file).slice(0, 200)}` }
    },
  },
  {
    name: 'Tải template XLSX kèm dữ liệu mẫu',
    run: async ({ page, BASE, OUT, name }) => {
      await page.goto(`${BASE}/supplycore/data-io?m=m0&dt=SC%20UOM`)
      await page.waitForTimeout(1000)
      const fmtSelect = page.locator('select').filter({ has: page.locator('option[value="xlsx"]') }).first()
      await fmtSelect.selectOption('xlsx')
      const respP = page.waitForResponse(r => r.url().includes('data_io.get_template') && r.status() === 200, { timeout: 8000 })
      await page.click('button:has-text("Template + dữ liệu mẫu")')
      const resp = await respP
      const body = await resp.json()
      const file = body.message
      const buf = Buffer.from(file.content_b64, 'base64')
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      // XLSX = ZIP → bắt đầu bằng "PK\x03\x04"
      const isXlsx = buf[0] === 0x50 && buf[1] === 0x4b
      return file.filename.endsWith('.xlsx') && isXlsx
        ? { ok: true, detail: `${file.filename} (${buf.length} bytes)` }
        : { ok: false, detail: `not xlsx: ${buf.slice(0, 4).toString('hex')}` }
    },
  },
  {
    name: 'Upload CSV → Dry-run hiện preview "create"',
    run: async ({ page, BASE, OUT, name }) => {
      await page.goto(`${BASE}/supplycore/data-io?m=m0&dt=SC%20UOM`)
      await page.waitForTimeout(1000)
      const csv = `name,uom_name,abbreviation,must_be_whole_number,disabled\n${TEST_UOM},${TEST_UOM},${TEST_UOM},1,0\n`
      await page.setInputFiles('#sc-import-file', {
        name: 'uom-test.csv',
        mimeType: 'text/csv',
        buffer: Buffer.from(csv, 'utf-8'),
      })
      await page.waitForTimeout(400)
      const respP = page.waitForResponse(r => r.url().includes('data_io.import_data') && r.status() === 200, { timeout: 10000 })
      await page.click('button:has-text("Dry-run")')
      const resp = await respP
      const body = (await resp.json()).message
      await page.waitForTimeout(800)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      const previewActions = (body.preview || []).map(p => p.action)
      const wouldCreate = body.summary?.would_create || 0
      return wouldCreate === 1 && previewActions.includes('create')
        ? { ok: true, detail: `would_create=${wouldCreate}, errors=${body.errors.length}` }
        : { ok: false, detail: `summary=${JSON.stringify(body.summary)} errs=${JSON.stringify(body.errors)}` }
    },
  },
  {
    name: 'Commit → tạo bản ghi (badge "Đã tạo")',
    run: async ({ page, BASE, OUT, name }) => {
      await page.goto(`${BASE}/supplycore/data-io?m=m0&dt=SC%20UOM`)
      await page.waitForTimeout(1000)
      const csv = `name,uom_name,abbreviation,must_be_whole_number,disabled\n${TEST_UOM}-c,${TEST_UOM}-c,${TEST_UOM}-c,1,0\n`
      await page.setInputFiles('#sc-import-file', {
        name: 'uom-commit.csv',
        mimeType: 'text/csv',
        buffer: Buffer.from(csv, 'utf-8'),
      })
      await page.waitForTimeout(400)
      // Dry-run trước (nút Commit chỉ mở sau khi dry-run OK)
      const dryP = page.waitForResponse(r => r.url().includes('data_io.import_data') && r.status() === 200, { timeout: 10000 })
      await page.click('button:has-text("Dry-run")')
      await dryP
      await page.waitForTimeout(400)
      // Stub confirm dialog → tự accept
      page.once('dialog', d => d.accept())
      const commitP = page.waitForResponse(r => r.url().includes('data_io.import_data') && r.status() === 200, { timeout: 10000 })
      await page.click('button:has-text("Commit")')
      const commitResp = await commitP
      const body = (await commitResp.json()).message
      await page.waitForTimeout(800)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      const ok = body.summary?.created === 1 && body.preview?.[0]?.action === 'created'
      return ok
        ? { ok: true, detail: `created=${body.summary.created}, name=${body.preview[0].name}` }
        : { ok: false, detail: `summary=${JSON.stringify(body.summary)}` }
    },
  },
  {
    name: 'SC Stock Ledger Entry → banner export-only',
    run: async ({ page, BASE, OUT, name }) => {
      await page.goto(`${BASE}/supplycore/data-io?m=m4&dt=SC%20Stock%20Ledger%20Entry`)
      await page.waitForTimeout(1200)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      // Banner cảnh báo
      const banner = await page.locator('text=sổ hệ thống').count()
      // Không có file input (form Import ẩn)
      const fileInput = await page.locator('#sc-import-file').count()
      return banner >= 1 && fileInput === 0
        ? { ok: true, detail: 'banner shown, import form hidden' }
        : { ok: false, detail: `banner=${banner}, file_input=${fileInput}` }
    },
  },
  {
    name: 'DocList có nút "📥 Nhập / Xuất" deep-link',
    run: async ({ page, BASE, OUT, name }) => {
      await page.goto(`${BASE}/supplycore/list/SC%20UOM`)
      await page.waitForTimeout(1200)
      // Scope vào main (không lấy sidebar aside)
      const link = page.locator('main a[href*="/data-io"]').first()
      const href = await link.getAttribute('href')
      await link.click()
      await page.waitForTimeout(1200)
      const url = page.url()
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      const okHref = (href || '').includes('SC%20UOM') || (href || '').includes('SC+UOM')
      const okNav = url.includes('/data-io') && (url.includes('SC%20UOM') || url.includes('SC+UOM'))
      return okHref && okNav
        ? { ok: true, detail: `nav OK, href=${href}` }
        : { ok: false, detail: `href=${href}, url=${url}` }
    },
  },
]
