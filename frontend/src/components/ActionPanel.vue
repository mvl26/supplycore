<script setup>
import { ref, computed } from 'vue'
import { ACTIONS } from '../actions'
import { runDocMethod } from '../api'
import { useToastStore } from '../stores/toast'
import Modal from './Modal.vue'
import FieldInput from './FieldInput.vue'

const props = defineProps({
  doctype: String,
  doc: Object,
})
const emit = defineEmits(['after'])

const toast = useToastStore()
const running = ref(false)
const selected = ref(null)
const args = ref({})
const result = ref(null)

const visible = computed(() => {
  const list = ACTIONS[props.doctype] || []
  return list.filter(a => !a.when || a.when(props.doc || {}))
})

function openAction(a) {
  if (a.args && a.args.length) {
    selected.value = a
    args.value = {}
    a.args.forEach(f => { args.value[f.key] = f.default ?? '' })
  } else {
    runAction(a, {})
  }
}

async function runAction(a, argsObj) {
  running.value = true
  result.value = null
  try {
    const r = await runDocMethod(props.doctype, props.doc.name, a.method, argsObj)
    // Frappe wraps result: { message: { ... } }
    const msg = r?.message ?? r
    result.value = typeof msg === 'object' ? msg : { result: msg }
    toast.success(`Đã thực hiện: ${a.label}`)
    selected.value = null
    emit('after', a, result.value)
  } catch (e) {
    toast.error(e.message)
  } finally {
    running.value = false
  }
}

function confirmModal() {
  if (!selected.value) return
  // Validate required
  for (const f of selected.value.args || []) {
    if (f.required && (args.value[f.key] === '' || args.value[f.key] == null)) {
      toast.warning(`Vui lòng nhập ${f.label}`)
      return
    }
  }
  runAction(selected.value, args.value)
}

const btnClass = {
  primary:   'sc-btn-primary',
  secondary: 'sc-btn-secondary',
  success:   'bg-sc-success hover:bg-green-700 text-white px-4 py-2 rounded-md font-medium',
  warning:   'bg-sc-warning hover:bg-amber-600 text-white px-4 py-2 rounded-md font-medium',
  danger:    'bg-sc-danger hover:bg-red-700 text-white px-4 py-2 rounded-md font-medium',
}
</script>

<template>
  <div v-if="visible.length" class="sc-card p-5 mb-4">
    <h3 class="font-semibold text-sc-navy mb-3 flex items-center gap-2">
      ⚡ Hành động khả dụng
    </h3>
    <div class="flex flex-wrap gap-2">
      <button v-for="a in visible" :key="a.method"
        @click="openAction(a)" :disabled="running"
        :class="[btnClass[a.variant] || 'sc-btn-secondary', 'text-sm disabled:opacity-50']">
        <span class="mr-1">{{ a.icon }}</span> {{ a.label }}
      </button>
    </div>
  </div>

  <Modal :open="!!selected" :title="selected ? selected.label : ''" size="md"
    @close="selected = null">
    <div class="space-y-3">
      <FieldInput v-for="f in selected?.args || []" :key="f.key"
        v-model="args[f.key]"
        :label="f.label" :type="f.type || 'text'"
        :options="f.options" :required="f.required" />
    </div>
    <template #footer>
      <button @click="selected = null" class="sc-btn-secondary text-sm">Hủy</button>
      <button @click="confirmModal" :disabled="running"
        :class="[btnClass[selected?.variant] || 'sc-btn-primary', 'text-sm']">
        {{ running ? 'Đang chạy...' : 'Xác nhận' }}
      </button>
    </template>
  </Modal>
</template>
