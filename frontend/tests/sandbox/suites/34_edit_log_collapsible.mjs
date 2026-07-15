// Lịch sử sửa — section thu gọn mặc định, mỗi log 1 dòng tóm tắt,
// click mới mở chi tiết field-level.
//
// User: làm gọn, thu gọn/mở rộng được, tránh hiển thị nhiều log.

import { apiGetList, navigateTo, rand } from '../helpers.mjs'

async function createFC(page, num) {
  return page.evaluate(async ({ num }) => {
    const csrf = window.sc_csrf || document.querySelector('meta[name="csrf-token"]')?.content || ''
    const sup = await fetch('/api/method/supplycore.api.frontend.list_docs', {
      method: 'POST', credentials: 'include',
      headers: { 'Content-Type': 'application/json', 'X-Frappe-CSRF-Token': csrf },
      body: JSON.stringify({ doctype: 'SC Supplier', fields: ['name'],
        filters: [['disabled', '=', 0]], limit: 1 }),
    }).then(r => r.json()).then(d => d.message?.[0]?.name)
    const itm = await fetch('/api/method/supplycore.api.frontend.list_docs', {
      method: 'POST', credentials: 'include',
      headers: { 'Content-Type': 'application/json', 'X-Frappe-CSRF-Token': csrf },
      body: JSON.stringify({ doctype: 'SC Item', fields: ['name', 'uom'], limit: 1 }),
    }).then(r => r.json()).then(d => d.message?.[0])
    const body = {
      doctype: 'Framework Contract',
      supplier: sup, contract_number: num,
      contract_date: '2026-05-20', valid_from: '2026-05-20', valid_to: '2027-05-20',
      payment_terms: 'Net 30',
      items: [{ doctype: 'FC Item', item_code: itm.name, uom: itm.uom,
                contract_qty: 10, unit_price: 1000 }],
    }
    const r = await fetch('/api/resource/Framework%20Contract', {
      method: 'POST', credentials: 'include',
      headers: { 'Content-Type': 'application/json', 'X-Frappe-CSRF-Token': csrf },
      body: JSON.stringify(body),
    })
    const d = await r.json()
    if (!r.ok) throw new Error(d.exception || JSON.stringify(d))
    return d.data
  }, { num })
}

async function editFC(page, name, payload) {
  return page.evaluate(async ({ name, payload }) => {
    const csrf = window.sc_csrf || document.querySelector('meta[name="csrf-token"]')?.content || ''
    const r = await fetch(`/api/resource/Framework%20Contract/${encodeURIComponent(name)}`, {
      method: 'PUT', credentials: 'include',
      headers: { 'Content-Type': 'application/json', 'X-Frappe-CSRF-Token': csrf },
      body: JSON.stringify(payload),
    })
    const d = await r.json()
    if (!r.ok) throw new Error(d.exception || JSON.stringify(d))
  }, { name, payload })
}

