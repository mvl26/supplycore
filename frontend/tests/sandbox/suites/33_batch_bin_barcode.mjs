// Tạo lô / vị trí → tự sinh barcode tương ứng mã lô / mã vị trí.
//
// User: "Khi tạo lô đồng thời tạo 1 mã barcode tương ứng mã lô đó,
//         cả khi tạo vị trí cũng tạo barcode tương ứng mã vị trí.
//         Áp dụng cho tạo lô bình thường HOẶC tạo lô tự động ở phần tiếp nhận."

import { apiGetList, apiGetDoc, apiCall, navigateTo, rand } from '../helpers.mjs'

async function createDoc(page, doctype, body) {
  return page.evaluate(async ({ doctype, body }) => {
    const csrf = window.sc_csrf || document.querySelector('meta[name="csrf-token"]')?.content || ''
    const r = await fetch(`/api/resource/${encodeURIComponent(doctype)}`, {
      method: 'POST', credentials: 'include',
      headers: { 'Content-Type': 'application/json', 'X-Frappe-CSRF-Token': csrf },
      body: JSON.stringify({ doctype, ...body }),
    })
    const d = await r.json()
    if (!r.ok) throw new Error(d.exception || JSON.stringify(d._server_messages || d))
    return d.data
  }, { doctype, body })
}

