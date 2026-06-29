import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { clickOutside } from './directives/clickOutside'
import './assets/main.css'
import './mobile/mobile.css'
import { registerPwa } from './pwa'
import { isNative } from './platform'
import { initNative } from './mobile/native'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.directive('click-outside', clickOutside)
app.mount('#app')
// PWA service worker chỉ cho web. Trên native (Capacitor) KHÔNG đăng ký SW:
// SW build theo base web /supplycore → precache URL sai (404) + can thiệp WebView.
if (!isNative()) registerPwa()
else initNative()   // StatusBar navy + ẩn splash + keyboard (no-op nếu lỗi plugin)
