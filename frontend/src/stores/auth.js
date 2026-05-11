import { defineStore } from 'pinia'
import { login as apiLogin, logout as apiLogout, getSession, getUserInfo } from '../api'

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
        this.user = { name: 'Guest', is_guest: true, roles: [] }
      } else {
        const info = await getUserInfo(sess)
        this.user = {
          name: sess,
          full_name: info?.full_name || sess,
          email: sess,
          user_image: info?.user_image,
          is_guest: false,
          roles: window.sc_session_user?.roles || [],
        }
      }
      this.booted = true
    },
    async doLogin(usr, pwd) {
      this.loginError = null
      this.loginLoading = true
      try {
        await apiLogin(usr, pwd)
        await this.boot()
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
      this.booted = false
    },
  },
})
