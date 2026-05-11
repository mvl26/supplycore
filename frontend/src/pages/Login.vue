<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()
const usr = ref('')
const pwd = ref('')
const showPwd = ref(false)

async function submit() {
  const ok = await auth.doLogin(usr.value, pwd.value)
  if (ok) {
    const redirect = router.currentRoute.value.query.redirect || '/dashboard'
    router.replace(redirect)
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-sc-navy via-sc-royal to-sc-royal-light p-4">
    <div class="w-full max-w-md">
      <div class="text-center mb-6">
        <div class="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-white/10 backdrop-blur-sm text-3xl mb-3">
          🏥
        </div>
        <h1 class="text-3xl font-bold text-white tracking-tight">SupplyCore</h1>
        <p class="text-white/70 text-sm mt-1">Hospital Supply Chain Management</p>
      </div>

      <div class="bg-white rounded-2xl shadow-2xl p-8">
        <h2 class="text-xl font-semibold text-sc-navy mb-1">Đăng nhập</h2>
        <p class="text-sm text-sc-text-muted mb-5">Nhập email/username và mật khẩu</p>

        <form @submit.prevent="submit" class="space-y-3">
          <div>
            <label class="text-xs font-medium text-sc-text-muted block mb-1">Email / Username</label>
            <input v-model="usr" type="text" required autofocus
              autocomplete="username"
              class="sc-input"
              placeholder="user@example.com hoặc Administrator" />
          </div>
          <div>
            <label class="text-xs font-medium text-sc-text-muted block mb-1">Mật khẩu</label>
            <div class="relative">
              <input v-model="pwd" :type="showPwd ? 'text' : 'password'" required
                autocomplete="current-password"
                class="sc-input pr-10"
                placeholder="••••••••" />
              <button type="button" @click="showPwd = !showPwd"
                class="absolute right-2 top-1/2 -translate-y-1/2 text-sc-text-muted text-sm">
                {{ showPwd ? '🙈' : '👁️' }}
              </button>
            </div>
          </div>

          <div v-if="auth.loginError"
            class="bg-red-50 border-l-4 border-sc-danger text-sm text-sc-danger px-3 py-2 rounded">
            {{ auth.loginError }}
          </div>

          <button type="submit" :disabled="auth.loginLoading"
            class="sc-btn-primary w-full py-2.5 mt-2 disabled:opacity-50">
            {{ auth.loginLoading ? 'Đang đăng nhập...' : 'Đăng nhập' }}
          </button>
        </form>

        <div class="mt-5 text-center text-xs text-sc-text-muted">
          © 2026 SupplyCore · Hospital Supply Chain v0.1
        </div>
      </div>
    </div>
  </div>
</template>
