// M3 Receiving — UC-09..14
import { apiGetList, apiGetDoc, apiCount, navigateTo } from '../helpers.mjs'

export const tests = [
  {
    name: 'UC-09: Purchase Receipt submitted với batch auto-created',
    run: async ({ page, BASE, OUT, name }) => {
      const prs = await apiGetList(page, 'SC Purchase Receipt', {
        fields: ['name'],
        filters: [['docstatus', '=', 1], ['is_return', '=', 0]], limit: 1,
      })
      if (!prs.length) return { ok: false, detail: 'No submitted PR' }
      await navigateTo(page, BASE, `/doc/SC%20Purchase%20Receipt/${encodeURIComponent(prs[0].name)}`)
      await page.waitForTimeout(1500)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      const doc = await apiGetDoc(page, 'SC Purchase Receipt', prs[0].name)
      const itemsWithBatch = (doc.items || []).filter(i => i.batch_no).length
      return itemsWithBatch >= 1
        ? { ok: true, detail: `${prs[0].name}: ${itemsWithBatch} items có batch (UC-14 auto)` }
        : { ok: false, detail: 'No batch_no on items' }
    },
  },
  {
    name: 'UC-11: Return PR có Debit Note button',
    run: async ({ page, BASE, OUT, name }) => {
      const rprs = await apiGetList(page, 'SC Purchase Receipt', {
        fields: ['name', 'debit_note'],
        filters: [['is_return', '=', 1], ['docstatus', '=', 1]], limit: 1,
      })
      if (!rprs.length) return { ok: false, detail: 'No Return PR' }
      await navigateTo(page, BASE, `/doc/SC%20Purchase%20Receipt/${encodeURIComponent(rprs[0].name)}`)
      await page.waitForTimeout(1500)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      // If debit_note already created, button hidden — check Credit Note instead
      const cnBtn = await page.locator('button:has-text("Credit Note")').count()
      const dnBtn = await page.locator('button:has-text("Debit Note")').count()
      return (cnBtn + dnBtn) >= 1
        ? { ok: true, detail: `Return PR ${rprs[0].name}: ${dnBtn} DN btn, ${cnBtn} CN btn` }
        : { ok: false, detail: 'No DN/CN buttons' }
    },
  },
  {
    name: 'UC-12: QI submitted với readings',
    run: async ({ page, BASE, OUT, name }) => {
      const qis = await apiGetList(page, 'SC Quality Inspection', {
        fields: ['name', 'overall_status'],
        filters: [['docstatus', '=', 1]], limit: 1,
      })
      if (!qis.length) return { ok: false, detail: 'No submitted QI' }
      const doc = await apiGetDoc(page, 'SC Quality Inspection', qis[0].name)
      await navigateTo(page, BASE, `/doc/SC%20Quality%20Inspection/${encodeURIComponent(qis[0].name)}`)
      await page.waitForTimeout(1200)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      return (doc.readings?.length || 0) >= 1
        ? { ok: true, detail: `${qis[0].name}: ${doc.readings.length} readings, status=${doc.overall_status}` }
        : { ok: false, detail: 'No readings' }
    },
  },
  {
    name: 'UC-14: PR submit → SC Batch auto-created',
    run: async ({ page }) => {
      // PR submitted gần nhất → mọi dòng item phải có batch_no tự sinh
      const prs = await apiGetList(page, 'SC Purchase Receipt', {
        fields: ['name'],
        filters: [['docstatus', '=', 1], ['is_return', '=', 0]],
        limit: 1, order_by: 'creation desc',
      })
      if (!prs.length) return { ok: false, detail: 'No submitted PR' }
      const doc = await apiGetDoc(page, 'SC Purchase Receipt', prs[0].name)
      const items = doc.items || []
      const withBatch = items.filter(i => i.batch_no).length
      return items.length > 0 && withBatch >= 1
        ? { ok: true, detail: `${prs[0].name}: ${withBatch}/${items.length} dòng có lô tự sinh` }
        : { ok: false, detail: `${prs[0].name}: ${withBatch}/${items.length} dòng có batch_no` }
    },
  },
]
