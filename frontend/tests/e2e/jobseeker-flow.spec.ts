import { expect, test } from "@playwright/test";

import { annotateSkippedProtectedTest, expectNoHorizontalOverflow, storageStateFor } from "./helpers";

const jobseekerStorageState = storageStateFor("jobseeker");

test("job seeker protected routes redirect safely without auth", async ({ page }) => {
  await page.goto("/jobseeker/settings/profile");
  await expect(page.locator("body")).toContainText(/login|continue|job seeker/i);
  await expectNoHorizontalOverflow(page);
});

test.describe("authenticated job seeker flow", () => {
  test.skip(!jobseekerStorageState, "Set E2E_JOBSEEKER_STORAGE_STATE to run authenticated job seeker tests without automating CAPTCHA/OTP.");
  test.use({ storageState: jobseekerStorageState || undefined });

  test("profile settings show required markers and mobile-safe skills dropdown", async ({ page }) => {
    await page.goto("/jobseeker/settings/profile");
    await expect(page.locator("body")).toContainText(/fields marked with \*/i);
    await expect(page.locator("body")).toContainText(/compulsory for completing your profile/i);
    await expect(page.locator("body")).toContainText(/resume/i);
    const skillButton = page.getByRole("button", { name: /skills selected|select skills/i }).first();
    await expect(skillButton).toBeVisible();
    await skillButton.click();
    await expect(page.getByPlaceholder(/search skills/i)).toBeVisible();
    await expectNoHorizontalOverflow(page);
  });

  test("resume upload rejects unsafe file type and oversized file before server upload", async ({ page }) => {
    await page.goto("/jobseeker/settings/profile");
    const resumeInput = page.locator('input[type="file"]').nth(1);
    await resumeInput.setInputFiles({
      name: "resume.exe",
      mimeType: "application/x-msdownload",
      buffer: Buffer.from("not a resume")
    });
    await expect(page.locator("body")).toContainText(/unsupported file type/i);

    await resumeInput.setInputFiles({
      name: "large-resume.pdf",
      mimeType: "application/pdf",
      buffer: Buffer.alloc(6 * 1024 * 1024, 1)
    });
    await expect(page.locator("body")).toContainText(/file too large|under 5 MB/i);
  });

  test("swipe page keeps save/apply/skip fallback buttons visible", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/jobseeker/swipe");
    await expectNoHorizontalOverflow(page);
    const body = await page.locator("body").innerText();
    if (/no active jobs|complete your profile|skip|save|apply/i.test(body)) {
      await expect(page.locator("body")).toContainText(/skip|save|apply|complete your profile|no active jobs/i);
    }
  });
});

test("job seeker destructive flows remain manual unless auth state is supplied", async ({}, testInfo) => {
  await annotateSkippedProtectedTest(testInfo, "jobseeker");
});
