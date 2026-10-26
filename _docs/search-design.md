# Search and scoring — design (v2)

Implementation for main. Requirements, quality targets and measured gaps are in
[search-spec.md](search-spec.md); the full schema and deployment boundaries are
in [architecture.md](architecture.md). Earlier proposals remain in git history.

## 1. Pipeline stages

[run_pipeline](../backend/app/services/pipeline.py) coordinates the run and writes
progress to its database row. Service modules sit in `backend/app/services/`,
not a separate `stages/` directory.

| Step | Module / responsibility | Output or failure behavior |
|---|---|---|
| Recovery | `pipeline.py` | Retry stored `new` events before new discovery |
| Criteria and window | `criteria.py`, `window.py` | Cached facets and a window resolved at run time |
| Search | Adapter selected by `factory.py` | One criteria-text-plus-`event` query; known single-event pages removed |
| Extract | `extract.py` | Per-page full-content reads; snippet fallback when content is absent |
| Event-page hop | `detail_hop.py` | Re-extract a listing event from its linked page; retain listing record on failure |
| Filter | `filters.py` | Screen missing fields, no start time, past events, stored event-page/date |
| Store | `pipeline.py` | Commit candidates as `new` before judging |
| Judge and triage | `judge.py`, `pipeline.py` | Score/reason; threshold status; judge error leaves `new` |
| Duplicate check | `dedup.py` | Model compares new accepted/queued events with same-day candidates |
| Finalize | `pipeline.py` | Counts, errors, usage, timestamps and run outcome |

A committed `new` row can be retried after interruption. This is not recovery of
lost page extractions or a durable background-job queue.

## 2. Data model changes

