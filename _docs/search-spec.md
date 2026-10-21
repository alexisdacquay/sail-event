# Search and scoring — specification (v2)

What the search must deliver. The how is in `search-design.md`.

Revision 2026-10-18 (owner): the user's criteria text is the search query, sent to the engine as written; the code adds nothing, translates nothing, and never stops a run for a missing city or country. The extractor records title, description, start with time zone, city, country, link; no price. The judge scores topic, place and dates against the criteria; there is no price or budget rule and no budget cap. Rows below that say otherwise (place "run stops", query strategy bullets, price rows, C3/C10 "run stops") are superseded.
Revision 2026-10-21 (owner): when the criteria text names no place (no city, no country), nothing is accepted automatically, whatever the user's thresholds: events scoring at or above the upper threshold go to the review queue with their score unchanged; the lower threshold still rejects. The code never asks the user for a place and never adds one to the query.
Reference case throughout: criteria `jazz in Berlin (Germany) next week (19-21st October 2026)`, run on 2026-10-18 in `Europe/Berlin`.

First fact: the deployed result ("Outdoor Photography Meetup", Portland) is a configuration state, not a scoring defect. Prod has no keys, so `SEARCH_PROVIDER` and `SCORER` fell back to the canned fixture list and the `md5(title)` scorer; the Berlin text never reached a search engine or a model. This spec makes that state impossible to miss (§9: a run on fixture or fake adapters in production is recorded as refused) and then defines quality once real adapters run.

## 1. The job

| Input | Output |
|---|---|
| One free-text criteria per user | A list of real, upcoming events that fit the criteria's place, time, topic and budget |
| | Each event: title, start date-time with time zone, city and country, link, price when known, score 0–100, one sentence the user understands |

- The score decides: above the upper cut-off → calendar; below the lower → gone; between → queue.
- The sentence is the user's only explanation. It names the facts the score rests on.
- Nothing reaches the user that the pipeline could have checked in code: date, place, past, duplicate, non-event.

## 2. Quality definition

| Measure | Target | How measured |
|---|---|---|
| Precision of auto-accepted | ≥ 90 % true fits | owner labels the weekly smoke run |
| Precision of queued | ≥ 70 % plausible | same |
| Wrong-country event in accepted or queued | 0 | golden set in CI + smoke |
| Event outside the date window in accepted or queued | 0 | same |
| Past event anywhere visible | 0 | same |
| Non-event (article, venue page, listicle) visible | 0 | same |
| Duplicate (same event, two links) visible | 0 | same |
| Recall for the reference case | ≥ 3 distinct real jazz events in Berlin in the window | smoke run |

False positive classes, in the order they must be caught:

| Class | Example | Caught by |
|---|---|---|
| Wrong city / country | "Jazz Under the Stars", Chicago | place filter (code) |
| Wrong dates | "Jazzfest Berlin", 5 Nov 2026 for a 19–21 Oct window | date filter (code) |
| Past event | "Jazz at b-flat", 17 Oct 2026 | past filter (code) |
| Not an event | "Top 10 jazz clubs in Berlin" | extraction returns no event |
| Duplicate | same event, two URLs or two listings | dedup (code) |
| Off-topic | "Techno night", Berlin, 20 Oct | judge (low score) |
| Over budget | 120 EUR ticket against "under 30 EUR" | judge (capped score) |

The user must never see: a score without a reason; a date without a time zone; a place without a country; an event the code could have excluded; a run that silently did less than it says (fixture data in production, a budget cut not reported).

## 3. Criteria understanding

Facets extracted once per criteria text, stored, re-extracted when the text changes.

| Facet | Example from reference case | When missing |
|---|---|---|
| Place: city, country (ISO-2), region | Berlin, DE | No queries can be targeted → the run stops with the reason "add a place" unless a format is `online` |
| Radius (km) | none | City match is exact; nearby cities are excluded |
| Date window, absolute | 2026-10-19 → 2026-10-21 | Relative expression used; both missing → now → now + 30 days |
| Date window, relative | `next_week` | Absolute wins when both are present |
| Topics | jazz | Whole text becomes the topic; the judge carries the weight |
| Topics in the place's language | Jazz, Jazzkonzert | Queries run in English only |
| Formats | none | Any format |
| Budget: max amount, currency, free-only | none | No budget judgement |
| Language of the place | de | Queries in English only |
| Other constraints (free text the facets cannot hold) | none | Passed to the judge verbatim, e.g. "Saturdays only", "English-friendly" |