export const tests = [
  {
    name: 'Tạo lô thường → barcode tự sinh = batch_id',
    run: async ({ page }) => {
      const items = await apiGetList(page, 'SC Item', {
        fields: ['name'], filters: [['has_batch_no', '=', 1]], limit: 1,
      })
      if (!items.length) return { ok: false, detail: 'No batch-tracked item' }
      const bid = `TEST-BC-${rand(6).toUpperCase()}`
      const batch = await createDoc(page, 'SC Batch', {
        batch_id: bid,
        item: items[0].name,
        expiry_date: '2027-12-31',
        manufacturing_date: '2026-01-01',
      })
      if (batch.barcode !== bid) {
        return { ok: false, detail: `barcode=${batch.barcode}, expected=${bid}` }
      }
      return { ok: true, detail: `${bid}: barcode tự sinh = batch_id ✓` }
    },
  },
  {
    name: 'Tạo lô với barcode tự nhập (GS1) → giữ nguyên không đè',
    run: async ({ page }) => {
      const items = await apiGetList(page, 'SC Item', {
        fields: ['name'], filters: [['has_batch_no', '=', 1]], limit: 1,
      })
      if (!items.length) return { ok: false, detail: 'No batch-tracked item' }
      const bid = `TEST-BC-${rand(6).toUpperCase()}`
      const customBc = `8935001${rand(6)}`
      const batch = await createDoc(page, 'SC Batch', {
        batch_id: bid,
        barcode: customBc,
        item: items[0].name,
        expiry_date: '2027-12-31',
      })
      if (batch.barcode !== customBc) {
        return { ok: false, detail: `barcode=${batch.barcode}, expected custom ${customBc}` }
      }
      return { ok: true, detail: `barcode GS1 tự nhập "${customBc}" giữ nguyên ✓` }
    },
  },
  {
    name: 'Tạo vị trí (Bin Location) → barcode tự sinh = bin_code',
    run: async ({ page }) => {
      const whs = await apiGetList(page, 'SC Warehouse', {
        fields: ['name'], filters: [['is_group', '=', 0]], limit: 1,
      })
      if (!whs.length) return { ok: false, detail: 'No warehouse' }
      const binCode = `TEST-BIN-${rand(6).toUpperCase()}`
      const bin = await createDoc(page, 'Bin Location', {
        warehouse: whs[0].name,
        bin_code: binCode,
      })
      if (bin.barcode !== binCode) {
        return { ok: false, detail: `barcode=${bin.barcode}, expected=${binCode}` }
      }
      return { ok: true, detail: `${binCode}: barcode tự sinh = bin_code ✓` }
    },
  },
  {
    name: 'Tạo lô tự động ở tiếp nhận (PR submit) → batch có barcode',
    run: async ({ page }) => {
      const items = await apiGetList(page, 'SC Item', {
        fields: ['name', 'uom'], filters: [['has_batch_no', '=', 1]], limit: 1,
      })
      const whs = await apiGetList(page, 'SC Warehouse', {
        fields: ['name'], filters: [['is_group', '=', 0]], limit: 1,
      })
      const sups = await apiGetList(page, 'SC Supplier', {
        fields: ['name'], filters: [['disabled', '=', 0]], limit: 1,
      })
      if (!items.length || !whs.length || !sups.length) {
        return { ok: false, detail: 'Thiếu item/warehouse/supplier' }
      }
      const it = items[0]
      // Tạo PR không PO, item batch-tracked, có expiry → submit sẽ auto tạo lô
      const pr = await createDoc(page, 'SC Purchase Receipt', {
        supplier: sups[0].name,
        posting_date: '2026-05-20',
        to_warehouse: whs[0].name,
        is_return: 0,
        qc_required: 0,
        no_po_reason: 'Auto-test barcode lô tự động',
        items: [{
          doctype: 'SC Purchase Receipt Item',
          item: it.name, uom: it.uom,
          qty: 10, rate: 1000,
          warehouse: whs[0].name,
          supplier_batch_no: `LOTBC-${rand(5)}`,
          expiry_date: '2027-10-31',
        }],
      })
      // Submit PR → on_submit gọi _create_batches_if_needed
      await apiCall(page, 'supplycore.api.frontend.submit_doc', {
        doctype: 'SC Purchase Receipt', name: pr.name,
      })
      // Re-fetch PR → lấy batch_no đã gán
      const prAfter = await apiGetDoc(page, 'SC Purchase Receipt', pr.name)
      const batchNo = prAfter.items?.[0]?.batch_no
      if (!batchNo) {
        return { ok: false, detail: `PR ${pr.name} item không được gán batch_no` }
      }
      // Fetch batch → kiểm barcode
      const batch = await apiGetDoc(page, 'SC Batch', batchNo)
      if (!batch.barcode) {
        return { ok: false, detail: `Lô tự động ${batchNo} KHÔNG có barcode` }
      }
      if (batch.barcode !== batch.batch_id) {
        return { ok: false, detail: `barcode=${batch.barcode} != batch_id=${batch.batch_id}` }
      }
      return { ok: true, detail: `PR ${pr.name} → lô ${batchNo}, barcode="${batch.barcode}" ✓` }
    },
  },
  {
    name: 'UI: form SC Batch hiển thị field Barcode lô',
    run: async ({ page, BASE, OUT, name }) => {
      await navigateTo(page, BASE, '/doc/SC%20Batch/new')
      await page.waitForTimeout(1500)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      const html = await page.content()
      if (!html.includes('Barcode lô')) {
        return { ok: false, detail: 'Field "Barcode lô" không render trên form' }
      }
      return { ok: true, detail: 'Form SC Batch có field "Barcode lô" ✓' }
    },
  },
  {
    name: 'List SC Batch có cột Barcode + mọi lô đều có barcode',
    run: async ({ page }) => {
      const batches = await apiGetList(page, 'SC Batch', {
        fields: ['name', 'batch_id', 'barcode'], limit: 50,
      })
      if (!batches.length) return { ok: false, detail: 'No batches' }
      const missing = batches.filter(b => !b.barcode)
      if (missing.length) {
        return { ok: false, detail: `${missing.length}/${batches.length} lô thiếu barcode: ${missing.slice(0,3).map(b => b.name)}` }
      }
      return { ok: true, detail: `${batches.length}/${batches.length} lô đều có barcode ✓` }
    },
  },
  {
    name: 'UI: SC Batch detail render mã vạch QUÉT ĐƯỢC (SVG bars)',
    run: async ({ page, BASE, OUT, name }) => {
      const batches = await apiGetList(page, 'SC Batch', {
        fields: ['name'], limit: 1, order_by: 'creation desc',
      })
      if (!batches.length) return { ok: false, detail: 'No batches' }
      await navigateTo(page, BASE, `/doc/SC%20Batch/${encodeURIComponent(batches[0].name)}`)
      await page.waitForTimeout(2000)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      // Panel tiêu đề
      const html = await page.content()
      if (!html.includes('Mã vạch')) {
        return { ok: false, detail: 'Panel "Mã vạch" không render' }
      }
      // jsbarcode render <svg> chứa nhiều <rect> (các vạch) — đếm rect
      const bars = await page.locator('svg rect').count()
      if (bars < 10) {
        return { ok: false, detail: `Mã vạch chỉ có ${bars} vạch — không phải barcode hợp lệ` }
      }
      // Nút In nhãn
      const printBtn = await page.locator('button:has-text("In nhãn")').count()
      if (!printBtn) return { ok: false, detail: 'Thiếu nút "In nhãn"' }
      return { ok: true, detail: `Batch ${batches[0].name}: barcode SVG ${bars} vạch + nút In nhãn ✓` }
    },
  },
  {
    name: 'UI: Bin Location detail render mã vạch quét được',
    run: async ({ page, BASE, OUT, name }) => {
      const bins = await apiGetList(page, 'Bin Location', {
        fields: ['name'], limit: 1, order_by: 'creation desc',
      })
      if (!bins.length) return { ok: false, detail: 'No bin locations' }
      await navigateTo(page, BASE, `/doc/Bin%20Location/${encodeURIComponent(bins[0].name)}`)
      await page.waitForTimeout(2000)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      const html = await page.content()
      if (!html.includes('Mã vạch')) {
        return { ok: false, detail: 'Panel "Mã vạch" không render' }
      }
      const bars = await page.locator('svg rect').count()
      if (bars < 10) {
        return { ok: false, detail: `Mã vạch chỉ có ${bars} vạch` }
      }
      return { ok: true, detail: `Bin ${bins[0].name}: barcode SVG ${bars} vạch ✓` }
    },
  },
]
