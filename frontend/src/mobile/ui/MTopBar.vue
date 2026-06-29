<template>
  <header class="m-topbar">
    <div class="m-topbar__row">
      <div>
        <div class="m-topbar__title">{{ title }}</div>
        <div v-if="sub" class="m-topbar__sub">{{ sub }}</div>
      </div>
      <slot name="right" />
    </div>
    <slot />
  </header>
</template>

<script setup>
defineProps({ title: String, sub: String })
</script>
