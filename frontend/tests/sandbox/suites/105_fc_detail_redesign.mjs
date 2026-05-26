// Suite 105: Framework Contract detail page redesign smoke
//
// Mục tiêu: verify hero + value tiles + validity timeline + items totals
// render đúng trên submitted FC.

export const tests = [
  {
    name: 'FC detail: hero, value tiles, validity bar, totals footer hiển thị',
    run: async ({ page, BASE, OUT, name }) => {
      // Tìm 1 FC submitted
      const csrf = await page.evaluate(() => window.sc_csrf)
      const fc = await page.evaluate(async ({ csrf }) => {
        const r = await fetch('/api/method/supplycore.api.frontend.list_docs', {
          method: 'POST', credentials: 'include',
          headers: { 'Content-Type': 'application/json', 'X-Frappe-CSRF-Token': csrf },
          body: JSON.stringify({
            doctype: 'Framework Contract', fields: ['name'],
            filters: { docstatus: 1 }, limit: 1,
          }),
        })
        const d = await r.json()
        return (d.message || [])[0]?.name
      }, { csrf })
      if (!fc) return { ok: 'skip', detail: 'Không có FC submitted để smoke' }

      await page.goto(`${BASE}/supplycore/doc/Framework%20Contract/${encodeURIComponent(fc)}`,
        { waitUntil: 'networkidle' })
      await page.waitForTimeout(1500)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })

      // Checks
      const checks = await page.evaluate(() => {
        const hasHero = !!document.querySelector('h1') &&
          document.body.textContent.includes('Hợp đồng khung')
        const hasTimeline = document.body.textContent.includes('thời lượng') ||
          document.body.textContent.includes('Còn') ||
          document.body.textContent.includes('Đã quá hạn')
        const hasValueTiles = document.body.textContent.includes('Tổng giá trị') &&
          document.body.textContent.includes('Còn lại khả dụng')
        const hasItems = document.body.textContent.includes('Danh mục vật tư')
        const hasTotals = !!document.querySelector('table tfoot')
        const hasApprovalTimeline = document.body.textContent.includes('Quy trình phê duyệt')
        return { hasHero, hasTimeline, hasValueTiles, hasItems, hasTotals, hasApprovalTimeline }
      })

      const missing = Object.entries(checks).filter(([, v]) => !v).map(([k]) => k)
      return missing.length === 0
        ? { ok: true, detail: `FC ${fc}: hero + timeline + tiles + items + totals + approval OK` }
        : { ok: false, detail: `FC ${fc} thiếu: ${missing.join(', ')}` }
    },
  },
]
