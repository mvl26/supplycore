<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { call, logout } from '../api'
import Icon from '../components/Icon.vue'

const route = useRoute()
const router = useRouter()

const key = ref(route.query.key || '')
const pw = ref('')
const pw2 = ref('')
const show = ref(false)
const busy = ref(false)
const errorMsg = ref('')
const done = ref(false)

// Quy định mật khẩu mạnh — đồng bộ với backend validate_password_strength.
const checks = computed(() => {
  const p = pw.value || ''
  return {
    len: p.length >= 8,
    upper: /[A-Z]/.test(p),
    lower: /[a-z]/.test(p),
    digit: /[0-9]/.test(p),
    special: /[^A-Za-z0-9]/.test(p),
  }
})
const strong = computed(() => Object.values(checks.value).every(Boolean))
const match = computed(() => pw.value === pw2.value)
const canSubmit = computed(() => !!key.value && strong.value && match.value && !busy.value)

async function submit() {
  if (!canSubmit.value) return
  busy.value = true
  errorMsg.value = ''
  try {
    // Frappe consume reset-key + đặt mật khẩu mới (tự đăng nhập user).
    await call('frappe.core.doctype.user.user.update_password', {
      new_password: pw.value,
      key: key.value,
    })
    // update_password tự login → đăng xuất để quay về trang đăng nhập sạch sẽ.
    try { await logout() } catch (e) { /* ignore */ }
    done.value = true
    setTimeout(() => router.replace({ path: '/login', query: { reset: '1' } }), 1600)
  } catch (e) {
    errorMsg.value = e.message
      || 'Không đặt lại được mật khẩu. Liên kết có thể đã hết hạn — vui lòng yêu cầu gửi lại.'
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <div class="min-h-screen flex bg-sc-bg">
    <!-- ===== Brand panel (desktop) ===== -->
    <div class="hidden lg:flex lg:w-[46%] xl:w-[42%] relative overflow-hidden
      bg-gradient-to-br from-sc-navy via-sc-navy to-sc-navy-deep text-white flex-col">
      <div class="pointer-events-none absolute inset-0">
        <div class="absolute -top-24 -right-24 w-96 h-96 rounded-full bg-sc-royal/25 blur-3xl" />
        <div class="absolute bottom-0 -left-20 w-80 h-80 rounded-full bg-sc-royal-light/15 blur-3xl" />
      </div>
      <div class="relative flex flex-col h-full p-12 xl:p-16">
        <div class="flex items-center gap-3">
          <svg width="46" height="46" viewBox="0 0 40 40" fill="none">
            <defs>
              <linearGradient id="rpLogo" x1="2" y1="2" x2="38" y2="38" gradientUnits="userSpaceOnUse">
                <stop stop-color="#9CC5E8" /><stop offset="1" stop-color="#2E75B6" />
              </linearGradient>
            </defs>
            <rect x="1.5" y="1.5" width="37" height="37" rx="12" fill="url(#rpLogo)" />
            <path d="M20 11v18 M11 20h18" stroke="#fff" stroke-width="3.8" stroke-linecap="round" />
          </svg>
          <div>
            <div class="text-xl font-extrabold tracking-tight">SupplyCore</div>
            <div class="text-[11px] uppercase tracking-[0.18em] text-white/50">Chuỗi cung ứng Phân phối</div>
          </div>
        </div>
        <div class="mt-auto mb-10">
          <h1 class="text-3xl xl:text-[34px] font-extrabold leading-snug tracking-tight">
            Đặt lại mật khẩu<br />an toàn cho tài khoản của bạn
          </h1>
          <p class="mt-3 text-white/55 text-sm max-w-sm leading-relaxed">
            Tạo mật khẩu mạnh gồm chữ hoa, chữ thường, số và ký tự đặc biệt để
            bảo vệ dữ liệu vận hành.
          </p>
        </div>
        <div class="mt-10 text-[11px] text-white/35">© 2026 SupplyCore · Phiên bản 0.1</div>
      </div>
    </div>

    <!-- ===== Form panel ===== -->
    <div class="flex-1 flex items-center justify-center p-6 sc-app-bg">
      <div class="w-full max-w-[400px] sc-rise">
        <div class="lg:hidden flex flex-col items-center mb-7">
          <svg width="52" height="52" viewBox="0 0 40 40" fill="none">
            <defs>
              <linearGradient id="rpMb" x1="2" y1="2" x2="38" y2="38" gradientUnits="userSpaceOnUse">
                <stop stop-color="#5B9BD5" /><stop offset="1" stop-color="#1F4E79" />
              </linearGradient>
            </defs>
            <rect x="1.5" y="1.5" width="37" height="37" rx="12" fill="url(#rpMb)" />
            <path d="M20 11v18 M11 20h18" stroke="#fff" stroke-width="3.8" stroke-linecap="round" />
          </svg>
          <div class="text-xl font-extrabold tracking-tight text-sc-navy mt-2.5">SupplyCore</div>
        </div>

        <div class="bg-sc-surface rounded-2xl shadow-sc-lg border border-sc-border p-7 sm:p-8">
          <!-- Success state -->
          <template v-if="done">
            <div class="flex flex-col items-center text-center py-4">
              <div class="h-14 w-14 rounded-full bg-sc-success/15 text-sc-success flex items-center justify-center mb-4">
                <Icon name="check" :size="30" />
              </div>
              <h2 class="text-xl font-bold text-sc-navy">Đặt lại thành công</h2>
              <p class="text-[13px] text-sc-text-muted mt-1.5">
                Mật khẩu đã được cập nhật. Đang chuyển về trang đăng nhập…
              </p>
            </div>
          </template>

          <!-- Missing key -->
          <template v-else-if="!key">
            <h2 class="text-xl font-bold text-sc-navy">Liên kết không hợp lệ</h2>
            <p class="text-[13px] text-sc-text-muted mt-1.5 mb-6">
              Thiếu mã đặt lại mật khẩu. Vui lòng mở đúng liên kết trong email, hoặc yêu cầu gửi lại.
            </p>
            <router-link to="/login" class="sc-btn-secondary w-full py-2.5 text-[14px] justify-center">
              <Icon name="chevron-left" :size="16" /> Về trang đăng nhập
            </router-link>
          </template>

          <!-- Form -->
          <template v-else>
            <h2 class="text-xl font-bold text-sc-navy">Đặt mật khẩu mới</h2>
            <p class="text-[13px] text-sc-text-muted mt-1 mb-6">
              Nhập mật khẩu mới cho tài khoản SupplyCore của bạn.
            </p>

            <form @submit.prevent="submit" class="space-y-4">
              <div>
                <label class="sc-label">Mật khẩu mới</label>
                <div class="relative">
                  <span class="absolute left-3 top-1/2 -translate-y-1/2 text-sc-text-muted">
                    <Icon name="shield" :size="17" />
                  </span>
                  <input v-model="pw" :type="show ? 'text' : 'password'" required autofocus
                    autocomplete="new-password" class="sc-input pl-9 pr-10" placeholder="••••••••" />
                  <button type="button" @click="show = !show"
                    class="absolute right-2.5 top-1/2 -translate-y-1/2 text-sc-text-muted hover:text-sc-navy transition-colors"
                    :aria-label="show ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'">
                    <Icon :name="show ? 'eye-off' : 'eye'" :size="17" />
                  </button>
                </div>
              </div>

              <div>
                <label class="sc-label">Nhập lại mật khẩu</label>
                <div class="relative">
                  <span class="absolute left-3 top-1/2 -translate-y-1/2 text-sc-text-muted">
                    <Icon name="shield" :size="17" />
                  </span>
                  <input v-model="pw2" :type="show ? 'text' : 'password'" required
                    autocomplete="new-password" class="sc-input pl-9"
                    :class="pw2 && !match ? 'border-sc-danger' : ''" placeholder="Gõ lại mật khẩu" />
                </div>
              </div>

              <ul v-if="pw" class="text-xs space-y-0.5 pl-0.5">
                <li :class="checks.len ? 'text-sc-success' : 'text-sc-text-muted'">
                  {{ checks.len ? '✓' : '•' }} Ít nhất 8 ký tự</li>
                <li :class="checks.upper && checks.lower ? 'text-sc-success' : 'text-sc-text-muted'">
                  {{ checks.upper && checks.lower ? '✓' : '•' }} Có chữ in HOA và chữ thường</li>
                <li :class="checks.digit ? 'text-sc-success' : 'text-sc-text-muted'">
                  {{ checks.digit ? '✓' : '•' }} Có chữ số</li>
                <li :class="checks.special ? 'text-sc-success' : 'text-sc-text-muted'">
                  {{ checks.special ? '✓' : '•' }} Có ký tự đặc biệt (@ # ! $ %…)</li>
                <li v-if="pw2" :class="match ? 'text-sc-success' : 'text-sc-danger'">
                  {{ match ? '✓' : '✕' }} Nhập lại khớp</li>
              </ul>

              <Transition name="sc-modal">
                <div v-if="errorMsg"
                  class="flex items-start gap-2 bg-sc-danger-50 border border-sc-danger/40 text-[13px] text-sc-danger px-3 py-2.5 rounded-lg">
                  <Icon name="alert-triangle" :size="16" class="mt-px flex-shrink-0" />
                  <span>{{ errorMsg }}</span>
                </div>
              </Transition>

              <button type="submit" :disabled="!canSubmit"
                class="sc-btn-primary w-full py-2.5 text-[14px]">
                <Icon v-if="busy" name="rotate-cw" :size="16" class="animate-spin" />
                {{ busy ? 'Đang cập nhật...' : 'Đặt lại mật khẩu' }}
                <Icon v-if="!busy" name="check" :size="16" />
              </button>

              <router-link to="/login"
                class="block text-center text-[13px] text-sc-text-muted hover:text-sc-navy mt-1">
                Quay về đăng nhập
              </router-link>
            </form>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>
