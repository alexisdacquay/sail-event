# Search and scoring — design (v2)

How `search-spec.md` is built. Paths are repo-relative. Nothing here is implemented yet; section 11 is the order.

## 1. Pipeline stages

`run_pipeline(user, db, trigger)` stays the single entry point and keeps its contract: always writes a Run row, commits events as `new` before judging, recovers leftover `new` events first. Inside, the stages become functions in `backend/app/services/stages/`, one file each, pure where possible.

| # | Stage | Module | Input | Output | Model call | 12-factor |
|---|---|---|---|---|---|---|
| 1 | understand criteria | `criteria.py` | `Criteria.text`, `User.time_zone` | `Facets` (pydantic), stored on `Criteria.facets_json` | 1, only when `text` changed since `parsed_at` | 2 prompts as files, 4 structured output |
| 2 | resolve window | `window.py` | `Facets.date`, now, user tz | `Window(start_utc, end_utc, tz)` | none | 8 control flow in code |
| 3 | plan queries | `planner.py` | `Facets`, `Window`, trigger, run ordinal | `list[PlannedQuery(text, country, language, priority)]` | none | 8 |
| 4 | search | `search.py` | queries, `SearchProvider` | `list[SearchResult]` deduped by canonical URL, known links removed | none | 10 small steps |
| 5 | extract | `extract.py` | one `SearchResult`, `Window`, target place, today | `list[ExtractedEvent]`, `page_kind` | 1 per result | 4 |
| 6 | filter | `filters.py` | `ExtractedEvent`s, `Window`, `Facets.place`, stored events | kept events + `FilterCounts` | none | 8 |
| 7 | judge | `judge.py` | one event, criteria text, `Facets`, `Window` | `Verdict(score, reason, flags)` → capped score | 1 per event | 4, 12 stateless |
| 8 | triage | existing `_score_and_triage` logic | score, thresholds | status | none | 7 humans via the queue, 8 |
| 9 | persist run | `pipeline.py` | counts, calls, tokens, stop reason | `Run` row | none | 5 state in the DB |

Control flow rules:

- Each stage returns data; `pipeline.py` loops and counts. No stage calls another.
- A model response that fails its schema raises; the run records the error. Nothing is guessed.
- Errors from one query or one page are compacted into the run: the item is skipped, a counter incremented, the first error message kept in `Run.error_detail` as `<stage>: <ExceptionType>: <message[:200]>`. The run fails only when a whole stage produced nothing because of errors.
- Stage 1 runs before the budget check for the run because it is at most one call per text change.

## 2. Data model changes

One Alembic migration `backend/alembic/versions/<rev>_search_v2.py`, first issue.

| Table | Column | Type | Null | Note |
|---|---|---|---|---|
| users | time_zone | String(64) | no, default `UTC` | IANA name; set from the browser on criteria save |
| criteria | facets_json | Text | yes | JSON of `Facets` |
| criteria | facets_version | String(16) | yes | prompt version that produced it, e.g. `criteria_v2` |
| criteria | parsed_at | DateTime(tz) | yes | compare with `updated_at`: re-parse when `updated_at > parsed_at` or version differs |
| events | date_time | String | no | unchanged type; now always ISO-8601 local with offset when the zone is known, `YYYY-MM-DDTHH:MM` otherwise |
| events | start_tz | String(64) | yes | IANA; null = unknown zone |
| events | end_time | String | yes | same format as `date_time` |
| events | city | String | no | from extraction |
| events | country | String(2) | no | ISO-3166-1 alpha-2 |
| events | price_amount | Float | yes | null = unknown; 0 = free |
| events | price_currency | String(3) | yes | ISO-4217 |
| events | source_query | String | yes | the planned query text that surfaced the page |
| events | extraction_confidence | Float | yes | 0–1 |
| events | judge_model | String | yes | renamed from `scorer_model` (`op.alter_column(new_column_name=...)`) |
| events | judge_version | String(16) | yes | e.g. `judge_v2` |
| runs | stage_counts | Text | yes | JSON: `queries_planned, results_fetched, results_known, events_extracted, filtered_past, filtered_date, filtered_place, filtered_non_event, filtered_duplicate, events_judged, accepted, rejected, queued, search_errors, extract_errors` |
| runs | search_calls | Integer | no, default 0 | |
| runs | llm_calls | Integer | no, default 0 | |
| runs | llm_tokens_in | Integer | no, default 0 | 0 when the API returns no usage |
| runs | llm_tokens_out | Integer | no, default 0 | |
| runs | cost_usd | Float | yes | null when unit prices are unset |
| runs | stopped_at_stage | String(16) | yes | `search`, `extract`, `judge`; null = completed |
| runs | error_detail | Text | yes | compacted first error; `error` keeps the run-level message |

