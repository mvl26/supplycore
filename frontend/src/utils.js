// Util helpers

export const today = () => new Date().toISOString().slice(0, 10)

export const fmtVND = (v) => new Intl.NumberFormat('vi-VN', {
  style: 'currency', currency: 'VND', maximumFractionDigits: 0,
}).format(Number(v) || 0)

export const fmtNumber = (v) => new Intl.NumberFormat('vi-VN').format(Number(v) || 0)

export const fmtShort = (v) => {
  const n = Number(v) || 0
  if (Math.abs(n) >= 1e9) return (n / 1e9).toFixed(2) + ' tỷ'
  if (Math.abs(n) >= 1e6) return (n / 1e6).toFixed(1) + ' tr'
  if (Math.abs(n) >= 1e3) return (n / 1e3).toFixed(1) + 'k'
  return n.toLocaleString('vi-VN')
}

export const fmtDate = (v) => v ? new Date(v).toLocaleDateString('vi-VN') : ''
export const fmtDateTime = (v) => v ? new Date(v).toLocaleString('vi-VN') : ''
