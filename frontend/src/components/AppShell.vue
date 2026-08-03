<script setup>
import { computed, ref, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { MODULES } from '../modules'
import { NAV_BLOCKS } from '../nav-blocks'
import { useAuthStore } from '../stores/auth'
import { useAccessStore } from '../stores/access'
import Icon from './Icon.vue'
import Modal from './Modal.vue'
import OfflineBanner from './OfflineBanner.vue'
import { APP_VERSION, BUILD_DATE, RELEASE_NOTES } from '../version'

const showVersionModal = ref(false)

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const access = useAccessStore()

// Sidebar state — collapse persists; drawer is mobile-only
const collapsed = ref(localStorage.getItem('sc-sidebar') === '1')
const sidebarOpen = ref(false)
const userMenuOpen = ref(false)

function toggleCollapse() {
  collapsed.value = !collapsed.value
  localStorage.setItem('sc-sidebar', collapsed.value ? '1' : '0')
}

// Active persona — derived 100% from logged-in user's Frappe roles.
// There is intentionally no switcher: persona is RBAC, not preference.
const persona = computed(() => access.activePersona)

// ---------------------------------------------------------------------------
// 3 khối phân hệ (MUA HÀNG / BÁN HÀNG / DÙNG CHUNG) — "không có phận sự thì
// không thấy": mục gate theo quyền doctype/feature, khối rỗng bị ẩn.
// ---------------------------------------------------------------------------
function itemVisible(item) {
  if (item.always) return true
  if (item.dt) return access.canDoctype(item.dt)
  if (item.feat) return access.canFeature(item.feat)
  return false
}
// Khối hiện khi: (a) vai user thuộc block.roles (hoặc block không giới hạn / user
// là admin) VÀ (b) có >=1 mục qua item-gate. Tách phân hệ theo vai (điểm 4 spec).
function blockAllowed(b) {
  if (access.is_admin) return true
  if (!b.roles || !b.roles.length) return true
  const roles = access.roles || []
  return b.roles.some(r => roles.includes(r))
}
const visibleBlocks = computed(() =>
  NAV_BLOCKS
    .filter(blockAllowed)
    .map(b => ({ ...b, items: b.items.filter(itemVisible) }))
    .filter(b => b.items.length)
)

// Route so khớp mục nav (dùng cho active + auto-expand + chip page-header).
const decode = (p) => { try { return decodeURIComponent(p) } catch { return p } }
function isActive(path) {
  if (path === '/dashboard') return route.path === '/' || route.path === '/dashboard'
  return decode(route.path) === decode(path)
}
function blockHasActive(b) { return b.items.some(i => isActive(i.to)) }

// Khối chứa trang đang mở — cho chip phân hệ ở page-header.
const activeBlock = computed(() =>
  visibleBlocks.value.find(blockHasActive) || null
)

// Collapse/expand từng khối — nhớ localStorage; mặc định MỞ; khối chứa trang
// đang mở luôn được coi là mở (không ẩn mục active).
const blockCollapsed = reactive(
  JSON.parse(localStorage.getItem('sc-nav-blocks') || '{}')
)
function toggleBlock(id) {
  blockCollapsed[id] = !blockCollapsed[id]
  localStorage.setItem('sc-nav-blocks', JSON.stringify(blockCollapsed))
}
function isBlockOpen(b) {
  if (blockHasActive(b)) return true
  return !blockCollapsed[b.id]
}
function isDashboardActive() { return route.path === '/' || route.path === '/dashboard' }

const currentTitle = computed(() => {
  if (route.name === 'module') {
    const m = MODULES.find(x => x.id === `m${route.params.n}`)
    return m ? `${m.code} · ${m.name}` : 'Phân hệ'
  }
  return route.meta?.title || 'SupplyCore'
})

const initials = computed(() => {
  const n = auth.user.full_name || auth.user.name || 'G'
  return n.trim().split(/\s+/).slice(-2).map(w => w[0]).join('').toUpperCase().slice(0, 2)
})

function closeDrawer() { sidebarOpen.value = false }

async function logout() {
  await auth.doLogout()
  router.replace('/login')
}
</script>

<template>
  <div class="min-h-screen flex sc-app-bg">
    <OfflineBanner />
    <!-- Mobile backdrop -->
    <Transition name="route">
      <div v-if="sidebarOpen" class="fixed inset-0 z-40 bg-sc-navy-900/55 backdrop-blur-[2px] md:hidden"
        @click="sidebarOpen = false" />
    </Transition>

    <!-- ============ Sidebar ============ -->
    <aside
      class="fixed md:sticky top-0 z-50 h-screen flex flex-col flex-shrink-0
             bg-gradient-to-b from-sc-navy to-sc-navy-deep text-white
             border-r border-white/5 shadow-sc-lg md:shadow-none
             transition-[width,transform] duration-300 ease-sc"
      :class="[
        collapsed ? 'md:w-[78px]' : 'md:w-[266px]',
        sidebarOpen ? 'w-[266px] translate-x-0' : 'w-[266px] -translate-x-full md:translate-x-0',
      ]">

      <!-- Brand -->
      <div class="h-[60px] flex items-center gap-3 px-4 border-b border-white/8 flex-shrink-0">
        <div class="relative flex-shrink-0">
          <svg width="38" height="38" viewBox="0 0 40 40" fill="none">
            <defs>
              <linearGradient id="scLogoG" x1="2" y1="2" x2="38" y2="38" gradientUnits="userSpaceOnUse">
                <stop stop-color="#7FB4E0" />
                <stop offset="1" stop-color="#1F4E79" />
              </linearGradient>
            </defs>
            <rect x="1.4" y="1.4" width="37.2" height="37.2" rx="11" fill="url(#scLogoG)" />
            <rect x="1.4" y="1.4" width="37.2" height="37.2" rx="11" fill="none"
              stroke="#FFFFFF" stroke-opacity="0.28" stroke-width="1.1" />
            <path d="M20 11v18 M11 20h18" stroke="#FFFFFF" stroke-width="3.7" stroke-linecap="round" />
          </svg>
        </div>
        <div v-if="!collapsed" class="min-w-0 overflow-hidden">
          <div class="text-[15px] font-extrabold tracking-tight leading-tight">SupplyCore</div>
          <div class="text-[10.5px] uppercase tracking-[0.14em] text-white/70 leading-tight mt-0.5">
            Chuỗi cung ứng Phân phối
          </div>
        </div>
      </div>

      <!-- Persona card (named persona only) -->
      <div v-if="persona && !persona.flat && !collapsed"
        class="mx-3 mt-3 mb-1 rounded-xl border border-white/10 bg-white/5 backdrop-blur-sm
               px-3 py-2.5 flex items-start gap-2.5">
        <div class="h-10 w-10 rounded-lg flex-shrink-0 flex items-center justify-center
                    text-white font-extrabold text-[15px] shadow-sc-xs"
          :style="{ background: persona.color }">
          {{ persona.avatar }}
        </div>
        <div class="min-w-0 flex-1">
          <div class="text-[13px] font-bold leading-tight truncate">{{ persona.name }}</div>
          <div class="text-[10.5px] text-white/55 leading-tight truncate mt-0.5">{{ persona.title }}</div>
          <span class="inline-block mt-1.5 text-[9.5px] font-bold tracking-[0.04em]
                       bg-white/12 text-white/90 px-2 py-[2px] rounded-full">
            {{ persona.role }}
          </span>
        </div>
      </div>

      <!-- Nav — 3 khối phân hệ (Mua hàng / Bán hàng / Dùng chung) -->
      <nav class="flex-1 overflow-y-auto overflow-x-hidden py-3 sc-nav-scroll">

        <!-- Ghim: Tổng quan (luôn hiện) -->
        <div class="space-y-0.5 mb-1.5">
          <router-link to="/dashboard" @click="closeDrawer" :title="collapsed ? 'Tổng quan' : ''"
            class="sc-nav-item group"
            :class="[ isDashboardActive() ? 'sc-nav-active' : 'sc-nav-idle',
                      collapsed ? 'justify-center px-0 mx-2' : 'px-3 mx-2.5' ]">
            <span v-if="isDashboardActive()" class="sc-nav-bar" style="background:#7FB4E0" />
            <Icon name="layout-dashboard" :size="19"
              class="transition-transform duration-200 ease-sc group-hover:scale-110" />
            <span v-if="!collapsed" class="text-[13.5px] font-medium truncate">Tổng quan</span>
          </router-link>
        </div>

        <div v-for="b in visibleBlocks" :key="b.id" class="mt-3 first:mt-1.5">
          <!-- Header nhóm (không phải link — bấm để collapse) -->
          <button v-if="!collapsed" type="button" @click="toggleBlock(b.id)"
            class="w-full flex items-center gap-2 px-4 mb-1 group/hd select-none">
            <Icon :name="b.icon" :size="14" class="flex-shrink-0" :style="{ color: b.accent }" />
            <span class="text-[10.5px] font-extrabold uppercase tracking-[0.15em]"
              :style="{ color: b.accent }">{{ b.label }}</span>
            <span class="ml-auto flex items-center gap-1.5">
              <span class="h-[3px] w-6 rounded-full opacity-70" :style="{ background: b.accent }" />
              <Icon name="chevron-down" :size="14"
                class="text-white/60 group-hover/hd:text-white/80 transition-transform duration-200"
                :class="isBlockOpen(b) ? '' : '-rotate-90'" />
            </span>
          </button>
          <!-- Chế độ thu gọn: chỉ 1 dải màu phân cách khối -->
          <div v-else class="mx-3 my-2 h-[3px] rounded-full opacity-70" :style="{ background: b.accent }" />

          <div v-show="collapsed || isBlockOpen(b)" class="space-y-0.5">
            <router-link v-for="item in b.items" :key="item.to"
              :to="item.to" @click="closeDrawer" :title="collapsed ? item.label : ''"
              class="sc-nav-item group"
              :class="[ isActive(item.to) ? 'sc-nav-on' : 'sc-nav-idle',
                        collapsed ? 'justify-center px-0 mx-2' : 'px-3 mx-2.5' ]"
              :style="isActive(item.to)
                ? { background: `linear-gradient(90deg, ${b.tint}, ${b.tintSoft})`, color: '#fff' }
                : null">
              <span v-if="isActive(item.to)" class="sc-nav-bar"
                :style="{ background: b.accent, boxShadow: `0 0 10px ${b.accent}` }" />
              <Icon :name="item.icon" :size="18.5"
                class="transition-transform duration-200 ease-sc group-hover:scale-110"
                :style="isActive(item.to) ? { color: b.accent } : null" />
              <span v-if="!collapsed" class="text-[13.5px] font-medium truncate">{{ item.label }}</span>
            </router-link>
          </div>
        </div>
      </nav>

      <!-- Scope note (named persona only) -->
      <div v-if="persona && !persona.flat && !collapsed"
        class="mx-3 mb-2 px-3 py-2 rounded-lg bg-sc-success/10 border border-sc-success/40
               text-[10.5px] leading-relaxed text-emerald-100/85">
        <div class="flex items-start gap-1.5">
          <Icon name="shield-check" :size="13" class="mt-[1px] flex-shrink-0 text-emerald-300" />
          <div class="min-w-0">
            <div><b class="text-emerald-200">Phạm vi:</b> {{ persona.scope }}</div>
            <div class="mt-0.5"><b class="text-emerald-200">2FA:</b> {{ persona.twofa }}</div>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="border-t border-white/8 flex-shrink-0 p-2.5">
        <button @click="toggleCollapse"
          class="hidden md:flex items-center gap-2.5 w-full rounded-lg px-3 py-2
                 text-white/55 hover:text-white hover:bg-white/[0.07]
                 transition-colors duration-150"
          :class="collapsed ? 'justify-center' : ''">
          <Icon name="panel-left" :size="18"
            class="transition-transform duration-300 ease-sc" :class="collapsed ? 'rotate-180' : ''" />
          <span v-if="!collapsed" class="text-xs font-medium">Thu gọn thanh điều hướng</span>
        </button>
        <button v-if="!collapsed" @click="showVersionModal = true"
          class="w-full px-3 pt-1.5 text-[10.5px] text-white/65 hover:text-white/90 flex items-center gap-1.5 cursor-pointer text-left">
          <span class="h-1.5 w-1.5 rounded-full bg-sc-success/80" />
          <span>v{{ APP_VERSION }} · {{ auth.primaryRole }}</span>
          <Icon name="chevron-right" :size="14" class="ml-auto text-white/60" />
        </button>
      </div>
    </aside>

    <!-- ============ Main column ============ -->
    <div class="flex-1 flex flex-col min-w-0">
      <!-- Top bar -->
      <header class="sticky top-0 z-30 h-[60px] flex items-center gap-3 px-4 md:px-6
        bg-sc-surface/85 backdrop-blur-md border-b border-sc-border">
        <button @click="sidebarOpen = true" class="sc-icon-btn md:hidden">
          <Icon name="menu" :size="20" />
        </button>

        <div class="flex items-center gap-2.5 min-w-0">
          <!-- Chip phân hệ: emoji + tên khối + màu — luôn biết đang ở phân hệ nào -->
          <span v-if="activeBlock"
            class="inline-flex items-center gap-1.5 h-7 pl-2 pr-2.5 rounded-md text-[11.5px] font-bold"
            :style="{ background: activeBlock.accentBase + '1A', color: activeBlock.accentBase,
                      boxShadow: `inset 3px 0 0 ${activeBlock.accentBase}` }"
            :title="`Phân hệ: ${activeBlock.label}`">
            <Icon :name="activeBlock.icon" :size="13" />
            <span class="hidden sm:inline">{{ activeBlock.label }}</span>
          </span>
          <span v-else class="hidden sm:inline-flex h-7 w-7 items-center justify-center rounded-md
            bg-sc-royal-50 text-sc-royal">
            <Icon name="circle-dot" :size="15" />
          </span>
          <h2 class="text-[15px] font-bold text-sc-navy truncate">{{ currentTitle }}</h2>
        </div>

        <div class="flex-1" />

        <router-link v-if="access.canFeature('alerts')" to="/alerts"
          class="sc-icon-btn relative" title="Cảnh báo">
          <Icon name="bell" :size="19" />
        </router-link>

        <!-- Persona chip — read-only badge of the active persona (no switching) -->
        <div v-if="persona && !persona.flat"
          class="hidden md:flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 bg-sc-bg-soft"
          :title="`Phân quyền theo chân dung: ${persona.role}`">
          <span class="h-5 w-5 rounded flex items-center justify-center text-[10px]
                       font-extrabold text-white flex-shrink-0"
            :style="{ background: persona.color }">{{ persona.avatar }}</span>
          <span class="text-[12px] font-semibold text-sc-navy max-w-[160px] truncate">
            {{ persona.name }}
          </span>
        </div>

        <div class="h-6 w-px bg-sc-border mx-0.5 hidden sm:block" />

        <!-- User menu -->
        <div class="relative" v-click-outside="() => userMenuOpen = false">
          <button @click.stop="userMenuOpen = !userMenuOpen"
            class="flex items-center gap-2.5 rounded-lg pl-1.5 pr-2 py-1
                   hover:bg-sc-bg-soft transition-colors duration-150">
            <div class="h-8 w-8 rounded-lg bg-gradient-to-br from-sc-royal to-sc-navy
              text-white flex items-center justify-center font-bold text-xs shadow-sc-xs">
              {{ initials }}
            </div>
            <div class="text-left hidden sm:block leading-tight">
              <div class="text-[13px] font-semibold text-sc-text max-w-[140px] truncate">
                {{ auth.user.full_name || auth.user.name }}
              </div>
              <div class="text-[11px] text-sc-text-muted">{{ auth.primaryRole }}</div>
            </div>
            <Icon name="chevron-down" :size="15"
              class="text-sc-text-muted transition-transform duration-200"
              :class="userMenuOpen ? 'rotate-180' : ''" />
          </button>
          <Transition name="sc-pop">
            <div v-if="userMenuOpen"
              class="absolute right-0 top-full mt-2 w-60 bg-sc-surface rounded-xl
                     shadow-sc-lg border border-sc-border py-1.5 z-40 origin-top-right">
              <div class="px-3.5 py-2.5 border-b border-sc-border">
                <div class="text-[13px] font-semibold text-sc-text truncate">
                  {{ auth.user.full_name || auth.user.name }}
                </div>
                <div class="text-[11px] text-sc-text-muted truncate">
                  {{ auth.user.email || auth.user.name }}
                </div>
              </div>
              <button @click="userMenuOpen = false; logout()"
                class="flex items-center gap-2.5 w-full text-left px-3.5 py-2.5 text-[13px]
                       font-medium text-sc-danger hover:bg-sc-danger-50 transition-colors">
                <Icon name="log-out" :size="17" />
                Đăng xuất
              </button>
            </div>
          </Transition>
        </div>
      </header>

      <!-- Page body -->
      <main class="flex-1 overflow-y-auto">
        <div class="p-4 md:p-6 lg:p-7 max-w-[1600px] mx-auto w-full">
          <slot />
        </div>
      </main>
    </div>

    <!-- FEAT-005: Version / Changelog modal -->
    <Modal :open="showVersionModal" title="Phiên bản & Changelog" @close="showVersionModal = false" size="lg">
      <div class="space-y-1 text-sm mb-4 pb-3 border-b border-sc-border">
        <div><span class="text-sc-text-muted">Phiên bản:</span> <strong>v{{ APP_VERSION }}</strong></div>
        <div><span class="text-sc-text-muted">Build date:</span> {{ BUILD_DATE }}</div>
        <div><span class="text-sc-text-muted">Role:</span> {{ auth.primaryRole }}</div>
      </div>
      <div class="space-y-5 max-h-[60vh] overflow-y-auto">
        <div v-for="r in RELEASE_NOTES" :key="r.version">
          <div class="flex items-baseline gap-2 mb-2">
            <h3 class="font-semibold text-sc-navy">v{{ r.version }}</h3>
            <span class="text-xs text-sc-text-muted">{{ r.date }} — {{ r.title }}</span>
          </div>
          <ul class="space-y-1.5 text-sm pl-1">
            <li v-for="(i, k) in r.items" :key="k" class="flex items-start gap-2">
              <span class="inline-block px-1.5 py-0.5 rounded text-[10px] font-semibold flex-shrink-0 mt-0.5"
                :class="{
                  'bg-sc-danger-50 text-sc-danger':    i.type === 'fix',
                  'bg-sc-info-50 text-sc-info':  i.type === 'feat',
                  'bg-purple-100 text-purple-700': i.type === 'ux',
                  'bg-sc-warning-50 text-sc-warning':i.type === 'perf',
                  'bg-sc-bg-soft text-gray-700':  i.type === 'docs',
                }">
                {{ i.type.toUpperCase() }}
              </span>
              <span>{{ i.text }}</span>
            </li>
          </ul>
        </div>
      </div>
    </Modal>
  </div>
