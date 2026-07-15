// Suite 00: Login + dashboard load

export const tests = [
  {
    name: 'Dashboard hiển thị sau login',
    run: async ({ page, BASE, OUT, name }) => {
      // login() đã chạy trong runner
      const url = page.url()
      const onDashboard = url === `${BASE}/supplycore/` || url === `${BASE}/supplycore/dashboard`
      if (!onDashboard) return { ok: false, detail: `URL: ${url}` }
      await page.waitForTimeout(800)
      const kpis = await page.locator('.sc-card').filter({ hasText: /Tổng giá trị|Chi phí|Công nợ/ }).count()
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      return kpis >= 3
        ? { ok: true, detail: `${kpis} KPI cards` }
        : { ok: false, detail: `Only ${kpis} KPI cards` }
    },
  },
  {
    name: 'Top items table có data',
    run: async ({ page, OUT, name }) => {
      const rows = await page.locator('table tbody tr').count()
      return rows >= 1
        ? { ok: true, detail: `${rows} rows` }
        : { ok: false, detail: 'No rows' }
    },
  },
  {
    name: 'Sidebar có M0..M11 (12 modules)',
    run: async ({ page }) => {
      const items = await page.locator('aside a[href^="/supplycore/m"]').count()
      return items >= 12
        ? { ok: true, detail: `${items} module links` }
        : { ok: false, detail: `Only ${items} module links` }
    },
  },
  {
    name: 'User menu logout button visible',
    run: async ({ page, OUT, name }) => {
      // Click the user menu trigger in header
      const trigger = page.locator('header button').filter({ hasText: /Administrator|User/i }).first()
      await trigger.waitFor({ state: 'visible', timeout: 5000 })
      await trigger.click({ force: true })
      await page.waitForTimeout(500)
      await page.screenshot({ path: `${OUT}/${name}.png` })
      // Logout button text inside the dropdown
      const logout = await page.locator('button:has-text("Đăng xuất")').count()
      return logout >= 1
        ? { ok: true, detail: 'Logout visible' }
        : { ok: false, detail: 'No logout button after click' }
    },
  },
]
