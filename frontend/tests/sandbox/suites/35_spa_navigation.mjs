// Suite 35: SPA navigation — clicking sidebar links must render page content.
// Regression guard: a <Transition mode="out-in"> around multi-root page
// components deadlocked the leave step, leaving <main> blank after every
// in-app navigation (fresh page loads were unaffected, so it slipped past
// every goto()-based suite). This suite navigates by CLICKING.

async function mainLen(page) {
  try { return (await page.locator('main').innerText()).length } catch { return -1 }
}

async function clickNavAndCheck(page, hrefEnds, OUT, shotName) {
  await page.locator(`aside a[href$="${hrefEnds}"]`).first().click()
  await page.waitForTimeout(1800)
  const len = await mainLen(page)
  if (OUT && shotName) await page.screenshot({ path: `${OUT}/${shotName}.png` })
  const onRoute = page.url().endsWith(hrefEnds)
  return { onRoute, len, url: page.url() }
}

export const tests = [
  {
    name: 'Click sidebar M0 → trang hiển thị (không trắng)',
    run: async ({ page, OUT, name }) => {
      const r = await clickNavAndCheck(page, '/m0', OUT, name)
      return r.onRoute && r.len > 50
        ? { ok: true, detail: `/m0 render OK — main ${r.len} ký tự` }
        : { ok: false, detail: `BLANK — url=${r.url}, main len=${r.len}` }
    },
  },
  {
    name: 'Click sidebar Tổng quan → Dashboard hiển thị',
    run: async ({ page }) => {
      const r = await clickNavAndCheck(page, '/dashboard')
      return r.onRoute && r.len > 50
        ? { ok: true, detail: `dashboard render OK — main ${r.len} ký tự` }
        : { ok: false, detail: `BLANK — url=${r.url}, main len=${r.len}` }
    },
  },
  {
    name: 'Click sidebar M4 → trang hiển thị',
    run: async ({ page, OUT, name }) => {
      const r = await clickNavAndCheck(page, '/m4', OUT, name)
      return r.onRoute && r.len > 50
        ? { ok: true, detail: `/m4 render OK — main ${r.len} ký tự` }
        : { ok: false, detail: `BLANK — url=${r.url}, main len=${r.len}` }
    },
  },
]