- Existing rows: `city`/`country` backfilled with `''`/`'ZZ'` (user-assigned ISO code = unknown) in the migration; the UI shows them as "place unknown". `time_zone` backfilled `UTC`.
- `UNIQUE(user_id, link)` stays; `link` is now the canonical link (section 7).
- API (`openapi.yaml`, `models.py`): `Event` gains `startTz`, `endTime`, `city`, `country`, `priceAmount`, `priceCurrency`; `SearchResult` gains `stageCounts`, `stoppedAtStage`, `error`; `SaveCriteriaRequest` and `Criteria` gain optional `timeZone`. Additive only.

## 3. Adapters

### SearchProvider (revised)

```
class SearchResult(BaseModel):
    url: str; title: str; snippet: str
    raw_content: str | None      # page text when the provider returns it
    published_at: str | None     # ISO date when known
    provider: str

class SearchProvider(Protocol):
    name: str
    def search(self, query: str, *, country: str | None, language: str | None,
               freshness_days: int | None, max_results: int) -> list[SearchResult]: ...
```

| Implementation | File | Request | Mapping |
|---|---|---|---|
| `TavilySearchProvider` | `adapters/search_tavily.py` (rewrite) | POST `https://api.tavily.com/search` body `{query, search_depth: "basic", max_results, country, include_raw_content: true}`; `freshness_days` ignored (no general-web control) | `results[].url/title/content/raw_content/published_date` |
| `BraveSearchProvider` | `adapters/search_brave.py` (new) | GET `https://api.search.brave.com/res/v1/web/search?q&country&search_lang&count&freshness=YYYY-MM-DDtoYYYY-MM-DD&extra_snippets=true`, header `X-Subscription-Token` | `web.results[].url/title/description + extra_snippets joined` as snippet; `raw_content` null; `page_age` → published_at |
| `FixtureSearchProvider` | `adapters/fixture.py` | reads `adapters/fixtures.json` | fixture becomes a list of `SearchResult`s shaped like the golden set pages (section 10); the old event fixtures go |

- Both real providers use `urllib.request` as today; no new dependency.
- Page content handed to extraction: `title + "\n" + snippet + "\n" + raw_content[:8000]`.
- Date-string regexes in `search_tavily.py` are deleted; extraction owns dates.
- `RawEvent` is deleted once `ExtractedEvent` (section 5) replaces it.

### LanguageModel (new)

```
class LanguageModel(Protocol):
    model_id: str                           # "<provider>:<model>"
    def complete_json(self, *, prompt_name: str, prompt_version: str,
                      variables: dict[str, str], schema: dict) -> tuple[dict, Usage]: ...
```

| Implementation | File | Transport | Structured output |
|---|---|---|---|
| `AnthropicModel` | `adapters/llm_anthropic.py` | `anthropic` SDK (already pinned), `timeout=30, max_retries=1`, temperature 0 | `output_config.format = {type: json_schema, strict: true, schema}` as the current scorer does |
| `OpenAICompatibleModel` | `adapters/llm_openai_compat.py` | `urllib.request` POST `{LLM_BASE_URL}/chat/completions`, bearer `LLM_API_KEY`, temperature 0, timeout 30, one retry on 429/5xx after 2 s | `response_format: {type: json_schema, json_schema: {name, schema, strict: true}}`; on HTTP 400 that names `response_format`, retry once with `{type: json_object}` and the schema already in the prompt text; the fallback increments metric `sail_llm_json_mode_fallback_total` |
| `FakeLanguageModel` | `adapters/llm_fake.py` | replays `backend/tests/fixtures/llm/<prompt_name>_<prompt_version>/<sha256(rendered prompt)[:16]>.json` | a missing recording raises `FileNotFoundError` with the prompt name and hash: no silent default |

