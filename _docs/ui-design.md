# UI design decisions

What the screens look like, why, and where each decision came from. Newest at the bottom of each table. Mockups live in `_docs/ui/` (open the HTML in a browser); the owner reviews them as claude.ai artifacts first, then they are copied here when a decision is taken.

Status words: **decided** (build it), **candidate** (owner leaning to it, not final), **rejected**, **built** (merged on main).

## Direction

| Date | Decision | Why | Where |
|---|---|---|---|
| 2026-10-21 | Main page = **Stream**: one column; the saved search text pinned at the top; the run as a chronology with the funnel; earlier runs; one-line event rows; a right rail with calendar, feed link, searches, event detail tied to the selected row. | Owner picked it from five directions (Stream, Agenda, Inbox, Spotlight, Board) and approved the assembled version ("awesome, I love it"). | `_docs/ui/03-stream-assembled.html` · built: issues 108 + 109, PRs 110 + 111 (main 07fff9d, 2026-10-22), on dev; one saved search per user in this version; ribbon colours are the app theme's, not the mockup's |
| 2026-10-21 | Agenda, Inbox, Spotlight, Board directions | Discarded by the owner after review. The Inbox's event-detail pane survives inside Stream. | `_docs/ui/01-five-directions.html` §02-05 · rejected |
| 2026-10-21 | Several saved searches per user (the rail lists them; "+ new search") | Every direction assumed it; owner: "we can add several saved searches as a feature if it makes sense". Not scheduled. | `_docs/ui/01-five-directions.html` · candidate |

## Stream, parts

| Date | Decision | Why | Where |
|---|---|---|---|
| 2026-10-21 | **Run funnel** beside the chronology: the N events found split into in calendar / to review / rejected (wrong date, off topic) / set aside (past, wrong place, duplicate), ribbons to scale. | Owner: show "ins and outs, how each became excluded or included and why". Explains a run at one glance; wrong dates and listing pages show up as the main loss. | `_docs/ui/02-stream-variants.html` §01+B, `_docs/ui/03-stream-assembled.html` · decided |
| 2026-10-21 | **Earlier runs** under the funnel: label "Earlier runs" on top, three rows (time, colour bar in the funnel's colours, "N found · a / b / c" on the same line), then "earlier ›" for the rest. | Owner: "did the hourly run find anything new" answered without opening anything; three rows is enough; right text must fit on one line. | `_docs/ui/03-stream-assembled.html` · decided |
| 2026-10-21 | **Event detail in the rail**, placed under Searches: title, when/where, buttons, score bar, the judge's sentence, source link. | Owner liked the Inbox detail pane; the rail has the room. | `_docs/ui/03-stream-assembled.html` · decided |
| 2026-10-21 | **Dotted tie** between the selected row and the detail: both get the one blue contour and tint used nowhere else, plus a dotted line from the row's right edge to the detail's left edge, drawn from the boxes' real positions. | Owner: the detail looked unrelated to the list; speech bubble too much; wanted colour contour or dotted line. | `_docs/ui/03-stream-assembled.html` · decided |
| 2026-10-21 | Detail opening inline under the row (no rail detail) | Owner: "too messy". | `_docs/ui/03-stream-assembled.html` (hidden section "alt") · rejected |
| 2026-10-21 | **Event rows on one line**: title · time · place · score · status pill, columns aligned across rows, long title cut with an ellipsis; on a phone the place column drops. | Owner: the two-line card wasted the horizontal space. | `_docs/ui/03-stream-assembled.html` · decided |

## Stream, revisions after the owner's first use on dev (2026-10-22)

| Date | Decision | Why | Where |
|---|---|---|---|
| 2026-10-22 | **Funnel at one scale** (candidate, supersedes the three-stage drawing where they differ): one px-per-event scale for the whole drawing; a count keeps its thickness wherever it appears; ribbons never taper; the judged ribbon is exactly the judged bar's height. Pages are a different unit and leave the drawing: "from 8 of 20 pages read" sits under "28 found", flush with that bar. Every label is anchored to one element, aligned to its left edge, details beneath, never under a neighbour. | Owner: "28 events shouldn't be smaller on the left than at the 2nd stage. It's the principle of the funnel"; "ensure the text doesn't overlap the diagram or sit in weird places". | issue 116, PR 117 (main d8d1a3a, 2026-10-22); screenshots `_docs/ui/116-funnel-light.png`, `116-funnel-dark.png` · built, on dev |
| 2026-10-22 | **Funnel in three stages**: pages read → events found (with "N pages: no events" as a side ribbon) → not judged (no date, past, duplicate) vs judged → in calendar / review / out (date or place, topic). The word "set aside" goes; "out" replaces "rejected" in pills and funnel. | Owner: "set aside isn't clear vs rejected, both are rejected in the end"; "should the funnel have more than 2 stages?" | mockup in the session (widget `stream_revisions_mockup`), issues 112 + 113, PRs 114 + 115 (main, 2026-10-22) · built, on dev |
| 2026-10-22 | Events without a start date get their own counter (`filtered_no_date`) and a ribbon. | The maths did not add up on dev (28 found, 17 + 6 shown): those events were counted with "pages with no events". | issue 112 · built (PRs 114 + 115, on dev) |
| 2026-10-22 | Search box: large, strong contour, the text itself is editable in place (click, type, Enter saves, Esc cancels); no Edit button; "Search again" is the only button. | Owner: "make the search bar more obvious"; "do I really need to edit? can I not click in the box?" | issue 113 · built (PRs 114 + 115, on dev) |
| 2026-10-22 | Theme switch (light/dark) top right, remembered in the browser. | Owner request. | issue 113 · built (PRs 114 + 115, on dev) |
| 2026-10-22 | Results list gets one column-header row (Event · Start · Where · Score · Status); time zone shown as a short name (CDT, BST) and only when it differs from the user's. | Owner: "what is 8%?"; "the time zone is too long, doesn't fit". | issue 113 · built (PRs 114 + 115, on dev) |
| 2026-10-22 | Remove the "To review" and "All events" pages and tabs. | The Stream shows the same rows; duplicates confuse. | issue 113 · built (PRs 114 + 115, on dev) |
| 2026-10-22 | Login and register pages restyled to the Stream look, with the pitch line. | Owner: "also update the login page". | issue 113 · built (PRs 114 + 115, on dev) |

## Event card (current app, before Stream)

| Date | Decision | Why | Where |
|---|---|---|---|
| 2026-10-21 | Card = title (link) / muted line `Tue 21 Oct · 21:00 · A-Trane, Berlin · Score: 95%` / action buttons / `Details ›` last, small, muted, opens the judge's sentence; closed by default, open for rejected. Band word ("fits", "mostly fits"…) and status badges removed. | Owner: "fits" means nothing to the user; "Score: 92%" does; the reason is useful for rejected events; "Details" must be the least obvious thing on the card. | issue 106, PR 107 (faadee9) · built |
| 2026-10-21 | Results under the search box: "Results" + "Clear all", summary line, groups "In your calendar (N)", "To review (N)", "Rejected (N) · show all". Live progress line while a run goes. | Owner: results were in tabs, "not visible, very small, not obvious"; the search section showed a static wait message. | issue 104, PR 105 (2802b81) · built |

## Rules the owner set for UI work

- Propose with pictures, not prose. Several options first, then iterate on the picked one; the rest are discarded and logged here.
- Review every proposal before showing it: useful to the owner, useful to the end user, every word earns its place.
- Nothing is built from a mockup until the owner says go; then it becomes an issue with the mockup file as the spec.
