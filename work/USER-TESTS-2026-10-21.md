# Naive user tests on prod (2026-10-21, prod 571b751) — no rubric, real pages, browser

## A — Dana, Lisbon, free Saturday 24 Oct, live music / food market / outdoors (scripted persona)
- Search 1 (long sentence): 20 results → 18 events → 6 judged, all rejected; none on Saturday 24. Review tab empty. Calendar empty.
- Search 2 ("jazz or fado in Lisbon this weekend, evening"): 34 events → 12 judged → all rejected; three real fado nights found but on Wed/Thu/7 Nov; a Saturday outdoor boat party with DJ appeared here but not in search 1.
- Verdict: would not come back. "27 cards, zero things I could do this Saturday, never asked to decide anything."
- Bugs: result counter inconsistent (18 events → 0 passed → 6 judged; 18+19 ≠ 20); slider legend clipped ("ı your cale"); stale reasons from the previous criteria stay on All events; "right city and weekend" for a Friday; listicle pages as sources (piedalies.lv, concerts50.com).
- Confusions: sign-in page says nothing about what the app does; "Times shown in UTC until you save your criteria"; "queued" wording; no accept/override on All events; Berlin time shown next to Lisbon time; "searches every hour" with no idea what will happen.
- Asks: actually find Saturday-in-Lisbon events (fado houses, jazz clubs, markets exist weekly); "I'd go anyway" on rejected cards and a near-miss section ("Wednesday fado — want it anyway?"); plain-words result line ("Looked at 20 pages, found 6 events, none on Sat 24 Oct").

## B — Tomás, Valencia, regatas en noviembre, writes Spanish (scripted persona)
- 3 searches, 33 min: found two real regattas, both at his own club (RCN Valencia); nothing from Alicante, Dénia, Castellón, Murcia, Balearics although he wrote "cerca de Valencia".
- Verdict: would not come back. Whole UI in English; reasons alternate Spanish/English; the placeholder says "jazz or folk concerts near Paris".
- Bugs: Search button vanishes while searching; reload mid-search loses the status and the result line (pressed again); result line contradicts cards (5 passed → 6 judged; "0 judged" next to "Review 3 events"); series event dated at its first date 3 Oct (past) and exported so to the .ics; proaclara.com events all at 15:31 (scrape artefact); past events shown (March/May 2026); the same windsurf festival twice with 30% and 62%; a course scored 74% and sent to review although he excluded courses in words.
- Wrong results: Germany, Croatia, Paris, Dubai, France, basketball, MotoGP, marathons, fishing.
- Asks: answer in the user's language everywhere; search the regional regatta calendars, "near Valencia" = the region; show progress and keep it after reload; result line must match the cards; a series shows its dates in the asked month.

## E — Carmen, Sevilla, mother of two (one in a wheelchair), cheap weekend plans for kids, Spanish (unscripted)
- It found real Sevilla kids' events (CaixaForum family cinema, Auditorio Cartuja theatre, a monsters route) and explained each score; she would keep the account "and check it on Fridays" but not recommend it yet.
- Blockers: decisions are one-way (reject / remove cannot be undone; "Remove from calendar" turns an accept into a rejection); no time or price on cards; an event whose own reason says "step-free access not confirmed" was auto-accepted at 72%; 97 s blind wait; funnel line for developers; login page with no pitch; thresholds changed are not re-applied to existing cards; slider knobs show 69/81 while the boxes say 80/70 and labels overlap; dates: exhibitions dated "today", a date range turned every other weekend into 4-5% rejections; reasons 3 Spanish + 1 English; Berlin time next to Madrid; feed is a bare https URL (no webcal/subscribe steps), Copy gives no feedback; no forgot-password.
- Top five: undo / put back to review; time + price on every card and no auto-accept when a hard constraint is "unconfirmed"; bearable wait (progress, result kept after reload, next automatic run shown); first-run sentence + plain-words result + reasons in the user's language; calendar on a phone (webcal, subscribe steps, Copied feedback, drop the second zone).
