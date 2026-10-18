# Search and scoring — specification (v2)

What the search must deliver. The how is in `search-design.md`.
Reference case throughout: criteria `jazz in Berlin (Germany) next week (19-21st October 2026)`, run on 2026-10-18 in `Europe/Berlin`.

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
- Window start is clipped to now: an event earlier today that already started is past.
- The reference case resolves to 2026-10-19 00:00 → 2026-10-21 23:59 Europe/Berlin because the absolute dates win over "next week" (19–25 Oct).

## 4. Candidate discovery

Sources, from the owner's keys:

| Provider | Use | Why / why not |
|---|---|---|
| Tavily | primary | already integrated and contract-tested; returns page content, which extraction needs; has country and domain controls |
| Brave Search | optional, selectable | independent index; first-party country, language and date-range freshness controls; cheap |
| Serper | not now | Google coverage is the best for local events, but two providers is the cap; revisit if Tavily recall fails the smoke target |
| Exa | no | semantic search over articles, weak on dated local listings |
| Linkup | no | overlaps Tavily |
| Firecrawl, Nimbleway | no | page fetching, not search; Tavily's raw content covers the need |

Query strategy:

- Queries are built from facets by code, not by a model: deterministic, testable, free.
- Each query targets one facet combination: topic × place × month, topic × place × exact dates, place-language variants, event-listing words of the place's language, ticket/programme words.
- Every query carries the city and the year. Nothing is searched without a place unless the format is online.
- Queries run in the place's language as well as English when they differ.
- Locale: country = the place's country; language = the place's language; freshness = pages published in the last 90 days where the provider supports a date range.

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
| time zone | from the page; else the country's zone when the country has one; else unknown |
| end | optional |
| place | venue, city, country (ISO-2); city or country missing → the place filter treats it as unknown |
| link | the page URL, or the deeper event URL when the page is a listing |
| price | amount + currency when printed; "free" recorded as free; else unknown |
| description | one line, ≤ 200 characters, from the page |
| confidence | 0–1; below 0.5 the event is dropped and counted |

- A page with many events (venue programme, listing): up to 10 events whose dates fall in the window; the rest ignored.
- A page with none (article, listicle, venue homepage, radio stream): no event, counted as non-event.
- The extractor is told today's date, the window and the target place so it picks the right occurrence from a programme page; it never decides fit.

## 6. Hard filters before scoring

Applied in code, in this order, each with a count on the run:

| Filter | Rule | Count |
|---|---|---|
| Past | start < now | `filtered_past` |
| Date window | start outside [window start, window end] in the event's zone | `filtered_date` |
| Place | country ≠ criteria country; or city ≠ criteria city when no radius; unknown city with known country passes to the judge | `filtered_place` |
| Non-event | extraction returned no event, or confidence < 0.5 | `filtered_non_event` |
| Duplicate by link | canonical link already stored for the user, or seen earlier in the run | `filtered_duplicate` |
| Duplicate by title+date | same calendar date and near-identical title (stopwords removed, ≥ 0.8 token overlap) against the user's stored events and the run | `filtered_duplicate` |

- Links known for the user are dropped before extraction, so no model call is spent on them.
- A duplicate of a rejected event stays rejected: rejected events never return.

## 7. Scoring

An LLM judge receives the criteria text, the facets, the resolved window and one event. It returns a score 0–100, one sentence to the user, and four fit flags (place, date, topic, budget: yes / no / unknown).

Rubric the judge applies:

| Band | Meaning |
|---|---|
| 90–100 | Real event with a specific start; every stated facet fits: place, date, topic, budget, formats, other constraints |
| 70–89 | All stated hard facets fit (place, date, topic); one soft facet is unknown or slightly off: price unknown, sub-genre adjacent, format differs |
| 40–69 | Topic fits loosely, or one facet is uncertain: date unclear inside the window, place nearby rather than in the city, budget unknown when the user set one |
| 10–39 | Place and date fit but the topic does not; or topic fits but a stated constraint fails |
| 0–9 | Not an event, or two or more facets fail |

Caps enforced in code from the flags, whatever the judge's number:

| Flag | Cap |
|---|---|
| place = no | 0 |
| date = no | 10 |
| budget = no (price over the stated maximum) | 30 |
| topic = no | 39 |

The sentence:

- One sentence, ≤ 140 characters, addressed to the user, facts first then the verdict.
- Pattern: `<what> in <city or district> on <date>, <price>: <fits / does not fit> <facets>`.
- Example: `Jazz trio in Berlin-Kreuzberg on 20 Oct, 18 EUR: fits your dates and budget`.
- Never: "the event", "the criteria", model talk, hedging.

