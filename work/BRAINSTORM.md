# Brainstorm log — lesson 1 step 1 (started 2026-10-15)

Idea as given: a personal event finder / scheduler / planner. Prior art: hermes-pa.
Seeds kept from earlier discussion (not decided): sources = web search + public ICS +
manual; relevance = criteria filters + score, LLM optional; output = public ICS feed;
multi-user profiles; nightly job with alert + bounded responder; non-goals list.

Format: Q / options / user's answer verbatim / decision.

## Q1 — who is the tool for?
options:
  a) you only, one profile (hermes as it is)
  b) several people, each with their own profile and private shortlist
  c) a group sharing one feed (a community calendar)
answer: "b)" (2026-10-15)
decision: multi-user; each user has own profile and private shortlist. my cap
(username + password, no sharing, no teams in v1) is a proposal, not yet decided.

## Q2 — where do events come from in v1?
options:
  a) public calendar feeds only (ICS URLs the user pastes: Luma calendars, Meetup groups)
  b) web search only (one provider, queries built from the user's criteria)
  c) both, plus manual add (the seed from earlier)
answer: "no fuckign manual add, adding what? event people don't know about? Or things I
already know therefore don't need to search? Fucking hell. Search." (2026-10-15)
decision: b) web search is the source. manual add is out. (feeds: not chosen; ask if
they come back as a search target later, not as a source.)

## Q3 — how does the tool decide an event matches you?
options:
  a) structured criteria: topics, city/radius, date window, online vs in person
  b) written profile in own words, scored by a model (hermes taste.md)
  c) a) as hard filters, then b) as optional ranking on what passes
user: "isn't a and b the same thing? they are criteria." -> reframed: who applies them?
  a) code only  b) a model only  c) code on hard fields, model ranks the rest
answer: "b)" (2026-10-15)
decision: criteria are free text; a model reads each event against them and scores.
carry to spec: tests and reviewers need a model key or a recorded stub.

## Q4 — what do you do with the matches?
options:
  a) read a ranked list, nothing to click
  b) accept or decline each one; declined never come back
  c) b) plus a "maybe" state to revisit
user: "what?" -> rephrased: straight to calendar / you pick yes-no first / plus a later pile
answer: "score then events based on the criteria. then auto-accept best ones, auto reject
very bad ones, ask approval for borderline ones." (2026-10-15)
decision: model scores each event; two thresholds: above = auto-accept, below =
auto-reject, between = queued for the user's approval.

## Q5 — where do accepted events end up?
options:
  a) a calendar feed the app publishes (ICS URL), user subscribes from Google/Apple Calendar
  b) written directly into Google Calendar (needs Google sign-in)
  c) only in the app
user asked which scores best -> a) (contract endpoint, integration-testable, no secrets).
answer: "a) we will trigger-push refreshes, or something like that." (2026-10-15)
decision: app publishes an ICS feed per user; calendar apps subscribe.
parked: ICS is pull-only; "push" needs CalDAV or Google API -> v2 note in the spec.

## Q6 — when does the search run?
options:
  a) on a schedule, every night, no action from the user
  b) only on "search now"
  c) both
answer: "c) every hour and by a \"search now\" buton." (2026-10-15)
decision: scheduled hourly run + manual "search now". carry: per-run cap on search
queries and model calls (quota, cost).

## Q7 — how do you learn that borderline events wait for approval?
options:
  a) open the app, see the queue
  b) email/message per run when queue non-empty
  c) daily digest
answer: "a)" (2026-10-15)
decision: approval queue in the app; no notifications in v1.

## Q8 — out of v1 (proposed non-goals; user says which must be in)
- travel schedule; link-following crawl; >1 search provider; self-maintenance/scribe/
  fix agent; sharing between users; Google Calendar write / push refresh;
  notifications; hand-editing the score
answer: "\"self-maintenance, scribe, fix agent\" is part of section(lesson) 4 or 5 I think.
To be included (longer-ter). others are ever longer tern, as optional" (2026-10-15)
decision: self-maintenance = the lesson-4 on-call responder + lesson-5 agent pack;
in scope, later phase, not the v1 app core. all other items: out of v1, optional later.

## Q9 — name
options: a) Hermes  b) Scout  c) Eventail  d) user's own
answer: "Sail-event" (2026-10-15)
decision: name = Sail-event.

## Closed 2026-10-15 -> _docs/plan.md v1 written from Q1-Q9. awaiting user review.
