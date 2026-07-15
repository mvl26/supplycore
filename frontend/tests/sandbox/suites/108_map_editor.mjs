// Suite 108: Map Editor — admin custom site map per bệnh viện.
//
//   - Render trang /map-editor: config panel + grid + unassigned list.
//   - API save_site_layout: bulk update + round-trip (đổi entrance, rồi
//     trả lại — đảm bảo không phá dữ liệu sản xuất).

export const tests = [
  {
    name: 'Render /map-editor: config + grid + unassigned',
    run: async ({ page, BASE, OUT, name }) => {
      await page.goto(`${BASE}/supplycore/map-editor`, { waitUntil: 'networkidle' })
      await page.waitForTimeout(1200)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: false })
      const r = await page.evaluate(() => {
        const body = document.body.textContent
        const blocked = body.includes('403') && body.includes('Không có quyền')
        return {
          blocked,
          hasTitle: body.includes('Bản đồ khuôn viên') || body.includes('Thiết kế bản đồ'),
          hasConfig: body.includes('Tên bệnh viện') && body.includes('Nhãn cổng'),
          hasGrid: body.includes('Lưới bản đồ'),
          hasUnassignedSection: body.includes('Kho chưa đặt'),
          hasSaveBtn: [...document.querySelectorAll('button')].some(b => b.textContent.includes('Lưu cấu hình')),
        }
      })
      if (r.blocked) {
        return { ok: 'skip', detail: 'Feature map_editor chưa load — cần `bench restart` để gunicorn worker pickup access.py mới' }
      }
      const miss = ['hasConfig', 'hasGrid', 'hasUnassignedSection', 'hasSaveBtn'].filter(k => !r[k])
      return miss.length === 0
        ? { ok: true, detail: 'Đủ panel: config + grid + unassigned + save' }
        : { ok: false, detail: `Thiếu: ${miss.join(', ')}` }
    },
  },
  {
    name: 'API save_site_layout: round-trip đổi entrance không phá data',
    run: async ({ page }) => {
      const csrf = await page.evaluate(() => window.sc_csrf)
      const r = await page.evaluate(async ({ csrf }) => {
        const get = async () => {
          const rr = await fetch('/api/method/supplycore.api.warehouse_map.get_editable_site_map',
            { credentials: 'include', headers: { 'X-Frappe-CSRF-Token': csrf } })
          return (await rr.json()).message
        }
        const before = await get()
        const orig = { ...before.config }
        const placed = (before.warehouses || []).filter(w => w.site_row && w.site_col).length

        // Save với entrance dịch 1 ô
        const newCfg = { ...orig, site_entrance_row: orig.site_entrance_row,
                                  site_entrance_col: Math.max(1, (orig.site_entrance_col || 3) + 1) }
        const r1 = await fetch('/api/method/supplycore.api.warehouse_map.save_site_layout', {
          method: 'POST', credentials: 'include',
          headers: { 'Content-Type': 'application/json', 'X-Frappe-CSRF-Token': csrf },
          body: JSON.stringify({
            config: newCfg,
            warehouses: (before.warehouses || []).filter(w => w.site_row && w.site_col).map(w => ({
              name: w.name, site_row: w.site_row, site_col: w.site_col,
              warehouse_type: w.warehouse_type, site_block: w.site_block || '',
            })),
          }),
        })
        const d1 = await r1.json()
        const mid = await get()

        // Restore
        const r2 = await fetch('/api/method/supplycore.api.warehouse_map.save_site_layout', {
          method: 'POST', credentials: 'include',
          headers: { 'Content-Type': 'application/json', 'X-Frappe-CSRF-Token': csrf },
          body: JSON.stringify({
            config: orig,
            warehouses: (mid.warehouses || []).filter(w => w.site_row && w.site_col).map(w => ({
              name: w.name, site_row: w.site_row, site_col: w.site_col,
              warehouse_type: w.warehouse_type, site_block: w.site_block || '',
            })),
          }),
        })
        const after = await get()
        return {
          status1: r1.status, status2: r2.status,
          midEntrance: { r: mid.config.site_entrance_row, c: mid.config.site_entrance_col },
          afterEntrance: { r: after.config.site_entrance_row, c: after.config.site_entrance_col },
          origEntrance: { r: orig.site_entrance_row, c: orig.site_entrance_col },
          placedBefore: placed,
          placedAfter: (after.warehouses || []).filter(w => w.site_row && w.site_col).length,
          msg1: d1.exception || '',
        }
      }, { csrf })
      const ok = r.status1 < 400 && r.status2 < 400
        && r.midEntrance.c !== r.origEntrance.c
        && r.afterEntrance.r === r.origEntrance.r && r.afterEntrance.c === r.origEntrance.c
        && r.placedAfter === r.placedBefore
      return ok
        ? { ok: true, detail: `entrance ${r.origEntrance.r},${r.origEntrance.c} → ${r.midEntrance.r},${r.midEntrance.c} → restored. ${r.placedAfter} kho intact.` }
        : { ok: false, detail: JSON.stringify(r) }
    },
  },
]
