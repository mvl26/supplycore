<script setup>
/* LineItemDetailDrawer — drawer chi tiết 1 DÒNG bảng con, DÙNG CHUNG cho mọi ChildTable.
   - Trượt từ phải, thấy bảng phía sau.
   - Render field theo `groups` (schema.detail.groups); nếu không có → fallback từ columns.
   - Sửa vào bản nháp (draft); "Áp dụng" ghi ngược ra dòng (state form, CHƯA lưu server).
   - Dòng trước/sau để duyệt nhanh (tự áp dụng nếu hợp lệ).
   - Esc / click ngoài → đóng, cảnh báo nếu đang sửa dở.
   - Validation dùng chung rule cột (required, số ≥ 0). */
import { ref, computed, watch, nextTick } from 'vue'
import FormField from './FormField.vue'
import Icon from './Icon.vue'
import { fmtVND } from '../utils'

const props = defineProps({
  open: Boolean,
  row: { type: Object, default: () => ({}) },
  groups: { type: Array, default: () => [] },   // [{ title, fields: [{name,label,type,...}] }]
  parentDoc: { type: Object, default: () => ({}) },
  index: { type: Number, default: 0 },          // 0-based
  total: { type: Number, default: 1 },
  title: { type: String, default: 'Chi tiết dòng' },
})
const emit = defineEmits(['apply', 'close', 'navigate'])  // navigate: -1 / +1

const draft = ref({})
const errors = ref({})
const confirmDiscard = ref(false)

// Nạp bản nháp mỗi khi mở / đổi dòng.
watch(() => [props.open, props.index], () => {
  if (props.open) { draft.value = JSON.parse(JSON.stringify(props.row || {})); errors.value = {}; confirmDiscard.value = false }
}, { immediate: true })

const dirty = computed(() => JSON.stringify(draft.value) !== JSON.stringify(props.row || {}))

const allFields = computed(() => props.groups.flatMap(g => g.fields || []))

// Recompute field tự tính (compute:{from:[...],op:'mul'|'sub'|'add'}) khi sửa.
function recompute() {
  for (const f of allFields.value) {
    if (!f.compute) continue
    const [a, b] = f.compute.from.map(k => Number(draft.value[k]) || 0)
    draft.value[f.name] = f.compute.op === 'mul' ? a * b
      : f.compute.op === 'sub' ? a - b : a + b
  }
}
function onField(name, val) {
  draft.value[name] = val
  if (errors.value[name]) delete errors.value[name]
  recompute()
}

function validate() {
  const e = {}
  for (const f of allFields.value) {
    if (f.readonly || f.compute) continue
    const v = draft.value[f.name]
    if (f.required && (v === '' || v == null)) e[f.name] = `Vui lòng nhập ${f.label}`
    else if (['Float', 'Currency', 'Int', 'Percent'].includes(f.type) && v !== '' && v != null && Number(v) < 0)
      e[f.name] = `${f.label} phải ≥ 0`
  }
  errors.value = e
  return Object.keys(e).length === 0
}

function apply() {
  if (!validate()) return false
  emit('apply', JSON.parse(JSON.stringify(draft.value)))
  return true
}
function applyAndClose() { if (apply()) emit('close') }

function requestClose() {
  if (dirty.value) { confirmDiscard.value = true; return }
  emit('close')
}
function discardClose() { confirmDiscard.value = false; emit('close') }

function navigate(dir) {
  // Duyệt nhanh: nếu đang sửa dở & hợp lệ → áp dụng trước rồi chuyển; nếu lỗi → chặn.
  if (dirty.value) { if (!apply()) return }
  emit('navigate', dir)
}

function onKey(e) {
  if (!props.open) return
  if (e.key === 'Escape') { e.preventDefault(); requestClose() }
}
watch(() => props.open, (o) => {
  if (o) window.addEventListener('keydown', onKey)
  else window.removeEventListener('keydown', onKey)
})

// Hiển thị đẹp cho field readonly Currency ở phần tóm tắt (nếu muốn).
const fmtMoney = (v) => fmtVND(v)
</script>

