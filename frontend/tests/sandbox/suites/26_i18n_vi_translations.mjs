// Suite 26: Verify UI hiển thị tiếng Việt cho enum options & labels
import { navigateTo } from '../helpers.mjs'

// (path, openOps, expectations[])
// expectations: { selectLabel, mustHave: [vi labels...], mustNotHave: [en values that should not appear as option text...] }
const cases = [
  {
    name: 'SC Warehouse: Loại kho hiển thị tiếng Việt',
    path: '/doc/SC%20Warehouse/new',
    select: 'Loại kho',
    mustHave: ['Kho chính', 'Kho khoa phòng', 'Kho cách ly'],
    mustNotHave: ['Main', 'Department', 'Quarantine'],
  },
  {
    name: 'Bin Location: Trạng thái hiển thị tiếng Việt',
    path: '/doc/Bin%20Location/new',
    select: 'Trạng thái',
    mustHave: ['Trống', 'Đang dùng', 'Đầy'],
    mustNotHave: ['Empty', 'In Use'],
  },
  {
    name: 'SC Transfer Request: Loại yêu cầu hiển thị tiếng Việt',
    path: '/doc/SC%20Transfer%20Request/new',
    select: 'Loại yêu cầu',
    mustHave: ['Thường quy', 'Khẩn cấp', 'Bổ sung', 'Trả về kho chính'],
    mustNotHave: ['Routine', 'Urgent', 'Replenishment'],
  },
  {
    name: 'SC Stock Entry: Loại GT hiển thị tiếng Việt',
    path: '/doc/SC%20Stock%20Entry/new',
    select: 'Loại GT',
    mustHave: ['Nhập kho', 'Xuất kho', 'Chuyển kho'],
    mustNotHave: ['Material Receipt', 'Material Issue', 'Material Transfer'],
  },
]

async function checkSelect(page, label, mustHave, mustNotHave) {
  // Lấy text các <option> trong <select> sau label tương ứng
  const sel = page.locator(`label:has-text("${label}")`).first().locator('xpath=following::select[1]')
  await sel.waitFor({ state: 'attached', timeout: 5000 })
  const optTexts = await sel.locator('option').allTextContents()
  const norm = optTexts.map(s => s.trim())
  const missing = mustHave.filter(s => !norm.some(t => t === s))
  const leaked  = mustNotHave.filter(s => norm.some(t => t === s))
  return { norm, missing, leaked }
}

export const tests = cases.map(c => ({
  name: c.name,
  run: async ({ page, BASE, OUT, name }) => {
    await navigateTo(page, BASE, c.path)
    await page.waitForTimeout(1300)
    await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
    const r = await checkSelect(page, c.select, c.mustHave, c.mustNotHave)
    const ok = r.missing.length === 0 && r.leaked.length === 0
    return ok
      ? { ok: true, detail: `OK — options: [${r.norm.slice(0, 6).join('; ')}]` }
      : { ok: false, detail: `missing=[${r.missing.join(', ')}] leaked=[${r.leaked.join(', ')}]` }
  },
})).concat([
  {
    name: 'Child table SC Stock Entry: cột "Bỏ qua FEFO" (không phải "FEFO override")',
    run: async ({ page, BASE, OUT, name }) => {
      await navigateTo(page, BASE, '/doc/SC%20Stock%20Entry/new')
      await page.waitForTimeout(1200)
      await page.locator('button:has-text("+ Thêm dòng")').first().click()
      await page.waitForTimeout(400)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      const vn = await page.locator('th:has-text("Bỏ qua FEFO")').count()
      const en = await page.locator('th:has-text("FEFO override")').count()
      return vn >= 1 && en === 0
        ? { ok: true, detail: `Cột tiếng Việt OK (vn=${vn}, en=${en})` }
        : { ok: false, detail: `vn=${vn}, en=${en}` }
    },
  },
  {
    name: 'Child table SC Transfer Request: bảng tên "Chi tiết" (không phải "Items")',
    run: async ({ page, BASE, OUT, name }) => {
      await navigateTo(page, BASE, '/doc/SC%20Transfer%20Request/new')
      await page.waitForTimeout(1400)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      const vn = await page.locator('h4:has-text("Chi tiết")').count()
      const en = await page.locator('h4').filter({ hasText: /^Items\b/ }).count()
      return vn >= 1 && en === 0
        ? { ok: true, detail: `Tiêu đề bảng = "Chi tiết" (vn=${vn}, en=${en})` }
        : { ok: false, detail: `vn=${vn}, en=${en}` }
    },
  },
  {
    name: 'Field "Disabled" trên SC Warehouse → hiển thị "Vô hiệu hoá"',
    run: async ({ page, BASE, OUT, name }) => {
      await navigateTo(page, BASE, '/doc/SC%20Warehouse/new')
      await page.waitForTimeout(1100)
      const vn = await page.locator('text=Vô hiệu hoá').count()
      const en = await page.locator('text=Disabled').count()
      return vn >= 1 && en === 0
        ? { ok: true, detail: `vn=${vn}, en=${en}` }
        : { ok: false, detail: `vn=${vn}, en=${en}` }
    },
  },
])
