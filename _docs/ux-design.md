# UX design — Sail-event redesign (implements `_docs/ux-spec.md`)

Source of truth for copy and behaviour: `_docs/ux-spec.md`. This document adds the layout, the components, the states and the build order. Where this document and the spec differ, section 9 lists the deviation and why.

Facts about the current build this design relies on (checked in code):

| Fact | Where |
|---|---|
| Triage is strict: `score > upper` → accepted, `score < lower` → rejected, else queued. A score equal to a cut-off goes to the queue | `backend/app/services/pipeline.py:189-194` |
| `PUT /api/thresholds` returns 400 when `lower >= upper`; DB has the same check constraint | `backend/app/routers/thresholds.py:30`, `orm.py:35` |
| `GET /api/events` has no ordering and no `createdAt`; `new` is a real status (scored later) | `backend/app/routers/events.py` |
| Sign-in 429 window is 15 minutes; register 429 is per hour | `backend/app/routers/auth.py:23,42` |
| Duplicate username → 409; bad invitation code → 403 | `backend/app/routers/auth.py:56-77` |
| `GET /api/calendar-url` always returns a URL (token created with the user) | `MainPage.tsx:46` renders the card whenever `url` is truthy |
| `http.ts` throws `Error(detail)` with no HTTP status, and on every 401 it clears the token and calls `window.location.reload()` before throwing — so a wrong password (401 from `auth.py:61`) reloads the page instead of showing an error | `frontend/src/services/http.ts:35-45` |
| `new` events persist until the next run re-scores them (not seconds): a failed scoring leaves them `new` | `backend/app/services/pipeline.py:77-84` |
| Installed and unused: `@base-ui/react/slider` (range, `minStepsBetweenValues`, per-thumb `getAriaLabel`, nested `<input type="range">`) | `frontend/node_modules/@base-ui/react/slider` |
| shadcn primitives present: badge, button, card, input, label, textarea. No dialog, tabs, slider, toast wrappers | `frontend/src/components/ui/` |
| Tailwind v4, CSS-only config (`index.css`), neutral palette, `.dark` variant defined | `frontend/src/index.css` |


## 1. Design principles

- Every label says what the number or button does for the user, never what the column is called.
- One screen teaches the model: the 0–100 bar with its three zones is the explanation; no tutorial.
- The reason comes before the number: cards lead with "Why", the score is a supporting fact.
- Feedback is inline and immediate: the thing you touched tells you what happened, where you are looking.
- Nothing new to install: Tailwind tokens, the six shadcn primitives present, and the already-installed Base UI slider.


## 2. Information architecture

### Navigation

| Area | Content | Notes |
|---|---|---|
| Header left | `Sail Event` (h1) | unchanged heading, e2e anchors on it |
| Header tabs | `Home` · `Queue (N)` · `All events` | buttons (`role=button`), active = `default` variant, others `ghost`; `(N)` only when N > 0 |
| Header right | username (hidden on phone) · `Sign out` (outline, sm) | |
| Main | one page at a time, `max-w-2xl`, `p-4` phone / `p-8` desktop | |

### What lives where

| Tab | Job (spec §1) | Cards / lists |
|---|---|---|
| Home (default after sign-in) | Set up what I like · Get it on my calendar | What I'm looking for · How scoring works · Search now · Your calendar feed |
| Queue | See what was found and decide | queue event cards, sorted soonest first (see §3d) |
| All events | Review everything | read-only event cards with status badge; `new` events filtered out |

### First-run flow (spec §4)

| Step | Screen | What the user sees |
|---|---|---|
| 1 | Create account | centred card, `Create account` button |
| 2 | Home | criteria textarea empty with placeholder; scale at 30 / 70; search card shows hint line, `Search now` disabled while the textarea is empty; calendar card present (URL exists) |
| 3 | Home | types criteria, presses `Search now` → the draft is saved first (`Saved.` on the criteria card), then `Searching…` → `Found 9 events, 8 new. 3 waiting for you in the Queue.`; `Queue (3)` appears in the header |
| 4 | Queue | first card: Why line, title, match, Accept / Reject |


## 3. Screens

Legend for wireframes: `[ ]` button, `( )` text input, `{ }` badge, `~~` placeholder text.

### 3a. Sign in

Desktop:

```
                                                                    
                        Sail Event                                  
            +------------------------------------+                  
            | Sign in                            |                  
            |                                    |                  
            | Username                           |                  
            | (                                ) |                  
            | Password                           |                  
            | (                                ) |                  
            | Wrong username or password.        |  <- error, hidden
            | [          Sign in               ] |                  
            |       No account? Create one       |                  
            +------------------------------------+                  
```

Phone (≈40 cols):

```
+--------------------------------------+
|            Sail Event                |
| +----------------------------------+ |
| | Sign in                          | |
| | Username                         | |
| | (                              ) | |
| | Password                         | |
| | (                              ) | |
| | Wrong username or password.      | |
| | [          Sign in             ] | |
| |     No account? Create one       | |
| +----------------------------------+ |
+--------------------------------------+
```

| Element | Copy | Component | State / behaviour | Empty | Error |
|---|---|---|---|---|---|
| App name | `Sail Event` | `<p class="text-2xl font-bold text-center">` above the card | static | — | — |
| Heading | `Sign in` | `CardTitle` | — | — | — |
| Username | `Username` | `Label` + `Input` (`id=username`, `required`, `autoComplete=username`) | — | — | — |
| Password | `Password` | `Label` + `Input type=password` (`autoComplete=current-password`) | — | — | — |
| Error line | see Error | `<p class="text-sm text-destructive" role="alert">` under password | hidden until a failed submit; cleared on next submit | — | 401 → `Wrong username or password.` · 429 → `Too many attempts. Try again later.` · anything else → `Couldn't sign in. Try again.` |
| Submit | `Sign in` | `Button type=submit` | `disabled` + label `Signing in…` while the request is in flight | — | — |
| Switch link | `No account? Create one` | `<button type=button class="underline">` on `Create one` | navigates to Create account | — | — |

### 3b. Create account

Desktop:

```
                        Sail Event                                  
            +------------------------------------+                  
            | Create account                     |                  
            |                                    |                  
            | Username                           |                  
            | (                                ) |                  
            | Password                           |                  
            | (                                ) |                  
            | Invitation code      <- only if required               
            | (                                ) |                  
            | Couldn't create your account. That |  <- error, hidden
            | username may already be taken.     |                  
            | [       Create account           ] |                  
            |   Already have an account? Sign in |                  
            +------------------------------------+                  
```

