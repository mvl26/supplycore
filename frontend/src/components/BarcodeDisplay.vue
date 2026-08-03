<script setup>
import { ref, watch, onMounted, nextTick } from 'vue'
import JsBarcode from 'jsbarcode'
import Icon from './Icon.vue'
import { printLabels } from '../utils/labels'

const props = defineProps({
  value:   { type: String, required: true },   // mã để mã hoá thành barcode
  title:   { type: String, default: '' },      // dòng tiêu đề trên nhãn in
  subtitle:{ type: String, default: '' },      // dòng phụ (vd item, kho)
  lines:   { type: Array, default: () => [] }, // các dòng thông tin thêm trên nhãn (vd NSX/HSD/Lô NCC/Model/Xuất xứ)
  format:  { type: String, default: 'CODE128' },
})

const svgRef = ref(null)
const error = ref('')
const qty = ref(1)   // số nhãn cần in cho lô này (1 lô có thể dán nhiều tem)

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

// In 1 nhãn — dùng chung util printLabels (in hàng loạt cũng dùng util này).
function printLabel() {
  printLabels([{
    value: props.value, title: props.title, subtitle: props.subtitle,
    lines: props.lines, format: props.format,
    copies: qty.value,
  }])
}
</script>

<template>
  <div class="sc-card p-4 mb-4">
    <div class="flex items-center justify-between mb-2">
      <h3 class="font-semibold text-sc-navy flex items-center gap-2"><Icon name="bookmark" :size="18" /> Mã vạch (quét được)</h3>
      <div class="flex items-center gap-2">
        <label class="text-xs text-sc-text-muted">Số nhãn</label>
        <input v-model.number="qty" type="number" min="1" max="200"
          class="sc-input py-1 w-16 text-sm text-center" title="Số tem cần in cho lô này" />
        <button @click="printLabel" type="button" class="sc-btn-secondary text-sm inline-flex items-center gap-1"
          :disabled="!!error || !value"><Icon name="printer" :size="14" /> In {{ qty > 1 ? qty + ' nhãn' : 'nhãn' }}</button>
      </div>
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
