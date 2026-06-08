import sharp from 'sharp'
import { mkdirSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const OUT = resolve(__dirname, '../public/icons')
mkdirSync(OUT, { recursive: true })

// Logo mark SupplyCore (đồng bộ với AppShell.vue): ô bo góc gradient Navy + dấu cộng trắng.
const mark = (size, { maskable = false } = {}) => {
  const pad = maskable ? Math.round(size * 0.185) : Math.round(size * 0.06)
  const inner = size - pad * 2
  const r = Math.round(inner * 0.22)
  const cx = size / 2
  const stroke = Math.max(2, Math.round(inner * 0.092))
  const arm = inner * 0.225
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 ${size} ${size}">
    <defs><linearGradient id="g" x1="0" y1="0" x2="${size}" y2="${size}" gradientUnits="userSpaceOnUse">
      <stop stop-color="#7FB4E0"/><stop offset="1" stop-color="#1F4E79"/></linearGradient></defs>
    ${maskable ? `<rect width="${size}" height="${size}" fill="#1F4E79"/>` : ''}
    <rect x="${pad}" y="${pad}" width="${inner}" height="${inner}" rx="${r}" fill="url(#g)"/>
    <path d="M${cx} ${cx - arm}V${cx + arm} M${cx - arm} ${cx}H${cx + arm}"
      stroke="#FFFFFF" stroke-width="${stroke}" stroke-linecap="round"/>
  </svg>`
}

const render = (size, file, opts) =>
  sharp(Buffer.from(mark(size, opts))).png().toFile(resolve(OUT, file))

await Promise.all([
  render(192, 'icon-192.png'),
  render(512, 'icon-512.png'),
  render(512, 'icon-maskable-512.png', { maskable: true }),
  render(180, 'apple-touch-icon.png'),
])
console.log('icons → frontend/public/icons/')