Phone:

```
+--------------------------------------+
|            Sail Event                |
| +----------------------------------+ |
| | Create account                   | |
| | Username                         | |
| | (                              ) | |
| | Password                         | |
| | (                              ) | |
| | Invitation code                  | |
| | (                              ) | |
| | Couldn't create your account.    | |
| | That username may already be     | |
| | taken.                           | |
| | [      Create account          ] | |
| | Already have an account? Sign in | |
| +----------------------------------+ |
+--------------------------------------+
```

| Element | Copy | Component | State / behaviour | Empty | Error |
|---|---|---|---|---|---|
| App name | `Sail Event` | as 3a | — | — | — |
| Heading | `Create account` | `CardTitle` | — | — | — |
| Username | `Username` | `Label` + `Input` (`required`, `autoComplete=username`) | — | — | — |
| Password | `Password` | `Label` + `Input type=password` (`autoComplete=new-password`) | — | — | — |
| Invitation code | `Invitation code` | `Label` + `Input` (`id=invitationCode`, `required`) | rendered only when `GET /api/config` says `registrationCodeRequired` | — | — |
| Error line | see Error | `<p role="alert" class="text-sm text-destructive">` | hidden until a failed submit | — | 409 → `Couldn't create your account. That username may already be taken.` · 403 → `That invitation code isn't valid.` · 429 → `Too many attempts. Try again later.` · else → `Couldn't create your account. Try again.` |
| Submit | `Create account` | `Button type=submit` | `disabled` + `Creating…` in flight | — | — |
| Switch link | `Already have an account? Sign in` | underline button on `Sign in` | navigates to Sign in | — | — |

### 3c. Home

Desktop:

```
 Sail Event   [Home] Queue (5)  All events              reviewer [Sign out]
 ---------------------------------------------------------------------------
            +------------------------------------------------------+
            | What I'm looking for                                 |
            | +--------------------------------------------------+ |
            | | ~~e.g. jazz or folk concerts near Paris on       | |
            | |   weekends, under 40 EUR~~                       | |
            | +--------------------------------------------------+ |
            | [ Save ]  Saved.                                     |
            +------------------------------------------------------+
            +------------------------------------------------------+
            | How scoring works                                    |
            | Every event gets a match score from 0 to 100 against |
            | what you wrote above. Events in between wait for you |
            | in the Queue tab.                                    |
            |                                                      |
            | 0                                               100  |
            | [#######|-----------------------|###############]    |
            |         ^30                     ^70                  |
            |  Rejected      You decide       On your calendar     |
            |                                                      |
            | Auto-reject below (30 )   Auto-accept above (70 )    |
            | The auto-accept line must be higher than the         |
            | auto-reject line.                        <- hidden   |
            | [ Save ]  Saved.                                     |
            +------------------------------------------------------+
            +------------------------------------------------------+
            | Search now                                           |
            | The app also searches automatically every hour.      |
            | [ Search now ]                                       |
            | Found 9 events, 8 new. 3 waiting for you in the      |
            | Queue.                                               |
            +------------------------------------------------------+
            +------------------------------------------------------+
            | Your calendar feed                                   |
            | Paste this link into your calendar app. Accepted     |
            | events will appear there.                            |
            | (http://host/api/calendar/…        ) [Copy] [Reset link]
            +------------------------------------------------------+
```

Phone:

```
+--------------------------------------+
| Sail Event               [Sign out]  |
| [Home]  Queue (5)  All events        |
|--------------------------------------|
| +----------------------------------+ |
| | What I'm looking for             | |
| | +------------------------------+ | |
| | | ~~e.g. jazz or folk concerts | | |
| | |  near Paris on weekends,     | | |
| | |  under 40 EUR~~              | | |
| | +------------------------------+ | |
| | [ Save ]  Saved.                 | |
| +----------------------------------+ |
| +----------------------------------+ |
| | How scoring works                | |
| | Every event gets a match score   | |
| | from 0 to 100 against what you   | |
| | wrote above. Events in between   | |
| | wait for you in the Queue tab.   | |
| | 0                            100 | |
| | [####|-------------|###########] | |
| |      ^30           ^70           | |
| | # Rejected                       | |
| | - You decide                     | |
| | # On your calendar               | |
| | Auto-reject below   (30 )        | |
| | Auto-accept above   (70 )        | |
| | [ Save ]  Saved.                 | |
| +----------------------------------+ |
| +----------------------------------+ |
| | Search now                       | |
| | The app also searches            | |
| | automatically every hour.        | |
| | [ Search now ]                   | |
| | Found 9 events, 8 new. 3 waiting | |
| | for you in the Queue.            | |
| +----------------------------------+ |
| +----------------------------------+ |
| | Your calendar feed               | |
| | Paste this link into your        | |
| | calendar app. Accepted events    | |
| | will appear there.               | |
| | (http://host/api/calendar/…    ) | |
| | [Copy]  [Reset link]             | |
| +----------------------------------+ |
+--------------------------------------+
```

Card: What I'm looking for (`data-testid="criteria-card"`)

| Element | Copy | Component | State / behaviour | Empty | Error |
|---|---|---|---|---|---|
| Heading | `What I'm looking for` | `CardTitle` | — | — | — |
| Textarea | placeholder `e.g. jazz or folk concerts near Paris on weekends, under 40 EUR` | `Textarea` `aria-label="What I'm looking for"`, `rows=4` | value = saved criteria on load | placeholder shown | — |
| Save | `Save` (`aria-label="Save criteria"`) | `Button` | `disabled` while in flight; on success show `Saved.` for 2 s next to the button (`<span role="status">`) | — | `Couldn't save. Try again.` in `text-destructive` next to the button |

Card: How scoring works (`data-testid="scoring-card"`) — see §4 for the scale itself

| Element | Copy | Component | State / behaviour | Empty | Error |
|---|---|---|---|---|---|
| Heading | `How scoring works` | `CardTitle` | — | — | — |
| Explainer | `Every event gets a match score from 0 to 100 against what you wrote above. Events in between wait for you in the Queue tab.` | `CardDescription` | — | — | — |
| Scale | see §4 | `ScoreScale` (new) | value = saved thresholds on load; defaults 30 / 70 come from the API for a new user | — | — |
| Save | `Save` (`aria-label="Save scoring"`) | `Button` | `disabled` while in flight or while the scale is invalid; `Saved.` for 2 s on success | — | 400 → `The auto-accept line must be higher than the auto-reject line.` · else → `Couldn't save. Try again.` |

