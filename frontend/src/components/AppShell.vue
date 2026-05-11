<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { MODULES } from '../modules'

const props = defineProps({ user: String })
const route = useRoute()

const groups = computed(() => {
  const g = {}
  MODULES.forEach(m => {
    g[m.group] = g[m.group] || []
    g[m.group].push(m)
  })
  return g
})

const isActive = (path) => route.path.startsWith(path)
</script>

<template>
  <div class="min-h-screen flex bg-sc-bg">
    <!-- Sidebar -->
    <aside class="w-64 bg-sc-navy text-white flex-shrink-0 flex flex-col">
      <div class="px-6 py-5 border-b border-white/10">
        <div class="text-xl font-bold tracking-tight">SupplyCore</div>
        <div class="text-xs text-white/60 mt-0.5">Hospital Supply Chain</div>
      </div>

      <nav class="flex-1 overflow-y-auto py-4">
        <router-link to="/dashboard"
          class="flex items-center gap-3 px-6 py-2.5 hover:bg-white/10 transition"
          :class="{ 'bg-sc-royal/30 border-l-4 border-sc-royal-light': isActive('/dashboard') || route.path === '/' }">
          <span class="text-lg">🏠</span>
          <span class="text-sm font-medium">Dashboard</span>
        </router-link>

        <router-link to="/alerts"
          class="flex items-center gap-3 px-6 py-2.5 hover:bg-white/10 transition"
          :class="{ 'bg-sc-royal/30 border-l-4 border-sc-royal-light': isActive('/alerts') }">
          <span class="text-lg">🔔</span>
          <span class="text-sm font-medium">Alert Center</span>
        </router-link>

        <div v-for="(modules, group) in groups" :key="group" class="mt-5">
          <div class="px-6 mb-1 text-xs font-semibold text-white/40 uppercase tracking-wider">
            {{ group }}
          </div>
          <router-link v-for="m in modules" :key="m.id" :to="m.route"
            class="flex items-center gap-3 px-6 py-2 hover:bg-white/10 transition"
            :class="{ 'bg-sc-royal/30 border-l-4 border-sc-royal-light': isActive(m.route) }">
            <span class="text-base">{{ m.icon }}</span>
            <span class="text-sm">
              <span class="font-mono text-xs text-white/50 mr-1">{{ m.code }}</span>
              {{ m.name }}
            </span>
          </router-link>
        </div>
      </nav>

      <div class="px-6 py-3 border-t border-white/10 text-xs text-white/50">
        v0.1.0 · {{ user }}
      </div>
    </aside>

    <!-- Main -->
    <div class="flex-1 flex flex-col min-w-0">
      <!-- Top bar -->
      <header class="bg-white border-b border-sc-border h-14 flex items-center px-6 justify-between">
        <div class="flex items-center gap-3">
          <h1 class="text-lg font-semibold text-sc-navy">
            {{ route.meta?.title || 'SupplyCore' }}
          </h1>
        </div>
        <div class="flex items-center gap-3">
          <a href="/app" class="sc-btn-ghost text-sm">Frappe Desk →</a>
          <div class="w-9 h-9 rounded-full bg-sc-royal text-white flex items-center justify-center font-semibold text-sm">
            {{ (user || 'G').slice(0, 1).toUpperCase() }}
          </div>
        </div>
      </header>

      <!-- Content -->
      <main class="flex-1 overflow-y-auto p-6">
        <slot />
      </main>
    </div>
  </div>
</template>
