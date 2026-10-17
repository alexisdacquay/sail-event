import { test, expect } from "@playwright/test";

function uid() {
  return `e2e_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}

test.describe("Journey 1: full user flow", () => {
  test("register, criteria, search, queue decisions, events page", async ({
    page,
  }) => {
    const user = uid();
    const pw = "testpass1";

    // Register
    await page.goto("/");
    await page.getByRole("button", { name: "Register" }).click();
    await page.getByLabel("Username").fill(user);
    await page.getByLabel("Password").fill(pw);
    await page.getByRole("button", { name: "Register", exact: true }).click();

    // Wait for authenticated layout
    await expect(page.getByRole("heading", { name: "Sail Event" })).toBeVisible();

    // Set criteria
    await page.getByLabel("Criteria").fill("outdoor concerts and festivals");
    await page.getByRole("button", { name: "Save Criteria" }).click();

    // Search
    await page.getByRole("button", { name: "Search now" }).click();
    await expect(page.getByText("Search complete")).toBeVisible({ timeout: 15_000 });

    // Go to Queue
    await page.getByRole("button", { name: /Queue/ }).click();
    await expect(page.getByRole("heading", { name: "Queue" })).toBeVisible();

    // Accept first event, reject second
    const acceptButtons = page.getByRole("button", { name: "Accept" });
    const rejectButtons = page.getByRole("button", { name: "Reject" });

    // Wait for at least two queue items
    await expect(acceptButtons.first()).toBeVisible({ timeout: 5_000 });

    await acceptButtons.first().click();
    // After accepting, the next item becomes first
    await rejectButtons.first().click();

    // Go to Events page
    await page.getByRole("button", { name: "Events" }).click();
    await expect(page.getByRole("heading", { name: "Events" })).toBeVisible();

    // Verify statuses are shown (multiple badges possible; check first of each)
    await expect(page.getByText("accepted").first()).toBeVisible();
    await expect(page.getByText("rejected").first()).toBeVisible();
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
    await page1.goto("/");
    await page1.getByRole("button", { name: "Register" }).click();
    await page1.getByLabel("Username").fill(user1);
    await page1.getByLabel("Password").fill(pw);
    await page1.getByRole("button", { name: "Register", exact: true }).click();
    await expect(
      page1.getByRole("heading", { name: "Sail Event" })
    ).toBeVisible();
    await page1.getByLabel("Criteria").fill("sailing regattas");
    await page1.getByRole("button", { name: "Save Criteria" }).click();
    await page1.getByRole("button", { name: "Search now" }).click();
    await expect(page1.getByText("Search complete")).toBeVisible({
      timeout: 15_000,
    });

    // Confirm user 1 has events
    await page1.getByRole("button", { name: "Events" }).click();
    await expect(page1.getByText(/score/i).first()).toBeVisible();
    await ctx1.close();

    // --- User 2: register, go straight to events ---
    const ctx2 = await browser.newContext();
    const page2 = await ctx2.newPage();
    await page2.goto("/");
    await page2.getByRole("button", { name: "Register" }).click();
    await page2.getByLabel("Username").fill(user2);
    await page2.getByLabel("Password").fill(pw);
    await page2.getByRole("button", { name: "Register", exact: true }).click();
    await expect(
      page2.getByRole("heading", { name: "Sail Event" })
    ).toBeVisible();
    await page2.getByRole("button", { name: "Events" }).click();
    await expect(page2.getByRole("heading", { name: "Events" })).toBeVisible();
    await expect(page2.getByText("No events yet.")).toBeVisible();
    await ctx2.close();
  });
});
