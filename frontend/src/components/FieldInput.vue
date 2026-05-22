<script setup>
import { computed } from 'vue'
import { statusLabel } from '../modules'
import Icon from './Icon.vue'

const props = defineProps({
  modelValue: [String, Number, Boolean, Date],
  label:    String,
  type:     { type: String, default: 'text' },  // text/number/date/select/textarea/check/link
  options:  Array,   // for select
  required: Boolean,
  readonly: Boolean,
  placeholder: String,
  hint:     String,
  error:    String,
  prefix:     String,
  prefixIcon: String,   // icon name → renders an <Icon> in the prefix slot
  suffix:     String,
})

const hasPrefix = computed(() => !!props.prefix || !!props.prefixIcon)
const emit = defineEmits(['update:modelValue'])

const inputId = computed(() => `f-${Math.random().toString(36).slice(2, 8)}`)

function update(v) {
  if (props.type === 'number') emit('update:modelValue', v === '' ? null : Number(v))
  else if (props.type === 'check') emit('update:modelValue', v ? 1 : 0)
  else emit('update:modelValue', v)
}
</script>

<template>
  <div>
    <label v-if="label && type !== 'check'" :for="inputId"
      class="text-xs font-medium text-sc-text-muted block mb-1">
      {{ label }}
      <span v-if="required" class="text-sc-danger">*</span>
    </label>
    <div class="relative">
      <span v-if="hasPrefix"
        class="absolute left-3 top-1/2 -translate-y-1/2 text-sc-text-muted text-sm
               flex items-center pointer-events-none">
        <Icon v-if="prefixIcon" :name="prefixIcon" :size="16" />
        <template v-else>{{ prefix }}</template>
      </span>
      <textarea v-if="type === 'textarea'"
        :id="inputId" :value="modelValue || ''" :readonly="readonly"
        :placeholder="placeholder" rows="3"
        @input="e => update(e.target.value)" class="sc-input"
        :class="{ 'pl-9': hasPrefix, 'pr-8': suffix }" />
      <select v-else-if="type === 'select'"
        :id="inputId" :value="modelValue || ''" :disabled="readonly"
        @change="e => update(e.target.value)" class="sc-input"
        :class="{ 'pl-9': hasPrefix }">
        <option value="">{{ placeholder || '— Chọn —' }}</option>
        <option v-for="o in options" :key="o.value ?? o" :value="o.value ?? o">{{ o.label ?? statusLabel(o) }}</option>
      </select>
      <label v-else-if="type === 'check'" class="flex items-center gap-2 cursor-pointer py-1.5">
        <input type="checkbox" :checked="!!modelValue" :disabled="readonly"
          @change="e => update(e.target.checked)"
          class="w-4 h-4 text-sc-royal rounded" />
        <span class="text-sm">{{ label }}</span>
      </label>
      <input v-else
        :id="inputId" :type="type" :value="modelValue ?? ''" :readonly="readonly"
        :placeholder="placeholder"
        @input="e => update(e.target.value)" class="sc-input"
        :class="{ 'pl-9': hasPrefix, 'pr-8': suffix }" />
      <span v-if="suffix" class="absolute right-3 top-1/2 -translate-y-1/2 text-sc-text-muted text-sm">{{ suffix }}</span>
    </div>
    <div v-if="error" class="text-xs text-sc-danger mt-1">{{ error }}</div>
    <div v-else-if="hint" class="text-xs text-sc-text-muted mt-1">{{ hint }}</div>
  </div>
</template>
