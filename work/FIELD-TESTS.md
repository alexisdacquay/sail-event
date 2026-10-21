# Field tests — ledger and run log

Procedure: `.claude/skills/field-test/SKILL.md`. Tool and invariants: `backend/tests/field/`.
One block per run. Findings are grouped by invariant; one issue per (invariant, layer) cluster.

## 2026-10-21 tier 0 sweep — prod db (sail-event-db), main 7962670

58 users · 58 criteria · 371 runs · 2175 events (383 accepted · 343 queued · 1378 rejected · 71 new) · decided_by: auto 1723, user 29, null 423

| inv | result | layer | severity |
|---|---|---|---|
| I1 | accepted: 4 past when stored (1 auto, 3 user-decided from a series/range card), 48 past now; queued: 13 past when stored, all auto, 20 past now; 0 unparsed. 31 accepted are date-only and dated the day they were stored (underway-today, Priya's case). | pipeline (date-only past filter; series first-date; feed never expires #78) | high |
| I2 | place named, other country kept: priya_us1r90 "jazz Berlin" US:39 (35 accepted at ≥90, 4 queued) — all from the earlier place-less "jazz" criteria, so really I8. reviewer_oct18 / reviewer_test "near Paris" ZZ:8 (country unknown) kept. Place-less criteria: "jazz" US:73, "events" US:43, "something fun this weekend" US:34, "online webinar" US:21 + 6 countries. | judge + pipeline (no place ⇒ anything accepted at 95) | high |
| I3 | 67 hedged auto-accepts across 8 users; top reasons all "no place or date limits were given" at 92-95, US cities | judge prompt | high |
| I4 | 330 runs with counts: 0 internal mismatches; 81 runs where the report's judged ≠ events in the table for that run (dedup / already-known rows not attributed, or re-scored events moved run) | pipeline / api | medium |
| I5 | not checkable by SQL; battery | — | — |
| I6 | accepted: 10 root links, 14 listing links, 171 link = source page, 115 no time (30%); queued: 5 / 20 / 195 / 83 | extract | medium |
| I7 | 2 duplicate groups, 2 extra events | pipeline | low |
| I8 | see I2: after a criteria change, 35 accepted events from the old criteria stay accepted at 90+ | pipeline | high |
| I9 | fails by construction: a rejected event cannot be decided again (`decide_event` allows queued/accepted only); no undo (#95) | api | high |
| I10 | run errors stored raw: "TimeoutError: The read operation timed out" ×2, "RuntimeError: Tavily API error…" ×1, "'LLM_JSON_MODE'" ×2 (KeyError text), "no criteria text" ×20 (fine) | api / copy | medium |
| I11 | battery | — | — |
| I12 | battery | — | — |

Issues to file (one per cluster, after the battery confirms them live): I1 pipeline · I2/I3/I8 judge+pipeline (place-less and criteria-change) · I6 extract · I9 api · I10 copy. Existing: #78 (I1 feed expiry), #94/#95/#96 cover parts of I8, I9, I10.

## 2026-10-21 09:08 tier 1 battery — https://sail-event.onrender.com — 17 personas — main 7962670 (first run on this host: 5 registered, 12 at the registration cap)

| persona | status | flow | s | findings |
|---|---|---|---|---|
| valencia_regatta_es | register 429 {'detail': 'Too many registrations. Try again later.'} |  | 0 | - |
| valencia_ceramics_es | register 429 {'detail': 'Too many registrations. Try again later.'} |  | 0 | - |
| tokyo_jazz_ja | register 429 {'detail': 'Too many registrations. Try again later.'} |  | 0 | - |
| paris_kids_fr | register 429 {'detail': 'Too many registrations. Try again later.'} |  | 0 | - |
| munich_markets_de | register 429 {'detail': 'Too many registrations. Try again later.'} |  | 0 | - |
| med_regattas_region_en | register 429 {'detail': 'Too many registrations. Try again later.'} |  | 0 | - |
| vienna_contradictory_en | register 429 {'detail': 'Too many registrations. Try again later.'} |  | 0 | - |
| manchester_exclusion_en | register 429 {'detail': 'Too many registrations. Try again later.'} |  | 0 | - |
| porto_weekend_pt | register 429 {'detail': 'Too many registrations. Try again later.'} |  | 0 | - |
| nonevent_bike | register 429 {'detail': 'Too many registrations. Try again later.'} |  | 0 | - |
| injection | register 429 {'detail': 'Too many registrations. Try again later.'} |  | 0 | - |
| past_window_en | register 429 {'detail': 'Too many registrations. Try again later.'} |  | 0 | - |
| lisbon_sat_en | ok | 20 res → 30 ext → 8 judged → 2 acc / 0 queued / 6 rej · kept 2 | 81 | - |
| sevilla_kids_es | ok | 20 res → 24 ext → 12 judged → 0 acc / 2 queued / 10 rej · kept 2 | 63 | I9:1 |
| jazz_then_berlin | ok | 20 res → 20 ext → 10 judged → 9 acc / 1 queued / 0 rej · kept 10 | 151 | I3:14 I8:9 I9:1 |
| running_oneword | ok | 20 res → 30 ext → 13 judged → 12 acc / 1 queued / 0 rej · kept 13 | 55 | I3:10 I6:6 I9:1 |
| berlin_jazz_dates_en | ok | 16 res → 20 ext → 12 judged → 8 acc / 1 queued / 3 rej · kept 9 | 47 | I9:1 |

### Findings by invariant

- **I3** ×24 (jazz_then_berlin, running_oneword)
  - jazz_then_berlin: accepted 90 «Steve Davis» 2026-11-05T19:00 Westport,US — Steve Davis is a jazz performance, matching your jazz search; no place or dates were specified, so t
  - jazz_then_berlin: accepted 92 «Kay Kostopoulos And Black Olive Jazz» 2026-10-22T20:00 New York,US — A New York jazz gig by Kay Kostopoulos and Black Olive Jazz matches your jazz search, with no place 
  - jazz_then_berlin: accepted 92 «Mike Freeman» 2026-11-12T19:00 New York,US — Mike Freeman is a jazz gig at DiMenna Center, New York on Nov 12 — a clear match for your jazz searc
  - jazz_then_berlin: accepted 90 «Nikolaj Hess With Marc Mommaas, Tony Sch» 2026-10-21T19:00 New York,US — A jazz show in New York tonight fits your search for jazz; no city or dates were specified.
- **I6** ×6 (running_oneword)
  - running_oneword: accepted 95 «Be An Angel Race for Space» 2026-10-24 Houston,US link https://houstonrunning.co
  - running_oneword: queued 50 «MORE THAN PINK Walk - Austin» 2026-10-25 Austin,US link https://houstonrunning.co
  - running_oneword: accepted 92 «Monster Mash Run» 2026-10-31 Houston,US link https://houstonrunning.co
  - running_oneword: accepted 92 «GiGi's Playhouse 5K» 2026-11-14 Houston,US link https://houstonrunning.co
- **I8** ×9 (jazz_then_berlin)
  - jazz_then_berlin: stale accepted 90 «Nikolaj Hess With Marc Mommaas, Tony Sch»
  - jazz_then_berlin: stale accepted 92 «David Ostwald's Louis Armstrong Eternity»
  - jazz_then_berlin: stale accepted 92 «The Cookers»
  - jazz_then_berlin: stale accepted 92 «Mike Freeman»
- **I9** ×4 (berlin_jazz_dates_en, jazz_then_berlin, running_oneword, sevilla_kids_es)
  - sevilla_kids_es: a rejected event cannot be taken back: 400 Only queued and accepted events can be decided
  - jazz_then_berlin: a rejected event cannot be taken back: 400 Only queued and accepted events can be decided
  - running_oneword: a rejected event cannot be taken back: 400 Only queued and accepted events can be decided
  - berlin_jazz_dates_en: a rejected event cannot be taken back: 400 Only queued and accepted events can be decided

issues: #99 (I3 · judge), #100 (I6 · extract); already open: #94 (I8 stale reasons, I1 past dates, legend), #95 (I9 undo, webcal), #96 (I10 raw errors, tabs in URL), #78 (I1 feed expiry)
