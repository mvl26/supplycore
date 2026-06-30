<!-- frontend/src/mobile/ServerLogin.vue — màn đăng nhập premium -->
<template>
  <div class="login m-app">
    <div class="login__hero">
      <div class="login__logo"><Icon name="layers" :size="30" /></div>
      <div class="login__brand">SupplyCore</div>
      <div class="login__tag">Quản lý vật tư y tế</div>
    </div>

    <form class="login__card" @submit.prevent="submit">
      <label class="m-field">
        <span>Địa chỉ máy chủ</span>
        <input class="m-input" v-model="serverUrl" type="url" inputmode="url" autocapitalize="none"
               autocomplete="off" placeholder="https://bv-abc.example.com" />
      </label>
      <label class="m-field">
        <span>Tài khoản</span>
        <input class="m-input" v-model="usr" type="text" autocapitalize="none" autocomplete="username" />
      </label>
      <label class="m-field">
        <span>Mật khẩu</span>
        <input class="m-input" v-model="pwd" type="password" autocomplete="current-password"
               @keyup.enter="submit" />
      </label>

      <transition name="m-fade">
        <p v-if="auth.loginError" class="login__err"><Icon name="alert-triangle" :size="15" /> {{ auth.loginError }}</p>
      </transition>

      <button class="m-btn" type="submit" :disabled="auth.loginLoading || !valid">
        <Icon v-if="auth.loginLoading" name="rotate-cw" :size="18" class="m-ptr__spin" />
        {{ auth.loginLoading ? 'Đang đăng nhập…' : 'Đăng nhập' }}
      </button>
    </form>

    <div class="login__foot">Bảo mật bằng mã thông báo (token)</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { notifyError, tapMedium } from './native'
import Icon from '../components/Icon.vue'
import { getServerUrl } from '../platform'

const auth = useAuthStore()
const router = useRouter()
const serverUrl = ref('')
const usr = ref('')
const pwd = ref('')
const valid = computed(() => /^https?:\/\/.+/.test(serverUrl.value) && usr.value && pwd.value)

// Nạp lại địa chỉ máy chủ đã lưu → người dùng không cần gõ lại sau mỗi lần đăng xuất.
onMounted(async () => {
  try {
    const saved = await getServerUrl()
    if (saved) serverUrl.value = saved
  } catch (e) { /* bỏ qua khi chạy trên web */ }
})

async function submit() {
  if (!valid.value || auth.loginLoading) return
  tapMedium()
  const ok = await auth.mobileLogin(serverUrl.value.trim(), usr.value.trim(), pwd.value)
  if (ok) router.replace('/m/lookup')
  else notifyError()
}
</script>

<style scoped>
.login { min-height: 100vh; min-height: 100dvh; display: flex; flex-direction: column;
  background: var(--m-bg); }
.login__hero { padding: calc(var(--m-safe-t) + 56px) 24px 40px; text-align: center; color: #fff;
  background: linear-gradient(150deg, var(--m-navy) 0%, var(--m-royal) 100%);
  border-radius: 0 0 28px 28px; box-shadow: 0 10px 30px rgba(31,78,121,.25); }
.login__logo { width: 64px; height: 64px; margin: 0 auto 14px; border-radius: 18px;
  display: grid; place-items: center; background: rgba(255,255,255,.16); backdrop-filter: blur(4px); }
.login__brand { font-size: 26px; font-weight: 750; letter-spacing: -.02em; }
.login__tag { font-size: 13px; opacity: .85; margin-top: 3px; }
.login__card { margin: -22px 18px 0; background: #fff; border-radius: var(--m-r);
  box-shadow: var(--m-shadow); padding: 20px 18px; display: flex; flex-direction: column; gap: 14px; }
.login__err { color: var(--m-crit); font-size: 13px; display: flex; align-items: center; gap: 6px; margin: 0; }
.login__foot { margin-top: auto; padding: 20px; text-align: center; font-size: 12px; color: var(--m-ink-3); }
.m-fade-enter-active, .m-fade-leave-active { transition: opacity .2s; }
.m-fade-enter-from, .m-fade-leave-to { opacity: 0; }
</style>
