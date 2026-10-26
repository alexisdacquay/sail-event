---
name: reviewer-guide
description: Rebuild docs/reviewer-guide.md and the README reviewer table from the current rubric and repo. Use before submission or after any doc change.
---

# Reviewer guide

A peer reviewer has 15 minutes and scores 0 for anything they cannot find.
This skill makes every rubric point findable in two clicks from the README, with proof one click further.

Outputs:
- [docs/reviewer-guide.md](../../../docs/reviewer-guide.md): one section per criterion, fixed shape.
- The **For reviewers** table at the top of [README.md](../../../README.md): criterion | max | where to look | one-line proof.

## Steps

1. **Fetch the rubric.** `curl -s https://raw.githubusercontent.com/DataTalksClub/ai-dev-tools-zoomcamp/main/project/README.md`.
   `diff` it with the saved copy in `work/rubric-*.md`. If it changed, save the new one with today's date and note what moved (criteria, points, levels).
2. **Split each criterion into atomic claims**, in the rubric's own words.
   Example, Agent team: roles named · responsibilities clear · team defined · process defined · how they work together.
3. **Find the evidence for each claim**: a repo-relative link, a URL, or a command the reviewer can copy.
   Write one proof line per claim. Mark each claim present, weak or missing. Fix weak and missing ones in the doc that owns them first.
4. **List the lose-a-point risks.** Quote the next-lower level of the rubric. For each way a stranger could land there, say how we are covered. If we are not, write "Not covered yet" or "Partly", never pretend.
5. **Add extra credit**: 2-3 items beyond the rubric that would win the reviewer back if they dislike something else.
6. **Pick one visual per criterion**: a mermaid diagram (GitHub renders it) or a screenshot from `docs/images/`.
   Capture new screenshots on public pages or a local stack. Never sign in to a hosted site unless the owner's request names it.
7. **Write each section in the fixed shape**, short sentences, tables over prose:
   - **Full marks**: the rubric text, quoted.
   - **Checklist**: rubric words | where | proof.
   - **Why not the lower score**: risk | how we are covered.
   - **Extra evidence**: bullets with links.
   - **Picture**.
   Then rebuild the README table: one row per criterion, first link = the guide section, second = the main evidence. Keep **Known gaps** at the end of the guide, honest.
8. **Check every link.** Repo-relative paths must exist, `#anchors` must match a heading, `#L` anchors must be inside the file, URLs must answer 200.
   Pin code-line links to a commit (`blob/<sha>/path#L10`) so they do not drift.
9. **Blind review.** Run the [rubric-review](../rubric-review/SKILL.md) skill. Every "where I got lost" and "what would raise it" becomes a fix to this guide or the README. Repeat until the three reviewers agree on the score.

## Rules

- Every claim has a link or a command. No link, no claim.
- Counts come from a command you ran today, and the command is in the doc.
- Never edit files owned by an open PR. Link to them instead.
- Do not file issues or promote to prod from this skill; report gaps to the owner.
- A gap that costs a rubric point goes in the README row and the guide's scorecard, not only in Known gaps. Blind reviewers lose trust when a confident row meets a "Partly" 800 lines later.
- Say which test layers CI runs and in which job. A count that CI does not run is labelled "local only".
- Name the folder split (`_docs/` vs `docs/`) wherever a reviewer meets both.
- Docs on a branch do not exist for a reviewer: the guide counts only once it is on the default branch.
