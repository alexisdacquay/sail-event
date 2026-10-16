# ProjectOne — work state (resumable)

## Goal
Pick a project for DataTalksClub AI Dev Tools Zoomcamp (ProjectOne = temp name).

## Status
- [x] git init, work file created (2026-10-15)
- [x] fetch project instructions + rubric
- [x] read course modules 01-05
- [x] record understanding (work/UNDERSTANDING.md)
- [x] propose ideas (work/IDEAS.md)
- [ ] user picks idea (OPEN ASK since 2026-10-15)

## Decisions
- 2026-10-15 plugins installed at project scope (user: "yes deploy the 5 skills"):
  feature-dev, frontend-design, pr-review-toolkit, security-guidance, context7.
  -> .claude/settings.json in this folder. global settings unchanged (verified: langfuse only).
  active from the next session start.
- 2026-10-15 skills sonic-hw-recon / datasheet-info-collector: cannot unload mid-session;
  rule: never invoke or infer from them.

- 2026-10-15 user: shape axes (sources, relevance, output, users, operations, non-goals)
  are seeds, keep them all. We follow the course method, lesson by lesson. work/METHOD.md.
- 2026-10-15 idea K (event finder) is the working idea; formal confirmation comes out of
  the lesson-1 brainstorm (plan.md), not a chat yes.

## Where we are in the method (see work/METHOD.md)
- lesson 1, step 1: brainstorm, one question at a time. Q&A log: work/BRAINSTORM.md
- next: plan.md -> stack options -> tasks.md -> AGENTS.md/process.md -> roles

## Open asks
- brainstorm Q1 pending (see BRAINSTORM.md)

## Notes
- datasheet-info-collector is a desktop-app session skill (Application Support/Claude/...),
  not removable from here; user manages it in the app's Skills settings.
- engineering:* skills (architecture, system-design, testing-strategy...) come from a
  desktop-app bundled plugin, global, not project-scoped.
