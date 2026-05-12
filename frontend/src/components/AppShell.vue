<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { MODULES } from '../modules'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const groups = computed(() => {
  const g = {}
  MODULES.forEach(m => { (g[m.group] = g[m.group] || []).push(m) })
  return g
})

const userMenuOpen = ref(false)
const sidebarOpen = ref(false)

function isActive(path) {
  if (path === '/dashboard') return route.path === '/' || route.path === '/dashboard'
  return route.path.startsWith(path)
}

async function logout() {
  await auth.doLogout()
  router.replace('/login')
}
</script>

<template>
  <div class="min-h-screen flex bg-sc-bg">
    <!-- Sidebar -->
    <aside class="w-64 bg-sc-navy text-white flex-shrink-0 flex flex-col"
      :class="{ 'hidden md:flex': !sidebarOpen, 'fixed inset-0 z-40 flex': sidebarOpen }">
      <div class="px-5 py-4 border-b border-white/10 flex items-center gap-2">
        <div class="w-10 h-10 rounded-lg bg-white/10 flex items-center justify-center text-xl">🏥</div>
        <div>
          <div class="text-base font-bold tracking-tight leading-tight">SupplyCore</div>
          <div class="text-xs text-white/60 leading-tight">Hospital Supply Chain</div>
        </div>
      </div>

      <nav class="flex-1 overflow-y-auto py-3">
        <router-link to="/dashboard"
          class="flex items-center gap-3 px-5 py-2 hover:bg-white/10 transition"
          :class="{ 'bg-sc-royal/30 border-l-4 border-sc-royal-light pl-4': isActive('/dashboard') }">
          <span class="text-base">🏠</span>
          <span class="text-sm font-medium">Dashboard</span>
        </router-link>

        <router-link to="/alerts"
          class="flex items-center gap-3 px-5 py-2 hover:bg-white/10 transition"
          :class="{ 'bg-sc-royal/30 border-l-4 border-sc-royal-light pl-4': isActive('/alerts') }">
          <span class="text-base">🔔</span>
          <span class="text-sm font-medium">Alert Center</span>
        </router-link>

        <router-link to="/stock-balance"
          class="flex items-center gap-3 px-5 py-2 hover:bg-white/10 transition"
          :class="{ 'bg-sc-royal/30 border-l-4 border-sc-royal-light pl-4': isActive('/stock-balance') }">
          <span class="text-base">📊</span>
          <span class="text-sm font-medium">Tồn kho</span>
        </router-link>

        <router-link to="/putaway"
          class="flex items-center gap-3 px-5 py-2 hover:bg-white/10 transition"
          :class="{ 'bg-sc-royal/30 border-l-4 border-sc-royal-light pl-4': isActive('/putaway') }">
          <span class="text-base">📦</span>
          <span class="text-sm font-medium">Xếp hàng lên kệ</span>
        </router-link>

        <div v-for="(modules, group) in groups" :key="group" class="mt-4">
          <div class="px-5 mb-1 text-xs font-semibold text-white/40 uppercase tracking-wider">
            {{ group }}
          </div>
          <router-link v-for="m in modules" :key="m.id" :to="m.route"
            class="flex items-center gap-3 px-5 py-2 hover:bg-white/10 transition"
            :class="{ 'bg-sc-royal/30 border-l-4 border-sc-royal-light pl-4': isActive(m.route) }">
            <span class="text-base">{{ m.icon }}</span>
            <span class="text-sm flex-1">
              <span class="font-mono text-xs text-white/50 mr-1">{{ m.code }}</span>
              {{ m.name }}
            </span>
          </router-link>
        </div>
      </nav>

      <div class="px-5 py-3 border-t border-white/10 text-xs text-white/50">
        v0.1.0 · {{ auth.primaryRole }}
      </div>
    </aside>

    <!-- Main -->
    <div class="flex-1 flex flex-col min-w-0">
      <header class="bg-white border-b border-sc-border h-14 flex items-center px-5 justify-between">
        <button @click="sidebarOpen = !sidebarOpen" class="md:hidden text-sc-navy text-xl">☰</button>
        <div class="flex-1"></div>

        <!-- User menu -->
        <div class="relative" v-click-outside="() => userMenuOpen = false">
          <button @click.stop="userMenuOpen = !userMenuOpen"
            class="flex items-center gap-2 hover:bg-sc-bg rounded-md px-2 py-1 transition">
            <div class="w-8 h-8 rounded-full bg-sc-royal text-white flex items-center justify-center font-semibold text-sm">
              {{ (auth.user.full_name || auth.user.name || 'G').slice(0, 1).toUpperCase() }}
            </div>
            <div class="text-left hidden sm:block">
              <div class="text-sm font-medium text-sc-text">{{ auth.user.full_name || auth.user.name }}</div>
              <div class="text-xs text-sc-text-muted">{{ auth.primaryRole }}</div>
            </div>
            <span class="text-sc-text-muted text-xs">▾</span>
          </button>
          <Transition name="fade">
            <div v-if="userMenuOpen"
              class="absolute right-0 top-full mt-1 w-56 bg-white rounded-lg shadow-sc-lg border border-sc-border py-1 z-40">
              <div class="px-3 py-2 border-b border-sc-border">
                <div class="text-sm font-medium">{{ auth.user.full_name || auth.user.name }}</div>
                <div class="text-xs text-sc-text-muted">{{ auth.user.email || auth.user.name }}</div>
              </div>
              <button @click="userMenuOpen = false; logout()"
                class="block w-full text-left px-3 py-2 text-sm hover:bg-sc-bg text-sc-danger">
                Đăng xuất
              </button>
            </div>
          </Transition>
        </div>
      </header>

      <main class="flex-1 overflow-y-auto p-5 md:p-6">
        <slot />
      </main>
    </div>
  </div>
</template>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity .12s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
