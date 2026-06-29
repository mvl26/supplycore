<template>
  <div class="m-list" aria-hidden="true">
    <div v-for="i in count" :key="i" class="m-sk m-sk-card" />
  </div>
</template>

<script setup>
defineProps({ count: { type: Number, default: 4 } })
</script>
