import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  test: {
    environment: 'node',            // mặc định; test .vue tự khai báo happy-dom qua comment
    include: ['tests/**/*.spec.js'],
  },
})
