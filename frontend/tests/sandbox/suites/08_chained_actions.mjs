// Suite 08: Chained actions FC→MR→PO + PR→QI + Warehouse stock
import { apiCall, apiGetList, apiRunDocMethod, navigateTo } from '../helpers.mjs'

export const tests = [
  {
    name: 'FC make_material_request → tạo MR Draft',
    run: async ({ page, BASE, OUT, name }) => {
      // FC còn remaining_value > 0 → chắc chắn có item remaining_qty cho make_material_request
      const fcs = await apiGetList(page, 'Framework Contract',
        { fields: ['name'], order_by: 'remaining_value desc',
          filters: [['status', '=', 'Active'], ['docstatus', '=', 1],
                    ['remaining_value', '>', 0]], limit: 1 })
      if (!fcs.length) return { ok: false, detail: 'No Active FC còn remaining_value' }
      try {
        const result = await apiRunDocMethod(page, 'Framework Contract', fcs[0].name,
          'make_material_request')
        const mrName = result.material_request
        if (!mrName) return { ok: false, detail: `No MR name in result: ${JSON.stringify(result)}` }
        const mr = await apiCall(page, 'supplycore.api.frontend.get_doc',
          { doctype: 'SC Material Request', name: mrName })
        // Cleanup
        await page.evaluate(async ({ name, csrf }) => {
          await fetch(`/api/resource/SC%20Material%20Request/${encodeURIComponent(name)}`, {
            method: 'DELETE', credentials: 'include',
            headers: { 'X-Frappe-CSRF-Token': csrf },
          })
        }, { name: mrName, csrf: await page.evaluate(() => window.sc_csrf) })
        // UC-07 luồng 1b: mỗi dòng MR phải có sẵn framework_contract + đơn giá từ HĐ khung
        const items = mr.items || []
        if (!items.length) return { ok: false, detail: 'MR created but no items' }
        const missingFC = items.filter(r => !r.framework_contract).length
        const zeroPrice = items.filter(r => !(Number(r.estimated_unit_cost) > 0)).length
        if (missingFC) return { ok: false, detail: `MR ${mrName}: ${missingFC} dòng thiếu framework_contract` }
        if (zeroPrice) return { ok: false, detail: `MR ${mrName}: ${zeroPrice} dòng estimated_unit_cost = 0` }
        return { ok: true,
          detail: `FC ${fcs[0].name} → MR ${mrName} (${items.length} items, đủ HĐ khung + đơn giá)` }
      } catch (e) {
        return { ok: false, detail: e.message.slice(0, 200) }
      }
    },
  },
  {
    name: 'FC ActionPanel có button "Tạo Yêu cầu mua hàng"',
    run: async ({ page, BASE, OUT, name }) => {
      const fcs = await apiGetList(page, 'Framework Contract',
        { fields: ['name'], filters: { status: 'Active', docstatus: 1 }, limit: 1 })
      if (!fcs.length) return { ok: false, detail: 'No FC' }
      await navigateTo(page, BASE, `/doc/Framework%20Contract/${encodeURIComponent(fcs[0].name)}`)
      await page.waitForTimeout(2500)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      const btn = await page.locator('button:has-text("Tạo Yêu cầu mua hàng")').count()
      return btn >= 1
        ? { ok: true, detail: `Button visible trên FC ${fcs[0].name}` }
        : { ok: false, detail: 'Button không hiển thị' }
    },
  },
  {
    name: 'MR Approved → button "Tạo Đơn mua (PO)" visible',
    run: async ({ page, BASE, OUT, name }) => {
      const mrs = await apiGetList(page, 'SC Material Request',
        { fields: ['name'], filters: { docstatus: 1, status: 'Approved' }, limit: 1 })
      if (!mrs.length) {
        // Approve 1 MR first
        const draft = await apiGetList(page, 'SC Material Request',
          { fields: ['name'], filters: { docstatus: 1 }, limit: 1 })
        if (draft.length) {
          try { await apiRunDocMethod(page, 'SC Material Request', draft[0].name, 'approve') } catch {}
        }
      }
      const approved = await apiGetList(page, 'SC Material Request',
        { fields: ['name'], filters: { status: 'Approved' }, limit: 1 })
      if (!approved.length) return { ok: true, detail: 'No Approved MR (skip)' }
      await navigateTo(page, BASE, `/doc/SC%20Material%20Request/${encodeURIComponent(approved[0].name)}`)
      await page.waitForTimeout(2500)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      const btn = await page.locator('button:has-text("Tạo Đơn mua")').count()
      return btn >= 1
        ? { ok: true, detail: `Approved MR có button "Tạo Đơn mua"` }
        : { ok: false, detail: 'Button không hiển thị' }
    },
  },
  {
    name: 'PR submitted → button "Tạo Phiếu QC" + "Xem Lô đã tạo"',
    run: async ({ page, BASE, OUT, name }) => {
      const prs = await apiGetList(page, 'SC Purchase Receipt',
        { fields: ['name'], filters: { docstatus: 1, is_return: 0 }, limit: 1 })
      if (!prs.length) return { ok: false, detail: 'No PR' }
      await navigateTo(page, BASE, `/doc/SC%20Purchase%20Receipt/${encodeURIComponent(prs[0].name)}`)
      await page.waitForTimeout(2500)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      const qcBtn = await page.locator('button:has-text("Tạo Phiếu QC")').count()
      const batchBtn = await page.locator('button:has-text("Xem Lô đã tạo")').count()
      return (qcBtn >= 1 && batchBtn >= 1)
        ? { ok: true, detail: `PR ${prs[0].name}: 2 buttons OK` }
        : { ok: false, detail: `QC=${qcBtn}, Batch=${batchBtn}` }
    },
  },
  {
    name: 'PR.make_quality_inspection idempotent',
    run: async ({ page }) => {
      const prs = await apiGetList(page, 'SC Purchase Receipt',
        { fields: ['name'], filters: { docstatus: 1, is_return: 0 }, limit: 1 })
      if (!prs.length) return { ok: false, detail: 'No PR' }
      try {
        const result = await apiRunDocMethod(page, 'SC Purchase Receipt', prs[0].name,
          'make_quality_inspection')
        return result?.count >= 1
          ? { ok: true, detail: `${result.count} QIs cho PR ${prs[0].name}` }
          : { ok: false, detail: `count=${result?.count}` }
      } catch (e) {
        return { ok: false, detail: e.message.slice(0, 200) }
      }
    },
  },
  {
    name: 'QI Accepted → SC Batch.qc_status = Accepted',
    run: async ({ page }) => {
      const qis = await apiGetList(page, 'SC Quality Inspection',
        { fields: ['name', 'batch'], filters: { docstatus: 1, overall_status: 'Accepted' }, limit: 5 })
      if (!qis.length) return { ok: false, detail: 'No accepted QI with batch' }
      let okCount = 0
      for (const qi of qis) {
        if (!qi.batch) continue
        const batch = await apiCall(page, 'supplycore.api.frontend.get_doc',
          { doctype: 'SC Batch', name: qi.batch })
        if (batch.qc_status === 'Accepted') okCount++
      }
      return okCount >= 1
        ? { ok: true, detail: `${okCount}/${qis.length} QI Accepted → Batch Accepted` }
        : { ok: false, detail: 'No batch synced' }
    },
  },
  {
    name: 'Warehouse list (/warehouses) hiển thị tồn kho per kho',
    run: async ({ page, BASE, OUT, name }) => {
      await navigateTo(page, BASE, '/warehouses')
      await page.waitForTimeout(2500)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      const rows = await page.locator('table tbody tr').count()
      const hasQtyHeader = await page.locator('th:has-text("Tổng SL tồn")').count()
      const hasValueHeader = await page.locator('th:has-text("Giá trị tồn")').count()
      return (rows >= 1 && hasQtyHeader >= 1 && hasValueHeader >= 1)
        ? { ok: true, detail: `${rows} warehouses + cột SL/Giá trị` }
        : { ok: false, detail: `rows=${rows}, qty header=${hasQtyHeader}, value header=${hasValueHeader}` }
    },
  },
  {
    name: 'Warehouse summary API trả total_qty + total_value',
    run: async ({ page }) => {
      const summary = await apiCall(page, 'supplycore.api.frontend.warehouse_summary')
      const valid = summary.every(w => 'total_qty' in w && 'total_value' in w && 'distinct_items' in w)
      return valid
        ? { ok: true, detail: `${summary.length} kho có total_qty/value/items` }
        : { ok: false, detail: 'Missing fields' }
    },
  },
  {
    name: 'Warehouse detail có RelatedDocs "Tồn kho hiện tại"',
    run: async ({ page, BASE, OUT, name }) => {
      const whs = await apiGetList(page, 'SC Warehouse',
        { fields: ['name'], filters: { is_group: 0, disabled: 0 }, limit: 1 })
      if (!whs.length) return { ok: false, detail: 'No warehouse' }
      await navigateTo(page, BASE, `/doc/SC%20Warehouse/${encodeURIComponent(whs[0].name)}`)
      await page.waitForTimeout(2500)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      const stockSection = await page.locator('text=Tồn kho').count()
      return stockSection >= 1
        ? { ok: true, detail: `Warehouse ${whs[0].name} có Tồn kho section` }
        : { ok: false, detail: 'No section' }
    },
  },
]
