// Suite 06: Module hubs phải có nội dung + button Tạo mới

const MODULES_WITH_CREATE = [
  ['m0', 'Master Data', 8],
  ['m1', 'Hợp đồng', 1],
  ['m2', 'Kế hoạch & Mua', 2],
  ['m3', 'Tiếp nhận', 2],
  ['m4', 'Quản lý kho', 3],
  ['m5', 'FEFO', 1],
  ['m6', 'Chuyển kho', 2],
  ['m7', 'Cấp phát', 2],
  ['m8', 'Kế toán', 3],
  ['m9', 'Kiểm kê', 2],
  ['m10', 'Truy xuất & Recall', 2],
  ['m11', 'Dashboard & Alert', 2],
]

export const tests = MODULES_WITH_CREATE.flatMap(([id, expectedTitle, minCards]) => [
  {
    name: `${id.toUpperCase()} hub có ${minCards} doctype cards`,
    run: async ({ page, BASE, OUT, name }) => {
      await page.goto(`${BASE}/supplycore/${id}`)
      await page.waitForTimeout(1500)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: false })
      const title = await page.locator('h1').first().textContent()
      // Count "+ Tạo mới" buttons inside doctype cards
      const createBtns = await page.locator('button:has-text("+ Tạo mới")').count()
      return title?.includes(expectedTitle) && createBtns >= minCards
        ? { ok: true, detail: `"${title}", ${createBtns} create buttons` }
        : { ok: false, detail: `Title="${title}", btns=${createBtns} (need ${minCards})` }
    },
  },
])
