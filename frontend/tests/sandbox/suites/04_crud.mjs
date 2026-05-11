// Suite 04: Full CRUD flow — tạo doc + đọc + xóa
//
// Mỗi test tạo doc → verify → cleanup
// Dùng REST API để cleanup (faster than UI)

import { randomBytes } from 'crypto'

const rand = (n = 4) => randomBytes(n).toString('hex')

export const tests = [
  {
    name: 'CRUD: SC UOM tạo + view + xóa',
    run: async ({ page, BASE, OUT, name }) => {
      const uomName = `UOM-test-${rand()}`
      // 1. Mở form mới
      await page.goto(`${BASE}/supplycore/doc/SC%20UOM/new`)
      await page.waitForTimeout(1200)
      // 2. Điền form
      await page.locator('input[type=text]').first().fill(uomName)
      // 3. Click Lưu
      await page.locator('button').filter({ hasText: 'Lưu' }).click()
      await page.waitForTimeout(2000)
      // 4. Check URL chuyển sang detail
      const url = page.url()
      const created = url.includes(encodeURIComponent(uomName))
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      if (!created) return { ok: false, detail: `URL after save: ${url}` }

      // 5. Cleanup qua API
      const csrf = await page.evaluate(() => window.sc_csrf)
      const cleanupRes = await page.evaluate(async ({ uomName, csrf }) => {
        const r = await fetch(`/api/resource/SC%20UOM/${encodeURIComponent(uomName)}`, {
          method: 'DELETE', credentials: 'include',
          headers: { 'X-Frappe-CSRF-Token': csrf },
        })
        return r.status
      }, { uomName, csrf })

      return { ok: true, detail: `Created ${uomName}, cleanup HTTP ${cleanupRes}` }
    },
  },
  {
    name: 'CRUD: SC Department tạo + xóa',
    run: async ({ page, BASE, OUT, name }) => {
      const deptName = `Dept-test-${rand()}`
      await page.goto(`${BASE}/supplycore/doc/SC%20Department/new`)
      await page.waitForTimeout(1500)
      const firstField = page.locator('input').first()
      await firstField.fill(deptName)
      await page.waitForTimeout(300)
      await page.locator('button:has-text("Lưu")').first().click()
      await page.waitForTimeout(2500)
      const url = page.url()
      const created = url.includes(encodeURIComponent(deptName))
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      if (!created) {
        const toastErr = await page.locator('.bg-red-50').textContent().catch(() => '')
        return { ok: false, detail: `URL: ${url}; toast="${(toastErr || '').slice(0, 120)}"` }
      }

      const csrf = await page.evaluate(() => window.sc_csrf)
      await page.evaluate(async ({ deptName, csrf }) => {
        await fetch(`/api/resource/SC%20Department/${encodeURIComponent(deptName)}`, {
          method: 'DELETE', credentials: 'include',
          headers: { 'X-Frappe-CSRF-Token': csrf },
        })
      }, { deptName, csrf })
      return { ok: true, detail: `Created + cleaned: ${deptName}` }
    },
  },
  {
    name: 'List filter search by name',
    run: async ({ page, BASE }) => {
      await page.goto(`${BASE}/supplycore/list/SC%20Item`)
      await page.waitForTimeout(1500)
      const beforeRows = await page.locator('table tbody tr').count()
      // Type into search box
      const searchInput = page.locator('input[placeholder*="Tìm"]').first()
      await searchInput.fill('DTRC')
      await searchInput.press('Enter')
      await page.waitForTimeout(1500)
      const afterRows = await page.locator('table tbody tr').count()
      return afterRows >= 1 && afterRows <= beforeRows
        ? { ok: true, detail: `Filter DTRC: ${beforeRows} → ${afterRows} rows` }
        : { ok: false, detail: `${beforeRows} → ${afterRows}` }
    },
  },
]
