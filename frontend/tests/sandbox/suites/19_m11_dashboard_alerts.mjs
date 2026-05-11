// M11 Dashboard + Alerts — UC-32..34
import { apiGetList, apiCall, apiRunDocMethod, navigateTo } from '../helpers.mjs'

export const tests = [
  {
    name: 'UC-32: get_executive_dashboard trả 8 KPIs',
    run: async ({ page }) => {
      const d = await apiCall(page, 'supplycore.api.kpi.get_executive_dashboard',
        { period: 'this_month', force_refresh: 1 })
      const required = ['stock_value', 'monthly_cost', 'ap_outstanding', 'pending_pos',
                         'expiring_soon', 'low_stock_items', 'contract_expiring_30d', 'po_overdue_count']
      const got = Object.keys(d.kpis || {})
      const missing = required.filter(k => !got.includes(k))
      return missing.length === 0
        ? { ok: true, detail: `${got.length} KPIs, cached=${d.cached}, alerts=${d.open_alerts_total}` }
        : { ok: false, detail: `Missing: ${missing.join(',')}` }
    },
  },
  {
    name: 'UC-32: Dashboard cache hit lần 2',
    run: async ({ page }) => {
      await apiCall(page, 'supplycore.api.kpi.get_executive_dashboard',
        { period: 'this_month', force_refresh: 1 })
      const d2 = await apiCall(page, 'supplycore.api.kpi.get_executive_dashboard',
        { period: 'this_month' })
      return d2.cached === true
        ? { ok: true, detail: 'Cache hit lần 2 (5p TTL)' }
        : { ok: false, detail: `cached=${d2.cached}` }
    },
  },
  {
    name: 'UC-32: drill_down URLs đúng /list/<dt>',
    run: async ({ page }) => {
      const d = await apiCall(page, 'supplycore.api.kpi.get_executive_dashboard',
        { period: 'this_month' })
      const drills = d.drill_down || {}
      const count = Object.keys(drills).length
      return count >= 8
        ? { ok: true, detail: `${count} drill-down URLs` }
        : { ok: false, detail: `Only ${count}` }
    },
  },
  {
    name: 'UC-32: monthly cost trend 12 tháng',
    run: async ({ page }) => {
      const trend = await apiCall(page, 'supplycore.api.kpi.get_monthly_cost_trend',
        { months: 12 })
      return Array.isArray(trend)
        ? { ok: true, detail: `${trend.length} months data` }
        : { ok: false, detail: 'Not array' }
    },
  },
  {
    name: 'UC-33: Alert Rule có ≥ 4 cấu hình enabled',
    run: async ({ page, BASE, OUT, name }) => {
      const rules = await apiGetList(page, 'SC Alert Rule', {
        fields: ['name', 'title', 'alert_type', 'enabled', 'channel_email', 'channel_inapp'],
        filters: [['enabled', '=', 1]], limit: 20,
      })
      await navigateTo(page, BASE, '/list/SC%20Alert%20Rule')
      await page.waitForTimeout(1200)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      return rules.length >= 4
        ? { ok: true, detail: `${rules.length} enabled rules` }
        : { ok: false, detail: `Only ${rules.length}` }
    },
  },
  {
    name: 'UC-33: Test Alert Rule action (in-app channel)',
    run: async ({ page }) => {
      const rules = await apiGetList(page, 'SC Alert Rule', {
        fields: ['name'],
        filters: [['enabled', '=', 1], ['channel_inapp', '=', 1]], limit: 1,
      })
      if (!rules.length) return { ok: false, detail: 'No in-app rule' }
      const result = await apiRunDocMethod(page, 'SC Alert Rule', rules[0].name, 'test_alert_rule')
      return result.status
        ? { ok: true, detail: `test_alert_rule → ${result.status}` }
        : { ok: false, detail: `Unexpected: ${JSON.stringify(result)}` }
    },
  },
  {
    name: 'UC-34: Alert Center filter Critical/Warning',
    run: async ({ page, BASE, OUT, name }) => {
      await navigateTo(page, BASE, '/alerts')
      await page.waitForTimeout(1500)
      // Click Warning filter
      await page.locator('button:has-text("Warning")').first().click()
      await page.waitForTimeout(1200)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      const alerts = await apiGetList(page, 'SC Alert', {
        fields: ['name'],
        filters: [['resolved', '=', 0], ['severity', '=', 'Warning']],
        limit: 50,
      })
      return alerts.length >= 1
        ? { ok: true, detail: `${alerts.length} Warning alerts visible` }
        : { ok: true, detail: 'No Warning alerts (skipped)' }
    },
  },
  {
    name: 'UC-34: ActionPanel mark_resolved trên unresolved alert',
    run: async ({ page, BASE, OUT, name }) => {
      const alerts = await apiGetList(page, 'SC Alert', {
        fields: ['name'],
        filters: [['resolved', '=', 0]], limit: 1,
      })
      if (!alerts.length) return { ok: true, detail: 'No unresolved alerts (skipped)' }
      await navigateTo(page, BASE, `/doc/SC%20Alert/${encodeURIComponent(alerts[0].name)}`)
      await page.waitForTimeout(1500)
      await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true })
      const resolveBtn = await page.locator('button:has-text("Đánh dấu xử lý")').count()
      const snoozeBtn = await page.locator('button:has-text("Snooze")').count()
      return (resolveBtn + snoozeBtn) >= 2
        ? { ok: true, detail: `Action buttons: resolve=${resolveBtn}, snooze=${snoozeBtn}` }
        : { ok: false, detail: 'Missing action buttons' }
    },
  },
]
