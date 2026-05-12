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
import { useAuthStore } from './stores/auth'

const router = createRouter({
  history: createWebHistory('/supplycore/'),
  routes: [
    { path: '/login',  name: 'login', component: Login, meta: { public: true, layout: 'blank', title: 'Đăng nhập' } },
    { path: '/',       name: 'home', component: Dashboard, meta: { title: 'Dashboard' } },
    { path: '/dashboard', name: 'dashboard', component: Dashboard, meta: { title: 'Dashboard' } },
    { path: '/alerts', name: 'alerts', component: AlertCenter, meta: { title: 'Alert Center' } },

    { path: '/m:n(\\d+)', name: 'module', component: ModuleHub, meta: { title: 'Module' } },
    { path: '/stock-balance', name: 'stockBalance', component: StockBalance, meta: { title: 'Tồn kho' } },

    { path: '/warehouses', name: 'warehouseList', component: WarehouseList, meta: { title: 'Kho' } },
    { path: '/putaway', name: 'putaway', component: Putaway, meta: { title: 'Phiếu xếp hàng' } },
    { path: '/list/:dt', name: 'docList', component: DocList, meta: { title: 'Danh sách' } },
    { path: '/doc/:dt/:name', name: 'docView', component: DocView, meta: { title: 'Chi tiết' } },

    { path: '/:catch(.*)*', name: 'notfound', component: NotFound, meta: { title: '404' } },
  ],
})

router.beforeEach((to, from, next) => {
  const auth = useAuthStore()
  if (to.meta.public) return next()
  if (auth.isGuest) {
    if (to.path !== '/login') {
      return next({ path: '/login', query: { redirect: to.fullPath } })
    }
  }
  next()
})

router.afterEach((to) => {
  document.title = `${to.meta?.title || 'SupplyCore'} — SupplyCore`
})

export default router