- Every implementation validates the returned JSON against `schema` with pydantic before returning; failure raises `RuntimeError("<prompt_name>: schema violation: ...")`.
- `Usage(tokens_in, tokens_out)` from the API; zeros when absent.
- Prompt rendering: `adapters/prompts/loader.py` reads `prompts/<name>_<version>.md` and `prompts/<name>_<version>.schema.json`, renders with `str.format` on named variables, and returns both; the adapters never build prompt text.
- The Nous Portal key is used through `OpenAICompatibleModel` with `LLM_BASE_URL` set to the portal's OpenAI-compatible base; the owner sets the model name in `LLM_MODEL`.

### Environment variables

| Variable | Where | Values / default |
|---|---|---|
| `SEARCH_PROVIDER` | Render, `.env.example` | `fixture` (default outside prod), `tavily`, `brave` |
| `TAVILY_API_KEY`, `BRAVE_API_KEY` | Render only | required by the selected provider; startup fails without it |
| `LLM_PROVIDER` | Render, `.env.example` | `fake` (default outside prod), `anthropic`, `openai_compatible` |
| `ANTHROPIC_API_KEY` | Render only | for `anthropic` |
| `LLM_BASE_URL`, `LLM_API_KEY` | Render only | for `openai_compatible` |
| `LLM_MODEL` | Render, `.env.example` | model name for either real provider; default `claude-haiku-5-5` for anthropic, required for openai_compatible |
| `MAX_QUERIES_PER_RUN` | `.env.example` | 6 manual; scheduled runs use `MAX_QUERIES_SCHEDULED` = 2 |
| `MAX_RESULTS_PER_QUERY` | `.env.example` | 6 |
| `MAX_EVENTS_PER_RUN` | existing | 50 |
| `SEARCH_DAILY_CALLS`, `LLM_DAILY_CALLS` | `.env.example` | 500, 3000 |
| `LLM_USD_PER_1K_IN`, `LLM_USD_PER_1K_OUT`, `SEARCH_USD_PER_CALL` | optional | unset = `cost_usd` null |
| `SCORER`, `SCORER_MODEL` | removed | `factory.py` raises `ValueError("SCORER is replaced by LLM_PROVIDER")` when set |

- `factory.py`: `get_search_provider()`, `get_language_model()`; with `APP_ENV=prod`, `fixture` or `fake` raises at import of `main.py` (startup), message names the variable.
- `docs/deployment.md` and `.env.example` updated in the same issue as the adapter.

## 4. Prompts

Files in `backend/app/adapters/prompts/`, all version `v2`; `scorer_v1.md` deleted with the old scorer.

| Prompt | Files | Variables | Output schema (JSON Schema, `additionalProperties: false` everywhere) |
|---|---|---|---|
| criteria understanding | `criteria_v2.md`, `criteria_v2.schema.json` | `text`, `today`, `user_tz` | `Facets` below |
| event extraction | `extract_v2.md`, `extract_v2.schema.json` | `today`, `window_start`, `window_end`, `target_city`, `target_country`, `url`, `content` | `Extraction` below |
| judge | `judge_v2.md`, `judge_v2.schema.json` | `criteria_text`, `facets_json`, `window_start`, `window_end`, `event_json`, `today` | `Verdict` below |

`Facets`:

```
{ "place": {"city": str|null, "country": str|null (ISO-2), "region": str|null,
            "radius_km": number|null, "online": bool} | null,
  "date": {"start": "YYYY-MM-DD"|null, "end": "YYYY-MM-DD"|null,
           "relative": "today"|"tomorrow"|"this_week"|"next_week"|"this_weekend"|
                       "next_weekend"|"this_month"|"next_month"|"next_n_days"|null,
           "relative_n": int|null},
  "topics": [str], "topics_local": [str],
  "formats": ["concert"|"festival"|"workshop"|"meetup"|"talk"|"exhibition"|"party"|
              "sport"|"market"|"webinar"|"other"],
  "budget": {"max_amount": number|null, "currency": str|null, "free_only": bool},
  "language": str|null (BCP-47 of the place), "input_language": str,
  "other_constraints": [str] }
```

