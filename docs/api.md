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
| `deleteAllEvents` | `deleteAllEvents`| DELETE | `/api/events`               |
| `getCalendarUrl`  | `getCalendarUrl` | GET    | `/api/calendar-url`         |
| `rotateCalendarUrl` | `rotateCalendarUrl` | POST | `/api/calendar/rotate`    |
| —                 | `getCalendarFeed`| GET    | `/api/calendar/{ics_token}` |

Run fields (`/api/search/last-run`, `/api/search`): `durationSeconds` is `finishedAt - startedAt`, null while running; `trigger` is `manual` or `scheduled`. `stageCounts` holds, after triage, `rejected_date_place` (score 0-9: wrong city/country or dates), `rejected_off_topic` (10-39) and `rejected_other` (40 up to the lower threshold); the three sum to `rejected` and are present (0) on every finished run.

`GET /api/search/runs?limit=20` returns `{"runs": [RunSummary]}`, the caller's runs newest first, `limit` 1-100. `RunSummary` = `{runId, startedAt, finishedAt, durationSeconds, trigger, eventsFound, accepted, queued, rejected, setAside, pagesRead, pagesSkipped, error}`. Event-level: `eventsFound = events_extracted`; `setAside` is every extracted event that got no verdict, `filtered_incomplete + filtered_past + filtered_date + filtered_place + filtered_duplicate + events_capped + judge_errors` (`events_capped` = kept events over `MAX_EVENTS_PER_RUN`), so `accepted + queued + rejected + setAside == eventsFound` on every finished run. Page-level: `pagesRead = results_fetched`, `pagesSkipped = filtered_non_event`.

Event fields beyond the obvious: `decidedBy` is `auto` (triaged by the pipeline), `user` (decided in the queue) or null (still to review); `scoreReason` is the one-line reason shown under the title.
