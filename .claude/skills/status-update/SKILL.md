---
name: status-update
description: One-screen ASCII status block for the owner during long agent runs. Use when the owner asks for a status, "where are we", or a recurring update (every N minutes); also as the body of a cron or /loop prompt. No prose, facts from git and the tracker only.
---

# Status update

The owner reads this on a phone between two other things. One fenced block, nothing outside it, no prose, no questions, no options.

## Gather facts first (never from memory)

Run, in the main checkout:

```bash
date "+%H:%M"; git log --oneline -3; git status --short | wc -l
```

Then, when they apply to the work: the merge state (`ls .git/MERGE_HEAD`), the latest tracker comment title (`gh issue view <N> --json comments --jq '.comments[-1].body' | head -1`), and the live processes (`pgrep -fl "pytest|vitest|docker compose|playwright" | grep -v "sh -c" | head -2`). The live process tells you what is running now; the file count tells you whether an engineer is mid-edit.

## Format

```
HH:MM  <CURRENT STEP>                branch <name>  <sha>
--------------------------------------------------------
[x] <done item>                           <sha or count that proves it>
[ ] <current item>                        <- running now (<what the live process or tree shows>)
[ ] <pending item>
[ ] <pending item>

next: <the one thing that happens after the current item>
then: <the chain after that, arrows: a -> b -> c>
```

Rules:

- First line: time, step name in capitals, branch, short sha.
- Checklist in execution order. `[x]` only for things git or the tracker proves; attach the proof (sha, test counts, comment title). Never mark done on an agent's word alone.
- Exactly one `<- running now`, with evidence in parentheses: the live process, the number of edited files, or the merge in progress. When nothing is live, say so ("no live process: engineer editing").
- When a batch or test table exists, add one line per item under the checklist: `#n ok|stop|error kept=N  <5-word note>`, at most 20 lines.
- Problems ranked, one line each, only when something is red or blocked.
- Keep the same item list from one update to the next so the owner sees movement, not a new layout.
- Under 25 lines. Under 60 characters per line where possible.
- No sentences outside the block. No "I will", no apologies, no explanations of the method.

## Cadence

For "every N minutes": schedule a cron (session cron tool, or `/loop Nm /status-update`) whose prompt is the gather-and-format instructions above. Cancel it when the owner pauses the work or the run ends.
