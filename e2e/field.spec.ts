import { test, expect, Page } from "@playwright/test";

// Field-test UI invariants U1-U4 (the data ones are backend/tests/field/invariants.py).
// Each test asserts what a user expects. A test.fail() line names the open issue; the fix PR
// deletes that line, and Playwright then flags the test if it still fails.

async function signUp(page: Page) {
  const user = `field_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`;
  await page.goto("/");
  await page.getByRole("button", { name: "Create one" }).click();
  await page.getByLabel("Username").fill(user);
  await page.getByLabel("Password").fill("testpass1");
  await page.getByRole("button", { name: "Create account" }).click();
  await expect(page.getByRole("heading", { name: "Sail Event" })).toBeVisible();
  // a new user has no saved search, so the editor is open
  await page.getByLabel("What I'm looking for").fill("jazz in Berlin (Germany) next week (19-21st October 2026)");
  await page.getByRole("button", { name: "Save criteria" }).click();
  await expect(page.getByText("Saved.")).toBeVisible();
}

async function searchNow(page: Page) {
  await page.getByRole("button", { name: /Search (now|again)/ }).click();
  await expect(page.getByTestId("run-chronology")).toContainText(/Judged \d+ ·/, { timeout: 15_000 });
}

test("U1 reload keeps the page", async ({ page }) => {
  test.fail(true, "tabs are not in the URL (#96)");
  await signUp(page);
  await page.getByRole("button", { name: "All events" }).click();
  await expect(page.getByRole("heading", { name: "All events" })).toBeVisible();
  await page.reload();
  await expect(page.getByRole("heading", { name: "All events" })).toBeVisible();
});

test("U1 reload keeps the search result", async ({ page }) => {
  await signUp(page);
  await searchNow(page);
  await page.reload();
  await expect(page.getByTestId("run-chronology")).toContainText(/Judged \d+ ·/);
});

test("U2 the Judged line matches the badge and the rows", async ({ page }) => {
  await signUp(page);
  await searchNow(page);
  const line = (await page.getByTestId("run-chronology").textContent())!;
  const n = Number(line.match(/(\d+) to review/)![1]);
  const nav = page.getByRole("navigation", { name: "Main navigation" });
  if (n === 0) {
    await expect(nav.getByTestId("queue-count")).toHaveCount(0);
    return;
  }
  await expect(nav.getByTestId("queue-count")).toHaveText(`(${n})`);
  await expect(page.getByTestId("row-status").filter({ hasText: "To review" })).toHaveCount(n);
});

test("U3 slider knobs equal the boxes", async ({ page }) => {
  await signUp(page);
  await page.getByText("Scoring", { exact: true }).click();
  for (const name of ["Auto-reject below", "Auto-accept above"]) {
    const box = await page.getByRole("spinbutton", { name }).inputValue();
    await expect(page.getByRole("slider", { name })).toHaveAttribute("aria-valuenow", box);
  }
});

test("U3 the zone legend is not clipped on a narrow desktop", async ({ page }) => {
  test.fail(true, "legend clipped: 'ı your cale' (#94)");
  await page.setViewportSize({ width: 700, height: 900 });
  await signUp(page);
  await page.getByText("Scoring", { exact: true }).click();
  const clipped = await page
    .getByTestId("scoring-card")
    .locator("*")
    .evaluateAll((els) =>
      els
        // visible, wider than the 1px sr-only legend, and overflowing
        .filter((e) => (e as HTMLElement).offsetParent !== null && e.clientWidth > 1 && e.scrollWidth > e.clientWidth + 1)
        .map((e) => e.textContent?.trim())
    );
  expect(clipped).toEqual([]);
});

test("U4 copy gives feedback", async ({ page, context }) => {
  await context.grantPermissions(["clipboard-read", "clipboard-write"]);
  await signUp(page);
  await page.getByTestId("copy-calendar-url").click();
  await expect(page.getByTestId("copy-calendar-url")).toHaveText("Copied");
});

test("U4 the feed link is a webcal subscription", async ({ page }) => {
  test.fail(true, "the feed is a bare https URL with no subscribe steps (#95)");
  await signUp(page);
  await expect(page.getByTestId("calendar-url")).toHaveValue(/^webcal:\/\//);
});
