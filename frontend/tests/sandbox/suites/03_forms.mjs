// Suite 03: Form schema render cho tất cả creatable doctypes

const FORMS = [
  ['SC Item', 3, 4],            // 3 sections, 4+ inputs
  ['SC UOM', 1, 2],
  ['SC Supplier', 2, 5],
  ['SC Warehouse', 2, 4],
  ['SC Department', 1, 4],
  ['SC Patient', 3, 8],
  ['SC BHYT Code Config', 2, 5],
  ['SC GL Account', 1, 4],
  ['Framework Contract', 2, 5],
  ['SC Material Request', 1, 4],
  ['SC Purchase Order', 1, 4],
  ['SC Purchase Receipt', 1, 5],
  ['SC Batch', 2, 5],
  ['SC Transfer Request', 1, 3],
  ['SC Stock Entry', 1, 4],
  ['SC Dispensing Request', 1, 3],
  ['SC Patient Dispensing', 1, 4],
  ['SC Purchase Invoice', 1, 4],
  ['SC Payment Entry', 1, 4],
  ['SC Inventory Count Sheet', 1, 3],
  ['SC Stock Reconciliation', 2, 4],
  ['SC Recall Notice', 2, 7],
  ['SC Investigation Report', 3, 6],
  ['SC Alert Rule', 5, 10],
]

export const tests = FORMS.map(([dt, minSections, minInputs]) => ({
  name: `Form ${dt}`,
  run: async ({ page, BASE, OUT, name }) => {
    await page.goto(`${BASE}/supplycore/doc/${encodeURIComponent(dt)}/new`)
    await page.waitForTimeout(1200)
    const sections = await page.locator('h3').count()
    const inputs = await page.locator('input, select, textarea').count()
    if (inputs < 5) {
      // Only screenshot when something's off
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
    }
    return sections >= minSections && inputs >= minInputs
      ? { ok: true, detail: `${sections} sec, ${inputs} inputs` }
      : { ok: false, detail: `${sections} sec (>=${minSections}?), ${inputs} inputs (>=${minInputs}?)` }
  },
}))