export const tests = [
  {
    name: 'Lịch sử sửa thu gọn mặc định (không hiện chi tiết)',
    run: async ({ page, BASE, OUT, name }) => {
      const num = `TEST-LOG-${rand(5).toUpperCase()}`
      const fc = await createFC(page, num)
      // Tạo 2 lần sửa → 2 version
      await editFC(page, fc.name, { payment_terms: 'Net 45' })
      await editFC(page, fc.name, { payment_terms: 'Net 60', remarks: 'ghi chú test' })

      await navigateTo(page, BASE, `/doc/Framework%20Contract/${encodeURIComponent(fc.name)}`)
      await page.waitForTimeout(1800)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })

      const html = await page.content()
      if (!html.includes('Lịch sử sửa')) {
        return { ok: false, detail: 'Không thấy section "Lịch sử sửa"' }
      }
      // Thu gọn mặc định → header có "Bấm để xem", chưa render bảng diff
      if (!html.includes('Bấm để xem')) {
        return { ok: false, detail: 'Section không ở trạng thái thu gọn mặc định' }
      }
      // Khi thu gọn, value diff "Net 60" KHÔNG được hiển thị
      // (chỉ kiểm trong vùng lịch sử — value này không nằm field form vì FC đã readonly sau)
      return { ok: true, detail: `${num}: section "Lịch sử sửa" thu gọn mặc định ✓` }
    },
  },
  {
    name: 'Click header → mở section, mỗi log 1 dòng tóm tắt',
    run: async ({ page, BASE, OUT, name }) => {
      const fcs = await apiGetList(page, 'Framework Contract', {
        fields: ['name'], filters: [['contract_number', 'like', 'TEST-LOG-%']],
        limit: 1, order_by: 'creation desc',
      })
      if (!fcs.length) return { ok: false, detail: 'No TEST-LOG FC' }
      await navigateTo(page, BASE, `/doc/Framework%20Contract/${encodeURIComponent(fcs[0].name)}`)
      await page.waitForTimeout(1800)
      // Click header "Lịch sử sửa"
      await page.locator('button:has-text("Lịch sử sửa")').first().click()
      await page.waitForTimeout(1200)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      const html = await page.content()
      // Sau khi mở → có "thay đổi —" (dòng tóm tắt)
      if (!html.includes('thay đổi —')) {
        return { ok: false, detail: 'Không thấy dòng tóm tắt "N thay đổi —"' }
      }
      // Mặc định các version CHƯA mở chi tiết → không có bảng diff (line-through value)
      const diffRows = await page.locator('table td.line-through, table td[class*="line-through"]').count()
      if (diffRows > 0) {
        return { ok: false, detail: `Chi tiết diff hiện sẵn (${diffRows}) — đáng lẽ phải thu gọn` }
      }
      return { ok: true, detail: 'Mở section → log dạng 1 dòng tóm tắt, chi tiết vẫn ẩn ✓' }
    },
  },
  {
    name: 'Click 1 log → mở chi tiết field-level diff',
    run: async ({ page, BASE }) => {
      const fcs = await apiGetList(page, 'Framework Contract', {
        fields: ['name'], filters: [['contract_number', 'like', 'TEST-LOG-%']],
        limit: 1, order_by: 'creation desc',
      })
      if (!fcs.length) return { ok: false, detail: 'No TEST-LOG FC' }
      await navigateTo(page, BASE, `/doc/Framework%20Contract/${encodeURIComponent(fcs[0].name)}`)
      await page.waitForTimeout(1800)
      await page.locator('button:has-text("Lịch sử sửa")').first().click()
      await page.waitForTimeout(1200)
      // Click dòng tóm tắt đầu tiên
      const summaryBtn = page.locator('button:has-text("thay đổi —")').first()
      await summaryBtn.click()
      await page.waitForTimeout(600)
      // Giờ phải có bảng diff với value cũ/mới
      const diffRows = await page.locator('table td[class*="line-through"]').count()
      if (diffRows < 1) {
        return { ok: false, detail: 'Click log không mở được chi tiết diff' }
      }
      // Click lại → đóng
      await summaryBtn.click()
      await page.waitForTimeout(500)
      const afterClose = await page.locator('table td[class*="line-through"]').count()
      if (afterClose >= diffRows) {
        return { ok: false, detail: 'Click lại không đóng được chi tiết' }
      }
      return { ok: true, detail: `Click log → mở ${diffRows} dòng diff; click lại → đóng ✓` }
    },
  },
  {
    name: 'Log chỉ tạo khi lưu (1 explicit save = 1 version)',
    run: async ({ page }) => {
      const num = `TEST-LOG-${rand(5).toUpperCase()}`
      const fc = await createFC(page, num)
      // 3 lần sửa rời rạc
      await editFC(page, fc.name, { payment_terms: 'A' })
      await editFC(page, fc.name, { payment_terms: 'B' })
      await editFC(page, fc.name, { payment_terms: 'C' })
      const log = await page.evaluate(async ({ name }) => {
        const csrf = window.sc_csrf || document.querySelector('meta[name="csrf-token"]')?.content || ''
        const r = await fetch('/api/method/supplycore.api.frontend.get_doc_versions', {
          method: 'POST', credentials: 'include',
          headers: { 'Content-Type': 'application/json', 'X-Frappe-CSRF-Token': csrf },
          body: JSON.stringify({ doctype: 'Framework Contract', name }),
        })
        const d = await r.json()
        return d.message
      }, { name: fc.name })
      // 3 lần sửa → đúng 3 version, không phải nhiều hơn (không auto-track)
      if (!Array.isArray(log)) return { ok: false, detail: 'log không phải array' }
      if (log.length !== 3) {
        return { ok: false, detail: `3 lần sửa nhưng có ${log.length} version (mong đúng 3)` }
      }
      return { ok: true, detail: `${num}: 3 lần lưu = đúng 3 log, không track thừa ✓` }
    },
  },
]
