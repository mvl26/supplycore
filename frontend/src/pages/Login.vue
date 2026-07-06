<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import Icon from '../components/Icon.vue'

const router = useRouter()
const auth = useAuthStore()
const usr = ref('')
const pwd = ref('')
const showPwd = ref(false)

const highlights = [
  { icon: 'layers',   title: 'Quản lý lô & hạn dùng', desc: 'Xuất FEFO tự động, cảnh báo cận hạn' },
  { icon: 'shield',   title: 'Truy xuất & thu hồi',   desc: 'Lần vết lô vật tư toàn chuỗi cung ứng' },
  { icon: 'activity', title: 'Vận hành thời gian thực', desc: 'Tồn kho 3 tầng, bản đồ vị trí lưu trữ' },
  { icon: 'wallet',   title: 'Đối soát 3-way',  desc: 'Kiểm soát hóa đơn, thanh toán, chi phí' },
]

async function submit() {
  const ok = await auth.doLogin(usr.value, pwd.value)
  if (ok) {
    const redirect = router.currentRoute.value.query.redirect || '/dashboard'
    router.replace(redirect)
  }
}
</script>

<template>
  <div class="min-h-screen flex bg-sc-bg">
    <!-- ===== Brand panel (desktop) ===== -->
    <div class="hidden lg:flex lg:w-[46%] xl:w-[42%] relative overflow-hidden
      bg-gradient-to-br from-sc-navy via-sc-navy to-sc-navy-deep text-white flex-col">
      <!-- atmosphere -->
      <div class="pointer-events-none absolute inset-0">
        <div class="absolute -top-24 -right-24 w-96 h-96 rounded-full bg-sc-royal/25 blur-3xl" />
        <div class="absolute bottom-0 -left-20 w-80 h-80 rounded-full bg-sc-royal-light/15 blur-3xl" />
        <svg class="absolute right-6 top-1/2 -translate-y-1/2 opacity-[0.06]" width="420" height="420" viewBox="0 0 40 40">
          <path d="M20 4v32 M4 20h32" stroke="#fff" stroke-width="2.4" stroke-linecap="round" />
        </svg>
      </div>

      <div class="relative flex flex-col h-full p-12 xl:p-16">
        <!-- logo -->
        <div class="flex items-center gap-3">
          <svg width="46" height="46" viewBox="0 0 40 40" fill="none">
            <defs>
              <linearGradient id="lgLogo" x1="2" y1="2" x2="38" y2="38" gradientUnits="userSpaceOnUse">
                <stop stop-color="#9CC5E8" /><stop offset="1" stop-color="#2E75B6" />
              </linearGradient>
            </defs>
            <rect x="1.5" y="1.5" width="37" height="37" rx="12" fill="url(#lgLogo)" />
            <rect x="1.5" y="1.5" width="37" height="37" rx="12" fill="none"
              stroke="#fff" stroke-opacity="0.3" stroke-width="1.1" />
            <path d="M20 11v18 M11 20h18" stroke="#fff" stroke-width="3.8" stroke-linecap="round" />
          </svg>
          <div>
            <div class="text-xl font-extrabold tracking-tight">SupplyCore</div>
            <div class="text-[11px] uppercase tracking-[0.18em] text-white/50">Cung ứng Bệnh viện</div>
          </div>
        </div>

        <!-- headline -->
        <div class="mt-auto mb-10">
          <h1 class="text-3xl xl:text-[34px] font-extrabold leading-snug tracking-tight">
            Quản lý chuỗi cung ứng<br />y tế — chính xác & minh bạch
          </h1>
          <p class="mt-3 text-white/55 text-sm max-w-sm leading-relaxed">
            Nền tảng vận hành kho: từ hợp đồng, mua sắm, tiếp nhận đến
            chuyển kho và kế toán.
          </p>
        </div>

        <!-- highlights -->
        <div class="grid grid-cols-2 gap-3 sc-stagger">
          <div v-for="h in highlights" :key="h.title"
            class="rounded-xl bg-white/[0.06] border border-white/10 p-3.5
                   backdrop-blur-sm hover:bg-white/[0.1] transition-colors duration-200">
            <div class="h-8 w-8 rounded-lg bg-white/10 flex items-center justify-center text-sc-royal-light mb-2">
              <Icon :name="h.icon" :size="17" />
            </div>
            <div class="text-[13px] font-semibold leading-tight">{{ h.title }}</div>
            <div class="text-[11px] text-white/45 mt-0.5 leading-snug">{{ h.desc }}</div>
          </div>
        </div>

        <div class="mt-10 text-[11px] text-white/35">© 2026 SupplyCore · Phiên bản 0.1</div>
      </div>
    </div>

    <!-- ===== Form panel ===== -->
    <div class="flex-1 flex items-center justify-center p-6 sc-app-bg">
      <div class="w-full max-w-[400px] sc-rise">
        <!-- mobile logo -->
        <div class="lg:hidden flex flex-col items-center mb-7">
          <svg width="52" height="52" viewBox="0 0 40 40" fill="none">
            <defs>
              <linearGradient id="mbLogo" x1="2" y1="2" x2="38" y2="38" gradientUnits="userSpaceOnUse">
                <stop stop-color="#5B9BD5" /><stop offset="1" stop-color="#1F4E79" />
              </linearGradient>
            </defs>
            <rect x="1.5" y="1.5" width="37" height="37" rx="12" fill="url(#mbLogo)" />
            <path d="M20 11v18 M11 20h18" stroke="#fff" stroke-width="3.8" stroke-linecap="round" />
          </svg>
          <div class="text-xl font-extrabold tracking-tight text-sc-navy mt-2.5">SupplyCore</div>
          <div class="text-[11px] uppercase tracking-[0.16em] text-sc-text-muted">Cung ứng Bệnh viện</div>
        </div>

        <div class="bg-sc-surface rounded-2xl shadow-sc-lg border border-sc-border p-7 sm:p-8">
          <h2 class="text-xl font-bold text-sc-navy">Đăng nhập hệ thống</h2>
          <p class="text-[13px] text-sc-text-muted mt-1 mb-6">
            Sử dụng tài khoản nội bộ được cấp để tiếp tục.
          </p>

          <form @submit.prevent="submit" class="space-y-4">
            <div>
              <label class="sc-label">Email / Tên đăng nhập</label>
              <div class="relative">
                <span class="absolute left-3 top-1/2 -translate-y-1/2 text-sc-text-muted">
                  <Icon name="user" :size="17" />
                </span>
                <input v-model="usr" type="text" required autofocus autocomplete="username"
                  class="sc-input pl-9" placeholder="tên.dangnhap hoặc Administrator" />
              </div>
            </div>

            <div>
              <label class="sc-label">Mật khẩu</label>
              <div class="relative">
                <span class="absolute left-3 top-1/2 -translate-y-1/2 text-sc-text-muted">
                  <Icon name="shield" :size="17" />
                </span>
                <input v-model="pwd" :type="showPwd ? 'text' : 'password'" required
                  autocomplete="current-password" class="sc-input pl-9 pr-10"
                  placeholder="••••••••" />
                <button type="button" @click="showPwd = !showPwd"
                  class="absolute right-2.5 top-1/2 -translate-y-1/2 text-sc-text-muted
                         hover:text-sc-navy transition-colors"
                  :aria-label="showPwd ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'">
                  <Icon :name="showPwd ? 'eye-off' : 'eye'" :size="17" />
                </button>
              </div>
            </div>

            <Transition name="sc-modal">
              <div v-if="auth.loginError"
                class="flex items-start gap-2 bg-red-50 border border-red-200 text-[13px]
                       text-sc-danger px-3 py-2.5 rounded-lg">
                <Icon name="alert-triangle" :size="16" class="mt-px flex-shrink-0" />
                <span>{{ auth.loginError }}</span>
              </div>
            </Transition>

            <button type="submit" :disabled="auth.loginLoading"
              class="sc-btn-primary w-full py-2.5 text-[14px]">
              <Icon v-if="auth.loginLoading" name="rotate-cw" :size="16" class="animate-spin" />
              {{ auth.loginLoading ? 'Đang đăng nhập...' : 'Đăng nhập' }}
              <Icon v-if="!auth.loginLoading" name="arrow-right" :size="16" />
            </button>
          </form>

          <div class="mt-6 pt-5 border-t border-sc-border flex items-center gap-2
            text-[11.5px] text-sc-text-muted">
            <Icon name="shield" :size="14" class="text-sc-success" />
            Kết nối được mã hóa · Truy cập theo phân quyền vai trò
          </div>
        </div>

        <p class="text-center text-[11px] text-sc-text-muted mt-5 lg:hidden">
          © 2026 SupplyCore · Chuỗi cung ứng Bệnh viện v0.1
        </p>
      </div>
    </div>
  </div>
</template>
