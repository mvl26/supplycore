// Suite 33: Chained fetch — "Lấy từ upstream" prefill form
//
// Flow tested:
//   1. SC Material Request mới — FetchUpstream hiện, có nguồn "Framework Contract"
//   2. Click chọn 1 FC → header (request_type=Purchase) + items được merge
//   3. SC Purchase Order mới — hỗ trợ 2 nguồn (FC + MR)
//   4. Fetch từ FC → supplier + framework_contract + items có rate
//   5. SC Purchase Receipt mới — nguồn "PO"
//   6. Fetch từ PO → supplier + purchase_order + items
//   7. Backend API: validate mappings symmetry — sources_for() trả non-empty cho 7 target

const BASE_URL = process.env.SC_BASE || 'http://supplycore'

async function apiCall(page, method, args = {}) {
  return page.evaluate(async ({ m, a }) => {
    const fd = new FormData()
    for (const [k, v] of Object.entries(a)) fd.append(k, v)
    const r = await fetch(`/api/method/${m}`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'X-Frappe-CSRF-Token': window.sc_csrf || '' },
      body: fd,
    })
    return r.ok ? (await r.json()).message : null
  }, { m: method, a: args })
}

async function pickFirstActiveFC(page) {
  const list = await apiCall(page, 'supplycore.api.fetch_upstream.list_candidates', {
    source_doctype: 'Framework Contract',
    target_doctype: 'SC Purchase Order',
    limit: 1,
  })
  return list && list[0] ? list[0].name : null
}

