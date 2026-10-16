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
- (none yet)

## Open asks
- which idea: K event finder (recommended, see IDEAS.md) / A / E..J. B, C withdrawn.
- if K: approve the v1 cut (key-less mode, ICS export, 1-2 sources) as spec non-goals?
- (closed) user: just unload the sonic/datasheet skills, no deletion. I cannot unload a skill
  from a running session (list is injected by the harness); rule: never invoke or infer from them.
- install project-scoped plugins (feature-dev, frontend-design, pr-review-toolkit,
  security-guidance, context7) via `claude plugin install X@claude-plugins-official --scope project`?
  writes ProjectOne/.claude/settings.json only. (user word pending)

## Notes
- datasheet-info-collector is a desktop-app session skill (Application Support/Claude/...),
  not removable from here; user manages it in the app's Skills settings.
- engineering:* skills (architecture, system-design, testing-strategy...) come from a
  desktop-app bundled plugin, global, not project-scoped.
