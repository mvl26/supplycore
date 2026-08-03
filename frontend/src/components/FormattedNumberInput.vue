<script setup>
/* Ô nhập SỐ có ngăn cách hàng nghìn kiểu Việt Nam (dấu "." mỗi 3 chữ số,
   dấu "," thập phân) — dễ đọc khi nhập giá tiền. Lưu/emit là SỐ thô. */
import { ref, watch, nextTick } from 'vue'

const props = defineProps({
  modelValue: { type: [Number, String], default: null },
  id: String,
  readonly: Boolean,
  placeholder: String,
  allowDecimal: { type: Boolean, default: true },   // Int/Percent nguyên → false
})
const emit = defineEmits(['update:modelValue'])

const display = ref('')
const el = ref(null)

function groupInt(s) {
  return (s || '').replace(/\B(?=(\d{3})+(?!\d))/g, '.')
}
function fmtFromNumber(v) {
  if (v == null || v === '') return ''
  let s = String(v)
  const neg = s.startsWith('-'); if (neg) s = s.slice(1)
  let [ip, dp] = s.split('.')
  ip = ip || '0'
  return (neg ? '-' : '') + groupInt(ip) + (dp != null && dp !== '' ? ',' + dp : '')
}
function parseToNumber(disp) {
  if (disp === '' || disp === '-' || disp == null) return null
  const neg = disp.startsWith('-')
  const cleaned = disp.replace(/-/g, '').replace(/\./g, '').replace(',', '.')
  const n = Number((neg ? '-' : '') + cleaned)
  return Number.isFinite(n) ? n : null
}

// Đồng bộ display khi modelValue đổi TỪ NGOÀI (không phải do đang gõ).
watch(() => props.modelValue, (v) => {
  const shown = parseToNumber(display.value)
  const incoming = v == null || v === '' ? null : Number(v)
  if (shown !== incoming) display.value = fmtFromNumber(v)
}, { immediate: true })

function onInput(e) {
  const raw = e.target.value
  const selStart = e.target.selectionStart ?? raw.length
  // số ký tự "có nghĩa" (không phải dấu ngăn cách ".") trước con trỏ → phục hồi vị trí sau
  const meaningfulBefore = raw.slice(0, selStart).replace(/\./g, '').length

  let s = raw.replace(/[^\d,\-]/g, '')
  const neg = s.startsWith('-'); s = s.replace(/-/g, '')
  let ip, dp
  if (props.allowDecimal) {
    const parts = s.split(',')
    ip = parts[0]
    dp = parts.length > 1 ? parts.slice(1).join('') : undefined
  } else {
    ip = s.replace(/,/g, ''); dp = undefined
  }
  const formatted = (neg ? '-' : '') + groupInt(ip) + (dp !== undefined ? ',' + dp : '')
  display.value = formatted
  emit('update:modelValue', parseToNumber(formatted))

  nextTick(() => {
    if (!el.value) return
    let count = 0, pos = 0
    while (pos < formatted.length && count < meaningfulBefore) {
      if (formatted[pos] !== '.') count++
      pos++
    }
    try { el.value.setSelectionRange(pos, pos) } catch (_) { /* ignore */ }
  })
}
</script>

<template>
  <input ref="el" :id="id" type="text" inputmode="decimal"
    :value="display" :readonly="readonly" :placeholder="placeholder"
    @input="onInput" />
</template>