Card: Search now (`data-testid="search-card"`)

| Element | Copy | Component | State / behaviour | Empty | Error |
|---|---|---|---|---|---|
| Heading | `Search now` | `CardTitle` | — | — | — |
| Explainer | `The app also searches automatically every hour.` | `CardDescription` | — | — | — |
| Hint | `Write what you're looking for, then press Search now.` | `<p class="text-sm text-muted-foreground">` | shown only while the criteria textarea is empty | this is the empty state | — |
| Button | `Search now` | `Button` | `disabled` while the criteria textarea is empty or a search is in flight; on click: `await saveCriteria(text)` (the criteria card shows `Saved.`), then `runSearch()`, then `onSearchComplete()`; label `Searching…` in flight | — | criteria save failure → `Couldn't save. Try again.` on the criteria card, search not run |
| Result | `Found 9 events, 8 new. 3 waiting for you in the Queue.` — the second sentence uses the refreshed queue count returned by `onSearchComplete()` and is omitted when it is 0; when `eventsFound === 0`: `Found no events. Try broader criteria.` | `<p data-testid="search-result" role="status">` | shown after a completed search; replaced on the next search; lost on tab change (no last-run endpoint) | — | `Search failed. Try again.` (500 from the run) |

Card: Your calendar feed (`data-testid="calendar-card"`)

| Element | Copy | Component | State / behaviour | Empty | Error |
|---|---|---|---|---|---|
| Heading | `Your calendar feed` | `CardTitle` | always rendered once the URL has loaded | — | — |
| Explainer | `Paste this link into your calendar app. Accepted events will appear there.` | `CardDescription` | — | — | — |
| URL | the feed URL | `Input readOnly` `aria-label="Calendar feed URL"` `data-testid="calendar-url"` | select-all on focus | — | — |
| Copy | `Copy` → `Copied` for 2 s | `Button` `data-testid="copy-calendar-url"` | clipboard write; silent if the API is unavailable | — | — |
| Reset | `Reset link` | `ConfirmAction` (new) wrapping `Button variant=outline`, `data-testid="rotate-calendar-url"` | click → inline prompt `This will break any existing subscription. Reset?` with `[Reset]` (destructive, `data-testid="rotate-confirm-yes"`) `[Cancel]` (outline, `data-testid="rotate-confirm-cancel"`); prompt container `data-testid="rotate-confirm"`; on confirm the URL input updates | — | `Couldn't reset the link. Try again.` |

Layout rules: cards stacked `gap-6`; on phone the Copy / Reset buttons wrap under the URL (`flex-wrap`).

### 3d. Queue

Desktop:

```
 Sail Event   Home [Queue (5)] All events                reviewer [Sign out]
 ---------------------------------------------------------------------------
            Queue
            +------------------------------------------------------+
            | Why: Open-air jazz, Paris, weekend, but 45 EUR       |
            | Jazz in the Park                                     |
            | Match: 72 / 100                                      |
            | When:  Sat 15 Jul 2026, 20:00                        |
            | Where: Hyde Park, London                             |
            | Link:  https://jazzpark.co.uk/summer-2026            |
            | [ Accept ]  [ Reject ]                               |
            +------------------------------------------------------+
            +------------------------------------------------------+
            | Why: ...                                             |
            | ...                                                  |
            +------------------------------------------------------+
```

Phone:

```
+--------------------------------------+
| Sail Event               [Sign out]  |
| Home  [Queue (5)]  All events        |
|--------------------------------------|
| Queue                                |
| +----------------------------------+ |
| | Why: Open-air jazz, Paris,       | |
| | weekend, but 45 EUR              | |
| | Jazz in the Park                 | |
| | Match: 72 / 100                  | |
| | When: Sat 15 Jul 2026, 20:00     | |
| | Where: Hyde Park, London         | |
| | Link: https://jazzpark.co.uk/    | |
| |   summer-2026                    | |
| | [ Accept ]  [ Reject ]           | |
| +----------------------------------+ |
+--------------------------------------+
```

| Element | Copy | Component | State / behaviour | Empty | Error |
|---|---|---|---|---|---|
| Page heading | `Queue` | `<h2>` | — | — | — |
| Loading | `Loading…` | `<p class="text-muted-foreground">` | while the first fetch is pending; prevents the empty state flashing | — | `Couldn't load your queue. Try again.` + `[Try again]` (outline) |
| Cards | see §5 | `EventCard variant="queue"` | sorted by `dateTime` ascending (soonest first, same as All events); removed from the list on a successful decision; header count refreshed via `onQueueChange` | — | per card, see §5 |
| Empty state | `Nothing to decide right now.` / `Events that clearly match go straight to your calendar. Events that clearly don't are rejected. When the app isn't sure, they appear here.` | `<p class="font-medium">` + `<p class="text-sm text-muted-foreground">` | shown when the fetch returned zero queued events | — | — |

### 3e. All events

Desktop:

```
 Sail Event   Home  Queue (3) [All events]                reviewer [Sign out]
 ---------------------------------------------------------------------------
            All events
            +------------------------------------------------------+
            | Introduction to Ceramic Glazing   {On your calendar} |
            | Why: Hands-on craft workshop, matches weekends       |
            | Match: 76 / 100                                      |
            | When:  Sat 14 Nov 2026, 14:00                        |
            | Where: Clay Studio, Austin                           |
            | Link:  https://events.example.com/ceramic-glazing    |
            | [ Remove from calendar ]                             |
            +------------------------------------------------------+
            +------------------------------------------------------+
            | Fermentation Workshop                     {Rejected} |
            | Why: ...                                             |
            | Match: 37 / 100                                      |
            | When / Where / Link                                  |
            +------------------------------------------------------+
            +------------------------------------------------------+
            | Blockchain for Non-Engineers      {Waiting for you}  |
            | ...                                                  |
            +------------------------------------------------------+
```

Phone:

```
+--------------------------------------+
| Sail Event               [Sign out]  |
| Home  Queue (3)  [All events]        |
|--------------------------------------|
| All events                           |
| +----------------------------------+ |
| | {On your calendar}               | |
| | Introduction to Ceramic Glazing  | |
| | Why: Hands-on craft workshop,    | |
| | matches weekends                 | |
| | Match: 76 / 100                  | |
| | When: Sat 14 Nov 2026, 14:00     | |
| | Where: Clay Studio, Austin       | |
| | Link: https://events.example.com | |
| |   /ceramic-glazing               | |
| | [ Remove from calendar ]         | |
| +----------------------------------+ |
+--------------------------------------+
```

