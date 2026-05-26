// Suite 103: QA v3 round 4 — SC Purchase Receipt row required (BUG-004/005)
//
// Cặp validation trên `before_submit` của SC Purchase Receipt cho dòng item
// có `has_batch_no = 1` (xem sc_purchase_receipt.py:67-95):
//   - SC-E013 MANUFACTURER_REQUIRED: thiếu 'Nhà sản xuất'
//   - SC-E014 SUPPLIER_BATCH_REQUIRED: thiếu 'Số lô NCC'
//
// Suite 100 chỉ verify field tồn tại trong meta. Suite này thực sự build PR
// draft → submit → xác nhận server reject với đúng error code, rồi cleanup.

const todayISO = () => new Date().toISOString().slice(0, 10)
const futureISO = (days) => new Date(Date.now() + days * 86400000).toISOString().slice(0, 10)

async function pickFixture(page) {
  const csrf = await page.evaluate(() => window.sc_csrf)
  return page.evaluate(async ({ csrf }) => {
    const q = async (url) => {
      const r = await fetch(url, { credentials: 'include', headers: { 'X-Frappe-CSRF-Token': csrf } })
      return (await r.json()).message || []
    }
    const items = await q('/api/method/frappe.client.get_list?doctype=SC Item'
      + '&fields=["name","uom"]'
      + '&filters=' + encodeURIComponent(JSON.stringify([['has_batch_no', '=', 1], ['disabled', '=', 0]]))
      + '&limit=1')
    const whs = await q('/api/method/frappe.client.get_list?doctype=SC Warehouse'
      + '&fields=["name"]'
      + '&filters=' + encodeURIComponent(JSON.stringify([['is_group', '=', 0], ['disabled', '=', 0]]))
      + '&limit=1')
    const sups = await q('/api/method/frappe.client.get_list?doctype=SC Supplier'
      + '&fields=["name"]'
      + '&filters=' + encodeURIComponent(JSON.stringify([['disabled', '=', 0]]))
      + '&limit=1')
    return {
      item: items[0]?.name, uom: items[0]?.uom,
      warehouse: whs[0]?.name, supplier: sups[0]?.name,
    }
  }, { csrf })
}

async function createPrDraft(page, payload) {
  const csrf = await page.evaluate(() => window.sc_csrf)
  return page.evaluate(async ({ payload, csrf }) => {
    const r = await fetch('/api/resource/SC Purchase Receipt', {
      method: 'POST', credentials: 'include',
      headers: { 'Content-Type': 'application/json', 'X-Frappe-CSRF-Token': csrf },
      body: JSON.stringify(payload),
    })
    const d = await r.json()
    return { status: r.status, name: d.data?.name, exc: d.exception || '', msg: (d._server_messages || '').slice(0, 300) }
  }, { payload, csrf })
}

async function submitPr(page, name) {
  const csrf = await page.evaluate(() => window.sc_csrf)
  return page.evaluate(async ({ name, csrf }) => {
    const r = await fetch('/api/method/supplycore.api.frontend.submit_doc', {
      method: 'POST', credentials: 'include',
      headers: { 'Content-Type': 'application/json', 'X-Frappe-CSRF-Token': csrf },
      body: JSON.stringify({ doctype: 'SC Purchase Receipt', name }),
    })
    const d = await r.json()
    return { status: r.status, exc: d.exception || '', msg: (d._server_messages || '').slice(0, 300) }
  }, { name, csrf })
}

async function deletePr(page, name) {
  if (!name) return
  const csrf = await page.evaluate(() => window.sc_csrf)
  await page.evaluate(async ({ name, csrf }) => {
    await fetch(`/api/resource/SC Purchase Receipt/${encodeURIComponent(name)}`, {
      method: 'DELETE', credentials: 'include',
      headers: { 'X-Frappe-CSRF-Token': csrf },
    }).catch(() => null)
  }, { name, csrf })
}

