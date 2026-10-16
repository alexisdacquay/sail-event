# Sail-event

Find the events you would attend, decide when the answer is clear, ask when it is not, and put the accepted ones on your calendar.

## Problem

People who want to attend events, meetups or performances spend time every day scanning multiple sites and feeds to find what is coming up. Most events surface too late or not at all because no single source lists them, and checking frequently enough to catch short-notice events is tedious. Calendar-feed aggregators only collect events the user already knows about. Structured filters cannot express personal criteria in free-form language. The result is missed events, wasted search time, or settling for whatever appears first.

## What the system does

1. The user creates an account and signs in.
2. The user writes their criteria in free text: topics, places, dates, formats, anything that matters.
3. Every hour and on manual trigger, the app queries a web search provider with queries derived from the criteria and collects candidate events.
4. A model scores each new candidate against the user's criteria and records a score with a one-line reason.
5. Two user-set thresholds split scored events into auto-accept, auto-reject, and a queue of uncertain ones.
6. The user opens the app, reviews the queue, and accepts or rejects each uncertain event.
7. Accepted events appear in a per-user ICS calendar feed that any calendar application can subscribe to.

## Expected behaviour

- Each user has their own account, criteria, event list and calendar feed; nothing is shared between users.
- Criteria are free text, editable at any time, with no structured filters.
- Duplicate events found across searches are de-duplicated per user.
- A rejected event never reappears for that user.
- Events scored above the upper threshold are accepted without user action.
- Events scored below the lower threshold are rejected without user action.
- The user can change the accept and reject thresholds at any time.
- The ICS feed contains only accepted events; rejecting a previously accepted event removes it from the feed.
- The feed URL is per-user and acts as a secret: anyone who holds it can read that user's accepted events.
- There are no push notifications; the approval queue is the only place the user checks pending events.

## Status

Specification stage. No code yet. See `_docs/plan.md`.
