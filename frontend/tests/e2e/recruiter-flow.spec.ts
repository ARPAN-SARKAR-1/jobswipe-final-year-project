import { expect, test } from "@playwright/test";

import { annotateSkippedProtectedTest, expectNoHorizontalOverflow, storageStateFor } from "./helpers";

const recruiterStorageState = storageStateFor("recruiter");

test("recruiter protected routes redirect safely without auth", async ({ page }) => {
  await page.goto("/recruiter/company");
  await expect(page.locator("body")).toContainText(/login|continue|recruiter/i);
  await expectNoHorizontalOverflow(page);
  await page.goto("/recruiter/swipe");
  await expect(page.locator("body")).toContainText(/login|continue|recruiter/i);
  await expectNoHorizontalOverflow(page);
});

test.describe("authenticated recruiter flow", () => {
  test.skip(!recruiterStorageState, "Set E2E_RECRUITER_STORAGE_STATE to run authenticated recruiter tests without automating CAPTCHA/OTP.");
  test.use({ storageState: recruiterStorageState || undefined });

  test("company profile marks posting requirements clearly", async ({ page }) => {
    await page.goto("/recruiter/company");
    await expect(page.locator("body")).toContainText(/fields marked with \*/i);
    await expect(page.locator("body")).toContainText(/compulsory before posting jobs/i);
    await expect(page.locator("body")).toContainText(/official career links help applicants verify job authenticity/i);
    await expect(page.getByText(/company logo/i)).toBeVisible();
    await expectNoHorizontalOverflow(page);
  });

  test("job posting form requires career URL and core fields", async ({ page }) => {
    await page.goto("/recruiter/jobs/new");
    await expect(page.locator("body")).toContainText(/fields marked with \*/i);
    await expect(page.getByLabel(/official career page url/i)).toBeVisible();
    await expect(page.getByLabel(/job title/i)).toBeVisible();
    await expect(page.locator("body")).toContainText(/screening questions/i);
    await expect(page.getByRole("button", { name: /post job/i })).toBeVisible();
    await expectNoHorizontalOverflow(page);
  });

  test("applications filters stay mobile-safe", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/recruiter/applications");
    await expectNoHorizontalOverflow(page);
    await expect(page.locator("body")).toContainText(/application|filter|search|status/i);
  });

  test("candidate swipe page keeps review controls visible", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/recruiter/swipe");
    await expect(page.locator("body")).toContainText(/swipe right to shortlist|no candidates available|shortlist|screening answers/i);
    await expectNoHorizontalOverflow(page);
  });
});

test("recruiter write workflows remain manual unless auth state is supplied", async ({}, testInfo) => {
  await annotateSkippedProtectedTest(testInfo, "recruiter");
});
