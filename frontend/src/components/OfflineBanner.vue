<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const online = ref(navigator.onLine)
const set = () => { online.value = navigator.onLine }

onMounted(() => {
  window.addEventListener('online', set)
  window.addEventListener('offline', set)
})
onUnmounted(() => {
  window.removeEventListener('online', set)
  window.removeEventListener('offline', set)
})
</script>

<template>
  <div v-if="!online"
    class="fixed top-0 inset-x-0 z-[100] bg-amber-500 text-white text-[13px] font-medium text-center py-1.5 px-3 shadow">
    Mất kết nối mạng — dữ liệu cần kết nối để cập nhật
  </div>
</template>
