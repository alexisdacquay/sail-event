# UX specification — Sail-event redesign

## 1. Who the user is

A person who wants to go to events but does not want to scan sites every day.

### Three jobs

| Job | When | Done when |
|---|---|---|
| Set up what I like | Once, then tweak occasionally | My criteria are saved and a search has run |
| See what was found and decide | Every day or two | The queue is empty: every borderline event accepted or rejected |
| Get it on my calendar | After accepting | I subscribed to the feed; accepted events appear in my calendar app |


## 2. Mental model

The UI must teach this in one screen, without jargon:

- Every event the app finds gets a **match score from 0 to 100** against your criteria.
- You set two lines on that scale:
  - **Auto-accept above ___** — events scoring above this go straight to your calendar.
  - **Auto-reject below ___** — events scoring below this are rejected and never come back.
  - **In between** — the app puts them in your queue and you decide.
- The score comes with a one-line reason explaining why the event scored the way it did.

The home screen shows a visual of this scale: a horizontal bar from 0 to 100, with the two cut-off markers. The three zones are labelled: "Rejected", "You decide", "On your calendar". The user drags or types to move the markers.


## 3. Screens

### 3a. Sign in

- **Purpose:** authenticate a returning user
- **First thing the user sees:** centred card with the app name above it
- **Controls and labels:**
  - Heading: `Sign in`
  - Field: `Username`
  - Field: `Password`
  - Button (primary): `Sign in`
  - Text link: `No account? Create one`
- **Error state:** `Wrong username or password.` below the password field
- **Rate limit error:** `Too many attempts. Try again in a minute.`
- **Primary action:** Sign in

### 3b. Register

- **Purpose:** create a new account
- **First thing the user sees:** centred card with the app name above it
- **Controls and labels:**
  - Heading: `Create account`
  - Field: `Username`
  - Field: `Password`
  - Field (conditional, only when the deployment requires it): `Invitation code`
  - Button (primary): `Create account`
  - Text link: `Already have an account? Sign in`
- **Error state:** `Couldn't create your account. That username may already be taken.`
- **Primary action:** Create account

### 3c. Home

- **Purpose:** set up criteria, understand scoring, trigger a search, see your calendar link
- **Reached by:** the "Home" tab (default after sign-in)
- **First thing the user sees:** the criteria card, filled or with placeholder text

#### What I'm looking for (card)

- Heading: `What I'm looking for`
- Textarea placeholder (shown when empty): `e.g. jazz or folk concerts near Paris on weekends, under 40 EUR`
- Button: `Save`
- After save, brief confirmation: `Saved.`

#### How scoring works (card)

- Heading: `How scoring works`
- Explanatory line: `Every event gets a match score from 0 to 100 against what you wrote above. Events in between wait for you in the Queue tab.`
- Visual: horizontal bar, 0 on the left, 100 on the right, two draggable markers (or two number inputs below the bar)
  - Left marker label: `Auto-reject below`
  - Right marker label: `Auto-accept above`
  - Zone between the markers, labelled: `You decide`
  - Zone left of the left marker: `Rejected`
  - Zone right of the right marker: `On your calendar`
- Button: `Save`
- Validation error (lower >= upper): `The auto-accept line must be higher than the auto-reject line.`

#### Search now (card)

- Heading: `Search now`
- Explanatory line: `The app also searches automatically every hour.`
- Button: `Search now`
- After search: `Found 9 events, 8 new.` (inline, below the button)

#### Calendar feed (card, shown after first accepted event or always if URL exists)

- Heading: `Your calendar feed`
- Explanatory line: `Paste this link into your calendar app. Accepted events will appear there.`
- Read-only URL input + `Copy` button
- Secondary button: `Reset link` (with confirmation: `This will break any existing subscription. Reset?` — buttons `Reset` / `Cancel`)

#### Empty state (no criteria saved yet, first visit)

- The criteria card is open with the placeholder text.
- The scoring card shows the default markers (30 and 70).
- The search card says: `Write what you're looking for, then press Search now.`
- The calendar card is shown as always (the feed URL exists from the first visit; it is simply empty until events are accepted).

### 3d. Queue

- **Purpose:** decide borderline events the app couldn't sort automatically
- **Reached by:** the "Queue" tab, with a count badge when > 0
- **Tab label:** `Queue` (with count: `Queue (5)`)
- **First thing the user sees:** the first event card in the queue

#### Event card (queue variant)

- **Why** line first (the one-line reason from scoring), in emphasis
- Title of the event
- `Match: 72 / 100`
- Date, Place, Link (the link opens in a new tab)
- Two buttons: `Accept` (primary), `Reject` (outline/destructive)
- The card disappears from the queue on accept or reject

#### Empty state

- Text: `Nothing to decide right now.`
- Subtext: `Events that clearly match go straight to your calendar. Events that clearly don't are rejected. When the app isn't sure, they appear here.`

- **Primary action:** Accept or Reject the next event

### 3e. All events

- **Purpose:** see everything the app has found, in all states
- **Reached by:** the "All events" tab
- **Tab label:** `All events`
- **First thing the user sees:** the most recent events, sorted newest first

#### Event card (read-only variant)

- Title of the event
- Status badge:
  - `On your calendar` (was accepted)
  - `Rejected`
  - `Waiting for you` (queued but not decided yet)
