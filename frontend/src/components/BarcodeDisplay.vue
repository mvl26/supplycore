<script setup>
import { ref, watch, onMounted, nextTick } from 'vue'
import JsBarcode from 'jsbarcode'
import Icon from './Icon.vue'

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
// In nhãn chuẩn 50×30mm: mã vạch (kèm mã barcode) ở trên, dưới là tên vật tư + HSD.
function printLabel() {
  const tmp = document.createElementNS('http://www.w3.org/2000/svg', 'svg')
  try {
    // Barcode nhỏ gọn để vừa nhãn 50×30mm; displayValue hiện mã barcode ngay dưới mã vạch.
    JsBarcode(tmp, String(props.value), {
      format: props.format, height: 44, width: 1.6,
      displayValue: true, fontSize: 13, textMargin: 1, margin: 0,
    })
  } catch (e) {
    return
  }
  const svgStr = new XMLSerializer().serializeToString(tmp)
  const esc = (s) => String(s).replace(/[&<>"]/g,
    (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]))
  const win = window.open('', '_blank', 'width=420,height=320')
  if (!win) return
  win.document.write(`<!doctype html><html><head><title>Nhãn ${esc(props.value)}</title>
    <style>
      @page { size: 50mm 30mm; margin: 0; }
      * { box-sizing: border-box; }
      html, body { margin: 0; padding: 0; }
      .label {
        width: 50mm; height: 30mm; padding: 1.5mm 2mm; gap: 0.5mm;
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        font-family: Arial, sans-serif; text-align: center; overflow: hidden;
      }
      .bc { width: 100%; line-height: 0; }
      .bc svg { width: 100%; height: auto; max-height: 14mm; }
      .ln { max-width: 46mm; }
      .name { font-size: 8pt; font-weight: 700; line-height: 1.12;
        display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
      .exp  { font-size: 8pt; line-height: 1.12;
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    </style></head><body>
    <div class="label">
      <div class="bc">${svgStr}</div>
      ${props.title ? `<div class="ln name">${esc(props.title)}</div>` : ''}
      ${props.subtitle ? `<div class="ln exp">${esc(props.subtitle)}</div>` : ''}
    </div>
    <script>window.onload=function(){window.print();setTimeout(function(){window.close()},300)}<\/script>
    </body></html>`)
  win.document.close()
}
</script>

<template>
  <div class="sc-card p-4 mb-4">
    <div class="flex items-center justify-between mb-2">
      <h3 class="font-semibold text-sc-navy flex items-center gap-2"><Icon name="bookmark" :size="18" /> Mã vạch (quét được)</h3>
      <button @click="printLabel" type="button" class="sc-btn-secondary text-sm inline-flex items-center gap-1"
        :disabled="!!error || !value"><Icon name="printer" :size="14" /> In nhãn</button>
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
