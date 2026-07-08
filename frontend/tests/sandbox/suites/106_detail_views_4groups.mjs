// Suite 106: Detail-view redesign smoke cho 4 nhóm doctype (PO, PR, PI, MR,
// SE, TR, Recall, IR, ICS). Verify mỗi doctype có 1 doc submitted
// để render được hero + tiles + items table (nếu có).
// (DR/PD — M7 Dispensing — đã bỏ khỏi backend GĐ1)

const TARGETS = [
  { dt: 'SC Purchase Order',        path: 'SC Purchase Order',        needs: ['hero', 'tiles', 'items'] },
  { dt: 'SC Purchase Receipt',      path: 'SC Purchase Receipt',      needs: ['hero', 'tiles', 'items'] },
  { dt: 'SC Purchase Invoice',      path: 'SC Purchase Invoice',      needs: ['hero', 'tiles', 'items'] },
  { dt: 'SC Material Request',      path: 'SC Material Request',      needs: ['hero', 'tiles', 'items'] },
  { dt: 'SC Stock Entry',           path: 'SC Stock Entry',           needs: ['hero', 'tiles', 'items'] },
  { dt: 'SC Transfer Request',      path: 'SC Transfer Request',      needs: ['hero', 'tiles', 'items'] },
  { dt: 'SC Recall Notice',         path: 'SC Recall Notice',         needs: ['hero', 'tiles'] },
  { dt: 'SC Investigation Report',  path: 'SC Investigation Report',  needs: ['hero', 'tiles'] },
  { dt: 'SC Inventory Count Sheet', path: 'SC Inventory Count Sheet', needs: ['hero', 'tiles'] },
]

async function pickDoc(page, doctype) {
  const csrf = await page.evaluate(() => window.sc_csrf)
  return page.evaluate(async ({ doctype, csrf }) => {
    const r = await fetch('/api/method/supplycore.api.frontend.list_docs', {
      method: 'POST', credentials: 'include',
      headers: { 'Content-Type': 'application/json', 'X-Frappe-CSRF-Token': csrf },
      // Draft → edit form; chỉ smoke detail view với docstatus=1 (submitted)
      body: JSON.stringify({ doctype, fields: ['name'], filters: { docstatus: 1 }, limit: 1 }),
    })
    const d = await r.json()
    return (d.message || [])[0]?.name
  }, { doctype, csrf })
}

async function inspectDetail(page) {
  return page.evaluate(() => {
    const body = document.body.textContent
    // Hero check: kicker uppercase + h1
    const hasHero = !!document.querySelector('h1') &&
      !!document.querySelector('[class*="uppercase"]')
    // Tiles: 2+ ô có pattern label + value mono
    const tiles = document.querySelectorAll('.font-mono.text-xl.font-semibold')
    const hasTiles = tiles.length >= 2
    // Items table với tfoot có TỔNG
    const tfoot = document.querySelector('table tfoot')
    const hasItems = !!tfoot && body.includes('TỔNG')
    return { hasHero, hasTiles, hasItems }
  })
}

export const tests = TARGETS.map(t => ({
  name: `${t.dt}: hero + tiles${t.needs.includes('items') ? ' + items totals' : ''}`,
  run: async ({ page, BASE, OUT, name }) => {
    const docName = await pickDoc(page, t.dt)
    if (!docName) return { ok: 'skip', detail: `Không có ${t.dt} doc để smoke` }

    await page.goto(`${BASE}/supplycore/doc/${encodeURIComponent(t.path)}/${encodeURIComponent(docName)}`,
      { waitUntil: 'networkidle' })
    await page.waitForTimeout(1200)
    await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: false })

    const r = await inspectDetail(page)
    const need = t.needs
    const missing = need.filter(k => !r[`has${k.charAt(0).toUpperCase()}${k.slice(1)}`])
    return missing.length === 0
      ? { ok: true, detail: `${docName} render OK (hero+tiles${need.includes('items') ? '+items' : ''})` }
      : { ok: false, detail: `${docName} thiếu: ${missing.join(', ')} | tiles=${r.hasTiles} hero=${r.hasHero} items=${r.hasItems}` }
  },
}))
