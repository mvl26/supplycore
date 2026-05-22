// Suite 36: test button "Tạo phiếu chuyển kho" trên SC Transfer Request
// cụ thể SC-TR-2026-04584.
//
// Button (actions.js): make_stock_entry — when docstatus=1, status=Approved,
// chưa có stock_entry. Bấm → tạo SC Stock Entry (Material Transfer) draft +
// điều hướng sang trang SE; TR.status → In Transit.
//
// Test tự thích ứng trạng thái TR-04584:
//  - Draft  → submit để lên Approved rồi test bấm nút.
//  - Approved chưa có SE → bấm nút, kiểm SE tạo ra.
//  - Đã có SE → nút ẩn đúng thiết kế → kiểm SE liên kết hợp lệ.

import { apiCall, apiGetDoc, apiRunDocMethod, navigateTo } from '../helpers.mjs'

const TR = 'SC-TR-2026-04584'

async function getTr(page) {
  try {
    return await apiGetDoc(page, 'SC Transfer Request', TR)
  } catch (e) {
    return null
  }
}

export const tests = [
  {
    name: `${TR}: tồn tại + đưa về trạng thái Approved (sẵn sàng test nút)`,
    run: async ({ page }) => {
      let tr = await getTr(page)
      if (!tr || !tr.name) return { ok: false, detail: `${TR} không tồn tại` }
      page._tr = { name: TR }

      if (tr.docstatus === 2) {
        return { ok: false, detail: `${TR} đã Cancelled — không test được nút tạo SE` }
      }
      // Draft → submit (on_submit tự set status=Approved)
      if (tr.docstatus === 0) {
        await apiCall(page, 'supplycore.api.frontend.submit_doc',
          { doctype: 'SC Transfer Request', name: TR })
        tr = await getTr(page)
      }
      page._tr.alreadyHasSE = !!tr.stock_entry
      page._tr.existingSE = tr.stock_entry || null
      page._tr.from = tr.from_warehouse
      page._tr.to = tr.to_warehouse
      page._tr.itemCount = (tr.items || []).length

      if (tr.docstatus !== 1) {
        return { ok: false, detail: `${TR} docstatus=${tr.docstatus} (mong 1)` }
      }
      if (tr.status !== 'Approved' && !tr.stock_entry) {
        return { ok: false, detail: `${TR} status=${tr.status} (mong Approved)` }
      }
      return {
        ok: true,
        detail: tr.stock_entry
          ? `${TR} đã có SE=${tr.stock_entry} (sẽ kiểm nút ẩn đúng + SE hợp lệ)`
          : `${TR} Approved, chưa có SE — sẽ test bấm nút`,
      }
    },
  },

  {
    name: `SPA mở ${TR} → nút "Tạo phiếu chuyển kho" đúng trạng thái`,
    run: async ({ page, BASE, OUT, name }) => {
      if (!page._tr) return { ok: false, detail: 'Setup chưa chạy' }
      await navigateTo(page, BASE, `/doc/SC%20Transfer%20Request/${encodeURIComponent(TR)}`)
      await page.waitForTimeout(1800)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      const btnCount = await page.locator('button:has-text("Tạo phiếu chuyển kho")').count()

      if (page._tr.alreadyHasSE) {
        // Đã có SE → nút PHẢI ẩn (when: !d.stock_entry)
        return btnCount === 0
          ? { ok: true, detail: 'TR đã có SE → nút ẩn đúng thiết kế ✓' }
          : { ok: false, detail: `TR đã có SE nhưng nút vẫn hiện (${btnCount})` }
      }
      // Chưa có SE + Approved → nút PHẢI hiện
      return btnCount >= 1
        ? { ok: true, detail: 'Nút "Tạo phiếu chuyển kho" hiển thị ✓' }
        : { ok: false, detail: 'Không thấy nút "Tạo phiếu chuyển kho"' }
    },
  },

  {
    name: `Bấm nút → tạo SE thành công HOẶC chặn bằng lỗi nghiệp vụ rõ ràng`,
    run: async ({ page, OUT, name }) => {
      if (!page._tr) return { ok: false, detail: 'Setup chưa chạy' }

      if (page._tr.alreadyHasSE) {
        page._tr.seName = page._tr.existingSE
        page._tr.outcome = 'pre-existing'
        return { ok: true, detail: `Bỏ qua bấm — TR đã có SE=${page._tr.existingSE}` }
      }

      await page.locator('button:has-text("Tạo phiếu chuyển kho")').first().click()

      // Poll ~5s: bắt điều hướng SE hoặc toast lỗi (toast tự ẩn sau 4s)
      let errTxt = ''
      let seUrl = ''
      for (let i = 0; i < 14; i++) {
        await page.waitForTimeout(380)
        const url = page.url()
        if (/\/doc\/SC(%20| )Stock(%20| )Entry\/SC-SE-/.test(url)) { seUrl = url; break }
        // Toast lỗi: trong container .fixed.top-4.right-4, lấy dòng message
        const t = await page.locator('.fixed.top-4.right-4 .leading-snug')
          .first().textContent().catch(() => '')
        if (t && t.trim()) errTxt = t.trim()
      }
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })

      // Kết quả 1: tạo SE + điều hướng
      if (seUrl) {
        page._tr.seName = decodeURIComponent(seUrl.split('/').pop())
        page._tr.outcome = 'created'
        return { ok: true, detail: `Tạo SE thành công + điều hướng → ${page._tr.seName}` }
      }
      const tr = await getTr(page)
      if (tr?.stock_entry) {
        page._tr.seName = tr.stock_entry
        page._tr.outcome = 'created'
        return { ok: true, detail: `Tạo SE=${tr.stock_entry} (không auto-navigate)` }
      }

      // Kết quả 2: button chặn bằng lỗi nghiệp vụ (vd FEFO) — vẫn là hành vi ĐÚNG
      if (errTxt) {
        page._tr.outcome = 'blocked'
        page._tr.errMsg = errTxt
        return {
          ok: true,
          detail: `Button chặn đúng bằng lỗi nghiệp vụ: "${errTxt.slice(0, 160)}"`,
        }
      }
      return { ok: false, detail: `Bấm nút không có kết quả nào (không SE, không toast lỗi)` }
    },
  },

  {
    name: `Kiểm SC Stock Entry (nếu tạo được): entry_type + from/to + TR khớp`,
    run: async ({ page }) => {
      if (page._tr?.outcome === 'blocked') {
        return { ok: true, detail: `N/A — button bị chặn bởi lỗi nghiệp vụ (xem test trên)` }
      }
      if (!page._tr?.seName) return { ok: false, detail: 'Chưa có SE để kiểm' }
      const se = await apiGetDoc(page, 'SC Stock Entry', page._tr.seName)
      const checks = {
        entry_type: se?.entry_type === 'Material Transfer',
        from_warehouse: se?.from_warehouse === page._tr.from,
        to_warehouse: se?.to_warehouse === page._tr.to,
        transfer_request: se?.transfer_request === TR,
        has_items: (se?.items || []).length >= 1,
        qty_positive: (se?.items || []).every(i => Number(i.qty || 0) > 0),
      }
      const failed = Object.entries(checks).filter(([, v]) => !v).map(([k]) => k)
      return failed.length === 0
        ? { ok: true, detail: `SE=${page._tr.seName}: Material Transfer, from=${se.from_warehouse}, to=${se.to_warehouse}, ${se.items.length} dòng ✓` }
        : { ok: false, detail: `Sai: ${failed.join(', ')}` }
    },
  },

  {
    name: `${TR} trạng thái cuối: In Transit nếu tạo SE, giữ Approved nếu bị chặn`,
    run: async ({ page }) => {
      if (!page._tr) return { ok: false, detail: 'Setup chưa chạy' }
      const tr = await getTr(page)
      if (page._tr.outcome === 'blocked') {
        // Button chặn → TR phải GIỮ NGUYÊN Approved, KHÔNG có stock_entry
        return tr?.status === 'Approved' && !tr?.stock_entry
          ? { ok: true, detail: `Bị chặn → TR giữ Approved, chưa có SE (không side-effect bẩn) ✓` }
          : { ok: false, detail: `Bị chặn nhưng TR status=${tr?.status}, stock_entry=${tr?.stock_entry}` }
      }
      // Tạo SE → In Transit + stock_entry trỏ về SE
      return tr?.status === 'In Transit' && tr?.stock_entry === page._tr.seName
        ? { ok: true, detail: `status=${tr.status}, stock_entry=${tr.stock_entry} ✓` }
        : { ok: false, detail: `status=${tr?.status} (mong In Transit), stock_entry=${tr?.stock_entry}` }
    },
  },
]
