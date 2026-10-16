- Tasks are GitHub issues
- One issue at a time
- Read the acceptance criteria before starting and before closing
- Commit regularly

Labels

- `mvp` - needed for the MVP defined in `_docs/plan.md`
- `post-mvp` - real work, deliberately not now
- Every issue carries exactly one of the two

Roles

- PM - grooms a task before anyone implements it, follows `_docs/team/pm.md`
- Engineer - implements one groomed task, follows `_docs/team/software-engineer.md`
- QA - checks the result against the acceptance criteria, follows `_docs/team/qa-engineer.md`

Orchestrator

The main session is the orchestrator. It launches the PM, the engineer
and QA as subagents. It does not groom, implement or test itself.

Lifecycle

1. Pick the next issue
2. PM grooms it
3. Engineer implements it
4. QA verifies it
5. On FAIL: back to engineer with the QA comment
6. On PASS: close the issue
7. Repeat until the backlog is empty

Rules

- Do not skip grooming, even when the task looks obvious
- The engineer does not close the issue, QA does not fix the code
- Do not commit until the tests pass
- Only the orchestrator closes issues