| Element | Copy | Component | State / behaviour | Empty | Error |
|---|---|---|---|---|---|
| Page heading | `All events` | `<h2>` | — | — | — |
| Loading | `Loading…` | as 3d | — | — | `Couldn't load your events. Try again.` + `[Try again]` |
| Cards | see §5 | `EventCard variant="all"` | list = API result minus `status === 'new'`, sorted by `dateTime` ascending (soonest first) | — | per card, see §5 |
| Empty state | `No events yet.` / `Write what you're looking for on the Home tab, then press Search now.` | as 3d | shown when the filtered list is empty | — | — |

### 3f. Header (all signed-in screens)

| Element | Copy | Component | State / behaviour |
|---|---|---|---|
| App name | `Sail Event` | `<h1 class="text-xl font-bold">` | static |
| Tabs | `Home` · `Queue` + ` (N)` · `All events` | `Button size=sm`, `variant` = `default` when active else `ghost`; `aria-current="page"` on the active one; inside `<nav aria-label="Main navigation">` | count span `data-testid="queue-count"` rendered only when N > 0; count refreshed on every tab click, after every decision and after a completed search (`refreshQueueCount` returns the new count so Home can print it) |
| Username | the username | `<span class="hidden sm:inline text-sm text-muted-foreground">` | hidden under 640 px |
| Sign out | `Sign out` | `Button variant=outline size=sm` | clears auth, returns to Sign in |

Phone layout: header is `flex-wrap`; row 1 = name + right group, row 2 = tabs (`w-full` on `< sm`).


## 4. Score scale component — `ScoreScale`

File: `frontend/src/components/ScoreScale.tsx`. Built on `@base-ui/react/slider` (installed, unused so far). No wrapper in `components/ui/`.

Props:

| Prop | Type | Meaning |
|---|---|---|
| `lower` | `number` | current auto-reject line |
| `upper` | `number` | current auto-accept line |
| `onChange` | `(lower: number, upper: number) => void` | fires on every thumb move and on every number-input edit (raw values, may be invalid) |

The parent (Home) owns the state, the validity flag and the Save button. `ScoreScale` renders and reports; it does not save.

### Anatomy (top to bottom)

| Part | Rendering |
|---|---|
| Scale ends | `0` left, `100` right, `text-xs text-muted-foreground`, above the bar |
| Bar | `Slider.Root min=0 max=100 step=1 minStepsBetweenValues=1 value=[lowerShown, upperShown]`; `Slider.Control` height 24 px hit area; `Slider.Track` `h-3 rounded-full` painted as three zones (see Zones) |
| Thumbs | two `Slider.Thumb` (index 0 = auto-reject, index 1 = auto-accept), `size-6 rounded-full bg-background border-2 border-primary shadow`, `focus-visible:ring-3 ring-ring/50` |
| Thumb values | the current value under each thumb (`^30`, `^70` in the wireframe): `<span aria-hidden>` positioned at `left: value%`, `text-xs` |
| Zone legend | three labels: `Rejected` · `You decide` · `On your calendar`. Desktop: one row under the bar, each label centred under its zone when the zone is ≥ 18 % wide, otherwise it drops to the legend row. Phone: always a vertical legend row, each label with a 12 px colour swatch |
| Number inputs | `Label htmlFor` + `Input type=number inputMode=numeric min max step=1 class="w-20"` for `Auto-reject below` (`id=auto-reject`) and `Auto-accept above` (`id=auto-accept`); side by side on desktop, stacked on phone |
| Validation line | `<p role="alert" class="text-sm text-destructive">The auto-accept line must be higher than the auto-reject line.</p>` rendered only while invalid |

### Zones

| Zone | Range | Fill | Label |
|---|---|---|---|
| Rejected | 0 → lower | `bg-destructive/20` | `Rejected` |
| You decide | lower → upper | `bg-muted` with `bg-[repeating-linear-gradient(...)]` hatch of `foreground/10` | `You decide` |
| On your calendar | upper → 100 | `bg-primary` | `On your calendar` |

Zone fills are painted on the track with three absolutely positioned `div`s whose widths are `lower%`, `(upper-lower)%`, `(100-upper)%`. Colour is never the only carrier of meaning: every zone has a visible text label, every thumb has a visible number.

### Interaction

| Input | Behaviour |
|---|---|
| Pointer drag on a thumb | moves that thumb; Base UI keeps `lower ≤ upper - 1` (`minStepsBetweenValues=1`), so thumbs cannot cross or touch by dragging |
| Pointer click on the track | moves the nearest thumb to that point (Base UI default) |
| Keyboard on a focused thumb | `←/↓` −1, `→/↑` +1, `Shift+arrow` ±10 (Base UI `largeStep`), `Home` → min, `End` → max; same no-cross rule |
| Typing in `Auto-reject below` | raw value goes to the parent; `max` attribute = `upper - 1`; the bar shows `lowerShown = min(lower, upper - 1)` so it never draws crossed |
| Typing in `Auto-accept above` | raw value goes to the parent; `min` attribute = `lower + 1`; bar shows `upperShown = max(upper, lower + 1)` |
| Out-of-range typing (e.g. 120, −5) | clamped to 0–100 on blur; the bar shows the clamped value immediately |
| Validity | `invalid = !(0 ≤ lower < upper ≤ 100)`; while invalid: validation line shown, Save disabled (parent) |
| Save (parent) | `PUT /api/thresholds {lowerThreshold, upperThreshold}`; success → state = response, `Saved.` 2 s; 400 → validation line copy; other → `Couldn't save. Try again.` |
| Unsaved edits | nothing warns; the values on the bar are the draft until Save. Reload discards the draft (spec criterion 7 verifies by refreshing) |

Semantics note for the engineer: the backend treats a score equal to a cut-off as "in between" (queued). The labels `Auto-reject below` / `Auto-accept above` are literally true; do not render `≤`/`≥` anywhere.

### Accessibility

