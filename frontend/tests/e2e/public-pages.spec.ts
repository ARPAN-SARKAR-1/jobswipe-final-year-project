import { expect, test } from "@playwright/test";

import {
  expectHelpAssistantAvailable,
  expectNoCriticalDiagnostics,
  expectNoHorizontalOverflow,
  expectNoBannedPublicCopy,
  expectVisibleFormControlsHaveNames,
  expectVisibleButtonsHaveNames,
  expectVisibleImagesHaveAlt,
  gotoAppPage
} from "./helpers";

const publicRoutes = [
  { path: "/", title: /Swipe|Success|Apply/i },
  { path: "/login", title: /login|continue/i },
  { path: "/register", title: /join|create account/i },
  { path: "/forgot-password", title: /forgot|reset/i },
  { path: "/contact", title: /contact support|support/i },
  { path: "/terms", title: /terms/i },
  { path: "/privacy", title: /privacy/i }
];

test.describe("public page smoke", () => {
  for (const route of publicRoutes) {
    test(`${route.path} loads without public-copy regressions`, async ({ page }) => {
      const diagnostics = await gotoAppPage(page, route.path);
      await expect(page.locator("body")).toContainText(route.title);
      await expectHelpAssistantAvailable(page);
      await expectVisibleButtonsHaveNames(page);
      await expectVisibleImagesHaveAlt(page);
      await expectVisibleFormControlsHaveNames(page);
      await expectNoCriticalDiagnostics(diagnostics);
    });
  }

  test("homepage logo and favicon metadata are present", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByAltText("Swipe for Success").first()).toBeVisible();
    await expect(page.locator('link[rel~="icon"], link[rel="shortcut icon"], link[rel="apple-touch-icon"]').first()).toHaveCount(1);
  });

  test("unknown route shows custom not-found page", async ({ page }) => {
    await page.goto("/not-a-real-swipe-route");
    await expect(page.locator("body")).toContainText(/page not found|not found/i);
    await expectNoHorizontalOverflow(page);
    await expectNoBannedPublicCopy(page);
  });
});