Relative dates:

| Expression | Resolves to (user's time zone, ISO weeks Mon–Sun) |
|---|---|
| today / tomorrow | that calendar day |
| this week / next week | the current / following ISO week, full |
| this weekend / next weekend | Sat 00:00 → Sun 23:59 of the current / following week |
| this month / next month | the calendar month |
| next N days | now → now + N days |
| a season or holiday | the parser writes absolute dates |

- Resolution happens at run time, every run, in the user's time zone, never at parse time.
- Window start is clipped to now: an event that has already ended is past (§6 has the end-of-day rule).
- Window end before now (the absolute dates have passed): the run continues; the per-event past filter and the judge handle dates. Facets are parsed once per criteria text; relative date words resolve against now on every run; absolute dates are fixed.
- The user's time zone is `UTC` until their first criteria save from the new UI; the UI says so.
- The reference case resolves to 2026-10-19 00:00 → 2026-10-21 23:59 Europe/Berlin because the absolute dates win over "next week" (19–25 Oct).

## 4. Candidate discovery

Sources, from the owner's keys:

| Provider | Use | Why / why not |
|---|---|---|
| Tavily | primary (key already on Render) | already integrated and contract-tested; returns page content, which extraction needs; has `country` (a boost by country name, not a filter), `language`, `time_range`/`start_date`/`end_date` and domain controls |
| Brave Search | optional, selectable | independent index; first-party `country`, `search_lang` and date-range `freshness` controls; cheap |
| Serper | not now | Google coverage is the best for local events, but two providers is the cap; revisit if Tavily recall fails the smoke target |
| Exa | no | semantic search over articles, weak on dated local listings |
| Linkup | no | overlaps Tavily |
| Firecrawl, Nimbleway | no | page fetching, not search; Tavily's raw content covers the need |

Query strategy:

- The criteria text is the query, verbatim, one call per run (revision 2026-10-18). No templates, no translation, no country or language parameter, no freshness filter. What the engine returns is what the extractor reads; the place filter in code (city and country required on the event) and the judge do the rest.

Result budget per run:

| Limit | Default | Scheduled runs |
|---|---|---|
| Queries per run | 6 | 2, rotating through the planned list across hours |
| Results per query | 6 | same |
| Results sent to extraction | 36, minus links already known for the user | same |
| Events judged | `MAX_EVENTS_PER_RUN` = 50 | same |

## 5. Event extraction

From one search result to zero or more events.

| Field | Rule |
|---|---|
| title | the event's own name, not the page title when they differ |
| start | local date-time; date alone allowed; missing date → not an event |
| time zone | IANA zone derived from the city (the model does the lookup); required |
| end | optional |
| place | city and country (ISO-2) required; venue and street optional, never required |
| link | the page URL, or the deeper event URL when the page is a listing |
| description | one line, ≤ 200 characters, from the page |
| confidence | 0–1; below 0.5 the event is dropped and counted |

- Owner rule (2026-10-18): every stored event has a title, a description, a start date-time with its time zone, a city and a country. An extracted event missing any of these is dropped and counted (`filtered_incomplete`), never stored. Language of the event is not tracked.

- A page with many events (venue programme, listing): up to 10 events whose dates fall in the window; the rest ignored.
- A page with none (article, listicle, venue homepage, radio stream): no event, counted as non-event.
- The extractor is told today's date, the window and the target place so it picks the right occurrence from a programme page; it never decides fit.

## 6. Hard filters before scoring

Applied in code, in this order, each with a count on the run:

| Filter | Rule | Count |
|---|---|---|
| Past | the event has ended: `end < now`, or when there is no end, `start < now` for timed events and `start day 23:59 < now` for date-only events | `filtered_past` |
| Date window | no overlap with the window: `start > window end` or `(end or start) < window start`, compared in the event's zone; a festival 17–22 Oct overlaps a 19–21 Oct window and is kept | `filtered_date` |
| Place | country unknown; or country ≠ criteria country; or city ≠ criteria city when no radius is given; unknown city with the right country passes to the judge | `filtered_place` |
| Non-event | extraction returned no event, or confidence < 0.5 | `filtered_non_event` |
| Duplicate by link | the event's canonical link and date already stored for the user, or seen earlier in the run | `filtered_duplicate` |
| Duplicate by title+date | same calendar date and near-identical title (stopwords removed; ≥ 0.8 token overlap, or one title's tokens inside the other's when the shorter has at least 3 tokens) against the user's stored events and the run | `filtered_duplicate` |

- A page already stored as a single-event page is dropped before extraction, so no model call is spent on it.
- A listing page (venue programme, weekly jam) is extracted again on every run: its already-stored occurrences are removed by the title+date rule, new occurrences are kept. This is how next week's concerts on a known page are found.
- A duplicate of a rejected event stays rejected and is counted: rejected events never return.

## 7. Scoring

An LLM judge receives the criteria text, the facets, the resolved window and one event. It returns a score 0–100, one sentence to the user, and four fit flags (place, date, topic, budget: yes / no / unknown).

Rubric the judge applies:

| Band | Meaning |
|---|---|
| 90–100 | Real event with a specific start; every stated facet fits: place, date, topic, budget, formats, other constraints |
| 70–89 | All stated hard facets fit (place, date, topic); one soft facet is unknown or slightly off: price unknown while the user stated a budget, sub-genre adjacent, format differs |
| 40–69 | Topic fits loosely, or one facet is uncertain: date unclear inside the window, place nearby rather than in the city |

| 10–39 | Place and date fit but the topic does not; or topic fits but a stated constraint fails |
| 0–9 | Not an event, or two or more facets fail |

Unconfirmed hard constraints: when the user named a hard constraint (accessibility, a maximum price, "no courses", a specific day) and the event text does not let you confirm it, the score is at most 89 and the reason names the unconfirmed constraint. The event goes to the user's review queue, never auto-accepted.

Caps enforced in code from the flags, whatever the judge's number:

| Flag | Cap |
|---|---|
| place = no | 0 |
| date = no | 10 |
| topic = no | 39 |

The sentence:

- One sentence, ≤ 140 characters, addressed to the user, facts first then the verdict, in the language the criteria were written in.
- Pattern: `<what> in <city or district> on <date>, <price>: <fits / does not fit> <facets>`.
- Example: `Jazz trio in Berlin-Kreuzberg on 20 Oct, 18 EUR: fits your dates and budget`.
- Never: "the event", "the criteria", model talk, hedging.
- The sentence is checked in code for length and pattern (§10, structure layer); a sentence that fails is an error for that event, never shown.

Consistency:

- Target: same event and criteria → same score within ±5 across three calls (temperature 0, pinned model, versioned prompt).
- This is a smoke measurement, not a CI assertion: the fake model replays recordings bit-identically, and the live model at temperature 0 is not guaranteed deterministic. The smoke script prints the spread per event; the owner reads it.
- The judge model and prompt version are stored on the event.
- A score with a missing or malformed reason is an error, not a 0.

The two cut-offs against this score:

| Cut-off | Meaning for the user |
|---|---|
| Upper (auto-accept), default 90 for new users | "every stated facet fits": score ≥ upper goes to the calendar |
| Lower (auto-reject), default 40 for new users | "not on topic": score ≤ lower is gone |
| Between | the judge saw a real fit with an open question; the queue card's sentence says which |

- Existing users keep their current thresholds (70/30 today); the thresholds page tells them what the bands now mean so they can move them.

## 8. Transparency to the user

Queue card:

| Line | Content |
|---|---|
| Score | the number with its band word, no `%` (it is a rubric band, not a probability): `56 · open question`; bands: 90–100 `fits`, 70–89 `mostly fits`, 40–69 `open question`, 10–39 `off topic`, 0–9 `not a fit` |
| Reason | the judge's sentence, no label |
| Title | event title |
| When | `Tue 20 Oct 2026, 21:00 (Europe/Berlin)`; the user's zone beside it when different |
| Where | venue, city, country |
| Link | the event page |

Run report (after "Search now" and on the last scheduled run):

- `6 queries → 31 results → 12 events → 9 passed filters → 9 judged → 2 accepted, 3 queued, 2 rejected`. When recovered `new` events from a prior crashed run are judged in this run, the line reads `9 judged (2 recovered)`. `passed filters` counts events_extracted minus the filter drops; `judged` = passed + recovered; the filter detail line sums to events_extracted − passed. "0 judged" never appears next to "Review N events".
- What the filters removed, by count.
- When the run stopped early: at which stage and why (budget, provider error, adapters refused in production). Every early stop sets `stopped_at_stage` and writes zero `stage_counts` so the UI shows the reason.
- "Search now" beyond 6 in an hour: `Search limit reached, try again in N minutes` (HTTP 429 with `Retry-After`).
- Times are shown in UTC until the user saves their criteria from the new UI; the page says so.
- Never the criteria text in logs; never fixture data labelled as a search.

## 9. Cost and limits

| Budget | Scope | Default | When exhausted |
|---|---|---|---|
| Search calls | per run | queries per run (above) | n/a, planned |
| Search calls | per day, whole deployment | 600 | run stops before search; report says `budget: search` |
| Model calls | per run | ≤ 1 (criteria) + queries (snippet extraction) + listing or incomplete pages (content extraction) + `MAX_EVENTS_PER_RUN` (judge) | n/a, planned |
| Model calls | per day, whole deployment | 5000 | run stops at the stage that would exceed it; judged events keep their state; unjudged stay `new` and are judged on the next run |
| "Search now" | per user | 6 per hour | HTTP 429 with `Retry-After`; nothing runs |
| Money | per day | derived from calls × configured unit prices; unset = not computed | reported, not enforced |

Sizing assumption: 10 users on the hourly schedule (2 queries, 4–16 model calls per run each) plus about 10 cold manual runs a day (6 queries, ~27 model calls each) → ~540 search and ~4 100 model calls a day at the worst. At 50 users the caps are hit mid-day; raise them with the user count, and size the Tavily plan at ~1 500 searches per user per month.

- Exhaustion is a reported outcome of the run, visible to the user and in metrics. Never a fallback to fixtures, a fake judge, or a silently shorter run.
- In production the fixture provider and the fake judge are refused at first use, not at start-up: the service stays healthy, the run is recorded with `adapters refused in prod: set SEARCH_PROVIDER and LLM_PROVIDER`, and nothing fixture-shaped is stored.
- The hourly job enqueues work and returns at once; users are run in the background, oldest last run first; a user whose run started less than 55 minutes ago and has not finished is skipped. When the daily cap is hit, the users who lose are the ones whose turn comes last, and that rotates with the ordering.

Rollout, in this order:

1. Today, on current code: set the DeepSeek variables on Render prod (the old code ignores the new names); the Tavily and Lakera keys are already there. Do not set `SEARCH_PROVIDER=tavily` yet: the old code would search for real and score with `md5(title)`.
2. The data model, adapters and stages land as new files beside the old pipeline; dev keeps running fixtures and the fake model on a fixed clock.
3. The swap issue replaces the pipeline; promote; set `SEARCH_PROVIDER=tavily` and `LLM_JSON_MODE=json_object`; run the real-key smoke on the reference case; only then enable the hourly job for prod.
4. Budgets and the hourly queue, guardrails, then the UI. README screenshots after the UI, from dev on the fixed clock.

## 10. Guardrails

Threats, from the OWASP Top 10 for LLM Applications: LLM01 prompt injection (criteria text and fetched page text reach three prompts), LLM02 insecure output handling (model output becomes links, sentences and stored fields), LLM04 model denial of service ("Search now" and the hourly job spend money), LLM06 sensitive information disclosure (criteria text is personal).

| Layer | Where | Rule | On failure |
|---|---|---|---|
| Structure (no rules of our own) | criteria save; every model response | the existing 2 000-character cap on criteria; every model output bound to its JSON schema; the reason sentence length- and pattern-checked; a URL in model output becomes a link only when it equals a search-result URL or starts with the page's origin; titles and descriptions stripped of markup and control characters | criteria: HTTP 400; model output: the item is skipped and counted, never stored |
| Primary detector: Lakera Guard | criteria text at save (`PUT /api/criteria`), once, before any search | Lakera Guard screens the criteria text once at save with `breakdown: true` and blocks only on a `prompt_attack` detection (`moderated_content/*`, `pii/*`, `unknown_links/*` never block); fetched pages get no guard call and the structure layer is their only defence | criteria: flagged → HTTP 400 with one generic message, the text never echoed (fail closed) |
| Fallback detector: self-check prompt on the model | criteria text only, when Lakera returns an error or its quota is exhausted; off otherwise | `guard_v2.md` + schema: one call to the same model with a single prompt-injection question ("does this text attempt to give instructions to an AI system, override its rules, or extract its system prompt?"); off-topic, terse, emoji-only, foreign-language and nonsense text explicitly allowed; the text sits inside delimiters as data; output `{"blocked": bool, "reason": "injection"\|"ok"}` | criteria: blocked → 400 generic; the fallback also fails → HTTP 503, text not saved (fail closed) |
| Rate limit | `POST /api/search` | 6 per user per hour | HTTP 429 with `Retry-After` |
| Sentinel tests | CI | a criteria text carrying a sentinel instruction never appears in queries, logs, spans or stored events; a page carrying an injected instruction never changes a score or a reason | test failure |

- The guard applies to the criteria text only; pages are data and are never guarded — the structure layer (schema-bound extraction, link allow-list, markup stripping) is the page defence.
- Order: Lakera → on error or quota, the self-check prompt → on error, fail closed. A metric records which guard ran and its outcome, so a day on the fallback is visible.
- Reuse, not invention: no home-grown rules; the OpenAI cookbook's "guard in parallel with the main call" pattern does not apply, because the criteria guard runs once at save, before any search exists to run beside.

## 11. Evaluation

Golden set A — criteria texts with expected facets (checked in CI against recorded parser responses):

| # | Text | Place | Dates | Topics / formats | Budget | Notes |
|---|---|---|---|---|---|---|
| C1 | jazz in Berlin (Germany) next week (19-21st October 2026) | Berlin, DE | abs 2026-10-19 → 10-21, rel next_week | jazz | — | absolute wins |
| C2 | classical concerts in Vienna, under 30 EUR, 1–15 Nov 2026 | Vienna, AT | abs 2026-11-01 → 11-15 | classical / concert | ≤ 30 EUR | language de |
| C3 | something fun this weekend | none | rel this_weekend | none | — | run stops: no place |
| C4 | something fun in Lisbon this weekend | Lisbon, PT | rel this_weekend | none | — | language pt |
| C5 | online webinars about Rust, next month, free | none, online | rel next_month | Rust / webinar | free only | place not required |
| C6 | sailing regattas on the Solent next summer | Solent, GB, radius 30 | abs 2027-06-01 → 08-31 | sailing regatta | — | season → absolute |
| C7 | Techno-Partys in Berlin am 31. Oktober 2026 | Berlin, DE | abs 2026-10-31 | techno / party | — | German input |
| C8 | art exhibitions in Paris within 20 km, this month, English-friendly | Paris, FR, radius 20 | rel this_month | art / exhibition | — | other: English-friendly |
| C9 | kids science workshops near Amsterdam on Saturdays in November | Amsterdam, NL, radius 25 | abs 2026-11-01 → 11-30 | kids science / workshop | — | other: Saturdays |
| C10 | jazz | none | none → default 30 days | jazz | — | run stops: no place |
| C11 | tech meetups in Tokyo, 2026-10-20 to 2026-10-22, Japanese ok | Tokyo, JP | abs 2026-10-20 → 10-22 | tech / meetup | — | language ja |
| C12 | beer festivals in Munich, Germany, from 20 to 30 euros, in the next 10 days | Munich, DE | rel next_n_days 10 | beer / festival | ≤ 30 EUR | |
| C13 | anything in Berlin | Berlin, DE | none → default 30 days | none | — | topic empty allowed |

Golden set B — labelled candidates for C1, now = 2026-10-18 12:00 Europe/Berlin (checked in CI with the recorded judge):

| # | Candidate | Start | Place | Label | Expected |
|---|---|---|---|---|---|
| E1 | Jazz Trio at A-Trane, 18 EUR | 2026-10-20 21:00 | Berlin DE | fit | judged, 90–100 |
| E2 | Late Night Jam Session, Zig Zag Jazz Club | 2026-10-21 22:00 | Berlin DE | fit | judged, 85–100 |
| E3 | Open-air jazz, Mauerpark, free | 2026-10-19 16:00 | Berlin DE | fit | judged, 90–100 |
| E4 | Jazz vocal workshop | 2026-10-21 18:00 | Berlin DE | fit, format differs | judged, 70–89 |
| E5 | Jazz Under the Stars | 2026-10-20 20:00 | Chicago US | wrong city | filtered_place |
| E6 | Jazz night Potsdam | 2026-10-20 20:00 | Potsdam DE | wrong city, same country | filtered_place |
| E7 | Jazz in Bern | 2026-10-20 20:00 | Bern CH | wrong city, name confusion | filtered_place |
| E8 | Jazzfest Berlin | 2026-11-05 20:00 | Berlin DE | wrong date | filtered_date |
| E9 | Sunday Jazz Brunch | 2026-10-25 11:00 | Berlin DE | wrong date, inside "next week" but outside the absolute window | filtered_date |
| E10 | Jazz Trio at A-Trane | 2026-10-22 21:00 | Berlin DE | wrong date, one day past the end | filtered_date |
| E11 | Jazz Under the Stars | 2026-12-01 20:00 | Chicago US | wrong city and date | filtered_past/date/place, never judged |
| E12 | Jazz in the Park | 2026-10-10 15:00 | Berlin DE | past | filtered_past |
| E13 | Jazz at b-flat | 2026-10-17 21:00 | Berlin DE | past, yesterday | filtered_past |
| E14 | Top 10 jazz clubs in Berlin | — | — | not an event | filtered_non_event |
| E15 | History of jazz in Berlin (encyclopedia page) | — | — | not an event | filtered_non_event |
| E16 | A-Trane venue homepage, no dates | — | Berlin DE | not an event | filtered_non_event |
| E17 | Berlin jazz radio, 24/7 stream | — | — | not an event | filtered_non_event |
| E18 | E1 under the same URL with `?utm_source=x` | 2026-10-20 21:00 | Berlin DE | duplicate by link | filtered_duplicate |
| E19 | "A-Trane: Jazz Trio" on another site | 2026-10-20 21:00 | Berlin DE | duplicate by title+date | filtered_duplicate |
| E20 | Techno night at Berghain | 2026-10-20 23:00 | Berlin DE | off-topic | judged, 10–39 |
| E21 | Outdoor Photography Meetup | 2026-10-20 10:00 | Berlin DE | off-topic | judged, 10–39 |
| E22 | Vienna Philharmonic, 120 EUR (for C2) | 2026-11-05 19:30 | Vienna AT | over budget | judged, ≤ 30 |

- CI: both sets run on every push with recorded model responses; no network; the clock is fixed at 2026-10-18 12:00 Europe/Berlin so recordings and fixture dates never age.
- E1, E4 and E20 are the judge's few-shot examples and are excluded from the CI judge check; E2, E3, E21 and E22 are the CI judge rows.
- Weekly real-key smoke, by hand: the full pipeline on C1 and C4 with the live provider and judge; the owner labels the output; precision numbers in section 2 are read from it.

## 12. Acceptance criteria

1. The reference criteria yields no event outside Germany in accepted or queued; an event with an unknown country counts as outside.
2. The reference criteria yields no event that does not overlap 2026-10-19 → 2026-10-21 in accepted or queued; a 17–22 Oct festival is kept.
3. No event that has already ended at run time is inserted; a date-only event counts as ending at 23:59 of its day.
4. Every stored event has a start with a time zone or an explicit "unknown zone", a city, a country, the page it came from and its own link.
5. Every stored event has a score, a reason sentence ≤ 140 characters passing the pattern check, a judge model and a judge version.
6. The reason sentence names at least the date and the place, in the language of the criteria text.
7. The smoke script with three repeats prints the score spread per event; the owner reads it against ±5 (measurement, not a CI assertion).
8. Facets are parsed once per criteria text (hash) or prompt version change. Relative date words resolve against now on every run in `window.py`; absolute dates are fixed and the past filter and the judge handle them.
9. "next week" resolves to the ISO week after the run date in the user's time zone; absolute dates win; a window that ended before now does not stop the run — the per-event past filter and the judge handle dates (#70).
10. Criteria without a place and without an online format produce a run with zero queries and the report says why.
11. Every query contains the city and the year; when the place's language is not English, at least one query is in that language; Tavily receives the country as its name (`germany`), Brave as `DE`.
12. A listing page yields at most 10 events, each overlapping the window; a listing page seen before is extracted again on the next run and only its new occurrences are stored.
13. A single-event page already stored for the user costs no model call.
14. Two candidates with the same canonical link and date, or the same date and ≥ 0.8 title overlap (subset rule only from 3 tokens), yield one stored event; two different concerts at one venue on one night stay two.
15. A duplicate of a rejected event is not inserted and is counted.
16. The run row carries counts for every stage, filter and guard, the number of search and model calls, tokens, and the stage where it stopped if it stopped early.
17. Reaching a daily budget stops the run at that stage with `budget: <which>` and HTTP 200; a judge error leaves that event `new`, is counted, and the run completes.
18. With `APP_ENV=prod` and a fixture or fake adapter selected, `GET /api/health` stays 200 and a run is recorded as refused with nothing stored.
19. Golden set A (13 criteria) and golden set B (22 candidates) pass in CI without network on the fixed clock; the demo user on dev has a non-empty queue on the fixed clock.
20. A contract test per provider (Tavily, Brave) passes against recorded responses, and the model adapter's contract test covers `json_object` mode, empty content retry and 429 retry.
21. No log line, span attribute or metric label contains criteria text, query text, page text, event descriptions or prompt bodies.
22. `POST /api/search/all` returns 202 within 5 seconds, skips a user whose run started less than 55 minutes ago and is unfinished, and runs users oldest-last-run first.
23. New registrations get thresholds 90/40; existing users' thresholds are unchanged by the migration.
24. Guardrails: criteria flagged by Lakera get a generic 400 without echo; when Lakera errors or is out of quota the self-check prompt runs instead and a metric says so; both failing → 503 and nothing saved; a flagged page is skipped and counted; a seventh "Search now" within an hour gets 429 with `Retry-After`; the sentinel tests pass.
25. The real-key smoke script runs the full pipeline for C1 and prints the run report and every judged event with its sentence; the owner's first smoke finds at least 3 real Berlin jazz events in the window.

## 13. Out of scope

- Geocoding and true distance; radius relaxes the city filter to the judge only.
- Following links from results to further pages beyond the page content the provider returns.
- More than two search providers; provider fallback inside a run.
- Learning from the user's accept/reject decisions.
- Notifications; editing a score by hand.
- Travel schedule (where the user will be on a date).
- Recurring events as series; each occurrence is one event.
- An Anthropic model adapter in the app; the model interface is OpenAI-compatible only.
- Rules of our own for prompt injection; detection is Lakera's job, with the self-check prompt as its fallback.

## Review applied

Source: `_docs/search-design-review.md`, 2026-10-18.

| Finding | Where in this spec |
|---|---|
| §0 Portland traced to config | intro, first fact |
| F2 listing pages lost after run 1 | §6 known-page rule, listing re-extraction; ac 12, 13 |
| F3 recordings age | §11 fixed clock; ac 19 |
| F5 hourly job sequential | §9 enqueue rule; ac 22 |
| F6 prod refusal kills health | §9 refused at first use; ac 18 |
| F9 past/window on start only | §6 past and overlap rules; ac 2, 3 |
| F10 unknown country passes | §6 place rule; ac 1 |
| F11 past window searched hourly | §3 dates-in-the-past stop; ac 9 |
| F12 unknown price contradiction | §7 price rule |
| F13 cut-offs vs code defaults | §7 cut-offs 90/40, `>=`/`<=`; existing users told; ac 23 |
| F14 subset rule merges short titles | §6 title+date rule; ac 14 |
| F18 Tavily claims | §4 provider table and locale bullets |
| F19 "Score 56%" reads as probability | §8 band word, `%` dropped |
| F20 few-shot rows in CI | §11 E2/E3/E21/E22 in CI |
| F21 English-only sentence | §7 language of the criteria; ac 6 |
| F22 ±5 untestable | §7 consistency as a smoke measurement; ac 7 |
| F23 who loses at the cap | §9 rotation note |
| Cost §2 caps sized for ~10 users | §9 caps 600/5 000 with the stated assumption |
| Rollout §3 | §9 rollout list |
| Owner (1) DeepSeek only | §13 out of scope: Anthropic adapter |
| Owner (2) Tavily primary | §4 |
| Owner (3) guardrails, final: Lakera primary, self-check fallback, no own rules | §10, ac 24 |
| Owner (4) caps and hourly queue | §9 |
| Owner (5) 90/40 defaults | §7, ac 23 |
