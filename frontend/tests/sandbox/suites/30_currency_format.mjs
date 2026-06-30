// Suite 30: Định dạng nhập tiền — Currency hiển thị dấu '.' ngăn hàng nghìn
// Kiểm thử fix FormField.vue (đơn giá & các field tiền).

export const tests = [
  {
    name: 'Header Currency (SC Supplier · Hạn mức tín dụng) → format dấu .',
    run: async ({ page, BASE, OUT, name }) => {
      await page.goto(`${BASE}/supplycore/doc/${encodeURIComponent('SC Supplier')}/new`)
      await page.waitForTimeout(1000)
      const inp = page.locator('input[inputmode="numeric"]').first()
      if (!(await inp.count())) return { ok: false, detail: 'Không thấy input tiền (inputmode=numeric)' }
      await inp.fill('1234567')
      await page.waitForTimeout(150)
      const v = await inp.inputValue()
      await page.screenshot({ path: `${OUT}/${name}.png` })
      return v === '1.234.567'
        ? { ok: true, detail: `1234567 → "${v}"` }
        : { ok: false, detail: `Mong "1.234.567", nhận "${v}"` }
    },
  },
  {
    name: 'Gõ từng phím → grouping cập nhật trực tiếp (không kẹt 00/ký tự lạ)',
    run: async ({ page, BASE, OUT, name }) => {
      await page.goto(`${BASE}/supplycore/doc/${encodeURIComponent('SC Supplier')}/new`)
      await page.waitForTimeout(1000)
      const inp = page.locator('input[inputmode="numeric"]').first()
      await inp.click()
      await inp.pressSequentially('250000', { delay: 30 })
      await page.waitForTimeout(120)
      const live = await inp.inputValue()
      // thử ký tự lạ + số 0 dư
      await inp.fill('')
      await inp.pressSequentially('00', { delay: 30 })
      const zeros = await inp.inputValue()
      await page.screenshot({ path: `${OUT}/${name}.png` })
      if (live !== '250.000') return { ok: false, detail: `Gõ 250000 → "${live}" (mong 250.000)` }
      if (zeros !== '0') return { ok: false, detail: `Gõ 00 → "${zeros}" (mong 0, không kẹt)` }
      return { ok: true, detail: `250000→"${live}", 00→"${zeros}"` }
    },
  },
  {
    name: 'Đơn giá (Framework Contract · FC item) → format dấu .',
    run: async ({ page, BASE, OUT, name }) => {
      await page.goto(`${BASE}/supplycore/doc/${encodeURIComponent('Framework Contract')}/new`)
      await page.waitForTimeout(1200)
      // Thêm 1 dòng vật tư vào child table
      const addBtn = page.locator('button', { hasText: 'Thêm dòng' }).first()
      if (!(await addBtn.count())) return { ok: false, detail: 'Không thấy nút "+ Thêm dòng"' }
      await addBtn.click()
      await page.waitForTimeout(500)
      // đơn giá = ô tiền editable trong dòng (loại trừ readonly như Thành tiền)
      const priceInp = page.locator('input[inputmode="numeric"]:not([readonly])').first()
      if (!(await priceInp.count())) return { ok: false, detail: 'Không thấy ô đơn giá editable' }
      await priceInp.fill('850000')
      await page.waitForTimeout(150)
      const v = await priceInp.inputValue()
      await page.screenshot({ path: `${OUT}/${name}.png` })
      return v === '850.000'
        ? { ok: true, detail: `đơn giá 850000 → "${v}"` }
        : { ok: false, detail: `Mong "850.000", nhận "${v}"` }
    },
  },
]
