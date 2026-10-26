# Regression test store

One test per fixed bug: input + expected outcome + issue number, written red before the fix.
Run as phase 2 of the unified runner.
Seeded from every CLOSED GitHub issue labelled "bug" plus findings in
`work/USER-TESTS-2026-10-21.md` and `work/FIELD-TESTS.md`.

## Reproduced with fixtures

| Bug | File | What the test checks |
|-----|------|---------------------|
| #124 | test_london_ai_hub.py | Listing page whose snippet yields no events but raw_content does |
| #125 | test_135_judge_repair.py | Extra fields dropped (not rejected); missing is_event triggers repair |
| #112 | test_135_no_date_counter.py | Event without start_local is incomplete; never counted as a page |
| listing links (2026-10-25) | test_listing_own_links.py | A listing event takes its own URL from the listing HTML (another host too) and its page is opened |

## Cannot reproduce yet

| Bug | Reason |
|-----|--------|
| #120 | Frontend-only: search box required two clicks because of the lock-step save. No backend logic to test. |
| #116 | Frontend-only: funnel SVG geometry was drawn as three separate pieces. No backend logic to test. |
| I9 (field test, #95) | API rejects re-deciding a rejected event. Bug is an open design issue, not yet fixed; a regression test would test the current (broken) behaviour. |
| I3 (field test, #99) | Hedged auto-accept reasons. Requires LLM interaction; cannot reproduce with recorded fixtures. |
| I8 (field test, #94) | Stale reasons after criteria change. Requires two sequential live searches; cannot reproduce offline. |
| I6 (field test, #100) | Listing links as event links. Requires LLM extraction; no fixture captures this pattern yet. |
| Valencia CA (user test D) | Wrong-country events auto-accepted. Requires LLM judge; no fixture captures the Valencia ambiguity. |
| Past dates in calendar (user tests C, D) | Requires full pipeline with date filter edge cases. Partially covered by invariant I1 in phase 1. |
| Raw error messages (user test D, I10) | API returns raw exception text. Open issue #96; partially covered by invariant I10 in phase 1. |
