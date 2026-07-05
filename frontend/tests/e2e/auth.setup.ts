import { mkdir } from "node:fs/promises";
import path from "node:path";

import { expect, test } from "@playwright/test";

type DemoRole = {
  key: "jobseeker" | "recruiter" | "admin";
  expectedRole: "JOB_SEEKER" | "RECRUITER" | "ADMIN";
  portalLabel: string;
  landingPath: string;
};

const authDir = path.join(process.cwd(), "tests", ".auth");
const authSetupTimeoutMs = Number(process.env.E2E_AUTH_SETUP_TIMEOUT_MS || 180_000);

const roles: DemoRole[] = [
  { key: "jobseeker", expectedRole: "JOB_SEEKER", portalLabel: "Job Seeker", landingPath: "/jobseeker/settings/profile" },
  { key: "recruiter", expectedRole: "RECRUITER", portalLabel: "Recruiter", landingPath: "/recruiter/settings/profile" },
  { key: "admin", expectedRole: "ADMIN", portalLabel: "Admin", landingPath: "/admin/dashboard" }
];

function credentialsFor(role: DemoRole) {
  const prefix = `E2E_${role.key.toUpperCase()}`;
  return {
    email: process.env[`${prefix}_EMAIL`] || "",
    password: process.env[`${prefix}_PASSWORD`] || ""
  };
}

function isPlaceholder(value: string) {
  return /^(replace_|your_|demo_|test_|password$)|example\.com$/i.test(value.trim());
}

function maskEmail(email: string) {
  const [name, domain] = email.split("@");
  if (!name || !domain) return "configured email";
  return `${name.slice(0, 2)}***@${domain}`;
}

test.describe.configure({ mode: "serial" });

for (const role of roles) {
  test.describe(`${role.key} storage state`, () => {
    const credentials = credentialsFor(role);
    const hasUsableCredentials = Boolean(credentials.email && credentials.password && !isPlaceholder(credentials.email) && !isPlaceholder(credentials.password));

    test.skip(!hasUsableCredentials, `Missing disposable ${role.key} demo credentials. Set E2E_${role.key.toUpperCase()}_EMAIL/PASSWORD to generate storage state.`);

    test(`create ${role.key} storage state`, async ({ page }) => {
      test.setTimeout(authSetupTimeoutMs + 30_000);
      await mkdir(authDir, { recursive: true });

      console.log(`[auth-setup] ${role.key}: using ${maskEmail(credentials.email)}. Passwords, tokens, and cookies are never printed.`);
      console.log(`[auth-setup] ${role.key}: if CAPTCHA or OTP appears, solve it in the opened browser. Waiting up to ${Math.round(authSetupTimeoutMs / 1000)}s.`);

      await page.goto("/login");
      await page.getByRole("button", { name: new RegExp(role.portalLabel, "i") }).click();
      await page.getByLabel(/^email$/i).fill(credentials.email);
      await page.getByLabel(/^password$/i).fill(credentials.password);

      const tokenReady = page.waitForFunction(() => {
        const token = window.localStorage.getItem("jobswipe_token");
        const user = window.localStorage.getItem("jobswipe_user");
        return Boolean(token && user);
      }, null, { timeout: authSetupTimeoutMs });

      await tokenReady;
      const storedRole = await page.evaluate(() => {
        const raw = window.localStorage.getItem("jobswipe_user");
        if (!raw) return "";
        try {
          return JSON.parse(raw).role || "";
        } catch {
          return "";
        }
      });

      expect(storedRole).toBe(role.expectedRole);
      await page.goto(role.landingPath);
      await expect(page.locator("body")).toBeVisible();

      const storagePath = path.join(authDir, `${role.key}.json`);
      await page.context().storageState({ path: storagePath });
      console.log(`[auth-setup] ${role.key}: storage state saved to tests/.auth/${role.key}.json`);
    });
  });
}
