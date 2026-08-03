<script setup>
/* DocPreviewDrawer — xem nhanh CHI TIẾT 1 phiếu tham chiếu ngay tại chỗ.
   Trượt từ phải; tải phiếu qua getDoc; hiện các trường chính (bỏ bảng con);
   nút "Mở phiếu" để vào trang đầy đủ. Dùng cho mọi trường Link/tham chiếu. */
import { ref, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import { getDoc } from '../api'
import Icon from './Icon.vue'
import { fieldLabel } from '../i18n'
import { DT, statusLabel, STATUS_BADGE } from '../modules'
import { fmtDate, fmtDateTime, fmtNumber, fmtVND } from '../utils'

const props = defineProps({
  open: Boolean,
  doctype: { type: String, default: '' },
  name: { type: String, default: '' },
})
const emit = defineEmits(['close'])
const router = useRouter()

const doc = ref(null)
const loading = ref(false)
const error = ref('')

const SKIP = new Set(['doctype', 'name', 'parent', 'parentfield', 'parenttype', 'idx',
  'owner', 'creation', 'modified', 'modified_by', 'docstatus',
  'lft', 'rgt', 'old_parent', 'amended_from', 'naming_series'])
const STATUS_KEYS = new Set(['status', 'qc_status', 'overall_status', 'severity',
  'approval_stage', 'request_type', 'entry_type', 'recall_status', 'return_status'])

const cfg = computed(() => DT[props.doctype])
const rows = computed(() => {
  if (!doc.value) return []
  const out = []
  for (const [k, v] of Object.entries(doc.value)) {
    if (SKIP.has(k) || k.startsWith('_')) continue
    if (Array.isArray(v)) continue          // bỏ bảng con trong xem nhanh
    if (v == null || v === '') continue
    out.push({ key: k, value: v })
  }
  return out.slice(0, 24)
})

// Bảng con (vd dòng vật tư của HĐ khung / đơn hàng) — hiện để "biết nội dung".
const childTables = computed(() => {
  if (!doc.value) return []
  const out = []
  for (const [k, v] of Object.entries(doc.value)) {
    if (!Array.isArray(v) || !v.length || typeof v[0] !== 'object') continue
    const cols = Object.keys(v[0])
      .filter(c => !SKIP.has(c) && !c.startsWith('_')).slice(0, 5)
    out.push({ key: k, cols, rows: v.slice(0, 30) })
  }
  return out
})

function isStatus(key) { return STATUS_KEYS.has(key) }
function fmt(value, key) {
  if (typeof value === 'object') return ''
  if (/_date$/.test(key)) return fmtDate(value)
  if (/_at$/.test(key)) return fmtDateTime(value)
  if (STATUS_KEYS.has(key) && typeof value === 'string') return statusLabel(value, key)
  if (/value|amount|total|cost|price|rate/.test(key) && typeof value === 'number') return fmtVND(value)
  if (typeof value === 'number') {
    if ((value === 0 || value === 1) &&
        /^(is_|has_|allow_|auto_|default_|enabled|require|active|blocked)/i.test(key))
      return value === 1 ? 'Có' : 'Không'
    return fmtNumber(value)
  }
  return value
}

async function load() {
  if (!props.doctype || !props.name) return
  loading.value = true; error.value = ''; doc.value = null
  try {
    doc.value = await getDoc(props.doctype, props.name)
  } catch (e) {
    error.value = e.message || 'Không tải được phiếu tham chiếu'
  } finally {
    loading.value = false
  }
}
watch(() => [props.open, props.doctype, props.name],
  () => { if (props.open) load() }, { immediate: true })

function openFull() {
  emit('close')
  router.push(`/doc/${encodeURIComponent(props.doctype)}/${encodeURIComponent(props.name)}`)
}
function onKey(e) { if (props.open && e.key === 'Escape') { e.preventDefault(); emit('close') } }
watch(() => props.open, (o) => {
  o ? window.addEventListener('keydown', onKey) : window.removeEventListener('keydown', onKey)
})
</script>

<template>
  <Teleport to="body">
    <Transition name="sc-drawer">
      <div v-if="open" class="fixed inset-0 z-[75]">
        <div class="absolute inset-0 bg-sc-navy-900/25" @click="$emit('close')" />
        <aside class="sc-drawer-panel absolute inset-y-0 right-0 w-full max-w-[420px] bg-sc-surface
                      shadow-sc-xl border-l border-sc-border flex flex-col"
          role="dialog" aria-modal="true" :aria-label="`Chi tiết ${doctype}`">
          <!-- Header -->
          <div class="flex items-center justify-between px-4 h-[56px] border-b border-sc-border flex-shrink-0 gap-2">
            <div class="min-w-0 flex items-center gap-2">
              <Icon :name="cfg?.icon || 'file-text'" :size="18" class="text-sc-royal flex-shrink-0" />
              <div class="min-w-0">
                <div class="font-bold text-[14px] text-sc-navy truncate">{{ cfg?.label || doctype }}</div>
                <div class="text-[11px] text-sc-text-muted font-mono truncate">{{ name }}</div>
              </div>
            </div>
            <div class="flex items-center gap-1 flex-shrink-0">
              <button type="button" class="sc-btn-secondary text-xs" @click="openFull" title="Mở phiếu đầy đủ">
                <Icon name="external-link" :size="14" /> Mở phiếu
              </button>
              <button type="button" class="sc-icon-btn" aria-label="Đóng" @click="$emit('close')">
                <Icon name="x" :size="18" />
              </button>
            </div>
          </div>
          <!-- Body -->
          <div class="flex-1 overflow-y-auto px-4 py-3">
            <div v-if="loading" class="space-y-2 py-2">
              <div v-for="n in 7" :key="n" class="sc-skeleton h-6 w-full" :style="{ opacity: 1 - n * 0.1 }" />
            </div>
            <div v-else-if="error" class="text-sm text-sc-danger py-4 flex items-start gap-2">
              <Icon name="alert-triangle" :size="16" class="mt-0.5 flex-shrink-0" /> {{ error }}
            </div>
            <dl v-else class="text-sm">
              <div v-for="r in rows" :key="r.key"
                class="grid grid-cols-[130px_1fr] gap-2 py-1.5 border-b border-sc-border/50 last:border-0">
                <dt class="text-sc-text-muted truncate">{{ fieldLabel(r.key) }}</dt>
                <dd class="break-all">
                  <span v-if="isStatus(r.key)" :class="['sc-badge', STATUS_BADGE[r.value] || 'sc-badge-neutral']">
                    {{ fmt(r.value, r.key) }}
                  </span>
                  <span v-else class="text-sc-text font-medium">{{ fmt(r.value, r.key) }}</span>
                </dd>
              </div>
            </dl>
            <!-- Bảng con (dòng vật tư / chi tiết) -->
            <section v-for="ct in childTables" :key="ct.key" class="mt-4">
              <h4 class="text-[11px] font-bold uppercase tracking-wide text-sc-text-muted mb-1.5">
                {{ fieldLabel(ct.key) }} ({{ ct.rows.length }})
              </h4>
              <div class="overflow-x-auto border border-sc-border rounded-lg">
                <table class="w-full text-xs">
                  <thead>
                    <tr class="bg-sc-bg-soft">
                      <th v-for="c in ct.cols" :key="c"
                        class="text-left px-2 py-1.5 font-semibold text-sc-text-muted whitespace-nowrap">
                        {{ fieldLabel(c) }}
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(row, i) in ct.rows" :key="i" class="border-t border-sc-border/50">
                      <td v-for="c in ct.cols" :key="c" class="px-2 py-1"
                        :class="typeof row[c] === 'number' ? 'text-right font-mono' : ''">
                        {{ fmt(row[c], c) }}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </section>
          </div>
        </aside>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.sc-drawer-enter-active, .sc-drawer-leave-active { transition: opacity .2s ease; }
.sc-drawer-enter-from, .sc-drawer-leave-to { opacity: 0; }
.sc-drawer-enter-active .sc-drawer-panel { transition: transform .28s cubic-bezier(0.22,1,0.36,1); }
.sc-drawer-leave-active .sc-drawer-panel { transition: transform .2s ease; }
.sc-drawer-enter-from .sc-drawer-panel, .sc-drawer-leave-to .sc-drawer-panel { transform: translateX(100%); }
</style>
