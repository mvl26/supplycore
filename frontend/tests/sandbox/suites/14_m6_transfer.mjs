// M6 Transfer — UC-18
import { apiGetList, apiGetDoc, navigateTo } from '../helpers.mjs'

export const tests = [
  {
    name: 'UC-18: Stock Entry Material Transfer submitted',
    run: async ({ page, BASE, OUT, name }) => {
      const ses = await apiGetList(page, 'SC Stock Entry', {
        fields: ['name', 'entry_type', 'from_warehouse', 'to_warehouse', 'total_qty'],
        filters: [['entry_type', '=', 'Material Transfer'], ['docstatus', '=', 1]],
        limit: 1,
      })
      if (!ses.length) return { ok: false, detail: 'No Material Transfer SE' }
      await navigateTo(page, BASE, `/doc/SC%20Stock%20Entry/${encodeURIComponent(ses[0].name)}`)
      await page.waitForTimeout(1500)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      const se = ses[0]
      return (se.from_warehouse && se.to_warehouse && se.from_warehouse !== se.to_warehouse)
        ? { ok: true, detail: `${se.name}: ${se.from_warehouse} → ${se.to_warehouse}, qty=${se.total_qty}` }
        : { ok: false, detail: `Bad SE: ${JSON.stringify(se)}` }
    },
  },
  {
    name: 'UC-18: SE submit tạo SLE âm + dương',
    run: async ({ page }) => {
      const ses = await apiGetList(page, 'SC Stock Entry', {
        fields: ['name'],
        filters: [['entry_type', '=', 'Material Transfer'], ['docstatus', '=', 1]],
        limit: 1,
      })
      if (!ses.length) return { ok: false, detail: 'No SE' }
      const sle = await apiGetList(page, 'SC Stock Ledger Entry', {
        fields: ['name', 'qty_change'],
        filters: [['voucher_type', '=', 'SC Stock Entry'], ['voucher_no', '=', ses[0].name]],
        limit: 20,
      })
      const positive = sle.filter(s => s.qty_change > 0).length
      const negative = sle.filter(s => s.qty_change < 0).length
      return (positive >= 1 && negative >= 1)
        ? { ok: true, detail: `${ses[0].name}: ${negative} âm + ${positive} dương SLE` }
        : { ok: false, detail: `pos=${positive}, neg=${negative}` }
    },
  },
]
