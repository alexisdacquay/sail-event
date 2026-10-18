# UX design review — `_docs/ux-spec.md` + `_docs/ux-design.md`

Reviewer walked the three screens as a first-time user against the current build (`frontend/src/pages/*`, `docs/images/02-04`), the API (`backend/app/routers/*`), and `e2e/journeys.spec.ts`.

## One-screen test (owner's question)

| Does Home teach it? | Verdict | Where it fails |
|---|---|---|
| Events get a 0–100 match score | yes | explainer line + bar ends `0` / `100` |
| Above one line → calendar | yes | zone `On your calendar`, label `Auto-accept above` |
| Below the other → gone | yes, but the copy is false | spec says "hidden"; they are listed under All events as `Rejected` (S1) |
| In between → the app asks | no | zone says `You decide`; nothing on Home names the Queue tab, and after a search the header count is stale (B2, S2) |

## Findings

| id | sev | what is wrong | exact change | doc |
|---|---|---|---|---|
| B1 | blocker | `Wrong username or password.` can never render: `http.ts:36-41` calls `window.location.reload()` on every 401 before the throw; login returns 401 (`auth.py:61`). Design facts table lists only "throws `Error(detail)` with no HTTP status" | §7 `http.ts` row and Issue A checklist: the 401 reload + token clear runs only when a token is present (`if (res.status === 401 && token())`); add the reload fact to the facts table; Issue A acceptance line "401 shows `Wrong username or password.`" needs a unit test with no token in storage | design |
| B2 | blocker | §2 First-run step 4 promises "`Queue (N)` count appears in the header" but §3f refreshes the count only "on every tab click and after every decision" and Issue C has no line for it. After `Found 9 events, 8 new.` the header reads bare `Queue`: no cue to step 5 | §3f count rule add "and after a completed search"; Issue C add "MainPage takes `onSearchComplete`; App passes `refreshQueueCount`"; §3c Result row: append the count to the line (`Found 9 events, 8 new. 3 waiting for you in the Queue.`) using the same number | design |
| S1 | should | Spec §2 "events scoring below this are hidden and never come back" and §3d empty subtext "Events that clearly don't are hidden" are false: All events lists them with badge `Rejected` (design §3e; `GET /api/events` returns all statuses) | spec §2 bullet and §3d subtext: "hidden" → "rejected" (keep "never come back"); design §3d Empty state row and §6 Queue page follow | both |
| S2 | should | Home never links the middle zone to the Queue tab: zone `You decide` (spec §3c), tab `Queue (N)`; the only explanation of what "ask" means lives in the queue empty state the user reaches last | spec §3c "How scoring works" explanatory line gets a second sentence naming the tab (`Events in between wait for you in the Queue tab.`); design §3c Explainer row and §6 Scoring card follow | both |
| S3 | should | Search hint contradicts the disabled rule: §3c hint `Write what you're looking for, then press Search now.` while the button is `disabled while saved criteria are empty` (decision 11). User types, button stays dead, hint says press it | Reverse decision 11: `Search now` saves the textarea draft first (`await saveCriteria(text)` then `runSearch()`), disabled only while the textarea is empty; hint unchanged; spec §4 steps 3-4 collapse to "write criteria, press Search now"; decision 11's counter-fact ("searches with the old text") disappears | both |
| S4 | should | Issue E selector `getByLabel("Auto-accept above")` matches two elements by design (§4 Accessibility: thumb `<input type=range>` and number input share the name) → Playwright strict-mode error | Issue E: `getByRole("spinbutton", { name: "Auto-accept above" })` for the number input; Issue D `ScoreScale.test.tsx`: same split (`slider` vs `spinbutton`) | design |
| S5 | should | Queue order unspecified: §2 says "newest-dated last (see §9)" but §9 has no queue decision and §3d Cards row says nothing; the engineer will guess | §3d Cards row add "sorted by `dateTime` ascending (soonest first, same as All events)"; §2 pointer → "(see §3d)" | design |
| S6 | should | Sign-in link says `Register`; the screen it opens is headed `Create account` (spec §3a vs §3b; terminology row "Register → Create account") | spec §3a link `No account? Create one`; design §3a Switch link row, §6 Sign in, Issue E rows for lines 16 / 67 / 90 → `getByRole("button", { name: "Create one" })` | both |
| N1 | nice | `Found 0 events, 0 new.` gives no next step | §3c Result row: branch on `eventsFound === 0` → `Found no events. Try broader criteria.`; §6 copy table | design |
| N2 | nice | Queue `Reject` is terminal (`events.py:68` refuses re-deciding a rejected event) with no confirm and no undo; `Remove from calendar` (same end state) gets a confirm. Asymmetry is unstated | §9 add a decision row: "Queue Reject: no confirmation, no undo; the API refuses re-decision; accepted because confirm-per-event defeats the daily job" | design |
| N3 | nice | `Link:` row with the full URL (decision 15) is the ugliest line on every card and the seventh row | §5 layout: title rendered as the link (`<a target=_blank rel=noopener>`), `Link:` row dropped; `EventCard.test` asserts `getByRole('link', { name: title })` | design |
| N4 | nice | The card's score is a bare number; the three zones are drawn only on Home. Highest-leverage "modern" touch that needs no theme | §5 row 3: under `Match: 72 / 100` a 4 px track with the same three zone fills and a tick at the score; thresholds fetched once in App and passed down | design |
| N5 | nice | Decision 7 counter-fact is wrong: `new` events persist until the next run (pipeline.py:77-84 re-scores leftovers), not "for a few seconds"; the filter hides a failed scoring | §9 decision 7: correct the fact; keep the filter | design |
| N6 | nice | Hourly search is invisible: the sentence `The app also searches automatically every hour.` is the only trace, and the run is a GitHub Actions cron (architecture.md:57) the user cannot see | spec §9 "Last search result" promoted from nice-to-have to the first post-P1 API item | spec |

