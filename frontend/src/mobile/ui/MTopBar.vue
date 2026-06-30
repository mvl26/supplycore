<template>
  <header class="m-topbar">
    <div class="m-topbar__row">
      <div class="m-topbar__info">
        <h1 class="m-topbar__title">{{ title }}</h1>
        <div v-if="sub" class="m-topbar__sub">{{ sub }}</div>
      </div>
      <div v-if="$slots.right" class="m-topbar__right"><slot name="right" /></div>
    </div>
    <slot />
  </header>
</template>

<script setup>
defineProps({ title: String, sub: String })
</script>
