// Suite 23: TR Approved → action "Tạo phiếu chuyển kho" → SE auto-fetch data
import { apiCall, apiGetList, navigateTo } from '../helpers.mjs'

async function findItemWithStock(page) {
  // Lấy SLE positive aggregate cho (item, warehouse)
  const rows = await apiCall(page, 'supplycore.api.frontend.list_docs', {
    doctype: 'SC Stock Ledger Entry',
    fields: ['item', 'warehouse', 'qty_change'],
    filters: { is_cancelled: 0 },
    limit: 200,
    order_by: 'modified desc',
  })
  const tally = {}
  for (const r of rows || []) {
    const k = `${r.item}::${r.warehouse}`
    tally[k] = (tally[k] || 0) + Number(r.qty_change || 0)
  }
  const positive = Object.entries(tally)
    .filter(([_, q]) => q > 0)
    .sort((a, b) => b[1] - a[1])
  if (!positive.length) return null
  const [k, qty] = positive[0]
  const [item, warehouse] = k.split('::')
  return { item, warehouse, available: qty }
}

async function findOtherWarehouse(page, exclude) {
  const rows = await apiGetList(page, 'SC Warehouse', {
    fields: ['name'],
    filters: { is_group: 0, disabled: 0 },
    limit: 10,
  })
  return (rows || []).find(w => w.name !== exclude)?.name
}

export const tests = [
  {
    name: 'Setup: tìm item + kho có stock thực + kho đích',
    run: async ({ page }) => {
      const src = await findItemWithStock(page)
      if (!src) return { ok: false, detail: 'Không tìm thấy (item, warehouse) có stock > 0' }
      const dst = await findOtherWarehouse(page, src.warehouse)
      if (!dst) return { ok: false, detail: 'Không tìm thấy kho đích khác' }
      page._ctx = { ...src, dst }
      return { ok: true, detail: `item=${src.item}, from=${src.warehouse} (${src.available}), to=${dst}` }
    },
  },

  {
    name: 'Tạo + Submit TR qua API → status=Approved',
    run: async ({ page }) => {
      const { item, warehouse: from, dst: to, available } = page._ctx
      const itemDoc = await apiCall(page, 'frappe.client.get_value',
        { doctype: 'SC Item', filters: { name: item }, fieldname: 'uom' })
      const uom = itemDoc?.uom || 'Cái'
      const today = new Date().toISOString().slice(0, 10)
      const qty = Math.min(1, available)

      const created = await apiCall(page, 'frappe.client.insert', {
        doc: {
          doctype: 'SC Transfer Request',
          request_date: today,
          required_by: today,
          transfer_type: 'Routine',
          from_warehouse: from,
          to_warehouse: to,
          items: [{ doctype: 'SC Transfer Request Item', item, uom, requested_qty: qty, approved_qty: qty }],
        },
      })
      page._trName = created.name

      // Submit qua wrapper backend (tránh TimestampMismatchError)
      await apiCall(page, 'supplycore.api.frontend.submit_doc', {
        doctype: 'SC Transfer Request', name: created.name,
      })
      const after = await apiCall(page, 'frappe.client.get_value', {
        doctype: 'SC Transfer Request',
        filters: { name: created.name },
        fieldname: ['docstatus', 'status'],
      })
      return after?.docstatus === 1 && after?.status === 'Approved'
        ? { ok: true, detail: `TR=${created.name}, docstatus=1, status=${after.status}` }
        : { ok: false, detail: `docstatus=${after?.docstatus}, status=${after?.status}` }
    },
  },

  {
    name: 'SPA mở TR → action "Tạo phiếu chuyển kho" visible',
    run: async ({ page, BASE, OUT, name }) => {
      await navigateTo(page, BASE, `/doc/SC%20Transfer%20Request/${encodeURIComponent(page._trName)}`)
      await page.waitForTimeout(1500)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      const btn = await page.locator('button:has-text("Tạo phiếu chuyển kho")').count()
      return btn >= 1
        ? { ok: true, detail: 'Action button hiện' }
        : { ok: false, detail: 'Không thấy nút "Tạo phiếu chuyển kho"' }
    },
  },

  {
    name: 'Click action → SE được tạo + navigate sang trang SE',
    run: async ({ page, OUT, name }) => {
      await page.locator('button:has-text("Tạo phiếu chuyển kho")').first().click()
      await page.waitForTimeout(3000)
      const url = page.url()
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      const onSE = /\/doc\/SC%20Stock%20Entry\/SC-SE-/.test(url) ||
                   /\/doc\/SC Stock Entry\/SC-SE-/.test(url)
      if (onSE) {
        page._seName = decodeURIComponent(url.split('/').pop())
        return { ok: true, detail: `Đã sang SE=${page._seName}` }
      }
      return { ok: false, detail: `URL=${url}` }
    },
  },

  {
    name: 'SE auto-fetch: entry_type=Material Transfer, from/to/items đúng từ TR',
    run: async ({ page }) => {
      const se = await apiCall(page, 'frappe.client.get', {
        doctype: 'SC Stock Entry', name: page._seName,
      })
      const tr = page._ctx
      const item0 = se?.items?.[0]
      const checks = {
        entry_type: se?.entry_type === 'Material Transfer',
        from_warehouse: se?.from_warehouse === tr.warehouse,
        to_warehouse: se?.to_warehouse === tr.dst,
        transfer_request: se?.transfer_request === page._trName,
        item_count: (se?.items || []).length >= 1,
        item_match: item0?.item === tr.item,
        qty_positive: Number(item0?.qty || 0) > 0,
      }
      const failed = Object.entries(checks).filter(([_, v]) => !v).map(([k]) => k)
      return failed.length === 0
        ? { ok: true, detail: `Đầy đủ: entry_type, from, to, transfer_request, items[0]=${item0.item} qty=${item0.qty}` }
        : { ok: false, detail: `Sai: ${failed.join(', ')}; SE=${JSON.stringify({entry_type:se?.entry_type, from:se?.from_warehouse, to:se?.to_warehouse, tr:se?.transfer_request}).slice(0,200)}` }
    },
  },

  {
    name: 'TR sau khi tạo SE: status=In Transit, stock_entry trỏ về SE',
    run: async ({ page }) => {
      const tr = await apiCall(page, 'frappe.client.get_value', {
        doctype: 'SC Transfer Request',
        filters: { name: page._trName },
        fieldname: ['status', 'stock_entry'],
      })
      return tr?.status === 'In Transit' && tr?.stock_entry === page._seName
        ? { ok: true, detail: `status=${tr.status}, stock_entry=${tr.stock_entry}` }
        : { ok: false, detail: `status=${tr?.status}, stock_entry=${tr?.stock_entry}` }
    },
  },
]
