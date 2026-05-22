// FC list — Filter dải ngày Từ/Đến gộp thành 1 cặp overlap (period overlap)
//
// Yêu cầu user: thay vì 2 picker mỗi cột → 1 cặp picker filter khoảng giữa

import { navigateTo } from '../helpers.mjs'

export const tests = [
  {
    name: 'Pair render: chỉ 1 cặp 2 picker cho Hiệu lực HĐ (không phải 4)',
    run: async ({ page, BASE, OUT, name }) => {
      await navigateTo(page, BASE, '/list/Framework%20Contract')
      await page.waitForTimeout(1500)
      // Mở filter panel
      await page.locator('button:has-text("Lọc cột")').first().click()
      await page.waitForTimeout(500)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      // Đếm date input trong filter panel
      const html = await page.content()
      if (!html.includes('Hiệu lực HĐ')) {
        return { ok: false, detail: 'Không thấy label "Hiệu lực HĐ"' }
      }
      if (!html.includes('dải lọc giữa')) {
        return { ok: false, detail: 'Không thấy hint "dải lọc giữa"' }
      }
      // Đếm input[type=date] trong filter card (lần xuất hiện đầu tiên = filter panel)
      const dateInputs = await page.locator('input[type="date"]').count()
      // FC có 1 pair (valid_from + valid_to) → 2 picker. Nếu render đơn lẻ sẽ là 4.
      if (dateInputs !== 2) {
        return { ok: false, detail: `Mong 2 date picker, thấy ${dateInputs}` }
      }
      return { ok: true, detail: `Pair render: ${dateInputs} picker cho "Hiệu lực HĐ" ✓` }
    },
  },
  {
    name: 'Filter overlap: chọn dải [2026-01-01 → 2026-12-31] giảm số kết quả',
    run: async ({ page, BASE }) => {
      // Total ban đầu
      const total0 = await page.evaluate(async () => {
        const csrf = window.sc_csrf || document.querySelector('meta[name="csrf-token"]')?.content || ''
        const r = await fetch('/api/method/supplycore.api.frontend.count_docs', {
          method: 'POST', credentials: 'include',
          headers: { 'Content-Type': 'application/json', 'X-Frappe-CSRF-Token': csrf },
          body: JSON.stringify({ doctype: 'Framework Contract', filters: {} }),
        })
        const d = await r.json()
        return d.message
      })
      await navigateTo(page, BASE, '/list/Framework%20Contract')
      await page.waitForTimeout(1500)
      await page.locator('button:has-text("Lọc cột")').first().click()
      await page.waitForTimeout(500)
      // Chọn dải nhỏ — chỉ Q1 2026
      const dates = await page.locator('input[type="date"]').all()
      if (dates.length < 2) return { ok: false, detail: `Thiếu date picker (got ${dates.length})` }
      await dates[0].fill('2026-01-01')
      await dates[1].fill('2026-03-31')
      await page.waitForTimeout(800)  // debounce 300ms + load
      // Đọc subtitle "X bản ghi (đã lọc)"
      const subtitle = await page.locator('text=/\\d+.*bản ghi/').first().textContent()
      const m = subtitle?.match(/([\d.,]+)\s+bản\s+ghi/)
      if (!m) return { ok: false, detail: `Không parse được subtitle: ${subtitle}` }
      const filtered = Number(m[1].replace(/[.,]/g, ''))
      if (filtered >= total0) {
        return { ok: false, detail: `Filtered=${filtered} không nhỏ hơn total=${total0}` }
      }
      if (!subtitle.includes('đã lọc')) {
        return { ok: false, detail: `Subtitle thiếu "(đã lọc)": ${subtitle}` }
      }
      return { ok: true, detail: `total=${total0} → filtered=${filtered} (đã lọc Q1 2026) ✓` }
    },
  },
  {
    name: 'Filter overlap đúng SQL: valid_from <= to AND valid_to >= from',
    run: async ({ page }) => {
      // Pull list trực tiếp với filter dải
      const list = await page.evaluate(async () => {
        const csrf = window.sc_csrf || document.querySelector('meta[name="csrf-token"]')?.content || ''
        const r = await fetch('/api/method/supplycore.api.frontend.list_docs', {
          method: 'POST', credentials: 'include',
          headers: { 'Content-Type': 'application/json', 'X-Frappe-CSRF-Token': csrf },
          body: JSON.stringify({
            doctype: 'Framework Contract',
            fields: ['name', 'valid_from', 'valid_to'],
            filters: [
              ['valid_from', '<=', '2026-06-30'],
              ['valid_to',   '>=', '2026-01-01'],
            ],
            limit: 50,
          }),
        })
        const d = await r.json()
        return d.message
      })
      if (!Array.isArray(list)) return { ok: false, detail: 'list không phải array' }
      // Mọi record phải overlap với [2026-01-01, 2026-06-30]
      for (const fc of list) {
        const vf = fc.valid_from, vt = fc.valid_to
        if (!(vf <= '2026-06-30' && vt >= '2026-01-01')) {
          return { ok: false, detail: `${fc.name}: ${vf}→${vt} không overlap [2026-01-01, 2026-06-30]` }
        }
      }
      return { ok: true, detail: `${list.length} FC overlap đúng với dải Q1-Q2/2026 ✓` }
    },
  },
]
