// Suite 25: Trang Vị trí lưu trữ (Bin Location) trong M0 Dữ liệu nền
import { apiCall, apiGetList, navigateTo } from '../helpers.mjs'

export const tests = [
  {
    name: 'M0 hub có tab "Vị trí lưu trữ"',
    run: async ({ page, BASE, OUT, name }) => {
      await navigateTo(page, BASE, '/m0')
      await page.waitForTimeout(1200)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      const cnt = await page.locator('text=/Vị trí lưu trữ/i').count()
      return cnt >= 1
        ? { ok: true, detail: `Tìm thấy "Vị trí lưu trữ" (${cnt} lần)` }
        : { ok: false, detail: 'Không thấy tab "Vị trí lưu trữ" trong M0' }
    },
  },

  {
    name: 'List page /list/Bin Location render được',
    run: async ({ page, BASE, OUT, name }) => {
      await navigateTo(page, BASE, '/list/Bin%20Location')
      await page.waitForTimeout(1500)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      // Header có tiêu đề Vị trí lưu trữ + bảng có column Kho/Mã
      const titleOK = await page.locator('text=/Vị trí lưu trữ/').count()
      const colWh = await page.locator('th:has-text("Kho")').count()
      const colCode = await page.locator('th:has-text("Code"), th:has-text("Mã vị trí")').count()
      return titleOK >= 1 && colWh >= 1 && colCode >= 1
        ? { ok: true, detail: `title=${titleOK}, colWh=${colWh}, colCode=${colCode}` }
        : { ok: false, detail: `title=${titleOK}, colWh=${colWh}, colCode=${colCode}` }
    },
  },

  {
    name: 'Form /doc/Bin Location/new mở được và có required fields',
    run: async ({ page, BASE, OUT, name }) => {
      await navigateTo(page, BASE, '/doc/Bin%20Location/new')
      await page.waitForTimeout(1500)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      const labelKho = await page.locator('label:has-text("Kho")').count()
      const labelCode = await page.locator('label:has-text("Mã vị trí")').count()
      const labelZone = await page.locator('label:has-text("Khu (Zone)")').count()
      const labelTemp = await page.locator('label:has-text("Kiểm soát nhiệt độ")').count()
      return labelKho >= 1 && labelCode >= 1 && labelZone >= 1 && labelTemp >= 1
        ? { ok: true, detail: `labels: Kho=${labelKho}, Code=${labelCode}, Zone=${labelZone}, Temp=${labelTemp}` }
        : { ok: false, detail: `labels: Kho=${labelKho}, Code=${labelCode}, Zone=${labelZone}, Temp=${labelTemp}` }
    },
  },

  {
    name: 'Tạo mới Bin Location qua SPA: fill + Lưu',
    run: async ({ page, BASE, OUT, name }) => {
      const warehouses = await apiGetList(page, 'SC Warehouse', {
        fields: ['name'], filters: { is_group: 0, disabled: 0 }, limit: 1,
      })
      if (!warehouses?.[0]) return { ok: false, detail: 'Sandbox không có SC Warehouse' }
      const wh = warehouses[0].name
      const binCode = `TEST-${Date.now().toString(36).toUpperCase()}`

      await navigateTo(page, BASE, '/doc/Bin%20Location/new')
      await page.waitForTimeout(1300)

      // Fill kho
      const whInput = page.locator('label:has-text("Kho")').first()
        .locator('xpath=following::input[1]')
      await whInput.fill(wh)
      await page.waitForTimeout(600)
      await page.locator(`body > div[style*="z-index: 1000"] button:has-text("${wh}")`)
        .first().click().catch(() => null)
      await page.waitForTimeout(300)

      // Fill bin_code
      const codeInput = page.locator('label:has-text("Mã vị trí")').first()
        .locator('xpath=following::input[1]')
      await codeInput.fill(binCode)
      await page.waitForTimeout(200)

      await page.screenshot({ path: `${OUT}/${name}--before-save.png`, fullPage: true })
      await page.locator('button:has-text("Lưu")').first().click()
      await page.waitForTimeout(2200)
      await page.screenshot({ path: `${OUT}/${name}--after-save.png`, fullPage: true })

      const url = page.url()
      const onDetail = url.includes('/doc/Bin%20Location/') && !url.endsWith('/new')
      return onDetail
        ? { ok: true, detail: `Đã lưu, URL=${decodeURIComponent(url).split('/').pop()}` }
        : { ok: false, detail: `URL=${url}` }
    },
  },

  {
    name: 'Verify bin vừa tạo có trong DB qua API',
    run: async ({ page }) => {
      const rows = await apiGetList(page, 'Bin Location', {
        fields: ['name', 'warehouse', 'bin_code', 'enabled'],
        filters: { bin_code: ['like', 'TEST-%'] },
        order_by: 'creation desc',
        limit: 1,
      })
      const r = rows?.[0]
      return r?.name
        ? { ok: true, detail: `${r.name}: ${r.warehouse}/${r.bin_code} (enabled=${r.enabled})` }
        : { ok: false, detail: 'Không tìm thấy bin TEST-* trong DB' }
    },
  },
]
