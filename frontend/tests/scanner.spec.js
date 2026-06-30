// @vitest-environment happy-dom
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'

vi.mock('@capacitor/core', () => ({ Capacitor: { isNativePlatform: () => false } }))  // web

describe('scanner', () => {
  it('runScan() trả null trên web (không native)', async () => {
    const { useScannerStore } = await import('../src/mobile/scanner.js')
    const { runScan, scanning } = useScannerStore()
    expect(await runScan()).toBe(null)
    expect(scanning.value).toBe(false)
  })
  it('ScanOverlay render nút Huỷ khi scanning=true', async () => {
    const mod = await import('../src/mobile/scanner.js')
    const { scanning } = mod.useScannerStore()
    const Overlay = (await import('../src/mobile/ui/ScanOverlay.vue')).default
    scanning.value = true
    const w = mount(Overlay, { attachTo: document.body })
    await new Promise(r=>setTimeout(r,10))
    expect(document.body.textContent).toContain('Huỷ')
    scanning.value = false
    w.unmount()
  })
})
