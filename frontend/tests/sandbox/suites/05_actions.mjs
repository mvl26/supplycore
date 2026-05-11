// Suite 05: ActionPanel UC actions

export const tests = [
  {
    name: 'ActionPanel hiển thị trên Recall Notice submitted',
    run: async ({ page, BASE, OUT, name }) => {
      // Find a submitted recall notice
      const rcl = await page.evaluate(async () => {
        const r = await fetch('/api/resource/SC%20Recall%20Notice?filters=[["docstatus","=",1]]&limit_page_length=1',
          { credentials: 'include' })
        const d = await r.json()
        return d.data?.[0]?.name || null
      })
      if (!rcl) return { ok: false, detail: 'No submitted RCL exists' }

      await page.goto(`${BASE}/supplycore/doc/SC%20Recall%20Notice/${encodeURIComponent(rcl)}`)
      await page.waitForTimeout(1500)
      const actionBtns = await page.locator('.sc-card').filter({ hasText: 'Hành động khả dụng' }).locator('button').count()
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      return actionBtns >= 2
        ? { ok: true, detail: `${actionBtns} action buttons trên ${rcl}` }
        : { ok: false, detail: `Only ${actionBtns} buttons` }
    },
  },
  {
    name: 'Alert Center filter Critical/Warning/Info',
    run: async ({ page, BASE, OUT, name }) => {
      await page.goto(`${BASE}/supplycore/alerts`)
      await page.waitForTimeout(1500)
      // Click filter "Warning"
      await page.getByRole('button', { name: 'Warning' }).first().click()
      await page.waitForTimeout(1200)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      const cards = await page.locator('.sc-card').filter({ hasText: /Warning/ }).count()
      return cards >= 1
        ? { ok: true, detail: `${cards} Warning alerts` }
        : { ok: false, detail: 'No filtered cards' }
    },
  },
  {
    name: 'LinkAutocomplete: tìm "Khoa" warehouse',
    run: async ({ page, BASE, OUT, name }) => {
      await page.goto(`${BASE}/supplycore/doc/SC%20Material%20Request/new`)
      await page.waitForTimeout(1500)
      // Find SC Warehouse autocomplete (label "Kho nhận")
      const whInput = page.locator('input[placeholder*="Warehouse"], input[placeholder*="Kho"]').first()
      await whInput.click()
      await whInput.fill('Khoa')
      await page.waitForTimeout(800)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      // Suggestion dropdown
      const opts = await page.locator('button').filter({ hasText: /Kho.*Khoa|Khoa.*Kho/ }).count()
      return opts >= 1
        ? { ok: true, detail: `${opts} suggestions` }
        : { ok: false, detail: 'No suggestions' }
    },
  },
]
