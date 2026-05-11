// M10 Trace + Recall + Investigation — UC-29..31
import { apiGetList, apiGetDoc, apiCall, navigateTo } from '../helpers.mjs'

export const tests = [
  {
    name: 'UC-29: get_batch_trace API trả full lifecycle',
    run: async ({ page }) => {
      const batches = await apiGetList(page, 'SC Batch', {
        fields: ['name'], limit: 1,
      })
      if (!batches.length) return { ok: false, detail: 'No batch' }
      const trace = await apiCall(page, 'supplycore.m10_traceability.api.trace.get_batch_trace',
        { batch_no: batches[0].name })
      const keys = Object.keys(trace || {})
      const expected = ['exists', 'header', 'origin', 'movements', 'current_stock', 'data_quality']
      const missing = expected.filter(k => !keys.includes(k))
      return missing.length === 0
        ? { ok: true, detail: `Trace ${batches[0].name} có ${keys.length} sections` }
        : { ok: false, detail: `Missing: ${missing.join(',')}` }
    },
  },
  {
    name: 'UC-30: Recall Notice submitted block batch',
    run: async ({ page, BASE, OUT, name }) => {
      const rcls = await apiGetList(page, 'SC Recall Notice', {
        fields: ['name', 'batch_no', 'severity', 'status'],
        filters: [['docstatus', '=', 1]], limit: 1,
      })
      if (!rcls.length) return { ok: false, detail: 'No RCL' }
      const batch = await apiGetDoc(page, 'SC Batch', rcls[0].batch_no)
      await navigateTo(page, BASE, `/doc/SC%20Recall%20Notice/${encodeURIComponent(rcls[0].name)}`)
      await page.waitForTimeout(1500)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      return batch.blocked === 1
        ? { ok: true, detail: `${rcls[0].name}: batch ${rcls[0].batch_no} blocked=1` }
        : { ok: false, detail: `Batch blocked=${batch.blocked}` }
    },
  },
  {
    name: 'UC-30: ActionPanel hiển thị actions cho RCL Issued',
    run: async ({ page, BASE, OUT, name }) => {
      const rcls = await apiGetList(page, 'SC Recall Notice', {
        fields: ['name'],
        filters: [['docstatus', '=', 1]], limit: 1,
      })
      if (!rcls.length) return { ok: false, detail: 'No submitted RCL' }
      await navigateTo(page, BASE, `/doc/SC%20Recall%20Notice/${encodeURIComponent(rcls[0].name)}`)
      await page.waitForTimeout(1500)
      const actionBtns = await page.locator('.sc-card').filter({ hasText: 'Hành động khả dụng' })
        .locator('button').count()
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      return actionBtns >= 3
        ? { ok: true, detail: `${actionBtns} action buttons (notify/return/write-off/audit)` }
        : { ok: false, detail: `Only ${actionBtns}` }
    },
  },
  {
    name: 'UC-31: Investigation Report submitted',
    run: async ({ page, BASE, OUT, name }) => {
      const invs = await apiGetList(page, 'SC Investigation Report', {
        fields: ['name', 'investigation_type', 'status', 'theoretical_qty', 'actual_qty', 'variance_qty'],
        filters: [['docstatus', '=', 1]], limit: 1,
      })
      if (!invs.length) return { ok: false, detail: 'No INV' }
      const inv = invs[0]
      await navigateTo(page, BASE, `/doc/SC%20Investigation%20Report/${encodeURIComponent(inv.name)}`)
      await page.waitForTimeout(1500)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      return { ok: true, detail: `${inv.name}: ${inv.investigation_type}, variance=${inv.variance_qty}` }
    },
  },
]
