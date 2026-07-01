// Suite 32: Phiếu QC bỏ "Gửi duyệt" — DocView không còn nút submit/cancel
// (QC giờ non-submittable: Lưu là áp kết quả).
const QI_NAME = 'SC-QI-2026-04060'  // QI có sẵn trong DB seed

export const tests = [
  {
    name: 'QI DocView KHÔNG còn nút "Gửi duyệt"/"Submit kích hoạt"',
    run: async ({ page, BASE, OUT, name }) => {
      await page.goto(`${BASE}/supplycore/doc/${encodeURIComponent('SC Quality Inspection')}/${encodeURIComponent(QI_NAME)}`)
      await page.waitForTimeout(1500)
      // Phải load đúng phiếu (có tiêu đề/mã)
      const loaded = await page.locator(`text=${QI_NAME}`).count()
      if (!loaded) return { ok: false, detail: `Không load được phiếu ${QI_NAME}` }
      const guiDuyet = await page.locator('button', { hasText: 'Gửi duyệt' }).count()
      const submitKichHoat = await page.locator('button', { hasText: 'Submit kích hoạt' }).count()
      const huy = await page.locator('button', { hasText: /^Hủy$/ }).count()
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      if (guiDuyet > 0) return { ok: false, detail: 'Vẫn còn nút "Gửi duyệt"' }
      if (submitKichHoat > 0) return { ok: false, detail: 'Vẫn còn nút "Submit kích hoạt"' }
      if (huy > 0) return { ok: false, detail: 'Vẫn còn nút "Hủy" (cancel) cho QC non-submittable' }
      return { ok: true, detail: 'Không còn nút submit/cancel — chỉ Lưu' }
    },
  },
]
