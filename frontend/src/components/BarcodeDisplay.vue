<script setup>
import { ref, watch, onMounted, nextTick } from 'vue'
import JsBarcode from 'jsbarcode'

const props = defineProps({
  value:   { type: String, required: true },   // mã để mã hoá thành barcode
  title:   { type: String, default: '' },      // dòng tiêu đề trên nhãn in
  subtitle:{ type: String, default: '' },      // dòng phụ (vd item, kho)
  format:  { type: String, default: 'CODE128' },
})

const svgRef = ref(null)
const error = ref('')

function render() {
  if (!svgRef.value || !props.value) return
  error.value = ''
  try {
    JsBarcode(svgRef.value, String(props.value), {
      format: props.format,
      height: 56,
      width: 2,
      displayValue: true,
      fontSize: 14,
      textMargin: 4,
      margin: 6,
      background: '#ffffff',
    })
  } catch (e) {
    error.value = `Không tạo được mã vạch cho "${props.value}"`
  }
}

watch(() => props.value, () => nextTick(render))
onMounted(render)

// In nhãn: render barcode vào SVG tách rời → mở cửa sổ in
function printLabel() {
  const tmp = document.createElementNS('http://www.w3.org/2000/svg', 'svg')
  try {
    JsBarcode(tmp, String(props.value), {
      format: props.format, height: 70, width: 2,
      displayValue: true, fontSize: 16, margin: 8,
    })
  } catch (e) {
    return
  }
  const svgStr = new XMLSerializer().serializeToString(tmp)
  const win = window.open('', '_blank', 'width=480,height=360')
  if (!win) return
  win.document.write(`<!doctype html><html><head><title>Nhãn ${props.value}</title>
    <style>
      @page { margin: 6mm; }
      body { font-family: Arial, sans-serif; text-align: center; margin: 0; padding: 12px; }
      .t { font-size: 13px; font-weight: 700; margin-bottom: 2px; }
      .s { font-size: 11px; color: #444; margin-bottom: 8px; }
      svg { max-width: 100%; }
    </style></head><body>
    ${props.title ? `<div class="t">${props.title}</div>` : ''}
    ${props.subtitle ? `<div class="s">${props.subtitle}</div>` : ''}
    ${svgStr}
    <script>window.onload=function(){window.print();setTimeout(function(){window.close()},300)}<\/script>
    </body></html>`)
  win.document.close()
}
</script>

<template>
  <div class="sc-card p-4 mb-4">
    <div class="flex items-center justify-between mb-2">
      <h3 class="font-semibold text-sc-navy">🔖 Mã vạch (quét được)</h3>
      <button @click="printLabel" type="button" class="sc-btn-secondary text-sm"
        :disabled="!!error || !value">🖨 In nhãn</button>
    </div>
    <div v-if="error" class="text-sm text-sc-danger">{{ error }}</div>
    <div v-else class="flex flex-col items-center">
      <svg ref="svgRef" class="max-w-full"></svg>
      <p class="text-xs text-sc-text-muted mt-1">
        Quét bằng đầu đọc mã vạch để tra cứu nhanh
      </p>
    </div>
  </div>
</template>
