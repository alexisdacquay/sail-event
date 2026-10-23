import { test, expect, Page } from "@playwright/test";

function uid() {
  return `e2e_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}

const CRITERIA = "jazz in Berlin (Germany) next week (19-21st October 2026)";

async function register(page: Page, user: string, pw: string) {
  await page.goto("/");
  await expect(page.getByTestId("pitch")).toBeVisible();
  await page.getByRole("button", { name: "Create one" }).click();
  await page.getByLabel("Username").fill(user);
  await page.getByLabel("Password").fill(pw);
  await page.getByRole("button", { name: "Create account" }).click();
  await expect(page.getByRole("heading", { name: "Sail Event" })).toBeVisible();
}

test.describe("Issue 122 screenshots", () => {
  for (const colorScheme of ["light", "dark"] as const) {
    test(`live line mid-run ${colorScheme}`, async ({ browser }) => {
      const ctx = await browser.newContext({ colorScheme, viewport: { width: 1280, height: 900 } });
      const page = await ctx.newPage();
      const user = uid();
      await register(page, user, "testpass1");
      const box = page.getByLabel("What I'm looking for");
      await box.fill(CRITERIA);
      await box.press("Enter");
      await expect(page.getByText("Saved.")).toBeVisible({ timeout: 15_000 });
      // Start search and capture the live line before it finishes
      await page.getByRole("button", { name: /Search (now|again)/ }).click();
      // Wait for the chronology to show a live line with the hairline
      await expect(page.getByTestId("search-progress")).toBeVisible({ timeout: 15_000 });
      // Small wait to let the progress bar render a non-zero fraction
      await page.waitForTimeout(500);
      const tl = page.getByTestId("run-chronology");
      await tl.screenshot({ path: `test-results/122-live-line-${colorScheme}.png` });
      // Wait for search to finish, then capture the funnel
      await expect(page.getByTestId("run-chronology")).toContainText(/Judged \d+ ·/, { timeout: 15_000 });
      await page.getByTestId("funnel").screenshot({ path: `test-results/122-funnel-${colorScheme}.png` });
      await ctx.close();
    });
  }
});