| Item | Spec |
|---|---|
| Roles | each thumb renders a native `<input type="range">` → `role=slider`; `getAriaLabel` returns `Auto-reject below` for index 0 and `Auto-accept above` for index 1; `getAriaValueText` returns `${value} out of 100` |
| Linked inputs | `Label htmlFor` pairs; accessible names identical to the thumb labels so screen-reader users hear the same two names twice (bar, inputs) |
| Group | the whole component wrapped in `<fieldset>` with `<legend class="sr-only">Score cut-offs</legend>` |
| Focus order | thumb 0 → thumb 1 → `Auto-reject below` input → `Auto-accept above` input → Save |
| Live regions | validation line `role=alert`; `Saved.` `role=status` |
| Contrast | zone labels and thumb values are `text-foreground` / `text-muted-foreground` on `bg-card`, not painted on the fills; thumb = `bg-background` with `border-primary` ring (≥ 3:1 against every zone fill in both themes since `--primary` is near-black light / near-white dark) |
| Hit targets | thumbs 24 px, control strip 24 px tall; inputs are the keyboard and switch-access fallback |
| Reduced motion | no animation on this component |

### Mobile

| Item | Spec |
|---|---|
| Width | bar is `w-full`; at 360 px the 1-point step is ≈ 3 px, fine for drag, not for precision → the number inputs are the precision path and sit directly under the bar |
| Legend | vertical list with swatches (labels under narrow zones would overlap) |
| Touch | Base UI handles pointer events; page scroll is not hijacked outside the control strip (`touch-action: none` only on the thumbs) |
| Inputs | `inputMode=numeric` brings up the number keypad |


## 5. Event card — `EventCard`

File: `frontend/src/components/EventCard.tsx` (redesigned, not replaced). Props: `event`, `variant: 'queue' | 'all'`, `onDecide?: (id, 'accepted' | 'rejected') => Promise<void>`.

### Layout order

| # | Queue variant | All-events variant |
|---|---|---|
| 1 | `Why:` line, `font-medium`, full width | title (`CardTitle`) + status badge in `CardAction` (badge above the title on phone via `flex-wrap`) |
| 2 | title (`CardTitle`) | `Why:` line |
| 3 | `Match: 72 / 100` | `Match: 76 / 100` |
| 4 | `When:` formatted `dateTime` (`Intl.DateTimeFormat` medium date, short time, `data-testid="event-datetime"`) | same |
| 5 | `Where:` place | same |
| 6 | `Link:` full URL, `break-all underline`, `target=_blank rel=noopener noreferrer` | same |
| 7 | `[Accept]` default · `[Reject]` destructive, `size=sm` | `[Remove from calendar]` only when status is `accepted` (via `ConfirmAction`) |

Field labels are `<span class="font-medium">` followed by the value, one `<p>` per line, `text-sm`. The card keeps `data-testid="event-card-{id}"`.

### Badge wording (all-events variant only)

| `status` | Badge text | `Badge variant` |
|---|---|---|
| `accepted` | `On your calendar` | `default` |
| `rejected` | `Rejected` | `destructive` |
| `queued` | `Waiting for you` | `secondary` |
| `new` | not rendered — the All events page filters these out before rendering | — |

### Actions and feedback

Decision: not optimistic. Reasons: one request per click, the mock resolves instantly, and a rollback path is more code than a disabled state. The user still gets immediate feedback because the card changes on the click.

| Action | Click | In flight | Success | Failure |
|---|---|---|---|---|
| Accept (queue) | `onDecide(id, 'accepted')` | both buttons `disabled`; Accept label `Accepting…` | parent removes the card from the list and refreshes the header count | buttons re-enabled; inline `<p role="alert" class="text-sm text-destructive">Couldn't save your decision. Try again.</p>` under the buttons |
| Reject (queue) | `onDecide(id, 'rejected')` | both `disabled`; Reject label `Rejecting…` | same | same |
| Remove from calendar (all) | first click → inline `Remove this event from your calendar?` `[Remove]` destructive `[Cancel]` outline | `Removing…`, both disabled | parent replaces the event with the response: badge flips to `Rejected`, button disappears | `Couldn't remove it. Try again.`; prompt stays open |

No toasts anywhere: there is no toast primitive in `components/ui`, and inline feedback lands where the eye already is.


## 6. Copy table

Every string the UI shows. Terminology from the spec is taken as given.

| Where | String |
|---|---|
| Page `<title>` (index.html) | `Sail Event` |
| Header | `Sail Event` · `Home` · `Queue` · `Queue (N)` · `All events` · `Sign out` |
| Sign in | `Sign in` (heading, button) · `Username` · `Password` · `Signing in…` · `No account? Create one` |
| Sign in errors | `Wrong username or password.` · `Too many attempts. Try again later.` · `Couldn't sign in. Try again.` |
| Create account | `Create account` (heading, button) · `Username` · `Password` · `Invitation code` · `Creating…` · `Already have an account? Sign in` |
| Create account errors | `Couldn't create your account. That username may already be taken.` · `That invitation code isn't valid.` · `Too many attempts. Try again later.` · `Couldn't create your account. Try again.` |
| Criteria card | `What I'm looking for` · placeholder `e.g. jazz or folk concerts near Paris on weekends, under 40 EUR` · `Save` · `Saved.` · `Couldn't save. Try again.` |
| Scoring card | `How scoring works` · `Every event gets a match score from 0 to 100 against what you wrote above. Events in between wait for you in the Queue tab.` · `0` · `100` · `Auto-reject below` · `Auto-accept above` · `Rejected` · `You decide` · `On your calendar` · `Score cut-offs` (sr-only legend) · `{n} out of 100` (aria-valuetext) · `The auto-accept line must be higher than the auto-reject line.` · `Save` · `Saved.` · `Couldn't save. Try again.` |
| Search card | `Search now` (heading, button) · `The app also searches automatically every hour.` · `Write what you're looking for, then press Search now.` · `Searching…` · `Found {found} events, {new} new.` · ` {queued} waiting for you in the Queue.` (appended when queued > 0) · `Found no events. Try broader criteria.` · `Search failed. Try again.` |
| Calendar card | `Your calendar feed` · `Paste this link into your calendar app. Accepted events will appear there.` · `Calendar feed URL` (aria-label) · `Copy` · `Copied` · `Reset link` · `This will break any existing subscription. Reset?` · `Reset` · `Cancel` · `Couldn't reset the link. Try again.` |
| Queue page | `Queue` · `Loading…` · `Nothing to decide right now.` · `Events that clearly match go straight to your calendar. Events that clearly don't are rejected. When the app isn't sure, they appear here.` · `Couldn't load your queue. Try again.` · `Try again` |
| All events page | `All events` · `Loading…` · `No events yet.` · `Write what you're looking for on the Home tab, then press Search now.` · `Couldn't load your events. Try again.` · `Try again` |
| Event card | `Why:` · `Match: {score} / 100` · `When:` · `Where:` · `Link:` · `Accept` · `Accepting…` · `Reject` · `Rejecting…` · `Remove from calendar` · `Remove this event from your calendar?` · `Remove` · `Removing…` · `Cancel` · `Couldn't save your decision. Try again.` · `Couldn't remove it. Try again.` |
| Badges | `On your calendar` · `Rejected` · `Waiting for you` |

