import { expect, test } from "@playwright/test";

import { annotateSkippedProtectedTest, expectNoHorizontalOverflow, storageStateFor } from "./helpers";

const adminStorageState = storageStateFor("admin");

test("admin protected route redirects safely without auth", async ({ page }) => {
  await page.goto("/admin/dashboard");
  await expect(page.locator("body")).toContainText(/login|continue|admin/i);
  await expectNoHorizontalOverflow(page);
});

test.describe("authenticated admin read-only flow", () => {
  test.skip(!adminStorageState, "Set E2E_ADMIN_STORAGE_STATE to run authenticated admin tests without automating CAPTCHA/OTP.");
  test.use({ storageState: adminStorageState || undefined });

  test("admin dashboard loads searchable management UI without mobile overflow", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/admin/dashboard");
    await expect(page.locator("body")).toContainText(/dashboard|users|support|verification/i);
    await expectNoHorizontalOverflow(page);
  });

  test("support ticket controls are visible but not mutated", async ({ page }) => {
    await page.goto("/admin/dashboard");
    await expect(page.locator("body")).toContainText(/support ticket|support/i);
    await expectNoHorizontalOverflow(page);
  });
});

test("admin destructive moderation actions remain manual unless demo data is provided", async ({}, testInfo) => {
  await annotateSkippedProtectedTest(testInfo, "admin");
});
