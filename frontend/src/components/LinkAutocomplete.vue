<script setup>
import { ref, watch, nextTick, onBeforeUnmount, onMounted } from 'vue'
import { getList, call } from '../api'

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

// L03/T05: ưu tiên hiển thị TÊN (mã làm phụ). Map field tên theo doctype.
const NAME_FIELD = {
  'SC Item': 'item_name', 'SC Supplier': 'supplier_name',
  'User': 'full_name', 'SC Warehouse': 'warehouse_name', 'SC Department': 'department_name',
  'SC Item Group': 'group_name', 'SC UOM': 'uom_name',
  'Framework Contract': 'contract_number',
  // M7 Sales: hiện TÊN khách hàng thay vì mã doc.
  'SC Customer': 'customer_name',
}
const nameFieldOf = (dt) => NAME_FIELD[dt] || null

// Nhãn tiếng Việt cho nút "+ Tạo mới …" (thay vì tên doctype tiếng Anh).
const DT_LABEL = {
  'SC Customer': 'Khách hàng', 'SC Supplier': 'Nhà cung cấp',
  'SC Item': 'Vật tư', 'SC Warehouse': 'Kho', 'SC Department': 'Khoa/Phòng',
  'SC Sales Framework Contract': 'HĐ khung bán', 'Framework Contract': 'HĐ khung',
}
const dtLabel = (dt) => DT_LABEL[dt] || (dt || '').replace(/^SC /, '')

// M7 UX: doctype bán hàng KHÔNG có field tên đơn lẻ (HĐ khung bán, và các
// chứng từ SO/DN/SI vốn chỉ định danh bằng mã) → hiển thị TÊN KHÁCH làm chính,
// phụ đề là số phiếu + ngày (+ tiền/trạng thái). Dùng endpoint search chuyên
// biệt (join lấy customer_name), mirror cách Framework Contract (mua) đã làm.
const _money = (v) => (v == null || v === '') ? '' : `${Number(v).toLocaleString('vi-VN')} đ`
const _dot = (...p) => p.filter(Boolean).join(' · ')
const _cust = (r) => r.customer_name || r.customer || r.name
const COMPOSED = {
  'SC Sales Framework Contract': {
    endpoint: 'supplycore.api.frontend.search_sales_framework_contract', args: {},
    primary: _cust,
    sub: (r) => _dot((r.valid_from || r.valid_to) ? `HL: ${r.valid_from || '?'} → ${r.valid_to || '?'}` : '', r.status),
    inputLabel: (r) => r.valid_to ? `${_cust(r)} — HĐ đến ${r.valid_to}` : _cust(r),
  },
  'SC Sales Order': {
    endpoint: 'supplycore.api.frontend.search_sales_doc', args: { doctype: 'SC Sales Order' },
    primary: _cust, sub: (r) => _dot(r.name, r.ref_date, r.status),
    inputLabel: (r) => `${_cust(r)} — ${r.name}`,
  },
  'SC Delivery Note': {
    endpoint: 'supplycore.api.frontend.search_sales_doc', args: { doctype: 'SC Delivery Note' },
    primary: _cust, sub: (r) => _dot(r.name, r.ref_date, r.status),
    inputLabel: (r) => `${_cust(r)} — ${r.name}`,
  },
  'SC Sales Invoice': {
    endpoint: 'supplycore.api.frontend.search_sales_doc', args: { doctype: 'SC Sales Invoice' },
    primary: _cust, sub: (r) => _dot(r.name, r.ref_date, _money(r.amount), r.status),
    inputLabel: (r) => `${_cust(r)} — ${r.name}`,
  },
}
const composed = () => COMPOSED[props.linkTo]

// Nhãn hiển thị "Tên (mã)" — nếu không có tên thì chỉ mã.
function fmtLabel(row) {
  if (!row) return ''
  const c = composed()
  if (c) return c.inputLabel(row)
  const nf = nameFieldOf(props.linkTo)
  const nm = nf ? row[nf] : null
  return (nm && nm !== row.name) ? `${nm} (${row.name})` : row.name
}

// Re-fetch khi extraFilters đổi (vd: row.item thay đổi → filter dropdown đổi theo)
watch(() => JSON.stringify(props.extraFilters), () => {
  results.value = []
  if (open.value) doSearch(search.value)
})

