# Search and scoring — specification (v2)

Behavior described here is for main. Implementation: [search-design.md](search-design.md).
The [PRD](plan.md) explains the product; this file separates quality targets
from the behavior and measurements that can be checked today.

The 2026-10-18 revision replaced query planning and facet score caps with a
criteria-text query and suitability judge. The actual query includes ` event`.
The 2026-10-21 no-place auto-accept restriction remains **unshipped**
([#101](https://github.com/alexisdacquay/sail-event/issues/101), PR
[#103](https://github.com/alexisdacquay/sail-event/pull/103)). Later changes are
listed in the [PRD change log](plan.md#changed-after-the-mvp-dated).

## 1. The job

One saved sentence per user produces candidate events with title, start date and
time, time zone, city, country, link and description. A suitability judge adds a
0–100 score and reason. Thresholds decide calendar / review / out. There is no
price extraction or price/budget scoring rule.

## 2. Quality definition

These are targets, **not achieved precision or recall claims**.

| Measure | Target | Evidence needed |
|---|---|---|
| Auto-accepted precision | At least 90% true fits | Human labels on live-search output |
| Review precision | At least 70% plausible fits | Same |
| Wrong place/date in accepted or review | Zero | Labeled cases and live output |
| Past events, missing start time, non-events, duplicates in accepted or review | Zero | Pipeline tests plus review of live output |
| Reference-case discovery | At least three distinct Berlin jazz events in the 19–21 Oct 2026 fixture window | Fixed-clock smoke run with real adapters |

Wrong place/date and off-topic judgments depend on the model. Code screens
missing data, past events and stored event pages; cross-site duplicates use a
model after storage. Those checks do not establish live precision.

The recorded full recall run in [work/RECALL.md](../work/RECALL.md) at `ab21641`
on 2026-10-24 found **3/38 events (7.9%)**, with **0/38 accepted**. The ground-truth set remains
unvetted ([STATE](../work/STATE.md)), so the result is indicative. Recall after
the event-page hop has not been measured in that record.

## 3. Criteria understanding

[criteria.py](../backend/app/services/criteria.py) caches parsed facets by text
hash and prompt version. [window.py](../backend/app/services/window.py) resolves
relative dates each run in the user's saved time zone: ISO weeks Monday–Sunday,
weekends Saturday–Sunday, calendar months, today/tomorrow and next N days.
Absolute dates take precedence; no date defaults to now through 30 days ahead.
Past absolute dates do not stop the search.

The saved sentence drives the query and judge; facets supply extraction context
and window resolution. Missing place does not stop a run or prevent auto-accept
in main. That last behavior is the open requirement #101.

## 4. Candidate discovery

One selected provider per run: fixture, Tavily, Brave or Exa. The query is
`criteria_text + " event"`; no query templates, translation or place requirement.
The pipeline requests `MAX_RESULTS_PER_QUERY` (default 20). See
[pipeline.py](https://github.com/alexisdacquay/sail-event/blob/542e58cb0fe73065a905febec7637bfa377a77c4/backend/app/services/pipeline.py#L279-L298) and the
[adapter factory](../backend/app/adapters/factory.py).

Canonical result URLs are de-duplicated; previously stored single-event pages
are removed before extraction. Stored listing pages remain eligible.
Scheduled searches use the prod GitHub cron; actual starts are less frequent
than hourly. [PRD timing and measured durations](plan.md#2-search) gives the
source and reproduction command.

## 5. Event extraction

[extract.py](../backend/app/services/extract.py) reads every provider result with
page content in full, with no character slice or per-page event cap. Results
without page content use a snippet fallback. Page reads default to concurrency
10 (`EXTRACT_CONCURRENCY`). Model classification records `single_event`,
`listing` or `not_event`; confidence below 0.5 is excluded.

A listing event with a distinct HTTP(S) link to a public host can be completed
from its own page, including another site. [detail_hop.py](../backend/app/services/detail_hop.py)
checks destinations and redirects, fetches the page and re-extracts it. Fetch or
re-extraction failure keeps the listing record and increments the corresponding
error count. DNS is checked before a separate connection lookup, leaving a
DNS-rebinding window; the check is not a complete network sandbox.

Six required fields are title, description, start with a time component, time
zone, city and country. The filters below screen missing values after extraction.

## 6. Hard filters before scoring

[filters.py](https://github.com/alexisdacquay/sail-event/blob/542e58cb0fe73065a905febec7637bfa377a77c4/backend/app/services/filters.py#L193-L223) applies these checks
in order. Place and date-window suitability are left to the judge.

| Dropped | Counter |
|---|---|
| No start date | `filtered_no_date` |
| Date with no time | `filtered_no_time` |
| Other missing mandatory field | `filtered_incomplete` |
| Already ended (end, or start when no end exists) | `filtered_past` |
| Event's own page and calendar date already stored for the user | `filtered_duplicate` |

There is no in-run title match or `(user, link, start)` uniqueness constraint.
After storage, the model compares new accepted/queued events with same-day
candidates; it rejects duplicates and counts `dedup_merged`. Errors keep both
rows and count `dedup_errors`. See [dedup.py](../backend/app/services/dedup.py).

## 7. Scoring

[judge_v3.md](../backend/app/adapters/prompts/judge_v3.md) defines the bands:

| Score | Prompt meaning |
|---|---|
| 90–100 | Clearly fits place, time and topic as stated |
| 70–89 | Mostly fits; a minor aspect is off or unknown |
| 40–69 | Uncertain or loosely related |
| 10–39 | Topic does not match, but place and dates do |
| 0–9 | Wrong stated place/date, or criteria do not request events |

The JSON fields are `score`, `reason`, `is_event`; there are no fit flags or
code score caps. The prompt asks for a reason of at most 140 characters;
[judge.py](../backend/app/services/judge.py) allows up to 200 and rejects URLs
and markup. It does not require date/place tokens or enforce a non-empty reason.
One schema-repair call and a separate reason-repair call may follow the initial
call. An unrepaired judge error leaves the event `new` for retry on a later run.

New users default to upper 90 / lower 40. `score >= upper` accepts,
`score <= lower` rejects, and the middle queues. **Out** events remain
viewable through **show**; a later search does not bring them back.

## 8. Transparency to the user

The Stream page shows live stage progress, a funnel and earlier runs. Per-page extraction details are stored on the run
and returned by the API; the main page does not render them. Events show the score as a percentage, status and source; detail shows
the reason and decision buttons. A percentage is the suitability score, not a
calibrated probability. Current UI decisions: [ui-design.md](ui-design.md).

A run reports stage counts and errors. Missing historical counters must not be
read as measured zeros. A green scheduled workflow establishes enqueue success,
not the success of background searches.

## 9. Cost and limits

| Limit | Default | Source |
|---|---|---|
| Daily search budget | 600 credits, summed from run rows | [budget.py](../backend/app/services/budget.py) |
| Daily model budget | 5000 calls | Same |
| Manual searches | Six per user per rolling hour; then 429 with `Retry-After` | [search.py](../backend/app/routers/search.py) |
| Scheduled users per enqueue | 50, oldest last run first; never-run first | Same |

The overlap check skips users with an unfinished run started within 55 minutes.
The endpoint writes run rows, queues FastAPI background tasks and returns 202.
These tasks are not a durable queue. There is no per-search event cap; daily
budgets can still leave events unjudged. Search budget accounting uses configured
credits (advanced defaults to two, basic one), not a currency cap.

`cost_usd` is null unless unit prices are configured. Token/cost accounting is
incomplete: extraction and criteria token usage is not included in the pipeline
totals (also disclosed in PR #144). Do not use it as a billing reconciliation.
Fixture search and the fake model refuse at first use with `APP_ENV=prod`;
health can remain green while runs fail.

## 10. Guardrails

The criteria-save endpoint uses `GUARDRAIL=none` by default. With Lakera enabled,
a prompt-attack detection blocks save with a generic 400. A configured
`GUARD_FALLBACK=self_check` runs only when Lakera is unavailable; failure of both
returns 503. See [factory.py](../backend/app/adapters/factory.py) and
[criteria router](../backend/app/routers/criteria.py).

Fetched pages have no guard call. Schema validation, link checks, markup
stripping and the detail-fetch public-address check constrain their outputs;
they do not prove immunity to prompt injection. Manual rate limiting bounds
requests, not the cost of each one.

## 11. Evaluation

Recorded tests cover criteria parsing, judge outputs, filters, budgets, provider
contracts and recovery. They verify behavior on those recordings, not search
coverage or model quality in the wild. Tests and field runs are documented in
[docs/testing.md](../docs/testing.md); fixtures are under
[backend/tests/fixtures/](../backend/tests/fixtures/).

The [field runner](../backend/tests/field/runner.py) supports invariants,
regression tests, a breadth batch and ground-truth recall. Live phases spend
quota and need authorization. Retain the commit, settings, output and labeling
basis with a result; the unvetted ground truth limits the recall claim.

## 12. Acceptance criteria

For regression checks, use the executable cases linked in
[plan.md, Expected behaviour](plan.md#expected-behaviour). They cover triage
boundaries, isolation, rejection persistence, feed removal/reset and rate limits.
Quality targets in §2 need live evaluation in addition to recorded tests.

The no-place auto-accept requirement is open (#101). Do not mark it delivered
because it appears in an older specification or an unmerged PR.

## 13. Out of scope

- Price or personal budget scoring; currency spending caps.
- Query planning, translation, provider fallback or multiple providers in one run.
- General crawling beyond a listing's event-page hop.
- Learning from decisions, notifications, score editing or travel itineraries.
- Calendar-provider write access; the product publishes an ICS subscription.

## Review applied

The [2026-10-18 design review](search-design-review.md) records the earlier
proposal and objections. Query templates, place/date code filters, price fields,
facet caps and a two-pass snippet gate described there were superseded; it is
historical evidence, not the current acceptance contract.
