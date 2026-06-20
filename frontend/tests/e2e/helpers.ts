import { expect, type Page, type Request, type TestInfo } from "@playwright/test";

export type Diagnostics = {
  consoleErrors: string[];
  pageErrors: string[];
  failedRequests: string[];
};

const bannedPublicCopy = [
  /final year project/i,
  /final-year project/i,
  /full-stack project/i,
  /academic project/i,
  /student project/i,
  /demo project/i,
  /project demo/i,
  /generate reset token/i,
  /future scope/i
];

const allowedFailedRequestPatterns = [
  /chrome-extension:\/\//i,
  /\/favicon\.(ico|png)$/i,
  /\/_next\/static\//i,
  /\/api\/auth\/captcha/i
];

export function backendConfigured() {
  return Boolean(process.env.E2E_BACKEND_URL || process.env.NEXT_PUBLIC_API_BASE_URL);
}

export function storageStateFor(role: "jobseeker" | "recruiter" | "admin") {
  const key = `E2E_${role.toUpperCase()}_STORAGE_STATE`;
  return process.env[key] || "";
}

export function credentialsFor(role: "jobseeker" | "recruiter" | "admin") {
  const prefix = `E2E_${role.toUpperCase()}`;
  return {
    email: process.env[`${prefix}_EMAIL`] || "",
    password: process.env[`${prefix}_PASSWORD`] || ""
  };
}

export function hasCredentials(role: "jobseeker" | "recruiter" | "admin") {
  const credentials = credentialsFor(role);
  return Boolean(credentials.email && credentials.password);
}

export function attachDiagnostics(page: Page): Diagnostics {
  const diagnostics: Diagnostics = { consoleErrors: [], pageErrors: [], failedRequests: [] };
  page.on("console", (message) => {
    if (message.type() === "error" && !/CAPTCHA challenge fetch failed/i.test(message.text())) {
      diagnostics.consoleErrors.push(message.text());
    }
  });
  page.on("pageerror", (error) => diagnostics.pageErrors.push(error.message));
  page.on("requestfailed", (request) => {
    if (!isAllowedFailedRequest(request)) {
      diagnostics.failedRequests.push(`${request.method()} ${request.url()} ${request.failure()?.errorText || "failed"}`);
    }
  });
  return diagnostics;
}

function isAllowedFailedRequest(request: Request) {
  const url = request.url();
  return allowedFailedRequestPatterns.some((pattern) => pattern.test(url));
}

export async function expectNoCriticalDiagnostics(diagnostics: Diagnostics) {
  expect(diagnostics.pageErrors, "page errors").toEqual([]);
  expect(diagnostics.consoleErrors, "console errors").toEqual([]);
  expect(diagnostics.failedRequests, "failed network requests").toEqual([]);
}

export async function expectNoHorizontalOverflow(page: Page) {
  const result = await page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    innerWidth: window.innerWidth
  }));
  expect(result.scrollWidth, `scrollWidth ${result.scrollWidth} should fit viewport ${result.innerWidth}`).toBeLessThanOrEqual(result.innerWidth + 2);
}

export async function expectNoBannedPublicCopy(page: Page) {
  const visibleText = await page.locator("body").innerText();
  for (const pattern of bannedPublicCopy) {
    expect(visibleText, `public copy should not match ${pattern}`).not.toMatch(pattern);
  }
}

export async function expectHelpAssistantAvailable(page: Page) {
  await expect(page.getByRole("button", { name: /open help assistant/i })).toBeVisible();
}

export async function expectVisibleButtonsHaveNames(page: Page) {
  const buttons = page.locator("button:visible");
  const count = await buttons.count();
  for (let index = 0; index < count; index += 1) {
    const button = buttons.nth(index);
    const name = (await button.getAttribute("aria-label")) || (await button.innerText()).trim() || (await button.getAttribute("title")) || "";
    expect(name, `button ${index + 1} should have an accessible name`).not.toEqual("");
  }
}

export async function expectVisibleImagesHaveAlt(page: Page) {
  const images = page.locator("img:visible");
  const count = await images.count();
  for (let index = 0; index < count; index += 1) {
    const image = images.nth(index);
    const alt = await image.getAttribute("alt");
    expect(alt, `visible image ${index + 1} should define alt text, even if decorative`).not.toBeNull();
  }
}

export async function expectVisibleFormControlsHaveNames(page: Page) {
  const controls = page.locator('input:not([type="hidden"]):not([type="checkbox"]):not([type="radio"]):not([type="file"]):visible, textarea:visible, select:visible');
  const count = await controls.count();
  for (let index = 0; index < count; index += 1) {
    const control = controls.nth(index);
    const id = await control.getAttribute("id");
    const accessibleHint =
      (await control.getAttribute("aria-label")) ||
      (await control.getAttribute("placeholder")) ||
      (id ? await page.locator(`label[for="${id}"]`).first().textContent().catch(() => "") : "");
    expect((accessibleHint || "").trim(), `form control ${index + 1} should have label, aria-label, or placeholder`).not.toEqual("");
  }
}

export async function gotoAppPage(page: Page, path: string) {
  const diagnostics = attachDiagnostics(page);
  await page.goto(path);
  await expect(page.locator("body")).toBeVisible();
  await expectNoHorizontalOverflow(page);
  await expectNoBannedPublicCopy(page);
  return diagnostics;
}

export async function annotateSkippedProtectedTest(testInfo: TestInfo, role: "jobseeker" | "recruiter" | "admin") {
  const credentials = hasCredentials(role) ? "credentials provided" : "credentials missing";
  const storage = storageStateFor(role) ? "storage state provided" : "storage state missing";
  testInfo.annotations.push({
    type: "manual",
    description: `Protected ${role} workflow requires solved CAPTCHA/OTP or saved storage state; ${credentials}, ${storage}.`
  });
}