`Extraction`:

```
{ "page_kind": "single_event"|"listing"|"not_event",
  "events": [ { "title": str, "start_local": str ("YYYY-MM-DD" or "YYYY-MM-DDTHH:MM"),
                "tz": str|null, "end_local": str|null, "venue": str|null,
                "city": str|null, "country": str|null, "link": str,
                "price_amount": number|null, "price_currency": str|null, "is_free": bool|null,
                "description": str (≤200), "confidence": number (0–1) } ] }   # ≤ 10 items
```

`Verdict`:

```
{ "score": int (0–100), "reason": str (≤140),
  "fit": {"place": "yes"|"no"|"unknown", "date": "yes"|"no"|"unknown",
          "topic": "yes"|"no"|"unknown", "budget": "yes"|"no"|"unknown"},
  "is_event": bool }
```

Prompt content rules (own your prompts: the `.md` is the whole instruction, no text built in code):

- `criteria_v2.md`: role, the facet table from spec §3, the rule "relative expressions are returned as the enum, never resolved; seasons and holidays become absolute dates", "topics_local in the language of the place", two examples (C1, C5 from golden set A), then `{text}`.
- `extract_v2.md`: role, "today is {today}", "the user wants events in {target_city}, {target_country} between {window_start} and {window_end}; from a programme page return only occurrences in that range, at most 10", field rules from spec §5, "do not judge fit", one single-event example and one listing example (E1 page, A-Trane programme page) and one not_event example (E14), then `{url}` and `{content}`.
- `judge_v2.md`: role, the rubric table from spec §7 verbatim, the sentence pattern and the example sentence, "write to the user: your dates, your budget", "flags are facts, the score is your judgement", three few-shot examples from golden set B with full output: E1 → 94, `Jazz trio at A-Trane in Berlin on Tue 20 Oct, 18 EUR: fits your dates and topic` flags all yes/budget unknown; E20 → 12, `Techno night at Berghain in Berlin on 20 Oct: right place and dates, not jazz`, topic no; E4 → 78, `Jazz vocal workshop in Berlin on 21 Oct: fits your dates and topic, a workshop rather than a concert`.

Code after the judge (`judge.py`): apply the caps table from spec §7 to `score`; `is_event = false` → score 0 and the event is dropped with `filtered_non_event`; `reason` trimmed to 140; empty reason → error.

## 5. Query planning rules

`planner.py`, pure function `plan(facets, window, *, max_queries, offset) -> list[PlannedQuery]`.

| Order | Template | Condition |
|---|---|---|
| 1 | `{topic} {city} {Month} {year}` | per topic (first 2); no topic → `events {city} {Month} {year}` |
| 2 | `{topic_local} {city} {Month_local} {year}` | language ≠ en, per topic_local (first 2) |
| 3 | `{topic} {format} {city} {day_phrase}` | `day_phrase` = `19–21 October 2026` for a window ≤ 7 days, else `{Month} {year}`; format = first format or `concert`/`event` |
| 4 | `{city} {events_word_local} {topic_local} {day_phrase_local}` | language ≠ en; `events_word_local` from a 12-entry table in code (de Veranstaltungen, fr événements, es eventos, pt eventos, it eventi, nl evenementen, ja イベント, …) |
| 5 | `{topic} {city} tickets {Month} {year}` | always |
| 6 | `{topic} {city} programme this week` / `program {Month} {year}` | window ≤ 7 days |
| 7 | `{topic} online {Month} {year}` | `place.online` and no city |

- Queries deduplicated case-insensitively, truncated to `max_queries` in order; `offset` rotates the start index for scheduled runs (`offset = count of the user's scheduled runs mod len(plan)`) so two queries per hour cover the whole plan in three hours.
- `country` = `place.country`; `language` = `facets.language` for templates 2 and 4, `en` otherwise; `freshness_days` = 90.
- No city and not online → empty plan; the run records `stopped_at_stage = "search"`, `error = "no place in criteria"`.
- Month names: `calendar.month_name` for English; a 12-entry month table per supported language in code (de, fr, es, pt, it, nl); other languages fall back to English for template 2.

