// Suite 21: QI inline edit + batch create round-trip + bulk accept readings
import { apiCall, apiGetList, navigateTo } from '../helpers.mjs'

const LINK_PENDING_KEY = 'sc-link-create-pending'
const LINK_RESULT_KEY  = 'sc-link-create-result'

async function ensureDraftQI(page) {
  const items = await apiGetList(page, 'SC Item', { fields: ['name'], limit: 1 })
  const prs   = await apiGetList(page, 'SC Purchase Receipt', { fields: ['name', 'supplier'], limit: 1 })
  if (!items?.[0] || !prs?.[0]) throw new Error('Sandbox thiếu SC Item / SC Purchase Receipt để tạo draft QI')

  // Ưu tiên draft có sẵn ĐÃ điền item + PR (cần cho test prefill)
  const drafts = await apiGetList(page, 'SC Quality Inspection', {
    fields: ['name', 'item', 'purchase_receipt'],
    filters: { docstatus: 0 },
    limit: 20,
  })
  const usable = (drafts || []).find(d => d.item && d.purchase_receipt)
  if (usable) return usable

  const created = await apiCall(page, 'frappe.client.insert', {
    doc: {
      doctype: 'SC Quality Inspection',
      inspection_date: new Date().toISOString().slice(0, 10),
      purchase_receipt: prs[0].name,
      item: items[0].name,
      overall_status: 'Pending',
      readings: [
        { specification: 'Bao bì', status: 'Pending' },
        { specification: 'Hạn dùng', status: 'Pending' },
      ],
    },
  })
  return { name: created.name }
}

export const tests = [
  {
    name: 'Tạo / tìm 1 draft QI có item + PR',
    run: async ({ page }) => {
      const qi = await ensureDraftQI(page)
      page._qiName = qi.name
      page._qiItem = qi.item
      page._qiPR = qi.purchase_receipt
      const hasItem = !!qi.item
      const hasPR = !!qi.purchase_receipt
      return hasItem && hasPR
        ? { ok: true, detail: `QI=${qi.name}, item=${qi.item}, pr=${qi.purchase_receipt}` }
        : { ok: false, detail: `QI=${qi.name} thiếu item/pr (item=${qi.item}, pr=${qi.purchase_receipt})` }
    },
  },

  {
    name: 'Draft QI mở thẳng ở chế độ edit (không cần bấm "Sửa")',
    run: async ({ page, BASE, OUT, name }) => {
      const qi = page._qiName
      await page.goto(`${BASE}/supplycore/doc/SC%20Quality%20Inspection/${encodeURIComponent(qi)}`)
      await page.waitForTimeout(2000)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })

      // Form ở edit mode → có nút Lưu trong header (💾 Lưu)
      const saveBtn = await page.locator('button:has-text("Lưu")').count()
      // Nếu vẫn còn nút "Sửa" độc lập (không nằm trong "Hoàn tác" hay khác) = chưa auto-edit
      const sideBtnSua = await page.locator('button:has-text("Sửa")').count()
      // Field input phải có (không phải view-only labels)
      const inputCount = await page.locator('form input, form select, form textarea').count()
      const detail = `Lưu=${saveBtn}, Sửa=${sideBtnSua}, inputs=${inputCount}`
      return saveBtn >= 1 && inputCount >= 3
        ? { ok: true, detail }
        : { ok: false, detail }
    },
  },

  {
    name: 'Field "Nhà cung cấp" + "Tên vật tư" hiển thị readonly và được fetch',
    run: async ({ page, OUT, name }) => {
      // supplier label + readonly input bên cạnh
      const supLabel = page.locator('label:has-text("Nhà cung cấp")').first()
      const supExists = await supLabel.count()
      const itemNameExists = await page.locator('label:has-text("Tên vật tư")').count()
      // Readonly input có class bg-gray-50
      const readonlyInputs = await page.locator('input[readonly]').count()
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      return supExists >= 1 && itemNameExists >= 1 && readonlyInputs >= 1
        ? { ok: true, detail: `supplier+item_name label, ${readonlyInputs} readonly inputs` }
        : { ok: false, detail: `supLabel=${supExists}, itemName=${itemNameExists}, readonlyInputs=${readonlyInputs}` }
    },
  },

  {
    name: 'Bulk action "✓ Accept tất cả" áp dụng cho mọi reading',
    run: async ({ page, OUT, name }) => {
      const before = await page.locator('table tbody tr').count()
      if (!before) return { ok: false, detail: 'Không có reading rows' }
      const acceptAll = page.locator('button:has-text("Accept tất cả")').first()
      if (!await acceptAll.count()) return { ok: false, detail: 'Không thấy nút "Accept tất cả"' }
      await acceptAll.click()
      await page.waitForTimeout(600)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      // Sau apply: mọi select status có value=Accepted
      const selects = await page.locator('table tbody select').all()
      const vals = await Promise.all(selects.map(s => s.inputValue().catch(() => '')))
      const accepted = vals.filter(v => v === 'Accepted').length
      return accepted >= before
        ? { ok: true, detail: `${accepted}/${vals.length} rows → Accepted` }
        : { ok: false, detail: `Chỉ ${accepted}/${vals.length} row Accepted` }
    },
  },

  {
    name: 'Field "Lô" có nút "+ Tạo mới" trong dropdown',
    run: async ({ page, OUT, name }) => {
      const batchInput = page.locator('label:has-text("Lô")').first()
        .locator('xpath=following::input[1]')
      await batchInput.click()
      await batchInput.fill('zzz-search-noresult')
      await page.waitForTimeout(500)
      await page.screenshot({ path: `${OUT}/${name}.png` })
      const createBtn = await page.locator('button:has-text("+ Tạo mới Batch")').count()
      return createBtn >= 1
        ? { ok: true, detail: '"+ Tạo mới Batch" xuất hiện' }
        : { ok: false, detail: 'Không thấy "+ Tạo mới Batch" trong dropdown' }
    },
  },

  {
    name: 'Click "+ Tạo mới Batch" → sang form Batch new + sessionStorage pending',
    run: async ({ page, BASE, OUT, name }) => {
      const createBtn = page.locator('button:has-text("+ Tạo mới Batch")').first()
      await createBtn.click()
      await page.waitForTimeout(1500)
      const url = page.url()
      const pending = await page.evaluate((k) => sessionStorage.getItem(k), LINK_PENDING_KEY)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      const onBatchNew = url.includes('/doc/SC%20Batch/new') || url.includes('/doc/SC Batch/new')
      const pendingOk = pending && pending.includes('SC Batch') && pending.includes('batch')
      return onBatchNew && pendingOk
        ? { ok: true, detail: `Đã sang ${url.split('/').pop()}, pending=set` }
        : { ok: false, detail: `url=${url} pending=${(pending||'').slice(0,80)}` }
    },
  },

  {
    name: 'Form Batch new prefill Mã VT từ QI',
    run: async ({ page, OUT, name }) => {
      await page.waitForTimeout(1200)
      const itemInput = page.locator('form label:has-text("Mã VT")').first()
        .locator('xpath=following::input[1]')
      const v = await itemInput.inputValue().catch(() => '')
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      return v && v.length > 0
        ? { ok: true, detail: `Mã VT="${v}"` }
        : { ok: false, detail: 'Mã VT rỗng — prefill không chạy' }
    },
  },
]
