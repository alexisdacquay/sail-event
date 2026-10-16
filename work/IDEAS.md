# Candidate ideas for ProjectOne (2026-10-15)

Scoring lens: every idea can hit all 14 criteria. What differs is scope risk,
reviewer comprehension, and how natural the MCP tool / incident demo is.

## A. Lab resource booking  (RECOMMENDED)
- what: reserve shared lab gear (switches, benches, test rigs) for time windows;
  conflict detection; calendar view; who-has-what-now.
- entities: Resource, Reservation, User. relation: reservation -> resource.
- integration test: double-booking rejected end to end.
- MCP tool: `check_availability(resource, from, to)`, `list_reservations`.
- incident: conflict check endpoint 500s on overlapping edge case.
- real-time (optional): live calendar updates via WebSocket, mirrors M2.
- + reviewers understand it instantly; tiny domain; self-generated seed data.
- - generic; many peers may build "booking". differentiation only via workflow quality.

## B. Switch inventory & port planner  (domain flavour)
- what: catalogue of switch models (from your Arista/SONiC datasheet YAML), per-device
  port map, breakout planning, reservation of ports for a design.
- entities: Model, Device, Port, Allocation.
- MCP tool: `find_switch(ports>=N, speed)`, `port_map(device)`.
- incident: breakout validation endpoint fails on an unusual SKU.
- + you own the data and the domain; portfolio value for your field.
- - reviewers won't know SONiC/breakouts; spec and seed data take longer; risk of
    scope creep because the domain is rich.

## C. Architecture decision log (ADR board)
- what: teams record decisions (status, context, consequences, supersedes), browse,
  search, link to PRs.
- entities: Decision, Tag, Link.
- MCP tool: `search_decisions(q)` -> the agent pack reads ADRs as context (strong M5 story).
- incident: search endpoint degrades on a bad query.
- + the agent-extension story is the most coherent of the four.
- - "a form over a table"; weak frontend story; hard to make the demo feel alive.

## D. Peer-review queue
- what: submit a repo URL, get assigned N peers, score with a rubric, see aggregate.
- entities: Submission, Assignment, Review.
- MCP tool: `rubric(course)`, `pending_reviews(user)`.
- + meta-relevant to the course; clear workflow for integration tests.
- - it is the course platform; risks looking like a copy. GitHub API adds a credential.

## 2026-10-15 round 2 — user feedback
- B withdrawn: datacentre domain came from my inference, not from the user. too niche.
- A rewritten generic: shared-resource booking (rooms, desks, equipment).
- user asked for more variety, in the register of past homework (kanban, chores, API).

## E. Expense splitter (Splitwise-like)
- groups, shared bills, who-owes-whom, settle-up with minimal transfers.
- testable core: balance + settlement algorithm. MCP: `balances(group)`.
## F. Shared trip itinerary
- days, stops, notes; several people edit live (WebSocket, mirrors M2 collab).
- testable core: reorder/move stops, conflict on concurrent edit. MCP: `itinerary(trip)`.
## G. Flashcards with spaced repetition
- decks, cards, review sessions; SM-2 scheduling decides next review date.
- testable core: scheduling math, pure function. MCP: `due_cards(deck)`.
## H. Live polls / quiz room
- host creates questions, participants join by code, results update live.
- testable core: vote once per participant, tally. MCP: `results(poll)`.
## I. Meal planner -> shopping list
- recipes with ingredients, weekly plan, list aggregates quantities by unit.
- testable core: unit aggregation (2x200g + 1x0.5kg). MCP: `shopping_list(week)`.
## J. Habit tracker with streaks
- habits, daily check-ins, streak + heatmap.
- testable core: streak rules across timezones/missed days. MCP: `streaks(user)`.

## K. Personal event finder / scheduler (user's own idea, 2026-10-15)
- prior art: github.com/alexisdacquay/hermes-pa. read: README, tree. ~13.6k LOC python,
  CSV as the store, python review UI, nightly cron on a personal VPS, 6 paid search
  APIs + Luma + Meetup auth + Google Calendar, LLM judge against a personal taste.md,
  self-maintenance (scribe + fix agent). docs: prd, architecture, engineering, bugs.
- user: could start from scratch; wants to bring the idea to production-ready using the course.
- fit to rubric, if rebuilt from scratch and cut:
  + problem is real and reviewer-understandable (find events, score, review, hold)
  + natural entities: Source, Event, Decision, Profile. natural relation + workflow.
  + M4 story is native: nightly ingest job -> alert on failed run / 0 events -> responder.
    hermes already has scribe/fix-agent; the course adds the guardrails it lacks.
  + MCP tools obvious: `upcoming_events(city, days)`, `decide(event, accept|decline)`.
  + user has a PRD and decision history: spec phase (M1) starts warm.
  - reproducibility is the main risk: paid search APIs, auth feeds, LLM keys, personal
    calendar. mitigation: key-less mode (seeded fixtures, rule-based scorer), ICS export
    instead of Google Calendar write, 1-2 public sources only in v1.
  - shape mismatch: hermes is a pipeline, rubric wants frontend+backend+OpenAPI+DB.
    mitigation: web app first (FastAPI + Postgres + JS frontend), ingest = backend job.
  - scope creep: 13.6k LOC to be tempted to port. rule: port ideas, not code.
- v1 cut (proposal): sources = Luma public calendar + manual add + ICS import;
  scoring = rules, LLM optional behind a flag; review UI accept/decline; ICS export;
  nightly job in compose; everything else = non-goals in product-spec.md.

## K shape v2 — user proposal 2026-10-15: "standard searches, matching criteria, public calendar"
- standard searches (web search engines as the event source):
  + closest to hermes' real value (the open web, not one platform).
  - every search engine API needs a key; scraping result pages is ToS-hostile and bot-blocked.
  mitigation: ONE provider with a free tier (hermes used exa, brave, serper, tavily, firecrawl,
  linkup; free-tier limits NOT verified yet), README says "sign up for a free key" (allowed by
  logistics page), plus recorded fixtures so tests/CI/reviewers run with no key.
- matching criteria (rules: topics, city, date window, keywords; no LLM):
  + deterministic, unit-testable, reviewer-runnable, cheap.
  - hermes README, 2026-10-03: "The keyword prefilter and its Gleaner were deleted" because
    relevance became the LLM judge's call. the user already tried and rejected pure keywords.
  mitigation: criteria = hard filters (place, date, dedupe) + a transparent score; LLM rank
  optional behind a flag, never required.
- public calendar:
  reading: public Luma/Google calendars via ICS URL as a zero-key source. good.
  writing: the app SERVES a public ICS feed of accepted events; any calendar app subscribes.
  no Google Calendar API, no OAuth. good for reproducibility.
  - public = anyone with the URL sees the holds. acceptable for a demo; note it in security/.
- verdict: accept all three with the mitigations. open: which search provider (needs a
  free-tier check), and whether "public calendar" meant read, write, or both.

## Recommendation (round 3)
K, from scratch, with the v1 cut above. Beats A/E/G on motivation and on the M4/M5
story. Strongest fact against K: reproducibility for peer reviewers; without the
key-less mode it loses points on 10/14 and reviewers may fail to run it at all.

## Recommendation (round 2)
Any of A, E, F, G, H, I, J fits the rubric. Highest test/incident/MCP payoff per
unit of UI work: E (settlement math) and G (scheduling math).
Strongest fact against E and G: both are well-trodden clones; distinctiveness
must come from the workflow and docs, not the app.
