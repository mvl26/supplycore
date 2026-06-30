import { defineStore } from 'pinia'
import { login as apiLogin, logout as apiLogout, getSession, getUserInfo, mobileLoginApi } from '../api'
import { isNative, setServerUrl, setToken, clearToken, getToken } from '../platform'
import { useAccessStore } from './access'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: window.sc_session_user || { name: 'Guest', is_guest: true, roles: [] },
    booted: false,
    loginError: null,
    loginLoading: false,
  }),
  getters: {
    isGuest: (s) => !s.user || s.user.is_guest || s.user.name === 'Guest',
    isManager: (s) => s.user?.roles?.includes('SupplyCore Manager'),
    isAdmin: (s) => s.user?.roles?.includes('System Manager') || s.user?.roles?.includes('SupplyCore Manager'),
    isExecutive: (s) => s.user?.roles?.includes('SupplyCore Executive'),
    isAccountant: (s) => s.user?.roles?.includes('SupplyCore Accountant'),
    isStorekeeper: (s) => s.user?.roles?.includes('SupplyCore Storekeeper'),
    primaryRole: (s) => {
      const order = ['SupplyCore Executive', 'SupplyCore Manager',
        'SupplyCore Accountant', 'SupplyCore Storekeeper',
        'Pharmacy Officer', 'Warehouse Officer', 'SupplyCore Ward Staff']
      return order.find(r => s.user?.roles?.includes(r)) || 'User'
    },
  },
  actions: {
    async boot() {
      if (this.booted) return
      const sess = await getSession()
      if (sess === 'Guest') {
        // Native: phân biệt 401 thật (token bị xoá bởi api.js) với lỗi mạng
        // tạm thời (token vẫn còn trong Preferences). Khi mạng chập → getSession
        // catch mọi lỗi và trả 'Guest', nhưng token chưa bị xoá. Không hạ user
        // xuống Guest; không đặt booted=true để boot() có thể thử lại lần sau.
        if (isNative() && (await getToken())) return
        this.user = { name: 'Guest', is_guest: true, roles: [] }
        useAccessStore().reset()
      } else {
        const info = await getUserInfo(sess)
        this.user = {
          name: sess,
          full_name: info?.full_name || sess,
          email: sess,
          user_image: info?.user_image,
          is_guest: false,
          // Web: roles từ shell global. Native (không có global) → roles từ getUserInfo.
          roles: window.sc_session_user?.roles || info?.roles || [],
        }
        await useAccessStore().load(true)
      }
      this.booted = true
    },
    async doLogin(usr, pwd) {
      this.loginError = null
      this.loginLoading = true
      try {
        await apiLogin(usr, pwd)
        // Reset booted flag để boot() refresh user info từ session mới
        this.booted = false
        await this.boot()
        return true
      } catch (e) {
        this.loginError = e.message || 'Đăng nhập thất bại'
        return false
      } finally {
        this.loginLoading = false
      }
    },
    async mobileLogin(serverUrl, usr, pwd) {
      this.loginError = null
      this.loginLoading = true
      try {
        const r = await mobileLoginApi(serverUrl, usr, pwd)
        await setServerUrl(serverUrl)
        await setToken(r.api_key, r.api_secret)
        this.user = { name: r.user, full_name: r.full_name, email: r.user,
          is_guest: false, roles: r.roles || [] }
        this.booted = true
        await useAccessStore().load(true)
        return true
      } catch (e) {
        this.loginError = e.message || 'Đăng nhập thất bại'
        return false
      } finally {
        this.loginLoading = false
      }
    },
    async doLogout() {
      try { await apiLogout() } catch (e) {}
      this.user = { name: 'Guest', is_guest: true, roles: [] }
      useAccessStore().reset()
      this.booted = false
    },
    // Native-only logout: clear stored token, reset to Guest, no server session call.
    async mobileLogout() {
      await clearToken()
      this.user = { name: 'Guest', is_guest: true, roles: [] }
      useAccessStore().reset()
      this.booted = false
    },
  },
})