</template>

<style scoped>
/* Nav item base */
.sc-nav-item {
  position: relative;
  display: flex;
  align-items: center;
  gap: 11px;
  height: 40px;
  border-radius: 9px;
  transition: background-color .15s ease, color .15s ease;
}
.sc-nav-idle { color: rgba(255, 255, 255, 0.62); }
.sc-nav-idle:hover {
  color: #fff;
  background-color: rgba(255, 255, 255, 0.07);
}
.sc-nav-active {
  color: #fff;
  background: linear-gradient(90deg, rgba(91, 155, 213, 0.30), rgba(91, 155, 213, 0.07));
}
.sc-nav-active :deep(.sc-icon) { color: #9CC5E8; }
/* Mục active trong khối: nền + màu icon set inline theo màu khối; class chỉ giữ chữ trắng + hover nhẹ. */
.sc-nav-on { color: #fff; font-weight: 600; }
@media (prefers-reduced-motion: reduce) {
  .sc-nav-item, .sc-nav-item :deep(.sc-icon) { transition: none !important; }
  .sc-nav-bar { animation: none !important; }
}
/* Focus bàn phím rõ ràng (a11y) */
.sc-nav-item:focus-visible {
  outline: 2px solid rgba(255,255,255,0.55);
  outline-offset: -2px;
}

/* Sliding accent bar */
.sc-nav-bar {
  position: absolute;
  left: -10.5px;
  top: 50%;
  height: 22px;
  width: 3.5px;
  border-radius: 999px;
  background: #7FB4E0;
  box-shadow: 0 0 10px rgba(127, 180, 224, 0.7);
  transform: translateY(-50%);
  animation: sc-bar-in .26s cubic-bezier(0.22, 1, 0.36, 1) both;
}
@keyframes sc-bar-in {
  from { opacity: 0; height: 4px; }
  to   { opacity: 1; height: 22px; }
}

/* Dark scrollbar inside sidebar */
.sc-nav-scroll::-webkit-scrollbar { width: 6px; }
.sc-nav-scroll::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.14);
  border: none;
}
.sc-nav-scroll::-webkit-scrollbar-thumb:hover { background: rgba(255, 255, 255, 0.24); }

/* User-menu popover */
.sc-pop-enter-active { transition: opacity .16s ease, transform .16s cubic-bezier(0.22, 1, 0.36, 1); }
.sc-pop-leave-active { transition: opacity .1s ease, transform .1s ease; }
.sc-pop-enter-from, .sc-pop-leave-to { opacity: 0; transform: translateY(-6px) scale(0.97); }

.route-enter-active, .route-leave-active { transition: opacity .2s ease; }
.route-enter-from, .route-leave-to { opacity: 0; }
</style>
