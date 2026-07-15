// M2 Planning — UC-05, UC-07, UC-08
import { apiGetList, apiCount, navigateTo, pickByField, apiCall } from '../helpers.mjs'

export const tests = [
  {
    name: 'UC-05: Items có safety_stock được set',
    run: async ({ page }) => {
      const items = await apiGetList(page, 'SC Item', {
        fields: ['name', 'safety_stock', 'reorder_level'],
        filters: [['safety_stock', '>', 0]], limit: 10,
      })
      return items.length >= 5
        ? { ok: true, detail: `${items.length} items có safety_stock > 0` }
        : { ok: false, detail: `Only ${items.length}` }
    },
  },
  {
    name: 'UC-05: scan_alerts tạo low_stock alerts',
    run: async ({ page }) => {
      const alerts = await apiGetList(page, 'SC Alert', {
        fields: ['name', 'title'],
        filters: [['alert_type', '=', 'low_stock']],
        limit: 5,
      })
      return alerts.length >= 1
        ? { ok: true, detail: `${alerts.length} low_stock alerts đã tạo` }
        : { ok: false, detail: 'No low_stock alerts' }
    },
  },
  {
    name: 'UC-07: List Material Request có rows',
    run: async ({ page, BASE, OUT, name }) => {
      await navigateTo(page, BASE, '/list/SC%20Material%20Request')
      await page.waitForTimeout(1200)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      const rows = await page.locator('table tbody tr').count()
      return rows >= 1
        ? { ok: true, detail: `${rows} MR records` }
        : { ok: false, detail: 'Empty' }
    },
  },
  {
    name: 'UC-07: MR có items child table',
    run: async ({ page }) => {
      // Fetch via parent doc — Frappe child table chỉ trả qua get_doc
      const mrs = await apiGetList(page, 'SC Material Request', {
        fields: ['name'], filters: [['docstatus', '=', 1]], limit: 1,
      })
      if (!mrs.length) return { ok: false, detail: 'No submitted MR' }
      const doc = await page.evaluate(async (name) => {
        const r = await fetch(`/api/resource/SC%20Material%20Request/${encodeURIComponent(name)}`,
          { credentials: 'include' })
        return (await r.json()).data
      }, mrs[0].name)
      return (doc.items?.length || 0) >= 1
        ? { ok: true, detail: `${mrs[0].name}: ${doc.items.length} items` }
        : { ok: false, detail: 'No items in doc' }
    },
  },
  {
    name: 'UC-08: PO submitted với approval_stage=Approved',
    run: async ({ page, BASE, OUT, name }) => {
      const pos = await apiGetList(page, 'SC Purchase Order', {
        fields: ['name', 'approval_stage', 'status', 'docstatus'],
        filters: [['docstatus', '=', 1]], limit: 3,
      })
      if (!pos.length) return { ok: false, detail: 'No submitted POs' }
      const allApproved = pos.every(p => p.approval_stage === 'Approved')
      await navigateTo(page, BASE, `/doc/SC%20Purchase%20Order/${encodeURIComponent(pos[0].name)}`)
      await page.waitForTimeout(1500)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      return allApproved
        ? { ok: true, detail: `${pos.length} POs Approved (${pos[0].name})` }
        : { ok: false, detail: `Found non-Approved: ${JSON.stringify(pos)}` }
    },
  },
  {
    name: 'UC-08: PO ActionPanel hiển thị send_to_supplier khi Approved',
    run: async ({ page, BASE, OUT, name }) => {
      const pos = await apiGetList(page, 'SC Purchase Order', {
        fields: ['name'],
        filters: [['docstatus', '=', 1], ['status', '=', 'Approved']], limit: 1,
      })
      if (!pos.length) return { ok: true, detail: 'No Approved PO (skipped)' }
      await navigateTo(page, BASE, `/doc/SC%20Purchase%20Order/${encodeURIComponent(pos[0].name)}`)
      await page.waitForTimeout(1500)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      const sendBtn = await page.locator('button:has-text("Gửi NCC")').count()
      return sendBtn >= 1
        ? { ok: true, detail: 'send_to_supplier visible' }
        : { ok: false, detail: 'No send button' }
    },
  },
]