<template>
  <Teleport to="body">
    <Transition name="sc-drawer">
      <div v-if="open" class="fixed inset-0 z-[70]">
        <!-- scrim (mờ nhẹ để vẫn thấy bảng) -->
        <div class="absolute inset-0 bg-sc-navy-900/25" @click="requestClose" />
        <!-- panel phải -->
        <aside class="sc-drawer-panel absolute inset-y-0 right-0 w-full max-w-[440px] bg-sc-surface
                      shadow-sc-xl border-l border-sc-border flex flex-col"
          role="dialog" aria-modal="true" :aria-label="title">
          <!-- Header -->
          <div class="flex items-center justify-between px-4 h-[56px] border-b border-sc-border flex-shrink-0">
            <div class="min-w-0">
              <div class="font-bold text-[15px] text-sc-navy truncate">{{ title }}</div>
              <div class="text-[11px] text-sc-text-muted">Dòng {{ index + 1 }} / {{ total }}</div>
            </div>
            <div class="flex items-center gap-1">
              <button type="button" class="sc-icon-btn" :disabled="index <= 0"
                title="Dòng trước" @click="navigate(-1)"><Icon name="chevron-up" :size="18" /></button>
              <button type="button" class="sc-icon-btn" :disabled="index >= total - 1"
                title="Dòng sau" @click="navigate(1)"><Icon name="chevron-down" :size="18" /></button>
              <button type="button" class="sc-icon-btn" aria-label="Đóng" @click="requestClose">
                <Icon name="x" :size="18" /></button>
            </div>
          </div>

          <!-- Body: các section -->
          <div class="flex-1 overflow-y-auto px-4 py-3 space-y-4">
            <section v-for="g in groups" :key="g.title">
              <h4 class="text-[11px] font-bold uppercase tracking-wide text-sc-text-muted mb-2
                         flex items-center gap-1.5">
                <Icon v-if="g.icon" :name="g.icon" :size="13" /> {{ g.title }}
              </h4>
              <div class="space-y-2.5">
                <div v-for="f in g.fields" :key="f.name"
                  :class="{ 'sc-field-invalid': errors[f.name] }">
                  <FormField
                    :field="{ ...f, readonly: f.readonly || !!f.compute }"
                    :model-value="draft[f.name]"
                    :context="draft" :parent-doc="parentDoc" :show-label="true"
                    @update:model-value="v => onField(f.name, v)" />
                  <div v-if="errors[f.name]" class="text-xs text-sc-danger mt-1">{{ errors[f.name] }}</div>
                </div>
              </div>
            </section>
          </div>

          <!-- Bar xác nhận bỏ thay đổi (inline, không dùng confirm native) -->
          <div v-if="confirmDiscard"
            class="px-4 py-3 border-t border-sc-warning/40 bg-sc-warning-50 flex items-center justify-between flex-shrink-0">
            <span class="text-xs text-sc-warning flex items-center gap-1.5">
              <Icon name="alert-triangle" :size="14" /> Bỏ thay đổi chưa áp dụng?
            </span>
            <div class="flex gap-2">
              <button type="button" class="sc-btn-secondary text-xs" @click="confirmDiscard = false">Ở lại</button>
              <button type="button" class="sc-btn-danger text-xs" @click="discardClose">Bỏ & đóng</button>
            </div>
          </div>
          <!-- Footer -->
          <div v-else class="px-4 py-3 border-t border-sc-border bg-sc-bg-soft/60 flex items-center justify-between flex-shrink-0">
            <span v-if="dirty" class="text-[11px] text-sc-warning flex items-center gap-1">
              <Icon name="alert-triangle" :size="12" /> Chưa áp dụng
            </span><span v-else></span>
            <div class="flex gap-2">
              <button type="button" class="sc-btn-secondary text-sm" @click="requestClose">Đóng</button>
              <button type="button" class="sc-btn-primary text-sm" :disabled="!dirty" @click="applyAndClose">
                Áp dụng
              </button>
            </div>
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
