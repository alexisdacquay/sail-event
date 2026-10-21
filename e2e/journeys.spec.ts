import { test, expect } from "@playwright/test";

function uid() {
  return `e2e_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}

test.describe("Journey 1: full user flow", () => {
  test("register, criteria, scoring, search, queue decisions, events page", async ({
    page,
  }) => {
    const user = uid();
    const pw = "testpass1";

    // Register
    await page.goto("/");
    await page.getByRole("button", { name: "Create one" }).click();
    await page.getByLabel("Username").fill(user);
    await page.getByLabel("Password").fill(pw);
    await page.getByRole("button", { name: "Create account" }).click();

    // Wait for authenticated layout
    await expect(page.getByRole("heading", { name: "Sail Event" })).toBeVisible();

    // Set criteria
    await page.getByLabel("What I'm looking for").fill("jazz in Berlin (Germany) next week (19-21st October 2026)");
    await page.getByRole("button", { name: "Save criteria" }).click();
    await expect(page.getByText("Saved.")).toBeVisible();

    // Adjust scoring scale: raise Auto-accept above by 6 (90 → 96) so
    // more events land in the queue for the accept/reject test below
    const slider = page.getByRole("slider", { name: "Auto-accept above" });
    await slider.focus();
    for (let i = 0; i < 6; i++) {
      await slider.press("ArrowRight");
    }
    // the key presses must have reached the shared state before saving
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
    await expect(
      page.getByRole("spinbutton", { name: "Auto-accept above" })
    ).toHaveValue("96");

    // Search — run report shows pipeline line or fallback "Found N events"
    await page.getByRole("button", { name: "Search now" }).click();
    await expect(page.getByTestId("search-result")).toBeVisible({ timeout: 15_000 });

    // Assert To review badge with count is visible in the header before clicking
    await expect(page.getByRole("button", { name: /To review \(\d+\)/ })).toBeVisible();

    // Go to To review
    await page.getByRole("button", { name: /To review/ }).click();
    await expect(page.getByRole("heading", { name: "To review" })).toBeVisible();

    // Add first event to calendar, reject second
    const addButtons = page.getByRole("button", { name: "Add to calendar" });
    const rejectButtons = page.getByRole("button", { name: "Reject" });

    // Wait for at least two queue items
    await expect(addButtons.first()).toBeVisible({ timeout: 5_000 });

    await addButtons.first().click();
    // After adding, the next item becomes first
    await rejectButtons.first().click();

    // Go to All events page
    await page.getByRole("button", { name: "All events" }).click();
    await expect(page.getByRole("heading", { name: "All events" })).toBeVisible();

    // Verify an accepted event shows Remove from calendar
    await expect(page.getByRole("button", { name: "Remove from calendar" }).first()).toBeVisible();

    // Remove from calendar: click it, confirm
    await page.getByRole("button", { name: "Remove from calendar" }).first().click();
    await page.getByRole("button", { name: "Remove", exact: true }).click();

    // After removal the card shows Add to calendar (status flipped to rejected)
    await expect(page.getByRole("button", { name: "Add to calendar" }).first()).toBeVisible();
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
    await page1.getByRole("button", { name: "Create one" }).click();
    await page1.getByLabel("Username").fill(user1);
    await page1.getByLabel("Password").fill(pw);
    await page1.getByRole("button", { name: "Create account" }).click();
    await expect(
      page1.getByRole("heading", { name: "Sail Event" })
    ).toBeVisible();
    await page1.getByLabel("What I'm looking for").fill("jazz in Berlin (Germany) next week (19-21st October 2026)");
    await page1.getByRole("button", { name: "Save criteria" }).click();
    await page1.getByRole("button", { name: "Search now" }).click();
    await expect(page1.getByTestId("search-result")).toBeVisible({
      timeout: 15_000,
    });

    // Confirm user 1 has events
    await page1.getByRole("button", { name: "All events" }).click();
    await expect(page1.getByText(/Score: \d+%/).first()).toBeVisible();
    await ctx1.close();

    // --- User 2: register, go straight to events ---
    const ctx2 = await browser.newContext();
    const page2 = await ctx2.newPage();
    await page2.goto("/");
    await page2.getByRole("button", { name: "Create one" }).click();
    await page2.getByLabel("Username").fill(user2);
    await page2.getByLabel("Password").fill(pw);
    await page2.getByRole("button", { name: "Create account" }).click();
    await expect(
      page2.getByRole("heading", { name: "Sail Event" })
    ).toBeVisible();
    await page2.getByRole("button", { name: "All events" }).click();
    await expect(page2.getByRole("heading", { name: "All events" })).toBeVisible();
    await expect(page2.getByText("No events yet.")).toBeVisible();
    await ctx2.close();
  });
});
