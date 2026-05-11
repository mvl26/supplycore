<script setup>
import LinkAutocomplete from './LinkAutocomplete.vue'

const props = defineProps({
  modelValue: [String, Number, Boolean, Date],
  field:      { type: Object, required: true },  // { name, label, type, required, options, linkTo, hint }
  size:       { type: String, default: 'normal' },
  showLabel:  { type: Boolean, default: true },
})
const emit = defineEmits(['update:modelValue', 'selected'])

function update(v) {
  if (props.field.type === 'Int' || props.field.type === 'Float' || props.field.type === 'Currency' || props.field.type === 'Percent') {
    emit('update:modelValue', v === '' || v == null ? null : Number(v))
  } else if (props.field.type === 'Check') {
    emit('update:modelValue', v ? 1 : 0)
  } else {
    emit('update:modelValue', v)
  }
}

const inputClass = props.size === 'sm' ? 'sc-input py-1.5 text-sm' : 'sc-input'
</script>

<template>
  <div :class="field.type === 'Check' ? '' : 'flex flex-col'">
    <label v-if="showLabel && field.type !== 'Check'"
      class="text-xs font-medium text-sc-text-muted mb-1">
      {{ field.label }}
      <span v-if="field.required" class="text-sc-danger">*</span>
    </label>

    <!-- Link → autocomplete -->
    <LinkAutocomplete v-if="field.type === 'Link'"
      :model-value="modelValue" :link-to="field.linkTo" :required="field.required"
      :size="size"
      @update:model-value="update" @selected="(r) => emit('selected', r)" />

    <!-- Select -->
    <select v-else-if="field.type === 'Select'"
      :value="modelValue ?? ''" :required="field.required"
      @change="e => update(e.target.value)" :class="inputClass">
      <option value="">— Chọn —</option>
      <option v-for="o in field.options" :key="o.value ?? o" :value="o.value ?? o">
        {{ o.label ?? o }}
      </option>
    </select>

    <!-- Text areas -->
    <textarea v-else-if="field.type === 'Small Text' || field.type === 'Long Text' || field.type === 'Text'"
      :value="modelValue ?? ''" :required="field.required"
      :rows="field.type === 'Long Text' ? 5 : 3"
      @input="e => update(e.target.value)" :class="inputClass" />

    <!-- Check -->
    <label v-else-if="field.type === 'Check'" class="flex items-center gap-2 cursor-pointer py-1.5">
      <input type="checkbox" :checked="!!modelValue"
        @change="e => update(e.target.checked)"
        class="w-4 h-4 text-sc-royal rounded" />
      <span class="text-sm">{{ field.label }}{{ field.required ? ' *' : '' }}</span>
    </label>

    <!-- Date -->
    <input v-else-if="field.type === 'Date'" type="date"
      :value="modelValue ?? ''" :required="field.required"
      @input="e => update(e.target.value)" :class="inputClass" />

    <!-- Datetime -->
    <input v-else-if="field.type === 'Datetime'" type="datetime-local"
      :value="modelValue ? new Date(modelValue).toISOString().slice(0, 16) : ''"
      :required="field.required"
      @input="e => update(e.target.value)" :class="inputClass" />

    <!-- Time -->
    <input v-else-if="field.type === 'Time'" type="time"
      :value="modelValue ?? ''" :required="field.required" step="1"
      @input="e => update(e.target.value)" :class="inputClass" />

    <!-- Number-like -->
    <input v-else-if="['Int','Float','Currency','Percent'].includes(field.type)" type="number"
      :step="field.type === 'Int' ? '1' : '0.01'"
      :value="modelValue ?? ''" :required="field.required"
      @input="e => update(e.target.value)" :class="inputClass" />

    <!-- Default: text/data -->
    <input v-else type="text"
      :value="modelValue ?? ''" :required="field.required"
      @input="e => update(e.target.value)" :class="inputClass" />

    <div v-if="field.hint" class="text-xs text-sc-text-muted mt-1">{{ field.hint }}</div>
  </div>
</template>
