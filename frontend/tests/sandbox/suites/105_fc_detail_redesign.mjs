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
      if (missing.length) {
        return { ok: false, detail: `FC ${fc} thiếu: ${missing.join(', ')}` }
      }

      // Alignment check: tfoot cells phải có cùng padding với tbody cells
      const align = await page.evaluate(() => {
        const table = document.querySelector('table.sc-table, table')
        if (!table) return { ok: false, reason: 'no-table' }
        const tbodyTd = table.querySelector('tbody td')
        const tfootTds = table.querySelectorAll('tfoot td')
        if (!tbodyTd || !tfootTds.length) return { ok: false, reason: 'no-cells' }
        const tb = getComputedStyle(tbodyTd)
        const bodyPx = `${tb.paddingLeft} ${tb.paddingRight} ${tb.paddingTop} ${tb.paddingBottom}`
        const mismatched = []
        tfootTds.forEach((td, i) => {
          const tf = getComputedStyle(td)
          const footPx = `${tf.paddingLeft} ${tf.paddingRight} ${tf.paddingTop} ${tf.paddingBottom}`
          if (footPx !== bodyPx) mismatched.push(`col${i}:${footPx}`)
        })
        // Vertical alignment of first numeric tbody td vs first numeric tfoot td (column "SL HĐ" = idx 4)
        const bodyRow = table.querySelector('tbody tr')
        const bodyTds = bodyRow ? bodyRow.querySelectorAll('td') : []
        const slhdBody = bodyTds[4]?.getBoundingClientRect()
        const slhdFoot = tfootTds[1]?.getBoundingClientRect()
        const xDiff = (slhdBody && slhdFoot) ? Math.abs(slhdBody.right - slhdFoot.right) : -1
        return { ok: mismatched.length === 0 && xDiff <= 1,
                 mismatched, bodyPx, xDiff,
                 footCount: tfootTds.length }
      })
      if (!align.ok) {
        return { ok: false,
          detail: `Alignment fail mismatch=${(align.mismatched||[]).join('|').slice(0,120)} xDiff=${align.xDiff}` }
      }
      return { ok: true,
        detail: `FC ${fc}: hero+timeline+tiles+items+totals+approval OK, tfoot align xDiff=${align.xDiff}px` }
    },
  },
]