Example, C1 (Berlin jazz, window 19–21 Oct 2026, language de):

1. `jazz Berlin October 2026`
2. `Jazz Berlin Oktober 2026`
3. `jazz concert Berlin 19–21 October 2026`
4. `Berlin Veranstaltungen Jazz 19.–21. Oktober 2026`
5. `jazz Berlin tickets October 2026`
6. `jazz Berlin programme this week`

Example, C4 (`something fun in Lisbon this weekend`, run 2026-10-18 → window Sat 24 – Sun 25 Oct 2026, no topics, language pt):

1. `events Lisbon October 2026`
2. `eventos Lisboa Outubro 2026`
3. `events Lisbon 24–25 October 2026`
4. `Lisboa eventos 24–25 outubro 2026`
5. `events Lisbon tickets October 2026`
6. `events Lisbon programme this week`

Example, C3 (`something fun this weekend`, no place): empty plan, run stops, report `no place in criteria`.

## 6. Relative dates and time zones

- `User.time_zone` (IANA) set by the frontend from `Intl.DateTimeFormat().resolvedOptions().timeZone` on every criteria save; default `UTC`.
- `window.py`: `resolve(facets.date, now_utc, tz) -> Window`; `now_local = now_utc.astimezone(ZoneInfo(tz))`; ISO weeks Monday–Sunday; weekend = Saturday 00:00 → Sunday 23:59:59; `next_n_days` = `now_local` → `now_local + n days` end of day; absolute dates win; neither → `now_local` → `+30 days`. Start is `max(window start, now_local)`.
- `Window` carries `start_utc`, `end_utc`, `tz`; filters compare in UTC.
- Event instant: `start_local` parsed with `start_tz` when known; unknown zone → country's single zone from a code table (`DE → Europe/Berlin`, `AT`, `FR`, `GB`, `PT`, `NL`, `JP`, …; multi-zone countries such as `US`, `AU`, `BR`, `RU`, `CA` → null); still unknown → compared in the user's zone and stored with `start_tz = null`.
- `date_time` stored as `YYYY-MM-DDTHH:MM:SS+02:00` when the zone is known, local naive otherwise; `start_tz` stored beside it so the UI can print `21:00 (Europe/Berlin)` and the user's zone next to it when different. Date-only events are stored as `YYYY-MM-DD` with no time; the past filter treats them as starting at 00:00 and the UI prints the date only.
- ICS: `DTSTART;TZID=<start_tz>` when known, floating local time otherwise (unchanged behaviour for the unknown case).

## 7. Dedup rules

`filters.py`:

| Rule | Definition |
|---|---|
| Canonical link | lowercase scheme and host; drop default port and fragment; drop query keys `utm_*`, `fbclid`, `gclid`, `ref`, `source`; strip trailing `/`; keep everything else |
| Known link | canonical link already stored for the user (any status) → dropped before extraction, counted `results_known` |
| In-run link | second occurrence of a canonical link in the run → dropped, counted `filtered_duplicate` |
| Title key | title lowercased, punctuation removed, tokens split on whitespace, stopwords removed (en, de, fr, es, pt, it, nl short lists: the/a/an/of/at/in/and/der/die/das/im/am/le/la/de/du/el/los/y/o/e/het/een) |
| Near-match | same local calendar date and (Jaccard of title keys ≥ 0.8 or one key set ⊂ the other) |
| Near-match scope | the user's stored events with the same calendar date (one query on `date_time LIKE 'YYYY-MM-DD%'`) and the events kept so far in the run |
| Winner | the first seen; a near-match of a stored `rejected` event is dropped without insertion |

## 8. Budget enforcement and backoff

