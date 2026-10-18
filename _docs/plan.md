# Sail-event — MVP scope

## Product goal

Find the events a person would want to attend, decide for them when the answer is
clear, ask them when it is not, and put the accepted events on their calendar.

## Users

Several people use one deployment. Each user has their own account, their own
criteria, their own event list and their own calendar feed. Nothing is shared
between users.

## Core workflow

### 1. Describe what you want

A user writes their criteria in their own words: topics, places, dates, formats,
anything that matters to them. One free-text profile per user, editable at any time.

### 2. Search

Every hour, and whenever the user presses "Search now", the app queries one web
search provider with queries derived from the criteria, collects candidate events
(title, date and time, place, link, description) and de-duplicates them against
what it already knows for that user.

### 3. Score

A model reads each new candidate against the user's criteria and returns a score
with a one-line reason. The score, the reason and the model used are stored on
the event.

### 4. Triage

Two thresholds split the scored events:

- above the upper threshold: accepted automatically
- below the lower threshold: rejected automatically
- in between: queued for the user

Rejected events never return. The user can change the thresholds.

### 5. Approve

The user opens the app and sees the queue. For each queued event they choose
accept or reject. There is no notification; the queue is where they look.

### 6. Calendar

The app publishes one calendar feed (ICS) per user. Accepted events appear in it;
the user subscribes to the feed from their calendar application. Rejecting an
accepted event removes it from the feed.

## Features the MVP settles on

1. Per-user criteria profile in free text
2. Hourly and on-demand search, model scoring, three-way triage
3. Approval queue
4. Per-user ICS calendar feed

## Decisions made for the MVP

### Multi-user from the start

**Decision:** accounts with username and password; every record belongs to a user.

**Why:** the app is deployed publicly and others must be able to try it as
themselves.

**Alternatives considered:** single profile (simpler, but nobody else can use the
deployment); shared group feed (not the product).

### Web search is the only source

**Decision:** events come from a web search provider, nothing else.

**Why:** the point is to find events the user does not already know about.

**Alternatives considered:** pasted calendar feeds (events the user already found);
manual add (same).

### A model applies the criteria

**Decision:** criteria are free text; a model scores each event against them.

**Why:** structured filters were tried in the previous version and dropped; the
judgement is the product.

**Alternatives considered:** code-only filters (cheap, testable, too blunt);
filters first then model (two mechanisms to maintain).

**Cost accepted:** every run makes model calls; tests and reviewers need a model
key or a recorded stub.

### Three-way triage with user-set thresholds

**Decision:** auto-accept, auto-reject, ask in between.

**Why:** the user should only be asked about the events the model is unsure of.

**Alternative considered:** the user decides every event (too much work; the
previous version showed that).

### Calendar by published feed

**Decision:** the app serves an ICS feed per user; no calendar-provider login.

**Why:** no third-party credentials, works with any calendar application, one
endpoint in the API contract.

**Alternatives considered:** writing into Google Calendar (needs a Google cloud
project and per-user sign-in); app-only list (no scheduler).

**Cost accepted:** a feed is pulled on the calendar application's schedule; a hold
can appear hours late. The feed URL is a secret: anyone holding it sees the holds.

### Hourly schedule plus a button

**Decision:** a scheduled run every hour and a manual "Search now".

**Why:** events appear and sell out within a day.

**Cost accepted:** search quota and model calls scale with runs; each run is capped.

## Out of scope for the MVP

- travel schedule (where the user will be on a date)
- following links from search results to discover more events
- more than one search provider
- sharing or seeing other users' events
- writing into Google Calendar; push refresh of the calendar
- email or other notifications
- editing a score by hand

## Later, after the MVP

- self-maintenance: an on-call responder that investigates a failed or empty run
  and proposes a fix for approval (course lesson 4), and the agent extension pack
  around the project (course lesson 5)
- status 2026-10-17: both delivered. Responder: issues #25, #26, directory
  `incident-response/`. Extension pack: issue #28, reduced to the QA subagent and
  the pre-commit hook.
