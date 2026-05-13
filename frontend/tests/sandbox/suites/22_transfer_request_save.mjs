// Suite 22: Tạo + Lưu SC Transfer Request không lỗi
import { apiCall, apiGetList, navigateTo } from '../helpers.mjs'

async function pickTwoWarehouses(page) {
  const rows = await apiGetList(page, 'SC Warehouse', {
    fields: ['name', 'is_group', 'disabled'],
    filters: { is_group: 0, disabled: 0 },
    limit: 5,
  })
  if ((rows || []).length < 2) throw new Error('Sandbox cần ≥2 SC Warehouse non-group')
  return [rows[0].name, rows[1].name]
}

async function pickItemWithStock(page, warehouse) {
  // Lấy 1 item có sẵn SLE ở warehouse — đảm bảo transfer hợp lệ sau này
  const sle = await apiGetList(page, 'SC Stock Ledger Entry', {
    fields: ['item', 'warehouse'],
    filters: { warehouse, is_cancelled: 0 },
    limit: 1,
  })
  if (sle?.[0]?.item) return sle[0].item
  // Fallback: bất kỳ item nào
  const items = await apiGetList(page, 'SC Item', { fields: ['name'], limit: 1 })
  return items?.[0]?.name
}

export const tests = [
  {
    name: 'API insert SC Transfer Request (draft) — server không lỗi',
    run: async ({ page }) => {
      const [from, to] = await pickTwoWarehouses(page)
      const item = await pickItemWithStock(page, from)
      page._trCtx = { from, to, item }
      // Lấy UOM thật từ item
      const itemDoc = await apiCall(page, 'frappe.client.get_value',
        { doctype: 'SC Item', filters: { name: item }, fieldname: 'uom' })
      const uom = itemDoc?.uom || 'Cái'
      const today = new Date().toISOString().slice(0, 10)
      const res = await apiCall(page, 'frappe.client.insert', {
        doc: {
          doctype: 'SC Transfer Request',
          request_date: today,
          required_by: today,
          transfer_type: 'Routine',
          from_warehouse: from,
          to_warehouse: to,
          items: [{
            doctype: 'SC Transfer Request Item',
            item, uom, requested_qty: 1,
          }],
        },
      })
      page._trName = res?.name
      return res?.name
        ? { ok: true, detail: `Đã tạo ${res.name} (from=${from}, to=${to}, item=${item})` }
        : { ok: false, detail: `Không tạo được: ${JSON.stringify(res)}` }
    },
  },

  {
    name: 'Form SPA mở /doc/SC Transfer Request/new → fill + Lưu không lỗi',
    run: async ({ page, BASE, OUT, name }) => {
      const { from, to, item } = page._trCtx
      const itemDoc = await apiCall(page, 'frappe.client.get_value',
        { doctype: 'SC Item', filters: { name: item }, fieldname: 'uom' })
      const uom = itemDoc?.uom || 'Cái'

      await navigateTo(page, BASE, '/doc/SC%20Transfer%20Request/new')
      await page.waitForTimeout(1500)

      // Verify schema có Loại yêu cầu (đã được sửa)
      const hasType = await page.locator('label:has-text("Loại yêu cầu")').count()
      const hasRequiredBy = await page.locator('label:has-text("Cần trước ngày")').count()
      if (!hasType || !hasRequiredBy) {
        return { ok: false, detail: `Schema thiếu field: type=${hasType}, required_by=${hasRequiredBy}` }
      }

      // Fill kho nguồn (autocomplete)
      const fromInput = page.locator('label:has-text("Kho nguồn")').first()
        .locator('xpath=following::input[1]')
      await fromInput.fill(from)
      await page.waitForTimeout(500)
      await page.locator(`button:has-text("${from}")`).first().click().catch(() => null)
      await page.waitForTimeout(300)

      // Fill kho đích
      const toInput = page.locator('label:has-text("Kho đích")').first()
        .locator('xpath=following::input[1]')
      await toInput.fill(to)
      await page.waitForTimeout(500)
      await page.locator(`button:has-text("${to}")`).first().click().catch(() => null)
      await page.waitForTimeout(300)

      // Thêm 1 dòng item
      await page.locator('button:has-text("+ Thêm dòng")').first().click()
      await page.waitForTimeout(400)

      // Fill item
      const itemInput = page.locator('table input').first()
      await itemInput.fill(item)
      await page.waitForTimeout(600)
      await page.locator(`button:has-text("${item}")`).first().click().catch(() => null)
      await page.waitForTimeout(300)

      // Fill UOM
      const uomInput = page.locator('table tr td:nth-child(3) input').first()
      await uomInput.fill(uom)
      await page.waitForTimeout(500)
      await page.locator(`button:has-text("${uom}")`).first().click().catch(() => null)
      await page.waitForTimeout(300)

      // Fill SL yêu cầu (col 4)
      const qtyInput = page.locator('table tr td:nth-child(4) input').first()
      await qtyInput.fill('1')
      await page.waitForTimeout(300)

      await page.screenshot({ path: `${OUT}/${name}--before-save.png`, fullPage: true })

      // Bấm Lưu
      const saveBtn = page.locator('button:has-text("Lưu")').first()
      // Watch alerts/toasts
      const errors = []
      page.on('dialog', d => { errors.push(d.message()); d.dismiss().catch(() => null) })
      await saveBtn.click()
      await page.waitForTimeout(2500)

      await page.screenshot({ path: `${OUT}/${name}--after-save.png`, fullPage: true })

      // Sau save thành công → URL phải đổi sang /doc/SC Transfer Request/SC-TR-...
      const url = page.url()
      const onDetail = /\/doc\/SC%20Transfer%20Request\/SC-TR-/.test(url) ||
                       /\/doc\/SC Transfer Request\/SC-TR-/.test(url)

      // Toast lỗi visible?
      const errToast = await page.locator('[class*="toast"], [class*="error"]').filter({ hasText: /lỗi|error|required|throw/i }).count()

      if (onDetail) {
        const docName = decodeURIComponent(url.split('/').pop())
        return { ok: true, detail: `Đã lưu → ${docName}, errors=${errors.length}, errToast=${errToast}` }
      }
      return { ok: false, detail: `URL không đổi (${url}), errors=${JSON.stringify(errors).slice(0,200)}, errToast=${errToast}` }
    },
  },

  {
    name: 'TR tạo qua API có status=Draft và items có requested_qty',
    run: async ({ page }) => {
      const name = page._trName
      if (!name) return { ok: false, detail: 'Test 1 không tạo được TR' }
      const doc = await apiCall(page, 'frappe.client.get', { doctype: 'SC Transfer Request', name })
      const item0 = doc?.items?.[0]
      const ok = doc?.status === 'Draft' && item0?.requested_qty > 0
      return ok
        ? { ok: true, detail: `status=${doc.status}, items[0].requested_qty=${item0.requested_qty}` }
        : { ok: false, detail: `status=${doc?.status}, items=${JSON.stringify(doc?.items || []).slice(0,150)}` }
    },
  },

  {
    name: 'Form mới: required_by mặc định = hôm nay (auto-fill)',
    run: async ({ page, BASE, OUT, name }) => {
      await navigateTo(page, BASE, '/doc/SC%20Transfer%20Request/new')
      await page.waitForTimeout(1200)
      const reqByInput = page.locator('label:has-text("Cần trước ngày")').first()
        .locator('xpath=following::input[1]')
      const v = await reqByInput.inputValue().catch(() => '')
      await page.screenshot({ path: `${OUT}/${name}.png` })
      const today = new Date().toISOString().slice(0, 10)
      return v === today
        ? { ok: true, detail: `required_by = ${v} = today` }
        : { ok: false, detail: `required_by = "${v}" ≠ ${today}` }
    },
  },

  {
    name: 'Bấm Lưu khi thiếu requested_qty → toast cảnh báo, KHÔNG tạo doc',
    run: async ({ page, BASE, OUT, name }) => {
      const { from, to, item } = page._trCtx
      const itemDoc = await apiCall(page, 'frappe.client.get_value',
        { doctype: 'SC Item', filters: { name: item }, fieldname: 'uom' })
      const uom = itemDoc?.uom || 'Cái'

      await navigateTo(page, BASE, '/doc/SC%20Transfer%20Request/new')
      await page.waitForTimeout(1500)

      // Fill warehouses
      const fromInput = page.locator('label:has-text("Kho nguồn")').first().locator('xpath=following::input[1]')
      await fromInput.fill(from)
      await page.waitForTimeout(500)
      await page.locator(`button:has-text("${from}")`).first().click().catch(() => null)
      await page.waitForTimeout(300)

      const toInput = page.locator('label:has-text("Kho đích")').first().locator('xpath=following::input[1]')
      await toInput.fill(to)
      await page.waitForTimeout(500)
      await page.locator(`button:has-text("${to}")`).first().click().catch(() => null)
      await page.waitForTimeout(300)

      // Add row + fill item + uom — BỎ requested_qty
      await page.locator('button:has-text("+ Thêm dòng")').first().click()
      await page.waitForTimeout(400)
      const itemInput = page.locator('table input').first()
      await itemInput.fill(item)
      await page.waitForTimeout(600)
      await page.locator(`button:has-text("${item}")`).first().click().catch(() => null)
      await page.waitForTimeout(300)
      const uomInput = page.locator('table tr td:nth-child(3) input').first()
      await uomInput.fill(uom)
      await page.waitForTimeout(500)
      await page.locator(`button:has-text("${uom}")`).first().click().catch(() => null)
      await page.waitForTimeout(300)

      // KHÔNG fill requested_qty → click Lưu
      const beforeUrl = page.url()
      await page.locator('button:has-text("Lưu")').first().click()
      await page.waitForTimeout(1500)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })

      const afterUrl = page.url()
      const urlNotChanged = afterUrl === beforeUrl
      // Toast warning visible?
      const toastWarn = await page.locator('text=/Thiếu trường bắt buộc/i').count()

      return urlNotChanged && toastWarn >= 1
        ? { ok: true, detail: `URL không đổi, toast cảnh báo hiện (${toastWarn})` }
        : { ok: false, detail: `urlChanged=${!urlNotChanged}, toastWarn=${toastWarn}, after=${afterUrl}` }
    },
  },
]