- `budget.py`: `daily_used(db, column) = SUM(runs.<column>) WHERE started_at >= today 00:00 UTC`; checked before search (`search_calls + len(plan) > SEARCH_DAILY_CALLS`) and before each model call (`llm_calls + 1 > LLM_DAILY_CALLS`).
- On breach: the stage stops, `Run.stopped_at_stage` set, `Run.error = "budget: search"` or `"budget: llm"`, run finishes normally, HTTP 200 with the report; events already inserted as `new` wait for the next run's recovery.
- Per-run caps: `MAX_QUERIES_*`, `MAX_RESULTS_PER_QUERY`, extraction ≤ results after known-link removal, judge ≤ `MAX_EVENTS_PER_RUN` (the rest stay `new`, recovered next run).
- Backoff: provider or model HTTP 429/5xx → one retry after 2 s; second failure skips that item (query or page) and counts `search_errors` / `extract_errors`; a judge failure raises and fails the run after the already-judged events are committed (current behaviour).
- `/api/search/all` keeps its per-user isolation: a budget stop for one user does not stop the others, but once the daily cap is hit every subsequent user's run records the same stop.
- Cost: `cost_usd = llm_tokens_in/1000 × LLM_USD_PER_1K_IN + llm_tokens_out/1000 × LLM_USD_PER_1K_OUT + search_calls × SEARCH_USD_PER_CALL`, null when any price is unset.

## 9. Observability

- Spans under `search_run`: `criteria`, `plan`, `search` (one child per query with `provider`, `result_count`), `extract` (one child per page with `page_kind`, `event_count`), `filter`, `judge` (one child per event with `score`, `capped`), `triage`, `persist`.
- Span attributes and log records carry counts, versions, provider and model names, latency, token counts, hashes. Never criteria text, query text, page content, prompt bodies, event titles or descriptions. Query text appears only as `sha256[:12]`.
- Metrics (existing meter): `sail_stage_items_total{stage, outcome}` where outcome is the filter reason or `kept`; `sail_llm_calls_total{prompt, provider}`; `sail_llm_tokens_total{direction}`; `sail_search_calls_total{provider, outcome}`; `sail_budget_stops_total{which}`; `sail_llm_json_mode_fallback_total`; existing run counters unchanged.
- A test asserts that running the pipeline with a sentinel criteria string leaves no log record or span attribute containing the sentinel.

## 10. Testing

| Layer | Location | What |
|---|---|---|
| Stage unit tests | `backend/tests/stages/test_<stage>.py` | each stage with hand-built inputs; `window.py` on fixed `now`; `planner.py` on golden facets; `filters.py` on golden set B; `judge.py` caps on hand-made verdicts |
| Recorded model responses | `backend/tests/fixtures/llm/<prompt>_<version>/<hash>.json` | one file per rendered prompt; `{"response": {...}, "usage": {...}, "recorded_at", "model"}` |
| Golden set A | `backend/tests/golden/criteria.json` + `test_golden_criteria.py` | 13 texts → expected `Facets` (field-level compare; `topics_local` compared as a non-empty check) |
| Golden set B | `backend/tests/golden/candidates.json` + `test_golden_candidates.py` | 22 pages as `SearchResult`s → run `extract → filter → judge` with the fake model; assert the expected counter or score band per row |
| Provider contract | `backend/tests/test_search_tavily.py`, `test_search_brave.py`, fixtures under `tests/fixtures/{tavily,brave}/` | request body/params built as specified; recorded response → `SearchResult` mapping; 401/429/5xx handling; missing key |
| Model contract | `test_llm_anthropic.py`, `test_llm_openai_compat.py` | request shape, schema validation failure raises, json_object fallback on 400, usage parsing |
| Pipeline | `test_pipeline.py` (rewritten where it touches `derive_queries`, `RawEvent`, `get_scorer`) | run counts, budget stop, no-place stop, recovery, prod refuses fakes |
| Smoke, real keys | `backend/scripts/smoke_search.py`, documented in `docs/testing.md` | `uv run python backend/scripts/smoke_search.py --criteria "<C1 text>" --tz Europe/Berlin [--record]`; runs every stage against the live provider and model, prints the run report and one line per judged event (score, flags, sentence, when, where, link); `--record` writes model responses into `tests/fixtures/llm/` for the golden sets; `--repeat 3` prints the score spread per event for the ±5 check |

- CI never reaches the network: `LLM_PROVIDER=fake`, `SEARCH_PROVIDER=fixture`, recordings committed.
- A prompt edit changes every hash; the smoke script with `--record` regenerates the recordings for the golden sets in one pass; the diff of recorded scores is reviewed in the PR.

## 11. Implementation plan

Issues in dependency order; each one engineer session.

