// frontend/capacitor.config.ts
import type { CapacitorConfig } from '@capacitor/cli'

const config: CapacitorConfig = {
  appId: 'vn.com.miyano.supplycore',
  appName: 'SupplyCore',
  // webDir trỏ tới native bundle do `npm run build:native` (CAP_BUILD=1) sinh ra dist/
  webDir: 'dist',
  server: { androidScheme: 'https' },
  plugins: {
    CapacitorHttp: { enabled: true }, // bỏ qua CORS browser cho request native
    SplashScreen: {
      launchShowDuration: 600,
      launchAutoHide: false,          // app tự ẩn sau khi mount (initNative)
      backgroundColor: '#1F4E79',
      androidSpinnerStyle: 'small',
      spinnerColor: '#FFFFFF',
    },
    StatusBar: { style: 'DARK', backgroundColor: '#1F4E79' },
    Keyboard: { resize: 'native' },
  },
}

export default config
