# UX specification — Sail-event redesign

This describes the Stream UI on main. The earlier Home/Queue/All events proposal
was superseded by [ui-design.md](ui-design.md); historical heading names below
are retained for existing links. Sources: [MainPage](../frontend/src/pages/MainPage.tsx),
[EventDetail](../frontend/src/components/EventDetail.tsx),
[ScoreScale](../frontend/src/components/ScoreScale.tsx).

## 1. Who the user is

A person who wants relevant events in their calendar without repeatedly
searching and checking pages.

### Three jobs

| Job | When | Outcome |
|---|---|---|
| Delegate discovery | Save or revise interests | Matching events reach my calendar without repeating the search myself |
| Resolve uncertain matches | Review results | Events I would attend are kept; unsuitable ones are out |
| Use the events | Plan my time | Accepted events appear in the calendar app I already use |

## 2. Mental model

A judge scores each event against the saved sentence from 0 to 100 and gives a
reason. Default thresholds are 90 and 40: at least 90 goes **In calendar**, at
most 40 goes **Out**, and the middle goes to **Review**. Users can change the
thresholds. The score is not a calibrated probability, despite the `%` display.

**Out** rows are hidden behind **show**. A later search does not bring them
back. Known wording gap: [Auto-accept above / Auto-reject below](https://github.com/alexisdacquay/sail-event/blob/542e58cb0fe73065a905febec7637bfa377a77c4/frontend/src/components/ScoreScale.tsx#L80-L86) describe strict comparisons, although the code includes equality.

## 3. Screens

### 3a. Sign in

[LoginPage](../frontend/src/pages/LoginPage.tsx) authenticates returning users.
Error copy distinguishes wrong credentials, rate limiting and other failures.
The sign-in pitch says “every hour”; actual GitHub workflow starts are less
frequent ([PRD timing](plan.md#2-search)).

### 3b. Register

[RegisterPage](../frontend/src/pages/RegisterPage.tsx) requires an invitation
code only when `GET /api/config` enables it. Authentication errors remain on the form.

### 3c. Home

The current main screen is the **Stream**, replacing the former Home card stack.
The search text, run chronology, results and supporting rail share one view.

#### What I'm looking for (card)

A visible textarea and one search action replace separate edit/save/search
steps. **Search now** saves the current text, then runs.
Enter submits; Shift+Enter permits a newline. During a run, Enter can save a
change for the next search; it does not launch a second run. The button itself
is disabled while searching.

#### How scoring works (card)

The rail's collapsed **Scoring** section has a two-marker scale, number inputs
and Save. The zones read **Out / You decide / On your calendar**. Saved settings
persist; invalid bounds disable Save. Known boundary-wording gap: §2.

#### Search now (card)

Chronology shows the active stage and counts, with a hairline progress indicator
when totals are known. The desktop funnel splits found events into screened out
and judged, then calendar/review/rejected/not scored yet. On phones the funnel
is hidden; the chronology remains. Earlier runs appear below it.

Scheduled searches are a GitHub cron targeting prod, with irregular actual
starts. There is no scheduling control in the UI. Search latency measurements
and their limits are in the [PRD](plan.md#2-search).

#### Calendar feed (card, shown after first accepted event or always if URL exists)

The rail shows **Calendar feed**, a copyable URL and **Reset link**. Reset asks
for confirmation and invalidates the old URL. Anyone with the URL can read the
feed. Calendar clients refresh it on their own schedule.

#### Empty state (no criteria saved yet, first visit)

The search box shows an example without a price condition. Search is disabled
for blank text. The rail shows “no search yet”; Results appears only when event
rows exist. Threshold values are loaded from the account, not fixed UI defaults.

### 3d. Queue

There is no Queue tab. **Review** rows appear in Results, grouped with other
visible events by date. Selecting a row opens its detail in the rail (a bottom
panel on phones). Review actions are **Add to calendar** and **Reject**.
Failures show an error beside the actions.

### 3e. All events

There is no All events tab. Results shows accepted and review rows; **show**
reveals Out rows. Accepted events have **Remove from calendar**, with confirmation.
**Clear all** confirms irreversible deletion of every event for the user.

<a id="event-detail"></a>

Known gap: the detail of an Out event shows **Add to calendar**, but
[the decision endpoint](../backend/app/routers/events.py) accepts decisions only
on queued or accepted events and returns 400 for rejected ones. The control does
not restore an Out event.

### 3f. Navigation bar

[App](../frontend/src/App.tsx) supplies the app header, theme switch, username
and Sign out. The main view has no Home/Queue/All events tabs. The Searches rail
lists one saved search; **+ new search** is disabled with “coming later”.

## 4. Onboarding (first-time user)

The intended first outcome is useful events, followed by a decision on uncertain
matches and a calendar subscription. There is no tutorial overlay or wizard.
Relevance and coverage are measured through the [search evaluation](search-spec.md#11-evaluation).

## 5. Terminology table

| Stored status / stage | User-facing wording |
|---|---|
| accepted | In calendar |
| queued | Review (rows), to review (run summary) |
| rejected | Out (rows), rejected (funnel/chronology) |
| new after judge error | Not scored yet in the funnel; no result row |
| Code exclusion | Screened out |
| Feed token rotation | Reset link |

## 6. What stays as is

One free-text profile per user, two threshold cutoffs, decisions on individual
events and a per-user ICS feed remain the core model. Known-zone events display
the listed local time, with a zone suffix when it differs from the browser zone.
Source: [EventCard](../frontend/src/components/EventCard.tsx). Comparing against
the saved user zone rather than the browser zone is still an open UX issue.

## 7. Out of scope

Multiple saved searches, notifications and calendar-provider write access are
not delivered. Theme history, mockups and content rules are in
[ui-design.md](ui-design.md), separate from this behavior specification.

## 8. Acceptance criteria

[MainPage tests](../frontend/src/pages/MainPage.test.tsx) and
[e2e journeys](../e2e/journeys.spec.ts) cover saved criteria, thresholds, run
progress, event decisions, hidden Out rows and feed behavior. Remaining issues:
[UI/API gaps](#3e-all-events) and [boundary labels](#2-mental-model).

## 9. API gaps

Run history is delivered through `GET /api/search/runs`, `/api/search/runs/{run_id}`
and `/api/search/last-run`; it is no longer a proposed endpoint.
`GET /api/events/counts` is not in the contract; the current screen loads events
and groups/counts them in memory. Removing accepted events uses the existing
`POST /api/events/{id}/decision` endpoint. Contract: [openapi.yaml](../openapi.yaml).
