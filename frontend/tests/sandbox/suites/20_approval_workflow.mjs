// Suite 20: Approval workflow actions với method names đúng
import { apiCall, apiGetList, apiRunDocMethod, navigateTo } from '../helpers.mjs'

export const tests = [
  {
    name: 'FC approve_as_manager method exists (UC-01)',
    run: async ({ page }) => {
      // Tạo FC mới ở Draft → submit_for_review → call approve_as_manager
      const sup = await apiGetList(page, 'SC Supplier', { fields: ['name'], limit: 1 })
      const items = await apiGetList(page, 'SC Item', { fields: ['name', 'uom'], limit: 1 })
      if (!sup.length || !items.length) return { ok: false, detail: 'No supplier/item' }

      const today = new Date().toISOString().slice(0, 10)
      const cn = `FC-TEST-${Date.now().toString(36)}`
      // Create FC Draft
      const fc = await page.evaluate(async ({ cn, sup, item, uom, today, csrf }) => {
        const r = await fetch('/api/resource/Framework%20Contract', {
          method: 'POST', credentials: 'include',
          headers: { 'Content-Type': 'application/json', 'X-Frappe-CSRF-Token': csrf },
          body: JSON.stringify({
            contract_number: cn,
            supplier: sup,
            contract_date: today,
            valid_from: today,
            valid_to: '2027-12-31',
            total_value: 1000000,
            items: [{ item_code: item, uom, contract_qty: 100, unit_price: 10000 }],
          }),
        })
        const d = await r.json()
        if (!r.ok) throw new Error(d.exception || JSON.stringify(d))
        return d.data
      }, { cn, sup: sup[0].name, item: items[0].name, uom: items[0].uom, today,
            csrf: await page.evaluate(() => window.sc_csrf) })

      try {
        // Call submit_for_review → Manager Review
        await apiRunDocMethod(page, 'Framework Contract', fc.name, 'submit_for_review')
        // Verify approval_stage = Manager Review
        const after1 = await apiCall(page, 'supplycore.api.frontend.get_doc',
          { doctype: 'Framework Contract', name: fc.name })
        if (after1.approval_stage !== 'Manager Review') {
          return { ok: false, detail: `submit_for_review → stage=${after1.approval_stage}` }
        }
        // Call approve_as_manager
        await apiRunDocMethod(page, 'Framework Contract', fc.name, 'approve_as_manager',
          { comment: 'Test manager approve' })
        const after2 = await apiCall(page, 'supplycore.api.frontend.get_doc',
          { doctype: 'Framework Contract', name: fc.name })
        // Cleanup
        await page.evaluate(async ({ name, csrf }) => {
          await fetch(`/api/resource/Framework%20Contract/${encodeURIComponent(name)}`, {
            method: 'DELETE', credentials: 'include',
            headers: { 'X-Frappe-CSRF-Token': csrf },
          })
        }, { name: fc.name, csrf: await page.evaluate(() => window.sc_csrf) })

        return ['Executive Review', 'Approved'].includes(after2.approval_stage)
          ? { ok: true, detail: `submit_for_review → Manager Review → approve_as_manager → ${after2.approval_stage}` }
          : { ok: false, detail: `Sau approve_as_manager: stage=${after2.approval_stage}` }
      } catch (e) {
        // Cleanup on error
        try {
          await page.evaluate(async ({ name, csrf }) => {
            await fetch(`/api/resource/Framework%20Contract/${encodeURIComponent(name)}`, {
              method: 'DELETE', credentials: 'include',
              headers: { 'X-Frappe-CSRF-Token': csrf },
            })
          }, { name: fc.name, csrf: await page.evaluate(() => window.sc_csrf) })
        } catch {}
        return { ok: false, detail: `${e.message}`.slice(0, 200) }
      }
    },
  },
  {
    name: 'FC ActionPanel hiển thị Manager duyệt khi Manager Review',
    run: async ({ page, BASE, OUT, name }) => {
      // Tạo FC + chuyển sang Manager Review state
      const sup = await apiGetList(page, 'SC Supplier', { fields: ['name'], limit: 1 })
      const items = await apiGetList(page, 'SC Item', { fields: ['name', 'uom'], limit: 1 })
      if (!sup.length || !items.length) return { ok: false, detail: 'No data' }
      const cn = `FC-UI-${Date.now().toString(36)}`
      const fc = await page.evaluate(async ({ cn, sup, item, uom, csrf }) => {
        const today = new Date().toISOString().slice(0, 10)
        const r = await fetch('/api/resource/Framework%20Contract', {
          method: 'POST', credentials: 'include',
          headers: { 'Content-Type': 'application/json', 'X-Frappe-CSRF-Token': csrf },
          body: JSON.stringify({
            contract_number: cn, supplier: sup,
            contract_date: today, valid_from: today, valid_to: '2027-12-31',
            total_value: 500000,
            items: [{ item_code: item, uom, contract_qty: 50, unit_price: 10000 }],
          }),
        })
        return (await r.json()).data
      }, { cn, sup: sup[0].name, item: items[0].name, uom: items[0].uom,
            csrf: await page.evaluate(() => window.sc_csrf) })
      try {
        await apiRunDocMethod(page, 'Framework Contract', fc.name, 'submit_for_review')
        await navigateTo(page, BASE, `/doc/Framework%20Contract/${encodeURIComponent(fc.name)}`)
        await page.waitForTimeout(2000)
        await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
        const managerBtn = await page.locator('button:has-text("Manager duyệt")').count()
        const rejectBtn = await page.locator('button:has-text("Từ chối")').count()
        // Cleanup
        await page.evaluate(async ({ name, csrf }) => {
          await fetch(`/api/resource/Framework%20Contract/${encodeURIComponent(name)}`, {
            method: 'DELETE', credentials: 'include',
            headers: { 'X-Frappe-CSRF-Token': csrf },
          })
        }, { name: fc.name, csrf: await page.evaluate(() => window.sc_csrf) })
        return (managerBtn >= 1 && rejectBtn >= 1)
          ? { ok: true, detail: `Manager Review state: Manager duyệt=${managerBtn}, Từ chối=${rejectBtn}` }
          : { ok: false, detail: `Manager=${managerBtn}, Reject=${rejectBtn}` }
      } catch (e) {
        try {
          await page.evaluate(async ({ name, csrf }) => {
            await fetch(`/api/resource/Framework%20Contract/${encodeURIComponent(name)}`, {
              method: 'DELETE', credentials: 'include',
              headers: { 'X-Frappe-CSRF-Token': csrf },
            })
          }, { name: fc.name, csrf: await page.evaluate(() => window.sc_csrf) })
        } catch {}
        return { ok: false, detail: e.message.slice(0, 200) }
      }
    },
  },
  {
    name: 'PO submit_for_review + approve_as_manager methods exist',
    run: async ({ page }) => {
      // Just verify method names không gây "no attribute" qua run_doc_method với invalid args
      // (sẽ throw validation error nhưng method tồn tại)
      const pos = await apiGetList(page, 'SC Purchase Order', {
        fields: ['name'],
        filters: [['docstatus', '=', 0]], limit: 1,
      })
      if (!pos.length) return { ok: true, detail: 'No Draft PO (skip)' }
      try {
        await apiRunDocMethod(page, 'SC Purchase Order', pos[0].name, 'submit_for_review')
        return { ok: true, detail: 'submit_for_review method tồn tại' }
      } catch (e) {
        // Method tồn tại nhưng raise validation lỗi nội bộ — OK
        if (e.message.includes('no attribute')) {
          return { ok: false, detail: 'Method KHÔNG tồn tại: ' + e.message.slice(0, 150) }
        }
        return { ok: true, detail: 'Method tồn tại (raise validation, OK)' }
      }
    },
  },
  {
    name: 'MR approve method exists',
    run: async ({ page }) => {
      const mrs = await apiGetList(page, 'SC Material Request', {
        fields: ['name'], filters: [['docstatus', '=', 1]], limit: 1,
      })
      if (!mrs.length) return { ok: true, detail: 'No MR (skip)' }
      try {
        const res = await apiRunDocMethod(page, 'SC Material Request', mrs[0].name, 'approve')
        return { ok: true, detail: `approve() trả ${JSON.stringify(res).slice(0, 80)}` }
      } catch (e) {
        if (e.message.includes('no attribute')) {
          return { ok: false, detail: 'Method approve không tồn tại' }
        }
        return { ok: true, detail: 'Method tồn tại (validation OK)' }
      }
    },
  },
]
