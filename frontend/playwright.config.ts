import { defineConfig, devices } from "@playwright/test";

const baseURL = process.env.E2E_BASE_URL?.trim() || "http://127.0.0.1:3000";
const startLocalServer = !process.env.E2E_BASE_URL;

export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 45_000,
  expect: {
    timeout: 8_000
  },
  fullyParallel: true,
  retries: process.env.CI ? 1 : 0,
  reporter: [
    ["list"],
    ["html", { open: "never", outputFolder: "playwright-report" }]
  ],
  use: {
    baseURL,
    actionTimeout: 10_000,
    navigationTimeout: 30_000,
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
    video: "retain-on-failure"
  },
  webServer: startLocalServer
    ? {
        command: "node ./node_modules/next/dist/bin/next dev --hostname 127.0.0.1 --port 3000",
        url: baseURL,
        reuseExistingServer: true,
        timeout: 120_000,
        gracefulShutdown: { signal: "SIGINT", timeout: 1_000 }
      }
    : undefined,
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
    {
      name: "mobile-chrome-360",
      use: { browserName: "chromium", hasTouch: true, isMobile: true, viewport: { width: 360, height: 740 } }
    },
    {
      name: "mobile-chrome-375",
      use: { browserName: "chromium", hasTouch: true, isMobile: true, viewport: { width: 375, height: 812 } }
    },
    {
      name: "mobile-chrome-390",
      use: { browserName: "chromium", hasTouch: true, isMobile: true, viewport: { width: 390, height: 844 } }
    },
    {
      name: "mobile-chrome-430",
      use: { browserName: "chromium", hasTouch: true, isMobile: true, viewport: { width: 430, height: 932 } }
    },
    {
      name: "tablet-768",
      use: { browserName: "chromium", hasTouch: true, isMobile: false, viewport: { width: 768, height: 1024 } }
    },
    {
      name: "desktop-1366",
      use: { ...devices["Desktop Chrome"], viewport: { width: 1366, height: 768 } }
    }
  ]
});
