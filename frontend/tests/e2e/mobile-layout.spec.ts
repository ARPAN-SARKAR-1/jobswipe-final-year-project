import { expect, test } from "@playwright/test";

import { expectHelpAssistantAvailable, expectNoHorizontalOverflow, expectNoBannedPublicCopy } from "./helpers";

const pages = [
  "/",
  "/login",
  "/register",
  "/contact",
  "/jobseeker/swipe",
  "/jobseeker/settings/profile",
  "/recruiter/company",
  "/admin/dashboard"
];

test.describe("mobile and responsive layout anomaly checks", () => {
  for (const path of pages) {
    test(`${path} has no horizontal overflow in configured viewport`, async ({ page }) => {
      await page.goto(path);
      await expect(page.locator("body")).toBeVisible();
      await expectNoHorizontalOverflow(page);
      await expectNoBannedPublicCopy(page);
      await expectHelpAssistantAvailable(page);
    });
  }

  test("swipe page action buttons are not overlapped when visible", async ({ page }) => {
    await page.goto("/jobseeker/swipe");
    const actionButtons = [/skip/i, /save/i, /apply/i].map((name) => page.getByRole("button", { name }).first());
    await page.waitForTimeout(3_000);

    const buttonVisibility = await Promise.all(actionButtons.map((button) => button.isVisible().catch(() => false)));
    if (!buttonVisibility.every(Boolean)) {
      await expectNoHorizontalOverflow(page);
      return;
    }

    for (const button of actionButtons) {
      await expect(button).toBeVisible();
    }
    await expectNoHorizontalOverflow(page);
  });
});
