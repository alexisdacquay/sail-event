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

// The criteria text is edited in place: type, Enter saves.
async function saveCriteria(page: Page) {
  const box = page.getByLabel("What I'm looking for");
  await expect(page.getByTestId("criteria-hint")).toBeVisible();
  await box.fill(CRITERIA);
  await box.press("Enter");
  await expect(page.getByText("Saved.")).toBeVisible();
  await expect(box).toHaveValue(CRITERIA);
  await expect(page.getByTestId("criteria-hint")).toBeHidden();
}

async function search(page: Page) {
  await page.getByRole("button", { name: /Search (now|again)/ }).click();
  await expect(page.getByTestId("run-chronology")).toContainText(/Judged \d+ ·/, { timeout: 15_000 });
}

test.describe("Journey 1: full user flow", () => {
  test("register, criteria, scoring, search, decisions from the stream", async ({ page }) => {
    const user = uid();
    const pw = "testpass1";

    await register(page, user, pw);
    await saveCriteria(page);

    // Scoring lives in the rail, folded: open it, raise Auto-accept above by 6 (90 → 96)
    // so more events land in review for the accept/reject test below
    await page.getByText("Scoring", { exact: true }).click();
    const slider = page.getByRole("slider", { name: "Auto-accept above" });
    await slider.focus();
    for (let i = 0; i < 6; i++) {
      await slider.press("ArrowRight");
    }
    await expect(
      page.getByRole("spinbutton", { name: "Auto-accept above" })
    ).toHaveValue("96");
    const saveScoring = page.getByRole("button", { name: "Save scoring" });
    await expect(saveScoring).toBeEnabled();
    const [saved] = await Promise.all([
      page.waitForResponse(
        (r) => r.url().includes("/api/thresholds") && r.request().method() === "PUT",
        { timeout: 15_000 }
      ),
      saveScoring.click(),
    ]);
    expect(saved.ok()).toBeTruthy();

    // Reload and verify the value persisted
    await page.reload();
    await expect(page.getByRole("heading", { name: "Sail Event" })).toBeVisible();
    await page.getByText("Scoring", { exact: true }).click();
    await expect(
      page.getByRole("spinbutton", { name: "Auto-accept above" })
    ).toHaveValue("96");

    // Search — the chronology ends with the Judged line and the three-stage funnel sums
    await search(page);
    const funnel = page.getByTestId("funnel");
    await expect(funnel).toBeVisible();
    await expect(funnel).toContainText(/\d+ pages read/);
    await expect(funnel).toContainText(/\d+ found/);
    await expect(funnel).toContainText(/\d+ judged/);
    await expect(funnel).not.toContainText(/set aside|rejected/);
    await expect(page.getByTestId("funnel-stage-3")).toBeVisible();

    // Results: a column header, rows grouped by day; select a Review row and decide from the detail
    await expect(page.getByTestId("row-header")).toHaveText(/Event.*Start.*Where.*Score.*Status/);
    await expect(page.getByTestId("day-heading").first()).toBeVisible();
    const reviewRows = page.getByTestId(/^event-row-/).filter({ has: page.getByTestId("row-status").getByText("Review", { exact: true }) });
    await expect(reviewRows.first()).toBeVisible();
    // pin the row by id: the filtered locator would re-resolve to the next review row after the decision
    const firstRow = page.getByTestId((await reviewRows.first().getAttribute("data-testid"))!);
    await firstRow.click();
    await expect(page.getByTestId("event-detail")).toBeVisible();
    await expect(page.getByTestId("tie")).toBeVisible();
    await page.getByTestId("event-detail").getByRole("button", { name: "Add to calendar" }).click();
    await expect(firstRow.getByTestId("row-status")).toHaveText("In calendar");

    // Reject the next one from the detail: it folds into the "out" line
    const secondRow = page.getByTestId((await reviewRows.first().getAttribute("data-testid"))!);
    await secondRow.click();
    await page.getByTestId("event-detail").getByRole("button", { name: "Reject" }).click();
    await expect(secondRow).toBeHidden();
    await expect(page.getByTestId("results-section")).toContainText(/\d+ out/);
    await page.getByTestId("rejected-toggle").click();
    await expect(secondRow.getByTestId("row-status")).toHaveText("Out");

    // Remove from calendar from the detail: click it, confirm, status flips to Out
    await firstRow.click();
    await page.getByTestId("event-detail").getByRole("button", { name: "Remove from calendar" }).click();
    await page.getByRole("button", { name: "Remove", exact: true }).click();
    await expect(firstRow.getByTestId("row-status")).toHaveText("Out");

    // The theme switch flips the dark class and survives a reload
    await page.getByRole("button", { name: "Switch to dark theme" }).click();
    await expect(page.locator("html")).toHaveClass(/dark/);
    await page.reload();
    await expect(page.locator("html")).toHaveClass(/dark/);
    await page.getByRole("button", { name: "Switch to light theme" }).click();
    await expect(page.locator("html")).not.toHaveClass(/dark/);
  });

  test("phone: single column, funnel hidden, place hidden, detail as a bottom sheet", async ({ page }) => {
    await page.setViewportSize({ width: 400, height: 800 });
    await register(page, uid(), "testpass1");
    await saveCriteria(page);
    await search(page);
    await expect(page.getByTestId("funnel")).toBeHidden();
    await expect(page.getByTestId("row-place").first()).toBeHidden();
    const row = page.getByTestId(/^event-row-/).first();
    await row.click();
    const detail = page.getByTestId("event-detail");
    await expect(detail).toBeVisible();
    await expect(page.getByTestId("tie")).toBeHidden();
    const box = (await detail.boundingBox())!;
    expect(box.y + box.height).toBeLessThanOrEqual(800 + 1);
    expect(box.y).toBeGreaterThan(400);
    await detail.getByRole("button", { name: "Close" }).click();
    await expect(detail).toBeHidden();
    const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
    expect(scrollWidth).toBeLessThanOrEqual(400);
    await page.screenshot({ path: "test-results/stream-400.png", fullPage: true });
  });

  test("screenshots: desktop light and dark", async ({ browser }) => {
    for (const colorScheme of ["light", "dark"] as const) {
      const ctx = await browser.newContext({ colorScheme, viewport: { width: 1280, height: 900 } });
      const page = await ctx.newPage();
      await register(page, uid(), "testpass1");
      await saveCriteria(page);
      await search(page);
      await page.getByTestId(/^event-row-/).first().click();
      await expect(page.getByTestId("event-detail")).toBeVisible();
      await page.screenshot({ path: `test-results/stream-desktop-${colorScheme}.png`, fullPage: true });
      await ctx.close();
    }
  });
});

test.describe("Journey 2: user isolation", () => {
  test("second user sees no events from first user", async ({ browser }) => {
    const user1 = uid();
    const user2 = uid();
    const pw = "testpass2";

    // --- User 1: register, criteria, search ---
    const ctx1 = await browser.newContext();
    const page1 = await ctx1.newPage();
    await register(page1, user1, pw);
    await saveCriteria(page1);
    await search(page1);

    // Confirm user 1 has rows
    await expect(page1.getByTestId(/^event-row-/).first()).toBeVisible();
    await ctx1.close();

    // --- User 2: register, the stream is empty ---
    const ctx2 = await browser.newContext();
    const page2 = await ctx2.newPage();
    await register(page2, user2, pw);
    await expect(page2.getByTestId("criteria-hint")).toBeVisible();
    await expect(page2.getByTestId("results-section")).toBeHidden();
    await expect(page2.getByTestId(/^event-row-/)).toHaveCount(0);
    await ctx2.close();
  });
});