### Issue A — Search v2 data model (migration first)
1. Alembic migration adds every column in §2, renames `scorer_model` → `judge_model`, backfills `city`/`country`/`time_zone`.
2. `orm.py` and `models.py` match; `openapi.yaml` gains the additive fields; the contract test passes.
3. `PUT /api/criteria` accepts `timeZone` and stores it on the user; invalid IANA name → 400.
4. `GET /api/events` returns the new fields; existing tests pass with backfilled defaults.
5. `alembic upgrade head` and `downgrade -1` both succeed on SQLite and Postgres (compose).

### Issue B — LanguageModel adapter and prompt loader
1. `LanguageModel` protocol, `AnthropicModel`, `OpenAICompatibleModel`, `FakeLanguageModel` as in §3, no new dependency.
2. Prompt loader reads `<name>_<version>.md` + `.schema.json`; rendering a prompt with a missing variable raises.
3. Schema validation on every response; violation raises with the prompt name.
4. `factory.get_language_model()` by `LLM_PROVIDER`; `SCORER` set → clear error; `APP_ENV=prod` + `fake` → startup error.
5. Contract tests for both real adapters against recorded responses, including the json_object fallback and 429 retry.
6. `.env.example` and `docs/deployment.md` list the new variables; `scorer_claude.py`, `scorer_v1.md`, `fake.py` deleted.

### Issue C — Criteria understanding and window resolution
1. `criteria_v2.md` + schema; `criteria.py` parses when `updated_at > parsed_at` or version differs, stores `facets_json`, `facets_version`, `parsed_at`.
2. `window.py` resolves every relative value from §6 on a fixed `now`; absolute wins; default 30 days; start clipped to now.
3. Golden set A file with 13 entries and recorded parser responses; `test_golden_criteria.py` passes.
4. Unit tests: week and weekend boundaries across a year end and a DST change in `Europe/Berlin`.
5. No criteria text in logs (sentinel test).

### Issue D — Search providers v2 and query planner
1. `SearchProvider` signature from §3; `TavilySearchProvider` rewritten (country, raw content, no date regex); `BraveSearchProvider` new; `FixtureSearchProvider` returns `SearchResult`s from the rewritten `fixtures.json`.
2. `planner.py` implements §5; the C1 and C4 examples are the test expectations verbatim; no place and not online → empty plan.
3. Scheduled rotation: `offset` cycles through the plan across runs (test with three consecutive scheduled runs).
4. Contract tests for Tavily and Brave against recorded responses; request params asserted.
5. Known links removed before extraction (`results_known` counted).

### Issue E — Extraction, filters, dedup
1. `extract_v2.md` + schema; `extract.py` returns ≤ 10 events per page, confidence < 0.5 dropped.
2. `filters.py` implements §6 order from the spec and §7 of this design; every drop increments its counter.
3. Canonical link function unit-tested on the utm, fragment, trailing-slash and port cases.
4. Near-match unit-tested on E19 ("A-Trane: Jazz Trio" vs "Jazz Trio at A-Trane") and on a non-match with the same date.
5. Golden set B file with 22 entries and recorded extraction responses; filter expectations for E5–E19 pass.
6. A near-match of a `rejected` stored event is not inserted.

### Issue F — Judge, triage, pipeline wiring, smoke script
1. `judge_v2.md` + schema with the rubric and the three few-shot examples; `judge.py` applies the caps table; empty reason raises.
2. `pipeline.py` runs the nine stages, records `stage_counts`, calls, tokens, `stopped_at_stage`, `error_detail`; recovery of `new` events unchanged.
3. `derive_queries`, `RawEvent`, `Scorer`, `get_scorer` removed; `test_pipeline.py` rewritten accordingly; all backend tests pass.
4. Golden set B judge expectations (E1–E4, E20–E22 bands) pass with recorded verdicts.
5. `SearchResult` API response carries `stageCounts`, `stoppedAtStage`, `error`.
6. `backend/scripts/smoke_search.py` with `--record` and `--repeat`; `docs/testing.md` "Real adapters smoke" section replaced.
7. Owner runs the smoke on C1 with live keys: ≥ 3 real Berlin jazz events in the window, zero outside Germany or the window.

