# Fact and link verification

Checked on 2026-10-26: all 27 changed Markdown files outside `work/`, against `origin/main` (`542e58cb0fe73065a905febec7637bfa377a77c4`). Reviewed docs are the rewrite committed in `02aff74`; HEAD at report time is `a84c660`. Sources checked include implementation/configuration, git history, GitHub issues and PR comments, CI logs and workflow runs, saved incident/recall records, screenshots, and HTTP GETs. No live registration, login or search was performed.

The prescribed command returned exit 0, **`all links ok`**:

```sh
python3 -I work/docs-pass/linkcheck.py $(git diff --name-only origin/main -- '*.md' | grep -v '^work/') README.md docs/reviewer-guide.md AGENTS.md
```

No broken links found. The checker validates relative links, Markdown anchors and pinned repository paths/line ranges. Additional GitHub API GETs verified all 52 distinct issue, PR and commit URLs in added lines; external document and hosted application GETs also resolved. The DeepSeek API base returns authentication-required HTTP 401, which is expected for an unauthenticated API endpoint, not a broken documentation link.

1. **Canonical URL deduplication is overstated.**

   **File and location:** `_docs/search-spec.md:63–64`, Candidate discovery.

   **Exact quote:** “Canonical result URLs are de-duplicated; previously stored single-event pages are removed before extraction.”

   **Problem:** Search-result deduplication compares raw `r.url` strings. Canonical equivalents that differ by a tracking parameter, fragment or trailing slash can both reach extraction. Canonicalization is used separately when comparing results with previously stored single-event pages. The sentence conflates these two operations.

   **Fix, with source:** Say: “Exact duplicate result URLs are removed. Canonical URL matching excludes previously stored single-event pages; stored listing pages remain eligible.” Source: `backend/app/services/pipeline.py:322–340` and `backend/app/adapters/search.py:40` (`canonical_url`) and `remove_known_pages`. Checked with `nl -ba backend/app/services/pipeline.py` and `nl -ba backend/app/adapters/search.py`. A read-only execution of the source's pure canonicalization function showed that `https://example.com/event?utm_source=test` and `https://example.com/event` produce one canonical URL, while the pipeline's raw-string set retains two.

   **Severity:** medium.

2. **The smoke instructions imply guardrail coverage that the script never exercises.**

   **File and location:** `docs/testing.md:124`, Real adapters smoke.

   **Exact quote:** “`GUARDRAIL=none` skips Lakera for local smoke runs. With `GUARDRAIL=lakera`, configure `LAKERA_API_KEY` and optionally `GUARD_FALLBACK=self_check`.”

   **Problem:** The script inserts criteria directly into its temporary database and calls `run_pipeline`; it never invokes the criteria-save endpoint or calls `get_guardrail`. Neither setting exercises Lakera or its fallback. Following this advice can therefore produce a successful smoke run with no guardrail check at all. This also contradicts the correct scope documented in `_docs/architecture.md` under Adapter interfaces.

   **Fix, with source:** State that this smoke tool bypasses criteria-save guardrails regardless of `GUARDRAIL`; remove the Lakera configuration advice from this tool's instructions and point guardrail verification to the criteria endpoint tests. Sources: `backend/scripts/smoke_search.py:134–167`, `backend/app/routers/criteria.py:51–66`, and `backend/tests/test_guardrails.py`. Verified with `rg -n 'get_guardrail|GUARDRAIL|GUARD_FALLBACK' backend/scripts/smoke_search.py backend/app/services backend/app/routers/criteria.py backend/app/adapters/factory.py`; the smoke file's only `get_guardrail` occurrence is an unused import at line 41.

   **Severity:** medium.

