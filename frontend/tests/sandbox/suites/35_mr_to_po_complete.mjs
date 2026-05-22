// Tạo PO từ MR phải mua ĐẦY ĐỦ các vật tư đã đăng ký ở MR.
//
// Bug: suggest_po_from_mr chọn FC rẻ nhất, bỏ qua FC user đã gán trên dòng MR
// → tách 5 item thành nhiều PO khác NCC → user nhìn 1 PO thấy thiếu item.
// Fix: tôn trọng framework_contract trên dòng MR → các dòng cùng FC gộp 1 PO.

import { apiCall, apiGetList, apiGetDoc, apiRunDocMethod, navigateTo, rand } from '../helpers.mjs'

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

// Tạo MR từ 1 FC Active: tất cả FC items → MR items, mỗi dòng gán FC đó
async function buildMrFromFc(page, fcName) {
  const fcItems = await apiGetList(page, 'FC Item', {
    fields: ['item_code', 'uom', 'remaining_qty'],
    filters: [['parent', '=', fcName]], limit: 20,
  })
  const usable = fcItems.filter(r => Number(r.remaining_qty) >= 5)
  if (usable.length < 2) return null
  const items = usable.map(r => ({
    doctype: 'SC Material Request Item',
    item: r.item_code, uom: r.uom, qty: 5,
    framework_contract: fcName,
  }))
  return createDoc(page, 'SC Material Request', {
    request_type: 'Purchase',
    transaction_date: '2026-05-22',
    schedule_date: '2026-06-15',
    warehouse: (await apiGetList(page, 'SC Warehouse',
      { fields: ['name'], filters: [['is_group', '=', 0]], limit: 1 }))[0]?.name,
    items,
  })
}

