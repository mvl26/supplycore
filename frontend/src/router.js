import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from './pages/Dashboard.vue'
import AlertCenter from './pages/AlertCenter.vue'
import ModuleHub from './pages/ModuleHub.vue'
import DocList from './pages/DocList.vue'
import DocView from './pages/DocView.vue'
import Login from './pages/Login.vue'
import NotFound from './pages/NotFound.vue'
import StockBalance from './pages/StockBalance.vue'
import WarehouseList from './pages/WarehouseList.vue'
import Putaway from './pages/Putaway.vue'
import Users from './pages/Users.vue'
import FinancialReports from './pages/FinancialReports.vue'
import BatchTrace from './pages/BatchTrace.vue'
import WarehouseMapPage from './pages/WarehouseMapPage.vue'
import Forbidden from './pages/Forbidden.vue'
import { useAuthStore } from './stores/auth'
import { useAccessStore } from './stores/access'

const router = createRouter({
  history: createWebHistory('/supplycore/'),
  routes: [
    { path: '/login',  name: 'login', component: Login, meta: { public: true, layout: 'blank', title: 'Đăng nhập' } },
    { path: '/',       name: 'home', component: Dashboard, meta: { title: 'Dashboard' } },
    { path: '/dashboard', name: 'dashboard', component: Dashboard, meta: { title: 'Dashboard' } },
    { path: '/alerts', name: 'alerts', component: AlertCenter, meta: { title: 'Alert Center', requireFeature: 'alerts' } },

    { path: '/m:n(\\d+)', name: 'module', component: ModuleHub, meta: { title: 'Module', requireModule: true } },
    { path: '/stock-balance', name: 'stockBalance', component: StockBalance, meta: { title: 'Tồn kho', requireFeature: 'stock_balance' } },

    { path: '/warehouses', name: 'warehouseList', component: WarehouseList, meta: { title: 'Kho', requireFeature: 'warehouses' } },
    { path: '/putaway', name: 'putaway', component: Putaway, meta: { title: 'Phiếu xếp hàng', requireFeature: 'putaway' } },
    { path: '/list/:dt', name: 'docList', component: DocList, meta: { title: 'Danh sách', requireDoctype: true } },
    { path: '/doc/:dt/:name', name: 'docView', component: DocView, meta: { title: 'Chi tiết', requireDoctype: true } },
    { path: '/users', name: 'users', component: Users, meta: { title: 'Người dùng & Phân quyền', requireFeature: 'users' } },
    { path: '/financial-reports', name: 'financialReports', component: FinancialReports, meta: { title: 'Báo cáo Tài chính', requireFeature: 'financial_reports' } },
    { path: '/batch-trace', name: 'batchTrace', component: BatchTrace, meta: { title: 'Truy xuất lô', requireFeature: 'batch_trace' } },
    { path: '/warehouse-map', name: 'warehouseMap', component: WarehouseMapPage, meta: { title: 'Bản đồ kho', requireFeature: 'warehouse_map' } },
    { path: '/403', name: 'forbidden', component: Forbidden, meta: { title: 'Không có quyền' } },

    { path: '/:catch(.*)*', name: 'notfound', component: NotFound, meta: { title: '404' } },
  ],
})

router.beforeEach(async (to, from, next) => {
  const auth = useAuthStore()
  if (to.meta.public) return next()
  if (auth.isGuest) {
    if (to.path !== '/login') {
      return next({ path: '/login', query: { redirect: to.fullPath } })
    }
    return next()
  }

  // Access store load lần đầu (auth.boot đã load nhưng phòng race)
  const access = useAccessStore()
  if (!access.loaded) {
    try { await access.load() } catch (e) {}
  }

  // Allow Forbidden / Dashboard / Login
  if (to.name === 'forbidden' || to.name === 'dashboard' || to.name === 'home') {
    return next()
  }

  // Feature flag check
  if (to.meta.requireFeature && !access.canFeature(to.meta.requireFeature)) {
    return next({ name: 'forbidden', query: {
      from: to.fullPath,
      r: `Tính năng "${to.meta.title}" không nằm trong phạm vi quyền của bạn`,
    }})
  }

  // Module check qua URL :n
  if (to.meta.requireModule) {
    const mid = `m${to.params.n}`
    if (!access.canModule(mid)) {
      return next({ name: 'forbidden', query: {
        from: to.fullPath,
        r: `Module ${mid.toUpperCase()} không nằm trong phạm vi quyền của bạn`,
      }})
    }
  }

  // Doctype check
  if (to.meta.requireDoctype) {
    const dt = decodeURIComponent(to.params.dt || '')
    // Nếu doctype không nằm trong tracked list → cho qua (Frappe REST sẽ tự reject)
    if (dt && access.doctypes[dt] !== undefined && !access.canDoctype(dt, 'read')) {
      return next({ name: 'forbidden', query: {
        from: to.fullPath,
        r: `Bạn không có quyền đọc DocType "${dt}"`,
      }})
    }
  }

  next()
})

router.afterEach((to) => {
  document.title = `${to.meta?.title || 'SupplyCore'} — SupplyCore`
})

export default router