The [architecture schema](architecture.md#data-model) lists the persisted fields;
[orm.py](../backend/app/orm.py) is the source. Facets are cached as JSON text;
run rows hold progress, counters, per-page results and usage. Events retain the
source, extraction fields, judge version and decision provenance.

There is no `(user_id, link, date_time)` unique constraint. PR
[#150](https://github.com/alexisdacquay/sail-event/pull/150) removed it and deleted
stored events without start times. The deletion is irreversible; rollback
across the three migrations added by PRs #128/#150 is untested. See the
[release process](../docs/release-process.md) before any database/code rollback.

## 3. Adapters

### SearchProvider (revised)

The [factory](../backend/app/adapters/factory.py) selects fixture, Tavily, Brave
or Exa with `SEARCH_PROVIDER`. The pipeline supplies query, maximum results and
search depth to the selected implementation. [search.py](../backend/app/adapters/search.py)
defines `SearchResult` and canonical URL/known-page handling. Provider request
construction is in [search_tavily.py](../backend/app/adapters/search_tavily.py),
[search_brave.py](../backend/app/adapters/search_brave.py) and
[search_exa.py](../backend/app/adapters/search_exa.py).

### LanguageModel (new)

`LLM_PROVIDER=fake` replays prompt-hash recordings;
`openai_compatible` uses [llm_openai_compat.py](../backend/app/adapters/llm_openai_compat.py).
Prompts and schemas are files. The adapter validates JSON and reports malformed
or truncated output; fake mode fails on a missing recording. Fixture/fake
adapters refuse at first use under `APP_ENV=prod`, without taking health down.

### Environment variables

Defaults and configuration are documented in [deployment.md](../docs/deployment.md).
Code defaults are fixture search, fake model and no guard. Local fixtures use
`FAKE_NOW`; Render dev uses real adapters, as does prod. Do not infer a running
service's variables from defaults or a historical design.

## 4. Prompts

Source directory: [adapters/prompts/](../backend/app/adapters/prompts/).

| Prompt | Role |
|---|---|
| `criteria_v2` | Parse the saved sentence; cache by text hash/version |
| `extract_v2` | Extract events and classify the page |
| `judge_v3` | Return score, reason and `is_event`; no facet flags/caps |
| `dedup_v1` | Identify the same event among same-day candidates |
| `guard_v2` | Prompt-attack self-check when configured as Lakera fallback |

The judge prompt asks for a 140-character reason; code accepts up to 200 and
rejects URLs/markup. Schema repair and reason repair are separate calls. See
[judge.py](../backend/app/services/judge.py) and the
[prompt loader](../backend/app/adapters/prompts/loader.py).

## 5. Query rule (revised 2026-10-18, owner decision)

One query: `Criteria.text + " event"`, no template planner, translation or place
requirement. Source: [pipeline.py](https://github.com/alexisdacquay/sail-event/blob/542e58cb0fe73065a905febec7637bfa377a77c4/backend/app/services/pipeline.py#L286-L298).
Facets supply extraction/window context; the judge receives the sentence and
event. It does not consume facet fit flags or apply code score caps.

## 6. Relative dates and time zones

[window.py](../backend/app/services/window.py) resolves relative expressions at
run time; absolute dates win, no date defaults to 30 days, start is clipped to
now. Stale absolute dates do not stop the run. [filters.py](../backend/app/services/filters.py)
checks whether events have ended; it does not screen date-window or place fit.

The UI saves the browser's IANA zone with criteria. Events with a known zone are
displayed in that event zone; the short zone name is added when it differs from
the browser's. The saved-user-zone versus browser-zone mismatch remains an open
UX concern. New events without a time component are screened out.

## 7. Dedup rules

1. [search.py](../backend/app/adapters/search.py) canonicalizes URLs and removes known stored single-event pages before extraction; listings are read again.
2. [filters.py](https://github.com/alexisdacquay/sail-event/blob/542e58cb0fe73065a905febec7637bfa377a77c4/backend/app/services/filters.py#L217-L221) excludes a stored event-page/calendar-date match. A listing's own URL does not qualify as an event page.
3. [dedup.py](../backend/app/services/dedup.py) compares new accepted/queued events with same-day candidates after storage, using `dedup_v1`. A matched duplicate becomes `rejected` with a “Duplicate of …” reason. Errors or insufficient budget can leave both rows.

No title matching, in-run link/date check or uniqueness constraint silently drops
a second event with the same listing link and start.

## 8. Budget enforcement and backoff

[budget.py](../backend/app/services/budget.py) sums usage from today's run rows.
Defaults are 600 search credits and 5000 model calls. Judge reservations cover
up to three calls per event, with a process lock; this is not a multi-worker DB
reservation system. There is no per-search event cap.

The [search router](../backend/app/routers/search.py) applies six manual runs per
rolling hour by default. Scheduled requests enqueue up to 50 users, oldest last
run first, and skip unfinished runs started within 55 minutes. A 202 response
means enqueued, not completed. A restart can interrupt in-process tasks.

Retry behavior belongs to the selected adapter. Usage and `cost_usd` on the run
are incomplete (criteria/extraction tokens are omitted); they are not a complete
bill. See [spec §9](search-spec.md#9-cost-and-limits).

## 9. Observability

The observability stack runs locally with `make up-all`; the deployed app sends no telemetry.
[telemetry.py](../backend/app/telemetry.py) enables OTel only when
`OTEL_EXPORTER_OTLP_ENDPOINT` is set. Local traces and structured logs correlate
by trace ID; metric series do not carry it. This leaves a gap against “share a
trace ID” in the course rubric. HTTP paths can expose calendar-feed tokens;
see the [observability guide](../observability/README.md) for privacy limits.
The alert/responder evidence is from injected-fault drills, not live outages.

## 10. Testing

[docs/testing.md](../docs/testing.md) gives local, integration, e2e and live
commands. `make test` runs backend, frontend and responder checks;
`make test-all` also runs integration and e2e. Recorded tests do not establish
live model quality or recall. The [field runner](../backend/tests/field/runner.py)
adds live evaluation; it spends quota, and its ground truth remains unvetted.

## 11. Guardrails

The guard runs once on criteria save, not on fetched pages. With Lakera selected,
prompt-attack detection blocks save; self-check fallback is optional. Failure of
both returns 503. The default `GUARDRAIL=none` skips detection.

Extraction validates model output, strips markup and checks links. Detail fetch
checks public destinations and redirects; a second DNS lookup at connection
leaves a rebinding window. These are specific controls, not a guarantee that
untrusted pages cannot affect a model. Sources:
[criteria.py](../backend/app/routers/criteria.py),
[factory.py](../backend/app/adapters/factory.py),
[extract.py](../backend/app/services/extract.py),
[detail_hop.py](../backend/app/services/detail_hop.py).

## 12. Rollout order

The original v2 rollout is complete; do not execute the old “set keys before
pipeline swap” instructions. Use [release-process.md](../docs/release-process.md).
Prod promotion needs the owner's approval of a named commit and a database
backup. Rollback across the three new migrations is untested; PR #150's delete
is irreversible. `curl -s https://sail-event.onrender.com/api/health` prints the
deployed commit.

## 13. Implementation plan

Historical issue split, retained for links; closed issues describe their scope
at the time, not a claim that each old criterion still matches main.

### Issue A — Search v2 data model (migration first)

Delivered through [#54](https://github.com/alexisdacquay/sail-event/issues/54); use the current ORM/schema above.

### Issue B — LanguageModel adapter, prompt loader, clock (new files only)

Delivered through [#55](https://github.com/alexisdacquay/sail-event/issues/55).

### Issue C — Criteria understanding and window resolution

Delivered through [#56](https://github.com/alexisdacquay/sail-event/issues/56).

### Issue D — Search providers v2 and query planner (new files only)

Historical scope of [#57](https://github.com/alexisdacquay/sail-event/issues/57); the query planner was withdrawn.

### Issue E — Extraction, filters, dedup

Delivered through [#58](https://github.com/alexisdacquay/sail-event/issues/58), then revised by later extraction and duplicate work.

### Issue F1 — Judge, caps, golden B verdicts

Historical scope of [#59](https://github.com/alexisdacquay/sail-event/issues/59); `judge_v3` has no facet caps.

### Issue F2 — Pipeline swap, smoke script, deletions

Delivered through [#60](https://github.com/alexisdacquay/sail-event/issues/60).

### Issue G — Budgets, hourly queue, backoff, observability

Delivered through [#61](https://github.com/alexisdacquay/sail-event/issues/61); telemetry remains local.

### Issue H — Guardrails (small)

Delivered through [#62](https://github.com/alexisdacquay/sail-event/issues/62).

### Issue I — Queue card and run report in the UI (last)

Historical UI scope of [#63](https://github.com/alexisdacquay/sail-event/issues/63); the Stream design superseded the card/tab layout.

## 14. Decisions

The [PRD decisions](plan.md#decisions-made-for-the-mvp) record the product
tradeoffs; [ui-design.md](ui-design.md) records UI choices. Key technical costs:
full-content extraction spends model quota; event-page failures keep weaker
listing data; duplicate judgments can err; in-process background tasks are not
durable; a healthy HTTP service does not establish provider readiness.

## Review applied

[search-design-review.md](search-design-review.md) is the review of the earlier
proposal. It explains why the design changed; its old rollout and quantitative
estimates are not instructions or measurements of main.
