# Invariants

What must hold for every user, whatever they typed. Code checks these; an LLM never grades them.
A finding is `invariant | persona cell | evidence | layer`. One issue per (invariant, layer) cluster,
titled by the invariant. No issue for a bare symptom.

Layers: `recall` (search provider, query), `extract` (page → event), `judge` (score, reason),
`pipeline` (filters, dedup, state, counters), `api`, `ui-state`, `copy`.

## Data (checked over /api/events, /api/calendar/<token>, the run report, or SQL)

| id | invariant | how to check |
|---|---|---|
| I1 | No event whose end is before now, or whose date is unparsed, is queued, accepted, or in the feed | `date_time` parses as ISO; end (or start, or 23:59 of the day) ≥ now |
| I2 | When the criteria name a place, every queued/accepted event is in that country | country code of the named place (persona cell gives it) == `country` |
| I3 | No auto-accept whose reason hedges | status accepted and `decided_by` is not the user, and reason matches `not confirmed|unconfirmed|rather than|no place|no city|no location|however|although|but it is in` |
| I4 | Counters sum | `results_fetched` = extracted + skipped; judged ≤ extracted; accepted+queued+rejected = judged; the run report equals the events table for that run |
| I5 | Reason language = criteria language | langdetect of reason vs criteria; ASCII-only short reasons are skipped |
| I6 | Every queued/accepted event has an event link and a time, or says time unknown | link is not the site root, not a search/listing page (`/search`, `?q=`, `/events/?$`), and ≠ `source_url` of a listicle; `date_time` has a clock time or `end_time`/description marks it as unknown |
| I7 | Same (title key, date) never twice for one user | `title_key` + calendar date unique per user |
| I8 | After a criteria change, nothing stays silently stale | every event's `score_reason` was produced by the current criteria (judge_version + run after `criteria.updated_at`), or the event is user-decided |
| I9 | Decisions are reversible and distinct | reject → undo → queued; "remove from calendar" leaves status ≠ rejected |
| I10 | A run never surfaces a raw exception; every stop has a plain reason; 429 is shown | `error` contains no `Error:`/`Traceback`/class name; `stopped_at_stage` set ⇒ a reason string; HTTP 429 ⇒ a message in the UI |
| I11 | No cross-user leakage | user B lists no event of user A; A's feed token does not serve B |
| I12 | Exclusions in words are honoured | criteria contains `no X|sin X|not X|kein X` ⇒ no queued/accepted event whose title/description is of kind X (checked by the persona's own exclusion list) |

## UI (Playwright, headless)

| id | invariant | how to check |
|---|---|---|
| U1 | Reload and tab switch keep the page and the search status | navigate to tab, reload, same tab; start search, reload, status still shown |
| U2 | The result line matches the cards | parse the numbers in the line; count cards per status |
| U3 | Slider boxes equal slider knobs; legend not clipped at 375 px | aria values == input values; legend element not overflowing |
| U4 | Copy gives feedback; feed link offers webcal and steps | button text changes after click; `webcal://` present |

## Severity

A violated invariant on an accepted or feed event is `high` (the user's calendar is wrong).
On a queued event: `medium`. On rejected: `low` (noted, not filed).
