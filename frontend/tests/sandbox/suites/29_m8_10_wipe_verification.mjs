// Suite 29: Verify wipe M8/M9/M10 — transactional rỗng, master nguyên vẹn
import { apiCall, navigateTo } from '../helpers.mjs'

const EXPECTED_EMPTY_8_10 = [
  // M8
  'SC Purchase Invoice', 'SC Payment Entry', 'SC GL Entry',
  // M9
  'SC Stock Reconciliation', 'SC Inventory Count Sheet',
  // M10
  'SC Recall Notice', 'SC Investigation Report',
]

const EXPECTED_MASTER = {
  'SC Item': 12, 'SC Supplier': 12, 'SC Warehouse': 15,
  'SC UOM': 18, 'SC Department': 33, 'SC Item Group': 23,
}

const ALSO_STILL_EMPTY = [
  // Wipe trước (M1/M2/M3/M6 + PR/PO/SE/Batch/SLE)
  // M7 Dispensing đã bỏ khỏi backend (GĐ1) — không còn doctype để check.
  'SC Purchase Receipt', 'SC Purchase Order', 'SC Stock Entry',
  'SC Stock Ledger Entry', 'SC Batch',
  'Framework Contract', 'SC Material Request', 'SC Quality Inspection',
  'SC Transfer Request',
]

const PAGES = [
  { dt: 'SC Purchase Invoice',     path: '/list/SC%20Purchase%20Invoice' },
  { dt: 'SC Payment Entry',        path: '/list/SC%20Payment%20Entry' },
  { dt: 'SC Stock Reconciliation', path: '/list/SC%20Stock%20Reconciliation' },
  { dt: 'SC Recall Notice',        path: '/list/SC%20Recall%20Notice' },
]

export const tests = [
  ...EXPECTED_EMPTY_8_10.map(dt => ({
    name: `${dt} = 0 record (M8-10)`,
    run: async ({ page }) => {
      const n = await apiCall(page, 'frappe.client.get_count', { doctype: dt })
      return n === 0
        ? { ok: true, detail: `count=0` }
        : { ok: false, detail: `count=${n}` }
    },
  })),

  ...Object.entries(EXPECTED_MASTER).map(([dt, expected]) => ({
    name: `${dt} = ${expected} (master nguyên vẹn)`,
    run: async ({ page }) => {
      const n = await apiCall(page, 'frappe.client.get_count', { doctype: dt })
      return n === expected
        ? { ok: true, detail: `count=${n}` }
        : { ok: false, detail: `count=${n} ≠ ${expected}` }
    },
  })),

  ...PAGES.map(({ dt, path }) => ({
    name: `Trang /list/${dt} hiển thị rỗng`,
    run: async ({ page, BASE, OUT, name }) => {
      await navigateTo(page, BASE, path)
      await page.waitForTimeout(1300)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      const rows = await page.locator('table tbody tr').count()
      return rows === 0
        ? { ok: true, detail: '0 rows' }
        : { ok: false, detail: `Còn ${rows} rows` }
    },
  })),

  {
    name: 'Các module wipe trước vẫn rỗng (regression check)',
    run: async ({ page }) => {
      const counts = {}
      for (const dt of ALSO_STILL_EMPTY) {
        counts[dt] = await apiCall(page, 'frappe.client.get_count', { doctype: dt })
      }
      const total = Object.values(counts).reduce((a, b) => a + b, 0)
      return total === 0
        ? { ok: true, detail: `${ALSO_STILL_EMPTY.length} doctype = 0` }
        : { ok: false, detail: JSON.stringify(counts) }
    },
  },
]