3. **The API definition omits the change in meaning of `events_judged` at finalization.**

   **File and location:** `docs/api.md:52`, Stage counters.

   **Exact quote:** “`events_to_judge`, `events_judged` | Live total entering the judge; events processed by the judge”

   **Problem:** During judging, `events_judged` counts completed attempts, including `JudgeError` results. After judging, it is overwritten with the count of this run's events whose score is non-null. With one success and one judge error, live progress can reach 2 and the finished counter becomes 1. “Events processed” does not accurately define the finished response and hides this observable decrease.

   **Fix, with source:** Define the two phases: “`events_to_judge` is the number of new candidates entering judging; live `events_judged` counts completed attempts, including failures, while the finished value counts events with a score.” Sources: `backend/app/services/pipeline.py:514`, `529–535`, `564–569`, and `701–714`. Verified by reading these assignments and the callback's position after the error/success branches with `nl -ba backend/app/services/pipeline.py`.

   **Severity:** low.

4. **`judge_repaired` includes reason repairs, not only schema repairs.**

   **File and location:** `docs/api.md:54`, Stage counters.

   **Exact quote:** “Responses repaired after schema validation failed; successfully scored events are excluded from `judge_errors`”

   **Problem:** A response can pass schema validation, fail the separate reason check, and be repaired successfully. That response also increments `judge_repaired`. The counter additionally includes successful repairs while recovering older `new` events, so it need not refer only to events discovered by this run.

   **Fix, with source:** Say: “Successfully scored responses repaired after schema or reason validation, including repairs during recovery of older events; these are excluded from the corresponding judge-error counter.” Sources: `backend/app/services/judge.py:125–130`, `187–218` and `backend/app/services/pipeline.py:196–198`, `708–712`. Verified with `nl -ba` on both files; reason repair explicitly sets `repaired = True` at `judge.py:214`.

   **Severity:** low.

5. **The reviewer checklist puts initial storage after judging.**

   **File and location:** `docs/reviewer-guide.md:65`, criterion 1 checklist, “the system functionality”.

   **Exact quote:** “Search → extract → event-page fetch → screen → score/triage → store → model duplicate check → feed.”

   **Problem:** Candidates are inserted and committed as `new` before scoring. This ordering is what preserves them for recovery if judging is interrupted. The checklist contradicts both the implementation and the correct ordering in `_docs/architecture.md` (Request flow) and `_docs/search-design.md` (Pipeline stages).

   **Fix, with source:** Use “Search → extract → event-page fetch → screen → store as new → score/triage → model duplicate check → feed.” Source: `backend/app/services/pipeline.py:487–515`; `db.commit()` is at line 510, before the judge stage begins. Verified with `nl -ba backend/app/services/pipeline.py`.

   **Severity:** low.

6. **The guide's promised full gap list omits two documented product gaps.**

   **File and location:** `docs/reviewer-guide.md:13` and Known gaps at `632–654`; also the description of this list in `README.md:252`.

   **Exact quotes:** “Main limitations (full list in [Known gaps](#known-gaps))”; “The [reviewer guide's gap list](docs/reviewer-guide.md#known-gaps) gives further detail, including open UI issues, incomplete issue labels, comment attribution and responder limits.”

   **Problem:** The guide and its gap index omit (a) criteria without a place can still auto-accept events, the unshipped owner requirement #101; and (b) an Out event offers “Add to calendar” but the backend rejects the action with HTTP 400. The first is disclosed in `README.md:248` and `_docs/search-spec.md:9–11,51–53`; the second is explicitly disclosed in `_docs/ux-spec.md:102–105`. Neither appears in the guide's claimed full list. This also fails the owner's STANDARD.md requirement that the known-gap list be complete.

   **Fix, with source:** Add short entries under criterion 1/5 for the unshipped no-place rule and the unusable Out-event restore action, linking the existing disclosures rather than repeating their detail. Sources: [issue #101](https://github.com/alexisdacquay/sail-event/issues/101), still OPEN as verified by `gh issue view 101 -R alexisdacquay/sail-event --json state,title,url`; `backend/app/services/pipeline.py:737–750` has no no-place acceptance restriction; `frontend/src/components/EventDetail.tsx:81–86` renders the rejected-event action; `backend/app/routers/events.py:80–84` returns 400 unless the current status is queued or accepted. Checked with `rg -n 'no.place|#101|Out|rejected' docs/reviewer-guide.md` and `nl -ba` on the cited implementation files.

   **Severity:** medium.

FAIL
