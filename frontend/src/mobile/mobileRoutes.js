// frontend/src/mobile/mobileRoutes.js
export const mobileRoutes = [
  {
    path: '/m/setup',
    name: 'mSetup',
    component: () => import('./ServerLogin.vue'),
    meta: { public: true, mobile: true, layout: 'mobile-blank' },
  },
  {
    path: '/m',
    component: () => import('./MobileShell.vue'),
    meta: { mobile: true },
    children: [
      { path: '', redirect: '/m/lookup' },
      {
        path: 'lookup',
        name: 'mLookup',
        component: () => import('./screens/StockLookup.vue'),
        meta: { mobile: true, title: 'Tra cứu' },
      },
      {
        path: 'approve',
        name: 'mApprove',
        component: () => import('./screens/ApproveDocs.vue'),
        meta: { mobile: true, title: 'Duyệt phiếu' },
      },
      {
        path: 'receiving',
        name: 'mReceiving',
        component: () => import('./screens/Receiving.vue'),
        meta: { mobile: true, title: 'Tiếp nhận' },
      },
      {
        path: 'dashboard',
        name: 'mDashboard',
        component: () => import('./screens/MobileDashboard.vue'),
        meta: { mobile: true, title: 'Bảng tin' },
      },
    ],
  },
]
