<template>
  <span :class="['m-badge', 'm-badge--' + badgeVariant]">{{ displayLabel }}</span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  status:  { type: String, default: '' },  // qc_status / severity / trạng thái
  label:   { type: String, default: '' },  // ép nhãn tường minh — screen tự quyết
  variant: { type: String, default: '' },  // ép variant tường minh
  domain:  { type: String, default: '' },  // 'qc' | 'approval' | 'workflow' | ''
})

// Bảng mặc định — gộp mọi domain, dùng khi không truyền domain
const MAP_DEFAULT = {
  '':              ['muted', 'Chưa QC'],
  // QC
  Accepted:        ['ok',   'Đạt'],
  Pass:            ['ok',   'Đạt'],
  Rejected:        ['crit', 'Không đạt'],
  Fail:            ['crit', 'Không đạt'],
  Pending:         ['warn', 'Chờ QC'],
  Conditional:     ['warn', 'Có điều kiện'],
  'Partial Pass':  ['warn', 'Đạt 1 phần'],
  // Mức độ nghiêm trọng
  Critical:        ['crit', 'Nghiêm trọng'],
  High:            ['crit', 'Cao'],
  Warning:         ['warn', 'Cảnh báo'],
  Medium:          ['warn', 'Trung bình'],
  Info:            ['info', 'Thông tin'],
  Low:             ['info', 'Thấp'],
  // Workflow / phê duyệt
  Draft:               ['muted', 'Nháp'],
  Submitted:           ['info',  'Đã gửi'],
  Approved:            ['ok',    'Đã duyệt'],
  'Manager Review':    ['warn',  'Chờ QL duyệt'],
  'Executive Review':  ['warn',  'Chờ GĐ duyệt'],
  Active:              ['ok',    'Hiệu lực'],
  Open:                ['warn',  'Đang mở'],
}

// Ghi đè theo domain — chỉ các key có ngữ nghĩa khác nhau giữa domain
const MAP_QC = {
  '':       ['muted', 'Chưa QC'],
  Pending:  ['warn',  'Chờ QC'],
  Rejected: ['crit',  'Không đạt'],
}
const MAP_APPROVAL = {
  '':       ['muted', 'Chưa duyệt'],
  Pending:  ['warn',  'Chờ duyệt'],
  Rejected: ['crit',  'Từ chối'],
}
const MAP_WORKFLOW = {
  Pending:  ['warn', 'Chờ xử lý'],
  Rejected: ['crit', 'Từ chối'],
}
const DOMAIN_MAPS = { qc: MAP_QC, approval: MAP_APPROVAL, workflow: MAP_WORKFLOW }

// Resolve entry theo domain (ghi đè) → fallback về MAP_DEFAULT
const resolvedEntry = computed(() => {
  const domainMap = props.domain ? DOMAIN_MAPS[props.domain] : null
  if (domainMap && props.status in domainMap) return domainMap[props.status]
  return MAP_DEFAULT[props.status]
})

const badgeVariant = computed(() => props.variant || resolvedEntry.value?.[0] || 'muted')
const displayLabel = computed(() => props.label  || resolvedEntry.value?.[1] || props.status || '')
</script>
