<!-- frontend/src/mobile/MobileShell.vue -->
<template>
  <div class="m-shell m-app">
    <transition name="m-net-slide">
      <div v-if="!online" class="m-net">
        <Icon name="alert-triangle" :size="15" /> Mất kết nối mạng — đang chờ kết nối lại…
      </div>
    </transition>

    <main class="m-content">
      <router-view v-slot="{ Component }">
        <transition name="m-fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>

    <nav class="m-tabbar" :style="{ paddingBottom: 'var(--m-safe-b)' }">
      <router-link v-for="t in tabs" :key="t.to" :to="t.to" class="m-tab"
        active-class="m-tab--active" @click="tapLight">
        <span class="m-tab__dot" />
        <Icon :name="t.icon" :size="22" />
        <span class="m-tab__lbl">{{ t.label }}</span>
      </router-link>
    </nav>

    <!-- Overlay camera quét mã (hiện khi đang quét; teleport ra body) -->
    <ScanOverlay />
  </div>
</template>

<script setup>
import { onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import Icon from '../components/Icon.vue'
import ScanOverlay from './ui/ScanOverlay.vue'
import { useNetwork } from './useNetwork'
import { tapLight } from './native'
import { clearToken } from '../platform'

const router = useRouter()
const { online } = useNetwork()

const tabs = [
  { to: '/m/lookup',    icon: 'layers',          label: 'Tra cứu'   },
  { to: '/m/approve',   icon: 'clipboard-check', label: 'Duyệt'     },
  { to: '/m/receiving', icon: 'truck',           label: 'Tiếp nhận' },
  { to: '/m/dashboard', icon: 'bar-chart',       label: 'Bảng tin'  },
]

// Hết phiên (api.js bắn 'sc:unauth' khi 401/403) → về màn đăng nhập.
async function onUnauth() { try { await clearToken() } catch (e) {} ; router.replace('/m/setup') }
onMounted(() => window.addEventListener('sc:unauth', onUnauth))
onUnmounted(() => window.removeEventListener('sc:unauth', onUnauth))
</script>

<style scoped>
.m-shell { display: flex; flex-direction: column; height: 100vh; height: 100dvh; background: var(--m-bg); }
.m-content { flex: 1; min-height: 0; overflow: hidden; }
.m-content > * { height: 100%; }

.m-tabbar {
  display: flex; background: rgba(255,255,255,.92); backdrop-filter: saturate(1.5) blur(10px);
  border-top: 1px solid var(--m-line); box-shadow: 0 -2px 14px rgba(16,24,40,.05);
}
.m-tab {
  flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 3px; padding: 9px 0 10px; font-size: 11px; color: var(--m-ink-3); text-decoration: none;
  -webkit-tap-highlight-color: transparent; transition: color .15s; position: relative;
}
.m-tab__dot { position: absolute; top: 5px; width: 5px; height: 5px; border-radius: 50%; background: transparent; transition: background .2s; }
.m-tab__lbl { font-weight: 600; }
.m-tab--active { color: var(--m-navy); }
.m-tab--active .m-tab__dot { background: var(--m-navy); }
.m-tab--active :deep(svg) { transform: translateY(-1px); transition: transform .2s; }

/* transitions */
.m-fade-enter-active, .m-fade-leave-active { transition: opacity .18s ease, transform .18s ease; }
.m-fade-enter-from { opacity: 0; transform: translateY(6px); }
.m-fade-leave-to { opacity: 0; }
.m-net-slide-enter-active, .m-net-slide-leave-active { transition: all .25s ease; }
.m-net-slide-enter-from, .m-net-slide-leave-to { transform: translateY(-100%); opacity: 0; }
</style>
