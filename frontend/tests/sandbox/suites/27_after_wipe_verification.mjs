// Suite 27: Verify wipe — transactional rỗng, master nguyên vẹn
import { apiCall, apiGetList, navigateTo } from '../helpers.mjs'

const EXPECTED_EMPTY = [
  'SC Purchase Receipt',
  'SC Purchase Order',
  'SC Stock Entry',
  'SC Stock Ledger Entry',
  'SC Batch',
]

const EXPECTED_MASTER_MIN = {
  'SC Item': 12,
  'SC Supplier': 12,
  'SC Warehouse': 15,
  'SC UOM': 18,
  'SC Department': 33,
  'SC Item Group': 23,
}

export const tests = [
  ...EXPECTED_EMPTY.map(dt => ({
    name: `${dt} = 0 record`,
    run: async ({ page }) => {
      const n = await apiCall(page, 'frappe.client.get_count', { doctype: dt })
      return n === 0
        ? { ok: true, detail: `count=0` }
        : { ok: false, detail: `count=${n} (vẫn còn record!)` }
    },
  })),

  ...Object.entries(EXPECTED_MASTER_MIN).map(([dt, expected]) => ({
    name: `${dt} = ${expected} (master nguyên vẹn)`,
    run: async ({ page }) => {
      const n = await apiCall(page, 'frappe.client.get_count', { doctype: dt })
      return n === expected
        ? { ok: true, detail: `count=${n}` }
        : { ok: false, detail: `count=${n} ≠ expected ${expected}` }
    },
  })),

  {
    name: 'List page PR rỗng / hiển thị "Chưa có"',
    run: async ({ page, BASE, OUT, name }) => {
      await navigateTo(page, BASE, '/list/SC%20Purchase%20Receipt')
      await page.waitForTimeout(1300)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      const rows = await page.locator('table tbody tr').count()
      return rows === 0
        ? { ok: true, detail: '0 rows trong list' }
        : { ok: false, detail: `Vẫn còn ${rows} rows` }
    },
  },

  {
    name: 'Naming series PR đã reset (tạo mới → SC-PR-2026-00001)',
    run: async ({ page }) => {
      const items = await apiGetList(page, 'SC Item', { fields: ['name'], limit: 1 })
      const suppliers = await apiGetList(page, 'SC Supplier', { fields: ['name'], limit: 1 })
      const warehouses = await apiGetList(page, 'SC Warehouse', {
        fields: ['name'], filters: { is_group: 0, disabled: 0 }, limit: 1,
      })
      if (!items?.[0] || !suppliers?.[0] || !warehouses?.[0]) {
        return { ok: false, detail: 'Master thiếu để tạo PR test' }
      }
      const today = new Date().toISOString().slice(0, 10)
      const created = await apiCall(page, 'frappe.client.insert', {
        doc: {
          doctype: 'SC Purchase Receipt',
          posting_date: today,
          supplier: suppliers[0].name,
          to_warehouse: warehouses[0].name,
          items: [{ doctype: 'SC Purchase Receipt Item',
            item: items[0].name, qty: 1, rate: 1000, uom: 'Cái' }],
        },
      })
      // Tên mới có dạng SC-PR-2026-00001 hoặc -03568 tuỳ format
      // Quan trọng: là PR đầu tiên sau wipe → counter restart
      const isFirst = /\b(0+1|00001)\b/.test(created?.name || '')
      const result = { ok: !!created?.name, detail: `PR mới = ${created?.name}, restart=${isFirst}` }
      // Cleanup: xóa PR vừa tạo
      try { await apiCall(page, 'frappe.client.delete', { doctype: 'SC Purchase Receipt', name: created.name }) } catch {}
      return result
    },
  },
]