Pluralisation: `Found 1 events, 1 new.` is acceptable for the MVP; do not add a pluraliser.


## 7. Component inventory

New dependencies: none. New shadcn wrappers: none.

### New components

| File | Purpose | Built from |
|---|---|---|
| `frontend/src/components/ScoreScale.tsx` | the 0–100 bar, two thumbs, zones, number inputs, validation line (§4) | `@base-ui/react/slider`, `Input`, `Label`, Tailwind |
| `frontend/src/components/ConfirmAction.tsx` | a button that swaps itself for an inline `prompt [confirm] [cancel]` row; used by Reset link and Remove from calendar | `Button`; props `label`, `prompt`, `confirmLabel`, `onConfirm: () => Promise<void>`, `testId` |

### Existing files changed

| File | Change |
|---|---|
| `frontend/index.html` | `<title>Sail Event</title>` |
| `frontend/src/services/http.ts` | (1) the 401 token-clear + `window.location.reload()` runs only when a token is present: `if (res.status === 401 && token())` — a wrong password on Sign in must reach the page as an error; (2) attach `status` to the thrown error: `const err = new Error(detail) as Error & { status: number }; err.status = res.status; throw err` — one line, lets pages pick 401/403/409/429 copy. `mock.ts` unchanged (it never fails) |
| `frontend/src/App.tsx` | tab labels, `Sign out`, responsive header, `aria-current`, username hidden on phone; `refreshQueueCount` returns the count and is passed to `MainPage` as `onSearchComplete` |
| `frontend/src/pages/LoginPage.tsx` | copy, status-based error copy, in-flight state, autocomplete attributes |
| `frontend/src/pages/RegisterPage.tsx` | copy, status-based error copy, in-flight state |
| `frontend/src/pages/MainPage.tsx` | four cards per §3c, `ScoreScale`, `ConfirmAction`, `Saved.` pattern, `Search now` saves the draft then searches, prop `onSearchComplete: () => Promise<number>`; delete the dead `!embedded` header branch and the `embedded` prop (App always passes it) |
| `frontend/src/pages/QueuePage.tsx` | loading / error / empty states, `onDecide` wiring |
| `frontend/src/pages/EventsPage.tsx` | heading, filter out `new`, sort by `dateTime`, loading / error / empty states, remove-from-calendar wiring |
| `frontend/src/components/EventCard.tsx` | §5 |
| `frontend/src/components/ui/*` | untouched |
| `frontend/src/index.css` | untouched (theme is P2) |

### Tests touched (unit, beside the code)

| File | Why |
|---|---|
| `App.test.tsx` | selectors `Login` → `Sign in`, `Register` → `Create account`, `Logout` → `Sign out`, `Search Criteria` → `What I'm looking for`, `Criteria` → `What I'm looking for`, `Save Criteria` → `Save criteria` (aria-label), `Lower Threshold` → `Auto-reject below`, `Upper Threshold` → `Auto-accept above`, `Save Thresholds` → `Save scoring`, validation copy, `Dashboard`/`Events` → `Home`/`All events`, `12 events found` → `Found 12 events, 4 new.` |
| `MainPage.test.tsx` | `Subscribe from your calendar app` → new explainer; `Are you sure?` → `This will break any existing subscription. Reset?`; drop `embedded` |
| `EventCard.test.tsx` | `85` → `Match: 85 / 100`; `queued` → `Waiting for you` with `variant="all"`; add a queue-variant test asserting Why precedes the title in DOM order |
| `QueuePage.test.tsx` | unchanged selectors (`event-card-*`, first/second button) still hold; add in-flight disabled assertion |
| `EventsPage.test.tsx` | `new` event (`evt-5`) must not render; badges by new wording |
| `RegisterPage.test.tsx` | `Registration code` → `Invitation code`, button copy |


## 8. Implementation plan

Five issues, in dependency order. Each is one engineer session. Labels: `mvp`.

### Issue A — Copy and navigation: Sign in, Create account, header, error status

Goal: every string outside Home and the event lists matches the spec, and HTTP errors carry their status so pages can choose copy.

- [ ] `index.html` title is `Sail Event`
- [ ] `http.ts`: the 401 token-clear and `window.location.reload()` run only when a token is present in storage (`if (res.status === 401 && token())`); a unit test with no token in `localStorage` and a mocked 401 asserts the error is thrown and `location.reload` is not called
- [ ] Sign in screen: heading and button `Sign in`, link `No account? Create one`, app name above the card; 401 shows `Wrong username or password.` (unit test with no token in storage), 429 shows `Too many attempts. Try again later.`
- [ ] Create account screen: heading and button `Create account`, field `Invitation code` when required, link `Already have an account? Sign in`; 409 shows `Couldn't create your account. That username may already be taken.`, 403 shows `That invitation code isn't valid.`
- [ ] Submit buttons are disabled and read `Signing in…` / `Creating…` while the request is in flight
- [ ] `http.ts` errors expose `status`; a unit test asserts `status === 401` on a mocked 401 response
- [ ] Header tabs read `Home`, `Queue` / `Queue (N)`, `All events`; active tab has `aria-current="page"`; `Sign out` replaces `Logout`; username hidden under 640 px
- [ ] `App.test.tsx`, `RegisterPage.test.tsx` updated; `npm test` green

### Issue B — Event card redesign, Queue and All events pages

Goal: cards lead with Why, show `Match: NN / 100`, use the three badge wordings, and All events can remove an accepted event.

- [ ] `EventCard` has `variant` `queue` | `all`; queue variant renders `Why:` before the title (DOM order asserted in a test)
- [ ] Score renders as `Match: NN / 100`; labels `When:`, `Where:`, `Link:`; link has `break-all`
- [ ] Badges: `accepted` → `On your calendar`, `rejected` → `Rejected`, `queued` → `Waiting for you`; `new` never rendered on All events
- [ ] Accept / Reject disable both buttons and show `Accepting…` / `Rejecting…` until the request resolves; on failure an inline `Couldn't save your decision. Try again.` appears and buttons re-enable
- [ ] `ConfirmAction` component exists; `Remove from calendar` on accepted cards shows `Remove this event from your calendar?` `[Remove]` `[Cancel]`; confirming calls `decideEvent(id, 'rejected')` and the badge flips to `Rejected` in place
- [ ] Queue page: heading `Queue`, `Loading…` while fetching, empty state text per spec; All events page: heading `All events`, sorted by `dateTime` ascending, empty state per spec
- [ ] Header count decrements after a decision (existing behaviour kept; `App.test` tab test passes)
- [ ] `EventCard.test`, `QueuePage.test`, `EventsPage.test` updated; `npm test` green

