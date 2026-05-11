// M7 Dispensing — UC-19, UC-22, UC-23
import { apiGetList, apiGetDoc, navigateTo } from '../helpers.mjs'

export const tests = [
  {
    name: 'UC-19: Dispensing Request submitted',
    run: async ({ page, BASE, OUT, name }) => {
      const drs = await apiGetList(page, 'SC Dispensing Request', {
        fields: ['name', 'department', 'from_warehouse', 'status'],
        filters: [['docstatus', '=', 1]], limit: 1,
      })
      if (!drs.length) return { ok: false, detail: 'No DR' }
      await navigateTo(page, BASE, `/doc/SC%20Dispensing%20Request/${encodeURIComponent(drs[0].name)}`)
      await page.waitForTimeout(1500)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      return { ok: true, detail: `${drs[0].name}: dept=${drs[0].department}, status=${drs[0].status}` }
    },
  },
  {
    name: 'UC-22: PD có BHYT calc (patient_pays < total_cost)',
    run: async ({ page }) => {
      const pds = await apiGetList(page, 'SC Patient Dispensing', {
        fields: ['name', 'patient', 'bhyt_card_no', 'patient_pays', 'total_cost'],
        filters: [['docstatus', '=', 1]], limit: 5,
      })
      // patient có BHYT → bhyt_payment_rate > 0 → patient_pays < total_cost
      const withBhyt = pds.filter(p => p.bhyt_card_no && p.patient_pays < p.total_cost)
      return withBhyt.length >= 1
        ? { ok: true, detail: `${withBhyt.length}/${pds.length} PDs có BHYT calc (pays < total)` }
        : { ok: false, detail: `${pds.length} PDs but no BHYT discount` }
    },
  },
  {
    name: 'UC-23: PD không có BHYT → patient_pays = total_cost',
    run: async ({ page, BASE, OUT, name }) => {
      const pds = await apiGetList(page, 'SC Patient Dispensing', {
        fields: ['name', 'bhyt_card_no', 'patient_pays', 'total_cost'],
        filters: [['docstatus', '=', 1]], limit: 10,
      })
      const noBhyt = pds.filter(p => !p.bhyt_card_no)
      if (!noBhyt.length) return { ok: true, detail: 'No no-BHYT PDs (skipped)' }
      const correct = noBhyt.filter(p =>
        Math.abs((p.patient_pays || 0) - (p.total_cost || 0)) < 1).length
      return correct >= 1
        ? { ok: true, detail: `${correct} no-BHYT PD: pays=total (100% tự trả)` }
        : { ok: false, detail: `${noBhyt.length} no-BHYT but pays!=total` }
    },
  },
  {
    name: 'UC-22: PD có items child table',
    run: async ({ page }) => {
      const pds = await apiGetList(page, 'SC Patient Dispensing', {
        fields: ['name'], filters: [['docstatus', '=', 1]], limit: 1,
      })
      if (!pds.length) return { ok: false, detail: 'No PD' }
      const doc = await apiGetDoc(page, 'SC Patient Dispensing', pds[0].name)
      return (doc.items?.length || 0) >= 1
        ? { ok: true, detail: `${pds[0].name}: ${doc.items.length} items` }
        : { ok: false, detail: 'No PD items' }
    },
  },
]