export const tests = [
  {
    name: 'sources_for() returns mappings cho 7 target',
    run: async ({ page, BASE, OUT, name }) => {
      await page.goto(`${BASE}/supplycore/dashboard`)
      await page.waitForTimeout(800)
      const expected = [
        'SC Material Request', 'SC Purchase Order', 'SC Purchase Receipt',
        'SC Purchase Invoice', 'SC Quality Inspection', 'SC Stock Entry',
        'SC Stock Reconciliation',
      ]
      const results = {}
      for (const t of expected) {
        const s = await apiCall(page, 'supplycore.api.fetch_upstream.sources_for',
          { target_doctype: t })
        results[t] = (s || []).length
      }
      const ok = Object.values(results).every(n => n >= 1)
      return ok
        ? { ok: true, detail: Object.entries(results).map(([k, v]) => `${k.replace('SC ', '')}=${v}`).join(', ') }
        : { ok: false, detail: JSON.stringify(results) }
    },
  },

  {
    name: 'MR mới: FetchUpstream hiện "Framework Contract"',
    run: async ({ page, BASE, OUT, name }) => {
      await page.goto(`${BASE}/supplycore/doc/SC%20Material%20Request/new`)
      await page.waitForTimeout(1500)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      const btn = page.locator('button:has-text("Lấy từ")')
      const cnt = await btn.count()
      if (!cnt) return { ok: false, detail: 'FetchUpstream button missing' }
      await btn.first().click()
      await page.waitForTimeout(500)
      const hasFC = await page.locator('button:has-text("Framework Contract")').count()
      const sourceBtnVisible = hasFC > 0
      return sourceBtnVisible
        ? { ok: true, detail: 'FC source visible' }
        : { ok: false, detail: `expected FC source, got ${hasFC}` }
    },
  },

  {
    name: 'FC → MR: header + items merge',
    run: async ({ page, BASE, OUT, name }) => {
      await page.goto(`${BASE}/supplycore/doc/SC%20Material%20Request/new`)
      await page.waitForTimeout(1500)
      // Get an active FC
      const fcName = await pickFirstActiveFC(page)
      if (!fcName) return { ok: false, detail: 'No active FC in DB' }
      // Click "Lấy từ"
      await page.locator('button:has-text("Lấy từ")').first().click()
      await page.waitForTimeout(400)
      // Click the candidate matching fcName
      const respP = page.waitForResponse(r => r.url().includes('fetch_upstream.fetch') && r.status() === 200, { timeout: 8000 })
      await page.locator(`button:has-text("${fcName}")`).first().click()
      const resp = await respP
      const body = (await resp.json()).message
      await page.waitForTimeout(800)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      const itemsCount = (body.items || []).length
      // Verify form đã có row trong child table
      const childRows = await page.locator('table.sc-table tbody tr, table tbody tr').count()
      return itemsCount > 0 && childRows >= itemsCount
        ? { ok: true, detail: `${itemsCount} items merged, ${childRows} rows in table` }
        : { ok: false, detail: `items=${itemsCount} rows=${childRows}` }
    },
  },

  {
    name: 'PO mới: FetchUpstream hỗ trợ FC + MR',
    run: async ({ page, BASE, OUT, name }) => {
      await page.goto(`${BASE}/supplycore/doc/SC%20Purchase%20Order/new`)
      await page.waitForTimeout(1500)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      await page.locator('button:has-text("Lấy từ")').first().click()
      await page.waitForTimeout(500)
      const fcBtn = await page.locator('button:has-text("Framework Contract")').count()
      const mrBtn = await page.locator('button:has-text("Material Request")').count()
      return fcBtn >= 1 && mrBtn >= 1
        ? { ok: true, detail: `FC=${fcBtn}, MR=${mrBtn}` }
        : { ok: false, detail: `FC=${fcBtn}, MR=${mrBtn}` }
    },
  },

  {
    name: 'FC → PO: supplier + framework_contract + rate prefilled',
    run: async ({ page, BASE, OUT, name }) => {
      await page.goto(`${BASE}/supplycore/doc/SC%20Purchase%20Order/new`)
      await page.waitForTimeout(1500)
      const fcName = await pickFirstActiveFC(page)
      if (!fcName) return { ok: false, detail: 'No FC available' }
      await page.locator('button:has-text("Lấy từ")').first().click()
      await page.waitForTimeout(400)
      const respP = page.waitForResponse(r => r.url().includes('fetch_upstream.fetch') && r.status() === 200, { timeout: 8000 })
      await page.locator(`button:has-text("${fcName}")`).first().click()
      const resp = await respP
      const body = (await resp.json()).message
      await page.waitForTimeout(1000)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      // Header must have supplier + framework_contract
      const hdr = body.header || {}
      const okHeader = !!hdr.supplier && hdr.framework_contract === fcName
      // Items have rate
      const itemsWithRate = (body.items || []).filter(it => it.rate > 0).length
      return okHeader && itemsWithRate > 0
        ? { ok: true, detail: `supplier=${hdr.supplier}, fc=${hdr.framework_contract}, rated_items=${itemsWithRate}` }
        : { ok: false, detail: `header=${JSON.stringify(hdr)} items=${(body.items || []).length}` }
    },
  },

  {
    name: 'API: FC→PR mapping không có (PR phải đi qua PO)',
    run: async ({ page, BASE, OUT, name }) => {
      // Negative test: ensure PR sources don't include FC (only PO)
      const sources = await apiCall(page, 'supplycore.api.fetch_upstream.sources_for',
        { target_doctype: 'SC Purchase Receipt' })
      const dts = (sources || []).map(s => s.source_doctype)
      const onlyPO = dts.length === 1 && dts[0] === 'SC Purchase Order'
      return onlyPO
        ? { ok: true, detail: 'PR sources = [PO]' }
        : { ok: false, detail: `PR sources = ${JSON.stringify(dts)}` }
    },
  },

  {
    name: 'API: candidate filter — submitted/Active only',
    run: async ({ page, BASE, OUT, name }) => {
      // FC candidates must all have status=Active + docstatus=1
      const list = await apiCall(page, 'supplycore.api.fetch_upstream.list_candidates',
        { source_doctype: 'Framework Contract', target_doctype: 'SC Purchase Order', limit: 5 })
      if (!list || !list.length) return { ok: false, detail: 'no candidates' }
      // Spot-check first via direct DB-like get_value
      const first = list[0].name
      const meta = await apiCall(page, 'frappe.client.get_value',
        { doctype: 'Framework Contract', filters: JSON.stringify({ name: first }),
          fieldname: JSON.stringify(['status', 'docstatus']) })
      const ok = meta?.status === 'Active' && meta?.docstatus === 1
      return ok
        ? { ok: true, detail: `${list.length} candidates, first ${first} is Active+submitted` }
        : { ok: false, detail: `meta=${JSON.stringify(meta)}` }
    },
  },
]
