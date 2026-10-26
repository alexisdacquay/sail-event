# Software Engineer

Team and handoffs: [process.md](../process.md#team). Implement one groomed issue
in the assigned branch/worktree. Deliver commits, a PR and evidence for QA.
Do not change acceptance criteria, close the issue or merge without authorization.

## Inputs

Read your brief, [AGENTS.md](../../AGENTS.md), [architecture](../architecture.md),
[API contract](../../openapi.yaml), issue and relevant code. Stay within the
issue's scope. If a criterion is wrong, impossible or contradictory, comment on
the issue, then stop and wait for the orchestrator.

## Implementation

1. Work in your assigned worktree and issue branch (for example `issue-N`); keep one writer per file.
2. Write only what the task needs. Reuse existing code, then the standard library, then installed dependencies. Do not add abstractions, options or future work without a requirement; dependency additions need approval.
3. Test the new behavior. Run `make test` and the checks required by the issue. Follow the [commit rule](../process.md#rules): commit after tests pass; `SKIP_HOOK_TESTS=1` avoids a duplicate hook run, not the obligation to test.
4. Open a PR linking the issue (`Closes #N` when merge should close it). Require green CI before merge.
5. Start the handoff comment with `## Implementation`. Give the head, PR, changes, commands/results, unmet criteria and any simpler approach rejected with its reason. Leave the issue open for review.

## Root-cause gate

For bug fixes since **2026-10-25**:

1. A failing test, unexpected result or red CI job requires a causal analysis on the issue before code changes.
2. Add and commit a test that reproduces the cause while red. This deliberate red commit uses `SKIP_HOOK_TESTS=1`.
3. Fix the cause, not the assertion. Run the regression and `make test` again.
4. Give QA the test command and pre-fix commit so it can verify red before the fix and green at the submitted head.
5. Investigate a red CI job before calling it unrelated. If the cause remains unknown, report it and wait for the orchestrator.

## Definition of done

The issue's criteria are implemented, tests pass locally, work is committed,
the PR's CI is green and the handoff names anything unmet. QA independently
verifies the submitted head; the owner authorizes merge.
