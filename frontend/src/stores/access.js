// Access matrix — fetched once at boot, used by router/sidebar/pages
// "Không có phận sự thì không thấy" — ẩn menu, gate route, ẩn nút action.

import { defineStore } from 'pinia'
import { call } from '../api'
import { resolvePersona, getPersona } from '../personas'

const EMPTY = {
  user: null,
  roles: [],
  is_admin: 0,
  modules: {},      // {m0: true, m1: false, ...}
  features: {},     // {data_io: true, users: false, ...}
  doctypes: {},     // {'SC Item': {read:1, write:1, create:1, submit:0, ...}}
}

const PERSONA_KEY = 'sc-persona-override'

export const useAccessStore = defineStore('access', {
  state: () => ({
    ...EMPTY,
    loaded: false,
    loading: false,
    // Admin can override the auto-detected persona for QA preview.
    // Persists in sessionStorage; cleared at logout (reset()).
    personaOverride: typeof sessionStorage !== 'undefined'
      ? sessionStorage.getItem(PERSONA_KEY) : null,
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
    // Auto-detected persona based on Frappe roles (no override).
    detectedPersonaId: (s) => resolvePersona(s.roles || []),
    // Effective persona id — override wins if admin set one.
    activePersonaId: (s) => {
      if (s.personaOverride && s.is_admin) return s.personaOverride
      return resolvePersona(s.roles || [])
    },
    activePersona() { return getPersona(this.activePersonaId) },
    // Detect: is the user impersonating via persona switcher right now?
    isImpersonating: (s) => !!s.personaOverride && s.is_admin
      && s.personaOverride !== resolvePersona(s.roles || []),
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
    setPersonaOverride(pid) {
      // Only admins may impersonate. Silent no-op otherwise.
      if (!this.is_admin) return
      if (!pid) {
        this.personaOverride = null
        if (typeof sessionStorage !== 'undefined') sessionStorage.removeItem(PERSONA_KEY)
        return
      }
      this.personaOverride = pid
      if (typeof sessionStorage !== 'undefined') sessionStorage.setItem(PERSONA_KEY, pid)
    },
    reset() {
      Object.assign(this, EMPTY)
      this.loaded = false
      this.personaOverride = null
      if (typeof sessionStorage !== 'undefined') sessionStorage.removeItem(PERSONA_KEY)
    },
  },
})
