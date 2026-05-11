<script setup>
import { onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import AppShell from './components/AppShell.vue'
import ToastContainer from './components/ToastContainer.vue'
import { useAuthStore } from './stores/auth'

const route = useRoute()
const auth = useAuthStore()
const isBlank = computed(() => route.meta?.layout === 'blank')

onMounted(async () => {
  await auth.boot()
})
</script>

<template>
  <div class="sc-app">
    <template v-if="isBlank">
      <router-view />
    </template>
    <template v-else>
      <AppShell>
        <router-view v-slot="{ Component }">
          <component :is="Component" />
        </router-view>
      </AppShell>
    </template>
    <ToastContainer />
  </div>
</template>
