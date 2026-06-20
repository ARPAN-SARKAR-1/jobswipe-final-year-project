import { expect, test } from "@playwright/test";

import { backendConfigured, expectNoHorizontalOverflow, expectNoBannedPublicCopy } from "./helpers";

test.describe("auth UI regression checks", () => {
  test("login has portal selection, password toggle, and clean helper text", async ({ page }) => {
    await page.goto("/login");
    await expect(page.getByRole("button", { name: /job seeker/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /recruiter/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /admin/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /owner/i })).toBeVisible();
    await expect(page.getByLabel(/^password$/i)).toHaveAttribute("type", "password");
    await page.getByRole("button", { name: /show password/i }).click();
    await expect(page.getByLabel(/^password$/i)).toHaveAttribute("type", "text");
    await expect(page.locator("body")).toContainText(/correct portal|portal/i);
    await expectNoHorizontalOverflow(page);
    await expectNoBannedPublicCopy(page);
  });

  test("CAPTCHA renders as an image when backend is configured", async ({ page }) => {
    test.skip(!backendConfigured(), "Set E2E_BACKEND_URL or NEXT_PUBLIC_API_BASE_URL to verify live CAPTCHA image loading.");
    await page.goto("/login");
    await expect(page.getByAltText("Security check image")).toBeVisible();
    await expect(page.locator("body")).not.toContainText(/what is \d+/i);
  });

  test("register has only public account types and password toggles", async ({ page }) => {
    await page.goto("/register");
    await expect(page.getByRole("button", { name: /join as job seeker/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /join as recruiter/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /join as admin/i })).toHaveCount(0);
    await expect(page.getByRole("button", { name: /join as owner/i })).toHaveCount(0);
    await expect(page.getByLabel(/^password$/i)).toHaveAttribute("type", "password");
    await page.getByRole("button", { name: /show password/i }).first().click();
    await expect(page.getByLabel(/^password$/i)).toHaveAttribute("type", "text");
    await expectNoHorizontalOverflow(page);
  });

  test("forgot password uses reset-link wording", async ({ page }) => {
    await page.goto("/forgot-password");
    await expect(page.getByRole("button", { name: /send reset link/i })).toBeVisible();
    await expect(page.locator("body")).not.toContainText(/generate reset token|token generated/i);
  });
});