- **Why** line (the one-line reason)
- `Match: 76 / 100`
- Date, Place, Link
- If status is "On your calendar": a `Remove from calendar` button (outline/destructive, with confirmation: `Remove this event from your calendar?` — buttons `Remove` / `Cancel`)

#### Empty state

- Text: `No events yet.`
- Subtext: `Write what you're looking for on the Home tab, then press Search now.`

- **Primary action:** review; optionally remove an accepted event from the calendar

### 3f. Navigation bar

- Left: app name `Sail Event`
- Tabs: `Home`, `Queue (N)`, `All events`
- Right: username, `Sign out` button


## 4. Onboarding (first-time user)

| Step | What happens |
|---|---|
| 1 | User creates an account on the Register screen |
| 2 | Home screen appears with an empty criteria card showing the placeholder example |
| 3 | User writes their criteria and presses Search now (the draft is saved first); the result line shows how many events were found and how many wait in the Queue |
| 4 | User opens the Queue tab and accepts or rejects their first event |

Ends with the user's first decision. No tutorial overlay, no wizard — the placeholder text and the "How scoring works" card teach the model.


## 5. Terminology table

| Old (current UI) | New | Why |
|---|---|---|
| Search Criteria | What I'm looking for | The user's words, not a database column |
| Thresholds | How scoring works | Says what the section is about |
| Lower Threshold | Auto-reject below | Says what the number does |
| Upper Threshold | Auto-accept above | Says what the number does |
| Save Criteria | Save | Obvious from context |
| Save Thresholds | Save | Obvious from context |
| Score: 76 | Match: 76 / 100 | Shows the scale; "match" is what it measures |
| Reason: ... | Why: ... | Shorter, natural |
| Dashboard (tab) | Home | Standard; "dashboard" is enterprise software |
| Events (tab) | All events | Distinguishes from the queue |
| queued (badge) | Waiting for you | Tells the user what to do |
| accepted (badge) | On your calendar | Tells the user where the event went |
| rejected (badge) | Rejected | Already clear |
| new (badge) | (not shown) | Internal pre-scoring state; the user never needs to see it |
| Login | Sign in | More common in consumer products |
| Register | Create account | Action-oriented |
| Logout | Sign out | Matches "Sign in" |
| Rotate link | Reset link | "Rotate" is ops jargon |
| Calendar Feed | Your calendar feed | Personal, not a feature label |
| Registration code | Invitation code | Friendlier; matches how the user received it |


## 6. What stays as is

- Three-tab layout (renamed but same structure)
- One free-text criteria field per user (no structured filters)
- Accept / Reject as the only two decisions
- Calendar feed via a copyable ICS URL (no calendar provider login)
- "Search now" button on the home screen
- Automatic hourly search (no UI for scheduling)
- EventCard as the unit of display (redesigned, not replaced)
- Auth flow: username + password, optional invitation code


## 7. Out of scope

- Visual theme (palette, type scale, spacing, dark mode) — P2 in the roadmap
- Icon / logo — P3 in the roadmap
- Admin / telemetry page — deferred, separate audience


## 8. Acceptance criteria

A person who has never seen the app before clicks through and can check each line.

1. The sign-in screen says "Sign in", not "Login"
2. The register screen says "Create account", not "Register"
3. The home screen shows a card titled "What I'm looking for" with a placeholder example
4. The home screen shows a card titled "How scoring works" with a visible 0–100 scale and two movable cut-off points
5. The left cut-off is labelled "Auto-reject below" and the right "Auto-accept above"
6. The zone between the cut-offs is labelled "You decide"
7. Changing a cut-off and pressing Save updates the user's settings (verify by refreshing)
8. The Queue tab shows a count badge when events are waiting
9. Each queue card shows the "Why" line before the title
10. Each queue card shows the match as "Match: NN / 100", not a bare number
11. Accepting a queue card removes it from the queue and it appears in All events as "On your calendar"
12. The All events tab shows status badges reading "On your calendar", "Rejected", or "Waiting for you" — never "new", "accepted", or "queued"
13. The All events tab has a "Remove from calendar" button on accepted events, with a confirmation step
14. The calendar card is titled "Your calendar feed" and the reset button says "Reset link", not "Rotate link"
15. Every button and label uses the words from the terminology table in section 5
16. The empty state for the queue explains the three zones in plain language
17. The empty state for All events directs the user to the Home tab
18. A first-time user can go from account creation to their first accept/reject decision without reading any documentation


## 9. API gaps

These are **not** current API endpoints. They would need to be added if the redesign uses them.

- **Event counts by status** — `GET /api/events/counts` → `{queued: 5, accepted: 12, rejected: 8}`. Currently the UI fetches all queued events and counts them in memory. A counts endpoint would let the home screen show a summary without loading every event. Nice-to-have; the current approach works.
- **Last search result** — `GET /api/search/last` → `{ranAt: "...", eventsFound: 9, eventsNew: 8}`. Currently the search result message disappears when the user changes tabs, and the hourly run (a GitHub Actions cron) leaves no trace in the UI. A last-run endpoint would let the home screen show "Last searched 2 hours ago, found 9 events" persistently. **First post-P1 API item** (promoted from nice-to-have by the design review).
- **Remove accepted event from calendar** — the All events screen adds a "Remove from calendar" action. The API already supports this: `POST /api/events/{id}/decision` with `{"decision": "rejected"}` changes an accepted event's status and removes it from the feed. **No new endpoint needed.**
