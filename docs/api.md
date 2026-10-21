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
| `getCalendarUrl`  | `getCalendarUrl` | GET    | `/api/calendar-url`         |
| `rotateCalendarUrl` | `rotateCalendarUrl` | POST | `/api/calendar/rotate`    |
| —                 | `getCalendarFeed`| GET    | `/api/calendar/{ics_token}` |

Event fields beyond the obvious: `decidedBy` is `auto` (triaged by the pipeline), `user` (decided in the queue) or null (still to review); `scoreReason` is the one-line reason shown under the title.

Changes in #95:
- `decideEvent` now accepts `decision: "queued"` to undo a decision (put back to review). Rejected events can now be decided (was 400).
- `saveThresholds` response now includes `eventsMoved: int` — the count of auto-decided events whose status changed to match the new thresholds.