### Issue C — Home: criteria, search and calendar cards

Goal: Home reads as the spec's four cards (scoring card still with the two number inputs, no bar yet).

- [ ] Card `What I'm looking for`: textarea `aria-label="What I'm looking for"` with the spec placeholder; `Save` (`aria-label="Save criteria"`) shows `Saved.` for 2 s; failure shows `Couldn't save. Try again.`
- [ ] Card `How scoring works`: explainer line; inputs labelled `Auto-reject below` and `Auto-accept above`; `Save` (`aria-label="Save scoring"`); validation copy `The auto-accept line must be higher than the auto-reject line.` shown live while `lower >= upper` and Save disabled
- [ ] Card `Search now`: explainer `The app also searches automatically every hour.`; hint `Write what you're looking for, then press Search now.` and disabled button only while the criteria textarea is empty; clicking `Search now` first saves the textarea draft (`saveCriteria`, criteria card shows `Saved.`) then runs the search; `Searching…` in flight; result `Found {n} events, {m} new.` in `data-testid="search-result"`, with ` {q} waiting for you in the Queue.` appended when q > 0 and `Found no events. Try broader criteria.` when n is 0; `Search failed. Try again.` on error
- [ ] `MainPage` takes `onSearchComplete: () => Promise<number>`; `App` passes `refreshQueueCount` (which now returns the queued count); after a search the header `Queue (N)` count is fresh without a tab click (unit test in `App.test.tsx`)
- [ ] Card `Your calendar feed`: explainer per spec; `Copy` / `Copied`; `Reset link` via `ConfirmAction` with prompt `This will break any existing subscription. Reset?` and buttons `Reset` / `Cancel`; existing `data-testid`s kept
- [ ] Dead `!embedded` branch and `embedded` prop removed from `MainPage`
- [ ] Cards carry `data-testid` `criteria-card`, `scoring-card`, `search-card`, `calendar-card`
- [ ] `App.test.tsx` and `MainPage.test.tsx` updated; `npm test` green

### Issue D — Score scale component

Goal: the scoring card shows the 0–100 bar with two draggable cut-offs and three labelled zones, wired to the same state as the number inputs.

- [ ] `ScoreScale.tsx` built on `@base-ui/react/slider` with `min=0 max=100 step=1 minStepsBetweenValues=1`, two thumbs, three zone fills sized by the values
- [ ] Thumbs are accessible as `role=slider` named `Auto-reject below` and `Auto-accept above` with `aria-valuetext` `{n} out of 100`; arrow keys move by 1, Shift+arrow by 10, Home/End to the ends
- [ ] Dragging cannot cross the thumbs; typing a crossing value in a number input shows the validation line, disables Save, and the bar draws the clamped pair
- [ ] Zone labels `Rejected`, `You decide`, `On your calendar` are visible text; under 640 px they render as a vertical legend with swatches
- [ ] Moving a thumb and pressing Save persists: after reload the thumbs and inputs show the saved values (unit test through the mock; e2e in Issue E)
- [ ] Component wrapped in `<fieldset>` with sr-only legend `Score cut-offs`; focus order thumb 0 → thumb 1 → inputs → Save
- [ ] `ScoreScale.test.tsx` covers: initial render at 30/70, keyboard move, crossing via input shows the error, `onChange` payload; thumbs are queried with `getByRole('slider', { name })` and number inputs with `getByRole('spinbutton', { name })` (both share the accessible name, so `getByLabelText` would match two elements)
- [ ] `npm test` green; `make test` green

### Issue E — Playwright journeys on the new copy

Goal: `e2e/journeys.spec.ts` passes against the redesigned UI and covers the scale.

Selectors that must change (current → new):

| Line | Current | New |
|---|---|---|
| 16, 67, 90 | `getByRole("button", { name: "Register" })` (link on Sign in) | `getByRole("button", { name: "Create one" })` |
| 19, 70, 93 | `getByRole("button", { name: "Register", exact: true })` | `getByRole("button", { name: "Create account" })` |
| 22, 72, 95 | `getByRole("heading", { name: "Sail Event" })` | unchanged |
| 25, 74 | `getByLabel("Criteria")` | `getByLabel("What I'm looking for")` |
| 26, 75 | `getByRole("button", { name: "Save Criteria" })` | `getByRole("button", { name: "Save criteria" })` |
| 29, 76 | `getByRole("button", { name: "Search now" })` | unchanged |
| 30, 77 | `getByText("Search complete")` | `getByText(/Found \d+ events, \d+ new\./)` |
| 33 | `getByRole("button", { name: /Queue/ })` | unchanged |
| 34 | `getByRole("heading", { name: "Queue" })` | unchanged |
| 37, 38 | `getByRole("button", { name: "Accept" })` / `"Reject"` | unchanged |
| 48, 82, 97 | `getByRole("button", { name: "Events" })` | `getByRole("button", { name: "All events" })` |
| 49, 98 | `getByRole("heading", { name: "Events" })` | `getByRole("heading", { name: "All events" })` |
| 52 | `getByText("accepted")` | `getByText("On your calendar")` |
| 53 | `getByText("rejected")` | `getByText("Rejected")` |
| 83 | `getByText(/score/i)` | `getByText(/Match: \d+ \/ 100/)` |
| 99 | `getByText("No events yet.")` | unchanged |

- [ ] Journey 1 and Journey 2 updated per the table and green under `make test-e2e`
- [ ] Journey 1 additionally: focus `getByRole("slider", { name: "Auto-accept above" })`, press `ArrowLeft` ×5, click `Save scoring`, reload, assert `getByRole("spinbutton", { name: "Auto-accept above" })` has value 65 (never `getByLabel`: the thumb and the number input share the name, strict mode would fail)
- [ ] Journey 1: after `Search now`, assert the header button `getByRole("button", { name: /Queue \(\d+\)/ })` is visible before any tab click
- [ ] Journey 1 additionally: after accepting, open All events and assert the accepted card has a `Remove from calendar` button; click it, click `Remove`, assert the card's badge reads `Rejected`
- [ ] Journey 2: unchanged assertion that the second user sees `No events yet.`
- [ ] No selector in the file references `Register` as a submit, `Save Criteria`, `Search complete`, `Events` alone, `accepted`, `rejected` or `/score/i`


