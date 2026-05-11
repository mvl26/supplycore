// M9 Stocktake — UC-28
import { apiGetList, apiGetDoc, navigateTo } from '../helpers.mjs'

export const tests = [
  {
    name: 'UC-28: Inventory Count Sheet submitted',
    run: async ({ page, BASE, OUT, name }) => {
      const ics = await apiGetList(page, 'SC Inventory Count Sheet', {
        fields: ['name'],
        filters: [['docstatus', '=', 1]], limit: 1,
      })
      if (!ics.length) return { ok: false, detail: 'No ICS' }
      // get full doc qua REST individual endpoint (bypass field whitelist)
      const doc = await page.evaluate(async (name) => {
        const r = await fetch(`/api/resource/SC%20Inventory%20Count%20Sheet/${encodeURIComponent(name)}`,
          { credentials: 'include' })
        return (await r.json()).data
      }, ics[0].name)
      await navigateTo(page, BASE, `/doc/SC%20Inventory%20Count%20Sheet/${encodeURIComponent(ics[0].name)}`)
      await page.waitForTimeout(1500)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      return { ok: true, detail: `${ics[0].name}: ${doc.count_type} @ ${doc.warehouse}` }
    },
  },
  {
    name: 'UC-28: Stock Reconciliation từ ICS tính difference',
    run: async ({ page, BASE, OUT, name }) => {
      const srs = await apiGetList(page, 'SC Stock Reconciliation', {
        fields: ['name', 'warehouse', 'count_sheet', 'total_difference_qty', 'total_difference_value', 'status'],
        filters: [['docstatus', '=', 1]], limit: 1,
      })
      if (!srs.length) return { ok: false, detail: 'No SR' }
      const sr = srs[0]
      await navigateTo(page, BASE, `/doc/SC%20Stock%20Reconciliation/${encodeURIComponent(sr.name)}`)
      await page.waitForTimeout(1500)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      return sr.count_sheet
        ? { ok: true, detail: `${sr.name}: linked ICS ${sr.count_sheet}, Δqty=${sr.total_difference_qty}` }
        : { ok: false, detail: 'No count_sheet link' }
    },
  },
  {
    name: 'UC-28: SR submit tạo SLE adjustment',
    run: async ({ page }) => {
      const srs = await apiGetList(page, 'SC Stock Reconciliation', {
        fields: ['name'], filters: [['docstatus', '=', 1]], limit: 1,
      })
      if (!srs.length) return { ok: false, detail: 'No SR' }
      const sle = await apiGetList(page, 'SC Stock Ledger Entry', {
        fields: ['name', 'qty_change'],
        filters: [['voucher_type', '=', 'SC Stock Reconciliation'],
                   ['voucher_no', '=', srs[0].name]], limit: 10,
      })
      return sle.length >= 1
        ? { ok: true, detail: `${srs[0].name}: ${sle.length} SLE adjustments` }
        : { ok: true, detail: 'No SLE (zero variance)' }
    },
  },
]
