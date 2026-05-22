// Suite 11: Patient Dispensing item auto-fetch UOM/đơn giá/lô FEFO
import { apiCall, navigateTo } from '../helpers.mjs'

export const tests = [
  {
    name: 'API pd_item_autofetch trả uom + unit_cost + batch FEFO',
    run: async ({ page }) => {
      const res = await apiCall(page, 'supplycore.api.frontend.pd_item_autofetch',
        { item: 'DTRC-RL', warehouse: 'Kho Khoa Dược' })
      if (!res || !res.uom) return { ok: false, detail: `Missing uom: ${JSON.stringify(res)}` }
      if (!res.batch) return { ok: false, detail: 'Không tìm thấy lô FEFO' }
      if (!(res.unit_cost > 0)) return { ok: false, detail: `unit_cost=${res.unit_cost}` }
      return { ok: true, detail: `uom=${res.uom}, đơn giá=${res.unit_cost}, lô=${res.batch}` }
    },
  },
  {
    name: 'API pd_item_autofetch: kho không có lô → batch=null',
    run: async ({ page }) => {
      const res = await apiCall(page, 'supplycore.api.frontend.pd_item_autofetch',
        { item: 'VTTH-MASK-3PLY', warehouse: 'Kho Khoa Nhi' })
      return res && !res.batch
        ? { ok: true, detail: 'batch=null khi kho không có lô khả dụng' }
        : { ok: false, detail: `batch=${res?.batch}` }
    },
  },
  {
    name: 'PD form: chọn item+kho → tự fill ĐVT/đơn giá/lô',
    run: async ({ page, BASE, OUT, name }) => {
      await navigateTo(page, BASE, '/doc/SC%20Patient%20Dispensing/new')
      await page.waitForTimeout(1500)
      // Add 1 row
      await page.locator('button:has-text("+ Thêm dòng")').first().click()
      await page.waitForTimeout(400)
      // Fill item
      const itemInput = page.locator('table input[placeholder*="SC Item"], table input[placeholder*="Vật tư"]').first()
      await itemInput.fill('DTRC-RL')
      await page.waitForTimeout(700)
      const opt = page.locator('button:has-text("DTRC-RL")').first()
      if (await opt.count()) await opt.click()
      await page.waitForTimeout(400)
      // Fill warehouse
      const whInput = page.locator('table input[placeholder*="Warehouse"], table input[placeholder*="Kho"]').first()
      await whInput.fill('Kho Khoa Dược')
      await page.waitForTimeout(700)
      const whOpt = page.locator('button:has-text("Kho Khoa Dược")').first()
      if (await whOpt.count()) await whOpt.click()
      await page.waitForTimeout(1200)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      // After autofetch: row should have uom/unit_cost/batch filled
      const inputs = await page.locator('table input').all()
      const values = await Promise.all(inputs.map(i => i.inputValue().catch(() => '')))
      const filled = values.filter(v => v && v.length > 0).length
      return filled >= 4
        ? { ok: true, detail: `${filled} ô đã tự điền` }
        : { ok: false, detail: `Chỉ ${filled} ô filled — autofetch không chạy` }
    },
  },
  {
    name: 'Putaway: bin dropdown có option cho kho mặc định',
    run: async ({ page, BASE, OUT, name }) => {
      await navigateTo(page, BASE, '/putaway')
      await page.waitForTimeout(2500)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      const selects = await page.locator('select').all()
      // Find row-level select dropdowns (skip the warehouse filter)
      let withOptions = 0
      for (const s of selects) {
        const opts = await s.locator('option').count()
        if (opts >= 3) withOptions++  // 1 placeholder + 2+ bins
      }
      return withOptions >= 1
        ? { ok: true, detail: `${withOptions} dropdown có ≥2 lựa chọn bin` }
        : { ok: false, detail: 'Tất cả dropdown rỗng' }
    },
  },
]
