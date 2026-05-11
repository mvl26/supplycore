// Suite 01: M0 Master Data module

export const tests = [
  {
    name: 'M0 Hub render',
    run: async ({ page, BASE, OUT, name }) => {
      await page.goto(`${BASE}/supplycore/m0`)
      await page.waitForTimeout(1500)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      const title = await page.locator('h1').first().textContent()
      const cards = await page.locator('.sc-card').filter({ hasText: /Vật tư|UOM|NCC|Kho|BHYT/ }).count()
      return title?.includes('Master Data') && cards >= 5
        ? { ok: true, detail: `Title="${title}", ${cards} doctype cards` }
        : { ok: false, detail: `Title="${title}", ${cards} cards` }
    },
  },
  {
    name: 'List SC Item — có rows',
    run: async ({ page, BASE, OUT, name }) => {
      await page.goto(`${BASE}/supplycore/list/SC%20Item`)
      await page.waitForTimeout(1500)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      const rows = await page.locator('table tbody tr').count()
      return rows >= 1 ? { ok: true, detail: `${rows} items` } : { ok: false, detail: 'No rows' }
    },
  },
  {
    name: 'List SC Supplier — có rows',
    run: async ({ page, BASE, OUT, name }) => {
      await page.goto(`${BASE}/supplycore/list/SC%20Supplier`)
      await page.waitForTimeout(1500)
      const rows = await page.locator('table tbody tr').count()
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      return rows >= 1 ? { ok: true, detail: `${rows} suppliers` } : { ok: false, detail: 'No rows' }
    },
  },
  {
    name: 'Form tạo SC UOM',
    run: async ({ page, BASE, OUT, name }) => {
      await page.goto(`${BASE}/supplycore/doc/SC%20UOM/new`)
      await page.waitForTimeout(1500)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      const inputs = await page.locator('input').count()
      return inputs >= 2 ? { ok: true, detail: `${inputs} inputs` } : { ok: false, detail: `Only ${inputs}` }
    },
  },
  {
    name: 'Form tạo SC Patient — có 3 sections',
    run: async ({ page, BASE, OUT, name }) => {
      await page.goto(`${BASE}/supplycore/doc/SC%20Patient/new`)
      await page.waitForTimeout(1500)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      const sections = await page.locator('h3').count()
      return sections >= 3 ? { ok: true, detail: `${sections} sections` } : { ok: false, detail: `Only ${sections}` }
    },
  },
  {
    name: 'Form tạo SC GL Account',
    run: async ({ page, BASE, OUT, name }) => {
      await page.goto(`${BASE}/supplycore/doc/SC%20GL%20Account/new`)
      await page.waitForTimeout(1500)
      const inputs = await page.locator('input, select').count()
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      return inputs >= 4 ? { ok: true, detail: `${inputs} fields` } : { ok: false, detail: `Only ${inputs}` }
    },
  },
]
