// Framework Contract — Tạo HĐ với attach, auto-sum, owner, lock khi duyệt, edit log
//
// Yêu cầu user (2026-05-18):
// 1. Tạo HĐ: nhập tên (contract_number) + attach bản mềm
// 2. Tổng giá trị (VND) = Σ thành tiền items (auto-sum, không cho nhập tay)
// 3. Ghi lại người tạo (owner)
// 4. Có chức năng sửa
// 5. Nếu đã duyệt → không cho sửa
// 6. Nếu sửa → ghi log (Version)

import {
  apiCall, apiGetList, apiGetDoc, apiRunDocMethod, navigateTo, rand,
} from '../helpers.mjs'

const SUPPLIER = 'SC-SUP-03152'
const ITEM = 'VTTH-GAUZE-5'

async function newFC(page, name, qty, price) {
  // Tạo via REST API resource — tương đương client-side createDoc
  return page.evaluate(async ({ supplier, num, qty, price, item }) => {
    const csrf = window.sc_csrf || document.querySelector('meta[name="csrf-token"]')?.content || ''
    const today = new Date()
    const validFrom = today.toISOString().slice(0, 10)
    const validTo = new Date(today.getFullYear() + 1, today.getMonth(), today.getDay()).toISOString().slice(0, 10)
    const uomRes = await fetch(`/api/method/frappe.client.get_value?doctype=SC%20Item&filters=${encodeURIComponent(JSON.stringify({name: item}))}&fieldname=uom`,
      { credentials: 'include' }).then(r => r.json())
    const uom = uomRes.message?.uom
    const body = {
      doctype: 'Framework Contract',
      supplier, contract_number: num,
      contract_date: validFrom, valid_from: validFrom, valid_to: validTo,
      payment_terms: 'Net 30',
      items: [{ doctype: 'FC Item', item_code: item, uom, contract_qty: qty, unit_price: price }],
    }
    const r = await fetch(`/api/resource/Framework%20Contract`, {
      method: 'POST', credentials: 'include',
      headers: { 'Content-Type': 'application/json', 'X-Frappe-CSRF-Token': csrf },
      body: JSON.stringify(body),
    })
    const d = await r.json()
    if (!r.ok) throw new Error(d.exception || JSON.stringify(d))
    return d.data
  }, { supplier: SUPPLIER, num: name, qty, price, item: ITEM })
}

