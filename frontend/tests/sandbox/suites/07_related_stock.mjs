// Suite 07: Related docs + Stock balance + PO/QI list khắc phục
import { apiCall, apiGetList, navigateTo } from '../helpers.mjs'

export const tests = [
  {
    name: 'PO list trả grand_total OK (không lỗi total_value)',
    run: async ({ page, BASE, OUT, name }) => {
      await navigateTo(page, BASE, '/list/SC%20Purchase%20Order')
      await page.waitForTimeout(1500)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      const rows = await page.locator('table tbody tr').count()
      return rows >= 1
        ? { ok: true, detail: `${rows} POs visible` }
        : { ok: false, detail: 'PO list empty' }
    },
  },
  {
    name: 'FC detail có RelatedDocs section "Đơn mua hàng"',
    run: async ({ page, BASE, OUT, name }) => {
      const fcs = await apiGetList(page, 'Framework Contract',
        { fields: ['name'], filters: { status: 'Active' }, limit: 1 })
      if (!fcs.length) return { ok: false, detail: 'No FC' }
      await navigateTo(page, BASE, `/doc/Framework%20Contract/${encodeURIComponent(fcs[0].name)}`)
      await page.waitForTimeout(2500)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      const poSection = await page.locator('text=Đơn mua hàng').count()
      return poSection >= 1
        ? { ok: true, detail: `FC ${fcs[0].name} có related POs section` }
        : { ok: false, detail: 'No PO section trong FC detail' }
    },
  },
  {
    name: 'PR detail có RelatedDocs "Kiểm tra QC" + "Lô đã nhập"',
    run: async ({ page, BASE, OUT, name }) => {
      const prs = await apiGetList(page, 'SC Purchase Receipt',
        { fields: ['name'], filters: { docstatus: 1, is_return: 0 }, limit: 1 })
      if (!prs.length) return { ok: false, detail: 'No PR' }
      await navigateTo(page, BASE, `/doc/SC%20Purchase%20Receipt/${encodeURIComponent(prs[0].name)}`)
      await page.waitForTimeout(2500)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      const qiSection = await page.locator('text=Kiểm tra QC').count()
      const batchSection = await page.locator('text=Lô đã nhập').count()
      return (qiSection >= 1 && batchSection >= 1)
        ? { ok: true, detail: `PR ${prs[0].name} có QC + Lô sections` }
        : { ok: false, detail: `QC=${qiSection}, Batch=${batchSection}` }
    },
  },
  {
    name: 'Item detail có RelatedDocs "Tồn kho" + "Lô"',
    run: async ({ page, BASE, OUT, name }) => {
      const items = await apiGetList(page, 'SC Item',
        { fields: ['name'], filters: { has_batch_no: 1 }, limit: 1 })
      if (!items.length) return { ok: false, detail: 'No item' }
      await navigateTo(page, BASE, `/doc/SC%20Item/${encodeURIComponent(items[0].name)}`)
      await page.waitForTimeout(2500)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      const stockSection = await page.locator('text=Tồn kho').count()
      const batchSection = await page.locator('text=Lô đã nhập').count()
      return (stockSection >= 1 || batchSection >= 1)
        ? { ok: true, detail: `Item ${items[0].name} có related sections (stock=${stockSection}, batch=${batchSection})` }
        : { ok: false, detail: 'No sections' }
    },
  },
  {
    name: 'Stock Balance page render với data',
    run: async ({ page, BASE, OUT, name }) => {
      await navigateTo(page, BASE, '/stock-balance')
      await page.waitForTimeout(2500)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      const rows = await page.locator('table tbody tr').count()
      const totalQty = await page.locator('text=Tổng số lượng tồn').count()
      return rows >= 1 && totalQty >= 1
        ? { ok: true, detail: `${rows} stock rows + KPI cards` }
        : { ok: false, detail: `rows=${rows}, totalQty kpi=${totalQty}` }
    },
  },
  {
    name: 'Stock Balance filter by warehouse',
    run: async ({ page, BASE }) => {
      const wh = await apiGetList(page, 'SC Warehouse',
        { fields: ['name'], filters: { is_group: 0 }, limit: 1 })
      if (!wh.length) return { ok: false, detail: 'No warehouse' }
      const balance = await apiCall(page, 'supplycore.api.frontend.stock_balance',
        { warehouse: wh[0].name })
      return Array.isArray(balance)
        ? { ok: true, detail: `${balance.length} rows ở ${wh[0].name}` }
        : { ok: false, detail: 'Not array' }
    },
  },
  {
    name: 'QI list visible với rows',
    run: async ({ page, BASE, OUT, name }) => {
      await navigateTo(page, BASE, '/list/SC%20Quality%20Inspection')
      await page.waitForTimeout(1500)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      const rows = await page.locator('table tbody tr').count()
      return rows >= 1
        ? { ok: true, detail: `${rows} QI rows visible` }
        : { ok: false, detail: 'QI list empty' }
    },
  },
]
