# API mapping

| Frontend function | operationId      | Method | Path                        |
|-------------------|------------------|--------|-----------------------------|
| `register`        | `register`       | POST   | `/api/auth/register`        |
| `login`           | `login`          | POST   | `/api/auth/login`           |
| `getCriteria`     | `getCriteria`    | GET    | `/api/criteria`             |
| `saveCriteria`    | `saveCriteria`   | PUT    | `/api/criteria`             |
| `getThresholds`   | `getThresholds`  | GET    | `/api/thresholds`           |
| `saveThresholds`  | `saveThresholds` | PUT    | `/api/thresholds`           |
| `runSearch`       | `runSearch`      | POST   | `/api/search`               |
| `listEvents`      | `listEvents`     | GET    | `/api/events`               |
| `decideEvent`     | `decideEvent`    | POST   | `/api/events/{id}/decision` |
| `getConfig`       | `getConfig`      | GET    | `/api/config`               |
| —                 | `healthCheck`    | GET    | `/api/health`               |
| —                 | `searchAll`      | POST   | `/api/search/all`           |
| `getLastRun`      | `getLastRun`     | GET    | `/api/search/last-run`      |
| `getRuns`         | `getRuns`        | GET    | `/api/search/runs`          |
| —                 | `getRun`         | GET    | `/api/search/runs/{run_id}` |
| `deleteAllEvents` | `deleteAllEvents`| DELETE | `/api/events`               |
| `getCalendarUrl`  | `getCalendarUrl` | GET    | `/api/calendar-url`         |
| `rotateCalendarUrl` | `rotateCalendarUrl` | POST | `/api/calendar/rotate`    |
| —                 | `getCalendarFeed`| GET    | `/api/calendar/{ics_token}` |

The endpoint contract is [openapi.yaml](../openapi.yaml); the frontend implementation is [http.ts](../frontend/src/services/http.ts). The fields below follow [the search router](https://github.com/alexisdacquay/sail-event/blob/542e58cb0fe73065a905febec7637bfa377a77c4/backend/app/routers/search.py#L30-L91) and pipeline code. Known contract gap: OpenAPI still describes counter version 3 as current; the implementation writes version 4.

## Run responses

`POST /api/search` returns the finished run directly. `GET /api/search/last-run` returns `{"run": RunDetail}` or `{"run": null}`. `GET /api/search/runs/{run_id}` returns the caller’s own run in the same wrapper, or 404. Run detail includes:

| Field | Meaning |
|---|---|
| `runId`, `trigger` | Run identifier; trigger is `manual` or `scheduled` |
| `startedAt`, `finishedAt`, `durationSeconds` | Timestamps; duration is their difference in seconds, rounded to one decimal; null until both exist |
| `eventsFound`, `eventsNew` | Pipeline run totals; use the event-level history fields below for the funnel |
| `stageCounts`, `countsVersion` | Stage counters and their stored format version; counters may be absent before the corresponding stage runs |
| `currentStage`, `stoppedAtStage`, `error` | Live stage; stage where work stopped; error message. A finished run clears `currentStage` |
| `pages` | Fetched result pages as `{url, title, events, kind}`; `events` is a count. `kind` is `single_event`, `listing`, `not_event`, `no_content` or `error`. Null on runs stored before [page recording](https://github.com/alexisdacquay/sail-event/issues/124) |

### Stage counters

Counter format versions: 4 includes event-page counters; 3 predates those counters; 2 predates `filtered_no_date`; 1 predates reject bands. When a detailed response reads older counters, it recomputes reject bands from the run’s stored events. The history summary reads stored counters without that recomputation.

| Group | Counter | Meaning |
|---|---|---|
| Pages | `results_fetched`, `results_known` | Results returned by search; result pages already represented by stored events and skipped before extraction |
| Pages | `pages_content_pass`, `pages_with_events`, `filtered_non_event` | Full-content reads; pages yielding events; pages yielding no events. A result with no content can take a snippet-only extraction path |
| Extraction | `events_extracted`, `extract_errors` | Extracted events; failed result-page extractions |
| Event pages | `detail_pages_done`, `detail_pages_to_open` | Live progress while `currentStage` is `detail_hop` |
| Event pages | `pages_detail_fetched`, `detail_fetch_errors`, `detail_extract_errors` | Successful event-page fetches; fetch failures; model re-extraction failures. On failure, the listing record continues to filtering |
| Filtering | `filtered_no_date`, `filtered_no_time`, `filtered_incomplete`, `filtered_past`, `filtered_date`, `filtered_place`, `filtered_duplicate` | Event screen-out counts; these are separate from pages that yielded no events |
| Judging | `events_to_judge`, `events_judged` | Live total entering the judge; events processed by the judge |
| Judging | `judge_errors`, `recovery_judge_errors` | This run’s events that could not be scored; failures while retrying older events. Unscored events stay `new` for later recovery |
| Judging | `judge_repaired` | Responses repaired after schema validation failed; successfully scored events are excluded from `judge_errors` |
| Triage | `accepted`, `queued`, `rejected` | Stored outcomes after judging and duplicate checking |
| Rejection | `rejected_date_place`, `rejected_off_topic`, `rejected_other` | Rejected scores 0–9, 10–39 and 40 or more, excluding model-marked duplicates. The last band includes user rejections as well as threshold rejections |
| Duplicates | `dedup_merged`, `dedup_errors` | New events moved to Out by the model duplicate check; failed checks, which keep both events |

The three reject bands plus `dedup_merged` account for the run’s rejected events at finalization. Run counters are snapshots; later user decisions do not rewrite them. There is no per-search event cap, but the daily model-call budget can stop judging early.

## Run history

`GET /api/search/runs?limit=20` returns `{"runs": [RunSummary]}`, newest first; `limit` accepts 1–100. Each summary includes identity, timing, trigger, counter version, error and these funnel fields:

| Field | Stored counter or calculation |
|---|---|
| `eventsFound` | `events_extracted` |
| `accepted`, `queued`, `rejected` | Corresponding triage counts |
| `setAside` | `filtered_no_date + filtered_no_time + filtered_incomplete + filtered_past + filtered_date + filtered_place + filtered_duplicate + judge_errors` |
| `pagesRead`, `pagesWithEvents`, `pagesSkipped` | `results_fetched`, `pages_with_events`, `filtered_non_event` |

The intended event identity is `accepted + queued + rejected + setAside == eventsFound`. Treat a run that stopped early or failed as incomplete: counters can be missing, and budget-limited unjudged events are not included in `setAside`. Page counts and event counts are different units.

## Event decisions

`decidedBy` is `auto`, `user` or null; null also applies to queued events awaiting a decision. `scoreReason` is the model’s explanation shown with the event. Out events remain available through the UI’s **show** toggle; later searches do not restore them to the queue.