const open = ref(false)
const search = ref('')            // nội dung ô input (hiển thị nhãn hoặc text đang gõ)
const displayLabel = ref('')      // nhãn "Tên (mã)" ứng với modelValue hiện tại
const typing = ref(false)         // user đang gõ để tìm (không phải hiển thị nhãn)
const results = ref([])
const loading = ref(false)
const inputEl = ref(null)
const dropdownStyle = ref({})

// Resolve nhãn cho 1 mã (khi load doc hoặc modelValue đổi từ ngoài).
async function resolveLabel(code) {
  if (!code) { displayLabel.value = ''; if (!typing.value) search.value = ''; return }
  // Doctype nhãn ghép (SFC/SO/DN/SI): gọi chính endpoint search rồi khớp đúng
  // mã để dựng nhãn tường minh (tên khách + số phiếu). Chỉ chạy khi load doc.
  const c = composed()
  if (c) {
    try {
      const rows = await call(c.endpoint, { ...c.args, q: code, limit: 20 })
      const row = (rows || []).find((r) => r.name === code)
      displayLabel.value = row ? c.inputLabel(row) : code
    } catch (e) { displayLabel.value = code }
    if (!typing.value) search.value = displayLabel.value
    return
  }
  const nf = nameFieldOf(props.linkTo)
  if (!nf) { displayLabel.value = code; if (!typing.value) search.value = code; return }
  try {
    const rows = await getList(props.linkTo, {
      fields: ['name', nf], filters: [['name', '=', code]], limit: 1,
    })
    displayLabel.value = rows && rows.length ? fmtLabel(rows[0]) : code
  } catch (e) {
    displayLabel.value = code
  }
  if (!typing.value) search.value = displayLabel.value
}

watch(() => props.modelValue, (v) => {
  if (typing.value) return
  if (!v) { displayLabel.value = ''; search.value = ''; return }
  // Nếu nhãn hiện tại đã ứng với mã này (kết thúc bằng "(mã)") thì khỏi fetch lại
  if (displayLabel.value && (displayLabel.value === v || displayLabel.value.endsWith(`(${v})`))) {
    search.value = displayLabel.value
    return
  }
  resolveLabel(v)
})
onMounted(() => { if (props.modelValue) resolveLabel(props.modelValue) })

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

let _seq = 0
async function doSearch(q) {
  const my = ++_seq   // chống race: chỉ áp dụng kết quả của lần tìm MỚI nhất
  loading.value = true
  try {
    // L11: HĐ khung tìm theo mã/số HĐ, mã/tên NCC, mã/tên vật tư (child) — endpoint riêng
    if (props.linkTo === 'Framework Contract') {
      const rows = await call('supplycore.api.frontend.search_framework_contract', { q: q || '', limit: 20 })
      if (my !== _seq) return
      results.value = rows || []
      return
    }
    // M7: doctype nhãn ghép (HĐ khung bán, SO/DN/SI) — endpoint search chuyên biệt
    // (join customer_name, tìm theo tên/mã khách + mã phiếu).
    const c = composed()
    if (c) {
      const rows = await call(c.endpoint, { ...c.args, q: q || '', limit: 20 })
      if (my !== _seq) return
      results.value = rows || []
      return
    }
    const nf = nameFieldOf(props.linkTo)
    // L11/T05: tìm theo mã (name) HOẶC theo tên hiển thị (item_name/supplier_name…)
    const or_filters = q
      ? (nf ? [['name', 'like', `%${q}%`], [nf, 'like', `%${q}%`]] : [['name', 'like', `%${q}%`]])
      : []
    const fields = props.linkTo === 'SC Item' ? ['name', 'item_name']
                  : props.linkTo === 'SC Supplier' ? ['name', 'supplier_name']
                  : props.linkTo === 'User' ? ['name', 'full_name']
                  : props.linkTo === 'SC Batch' ? ['name', 'item', 'expiry_date']
                  : props.linkTo === 'Framework Contract' ? ['name', 'contract_number', 'supplier_name']
                  : props.linkTo === 'SC Warehouse' ? ['name', 'warehouse_name']
                  : props.linkTo === 'SC Department' ? ['name', 'department_name']
                  : ['name']
    const order = props.linkTo === 'SC Batch' ? 'expiry_date asc' : 'modified desc'
    const args = { fields, order_by: order, limit: 20 }
    // extraFilters luôn AND; search dùng or_filters
    const extra = (props.extraFilters || []).filter(f => Array.isArray(f) && f.length >= 3)
    if (extra.length) args.filters = extra
    if (or_filters.length) args.or_filters = or_filters
    const rows = await getList(props.linkTo, args)
    if (my !== _seq) return        // đã có lần tìm mới hơn → bỏ kết quả cũ
    results.value = rows
  } catch (e) {
    if (my === _seq) results.value = []
  } finally {
    if (my === _seq) loading.value = false
  }
}

