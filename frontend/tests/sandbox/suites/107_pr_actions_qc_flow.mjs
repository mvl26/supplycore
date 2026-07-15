// Suite 107: SC Purchase Receipt action panel — sau QC mới có 2 nút PI + Putaway.
//
// Yêu cầu:
//   - GỠ: "Tạo Phiếu KCS", "Tạo Lô", "Xem Lô đã tạo"
//   - GIỮ/THÊM: "Tạo Hoá đơn mua (PI)" + "Xếp hàng lên kệ" — chỉ hiện sau
//     QC xong (qc_status='Accepted') hoặc PR không yêu cầu QC.

export const tests = [
  {
    name: 'PR ActionPanel: không còn nút KCS/Tạo Lô/Xem Lô; có PI + Putaway khi QC xong',
    run: async ({ page, BASE, OUT, name }) => {
      const csrf = await page.evaluate(() => window.sc_csrf)
      // Tìm PR đã submit, không phải return, qc_status='Accepted' hoặc qc_required=0
      const pr = await page.evaluate(async ({ csrf }) => {
        const r = await fetch('/api/method/supplycore.api.frontend.list_docs', {
          method: 'POST', credentials: 'include',
          headers: { 'Content-Type': 'application/json', 'X-Frappe-CSRF-Token': csrf },
          body: JSON.stringify({
            doctype: 'SC Purchase Receipt',
            fields: ['name', 'qc_required', 'qc_status'],
            filters: { docstatus: 1, is_return: 0 }, limit: 30,
          }),
        })
        const d = await r.json()
        const list = d.message || []
        return list.find(x => !x.qc_required || x.qc_status === 'Accepted') || null
      }, { csrf })
      if (!pr) return { ok: 'skip', detail: 'Không có PR submitted (QC done) để smoke' }

      await page.goto(`${BASE}/supplycore/doc/SC%20Purchase%20Receipt/${encodeURIComponent(pr.name)}`,
        { waitUntil: 'networkidle' })
      await page.waitForTimeout(1200)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: false })

      const buttons = await page.evaluate(() => {
        const panel = [...document.querySelectorAll('.sc-card')].find(c =>
          c.querySelector('h3')?.textContent?.includes('Hành động khả dụng'))
        if (!panel) return null
        return [...panel.querySelectorAll('button')].map(b => b.textContent.trim())
      })
      if (!buttons) return { ok: false, detail: 'Không tìm thấy ActionPanel' }
      const has = (t) => buttons.some(b => b.includes(t))
      const checks = {
        'Tạo Hoá đơn mua (PI)': has('Tạo Hoá đơn mua'),
        'Xếp hàng lên kệ': has('Xếp hàng lên kệ'),
        'NO Tạo Phiếu KCS': !has('Tạo Phiếu KCS'),
        'NO Tạo Lô': !buttons.some(b => /^Tạo Lô\b/.test(b)),
        'NO Xem Lô đã tạo': !has('Xem Lô đã tạo'),
      }
      const fail = Object.entries(checks).filter(([, ok]) => !ok).map(([k]) => k)
      return fail.length === 0
        ? { ok: true, detail: `PR ${pr.name} buttons OK: [${buttons.join(' | ')}]` }
        : { ok: false, detail: `PR ${pr.name} fail: ${fail.join(', ')} | buttons=[${buttons.join(' | ')}]` }
    },
  },
  {
    name: 'PR ActionPanel: chưa QC → KHÔNG hiện PI + Putaway',
    run: async ({ page, BASE }) => {
      const csrf = await page.evaluate(() => window.sc_csrf)
      const pr = await page.evaluate(async ({ csrf }) => {
        const r = await fetch('/api/method/supplycore.api.frontend.list_docs', {
          method: 'POST', credentials: 'include',
          headers: { 'Content-Type': 'application/json', 'X-Frappe-CSRF-Token': csrf },
          body: JSON.stringify({
            doctype: 'SC Purchase Receipt',
            fields: ['name', 'qc_required', 'qc_status'],
            filters: { docstatus: 1, is_return: 0, qc_required: 1 }, limit: 30,
          }),
        })
        const d = await r.json()
        return (d.message || []).find(x => x.qc_status !== 'Accepted' && x.qc_status !== 'Rejected') || null
      }, { csrf })
      if (!pr) return { ok: 'skip', detail: 'Không có PR đang chờ QC để smoke' }

      await page.goto(`${BASE}/supplycore/doc/SC%20Purchase%20Receipt/${encodeURIComponent(pr.name)}`,
        { waitUntil: 'networkidle' })
      await page.waitForTimeout(1200)
      const buttons = await page.evaluate(() => {
        const panel = [...document.querySelectorAll('.sc-card')].find(c =>
          c.querySelector('h3')?.textContent?.includes('Hành động khả dụng'))
        return panel ? [...panel.querySelectorAll('button')].map(b => b.textContent.trim()) : []
      })
      const noPI = !buttons.some(b => b.includes('Tạo Hoá đơn mua'))
      const noPutaway = !buttons.some(b => b.includes('Xếp hàng lên kệ'))
      return (noPI && noPutaway)
        ? { ok: true, detail: `PR ${pr.name} qc_status=${pr.qc_status || 'Pending'} ẩn PI+Putaway OK` }
        : { ok: false, detail: `PR ${pr.name} đáng lẽ ẩn nhưng buttons=[${buttons.join(' | ')}]` }
    },
  },
]
