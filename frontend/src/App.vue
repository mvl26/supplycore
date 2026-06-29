<script setup>
import { onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import AppShell from './components/AppShell.vue'
import ToastContainer from './components/ToastContainer.vue'
import { useAuthStore } from './stores/auth'
import { isNative } from './platform'

const route = useRoute()
const auth = useAuthStore()
// Blank layout: Login page and other chrome-free pages.
const isBlank = computed(() => route.meta?.layout === 'blank')
// Mobile bypass: mobile routes provide their own chrome (MobileShell / setup screens).
// isNative() is a static boolean set at page load — safe to use in computed.
const isMobile = computed(() => !!(route.meta?.mobile || isNative()))

onMounted(async () => {
  // getSession() catches all network errors and returns 'Guest', so boot() never
  // throws on native pre-login. The mobile beforeEach guard then redirects the
  // unauthenticated native user to /m/setup.
  await auth.boot()
})
</script>

<template>
  <div class="sc-app">
    <template v-if="isBlank || isMobile">
      <router-view />
    </template>
    <template v-else>
      <AppShell>
        <router-view v-slot="{ Component, route }">
          <!-- Keyed wrapper: remounts per route → CSS enter animation replays.
               Avoids <Transition mode="out-in">, which deadlocks on multi-root pages. -->
          <div :key="route.path" class="sc-route-view">
            <component :is="Component" />
          </div>
        </router-view>
      </AppShell>
    </template>
    <ToastContainer />
  </div>
</template>
