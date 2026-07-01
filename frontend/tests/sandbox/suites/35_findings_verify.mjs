// Suite 35: Verify các fix F01-F13 qua HTTP/UI thật.
const DRAFT_PO = 'SC-PO-2026-04308'
const MR = 'SC-MR-2026-758939'
const QI = 'SC-QI-2026-04061'

async function rpc(page, method, body) {
  return page.evaluate(async ({ method, body }) => {
    const r = await fetch(`/api/method/${method}`, {
      method: 'POST', credentials: 'include',
      headers: { 'Content-Type': 'application/json', 'X-Frappe-CSRF-Token': window.sc_csrf || '', Accept: 'application/json' },
      body: JSON.stringify(body),
    })
    const d = await r.json().catch(() => ({}))
    if (!r.ok) throw new Error(d.exception || `HTTP ${r.status}`)
    return d.message
  }, { method, body })
}

export const tests = [
  {
    name: 'F05: list_candidates MR chỉ trả Approved (ẩn Ordered)',
    run: async ({ page }) => {
      const mrs = await rpc(page, 'supplycore.api.fetch_upstream.list_candidates',
        { source_doctype: 'SC Material Request', target_doctype: 'SC Purchase Order', limit: 20 })
      const bad = []
      for (const m of mrs || []) {
        const st = await rpc(page, 'frappe.client.get_value',
          { doctype: 'SC Material Request', filters: { name: m.name }, fieldname: 'status' })
        if (st?.status !== 'Approved') bad.push(`${m.name}=${st?.status}`)
      }
      return bad.length ? { ok: false, detail: 'Có nguồn không-Approved: ' + bad.join(',') }
        : { ok: true, detail: `${(mrs || []).length} nguồn MR đều Approved` }
    },
  },
  {
    name: 'F02: candidate FC có supplier_name (Tên NCC)',
    run: async ({ page }) => {
      const fcs = await rpc(page, 'supplycore.api.fetch_upstream.list_candidates',
        { source_doctype: 'Framework Contract', target_doctype: 'SC Purchase Order', limit: 3 })
      if (!fcs || !fcs.length) return { ok: true, detail: 'không có FC (skip)' }
      return ('supplier_name' in fcs[0])
        ? { ok: true, detail: `FC candidate có supplier_name="${fcs[0].supplier_name || '—'}"` }
        : { ok: false, detail: 'FC candidate thiếu supplier_name' }
    },
  },
  {
    name: 'F01: fetch MR→PO điền warehouse mỗi dòng từ header',
    run: async ({ page }) => {
      const res = await rpc(page, 'supplycore.api.fetch_upstream.fetch',
        { source_doctype: 'SC Material Request', source_name: MR, target_doctype: 'SC Purchase Order' })
      const items = res?.items || []
      if (!items.length) return { ok: false, detail: 'fetch không trả dòng nào' }
      const missing = items.filter(i => !i.warehouse).length
      return missing === 0
        ? { ok: true, detail: `${items.length} dòng đều có warehouse` }
        : { ok: false, detail: `${missing}/${items.length} dòng thiếu warehouse` }
    },
  },
  {
    name: 'F08: DocList PO có cột "HĐ khung" + "YCMH"',
    run: async ({ page, BASE, OUT, name }) => {
      await page.goto(`${BASE}/supplycore/list/${encodeURIComponent('SC Purchase Order')}`)
      await page.waitForTimeout(1200)
      const heads = (await page.locator('table thead th').allInnerTexts()).join('|').toLowerCase()
      await page.screenshot({ path: `${OUT}/${name}.png` })
      return (heads.includes('hđ khung') && heads.includes('ycmh'))
        ? { ok: true, detail: 'có cột HĐ khung + YCMH' }
        : { ok: false, detail: 'thiếu — có: ' + heads }
    },
  },
  {
    name: 'F07: PO nháp có nút "Xóa nháp"',
    run: async ({ page, BASE, OUT, name }) => {
      await page.goto(`${BASE}/supplycore/doc/${encodeURIComponent('SC Purchase Order')}/${DRAFT_PO}`)
      await page.waitForTimeout(1500)
      const del = await page.locator('button', { hasText: 'Xóa nháp' }).count()
      await page.screenshot({ path: `${OUT}/${name}.png` })
      return del > 0 ? { ok: true, detail: 'có nút Xóa nháp' } : { ok: false, detail: 'thiếu nút Xóa nháp' }
    },
  },
  {
    name: 'F10: QC form có trường truy xuất PO/HĐK/YCMH',
    run: async ({ page, BASE, OUT, name }) => {
      await page.goto(`${BASE}/supplycore/doc/${encodeURIComponent('SC Quality Inspection')}/${QI}`)
      await page.waitForTimeout(1500)
      const body = await page.locator('body').innerText()
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      const hasPO = body.includes('Đơn mua')
      const hasFC = body.includes('HĐ khung') || body.includes('Hợp đồng khung')
      const hasMR = body.includes('YCMH') || body.includes('Yêu cầu mua') || body.includes('YC mua')
      return (hasPO && hasFC && hasMR) ? { ok: true, detail: 'có PO + HĐK + YCMH' }
        : { ok: false, detail: `PO=${hasPO} FC=${hasFC} MR=${hasMR}` }
    },
  },
  {
    name: 'F11: form PO (nháp) có mục "Tài liệu đính kèm"',
    run: async ({ page, BASE, OUT, name }) => {
      await page.goto(`${BASE}/supplycore/doc/${encodeURIComponent('SC Purchase Order')}/${DRAFT_PO}`)
      await page.waitForTimeout(1500)
      const body = await page.locator('body').innerText()
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      return body.includes('Tài liệu đính kèm')
        ? { ok: true, detail: 'có mục đính kèm' } : { ok: false, detail: 'thiếu mục đính kèm' }
    },
  },
]