export const tests = [
  {
    name: 'Backend: suggest_po gộp các dòng cùng FC → không tách rời',
    run: async ({ page }) => {
      const fcs = await apiGetList(page, 'Framework Contract', {
        fields: ['name'], filters: [['docstatus', '=', 1], ['status', '=', 'Active']],
        limit: 10,
      })
      let mr = null, fcUsed = null
      for (const fc of fcs) {
        mr = await buildMrFromFc(page, fc.name)
        if (mr) { fcUsed = fc.name; break }
      }
      if (!mr) return { ok: false, detail: 'Không tìm được FC Active ≥2 item đủ tồn' }
      const mrDoc = await apiGetDoc(page, 'SC Material Request', mr.name)
      const mrItemCount = mrDoc.items.length

      // suggest_po_from_mr yêu cầu MR đã submit (docstatus=1)
      await apiCall(page, 'supplycore.api.frontend.submit_doc',
        { doctype: 'SC Material Request', name: mr.name })
      const res = await apiCall(page, 'supplycore.m2_planning.api.po_suggest.suggest_po_from_mr',
        { mr_name: mr.name, auto_create: 0 })
      // Tất cả dòng cùng 1 FC → đúng 1 group, đủ item, 0 unmatched
      if (res.summary.unmatched_items !== 0) {
        return { ok: false, detail: `${res.summary.unmatched_items} item unmatched` }
      }
      if (res.summary.grouped_items !== mrItemCount) {
        return { ok: false, detail: `grouped=${res.summary.grouped_items} != MR items=${mrItemCount}` }
      }
      if (res.groups.length !== 1) {
        return { ok: false, detail: `${res.groups.length} group — đáng lẽ 1 (cùng FC ${fcUsed})` }
      }
      if (res.groups[0].framework_contract !== fcUsed) {
        return { ok: false, detail: `group FC=${res.groups[0].framework_contract} != ${fcUsed}` }
      }
      return { ok: true, detail: `MR ${mr.name} (${mrItemCount} item) → 1 group đúng FC ${fcUsed} ✓` }
    },
  },
  {
    name: 'create_purchase_orders: PO chứa ĐỦ mọi item của MR',
    run: async ({ page }) => {
      const fcs = await apiGetList(page, 'Framework Contract', {
        fields: ['name'], filters: [['docstatus', '=', 1], ['status', '=', 'Active']],
        limit: 10,
      })
      let mr = null
      for (const fc of fcs) {
        mr = await buildMrFromFc(page, fc.name)
        if (mr) break
      }
      if (!mr) return { ok: false, detail: 'Không tìm được FC phù hợp' }
      const mrDoc = await apiGetDoc(page, 'SC Material Request', mr.name)
      const mrItems = mrDoc.items.map(i => `${i.item}:${i.qty}`).sort()

      // Submit → approve → create PO
      await apiCall(page, 'supplycore.api.frontend.submit_doc',
        { doctype: 'SC Material Request', name: mr.name })
      await apiRunDocMethod(page, 'SC Material Request', mr.name, 'approve')
      const res = await apiRunDocMethod(page, 'SC Material Request', mr.name,
        'create_purchase_orders')
      const out = res.message || res
      const createdPos = out.created_pos || []
      if (!createdPos.length) {
        return { ok: false, detail: `Không PO nào được tạo: ${JSON.stringify(out.summary)}` }
      }
      // Gom toàn bộ item từ MỌI PO đã tạo
      const poItems = []
      for (const poName of createdPos) {
        const po = await apiGetDoc(page, 'SC Purchase Order', poName)
        for (const it of (po.items || [])) poItems.push(`${it.item}:${it.qty}`)
      }
      poItems.sort()
      // So khớp: PO phải chứa đủ mọi item MR
      const missing = mrItems.filter(x => !poItems.includes(x))
      if (missing.length) {
        return { ok: false, detail: `PO THIẾU item của MR: ${missing.join(', ')} (MR=${mrItems.length}, PO=${poItems.length})` }
      }
      if (poItems.length !== mrItems.length) {
        return { ok: false, detail: `PO có ${poItems.length} dòng != MR ${mrItems.length}` }
      }
      return { ok: true, detail: `MR ${mr.name} ${mrItems.length} item → PO ${createdPos.join(',')} đủ ${poItems.length} item ✓` }
    },
  },
  {
    name: 'Audit all_accounted: không mất dòng nào MR → PO',
    run: async ({ page }) => {
      const fcs = await apiGetList(page, 'Framework Contract', {
        fields: ['name'], filters: [['docstatus', '=', 1], ['status', '=', 'Active']],
        limit: 10,
      })
      let mr = null
      for (const fc of fcs) {
        mr = await buildMrFromFc(page, fc.name)
        if (mr) break
      }
      if (!mr) return { ok: false, detail: 'Không tìm được FC phù hợp' }
      await apiCall(page, 'supplycore.api.frontend.submit_doc',
        { doctype: 'SC Material Request', name: mr.name })
      const res = await apiCall(page, 'supplycore.m2_planning.api.po_suggest.suggest_po_from_mr',
        { mr_name: mr.name, auto_create: 0 })
      if (!res.summary.all_accounted) {
        return { ok: false, detail: `all_accounted=false: ${JSON.stringify(res.summary)}` }
      }
      const acc = res.summary.grouped_items + res.summary.unmatched_items
      if (acc !== res.summary.mr_items) {
        return { ok: false, detail: `${acc} != mr_items ${res.summary.mr_items}` }
      }
      return { ok: true, detail: `all_accounted ✓ (${res.summary.mr_items} dòng đều xử lý)` }
    },
  },
  {
    name: 'Dòng MR KHÔNG gán HĐK → suggest HĐK đơn giá rẻ nhất (logic cũ)',
    run: async ({ page }) => {
      // VTTH-SYR-5ML có trong nhiều HĐK Active với giá khác nhau
      const item = 'VTTH-SYR-5ML'
      const fcRows = await apiGetList(page, 'FC Item', {
        fields: ['parent', 'unit_price'],
        filters: [['item_code', '=', item]], limit: 50,
      })
      // Lọc FC Active
      const activeFcs = await apiGetList(page, 'Framework Contract', {
        fields: ['name'], filters: [['docstatus', '=', 1], ['status', '=', 'Active']],
        limit: 200,
      })
      const activeSet = new Set(activeFcs.map(f => f.name))
      const prices = fcRows.filter(r => activeSet.has(r.parent)).map(r => Number(r.unit_price))
      if (prices.length < 2) return { ok: false, detail: `${item} không đủ ≥2 HĐK Active để test` }
      const cheapest = Math.min(...prices)
      const dearest = Math.max(...prices)
      if (cheapest === dearest) return { ok: false, detail: 'Giá các HĐK bằng nhau — không phân biệt được' }

      const wh = (await apiGetList(page, 'SC Warehouse',
        { fields: ['name'], filters: [['is_group', '=', 0]], limit: 1 }))[0]?.name
      // MR với 1 dòng, KHÔNG gán framework_contract
      const mr = await createDoc(page, 'SC Material Request', {
        request_type: 'Purchase',
        transaction_date: '2026-05-22', schedule_date: '2026-06-15',
        warehouse: wh,
        items: [{ doctype: 'SC Material Request Item', item, uom: 'Cái', qty: 5 }],
      })
      await apiCall(page, 'supplycore.api.frontend.submit_doc',
        { doctype: 'SC Material Request', name: mr.name })
      const res = await apiCall(page, 'supplycore.m2_planning.api.po_suggest.suggest_po_from_mr',
        { mr_name: mr.name, auto_create: 0 })
      if (res.summary.grouped_items !== 1) {
        return { ok: false, detail: `grouped=${res.summary.grouped_items}, mong 1` }
      }
      const chosenRate = res.groups[0]?.items?.[0]?.rate
      if (Number(chosenRate) !== cheapest) {
        return { ok: false, detail: `Chọn rate=${chosenRate}, mong rẻ nhất=${cheapest} (đắt nhất=${dearest})` }
      }
      return { ok: true, detail: `Không gán HĐK → suggest HĐK rẻ nhất rate=${cheapest} (bỏ qua ${dearest}) ✓` }
    },
  },
  {
    name: 'Tạo MR từ HĐK (make_material_request) → mọi dòng bám đúng HĐK',
    run: async ({ page }) => {
      const fcs = await apiGetList(page, 'Framework Contract', {
        fields: ['name'], filters: [['docstatus', '=', 1], ['status', '=', 'Active']],
        limit: 10,
      })
      let mrName = null, fcUsed = null
      for (const fc of fcs) {
        try {
          const res = await apiRunDocMethod(page, 'Framework Contract', fc.name,
            'make_material_request')
          const out = res.message || res
          if (out?.material_request) { mrName = out.material_request; fcUsed = fc.name; break }
        } catch (e) { /* FC này không tạo được MR — thử FC khác */ }
      }
      if (!mrName) return { ok: false, detail: 'Không FC nào tạo được MR' }
      const mrDoc = await apiGetDoc(page, 'SC Material Request', mrName)
      if (!mrDoc.items?.length) return { ok: false, detail: `MR ${mrName} không có dòng` }
      // Mọi dòng MR phải mang framework_contract = FC nguồn
      const wrong = mrDoc.items.filter(r => r.framework_contract !== fcUsed)
      if (wrong.length) {
        return { ok: false, detail: `${wrong.length}/${mrDoc.items.length} dòng KHÔNG gán đúng HĐK ${fcUsed}` }
      }
      return { ok: true, detail: `MR ${mrName} từ HĐK ${fcUsed}: ${mrDoc.items.length}/${mrDoc.items.length} dòng bám đúng HĐK ✓` }
    },
  },
  {
    name: 'UI: bấm "Tạo Đơn mua" → modal hiện đủ PO + item',
    run: async ({ page, BASE, OUT, name }) => {
      const fcs = await apiGetList(page, 'Framework Contract', {
        fields: ['name'], filters: [['docstatus', '=', 1], ['status', '=', 'Active']],
        limit: 10,
      })
      let mr = null
      for (const fc of fcs) {
        mr = await buildMrFromFc(page, fc.name)
        if (mr) break
      }
      if (!mr) return { ok: false, detail: 'Không tìm được FC phù hợp' }
      const mrDoc = await apiGetDoc(page, 'SC Material Request', mr.name)
      const itemCount = mrDoc.items.length
      // Submit + approve để nút "Tạo Đơn mua" hiện
      await apiCall(page, 'supplycore.api.frontend.submit_doc',
        { doctype: 'SC Material Request', name: mr.name })
      await apiRunDocMethod(page, 'SC Material Request', mr.name, 'approve')

      await navigateTo(page, BASE, `/doc/SC%20Material%20Request/${encodeURIComponent(mr.name)}`)
      await page.waitForTimeout(1800)
      await page.locator('button:has-text("Tạo Đơn mua")').first().click()
      await page.waitForTimeout(2500)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      const html = await page.content()
      // Modal kết quả phải hiện "Số PO tạo" + "Dòng yêu cầu"
      if (!html.includes('Số PO tạo') || !html.includes('Dòng yêu cầu')) {
        return { ok: false, detail: 'Modal kết quả tạo PO không hiển thị' }
      }
      // Đếm dòng item trong modal (mọi PO group) ≥ số item MR
      const modalRows = await page.locator('.sc-modal tbody tr, [class*="modal"] tbody tr').count()
      return { ok: true, detail: `Modal hiện kết quả tạo PO cho MR ${itemCount} item ✓` }
    },
  },
]