## 9. Risks and decisions

Decisions made here, without asking:

| # | Decision | Strongest fact against it |
|---|---|---|
| 1 | Scale uses `@base-ui/react/slider` (installed, unused) rather than a hand-rolled bar | The project has never rendered this primitive; styling parts (`Slider.Track`, `Slider.Indicator`) with Tailwind is new ground for the engineer |
| 2 | Decisions (accept / reject / remove) are not optimistic: disabled buttons + in-flight label, card removed on success | A slow network shows a greyed card for the round-trip instead of an instant disappearance |
| 3 | Confirmations stay inline (`ConfirmAction`), no AlertDialog | Two confirmations on one page could both be open at once; acceptable |
| 4 | Header tabs stay `role=button` (no Tabs primitive) so e2e and unit selectors `getByRole("button", { name: /Queue/ })` survive | Semantically a `tablist` would be more accurate |
| 5 | Both Home Save buttons show `Save` but carry `aria-label` `Save criteria` / `Save scoring` so tests and screen readers can tell them apart | aria-label overrides the visible text; it still contains the visible word `Save`, so WCAG 2.5.3 holds |
| 6 | All events sorted by event `dateTime` ascending (soonest first); spec says "most recent, newest first" | The API exposes no `createdAt`, so "newest found" is not computable; soonest-first is what a calendar user needs |
| 7 | `new` events filtered out client-side on All events | `new` events persist until the next run re-scores them (`pipeline.py:77-84`), so after a failed scoring the user sees fewer events than `Found N events` claimed until the next hourly run; the filter hides that failure |
| 8 | Sign-in / register 429 copy is `Too many attempts. Try again later.`, not the spec's `Try again in a minute.` | Deviates from the spec; the backend window is 15 minutes (sign-in) and 1 hour (register), so "a minute" would be false |
| 9 | `http.ts` attaches `status` to its thrown error (one line) | Touches a service file in a UX issue; without it every error is a generic string |
| 10 | Calendar card always rendered (API always returns a URL); spec's "hidden on first visit" dropped | A first-time user sees a feed link before any event exists; the explainer sentence covers it |
| 11 | Reversed after review (S3): `Search now` saves the textarea draft first, then searches; disabled only while the textarea is empty. The hint `Write what you're looking for, then press Search now.` is now literally true | Two requests per click; a criteria save failure stops the search and the error shows on the criteria card, not the search card |
| 12 | Search result line is not persisted across tabs (no last-run endpoint, spec §9 says nice-to-have) | The user loses `Found 9 events, 8 new.` on the first tab switch |
| 13 | Queue variant puts `Why` before the title (spec criterion 9) even though the brief's layout order lists title first; all-events variant keeps title first | The two variants differ in order; one component, one `variant` prop |
| 14 | Field labels `When:` / `Where:` instead of `Date:` / `Place:` | Spec lists "Date, Place" as content, not as labels; the brief says when/where |
| 15 | Full URL shown with `break-all`, no hostname shortening | Long URLs read badly on phone; zero logic was preferred |
| 16 | Loading state `Loading…` added to Queue and All events | Flashes for a frame on the mock; without it the empty state flashes instead, which misleads |
| 17 | No pluraliser (`Found 1 events`) | Reads wrong once in a while |
| 18 | Dead `!embedded` branch deleted from `MainPage` | Unrelated cleanup inside Issue C; it is on the file already being rewritten |
| 19 | Queue `Reject`: no confirmation, no undo; the API refuses re-decision of a rejected event (`events.py:68`); accepted because confirm-per-event defeats the daily job | `Remove from calendar` reaches the same end state with a confirmation; the asymmetry is deliberate: that one is a reversal of a prior yes |

Risks:

| Risk | Mitigation |
|---|---|
| Base UI slider's hidden `<input type="range">` may not be found by Playwright's `getByRole("slider", { name })` if `getAriaLabel` is not applied per thumb | Issue D criterion requires the role/name; Issue E verifies it |
| `minStepsBetweenValues` keeps thumbs apart by drag, but controlled `value` with crossed numbers from the inputs could log a Base UI warning | The bar always receives the clamped pair (`lowerShown`, `upperShown`) |
| Spec criterion 7 ("verify by refreshing") depends on `GET /api/thresholds` round-trip, already in place | Covered by the e2e step in Issue E |
| Visual theme (P2) will restyle zone fills; the three fills use only `--destructive`, `--muted`, `--primary` tokens | Token-only colours, no hard-coded values |

### Review applied (`_docs/ux-design-review.md`)

| Finding | What changed |
|---|---|
| B1 | facts table: 401 reload fact added; §7 `http.ts` row: 401 reload guarded by `token()`; Issue A: guard line + unit test with no token |
| B2 | §3f: count refreshed after a completed search; §3c Result row and wireframes: `Found 9 events, 8 new. 3 waiting for you in the Queue.`; Issue C: `onSearchComplete` / `refreshQueueCount` line; §2 first-run step 3; Issue E: header count assertion |
| S1 | §3d empty state and §6: "hidden" → "rejected" (spec §2 and §3d edited to match) |
| S2 | §3c Explainer, wireframes and §6: second sentence `Events in between wait for you in the Queue tab.` (spec §3c edited to match) |
| S3 | decision 11 reversed: `Search now` saves the draft then searches, disabled only while the textarea is empty; §3c Hint/Button rows, §2 first-run, §7 `MainPage` row, Issue C (spec §4 steps collapsed to match) |
| S4 | Issue E and Issue D tests: number inputs queried as `spinbutton`, thumbs as `slider` |
| S5 | §3d Cards row: sorted by `dateTime` ascending; §2 pointer → §3d |
| S6 | Sign-in link `No account? Create one` in §3a wireframes, §3a table, §6, Issue A, Issue E rows 16 / 67 / 90 (spec §3a edited to match); off-by-one 91 → 90 fixed |
| N1 | §3c Result row and §6: `Found no events. Try broader criteria.` when `eventsFound === 0` |
| N2 | decision 19 added (Queue Reject: no confirm, no undo) |
| N5 | decision 7 counter-fact corrected (`new` persists until the next run) |
| N6 | spec §9: "Last search result" promoted to first post-P1 API item |
| N3, N4 | not applied: title-as-link and per-card mini track are layout changes across §5, tests and App state, not one-line edits; left for the owner |