Consistency:

- Same event and criteria → same score within ±5 across three calls (temperature 0, pinned model, versioned prompt).
- The judge model and prompt version are stored on the event.
- A score with a missing or malformed reason is an error, not a 0.

The two cut-offs against this score:

| Cut-off | Meaning for the user |
|---|---|
| Upper (auto-accept) | "every stated facet fits": 90 and above with the rubric; 80 if they accept unknown prices |
| Lower (auto-reject) | "not on topic": 40 and below |
| Between | the judge saw a real fit with an open question; the queue card's sentence says which |

## 8. Transparency to the user

Queue card:

| Line | Content |
|---|---|
| Score | `Score 56%` |
| Reason | the judge's sentence, no label |
| Title | event title |
| When | `Tue 20 Oct 2026, 21:00 (Europe/Berlin)`; the user's zone beside it when different |
| Where | venue, city, country |
| Price | `18 EUR` / `free` / omitted when unknown |
| Link | the event page |

Run report (after "Search now" and on the last scheduled run):

- `6 queries → 31 results → 12 events → 7 passed filters → 7 judged → 2 accepted, 3 queued, 2 rejected`.
- What the filters removed, by count.
- When the run stopped early: at which stage and why (budget, provider error, no place in criteria).
- Never the criteria text in logs; never fixture data labelled as a search.

## 9. Cost and limits

| Budget | Scope | Default | When exhausted |
|---|---|---|---|
| Search calls | per run | queries per run (above) | n/a, planned |
| Search calls | per day, whole deployment | 500 | run stops before search; report says `budget: search` |
| Model calls | per run | ≤ 1 (criteria) + results (extraction) + `MAX_EVENTS_PER_RUN` (judge) | n/a, planned |
| Model calls | per day, whole deployment | 3000 | run stops at the stage that would exceed it; judged events keep their state; unjudged stay `new` and are judged on the next run |
| Money | per day | derived from calls × configured unit prices; unset = not computed | reported, not enforced |

- Exhaustion is a reported outcome of the run, visible to the user and in metrics. Never a fallback to fixtures, a fake judge, or a silently shorter run.
- In production the fixture provider and the fake judge refuse to start.

## 10. Evaluation

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

- CI: both sets run on every push with recorded model responses; no network.
- Weekly real-key smoke, by hand: the full pipeline on C1 and C4 with the live provider and judge; the owner labels the output; precision numbers in section 2 are read from it.

## 11. Acceptance criteria

1. The reference criteria yields no event outside Germany in accepted or queued.
2. The reference criteria yields no event outside 2026-10-19 → 2026-10-21 in accepted or queued.
3. No event whose start is before the run time is ever inserted.
4. Every stored event has a start with a time zone or an explicit "unknown zone", a city and a country.
5. Every stored event has a score, a reason sentence ≤ 140 characters, a judge model and a judge version.
6. The reason sentence names at least the date and the place of the event.
7. Two runs on the same stored event and criteria give scores within ±5 (smoke run, three repeats).
8. Facets are stored on the criteria with a parse timestamp and re-parsed only when the text changes.
9. "next week" resolves to the ISO week after the run date in the user's time zone; absolute dates win when both are present.
10. Criteria without a place and without an online format produce a run with zero queries and the report says why.
11. Every query contains the city and the year; when the place's language is not English, at least one query is in that language.
12. A listing page yields at most 10 events, each inside the window.
13. A result whose link is already stored for the user costs no model call.
14. Two candidates with the same canonical link, or the same date and ≥ 0.8 title overlap, yield one stored event.
15. A duplicate of a rejected event is not inserted.
16. The run row carries counts for every stage and filter, the number of search and model calls, and the stage where it stopped if it stopped early.
17. Reaching the daily search or model budget stops the run at that stage with `budget: <which>` on the run; no fixture or fake adapter is used instead.
18. With `APP_ENV=prod`, starting with the fixture search provider or the fake language model fails at startup.
19. Golden set A (13 criteria) and golden set B (22 candidates) pass in CI without network.
20. A contract test per provider (Tavily, Brave) passes against recorded responses.
21. No log line, span attribute or metric label contains criteria text, event descriptions or prompt bodies.
22. The real-key smoke script runs the full pipeline for C1 and prints the run report and every judged event with its sentence.

## 12. Out of scope

- Geocoding and true distance; radius relaxes the city filter to the judge only.
- Following links from results to further pages beyond the page content the provider returns.
- More than two search providers; provider fallback inside a run.
- Learning from the user's accept/reject decisions.
- Notifications; editing a score by hand.
- Travel schedule (where the user will be on a date).
- Recurring events as series; each occurrence is one event.
