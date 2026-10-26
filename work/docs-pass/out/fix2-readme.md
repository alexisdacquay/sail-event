## Fixed

- Final review #2: replaced the defensive duplicate-result wording with “No event shows twice in In calendar or Review”; verified the accepted/queued uniqueness assertion in `backend/tests/integration/test_integration.py:103–129` with a file read and `git show 542e58cb0fe73065a905febec7637bfa377a77c4:backend/tests/integration/test_integration.py`.
- Final review #3: replaced “imperfect” with the measured 3/38 found, 0/38 accepted result, bounded to the local 2026-10-24 20:04 UTC run at `ab21641`; linked its exact recall-log section and disclosed the unvetted ground truth verified in `work/STATE.md:17`.
- Final review #3: added the open-issues link; `gh issue list -R alexisdacquay/sail-event --state open --limit 100 --json number,title,url` returned the listed open issues.
- Final review #5: dated worktrees/PR review and adoption of the QA definition to 20 October 2026, and owner pick/prod approval to 21 October; verified `_docs/process.md`, `work/STATE.md`, QA-definition git history, and `gh issue view 65 -R alexisdacquay/sail-event --json number,title,createdAt`.
- Final review #8: changed “explains the delays” to “measures the gaps” after reading the guide's schedule evidence.
- Final review #9: linked past rows directly to issue #94; `gh issue view 94 -R alexisdacquay/sail-event --json number,title,state,body` confirms the past-events criterion and OPEN state.
- Final review #15: clarified that calendar aggregators collect listings from sources they already know; compared the Problem text with `git show 'ac54483^:README.md'`.
- Final review #16: changed “PM adds” to “PM also reads” after reading the PM role's Inputs section.
- Final review #17: renamed “Try it” to “Run it locally” and “How it is built” to “Architecture”; retained an explicit `try-it` anchor for the guide's existing setup links.
- Final review #18: changed the promotion diagram to “Owner approves that SHA”; verified the named-SHA manual workflow in `.github/workflows/promote.yml` and the owner checklist in `docs/release-process.md`.
- Bounded the drill reference to its two named dates instead of asserting a total number of recorded drills; README contains no aggregate PR counts or `git log -S` commands to repair for final-review #1/#6.
- Re-read README end to end; `python3 -I work/docs-pass/linkcheck.py README.md docs/reviewer-guide.md` returned `all links ok`, and `git diff --check -- README.md` passed.

## Rejected

- Final review #3, “the one full recall run”: the exclusivity claim is false. A Python read splitting `work/RECALL.md` by its dated headings found several 38-event runs, including 12/38 found and 5/38 accepted at 2026-10-24 20:00 UTC on localhost:8031 (`work/RECALL.md:103–119`), and 3/38 found and 0/38 accepted at 20:04 UTC on localhost:8032 (`work/RECALL.md:139–155`), both at `ab21641`. README names the requested 20:04 result without claiming it was the only full run.

## Needs the owner

None for README.
