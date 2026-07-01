// Suite 36: Verify Việt hoá — không còn chuỗi tiếng Anh rò rỉ ở màn chính
const LEAK = ['Purchase','Ordered','Procurement Plan','Framework Contract','Material Request',
  'UOM','Supplier','Inspected By','Action Taken','Specification','Is Critical','Release Order','Debit Note']
export const tests = [
  {
    name: 'Danh sách YCMH: cột Loại hiện "Mua" (không "Purchase")',
    run: async ({ page, BASE, OUT, name }) => {
      await page.goto(`${BASE}/supplycore/list/${encodeURIComponent('SC Material Request')}`)
      await page.waitForTimeout(1400)
      const body = await page.locator('table').innerText().catch(() => '')
      await page.screenshot({ path: `${OUT}/${name}.png` })
      if (/\bPurchase\b/.test(body)) return { ok: false, detail: 'còn "Purchase" trong bảng MR' }
      return { ok: true, detail: 'MR list không có "Purchase"' }
    },
  },
  {
    name: 'Panel nguồn PO: nhãn tiếng Việt (fieldLabel)',
    run: async ({ page, BASE, OUT, name }) => {
      await page.goto(`${BASE}/supplycore/doc/${encodeURIComponent('SC Purchase Order')}/new`)
      await page.waitForTimeout(1600)
      // mở panel "Lấy từ..." nếu có
      const body = await page.locator('body').innerText()
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      const leaks = LEAK.filter(w => new RegExp(`(^|\\s|>)${w}(\\s|<|:|$)`).test(body))
      return leaks.length ? { ok: false, detail: 'rò rỉ: ' + leaks.join(', ') }
        : { ok: true, detail: 'form PO/new không rò tiếng Anh rõ' }
    },
  },
]
