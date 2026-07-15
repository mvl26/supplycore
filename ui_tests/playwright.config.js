// @ts-check
const { defineConfig, devices } = require('@playwright/test');
const { BASE_URL } = require('./config');

module.exports = defineConfig({
  testDir: './specs',
  outputDir: './artifacts',
  fullyParallel: false,          // các spec chia sẻ site → chạy tuần tự cho ổn định
  workers: 1,
  retries: process.env.CI ? 1 : 0,
  reporter: [['list'], ['html', { outputFolder: 'report', open: 'never' }]],
  timeout: 60_000,
  expect: { timeout: 15_000 },
  globalSetup: require.resolve('./global-setup.js'),
  use: {
    baseURL: BASE_URL,
    headless: true,
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
    video: 'retain-on-failure',
    actionTimeout: 15_000,
    navigationTimeout: 30_000,
    ignoreHTTPSErrors: true,
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
});
