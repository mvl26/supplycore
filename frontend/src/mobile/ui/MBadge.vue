<template>
  <span :class="['m-badge', 'm-badge--' + variant]">{{ display }}</span>
</template>

<script setup>
import { computed } from 'vue'
const props = defineProps({
  status: { type: String, default: '' },   // qc_status / severity / trạng thái
  label: { type: String, default: '' },     // ép nhãn nếu muốn
})

// status (key tiếng Anh) → { variant, nhãn tiếng Việt }
const MAP = {
  // QC
  Accepted: ['ok', 'Đạt'], Pass: ['ok', 'Đạt'], Rejected: ['crit', 'Không đạt'], Fail: ['crit', 'Không đạt'],
  Pending: ['warn', 'Chờ QC'], Conditional: ['warn', 'Có điều kiện'], 'Partial Pass': ['warn', 'Đạt 1 phần'],
  // Severity
  Critical: ['crit', 'Nghiêm trọng'], High: ['crit', 'Cao'], Warning: ['warn', 'Cảnh báo'],
  Medium: ['warn', 'Trung bình'], Info: ['info', 'Thông tin'], Low: ['info', 'Thấp'],
  // Workflow
  Draft: ['muted', 'Nháp'], Submitted: ['info', 'Đã gửi'], Approved: ['ok', 'Đã duyệt'],
  'Manager Review': ['warn', 'Chờ QL duyệt'], 'Executive Review': ['warn', 'Chờ GĐ duyệt'],
  Active: ['ok', 'Hiệu lực'], Open: ['warn', 'Đang mở'],
}
const variant = computed(() => (MAP[props.status]?.[0]) || 'muted')
const display = computed(() => props.label || MAP[props.status]?.[1] || props.status || '')
</script>
