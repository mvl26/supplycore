// M1 Contract — UC-01..04 (FC lifecycle)
import { apiGetList, apiGetDoc, apiCount, navigateTo } from '../helpers.mjs'

export const tests = [
  {
    name: 'UC-01: List Framework Contract hiển thị FC active',
    run: async ({ page, BASE, OUT, name }) => {
      await navigateTo(page, BASE, '/list/Framework%20Contract')
      await page.waitForTimeout(1200)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      const rows = await page.locator('table tbody tr').count()
      const active = await apiCount(page, 'Framework Contract', { status: 'Active' })
      return rows >= 1
        ? { ok: true, detail: `${rows} FC visible, ${active} Active` }
        : { ok: false, detail: 'No FCs' }
    },
  },
  {
    name: 'UC-02: FC detail có items child table',
    run: async ({ page, BASE, OUT, name }) => {
      const fcs = await apiGetList(page, 'Framework Contract', {
        fields: ['name'], filters: [['status', '=', 'Active']], limit: 1,
      })
      if (!fcs.length) return { ok: false, detail: 'No Active FC' }
      const fc = fcs[0].name
      await navigateTo(page, BASE, `/doc/Framework%20Contract/${encodeURIComponent(fc)}`)
      await page.waitForTimeout(1500)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      const doc = await apiGetDoc(page, 'Framework Contract', fc)
      return (doc.items?.length || 0) >= 1
        ? { ok: true, detail: `${fc} có ${doc.items.length} items` }
        : { ok: false, detail: 'No items' }
    },
  },
  {
    name: 'UC-02: FC remaining_value tính đúng',
    run: async ({ page }) => {
      const fcs = await apiGetList(page, 'Framework Contract', {
        fields: ['name', 'total_value', 'used_value', 'remaining_value'],
        filters: [['status', '=', 'Active']], limit: 3,
      })
      for (const fc of fcs) {
        const expected = (fc.total_value || 0) - (fc.used_value || 0)
        const diff = Math.abs((fc.remaining_value || 0) - expected)
        if (diff > 1000) {
          return { ok: false, detail: `${fc.name}: remaining=${fc.remaining_value}, expected=${expected}` }
        }
      }
      return { ok: true, detail: `${fcs.length} FCs có remaining = total - used` }
    },
  },
]
