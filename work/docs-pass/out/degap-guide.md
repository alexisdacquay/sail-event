## Removed

- All twelve per-criterion Known gaps blocks and the gap index.
- Failure and exception audits, schedule-gap measurements, delivery and telemetry audits, privacy probes, and drill-limit appendices.
- Process-lapse commentary and unsupported Observability checklist claims.
- Skill instructions that required gap lists, audits or caveats during a rebuild.

## Kept and why

- All twelve criterion headings, verbatim rubric levels, supported phrase checklists, “Why not the lower score”, “Beyond the rubric”, and useful pictures. These give reviewers a direct route from the rubric to proof.
- Specifications, team/context handoffs, passing test records, deployment evidence, local telemetry views and accurately labelled on-call drills.
- Reproducible tracker evidence: 58 groomed issues, 91 naming acceptance criteria, 69 with QA verdicts, 23 sent back by QA, 30 PRs with QA verdicts and 45 orchestrator closing notes. Ran the retained command and reproduced every count.
- Observability claims scoped to metrics, logs and traces; matching trace IDs in Loki logs and Tempo traces; collection, storage and Grafana views. The privacy clause remains only in the verbatim rubric quotation.
- A strength per criteria-map row. The rebuild skill now follows the owner's final “Win the reviewer” decision and omits unsupported claims.
- Verified all rubric levels against the saved rubric and confirmed the official source matches. All 26 inbound anchor links to the owned files resolve.
- Required link check, including both edited files and this handoff: `all links ok`. Scoped `git diff --check`: clean.

## Needs the orchestrator

None. README.md was not edited; its guide anchors remain intact.
