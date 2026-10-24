# Roadmap — later changes (owner feedback 2026-10-17, priority set by the orchestrator)

| Prio | Item | Owner's words (verbatim) | Direction | Size |
|---|---|---|---|---|
| P1 | UX-driven interface | "Thresholds doesn't talk to the user. What it means is auto-accept, auto-reject, and more importantly, it's the event score. You don't mention any of that. so "threshold" out of the blue is cryptic." / "it will require a complete UI/UX-driven interface. Not fields for code variables." | Redesign the main page around the user's job, not the data model: "Auto-accept events scoring above __", "Auto-reject below __", with the queue explained as "ask me in between"; show a score scale (0–100) with the two cut-offs on it; criteria card with an example; queue cards lead with the reason, not the score. Walk the 3 pages as a first-time user before coding. New issue when started. | L |
| P2 | Visual theme | "UI is simple (good) but not appealing. We should try to make it "sexy" and intuitive." / "prettiness and sexy/cool/modern/tech taste. Lesser priority than UX. It's easy to change a colour scheme." | After P1: palette, type scale, spacing, dark mode, empty states, motion on accept/reject. Tailwind tokens only; no new UI library. | M |
| P3 | Icon / logo | "an icon for sail-event, with a sail boat sail something like SAIL on top, then boat in sandwich, EVENT(s) at the bottom. just a suggestion, you will have to come with ideas of your own." | Favicon + header mark; 3 proposals as SVG before picking. | S |
| Q | Admin / telemetry page | "Should we propose an admin page with telemetry, etc? Maybe not on the user site/app, on its own? (Graphana, etc?). But maybe you already have that?" | Already exists as Grafana (operator-only, separate stack, `make up-all`, port 3001): dashboard, alerts, logs, traces. Not inside the user app: operators and users are different audiences, and the app stays small. Possible later: a read-only `/admin/status` page (runs, errors, users count) behind an admin token, only if Grafana proves too heavy for the operator. Default: no. | — |

Not before P1: anything that adds fields named after env vars or columns.

## Status 2026-10-18 (overnight run)
| Prio | Done | Where |
|---|---|---|
| P1 | Spec → design → review → issues #40-#44 + polish #46, all QA PASS, PRs #45 #47 merged | `_docs/ux-spec.md`, `_docs/ux-design.md`, `_docs/ux-design-review.md` |
| P2 | Design → review → issues #48-#50, all QA PASS, PR #51 merged; light + dark (OS), Bricolage Grotesque headings, sail mark, motion | `_docs/theme-design.md`, `_docs/theme-design-review.md` |
| P3 | Three SVG proposals; b-sail-mark chosen, now the favicon and header mark | `_docs/icon-proposals/` |
| Q | Answered: Grafana is the operator view; no admin page | — |
- Live on dev (auto-deploy). Prod stays on 93ad48f until the owner runs the promote workflow with the merge commit.
- Open design calls recorded for the owner: light-mode primaries are navy (teal fails text contrast); dark mode follows the OS, no toggle; one Google Fonts request per page load (Geist fallback).

## Deferred

- **CI red-before-green gate**: a workflow step that runs the new regression tests on the fix's parent commit and fails if they pass there (~60 lines). Needs test and fix in separate commits. Deferred by the owner on 2026-10-24 until the single runner (issue #135) exists.
