import { expect, test } from "@playwright/test";

import { backendConfigured, expectNoHorizontalOverflow } from "./helpers";

test.describe("contact and support ticket UI", () => {
  test("contact form exposes required fields and support email fallback", async ({ page }) => {
    await page.goto("/contact");
    await expect(page.getByRole("heading", { name: /contact support/i })).toBeVisible();
    await expect(page.getByRole("link", { name: /support/i })).toHaveAttribute("href", /mailto:/);
    await expect(page.getByLabel(/name/i)).toBeVisible();
    await expect(page.getByLabel(/email/i)).toBeVisible();
    await expect(page.getByLabel(/category/i)).toBeVisible();
    const priority = page.getByLabel(/priority/i);
    if (await priority.count()) {
      await expect(priority).toBeVisible();
    } else {
      await expect(page.locator("body")).toContainText(/priority.*automatic|automatic.*priority/i);
    }
    await expect(page.getByLabel(/subject/i)).toBeVisible();
    await expect(page.getByLabel(/message/i)).toBeVisible();
    await expect(page.getByRole("button", { name: /submit ticket/i })).toBeVisible();
    await expectNoHorizontalOverflow(page);
  });

  test("contact CAPTCHA renders as image when backend is configured", async ({ page }) => {
    test.skip(!backendConfigured(), "Set E2E_BACKEND_URL or NEXT_PUBLIC_API_BASE_URL to verify contact CAPTCHA.");
    await page.goto("/contact");
    await expect(page.getByAltText("Security check image")).toBeVisible();
  });

  test("empty submit uses browser validation instead of crashing", async ({ page }) => {
    await page.goto("/contact");
    await page.getByRole("button", { name: /submit ticket/i }).click();
    const invalidCount = await page.locator("input:invalid, textarea:invalid").count();
    expect(invalidCount).toBeGreaterThan(0);
  });

  test("ticket code format is documented for manual CAPTCHA completion", async ({ page }) => {
    await page.goto("/contact");
    await expect(page.locator("body")).toContainText(/ticket/i);
    test.info().annotations.push({
      type: "manual",
      description: "Correct CAPTCHA answer is intentionally not exposed; complete ticket creation manually and verify SFS-TKT-YYYYMMDD-XXXX."
    });
  });
});