export const tests = [
  {
    name: 'Tạo FC: auto-sum total_value từ items',
    run: async ({ page }) => {
      const num = `TEST-AUTOSUM-${rand()}`
      const fc = await newFC(page, num, 100, 5000)
      const expected = 100 * 5000
      if (Math.abs((fc.total_value || 0) - expected) > 1) {
        return { ok: false, detail: `total_value=${fc.total_value}, expected=${expected}` }
      }
      // Verify items[0].total_amount cũng được tính
      const ta = fc.items?.[0]?.total_amount || 0
      if (Math.abs(ta - expected) > 1) {
        return { ok: false, detail: `items[0].total_amount=${ta}, expected=${expected}` }
      }
      return { ok: true, detail: `${num}: total=${fc.total_value} = 100×5000 ✓` }
    },
  },
  {
    name: 'Tạo FC ghi lại owner = user hiện tại',
    run: async ({ page }) => {
      const num = `TEST-OWNER-${rand()}`
      const fc = await newFC(page, num, 50, 10000)
      const sess = await page.evaluate(async () => {
        const r = await fetch('/api/method/frappe.auth.get_logged_user', { credentials: 'include' })
        const d = await r.json()
        return d.message
      })
      if (fc.owner !== sess) {
        return { ok: false, detail: `owner=${fc.owner}, expected=${sess}` }
      }
      return { ok: true, detail: `owner=${fc.owner} ✓` }
    },
  },
  {
    name: 'Sửa FC khi Draft → tạo Version record (log)',
    run: async ({ page }) => {
      const num = `TEST-EDIT-${rand()}`
      const fc = await newFC(page, num, 10, 1000)
      // Update payment_terms
      await page.evaluate(async ({ name, newTerm }) => {
        const csrf = window.sc_csrf || document.querySelector('meta[name="csrf-token"]')?.content || ''
        const r = await fetch(`/api/resource/Framework%20Contract/${encodeURIComponent(name)}`, {
          method: 'PUT', credentials: 'include',
          headers: { 'Content-Type': 'application/json', 'X-Frappe-CSRF-Token': csrf },
          body: JSON.stringify({ payment_terms: newTerm }),
        })
        const d = await r.json()
        if (!r.ok) throw new Error(d.exception || JSON.stringify(d))
      }, { name: fc.name, newTerm: 'Net 60 — sửa lần 1' })
      // Pull log via custom endpoint
      const log = await apiCall(page, 'supplycore.api.frontend.get_doc_versions',
        { doctype: 'Framework Contract', name: fc.name })
      if (!Array.isArray(log) || log.length === 0) {
        return { ok: false, detail: `no version log found for ${fc.name}` }
      }
      const hasTerms = log.some(v => v.changed?.some(c => c.field === 'payment_terms'))
      return hasTerms
        ? { ok: true, detail: `${num}: ${log.length} version(s), bao gồm sửa payment_terms ✓` }
        : { ok: false, detail: `log có ${log.length} entry nhưng không thấy payment_terms` }
    },
  },
  {
    name: 'FC đã duyệt (Approved) → save bị chặn (SC-E-FC-LOCKED)',
    run: async ({ page }) => {
      const num = `TEST-LOCK-${rand()}`
      // Tạo FC dưới ngưỡng Executive (5tr) để chỉ qua Manager → Approved
      const fc = await newFC(page, num, 1, 5000000)
      try {
        await apiRunDocMethod(page, 'Framework Contract', fc.name, 'submit_for_review')
        await apiRunDocMethod(page, 'Framework Contract', fc.name,
          'approve_as_manager', { comment: 'auto-test' })
      } catch (e) {
        return { ok: false, detail: `cannot approve: ${e.message}` }
      }
      // Verify stage = Approved
      const after = await apiGetDoc(page, 'Framework Contract', fc.name)
      if (after.approval_stage !== 'Approved') {
        return { ok: false, detail: `stage=${after.approval_stage}, expected Approved` }
      }
      // Try sửa → phải bị chặn
      let blocked = false; let errMsg = ''
      try {
        await page.evaluate(async ({ name }) => {
          const csrf = window.sc_csrf || document.querySelector('meta[name="csrf-token"]')?.content || ''
          const r = await fetch(`/api/resource/Framework%20Contract/${encodeURIComponent(name)}`, {
            method: 'PUT', credentials: 'include',
            headers: { 'Content-Type': 'application/json', 'X-Frappe-CSRF-Token': csrf },
            body: JSON.stringify({ payment_terms: 'try-edit-after-approval' }),
          })
          const d = await r.json()
          if (!r.ok) throw new Error(d.exception || JSON.stringify(d._server_messages || d))
        }, { name: fc.name })
      } catch (e) {
        blocked = true
        errMsg = String(e.message || '')
      }
      if (!blocked) return { ok: false, detail: 'edit không bị chặn dù đã Approved' }
      if (!errMsg.includes('LOCKED') && !errMsg.toLowerCase().includes('duyệt')
          && !errMsg.toLowerCase().includes('approved')) {
        return { ok: false, detail: `bị chặn nhưng message không khớp: ${errMsg.slice(0, 200)}` }
      }
      return { ok: true, detail: `${num}: edit-after-approval bị chặn đúng SC-E-FC-LOCKED ✓` }
    },
  },
  {
    name: 'Attach file: upload_file endpoint + lưu URL vào FC',
    run: async ({ page }) => {
      const num = `TEST-ATTACH-${rand()}`
      const fc = await newFC(page, num, 5, 2000)
      // Upload 1 file text dummy + set vào field attachment (PDF dummy bytes fail pypdf parse)
      const uploaded = await page.evaluate(async () => {
        const csrf = window.sc_csrf || document.querySelector('meta[name="csrf-token"]')?.content || ''
        const blob = new Blob(['Hợp đồng bản mềm test'], { type: 'text/plain' })
        const fd = new FormData()
        fd.append('file', blob, 'test-contract.txt')
        fd.append('is_private', '0')
        fd.append('folder', 'Home/Attachments')
        const r = await fetch('/api/method/upload_file', {
          method: 'POST', credentials: 'include',
          headers: { 'X-Frappe-CSRF-Token': csrf, Accept: 'application/json' },
          body: fd,
        })
        const d = await r.json()
        if (!r.ok) throw new Error(d.exception || JSON.stringify(d))
        return d.message?.file_url
      })
      if (!uploaded) return { ok: false, detail: 'upload không trả file_url' }
      // Gán vào FC
      await page.evaluate(async ({ name, url }) => {
        const csrf = window.sc_csrf || document.querySelector('meta[name="csrf-token"]')?.content || ''
        const r = await fetch(`/api/resource/Framework%20Contract/${encodeURIComponent(name)}`, {
          method: 'PUT', credentials: 'include',
          headers: { 'Content-Type': 'application/json', 'X-Frappe-CSRF-Token': csrf },
          body: JSON.stringify({ attachment: url }),
        })
        const d = await r.json()
        if (!r.ok) throw new Error(d.exception || JSON.stringify(d))
      }, { name: fc.name, url: uploaded })
      const refetch = await apiGetDoc(page, 'Framework Contract', fc.name)
      if (refetch.attachment !== uploaded) {
        return { ok: false, detail: `attachment=${refetch.attachment}, expected=${uploaded}` }
      }
      return { ok: true, detail: `${num}: attached ${uploaded} ✓` }
    },
  },
  {
    name: 'SPA form: tạo FC mới hiển thị các field mới (UI smoke)',
    run: async ({ page, BASE, OUT, name }) => {
      await navigateTo(page, BASE, '/doc/Framework%20Contract/new')
      await page.waitForTimeout(1500)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      const html = await page.content()
      // Section header mới hiện ra
      if (!html.includes('Tệp đính kèm') && !html.includes('Bản mềm hợp đồng')) {
        return { ok: false, detail: 'Section Tệp đính kèm/Bản mềm không render' }
      }
      // Tổng giá trị hint
      if (!html.includes('Tự động tính')) {
        return { ok: false, detail: 'hint "Tự động tính" không render trên total_value' }
      }
      // Người tạo (chỉ khi name=new thì owner vẫn empty, nhưng hint hiện)
      if (!html.includes('Người tạo')) {
        return { ok: false, detail: 'field Người tạo không render' }
      }
      return { ok: true, detail: 'form mới hiển thị attach/người tạo/auto-sum ✓' }
    },
  },
]