function buildItem({ item, uom, supplierBatch, manufacturer }) {
  return {
    item, qty: 1, rate: 1000, uom,
    expiry_date: futureISO(180),
    supplier_batch_no: supplierBatch || '',
    manufacturer: manufacturer || '',
  }
}

export const tests = [
  // ---------------------------------------------------------------------
  // v3-M3-12 (BUG-004): PR submit thiếu manufacturer → SC-E013
  // ---------------------------------------------------------------------
  {
    name: 'v3-M3-12: PR submit thiếu manufacturer → SC-E013 MANUFACTURER_REQUIRED',
    run: async ({ page }) => {
      const fx = await pickFixture(page)
      if (!fx.item || !fx.warehouse || !fx.supplier || !fx.uom) {
        return { ok: 'skip', detail: `Fixture thiếu (item=${fx.item} wh=${fx.warehouse} sup=${fx.supplier} uom=${fx.uom})` }
      }
      const draft = await createPrDraft(page, {
        doctype: 'SC Purchase Receipt',
        supplier: fx.supplier,
        posting_date: todayISO(),
        to_warehouse: fx.warehouse,
        no_po_reason: 'TEST FIXTURE — không có PO (auto-tests SC-E013)',
        items: [buildItem({ item: fx.item, uom: fx.uom, supplierBatch: 'TEST-LOT-E013', manufacturer: '' })],
      })
      if (!draft.name) {
        return { ok: false, detail: `Không tạo được PR draft: status=${draft.status} exc="${draft.exc.slice(0, 120)}"` }
      }
      const sub = await submitPr(page, draft.name)
      await deletePr(page, draft.name)
      const blob = `${sub.exc} ${sub.msg}`
      const ok = sub.status >= 400 && (blob.includes('SC-E013') || blob.includes('MANUFACTURER_REQUIRED'))
      return ok
        ? { ok: true, detail: `${draft.name} reject SC-E013 (HTTP ${sub.status})` }
        : { ok: false, detail: `status=${sub.status} exc="${sub.exc.slice(0, 100)}" msg="${sub.msg.slice(0, 100)}"` }
    },
  },

  // ---------------------------------------------------------------------
  // v3-M3-13 (BUG-005): PR submit thiếu supplier_batch_no → SC-E014
  // ---------------------------------------------------------------------
  {
    name: 'v3-M3-13: PR submit thiếu supplier_batch_no → SC-E014 SUPPLIER_BATCH_REQUIRED',
    run: async ({ page }) => {
      const fx = await pickFixture(page)
      if (!fx.item || !fx.warehouse || !fx.supplier || !fx.uom) {
        return { ok: 'skip', detail: `Fixture thiếu (item=${fx.item} wh=${fx.warehouse} sup=${fx.supplier} uom=${fx.uom})` }
      }
      const draft = await createPrDraft(page, {
        doctype: 'SC Purchase Receipt',
        supplier: fx.supplier,
        posting_date: todayISO(),
        to_warehouse: fx.warehouse,
        no_po_reason: 'TEST FIXTURE — không có PO (auto-tests SC-E014)',
        items: [buildItem({ item: fx.item, uom: fx.uom, supplierBatch: '', manufacturer: 'TEST-MFR-E014' })],
      })
      if (!draft.name) {
        return { ok: false, detail: `Không tạo được PR draft: status=${draft.status} exc="${draft.exc.slice(0, 120)}"` }
      }
      const sub = await submitPr(page, draft.name)
      await deletePr(page, draft.name)
      const blob = `${sub.exc} ${sub.msg}`
      const ok = sub.status >= 400 && (blob.includes('SC-E014') || blob.includes('SUPPLIER_BATCH_REQUIRED'))
      return ok
        ? { ok: true, detail: `${draft.name} reject SC-E014 (HTTP ${sub.status})` }
        : { ok: false, detail: `status=${sub.status} exc="${sub.exc.slice(0, 100)}" msg="${sub.msg.slice(0, 100)}"` }
    },
  },
]
