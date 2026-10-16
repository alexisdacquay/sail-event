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

## Recommendation
A. Smallest surface that still exercises every criterion, zero reviewer friction,
natural conflict logic for tests and incidents.
Strongest fact against A: it is the least distinctive idea; the grade will ride on
documentation and workflow quality, not the app.
If you want domain flavour with low extra cost: A with resources = switches from
your datasheet data (B-lite), kept to Resource + Reservation only.
