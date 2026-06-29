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
  },
}

export default config