let _t = null
function onInput(e) {
  const v = e.target.value
  typing.value = true
  search.value = v
  clearTimeout(_t)
  _t = setTimeout(() => doSearch(v), 200)
  open.value = true
  positionDropdown()
}

function onFocus() {
  open.value = true
  positionDropdown()
  // chọn hết để gõ là thay nhãn — vẫn giữ nhãn nếu không gõ
  nextTick(() => { try { inputEl.value && inputEl.value.select() } catch (e) {} })
  if (!results.value.length) doSearch('')
}

function onBlur() {
  // delayed so click can register first
  setTimeout(() => {
    open.value = false
    typing.value = false
    // khôi phục nhãn nếu user gõ dở mà không chọn
    search.value = displayLabel.value || (props.modelValue || '')
  }, 150)
}

function pick(row) {
  typing.value = false
  displayLabel.value = fmtLabel(row)
  search.value = displayLabel.value
  emit('update:modelValue', row.name)
  emit('selected', row)
  open.value = false
}

const subLabel = (r) => {
  const c = composed()
  if (c) return c.sub(r)
  // Framework Contract: số HĐ làm chính → phụ hiện NCC
  if (props.linkTo === 'Framework Contract') {
    return r.supplier_name || ''
  }
  // SC Batch: hiện item + HSD
  if (props.linkTo === 'SC Batch' && (r.item || r.expiry_date)) {
    const parts = []
    if (r.item) parts.push(r.item)
    if (r.expiry_date) parts.push(`HSD: ${r.expiry_date}`)
    return parts.join(' · ')
  }
  return ''
}
// Tên hiển thị chính trong dropdown (ưu tiên tên)
const primaryText = (r) => {
  const c = composed()
  if (c) return c.primary(r)
  const nf = nameFieldOf(props.linkTo)
  const nm = nf ? r[nf] : null
  return nm || r.name
}
const hasName = (r) => {
  // Doctype nhãn ghép: mã phiếu đã nằm trong phụ đề (sub) → không hiện dòng mã riêng.
  if (composed()) return false
  const nf = nameFieldOf(props.linkTo)
  return !!(nf && r[nf] && r[nf] !== r.name)
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
          + Tạo mới {{ dtLabel(linkTo) }}{{ typing && search ? ` "${search}"` : '' }}
        </button>
        <div v-if="loading" class="px-3 py-2 text-sm text-sc-text-muted">Đang tìm...</div>
        <template v-else-if="results.length === 0">
          <div class="px-3 py-2 text-sm text-sc-text-muted">
            Không có kết quả{{ typing && search ? ` cho "${search}"` : '' }}
          </div>
          <!-- UX-004: gợi ý "Tạo mới" inline khi không tìm thấy + user đã gõ search -->
          <button v-if="typing && search && !allowCreate" type="button"
            @mousedown.prevent="emit('createNew', { search }); open = false"
            class="w-full text-left px-3 py-2 text-sm font-medium text-sc-royal hover:bg-sc-bg border-t border-sc-border bg-blue-50">
            + Tạo mới {{ dtLabel(linkTo) }} "{{ search }}"
          </button>
        </template>
        <button v-else v-for="r in results" :key="r.name" type="button"
          @mousedown.prevent="pick(r)"
          class="w-full text-left px-3 py-2 text-sm hover:bg-sc-bg border-b border-sc-border last:border-0">
          <div class="font-medium text-sc-text">{{ primaryText(r) }}</div>
          <div v-if="hasName(r)" class="text-xs text-sc-text-muted font-mono">{{ r.name }}</div>
          <div v-if="subLabel(r)" class="text-xs text-sc-text-muted truncate">{{ subLabel(r) }}</div>
        </button>
      </div>
    </Teleport>
  </div>
</template>
