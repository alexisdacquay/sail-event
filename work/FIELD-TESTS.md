# Field tests — ledger and run log

Superseded by `work/RUN-LOG.md` (unified runner, issue #135).
Procedure: `backend/tests/field/runner.py`. Invariants: `backend/tests/field/invariants.py`.

## Before 2026-10-25

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

## 2026-10-21 09:43 tier 1 battery — https://sail-event.onrender.com — 17 personas — main e59b9d0 (3 at the registration cap; 14 ran; 6 min wall)

| persona | status | flow | s | findings |
|---|---|---|---|---|
| valencia_ceramics_es | register 429 {'detail': 'Too many registrations. Try again later.'} |  | 0 | - |
| munich_markets_de | register 429 {'detail': 'Too many registrations. Try again later.'} |  | 0 | - |
| vienna_contradictory_en | register 429 {'detail': 'Too many registrations. Try again later.'} |  | 0 | - |
| lisbon_sat_en | ok | 20 res → 29 ext → 2 judged → 0 acc / 0 queued / 2 rej · kept 3 · recall 1/3 | 58 | - |
| valencia_regatta_es | ok | 20 res → 7 ext → 3 judged → 2 acc / 0 queued / 1 rej · kept 2 · recall 0/2 | 44 | I5:1 |
| sevilla_kids_es | ok | 20 res → 21 ext → 1 judged → 0 acc / 0 queued / 1 rej · kept 2 · recall 2/2 | 36 | I9:1 |
| jazz_then_berlin | ok | 20 res → 30 ext → 13 judged → 4 acc / 6 queued / 3 rej · kept 46 | 137 | I3:22 I6:4 I8:45 I9:1 |
| running_oneword | ok | 20 res → 30 ext → 15 judged → 11 acc / 4 queued / 0 rej · kept 28 | 49 | I3:18 I6:6 I9:1 |
| berlin_jazz_dates_en | ok | 20 res → 27 ext → 7 judged → 2 acc / 1 queued / 4 rej · kept 11 · recall 0/3 | 61 | I9:1 |
| tokyo_jazz_ja | ok | 18 res → 20 ext → 13 judged → 8 acc / 3 queued / 2 rej · kept 11 · recall 2/2 | 56 | I3:1 I5:10 I6:2 I9:1 |
| paris_kids_fr | ok | 20 res → 30 ext → 17 judged → 1 acc / 6 queued / 10 rej · kept 7 · recall 0/3 | 103 | I5:1 I9:1 |
| med_regattas_region_en | ok | 20 res → 13 ext → 7 judged → 2 acc / 0 queued / 5 rej · kept 2 | 54 | - |
| manchester_exclusion_en | ok | 20 res → 25 ext → 15 judged → 0 acc / 1 queued / 14 rej · kept 1 · recall 0/3 | 90 | I9:1 |
| porto_weekend_pt | ok | 20 res → 40 ext → 13 judged → 9 acc / 0 queued / 4 rej · kept 9 · recall 2/3 | 89 | I5:7 |
| nonevent_bike | ok | 20 res → 30 ext → 15 judged → 0 acc / 0 queued / 15 rej · kept 0 | 56 | - |
| injection | criteria 400 |  | 0 | - |
| past_window_en | ok | 20 res → 20 ext → 11 judged → 0 acc / 0 queued / 11 rej · kept 0 | 53 | - |

### Findings by invariant

- **I3** ×41 (jazz_then_berlin, running_oneword, tokyo_jazz_ja)
  - jazz_then_berlin: accepted 92 «Fbjr Ronja Rose Andresson» 2026-10-24 Berlin,DE — Live jazz concert in Berlin on 2026-10-24 matches your jazz Berlin search, though the date is three 
  - jazz_then_berlin: accepted 90 «Gretchen - BEAT MUSIC» 2026-10-31 Berlin,DE — Live jazz concert in Berlin on 2026-10-31 matches your search for jazz in Berlin; no dates were spec
  - jazz_then_berlin: accepted 94 «THE ZIG ZAG JAZZED UP JAM SESSION» 2026-10-27 Berlin,DE — A live jazz jam session in Berlin matching your jazz-in-Berlin search, with no dates specified by yo
  - jazz_then_berlin: accepted 95 «jazzexzess w/ O/H/R + HOW NOISY ARE THE » 2026-11-13T20:00 Berlin,DE — A jazz concert in Berlin with no dates requested, so it matches your search on both topic and place.
- **I5** ×19 (paris_kids_fr, porto_weekend_pt, tokyo_jazz_ja, valencia_regatta_es)
  - valencia_regatta_es: reason in en, criteria in es: Sailing regatta in Valencia on 9 November 2026 — matches your sport, place and m
  - tokyo_jazz_ja: reason in en, criteria in ja: A Tokyo jazz concert on November 29, 2026 matches your search for Tokyo jazz in 
  - tokyo_jazz_ja: reason in en, criteria in ja: A jazz festival in Tokyo on Nov 15, 2026 matches your city, month and genre, tho
  - tokyo_jazz_ja: reason in en, criteria in ja: Tokyo jazz-fusion event on 2026-11-01 matches your search for Tokyo jazz in Nove
- **I6** ×12 (jazz_then_berlin, running_oneword, tokyo_jazz_ja)
  - jazz_then_berlin: accepted 92 «A Night of Stars with Gregory Porter» 2026-11-16 Washington,US link https://www.dcjazzfest.org
  - jazz_then_berlin: queued 72 «Songs of the Silver Screen with Three Sw» 2026-10-22 San Antonio,US link https://tickets.jazztx.com
  - jazz_then_berlin: accepted 92 «A Night of Stars with Gregory Porter» 2026-11-16 Washington,US link https://www.dcjazzfest.org
  - jazz_then_berlin: queued 72 «Songs of the Silver Screen with Three Sw» 2026-10-22 San Antonio,US link https://tickets.jazztx.com
- **I8** ×45 (jazz_then_berlin)
  - jazz_then_berlin: stale accepted 95 «13 Kuukautta»
  - jazz_then_berlin: stale accepted 95 «Okusteinhuffmills»
  - jazz_then_berlin: stale accepted 93 «ZIG ZAG HALL: Kurt Elling & The Yellowja»
  - jazz_then_berlin: stale accepted 95 «Avishai Cohen Trio»
- **I9** ×7 (berlin_jazz_dates_en, jazz_then_berlin, manchester_exclusion_en, paris_kids_fr, running_oneword, sevilla_kids_es, tokyo_jazz_ja)
  - sevilla_kids_es: a rejected event cannot be taken back: 400 Only queued and accepted events can be decided
  - jazz_then_berlin: a rejected event cannot be taken back: 400 Only queued and accepted events can be decided
  - running_oneword: a rejected event cannot be taken back: 400 Only queued and accepted events can be decided
  - berlin_jazz_dates_en: a rejected event cannot be taken back: 400 Only queued and accepted events can be decided

recall: 7/21 real venue events found (lisbon 1/3, valencia 0/2, sevilla 2/2, berlin 0/3, tokyo 2/2, paris 0/3, manchester 0/3, porto 2/3).
holds on fresh runs: I1 past dates 0, I4 counters 0, I10 raw errors 0, I11 leakage 0; non-event, past window and injection keep nothing.
caveat: I3 on jazz_then_berlin counts "no dates were specified" for Berlin events that are right; the real I3 cases are running_oneword (US races for a Berlin user).
priorities (owner vets; nothing filed from this run):
1. HIGH  one-word criteria fill the calendar with events anywhere (11 US races auto-accepted for a Berlin user; prod 67) · I3 · judge · S · #99
2. HIGH  criteria change leaves the old accepted events in the calendar (45 stale) · I8 · pipeline · M · part of #94
3. HIGH  recall 33%: the real events in the window are not found (Berlin, Paris, Manchester 0/3) · recall · L · no issue
4. MED   reasons in English for Japanese and Portuguese criteria (19) · I5 · judge · S · part of #94
5. MED   a rejected event cannot be taken back (7/7) · I9 · api · S · #95
6. LOW   event link is the site root or a ticket shop (12) · I6 · extract · M · #100
