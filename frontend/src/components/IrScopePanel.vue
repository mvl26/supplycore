<script setup>
import { computed } from 'vue'
import Icon from './Icon.vue'
import { fmtNumber } from '../utils'

const props = defineProps({
  doc: Object,
})

const hasScope = computed(() =>
  !!(props.doc?.item || props.doc?.warehouse || props.doc?.batch))

const hasComparison = computed(() =>
  props.doc?.theoretical_qty != null || props.doc?.variance_qty != null)

const hasAnomalies = computed(() => {
  if (!props.doc?.anomalies_detected) return false
  try {
    const d = typeof props.doc.anomalies_detected === 'string'
      ? JSON.parse(props.doc.anomalies_detected)
      : props.doc.anomalies_detected
    return d && (Array.isArray(d) ? d.length > 0 : Object.keys(d).length > 0)
  } catch (e) { return false }
})

const anomaliesList = computed(() => {
  if (!hasAnomalies.value) return []
  try {
    const d = typeof props.doc.anomalies_detected === 'string'
      ? JSON.parse(props.doc.anomalies_detected)
      : props.doc.anomalies_detected
    if (Array.isArray(d)) return d
    if (d.anomalies && Array.isArray(d.anomalies)) return d.anomalies
    return []
  } catch (e) { return [] }
})
</script>

<template>
  <div v-if="doc">
    <!-- Banner gợi ý phạm vi nếu thiếu -->
    <div v-if="doc.docstatus === 0 && !hasScope"
      class="sc-card border-l-4 border-sc-warning/40 bg-sc-warning-50 px-4 py-3 mb-4 text-sm">
      <div class="font-semibold text-sc-warning flex items-center gap-1.5"><Icon name="alert-triangle" :size="16" /> Cần xác định phạm vi điều tra</div>
      <div class="text-sc-warning mt-1">
        Phải nhập <strong>ít nhất 1</strong> trong: <em>Vật tư</em>, <em>Kho</em>, <em>Lô</em>.
        Càng cụ thể, audit trail càng chính xác.
      </div>
    </div>

    <!-- Variance summary sau khi đã compare -->
    <div v-if="hasComparison" class="sc-card p-5 mb-4">
      <h3 class="font-semibold text-sc-navy mb-3 flex items-center gap-2">
        <Icon name="git-compare" :size="18" /> Kết quả so sánh tồn kho
      </h3>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div class="border border-sc-border rounded p-3">
          <div class="text-xs text-sc-text-muted">SL lý thuyết (SLE)</div>
          <div class="text-xl font-bold font-mono">{{ fmtNumber(doc.theoretical_qty) }}</div>
        </div>
        <div class="border border-sc-border rounded p-3"
          :class="doc.actual_qty != doc.theoretical_qty ? 'bg-sc-warning-50 border-sc-warning/40' : 'bg-sc-success-50 border-sc-success/40'">
          <div class="text-xs text-sc-text-muted">SL thực tế (đếm)</div>
          <div class="text-xl font-bold font-mono">{{ fmtNumber(doc.actual_qty) }}</div>
        </div>
        <div class="border border-sc-border rounded p-3"
          :class="doc.variance_qty == 0 ? 'border-sc-success/40 bg-sc-success-50' : (doc.variance_qty < 0 ? 'border-sc-danger/40 bg-sc-danger-50' : 'border-sc-info/40 bg-sc-info-50')">
          <div class="text-xs text-sc-text-muted">Δ Số lượng</div>
          <div class="text-xl font-bold font-mono"
            :class="doc.variance_qty < 0 ? 'text-sc-danger' : (doc.variance_qty > 0 ? 'text-sc-info' : 'text-sc-success')">
            {{ doc.variance_qty > 0 ? '+' : '' }}{{ fmtNumber(doc.variance_qty) }}
          </div>
        </div>
        <div class="border border-sc-border rounded p-3"
          :class="doc.variance_value == 0 ? 'border-sc-success/40 bg-sc-success-50' : (doc.variance_value < 0 ? 'border-sc-danger/40 bg-sc-danger-50' : 'border-sc-info/40 bg-sc-info-50')">
          <div class="text-xs text-sc-text-muted">Δ Giá trị (VND)</div>
          <div class="text-lg font-bold font-mono"
            :class="doc.variance_value < 0 ? 'text-sc-danger' : (doc.variance_value > 0 ? 'text-sc-info' : 'text-sc-success')">
            {{ doc.variance_value > 0 ? '+' : '' }}{{ fmtNumber(doc.variance_value) }}
          </div>
        </div>
      </div>
      <div v-if="doc.variance_qty != 0 && doc.docstatus === 0"
        class="mt-3 text-sm text-sc-text-muted">
        <Icon name="info" :size="16" /> Bấm <em>"Tạo SR điều chỉnh"</em> để generate phiếu Stock Reconciliation tự động điều chỉnh tồn kho theo SL đếm tay.
      </div>
    </div>

    <!-- Anomalies cards -->
    <div v-if="hasAnomalies" class="sc-card p-5 mb-4">
      <h3 class="font-semibold text-sc-navy mb-3 flex items-center gap-2">
        <Icon name="alert-triangle" :size="18" />
        Bất thường phát hiện ({{ anomaliesList.length }})
      </h3>
      <div class="space-y-2">
        <div v-for="(a, i) in anomaliesList" :key="i"
          class="border-l-4 border-sc-warning/40 bg-sc-warning-50 p-3 rounded">
          <div class="font-medium text-sc-warning flex items-center gap-2">
            <Icon name="alert-triangle" :size="18" />
            {{ a.type || a.kind || 'Anomaly #' + (i + 1) }}
          </div>
          <div class="text-xs text-sc-warning mt-1 grid grid-cols-2 gap-1">
            <template v-for="(v, k) in a" :key="k">
              <div v-if="k !== 'type' && k !== 'kind'" class="contents">
                <span class="text-sc-warning">{{ k }}:</span>
                <span class="font-mono">{{ typeof v === 'object' ? JSON.stringify(v) : v }}</span>
              </div>
            </template>
          </div>
        </div>
      </div>
    </div>

    <!-- System error adjustment linked -->
    <div v-if="doc.system_error_adjustment"
      class="sc-card border-l-4 border-sc-success/40 bg-sc-success-50 px-4 py-3 mb-4 text-sm">
      <Icon name="check" :size="16" /> <strong>SR điều chỉnh đã được tạo:</strong>
      <router-link :to="`/doc/SC Stock Reconciliation/${encodeURIComponent(doc.system_error_adjustment)}`"
        class="text-sc-royal hover:underline font-mono ml-1">
        {{ doc.system_error_adjustment }}
      </router-link>
    </div>
  </div>
</template>
