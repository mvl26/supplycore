// Suite 33: Verify qua HTTP thật — LƯU phiếu QC (không submit) là áp kết quả.
// + xác nhận khoá SC-E034 sau khi đã kết luận. Chạy qua gunicorn live.
const ITEM = '2024BD01', UOM = 'Viên', SUP = 'SC-SUP-03156', WH = 'Kho Hóa chất sinh phẩm'

async function rpc(page, method, body) {
  return page.evaluate(async ({ method, body }) => {
    const r = await fetch(`/api/method/${method}`, {
      method: 'POST', credentials: 'include',
      headers: { 'Content-Type': 'application/json', 'X-Frappe-CSRF-Token': window.sc_csrf || '', Accept: 'application/json' },
      body: JSON.stringify(body),
    })
    const d = await r.json().catch(() => ({}))
    if (!r.ok) throw new Error(d.exception || d._server_messages || `HTTP ${r.status}`)
    return d.message
  }, { method, body })
}

export const tests = [
  {
    name: 'LƯU QC Accepted (không submit) → Batch.qc_status=Accepted + PR.qc_status=Pass (HTTP)',
    run: async ({ page, BASE, OUT, name }) => {
      const today = new Date().toISOString().slice(0, 10)
      let prName = null
      try {
        // 1. Tạo PR (no PO) + submit → auto QI
        const pr = await page.evaluate(async ({ ITEM, UOM, SUP, WH, today }) => {
          const r = await fetch('/api/resource/SC%20Purchase%20Receipt', {
            method: 'POST', credentials: 'include',
            headers: { 'Content-Type': 'application/json', 'X-Frappe-CSRF-Token': window.sc_csrf || '' },
            body: JSON.stringify({
              supplier: SUP, posting_date: today, to_warehouse: WH, qc_required: 1,
              no_po_reason: 'QC HTTP verify',
              items: [{ item: ITEM, qty: 10, uom: UOM, rate: 5000, warehouse: WH,
                        supplier_batch_no: 'LOT-HTTP-QC', expiry_date: '2027-12-31', manufacturing_date: today }],
            }),
          })
          const d = await r.json(); if (!r.ok) throw new Error(d.exception || JSON.stringify(d)); return d.data
        }, { ITEM, UOM, SUP, WH, today })
        prName = pr.name
        await rpc(page, 'frappe.client.submit', { doc: JSON.stringify({ ...pr, docstatus: 0 }) })

        // 2. Lấy QI auto-tạo (Draft, Pending)
        const qis = await rpc(page, 'frappe.client.get_list', {
          doctype: 'SC Quality Inspection', filters: { purchase_receipt: prName },
          fields: ['name'], limit_page_length: 1,
        })
        if (!qis || !qis.length) return { ok: false, detail: 'PR không auto-tạo QI' }
        const qiName = qis[0].name

        // 3. GET QI đầy đủ → set readings Accepted → LƯU (PUT, KHÔNG submit)
        const qiDoc = await page.evaluate(async (qiName) => {
          const r = await fetch(`/api/resource/SC%20Quality%20Inspection/${encodeURIComponent(qiName)}`, { credentials: 'include' })
          return (await r.json()).data
        }, qiName)
        const readings = (qiDoc.readings || []).map(rd => ({ ...rd, status: 'Accepted' }))
        const saved = await page.evaluate(async ({ qiName, readings }) => {
          const r = await fetch(`/api/resource/SC%20Quality%20Inspection/${encodeURIComponent(qiName)}`, {
            method: 'PUT', credentials: 'include',
            headers: { 'Content-Type': 'application/json', 'X-Frappe-CSRF-Token': window.sc_csrf || '' },
            body: JSON.stringify({ readings, overall_status: 'Accepted' }),
          })
          const d = await r.json(); if (!r.ok) throw new Error(d.exception || JSON.stringify(d)); return d.data
        }, { qiName, readings })

        // 4. Kiểm tra hiệu lực: Batch.qc_status + PR.qc_status
        const batchName = saved.batch
        const batchQc = batchName ? await rpc(page, 'frappe.client.get_value', {
          doctype: 'SC Batch', filters: { name: batchName }, fieldname: 'qc_status' }) : null
        const prQc = await rpc(page, 'frappe.client.get_value', {
          doctype: 'SC Purchase Receipt', filters: { name: prName }, fieldname: 'qc_status' })
        await page.screenshot({ path: `${OUT}/${name}.png` })

        const okBatch = batchQc && batchQc.qc_status === 'Accepted'
        const okPr = prQc && prQc.qc_status === 'Pass'
        if (!okBatch || !okPr) {
          return { ok: false, detail: `Batch.qc=${batchQc?.qc_status} PR.qc=${prQc?.qc_status} (mong Accepted/Pass)` }
        }

        // 5. Khoá SC-E034: sửa lại QC đã kết luận (doc new-model docstatus=0) qua HTTP → chặn
        let locked = false
        try {
          await page.evaluate(async (qiName) => {
            const r = await fetch(`/api/resource/SC%20Quality%20Inspection/${encodeURIComponent(qiName)}`, {
              method: 'PUT', credentials: 'include',
              headers: { 'Content-Type': 'application/json', 'X-Frappe-CSRF-Token': window.sc_csrf || '' },
              body: JSON.stringify({ overall_status: 'Rejected' }),
            })
            const d = await r.json(); if (!r.ok) throw new Error(d.exception || JSON.stringify(d))
          }, qiName)
        } catch (e) {
          locked = /SC-E034|QC_LOCKED/.test(String(e.message || e))
        }
        await page.screenshot({ path: `${OUT}/${name}.png` })
        if (!locked) return { ok: false, detail: 'Áp kết quả OK nhưng KHÔNG khoá sau kết luận (SC-E034)' }
        return { ok: true, detail: `docstatus=${saved.docstatus} (không submit) → Batch=Accepted, PR=Pass; sửa lại bị chặn SC-E034` }
      } catch (e) {
        return { ok: false, detail: 'Lỗi: ' + String(e.message || e).slice(0, 200) }
      } finally {
        // Cleanup: cancel PR (đảo SLE) → xoá QI/PR. Bỏ qua lỗi cleanup.
        if (prName) {
          try {
            const full = await page.evaluate(async (prName) => {
              const r = await fetch(`/api/resource/SC%20Purchase%20Receipt/${encodeURIComponent(prName)}`, { credentials: 'include' })
              return (await r.json()).data
            }, prName)
            if (full?.docstatus === 1) await rpc(page, 'frappe.client.cancel', { doctype: 'SC Purchase Receipt', name: prName })
          } catch (e) { /* ignore */ }
        }
      }
    },
  },
]
