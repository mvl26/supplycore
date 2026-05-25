<script setup>
import { ref, watch, nextTick, onBeforeUnmount } from 'vue'
import { getList } from '../api'

const props = defineProps({
  modelValue: String,
  linkTo:     { type: String, required: true },
  placeholder: String,
  required:   Boolean,
  readonly:   Boolean,
  size:       { type: String, default: 'normal' }, // normal/sm
  allowCreate: Boolean,                            // hiển thị "+ Tạo mới"
  extraFilters: { type: Array, default: () => [] }, // [[field, op, value], ...] AND với search
})
const emit = defineEmits(['update:modelValue', 'selected', 'createNew'])

// Re-fetch khi extraFilters đổi (vd: row.item thay đổi → filter dropdown đổi theo)
watch(() => JSON.stringify(props.extraFilters), () => {
  results.value = []
  if (open.value) doSearch(search.value)
})

const open = ref(false)
const search = ref(props.modelValue || '')
const results = ref([])
const loading = ref(false)
const inputEl = ref(null)
const dropdownStyle = ref({})

watch(() => props.modelValue, (v) => {
  if (v !== search.value) search.value = v || ''
})

async function positionDropdown() {
  await nextTick()
  if (!inputEl.value) return
  const r = inputEl.value.getBoundingClientRect()
  const vh = window.innerHeight
  const spaceBelow = vh - r.bottom
  const above = spaceBelow < 240 && r.top > 240
  dropdownStyle.value = {
    position: 'fixed',
    top: above ? 'auto' : `${r.bottom + 4}px`,
    bottom: above ? `${vh - r.top + 4}px` : 'auto',
    left: `${r.left}px`,
    minWidth: `${Math.max(r.width, 320)}px`,
    maxWidth: '480px',
    zIndex: 1000,
  }
}
function onScroll() { if (open.value) positionDropdown() }
window.addEventListener('scroll', onScroll, true)
window.addEventListener('resize', onScroll)
onBeforeUnmount(() => {
  window.removeEventListener('scroll', onScroll, true)
  window.removeEventListener('resize', onScroll)
})

async function doSearch(q) {
  loading.value = true
  try {
    const filters = q ? [['name', 'like', `%${q}%`]] : []
    // Merge extraFilters (vd: scope theo item) — AND với search
    for (const f of (props.extraFilters || [])) {
      if (Array.isArray(f) && f.length >= 3) filters.push(f)
    }
    const fields = props.linkTo === 'SC Item' ? ['name', 'item_name']
                  : props.linkTo === 'SC Supplier' ? ['name', 'supplier_name']
                  : props.linkTo === 'SC Patient' ? ['name', 'patient_name']
                  : props.linkTo === 'User' ? ['name', 'full_name']
                  : props.linkTo === 'SC Batch' ? ['name', 'item', 'expiry_date']
                  : props.linkTo === 'Framework Contract' ? ['name', 'contract_number', 'supplier_name']
                  : ['name']
    const order = props.linkTo === 'SC Batch' ? 'expiry_date asc' : 'modified desc'
    const rows = await getList(props.linkTo, {
      fields, filters, order_by: order, limit: 20,
    })
    results.value = rows
  } catch (e) {
    results.value = []
  } finally {
    loading.value = false
  }
}

let _t = null
function onInput(e) {
  const v = e.target.value
  search.value = v
  emit('update:modelValue', v)
  clearTimeout(_t)
  _t = setTimeout(() => doSearch(v), 200)
  open.value = true
  positionDropdown()
}

function onFocus() {
  open.value = true
  positionDropdown()
  if (!results.value.length) doSearch('')
}

function onBlur() {
  // delayed so click can register first
  setTimeout(() => { open.value = false }, 150)
}

function pick(row) {
  emit('update:modelValue', row.name)
  emit('selected', row)
  search.value = row.name
  open.value = false
}

const subLabel = (r) => {
  // Framework Contract: số HĐ + NCC — để nhận biết HĐ khung nào
  if (props.linkTo === 'Framework Contract') {
    const parts = []
    if (r.contract_number) parts.push(`Số HĐ: ${r.contract_number}`)
    if (r.supplier_name) parts.push(r.supplier_name)
    return parts.join(' · ')
  }
  if (r.item_name || r.supplier_name || r.patient_name || r.full_name) {
    return r.item_name || r.supplier_name || r.patient_name || r.full_name
  }
  // SC Batch: hiện item + HSD
  if (r.item || r.expiry_date) {
    const parts = []
    if (r.item) parts.push(r.item)
    if (r.expiry_date) parts.push(`HSD: ${r.expiry_date}`)
    return parts.join(' · ')
  }
  return ''
}
</script>

<template>
  <div class="relative">
    <input ref="inputEl" :value="search" :placeholder="placeholder || `— Chọn ${linkTo} —`"
      :readonly="readonly" :required="required"
      @input="onInput" @focus="onFocus" @blur="onBlur"
      class="sc-input pr-8"
      :class="size === 'sm' ? 'py-1.5 text-sm' : ''" />
    <span class="absolute right-2 top-1/2 -translate-y-1/2 text-sc-text-muted text-xs pointer-events-none">▾</span>

    <Teleport to="body">
      <div v-if="open && !readonly" :style="dropdownStyle"
        class="bg-white border border-sc-border rounded-md shadow-lg max-h-72 overflow-y-auto">
        <button v-if="allowCreate" type="button"
          @mousedown.prevent="emit('createNew', { search }); open = false"
          class="w-full text-left px-3 py-2 text-sm font-semibold text-sc-royal hover:bg-sc-bg border-b border-sc-border bg-blue-50">
          + Tạo mới {{ linkTo.replace(/^SC /, '') }}{{ search ? ` "${search}"` : '' }}
        </button>
        <div v-if="loading" class="px-3 py-2 text-sm text-sc-text-muted">Đang tìm...</div>
        <template v-else-if="results.length === 0">
          <div class="px-3 py-2 text-sm text-sc-text-muted">
            Không có kết quả{{ search ? ` cho "${search}"` : '' }}
          </div>
          <!-- UX-004: gợi ý "Tạo mới" inline khi không tìm thấy + user đã gõ search -->
          <button v-if="search && !allowCreate" type="button"
            @mousedown.prevent="emit('createNew', { search }); open = false"
            class="w-full text-left px-3 py-2 text-sm font-medium text-sc-royal hover:bg-sc-bg border-t border-sc-border bg-blue-50">
            + Tạo mới {{ linkTo.replace(/^SC /, '') }} "{{ search }}"
          </button>
        </template>
        <button v-else v-for="r in results" :key="r.name" type="button"
          @mousedown.prevent="pick(r)"
          class="w-full text-left px-3 py-2 text-sm hover:bg-sc-bg border-b border-sc-border last:border-0">
          <div class="font-mono">{{ r.name }}</div>
          <div v-if="subLabel(r)" class="text-xs text-sc-text-muted truncate">{{ subLabel(r) }}</div>
        </button>
      </div>
    </Teleport>
  </div>
</template>
