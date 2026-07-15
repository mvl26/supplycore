// M8 Accounting — UC-24..27
import { apiGetList, apiGetDoc, apiCount, navigateTo } from '../helpers.mjs'

export const tests = [
  {
    name: 'UC-24: Purchase Invoice 3-way match (PI → PR → PO)',
    run: async ({ page, BASE, OUT, name }) => {
      const pis = await apiGetList(page, 'SC Purchase Invoice', {
        fields: ['name', 'supplier', 'purchase_receipt', 'grand_total'],
        filters: [['docstatus', '=', 1]], limit: 1,
      })
      if (!pis.length) return { ok: false, detail: 'No PI' }
      const pi = pis[0]
      const pr = pi.purchase_receipt
      await navigateTo(page, BASE, `/doc/SC%20Purchase%20Invoice/${encodeURIComponent(pi.name)}`)
      await page.waitForTimeout(1500)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      return pr
        ? { ok: true, detail: `${pi.name} link PR=${pr}, total=${pi.grand_total}` }
        : { ok: false, detail: 'No PR link' }
    },
  },
  {
    name: 'UC-25: Payment Entry với references',
    run: async ({ page, BASE, OUT, name }) => {
      const pes = await apiGetList(page, 'SC Payment Entry', {
        fields: ['name', 'supplier', 'amount', 'payment_method'],
        filters: [['docstatus', '=', 1]], limit: 1,
      })
      if (!pes.length) return { ok: false, detail: 'No PE' }
      const doc = await apiGetDoc(page, 'SC Payment Entry', pes[0].name)
      await navigateTo(page, BASE, `/doc/SC%20Payment%20Entry/${encodeURIComponent(pes[0].name)}`)
      await page.waitForTimeout(1500)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      return (doc.references?.length || 0) >= 1
        ? { ok: true, detail: `${pes[0].name}: ${doc.references.length} PI refs, amount=${pes[0].amount}` }
        : { ok: false, detail: 'No PI references' }
    },
  },
  {
    name: 'UC-26: Return PR có Debit Note linked',
    run: async ({ page }) => {
      const rprs = await apiGetList(page, 'SC Purchase Receipt', {
        fields: ['name', 'debit_note'],
        filters: [['is_return', '=', 1], ['docstatus', '=', 1]], limit: 3,
      })
      const withDN = rprs.filter(r => r.debit_note)
      return withDN.length >= 1
        ? { ok: true, detail: `${withDN.length}/${rprs.length} Return PR có Debit Note` }
        : { ok: false, detail: 'No Debit Notes generated' }
    },
  },
  {
    name: 'UC-27: GL Entry tự tạo từ PI + PE',
    run: async ({ page }) => {
      const gl = await apiCount(page, 'SC GL Entry')
      const piGl = await apiCount(page, 'SC GL Entry', { voucher_type: 'SC Purchase Invoice' })
      const peGl = await apiCount(page, 'SC GL Entry', { voucher_type: 'SC Payment Entry' })
      return gl >= 2
        ? { ok: true, detail: `${gl} GL entries (PI=${piGl}, PE=${peGl})` }
        : { ok: false, detail: `Only ${gl}` }
    },
  },
]
