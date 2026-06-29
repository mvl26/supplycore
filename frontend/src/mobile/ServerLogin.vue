<!-- frontend/src/mobile/ServerLogin.vue -->
<template>
  <div class="m-login">
    <h1 class="m-login__title">SupplyCore</h1>
    <label class="m-field">
      <span>Địa chỉ máy chủ</span>
      <input v-model="serverUrl" type="url" inputmode="url" placeholder="https://bv-abc.example.com" />
    </label>
    <label class="m-field">
      <span>Tài khoản</span>
      <input v-model="usr" type="text" autocapitalize="none" autocomplete="username" />
    </label>
    <label class="m-field">
      <span>Mật khẩu</span>
      <input v-model="pwd" type="password" autocomplete="current-password" />
    </label>
    <p v-if="auth.loginError" class="m-error">{{ auth.loginError }}</p>
    <button class="m-btn" :disabled="auth.loginLoading || !valid" @click="submit">
      {{ auth.loginLoading ? 'Đang đăng nhập…' : 'Đăng nhập' }}
    </button>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()
const serverUrl = ref('')
const usr = ref('')
const pwd = ref('')
const valid = computed(() => /^https?:\/\/.+/.test(serverUrl.value) && usr.value && pwd.value)

async function submit() {
  const ok = await auth.mobileLogin(serverUrl.value.trim(), usr.value.trim(), pwd.value)
  if (ok) router.replace('/m/lookup')
}
</script>

<style scoped>
.m-login { padding: 24px 18px; display: flex; flex-direction: column; gap: 16px; max-width: 420px; margin: 0 auto; }
.m-login__title { color: #1F4E79; font-size: 26px; font-weight: 700; text-align: center; margin-top: 32px; }
.m-field { display: flex; flex-direction: column; gap: 6px; font-size: 13px; color: #374151; }
.m-field input { border: 1px solid #d1d5db; border-radius: 8px; padding: 12px; font-size: 16px; }
.m-btn { background: #1F4E79; color: #fff; border: none; border-radius: 8px; padding: 14px; font-size: 16px; font-weight: 600; }
.m-btn:disabled { opacity: .5; }
.m-error { color: #b91c1c; font-size: 13px; }
</style>
