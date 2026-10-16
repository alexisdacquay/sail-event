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

## Recommendation (round 2)
Any of A, E, F, G, H, I, J fits the rubric. Highest test/incident/MCP payoff per
unit of UI work: E (settlement math) and G (scheduling math).
Strongest fact against E and G: both are well-trodden clones; distinctiveness
must come from the workflow and docs, not the app.
