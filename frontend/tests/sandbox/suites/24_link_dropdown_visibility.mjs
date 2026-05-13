// Suite 24: Verify autocomplete dropdown trong child table visible đầy đủ
// (không bị clip bởi overflow-x của table)
import { navigateTo } from '../helpers.mjs'

export const tests = [
  {
    name: 'TR form: dropdown chọn item trong table có width ≥320px và nằm trên cùng',
    run: async ({ page, BASE, OUT, name }) => {
      await navigateTo(page, BASE, '/doc/SC%20Transfer%20Request/new')
      await page.waitForTimeout(1500)
      // Thêm 1 dòng
      await page.locator('button:has-text("+ Thêm dòng")').first().click()
      await page.waitForTimeout(400)
      // Focus input đầu tiên trong row (Mã VT)
      const itemInput = page.locator('table tbody input').first()
      await itemInput.click()
      await page.waitForTimeout(700)
      // Dropdown đã teleport ra body → tìm bằng selector body level
      const dropdown = page.locator('body > div').filter({ hasText: /Đang tìm|Không có kết quả|^SC-/ })
        .or(page.locator('body > div[style*="position: fixed"]')).first()
      const box = await dropdown.boundingBox().catch(() => null)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      if (!box) {
        // Try alternative selector
        const alt = page.locator('div[style*="z-index: 1000"]').first()
        const altBox = await alt.boundingBox().catch(() => null)
        return altBox && altBox.width >= 320
          ? { ok: true, detail: `Dropdown w=${Math.round(altBox.width)}px (alt selector)` }
          : { ok: false, detail: 'Không tìm thấy dropdown teleported' }
      }
      return box.width >= 320
        ? { ok: true, detail: `Dropdown w=${Math.round(box.width)}px, x=${Math.round(box.x)}, y=${Math.round(box.y)}` }
        : { ok: false, detail: `Dropdown quá hẹp: ${Math.round(box.width)}px` }
    },
  },

  {
    name: 'Dropdown render qua Teleport (DOM nằm ngoài <table>)',
    run: async ({ page }) => {
      // Dropdown vẫn open từ test trên — kiểm tra DOM parent
      const insideTable = await page.locator('table div[style*="z-index"]').count()
      const insideBody = await page.locator('body > div[style*="z-index: 1000"]').count()
      return insideTable === 0 && insideBody >= 1
        ? { ok: true, detail: `Teleported: bên trong table=${insideTable}, body=${insideBody}` }
        : { ok: false, detail: `table=${insideTable}, body=${insideBody}` }
    },
  },

  {
    name: 'Click 1 option trong dropdown → input update giá trị',
    run: async ({ page, OUT, name }) => {
      // Đợi search có kết quả
      await page.waitForTimeout(500)
      const firstOption = page.locator('body > div[style*="z-index: 1000"] button').filter({ hasText: /^SC-|^[A-Z]/ }).first()
      const optExists = await firstOption.count()
      if (!optExists) {
        await page.screenshot({ path: `${OUT}/${name}--no-opt.png` })
        return { ok: false, detail: 'Không có option để click' }
      }
      // Lấy code dòng đầu (font-mono div)
      const expectedCode = (await firstOption.locator('div.font-mono').textContent() || '').trim()
      await firstOption.click()
      await page.waitForTimeout(400)
      const inputVal = await page.locator('table tbody input').first().inputValue()
      await page.screenshot({ path: `${OUT}/${name}.png` })
      return inputVal && inputVal === expectedCode
        ? { ok: true, detail: `Input="${inputVal}"` }
        : { ok: false, detail: `Input="${inputVal}", expected="${expectedCode}"` }
    },
  },
]
