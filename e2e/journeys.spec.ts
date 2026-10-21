import { test, expect, Page } from "@playwright/test";

function uid() {
  return `e2e_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}

const CRITERIA = "jazz in Berlin (Germany) next week (19-21st October 2026)";

async function register(page: Page, user: string, pw: string) {
  await page.goto("/");
  await page.getByRole("button", { name: "Create one" }).click();
  await page.getByLabel("Username").fill(user);
  await page.getByLabel("Password").fill(pw);
  await page.getByRole("button", { name: "Create account" }).click();
  await expect(page.getByRole("heading", { name: "Sail Event" })).toBeVisible();
}

// A new user has no saved search, so the Stream page opens with the editor.
async function saveCriteria(page: Page) {
  await page.getByLabel("What I'm looking for").fill(CRITERIA);
  await page.getByRole("button", { name: "Save criteria" }).click();
  await expect(page.getByText("Saved.")).toBeVisible();
  await expect(page.getByTestId("criteria-text")).toHaveText(CRITERIA);
}

async function search(page: Page) {
  await page.getByRole("button", { name: /Search (now|again)/ }).click();
  await expect(page.getByTestId("run-chronology")).toContainText(/Judged \d+ ·/, { timeout: 15_000 });
}

test.describe("Journey 1: full user flow", () => {
  test("register, criteria, scoring, search, stream decisions, queue, events page", async ({
    page,
  }) => {
    const user = uid();
    const pw = "testpass1";

    await register(page, user, pw);
    await saveCriteria(page);

    // Scoring lives in the rail, folded: open it, raise Auto-accept above by 6 (90 → 96)
    // so more events land in the queue for the accept/reject test below
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

    // Search — the chronology ends with the Judged line and the funnel shows the found count
    await search(page);
    await expect(page.getByTestId("funnel")).toBeVisible();
    await expect(page.getByTestId("funnel")).toContainText(/\d+ found/);

    // Results: rows grouped by day; select a To review row and decide from the detail
    await expect(page.getByTestId("day-heading").first()).toBeVisible();
    const firstQueued = page.getByTestId(/^event-row-/).filter({ hasText: "To review" }).first();
    await expect(firstQueued).toBeVisible();
    // pin the row by id: the filtered locator would re-resolve to the next queued row after the decision
    const queuedRow = page.getByTestId((await firstQueued.getAttribute("data-testid"))!);
    await queuedRow.click();
    await expect(page.getByTestId("event-detail")).toBeVisible();
    await expect(page.getByTestId("tie")).toBeVisible();
    await page.getByTestId("event-detail").getByRole("button", { name: "Add to calendar" }).click();
    await expect(queuedRow.getByTestId("row-status")).toHaveText("In calendar");

    // The To review badge counts the rest
    const nav = page.getByRole("navigation", { name: "Main navigation" });
    await expect(nav.getByRole("button", { name: /To review \(\d+\)/ })).toBeVisible();
    await nav.getByRole("button", { name: /To review/ }).click();
    await expect(page.getByRole("heading", { name: "To review" })).toBeVisible();
    const rejectButtons = page.getByRole("button", { name: "Reject" });
    await expect(rejectButtons.first()).toBeVisible({ timeout: 5_000 });
    await rejectButtons.first().click();

    // Go to All events page
    await nav.getByRole("button", { name: "All events" }).click();
    await expect(page.getByRole("heading", { name: "All events" })).toBeVisible();

    // Verify an accepted event shows Remove from calendar
    await expect(page.getByRole("button", { name: "Remove from calendar" }).first()).toBeVisible();

    // Remove from calendar: click it, confirm
    await page.getByRole("button", { name: "Remove from calendar" }).first().click();
    await page.getByRole("button", { name: "Remove", exact: true }).click();

    // After removal the card shows Add to calendar (status flipped to rejected)
    await expect(page.getByRole("button", { name: "Add to calendar" }).first()).toBeVisible();
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

    // Confirm user 1 has events
    await page1.getByRole("button", { name: "All events" }).click();
    await expect(page1.getByText(/Score: \d+%/).first()).toBeVisible();
    await ctx1.close();

    // --- User 2: register, go straight to events ---
    const ctx2 = await browser.newContext();
    const page2 = await ctx2.newPage();
    await register(page2, user2, pw);
    await expect(page2.getByTestId("results-section")).toBeHidden();
    await page2.getByRole("button", { name: "All events" }).click();
    await expect(page2.getByRole("heading", { name: "All events" })).toBeVisible();
    await expect(page2.getByText("No events yet.")).toBeVisible();
    await ctx2.close();
  });
});
