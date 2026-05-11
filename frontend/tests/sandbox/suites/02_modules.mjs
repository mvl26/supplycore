// Suite 02: 12 module hubs M0..M11

const MODULES = [
  ['m0', 'Master Data'],
  ['m1', 'Hợp đồng'],
  ['m2', 'Kế hoạch & Mua'],
  ['m3', 'Tiếp nhận'],
  ['m4', 'Quản lý kho'],
  ['m5', 'FEFO'],
  ['m6', 'Chuyển kho'],
  ['m7', 'Cấp phát'],
  ['m8', 'Kế toán'],
  ['m9', 'Kiểm kê'],
  ['m10', 'Truy xuất & Recall'],
  ['m11', 'Dashboard & Alert'],
]

export const tests = MODULES.map(([id, expectedTitle]) => ({
  name: `${id.toUpperCase()} — ${expectedTitle}`,
  run: async ({ page, BASE, OUT, name }) => {
    await page.goto(`${BASE}/supplycore/${id}`)
    await page.waitForTimeout(1200)
    await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: false })
    const title = await page.locator('h1').first().textContent()
    return title?.includes(expectedTitle)
      ? { ok: true, detail: `"${title}"` }
      : { ok: false, detail: `Got "${title}"` }
  },
}))
