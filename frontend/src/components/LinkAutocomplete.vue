<script setup>
import { ref, watch, onMounted } from 'vue'
import { getList } from '../api'

const props = defineProps({
  modelValue: String,
  linkTo:     { type: String, required: true },
  placeholder: String,
  required:   Boolean,
  readonly:   Boolean,
  size:       { type: String, default: 'normal' }, // normal/sm
  allowCreate: Boolean,                            // hiển thị "+ Tạo mới"
})
const emit = defineEmits(['update:modelValue', 'selected', 'createNew'])

const open = ref(false)
const search = ref('')
const results = ref([])
const loading = ref(false)
const inputEl = ref(null)
const _cache = ref({})  // cache results by query

watch(() => props.modelValue, (v) => {
  if (v !== search.value) search.value = v || ''
})

async function doSearch(q) {
  loading.value = true
  try {
    const filters = q ? [['name', 'like', `%${q}%`]] : []
    const fields = props.linkTo === 'SC Item' ? ['name', 'item_name']
                  : props.linkTo === 'SC Supplier' ? ['name', 'supplier_name']
                  : props.linkTo === 'SC Patient' ? ['name', 'patient_name']
                  : props.linkTo === 'User' ? ['name', 'full_name']
                  : ['name']
    const rows = await getList(props.linkTo, {
      fields, filters, order_by: 'modified desc', limit: 20,
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
}

function onFocus() {
  open.value = true
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

const subLabel = (r) => r.item_name || r.supplier_name || r.patient_name || r.full_name || ''
</script>

<template>
  <div class="relative">
    <input ref="inputEl" :value="search" :placeholder="placeholder || `— Chọn ${linkTo} —`"
      :readonly="readonly" :required="required"
      @input="onInput" @focus="onFocus" @blur="onBlur"
      class="sc-input pr-8"
      :class="size === 'sm' ? 'py-1.5 text-sm' : ''" />
    <span class="absolute right-2 top-1/2 -translate-y-1/2 text-sc-text-muted text-xs pointer-events-none">▾</span>

    <div v-if="open && !readonly"
      class="absolute z-30 mt-1 w-full bg-white border border-sc-border rounded-md shadow-lg max-h-64 overflow-y-auto">
      <button v-if="allowCreate" type="button"
        @mousedown.prevent="emit('createNew'); open = false"
        class="w-full text-left px-3 py-2 text-sm font-semibold text-sc-royal hover:bg-sc-bg border-b border-sc-border bg-blue-50">
        + Tạo mới {{ linkTo.replace(/^SC /, '') }}
      </button>
      <div v-if="loading" class="px-3 py-2 text-sm text-sc-text-muted">Đang tìm...</div>
      <div v-else-if="results.length === 0" class="px-3 py-2 text-sm text-sc-text-muted">
        Không có kết quả{{ search ? ` cho "${search}"` : '' }}
      </div>
      <button v-else v-for="r in results" :key="r.name" type="button"
        @mousedown.prevent="pick(r)"
        class="w-full text-left px-3 py-2 text-sm hover:bg-sc-bg border-b border-sc-border last:border-0">
        <div class="font-mono">{{ r.name }}</div>
        <div v-if="subLabel(r)" class="text-xs text-sc-text-muted truncate">{{ subLabel(r) }}</div>
      </button>
    </div>
  </div>
</template>