## Deviations checked (design §9)

| # | Deviation | Verdict | Strongest fact against |
|---|---|---|---|
| 6 | All events sorted by `dateTime` ascending, not "newest first" | right: API has no `createdAt`; soonest-first is what a calendar user needs | past-dated events sort to the top; fixtures are all future-dated so nobody has seen it |
| 8 | 429 copy `Try again later.` not `in a minute.` | right: windows are 900 s (`auth.py:23`) and 3600 s (`auth.py:42`) | spec copy was friendlier; "later" is vague |
| 10 | Calendar card always shown | right: subscribing before the first event is the better order | first-timer sees a feed URL before anything exists |
| 11 | `Search now` disabled until criteria saved | wrong, see S3 | — |

## Checks that passed

- Constraints: no new dependency; `@base-ui/react` 1.9.0 slider exposes `minStepsBetweenValues`, `largeStep`, `getAriaLabel`, `getAriaValueText` (verified in `node_modules/@base-ui/react/slider/**/*.d.ts`); `index.css` and `components/ui/*` untouched; every endpoint used exists.
- Issue E selector table matches `e2e/journeys.spec.ts` line for line (one off-by-one: 91 should read 90).
- Issues: A is independent; B → C (ConfirmAction) → D (scoring-card state) → E form a chain, which §8 states ("dependency order"). Sizes hold; B is the largest (one component, one new component, two pages, three test files) but still one session.
- Mobile: header wrap, legend swatches, `inputMode=numeric`, 24 px thumbs are specified; nothing missing at 360 px.
- Empty states and feedback: loading, empty and error copy exist for every list and every action; inline, no toast.

## Verdict

**APPROVE WITH CHANGES.** Strongest fact against: both blockers sit on the exact first-run path the owner asked to walk before coding (wrong-password feedback, the cue from "Found 9 events" to the Queue), so a REWORK call is defensible; it is not made because each fix is one line and leaves the structure, copy and issue split intact.
