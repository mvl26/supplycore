// Suite 28: Verify wipe M1/M2/M3/M6/M7 — transactional rỗng, master nguyên vẹn
import { apiCall, navigateTo } from '../helpers.mjs'

const EXPECTED_EMPTY = [
  'Framework Contract',
  'SC Material Request',
  'SC Quality Inspection',
  'SC Transfer Request',
  'SC Patient Dispensing',
  'SC Dispensing Request',
]

const EXPECTED_MASTER = {
  'SC Item': 12,
  'SC Supplier': 12,
  'SC Warehouse': 15,
  'SC Patient': 13,
  'SC UOM': 18,
  'SC Department': 33,
  'SC Item Group': 23,
}

const PAGE_TITLES_TO_CHECK = [
  { dt: 'Framework Contract', path: '/list/Framework%20Contract' },
  { dt: 'SC Material Request', path: '/list/SC%20Material%20Request' },
  { dt: 'SC Quality Inspection', path: '/list/SC%20Quality%20Inspection' },
  { dt: 'SC Transfer Request', path: '/list/SC%20Transfer%20Request' },
  { dt: 'SC Patient Dispensing', path: '/list/SC%20Patient%20Dispensing' },
]

export const tests = [
  ...EXPECTED_EMPTY.map(dt => ({
    name: `${dt} = 0 record`,
    run: async ({ page }) => {
      const n = await apiCall(page, 'frappe.client.get_count', { doctype: dt })
      return n === 0
        ? { ok: true, detail: `count=0` }
        : { ok: false, detail: `count=${n} (vẫn còn!)` }
    },
  })),

  ...Object.entries(EXPECTED_MASTER).map(([dt, expected]) => ({
    name: `${dt} = ${expected} (master nguyên vẹn)`,
    run: async ({ page }) => {
      const n = await apiCall(page, 'frappe.client.get_count', { doctype: dt })
      return n === expected
        ? { ok: true, detail: `count=${n}` }
        : { ok: false, detail: `count=${n} ≠ expected ${expected}` }
    },
  })),

  ...PAGE_TITLES_TO_CHECK.map(({ dt, path }) => ({
    name: `Trang /list/${dt} hiển thị rỗng`,
    run: async ({ page, BASE, OUT, name }) => {
      await navigateTo(page, BASE, path)
      await page.waitForTimeout(1200)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      const rows = await page.locator('table tbody tr').count()
      return rows === 0
        ? { ok: true, detail: '0 rows' }
        : { ok: false, detail: `Còn ${rows} rows` }
    },
  })),

  {
    name: 'PR/PO/SE/Batch/SLE (wipe trước) cũng rỗng',
    run: async ({ page }) => {
      const dts = ['SC Purchase Receipt', 'SC Purchase Order', 'SC Stock Entry',
                   'SC Stock Ledger Entry', 'SC Batch']
      const counts = {}
      for (const dt of dts) {
        counts[dt] = await apiCall(page, 'frappe.client.get_count', { doctype: dt })
      }
      const total = Object.values(counts).reduce((a, b) => a + b, 0)
      return total === 0
        ? { ok: true, detail: `Tổng = 0 (${JSON.stringify(counts).slice(1, -1)})` }
        : { ok: false, detail: `Tổng = ${total}: ${JSON.stringify(counts)}` }
    },
  },
]
