// Suite 31: Verify qua HTTP thật — duyệt FC với comment NGẮN không còn bị chặn
// (fix bỏ rule 10 ký tự / SC-E026). Chạy qua gunicorn đang phục vụ.
import { apiCall, apiGetList, apiRunDocMethod } from '../helpers.mjs'

export const tests = [
  {
    name: 'approve_as_manager + approve_as_executive với comment ngắn (HTTP)',
    run: async ({ page }) => {
      const sup = await apiGetList(page, 'SC Supplier', { fields: ['name'], limit: 1 })
      const items = await apiGetList(page, 'SC Item', { fields: ['name', 'uom'], limit: 1 })
      if (!sup.length || !items.length) return { ok: false, detail: 'No supplier/item' }

      const csrf = await page.evaluate(() => window.sc_csrf)
      const today = new Date().toISOString().slice(0, 10)
      const cn = `FC-SHORT-HTTP-${Date.now().toString(36)}`

      // Tạo FC Draft (total >= 100tr để ép qua Executive Review → test cả 2 cấp)
      const fc = await page.evaluate(async ({ cn, sup, item, uom, today, csrf }) => {
        const r = await fetch('/api/resource/Framework%20Contract', {
          method: 'POST', credentials: 'include',
          headers: { 'Content-Type': 'application/json', 'X-Frappe-CSRF-Token': csrf },
          body: JSON.stringify({
            contract_number: cn, supplier: sup, contract_date: today,
            valid_from: today, valid_to: '2028-12-31',
            items: [{ item_code: item, uom, contract_qty: 100, unit_price: 2000000 }],
          }),
        })
        const d = await r.json()
        if (!r.ok) throw new Error(d.exception || JSON.stringify(d))
        return d.data
      }, { cn, sup: sup[0].name, item: items[0].name, uom: items[0].uom, today, csrf })

      const cleanup = async () => {
        await page.evaluate(async ({ name, csrf }) => {
          await fetch(`/api/resource/Framework%20Contract/${encodeURIComponent(name)}`, {
            method: 'DELETE', credentials: 'include', headers: { 'X-Frappe-CSRF-Token': csrf },
          })
        }, { name: fc.name, csrf })
      }

      try {
        await apiRunDocMethod(page, 'Framework Contract', fc.name, 'submit_for_review')
        const s1 = await apiCall(page, 'supplycore.api.frontend.get_doc',
          { doctype: 'Framework Contract', name: fc.name })
        if (s1.approval_stage !== 'Manager Review') {
          await cleanup(); return { ok: false, detail: `submit_for_review → ${s1.approval_stage}` }
        }

        // Comment 2 ký tự — trước đây ném SC-E026
        await apiRunDocMethod(page, 'Framework Contract', fc.name, 'approve_as_manager', { comment: 'ok' })
        const s2 = await apiCall(page, 'supplycore.api.frontend.get_doc',
          { doctype: 'Framework Contract', name: fc.name })
        if (!['Executive Review', 'Approved'].includes(s2.approval_stage)) {
          await cleanup(); return { ok: false, detail: `manager('ok') → ${s2.approval_stage}` }
        }

        let execNote = ''
        if (s2.approval_stage === 'Executive Review') {
          await apiRunDocMethod(page, 'Framework Contract', fc.name, 'approve_as_executive', { comment: 'x' })
          const s3 = await apiCall(page, 'supplycore.api.frontend.get_doc',
            { doctype: 'Framework Contract', name: fc.name })
          if (s3.approval_stage !== 'Approved') {
            await cleanup(); return { ok: false, detail: `executive('x') → ${s3.approval_stage}` }
          }
          execNote = " + executive('x')→Approved"
        }

        await cleanup()
        return { ok: true, detail: `manager('ok')→${s2.approval_stage}${execNote}` }
      } catch (e) {
        await cleanup()
        const msg = String(e.message || e)
        if (msg.includes('SC-E026') || msg.includes('APPROVAL_COMMENT_TOO_SHORT')) {
          return { ok: false, detail: 'RULE 10 KÝ TỰ VẪN CÒN SỐNG (workers chưa reload?): ' + msg.slice(0, 120) }
        }
        return { ok: false, detail: 'Lỗi khác: ' + msg.slice(0, 160) }
      }
    },
  },
]
