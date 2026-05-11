import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from './pages/Dashboard.vue'
import AlertCenter from './pages/AlertCenter.vue'
import ModuleHub from './pages/ModuleHub.vue'
import NotFound from './pages/NotFound.vue'

const router = createRouter({
  history: createWebHistory('/supplycore/'),
  routes: [
    { path: '/',             name: 'home',       component: Dashboard,    meta: { title: 'Dashboard' } },
    { path: '/dashboard',    name: 'dashboard',  component: Dashboard,    meta: { title: 'Dashboard' } },
    { path: '/alerts',       name: 'alerts',     component: AlertCenter,  meta: { title: 'Alert Center' } },
    // 11 modules — same component, param-driven
    { path: '/m:n(\\d+)',    name: 'module',     component: ModuleHub,    meta: { title: 'Module' } },
    { path: '/:catch(.*)*',  name: 'notfound',   component: NotFound },
  ],
})

router.afterEach((to) => {
  document.title = `${to.meta?.title || 'SupplyCore'} — SupplyCore`
})

export default router
