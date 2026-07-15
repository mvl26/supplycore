// Suite 10: FEFO pick guide + Putaway + Warehouse stock panel
import { apiCall, apiGetList, navigateTo } from '../helpers.mjs'

export const tests = [
  {
    name: 'API fefo_pick_guide trả picks sorted by HD',
    run: async ({ page }) => {
      // Pick item có nhiều batch
      const items = await apiGetList(page, 'SC Item',
        { fields: ['name'], filters: { has_batch_no: 1 }, limit: 1 })
      const whs = await apiGetList(page, 'SC Warehouse',
        { fields: ['name'], filters: { is_group: 0, disabled: 0 }, limit: 1 })
      if (!items.length || !whs.length) return { ok: false, detail: 'No data' }
      const guide = await apiCall(page, 'supplycore.api.frontend.fefo_pick_guide',
        { item: items[0].name, warehouse: whs[0].name, qty_needed: 5 })
      const picks = guide.picks || []
      // Verify sorted by expiry_date ASC
      let sorted = true
      for (let i = 1; i < picks.length; i++) {
        if (picks[i - 1].expiry_date && picks[i].expiry_date) {
          if (picks[i - 1].expiry_date > picks[i].expiry_date) { sorted = false; break }
        }
      }
      return sorted && guide.summary
        ? { ok: true, detail: `${picks.length} picks, sorted by HD: ${guide.summary}` }
        : { ok: false, detail: `picks=${picks.length}, sorted=${sorted}` }
    },
  },
  {
    name: 'API warehouse_stock_for_item trả tồn + safety',
    run: async ({ page }) => {
      const whs = await apiGetList(page, 'SC Warehouse',
        { fields: ['name'], filters: { is_group: 0, disabled: 0 }, limit: 1 })
      if (!whs.length) return { ok: false, detail: 'No warehouse' }
      const rows = await apiCall(page, 'supplycore.api.frontend.warehouse_stock_for_item',
        { warehouse: whs[0].name })
      const valid = rows.every(r => 'qty' in r && 'item' in r && 'safety_stock' in r)
      return rows.length >= 1 && valid
        ? { ok: true, detail: `${rows.length} dòng tồn ở ${whs[0].name}` }
        : { ok: false, detail: `${rows.length}, valid=${valid}` }
    },
  },
  {
    name: 'API check_safety_after_transfer phát hiện dưới safety',
    run: async ({ page }) => {
      const items = await apiGetList(page, 'SC Item',
        { fields: ['name'], filters: { safety_stock: ['>', 0] }, limit: 1 })
      const whs = await apiGetList(page, 'SC Warehouse',
        { fields: ['name'], filters: { is_group: 0, disabled: 0 }, limit: 1 })
      if (!items.length || !whs.length) return { ok: true, detail: 'No data (skip)' }
      // Transfer huge qty → must trigger warning
      const result = await apiCall(page, 'supplycore.api.frontend.check_safety_after_transfer',
        { warehouse: whs[0].name, item: items[0].name, qty: 999999 })
      return result.below_safety === true && result.warning_msg
        ? { ok: true, detail: result.warning_msg }
        : { ok: false, detail: `below=${result.below_safety}, msg=${result.warning_msg}` }
    },
  },
  {
    name: 'API pending_putaway trả SLE chưa có bin',
    run: async ({ page }) => {
      const rows = await apiCall(page, 'supplycore.api.frontend.pending_putaway',
        { limit: 20 })
      return Array.isArray(rows)
        ? { ok: true, detail: `${rows.length} dòng chờ xếp lên kệ` }
        : { ok: false, detail: 'Not array' }
    },
  },
  {
    name: 'Page /putaway render',
    run: async ({ page, BASE, OUT, name }) => {
      await navigateTo(page, BASE, '/putaway')
      await page.waitForTimeout(2500)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      const title = await page.locator('h1').first().textContent()
      return title?.includes('xếp hàng')
        ? { ok: true, detail: `Title="${title}"` }
        : { ok: false, detail: `Title="${title}"` }
    },
  },
  {
    name: 'TR new form có WarehouseStockPanel',
    run: async ({ page, BASE, OUT, name }) => {
      // List TR with from_warehouse set
      const trs = await apiGetList(page, 'SC Transfer Request',
        { fields: ['name'], filters: { docstatus: 1 }, limit: 1 })
      if (!trs.length) return { ok: true, detail: 'No TR (skip)' }
      await navigateTo(page, BASE, `/doc/SC%20Transfer%20Request/${encodeURIComponent(trs[0].name)}`)
      await page.waitForTimeout(2500)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      const stockHeader = await page.locator('text=Tồn kho nguồn').count()
      return stockHeader >= 1
        ? { ok: true, detail: 'WarehouseStockPanel visible' }
        : { ok: false, detail: 'No panel' }
    },
  },
  {
    name: 'Sidebar có link "Xếp hàng lên kệ"',
    run: async ({ page }) => {
      const link = await page.locator('a[href*="/putaway"]').count()
      return link >= 1
        ? { ok: true, detail: 'Putaway link visible' }
        : { ok: false, detail: 'No link' }
    },
  },
  {
    name: 'FEFO guide: lô blocked không xuất hiện trong picks',
    run: async ({ page }) => {
      // pick a known recall batch (blocked=1)
      const blocked = await apiGetList(page, 'SC Batch',
        { fields: ['name', 'item'], filters: { blocked: 1 }, limit: 1 })
      if (!blocked.length) return { ok: true, detail: 'No blocked batch (skip)' }
      const whs = await apiGetList(page, 'SC Warehouse',
        { fields: ['name'], filters: { is_group: 0 }, limit: 1 })
      const guide = await apiCall(page, 'supplycore.api.frontend.fefo_pick_guide',
        { item: blocked[0].item, warehouse: whs[0].name, qty_needed: 100 })
      const hasBlocked = guide.picks?.some(p => p.batch === blocked[0].name)
      return !hasBlocked
        ? { ok: true, detail: `Lô blocked ${blocked[0].name} bị loại khỏi FEFO ✓` }
        : { ok: false, detail: 'Blocked batch xuất hiện!' }
    },
  },
]