### Issue G — Budgets, backoff, observability
1. `budget.py` daily sums; search and model stops as in §8 with run fields set and HTTP 200.
2. 429/5xx retry-once-then-skip for queries and pages; counters `search_errors`, `extract_errors`; first error in `error_detail`.
3. Spans and metrics from §9; sentinel test proves no criteria, query or event text in logs or span attributes.
4. `cost_usd` computed when prices are set, null otherwise.
5. `/api/search/all` test: second user after a budget stop records the same stop and the endpoint still returns 200.

### Issue H — Queue card and run report in the UI (last)
1. Card shows `Score NN%`, the reason sentence without a label, When as `Tue 20 Oct 2026, 21:00 (Europe/Berlin)` plus the user's zone when different, Where as venue, city, country, Price when known.
2. Unknown zone prints the local time with "local time"; date-only events print the date only.
3. After "Search now" the page shows the run report line from spec §8 and the stop reason when present.
4. The frontend sends `timeZone` with every criteria save.
5. Component tests beside the card and the report; e2e journey 1 updated for the new card text; README screenshots refreshed.

## 12. Decisions

| Decision | Strongest fact against it |
|---|---|
| Hard filters in code before the judge, not "let the model decide everything" | The plan says "the judgement is the product" and dropped structured filters once; this reintroduces them, on facts the model extracted |
| Query planning by templates in code, no model call | Templates cannot know venue names or local listing sites; recall depends on the provider's ranking of generic queries |
| Tavily primary, Brave optional, Serper deferred | Serper (Google) likely has the best local-event recall; it is deferred on provider count, not on evidence |
| One extraction call per result page | It is the dominant model cost; a batched call would be cheaper but the small-steps rule and per-page error isolation win |
| Extraction decides page kind; a page with no dated event is a non-event | A real event page whose date is in an image or a script yields nothing and is counted as non-event, invisibly to the user |
| Country match hard, city match hard unless a radius is given, no geocoding | "Potsdam" with a 30 km radius reaches the judge, which must know geography; "Berlin-Kreuzberg" relies on the extractor normalising the city |
| Absolute dates win over relative ones when both are present | The owner's own text pairs "next week" with 19–21 Oct; a user who writes a stale date and "next week" keeps getting the stale window until they edit |
| Relative dates resolved at run time in the user's zone, parse cached on the criteria | A parse is kept until the text changes; a prompt version bump forces a re-parse for every user on the next run (one call each) |
| Default window 30 days when no date is given | Events sell out within a day (plan), yet 30 days of generic results dilute the queue for a user who meant "soon" |
| Judge returns flags; code caps the score from them | A judge that sets `date = no` for an event the filter kept means the extractor and judge disagree; the cap hides that disagreement rather than surfacing it |
| Scheduled runs use 2 rotating queries, manual runs 6 | A newly listed event may take up to three hours to be reached by its query; the plan's "within a day" still holds |
| Daily caps enforced from `SUM(runs.*)`, no new table | Two concurrent runs can both pass the check and overshoot the cap by one run's worth |
| `OpenAICompatibleModel` over `urllib`, no `openai` SDK | Streaming, retries and auth variants of real endpoints are hand-written; the Nous Portal's exact JSON-mode support is assumed, not verified |
| json_object fallback when json_schema is rejected | It is a degradation the user never sees; it is counted in a metric only |
| Fake model replays recordings keyed by prompt hash | Every prompt edit invalidates every recording; re-recording costs about 60 live calls and a review of changed scores |
| Fixture search provider rewritten as golden-set pages | The dev deployment's demo data changes; README screenshots and e2e expectations move with it (issue H) |
| Production refuses fixture and fake adapters | The current prod deploy, which has no keys set, would fail to start until the keys are added to Render |
| `SCORER`/`SCORER_MODEL` removed, not aliased | Render env vars already set with the old names break on deploy; the error message names the replacement |
| Recall target is 3 events for C1, measured by hand weekly | Berlin has jazz every night; 3 is a floor that proves the pipeline works, not that recall is good |
| Reason sentence capped at 140 characters, pattern fixed in the prompt | The pattern crowds out nuance (a workshop versus a concert) in languages with long words; the few-shot examples are English only |
