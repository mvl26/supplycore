// Khi chọn item trong child row, dropdown UOM/Batch chỉ hiển thị giá trị
// liên quan đến item đó (scope filter).
//
// User: "chọn item DTRC-RL chỉ hiện uom và lô của item đó"

import { apiCall, apiGetList, navigateTo, rand } from '../helpers.mjs'

export const tests = [
  {
    name: 'Backend item_eligible_uoms trả UOM của item',
    run: async ({ page }) => {
      // Pick 1 item ngẫu nhiên
      const items = await apiGetList(page, 'SC Item', { fields: ['name', 'uom'], limit: 3 })
      if (!items.length) return { ok: false, detail: 'No items' }
      const it = items[0]
      const uoms = await apiCall(page, 'supplycore.api.frontend.item_eligible_uoms', { item: it.name })
      if (!Array.isArray(uoms) || !uoms.length) {
        return { ok: false, detail: `uoms rỗng cho ${it.name}` }
      }
      if (!uoms.includes(it.uom)) {
        return { ok: false, detail: `${it.uom} không có trong eligible: ${uoms.join(',')}` }
      }
      return { ok: true, detail: `${it.name} → ${uoms.length} UOM (${uoms.join(', ')}) ✓` }
    },
  },
  {
    name: 'item_eligible_uoms empty khi item rỗng/sai',
    run: async ({ page }) => {
      const u1 = await apiCall(page, 'supplycore.api.frontend.item_eligible_uoms', { item: '' })
      const u2 = await apiCall(page, 'supplycore.api.frontend.item_eligible_uoms',
                                 { item: 'NONEXISTENT-XXX' })
      if (!Array.isArray(u1) || u1.length !== 0) return { ok: false, detail: `empty item → ${u1}` }
      if (!Array.isArray(u2) || u2.length !== 0) return { ok: false, detail: `bad item → ${u2}` }
      return { ok: true, detail: 'empty/bad item → [] ✓' }
    },
  },
  {
    name: 'list_docs filter SC Batch theo item: chỉ trả batch của item đó',
    run: async ({ page }) => {
      // Tìm 1 item có batch
      const batches = await apiGetList(page, 'SC Batch', {
        fields: ['name', 'item'], limit: 5,
      })
      const target = batches.find(b => b.item)
      if (!target) return { ok: false, detail: 'No batch with item' }
      const itemCode = target.item
      // Filter
      const filtered = await apiGetList(page, 'SC Batch', {
        fields: ['name', 'item'],
        filters: [['item', '=', itemCode]],
        limit: 50,
      })
      if (!filtered.length) {
        return { ok: false, detail: `Filter trả rỗng cho item=${itemCode}` }
      }
      const wrong = filtered.filter(b => b.item !== itemCode)
      if (wrong.length) {
        return { ok: false, detail: `${wrong.length} batch sai item: ${wrong.slice(0,3).map(b => b.name).join(',')}` }
      }
      return { ok: true, detail: `item=${itemCode} → ${filtered.length} batch (đúng item) ✓` }
    },
  },
  {
    name: 'UI: FC form mới — chọn item code, dropdown UOM filter theo item',
    run: async ({ page, BASE, OUT, name }) => {
      // Pick 1 SC Item có UOM
      const items = await apiGetList(page, 'SC Item', {
        fields: ['name', 'uom', 'item_name'],
        limit: 1,
      })
      if (!items.length) return { ok: false, detail: 'no items' }
      const it = items[0]

      await navigateTo(page, BASE, '/doc/Framework%20Contract/new')
      await page.waitForTimeout(1500)
      // Bấm "+ Thêm dòng" trong bảng Danh mục vật tư
      await page.locator('button:has-text("Thêm dòng")').first().click()
      await page.waitForTimeout(400)
      // Điền item_code vào input đầu tiên của row (input đầu tiên trong tbody là Link autocomplete)
      const itemInput = page.locator('tbody input').first()
      await itemInput.click()
      await itemInput.fill(it.name)
      await page.waitForTimeout(500)
      // Click pick option matching item
      await page.locator(`button:has-text("${it.name}")`).first().click().catch(() => null)
      await page.waitForTimeout(800)
      // UOM input là input thứ 2 trong row → click để mở dropdown
      const uomInput = page.locator('tbody tr').first().locator('input').nth(1)
      await uomInput.click()
      await page.waitForTimeout(1000)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      // Đếm option trong dropdown teleported
      const visibleOpts = await page.locator('body > div[style*="position: fixed"] button').count()
      // Có thể nhiều dropdown trước đó được render; check qua actual UOM xuất hiện
      // Tìm dropdown teleport gần input UOM (open=true)
      const dropdownText = await page.locator('body > div[style*="position: fixed"]').last().textContent()
      const allUoms = await apiGetList(page, 'SC UOM', { fields: ['name'], limit: 50 })
      if (allUoms.length <= 1) {
        return { ok: true, detail: `Skip — chỉ ${allUoms.length} UOM trong hệ thống, không thể distinguish filter` }
      }
      // Dropdown phải chứa item.uom
      if (!dropdownText?.includes(it.uom)) {
        return { ok: false, detail: `UOM dropdown không chứa "${it.uom}" của item ${it.name}: ${dropdownText?.slice(0, 200)}` }
      }
      // Dropdown KHÔNG chứa toàn bộ allUoms (nếu chứa thì filter không hoạt động)
      const containedAll = allUoms.every(u => dropdownText.includes(u.name))
      if (containedAll && allUoms.length > 3) {
        return { ok: false, detail: `Dropdown chứa cả ${allUoms.length} UOM — filter scope không hoạt động` }
      }
      return { ok: true, detail: `UOM dropdown filter theo ${it.name} → có "${it.uom}", không show toàn bộ ✓` }
    },
  },
  {
    name: 'UI: Stock Entry — chọn item, dropdown Batch chỉ hiện batch của item',
    run: async ({ page, BASE, OUT, name }) => {
      // Pick item có batch
      const batches = await apiGetList(page, 'SC Batch', {
        fields: ['name', 'item'], limit: 20,
      })
      const target = batches.find(b => b.item)
      if (!target) return { ok: false, detail: 'No batch with item' }
      const itemCode = target.item
      const wrongItem = batches.find(b => b.item && b.item !== itemCode)?.item

      await navigateTo(page, BASE, '/doc/SC%20Stock%20Entry/new')
      await page.waitForTimeout(1500)
      await page.locator('button:has-text("Thêm dòng")').first().click()
      await page.waitForTimeout(400)
      const rowInputs = page.locator('tbody tr').first().locator('input')
      const itemInput = rowInputs.first()
      await itemInput.click()
      await itemInput.fill(itemCode)
      await page.waitForTimeout(500)
      await page.locator(`button:has-text("${itemCode}")`).first().click().catch(() => null)
      await page.waitForTimeout(800)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      // Batch col: item(0), uom(1), qty(2), valuation_rate(3), batch(4)
      const batchInput = rowInputs.nth(4)
      await batchInput.click()
      await page.waitForTimeout(1000)
      const dropText = await page.locator('body > div[style*="position: fixed"]').last().textContent()
      if (!dropText) return { ok: false, detail: 'không thấy dropdown batch' }
      // Phải có batch của itemCode (kiểm bằng tên target.name)
      if (!dropText.includes(target.name)) {
        return { ok: false, detail: `Batch ${target.name} không có trong dropdown` }
      }
      // KHÔNG được có batch của wrongItem (nếu có)
      if (wrongItem) {
        const wrongBatches = batches.filter(b => b.item === wrongItem)
        const leaked = wrongBatches.filter(b => dropText.includes(b.name))
        if (leaked.length) {
          return { ok: false, detail: `Batch của item khác lọt vào: ${leaked.slice(0,2).map(b => b.name)}` }
        }
      }
      return { ok: true, detail: `Batch dropdown lọc đúng item=${itemCode} ✓` }
    },
  },
]
