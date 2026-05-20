// Access matrix — fetched once at boot, used by router/sidebar/pages
// "Không có phận sự thì không thấy" — ẩn menu, gate route, ẩn nút action.

import { defineStore } from 'pinia'
import { call } from '../api'

const EMPTY = {
  user: null,
  roles: [],
  is_admin: 0,
  modules: {},      // {m0: true, m1: false, ...}
  features: {},     // {data_io: true, users: false, ...}
  doctypes: {},     // {'SC Item': {read:1, write:1, create:1, submit:0, ...}}
}

export const useAccessStore = defineStore('access', {
  state: () => ({
    ...EMPTY,
    loaded: false,
    loading: false,
  }),
  getters: {
    // Module có hiển thị không (sidebar)
    canModule: (s) => (mId) => !!s.modules?.[mId],
    // Feature flag (sidebar item & route gate)
    canFeature: (s) => (key) => !!s.features?.[key],
    // Doctype perm — perm ∈ read/write/create/submit/cancel/delete
    canDoctype: (s) => (dt, perm = 'read') => !!(s.doctypes?.[dt]?.[perm]),
    // Render badge "Bạn không có quyền" cho doctype lạ
    hasAnyPerm: (s) => (dt) => !!(s.doctypes?.[dt]?.read || s.doctypes?.[dt]?.write
                                    || s.doctypes?.[dt]?.create),
  },
  actions: {
    async load(force = false) {
      if (this.loaded && !force) return
      if (this.loading) return
      this.loading = true
      try {
        const data = await call('supplycore.api.access.menu')
        this.user = data.user
        this.roles = data.roles || []
        this.is_admin = data.is_admin || 0
        this.modules = data.modules || {}
        this.features = data.features || {}
        this.doctypes = data.doctypes || {}
        this.loaded = true
      } catch (e) {
        // Guest hoặc lỗi mạng → để mọi flag false (FE sẽ chỉ thấy Dashboard fallback)
        Object.assign(this, EMPTY)
        this.loaded = true
      } finally {
        this.loading = false
      }
    },
    reset() {
      Object.assign(this, EMPTY)
      this.loaded = false
    },
  },
})
