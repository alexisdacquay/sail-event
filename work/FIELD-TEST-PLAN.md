# Field-test plan (proposal, 2026-10-21, not built)

Why the last round was slow and still missed things: one orchestrator, one browser, one persona at a time,
on prod, behind an hourly 429 and 1-2 min searches; and the judge was the session that wrote the code.
Five personas took a day and found ~40 symptoms that STATE.md already folds into 3 root causes.
A test system has to (1) run many users at once without a browser, (2) check invariants with code, not
an LLM saying "looks fine", (3) group symptoms by the invariant they break so one issue = one root cause.

## 1. Skill: `/field-test` (`.claude/skills/field-test/`)

Files: `SKILL.md` (the procedure), `matrix.yaml` (persona axes), `invariants.md` (the oracle list),
`work/FIELD-TESTS.md` (coverage ledger + run log). Name: "field test" = the product meets real users in the
field, not the rubric. Alternatives: `/user-battery`, `/stress-users`.

### Persona matrix (axes, not a list)
Each run samples cells; the ledger records which cells are covered, which found defects.
- language of criteria: en / es / pt / de / ja / emoji / mixed
- place: named city / region ("cerca de Valencia") / none / wrong-looking ("Valencia" ambiguous) / URL
- time: explicit day / "this weekend" / month / none / past / far future
- specificity: one word / sentence / paragraph / contradictory ("free, under 50 EUR") / exclusion ("no courses")
- intent: concert, regatta, kids+accessibility, meetup, non-event ("buy a bike"), injection
- behaviour path: single search / change criteria then re-search / change thresholds / accept-reject-undo /
  reload mid-search / tab switch / second account / phone viewport
- device: API only / desktop browser / 375 px
Every persona also carries a ground-truth want: 2-5 real events that exist for that cell (see §4).

### Invariants (the oracle; code checks these, LLM never grades them)
Data (checked via /api/events, /api/calendar feed, run report):
- I1 no event with start < now, or unparsed date, in queue/accepted/feed
- I2 every event's country ∈ the countries the criteria name (when a place is named)
- I3 no auto-accept when the reason contains a hedge ("not confirmed", "rather than", "no place given")
- I4 counters sum: results = events + skipped; judged ≤ events; queued+accepted+rejected = judged
- I5 reason language = criteria language (langdetect)
- I6 every card has a real event URL (not homepage / search page / listicle) and a time or "time unknown"
- I7 same (title, date) never twice in one user's events
- I8 criteria change: old accepted events either re-scored or explicitly kept; never silently stale
- I9 decisions reversible: reject→undo→queued; remove from calendar ≠ rejected
- I10 run never ends in a raw exception string; every stop has a plain-words reason; 429 surfaces a message
- I11 no cross-user leakage (events, feed tokens)
- I12 exclusions in words ("no courses") are honoured
UI (Playwright, only these):
- U1 reload / tab switch keeps page + search status (tabs in URL)
- U2 result line text matches the card counts on screen
- U3 slider boxes = slider knobs; legend not clipped at 375 px
- U4 Copy shows feedback; feed link is webcal + steps

### Root-cause grouping (the anti-symptom rule)
A finding is logged as `invariant | persona cell | evidence | layer`, layer ∈ {search recall, extraction,
judge prompt, pipeline state, API, UI state, copy}. One issue per (invariant, layer) cluster, titled by the
invariant, listing its symptoms. No issue for a bare symptom. An engineer fixing one must name the invariant
and add it to tier 0/1 so it cannot regress. Fixes that pass the cell but not the invariant are rejected by QA.

## 2. Tiers (speed by construction)

| tier | what | runner | time | cost | when |
|---|---|---|---|---|---|
| 0 | invariant sweep over existing prod/dev data (35 accounts already there) | one script, SQL/API | 30 s | 0 | every run, CI nightly |
| 1 | persona battery via API: register→criteria→search→decisions→threshold change→re-search→feed; invariants after each step | `backend/scripts/field_battery.py` (extends remote_batch.py), 10-20 personas in parallel, ThreadPool | 3-5 min live, 20 s replayed | 20 searches live | every PR touching pipeline/judge/prompts (replay), daily (live) |
| 2 | naive-user agents: LLM persona with a goal, drives the API (and Playwright for the 4 UI invariants), writes a transcript + "would I come back" + the one thing that broke the goal; separate judge groups into invariants and proposes ONE new axis | 5-8 subagents in parallel, background, Sonnet for personas, Opus for the judge | 20-40 min wall | ~40 searches | weekly, and after a release |
| 3 | recall ground truth: for 10 (city, window, topic) triples, 3-5 events verified to exist on venue sites; recall@20 per triple | agent compiles the set once (reviewed by owner), script measures | 10 min | 10 searches | weekly; tracks the real product gap |
| 4 | Playwright journeys U1-U4 | existing e2e suite + 4 tests | 1 min | 0 | every PR |

Parallelism needs: run against dev (not prod) or local compose with real keys, `SEARCH_RATE_LIMIT` raised
for the test host, daily budget env set for the run. Tier 1 records every LLM/search response
(RecordingModel exists in smoke_search.py) so re-runs replay in seconds; re-record weekly or on prompt change.
Subagents have no browser: all persona work goes through the API; Playwright covers UI invariants headless.

## 3. Bias controls
- Personas and judge never see the issue tracker, STATE.md or the engineer's claims; they get the public URL,
  the matrix cell, the ground-truth want, and invariants.md.
- Verdict is computed: invariants violated (count, which), goal met (ground-truth events found y/n),
  come-back (persona's own answer). No "pass" wording in prompts; the judge's deliverable is a ranked
  cause list with a layer each, max 5, plus "what I could not test".
- Two judges on the same transcripts; disagreement is logged, not averaged.
- Coverage ledger: a cell untested for 2 runs gets priority; the judge's proposed new axis enters the
  matrix next run. This is the answer to "the dozens of things I did not ask about".

## 4. Build order (one day, in this sequence)
1. `invariants.md` + tier 0 script against prod data now (reuses what the 35 accounts already produced;
   gives numbers today: how many past dates, wrong countries, hedged auto-accepts are in feeds).
2. `field_battery.py` from remote_batch.py: persona flow + invariant checks + replay. CI job on PR for
   replay mode.
3. `/field-test` SKILL.md: matrix, tier 2 briefs, judge brief, grouping rule, ledger format.
4. Ground-truth set for 10 triples (owner reviews it once).
5. Playwright U1-U4.
6. First full run; file issues by invariant; re-run tier 0/1 after each fix.

## 5. What this does not solve
Recall is a product gap, not a test gap: tier 3 will measure it every week and it will stay low until the
query planning changes (one verbatim query + "event" → listicles). Testing shows the number; the fix is
design work. Tier 2 live runs cost real credits; tier 1 replay does not.
