import { defineConfig, devices } from "@playwright/test";

const baseURL = process.env.E2E_BASE_URL?.trim() || "http://127.0.0.1:3000";
const startLocalServer = !process.env.E2E_BASE_URL;

export default defineConfig({
  testDir: "./tests/e2e",
  testMatch: /auth\.setup\.ts/,
  timeout: Number(process.env.E2E_AUTH_SETUP_TIMEOUT_MS || 180_000) + 30_000,
  workers: 1,
  reporter: [["list"]],
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
  projects: [{ name: "setup-auth", use: { ...devices["Desktop Chrome"] } }]
});
