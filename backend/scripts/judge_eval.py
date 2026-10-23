#!/usr/bin/env python3
"""Judge evaluation: openrouter/free vs DeepSeek pro vs DeepSeek flash.

Usage:
    set -a; . backend/.env.local; set +a
    uv run --project backend --directory backend python scripts/judge_eval.py --phase extract
    uv run --project backend --directory backend python scripts/judge_eval.py --phase judge
    uv run --project backend --directory backend python scripts/judge_eval.py --phase report
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import statistics
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.adapters.prompts.loader import load_prompt, validate_response

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

WORK_DIR = Path(__file__).resolve().parent.parent.parent / "work" / "judge-eval"
GT_DIR = Path(__file__).resolve().parent.parent / "tests" / "ground_truth"

# ---------- LLM call (raw, no app dependency) ----------

def llm_call(
    *,
    base_url: str,
    api_key: str,
    model: str,
    prompt_text: str,
    max_retries: int = 3,
    backoff_base: float = 5.0,
    timeout: int = 180,
) -> dict:
    """Call an OpenAI-compatible chat/completions endpoint, return parsed JSON + meta."""
    url = f"{base_url.rstrip('/')}/chat/completions"
    body = {
        "model": model,
        "temperature": 0,
        "max_tokens": 16000,
        "messages": [{"role": "user", "content": prompt_text}],
        "response_format": {"type": "json_object"},
    }
    raw_body = json.dumps(body).encode()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    last_err = None
    for attempt in range(max_retries):
        if attempt > 0:
            wait = backoff_base * (2 ** (attempt - 1))
            logger.info("  retry %d in %.0fs", attempt, wait)
            time.sleep(wait)
        t0 = time.monotonic()
        try:
            req = urllib.request.Request(url, data=raw_body, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read())
            latency = time.monotonic() - t0

            content = data["choices"][0]["message"].get("content") or ""
            if not content.strip():
                last_err = RuntimeError("empty content")
                continue

            # The model field from the response tells us which model actually ran
            actual_model = data.get("model", model)
            usage = data.get("usage", {})

            try:
                parsed = json.loads(content)
            except json.JSONDecodeError:
                return {
                    "parsed": None,
                    "raw_content": content,
                    "actual_model": actual_model,
                    "latency": latency,
                    "tokens_in": usage.get("prompt_tokens", 0),
                    "tokens_out": usage.get("completion_tokens", 0),
                    "error": "json_parse_error",
                }

            return {
                "parsed": parsed,
                "raw_content": content,
                "actual_model": actual_model,
                "latency": latency,
                "tokens_in": usage.get("prompt_tokens", 0),
                "tokens_out": usage.get("completion_tokens", 0),
                "error": None,
            }

        except urllib.error.HTTPError as exc:
            latency = time.monotonic() - t0
            logger.warning("  HTTP %d (%.1fs), attempt %d", exc.code, latency, attempt)
            last_err = exc
            if exc.code == 429:
                time.sleep(backoff_base * (2 ** attempt))
            continue
        except Exception as exc:
            latency = time.monotonic() - t0
            logger.warning("  error: %s (%.1fs), attempt %d", exc, latency, attempt)
            last_err = exc
            continue

    return {
        "parsed": None,
        "raw_content": None,
        "actual_model": model,
        "latency": 0,
        "tokens_in": 0,
        "tokens_out": 0,
        "error": f"failed after {max_retries} attempts: {last_err}",
    }


# ---------- Phase 1: extract events from ground-truth pages ----------

def phase_extract():
    """Use DeepSeek pro to extract events from ground-truth pages."""
    pages = json.loads((GT_DIR / "pages.json").read_text())
    triples = json.loads((GT_DIR / "triples.json").read_text())["triples"]
    triple_map = {t["id"]: t for t in triples}

    base_url = os.environ["KILO_BASE_URL"]
    api_key = os.environ["KILO_API_KEY"]
    model = "~deepseek/deepseek-pro-latest"

    # Load extract prompt template and schema
    extract_md = (Path(__file__).resolve().parent.parent / "app" / "adapters" / "prompts" / "extract_v2.md").read_text()
    extract_schema = json.loads((Path(__file__).resolve().parent.parent / "app" / "adapters" / "prompts" / "extract_v2.schema.json").read_text())

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    dataset = []
    total_events = 0

    for i, page in enumerate(pages):
        if not page.get("has_events") or not page.get("raw_content"):
            continue

        triple_id = page["triple_id"]
        triple = triple_map.get(triple_id)
        if not triple:
            continue

        place = triple.get("place") or {}
        city = place.get("city", "unknown")
        country = place.get("country", "unknown")

        # Build a reasonable window based on the criteria
        window_start = "2026-10-24"
        window_end = "2026-11-30"

        content = page["raw_content"][:20000]  # same slice as the app

        variables = {
            "today": today,
            "target_city": city,
            "target_country": country,
            "window_start": window_start,
            "window_end": window_end,
            "content": content,
            "schema": json.dumps(extract_schema, indent=2),
        }
        rendered = extract_md.format(**variables)

        logger.info("[%d/%d] Extracting from %s (%s)...", i + 1, len(pages), page["url"][:60], triple_id)

        result = llm_call(
            base_url=base_url,
            api_key=api_key,
            model=model,
            prompt_text=rendered,
            max_retries=3,
            timeout=180,
        )

        if result["error"] or not result["parsed"]:
            logger.warning("  extraction failed: %s", result["error"])
            continue

        events = result["parsed"].get("events", [])
        for ev in events:
            if ev.get("confidence", 0) < 0.5:
                continue
            dataset.append({
                "triple_id": triple_id,
                "criteria": triple["criteria"],
                "user_tz": triple["timeZone"],
                "event": {
                    "title": ev.get("title", ""),
                    "start_local": ev.get("start_local", ""),
                    "start_tz": ev.get("start_tz"),
                    "city": ev.get("city"),
                    "country": ev.get("country"),
                    "description": ev.get("description", ""),
                    "link": ev.get("link", page["url"]),
                },
                "source_url": page["url"],
            })
            total_events += 1

        logger.info("  extracted %d events (total: %d)", len(events), total_events)
        time.sleep(0.5)  # be kind to the API

    out_path = WORK_DIR / "dataset.json"
    out_path.write_text(json.dumps(dataset, indent=2) + "\n")
    logger.info("Saved %d events to %s", len(dataset), out_path)


# ---------- Phase 2: judge all events with 3 routes ----------

JUDGE_SCHEMA = {
    "type": "object",
    "required": ["score", "reason", "is_event"],
    "additionalProperties": False,
    "properties": {
        "score": {"type": "integer", "minimum": 0, "maximum": 100},
        "reason": {"type": "string"},
        "is_event": {"type": "boolean"},
    },
}


def _render_judge_prompt(event: dict, criteria: str, user_tz: str) -> str:
    """Render the judge v3 prompt for one event."""
    judge_md = (Path(__file__).resolve().parent.parent / "app" / "adapters" / "prompts" / "judge_v3.md").read_text()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    event_json = json.dumps(event)
    schema_text = json.dumps(JUDGE_SCHEMA, indent=2)

    return judge_md.format(
        criteria_text=criteria,
        event_json=event_json,
        today=today,
        user_tz=user_tz,
        schema=schema_text,
    )


def _validate_verdict(parsed: dict | None) -> str | None:
    """Check if parsed response matches the judge schema. Returns error or None."""
    if parsed is None:
        return "no_response"
    if not isinstance(parsed, dict):
        return "not_object"
    for field in ("score", "reason", "is_event"):
        if field not in parsed:
            return f"missing_{field}"
    if not isinstance(parsed.get("score"), int):
        return "score_not_int"
    if not (0 <= parsed["score"] <= 100):
        return "score_out_of_range"
    if not isinstance(parsed.get("reason"), str):
        return "reason_not_string"
    if not isinstance(parsed.get("is_event"), bool):
        return "is_event_not_bool"
    return None


def _judge_one(
    item: dict,
    *,
    route_name: str,
    base_url: str,
    api_key: str,
    model: str,
    max_retries: int = 3,
    backoff_base: float = 5.0,
) -> dict:
    """Judge one event and return the result row."""
    prompt_text = _render_judge_prompt(item["event"], item["criteria"], item["user_tz"])

    result = llm_call(
        base_url=base_url,
        api_key=api_key,
        model=model,
        prompt_text=prompt_text,
        max_retries=max_retries,
        backoff_base=backoff_base,
    )

    schema_error = _validate_verdict(result["parsed"])

    # Repair round-trip: if schema error and we got raw content, re-ask
    repaired = False
    if schema_error and result["raw_content"]:
        repair_prompt = (
            f"Your previous response was not valid JSON matching the schema.\n"
            f"Error: {schema_error}\n"
            f"Your response was: {result['raw_content'][:500]}\n\n"
            f"Please respond again with ONLY valid JSON matching this schema:\n"
            f"{json.dumps(JUDGE_SCHEMA, indent=2)}\n\n"
            f"Original task:\n{prompt_text}"
        )
        repair_result = llm_call(
            base_url=base_url,
            api_key=api_key,
            model=model,
            prompt_text=repair_prompt,
            max_retries=2,
            backoff_base=backoff_base,
        )
        schema_error_after = _validate_verdict(repair_result["parsed"])
        if schema_error_after is None:
            # Repair succeeded
            repaired = True
            result["latency"] += repair_result["latency"]
            result["tokens_in"] += repair_result["tokens_in"]
            result["tokens_out"] += repair_result["tokens_out"]
            result["parsed"] = repair_result["parsed"]
            schema_error = None

    parsed = result["parsed"] or {}
    return {
        "route": route_name,
        "triple_id": item["triple_id"],
        "event_title": item["event"]["title"][:80],
        "actual_model": result["actual_model"],
        "latency": round(result["latency"], 2),
        "score": parsed.get("score"),
        "reason": parsed.get("reason", ""),
        "is_event": parsed.get("is_event"),
        "schema_error_before": schema_error if not repaired else _validate_verdict({"_bad": True}),
        "schema_error_after": schema_error,
        "repaired": repaired,
        "error": result["error"],
        "tokens_in": result["tokens_in"],
        "tokens_out": result["tokens_out"],
    }


def _reviewer_call(
    event: dict,
    criteria: str,
    verdict: dict,
    *,
    base_url: str,
    api_key: str,
    model: str,
    reviewer_name: str,
) -> dict:
    """Ask a reviewer to check the verdict for faithfulness."""
    prompt = (
        f"You are a quality reviewer. An AI judge scored an event against user criteria.\n"
        f"Check the judge's verdict for quality.\n\n"
        f"Criteria: {criteria}\n"
        f"Event: {json.dumps(event)}\n"
        f"Judge verdict: score={verdict.get('score')}, reason=\"{verdict.get('reason', '')}\"\n\n"
        f"Answer ONLY with JSON matching this schema:\n"
        f'{{"faithful": bool, "names_mismatch": bool, "agree": bool}}\n'
        f"- faithful: the reason states only facts present in the event or criteria (no hallucinations)\n"
        f"- names_mismatch: for scores below 40, the reason names the wrong date/place/topic\n"
        f"- agree: you would give a similar score (within 15 points)\n"
    )

    result = llm_call(
        base_url=base_url,
        api_key=api_key,
        model=model,
        prompt_text=prompt,
        max_retries=3,
        backoff_base=5.0,
    )

    parsed = result["parsed"] or {}
    return {
        "reviewer": reviewer_name,
        "actual_model": result["actual_model"],
        "faithful": parsed.get("faithful"),
        "names_mismatch": parsed.get("names_mismatch"),
        "agree": parsed.get("agree"),
        "latency": round(result["latency"], 2),
        "error": result["error"],
    }


def phase_judge(route_filter: str | None = None):
    """Judge all events with routes A (pro), B (flash), C (free).

    route_filter: if set, run only that route (e.g. 'A', 'B', 'C').
    """
    sampled_path = WORK_DIR / "dataset_sampled.json"
    ds_path = sampled_path if sampled_path.exists() else WORK_DIR / "dataset.json"
    dataset = json.loads(ds_path.read_text())
    logger.info("Loaded %d events from %s", len(dataset), ds_path.name)

    kilo_url = os.environ["KILO_BASE_URL"]
    kilo_key = os.environ["KILO_API_KEY"]
    or_url = os.environ["OPENROUTER_BASE_URL"]
    or_key = os.environ["OPENROUTER_API_KEY"]

    routes = [
        ("A_deepseek_pro", kilo_url, kilo_key, "~deepseek/deepseek-pro-latest", 3, 3.0),
        ("B_deepseek_flash", kilo_url, kilo_key, "deepseek/deepseek-v4.1-flash", 3, 3.0),
        ("C_openrouter_free", or_url, or_key, "openrouter/free", 5, 8.0),
    ]

    # Filter routes if requested
    if route_filter:
        routes = [r for r in routes if r[0].startswith(route_filter)]
        if not routes:
            logger.error("No route matches filter %r", route_filter)
            return

    all_results = []

    for route_name, base_url, api_key, model, retries, backoff in routes:
        logger.info("=== Route %s (%s) ===", route_name, model)
        route_results = []

        for i, item in enumerate(dataset):
            logger.info("  [%d/%d] %s", i + 1, len(dataset), item["event"]["title"][:50])
            row = _judge_one(
                item,
                route_name=route_name,
                base_url=base_url,
                api_key=api_key,
                model=model,
                max_retries=retries,
                backoff_base=backoff,
            )
            route_results.append(row)

            # Rate limiting for openrouter
            if "openrouter" in route_name.lower():
                time.sleep(2)
            else:
                time.sleep(0.3)

        all_results.extend(route_results)

        # Save intermediate results per route
        out = WORK_DIR / f"results_{route_name}.json"
        out.write_text(json.dumps(route_results, indent=2) + "\n")
        logger.info("Saved %d results to %s", len(route_results), out)

    # Save all results
    out = WORK_DIR / "results_all.json"
    out.write_text(json.dumps(all_results, indent=2) + "\n")
    logger.info("Saved %d total results to %s", len(all_results), out)

    if route_filter and not route_filter.startswith("C"):
        logger.info("Skipping reviewer/escalation (route filter = %s)", route_filter)
        return

    # Phase 2b: reviewer pass on C's verdicts
    logger.info("=== Reviewer pass on C verdicts ===")
    c_results = [r for r in all_results if r["route"] == "C_openrouter_free" and r["score"] is not None]
    reviews_flash = []
    reviews_free = []

    for i, row in enumerate(c_results):
        item = dataset[i] if i < len(dataset) else None
        if not item:
            continue

        logger.info("  [%d/%d] reviewing: %s", i + 1, len(c_results), row["event_title"][:40])

        # Reviewer 1: DeepSeek flash
        rev_flash = _reviewer_call(
            item["event"], item["criteria"], row,
            base_url=kilo_url, api_key=kilo_key,
            model="deepseek/deepseek-v4.1-flash",
            reviewer_name="flash_reviewer",
        )
        reviews_flash.append(rev_flash)
        time.sleep(0.3)

        # Reviewer 2: openrouter/free itself
        rev_free = _reviewer_call(
            item["event"], item["criteria"], row,
            base_url=or_url, api_key=or_key,
            model="openrouter/free",
            reviewer_name="free_reviewer",
        )
        reviews_free.append(rev_free)
        time.sleep(2)

    (WORK_DIR / "reviews_flash.json").write_text(json.dumps(reviews_flash, indent=2) + "\n")
    (WORK_DIR / "reviews_free.json").write_text(json.dumps(reviews_free, indent=2) + "\n")

    # Phase 2c: escalation — re-judge with pro when reviewer flags or score near threshold
    logger.info("=== Escalation pass ===")
    escalations = []
    for i, (row, rev) in enumerate(zip(c_results, reviews_flash)):
        needs_escalation = False
        reason = ""

        if rev.get("faithful") is False or rev.get("names_mismatch") is True:
            needs_escalation = True
            reason = "reviewer_flagged"
        elif row["score"] is not None:
            # Within 10 of thresholds 90 or 40
            s = row["score"]
            if 80 <= s <= 100 or 30 <= s <= 50:
                needs_escalation = True
                reason = "near_threshold"

        if needs_escalation and i < len(dataset):
            item = dataset[i]
            logger.info("  escalating [%d]: %s (%s)", i, row["event_title"][:40], reason)
            esc_row = _judge_one(
                item,
                route_name="C_escalated_to_pro",
                base_url=kilo_url,
                api_key=kilo_key,
                model="~deepseek/deepseek-pro-latest",
                max_retries=3,
                backoff_base=3.0,
            )
            esc_row["escalation_reason"] = reason
            esc_row["original_score"] = row["score"]
            escalations.append(esc_row)
            time.sleep(0.5)
        else:
            escalations.append(None)

    (WORK_DIR / "escalations.json").write_text(
        json.dumps([e for e in escalations if e], indent=2) + "\n"
    )
    logger.info("Escalated %d / %d events", sum(1 for e in escalations if e), len(c_results))


# ---------- Phase 3: report ----------

def _decision(score: int | None, t_accept: int = 90, t_reject: int = 40) -> str:
    if score is None:
        return "error"
    if score >= t_accept:
        return "accept"
    if score < t_reject:
        return "reject"
    return "review"


def phase_report():
    """Compute metrics and write the report."""
    all_results = json.loads((WORK_DIR / "results_all.json").read_text())
    reviews_flash = json.loads((WORK_DIR / "reviews_flash.json").read_text())
    reviews_free = json.loads((WORK_DIR / "reviews_free.json").read_text())
    escalations_raw = json.loads((WORK_DIR / "escalations.json").read_text())
    dataset = json.loads((WORK_DIR / "dataset.json").read_text())

    # Split by route
    by_route: dict[str, list] = {}
    for r in all_results:
        by_route.setdefault(r["route"], []).append(r)

    a_results = by_route.get("A_deepseek_pro", [])
    b_results = by_route.get("B_deepseek_flash", [])
    c_results = by_route.get("C_openrouter_free", [])

    n = min(len(a_results), len(b_results), len(c_results))

    def _metrics(ref: list, test: list, label: str) -> dict:
        agreements_90 = 0
        agreements_40 = 0
        abs_errors = []
        schema_violations_before = 0
        schema_violations_after = 0
        repairs = 0
        latencies = []
        errors = 0

        for i in range(n):
            r = ref[i]
            t = test[i]

            if t.get("error") or t.get("score") is None:
                errors += 1
                continue
            if r.get("error") or r.get("score") is None:
                continue

            ref_dec = _decision(r["score"])
            test_dec = _decision(t["score"])
            if ref_dec == test_dec:
                agreements_90 += 1
                agreements_40 += 1
            else:
                # Check at individual thresholds
                ref_90 = "accept" if r["score"] >= 90 else "other"
                test_90 = "accept" if t["score"] >= 90 else "other"
                if ref_90 == test_90:
                    agreements_90 += 1

                ref_40 = "reject" if r["score"] < 40 else "other"
                test_40 = "reject" if t["score"] < 40 else "other"
                if ref_40 == test_40:
                    agreements_40 += 1

            abs_errors.append(abs(r["score"] - t["score"]))
            latencies.append(t["latency"])

            if t.get("repaired"):
                repairs += 1
            if t.get("schema_error_before"):
                schema_violations_before += 1
            if t.get("schema_error_after"):
                schema_violations_after += 1

        valid = n - errors
        dec_agree = sum(
            1 for i in range(n)
            if (not ref[i].get("error") and ref[i].get("score") is not None
                and not test[i].get("error") and test[i].get("score") is not None
                and _decision(ref[i]["score"]) == _decision(test[i]["score"]))
        )

        return {
            "label": label,
            "n": n,
            "valid": valid,
            "errors": errors,
            "decision_agreement": f"{dec_agree / valid * 100:.1f}%" if valid else "N/A",
            "score_mae": f"{statistics.mean(abs_errors):.1f}" if abs_errors else "N/A",
            "schema_violation_before_repair": schema_violations_before,
            "schema_violation_after_repair": schema_violations_after,
            "repairs": repairs,
            "latency_p50": f"{statistics.median(latencies):.1f}s" if latencies else "N/A",
            "latency_p95": f"{sorted(latencies)[int(len(latencies) * 0.95)]:.1f}s" if len(latencies) > 1 else "N/A",
        }

    m_b = _metrics(a_results, b_results, "B (flash) vs A (pro)")
    m_c = _metrics(a_results, c_results, "C (free) vs A (pro)")

    # Guarded C: replace with escalation where available
    c_guarded = list(c_results[:n])
    esc_map = {}
    for esc in escalations_raw:
        # Find matching index
        for i, cr in enumerate(c_results[:n]):
            if cr["event_title"] == esc.get("event_title") and i not in esc_map:
                esc_map[i] = esc
                break
    for i, esc in esc_map.items():
        c_guarded[i] = esc

    m_cg = _metrics(a_results, c_guarded, "C+guard vs A (pro)")

    # Hallucination rate from reviewer
    c_valid = [i for i in range(min(len(c_results), len(reviews_flash)))
               if c_results[i].get("score") is not None]
    halluc_flash = sum(1 for i in c_valid if reviews_flash[i].get("faithful") is False)
    halluc_free = sum(1 for i in range(min(len(c_results), len(reviews_free)))
                      if i in set(c_valid) and reviews_free[i].get("faithful") is False)

    # Free models actually used
    free_models = {}
    for r in c_results:
        m = r.get("actual_model", "unknown")
        free_models[m] = free_models.get(m, 0) + 1
    for rev in reviews_free:
        m = rev.get("actual_model", "unknown")
        free_models[m] = free_models.get(m, 0) + 1

    # Worst C reasons
    worst = []
    for i in range(min(len(a_results), len(c_results))):
        a = a_results[i]
        c = c_results[i]
        if a.get("score") is not None and c.get("score") is not None:
            diff = abs(a["score"] - c["score"])
            worst.append((diff, i, a, c, dataset[i] if i < len(dataset) else None))
    worst.sort(key=lambda x: -x[0])

    escalation_count = len(escalations_raw)
    escalation_rate = f"{escalation_count / len(c_valid) * 100:.1f}%" if c_valid else "N/A"

    # Build report
    lines = [
        "# Judge Evaluation: openrouter/free vs DeepSeek",
        f"Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
        f"Dataset: {n} events across {len(set(d['triple_id'] for d in dataset))} criteria triples",
        "",
        "## Setup",
        "- A (reference): DeepSeek pro via Kilo (`~deepseek/deepseek-pro-latest`)",
        "- B (today's model): DeepSeek flash via Kilo (`deepseek/deepseek-v4.1-flash`)",
        "- C (candidate): openrouter/free via OpenRouter (routes to different free models per call)",
        "- Prompt: judge_v3 (the app's real prompt), temperature 0, json_object mode",
        "- Guardrails (C only): schema repair, flash reviewer for hallucinations, escalate to pro on flag or near threshold",
        "",
        "## Free models actually used by OpenRouter",
        "",
    ]
    for m, count in sorted(free_models.items(), key=lambda x: -x[1]):
        lines.append(f"- `{m}`: {count} calls")

    lines += [
        "",
        "## Metrics",
        "",
        "| Metric | B (flash) vs A | C (free) vs A | C+guard vs A |",
        "|--------|---------------|--------------|-------------|",
        f"| Events judged | {m_b['valid']} / {m_b['n']} | {m_c['valid']} / {m_c['n']} | {m_cg['valid']} / {m_cg['n']} |",
        f"| Decision agreement (90/40) | {m_b['decision_agreement']} | {m_c['decision_agreement']} | {m_cg['decision_agreement']} |",
        f"| Score MAE | {m_b['score_mae']} | {m_c['score_mae']} | {m_cg['score_mae']} |",
        f"| Schema violations (before repair) | {m_b['schema_violation_before_repair']} | {m_c['schema_violation_before_repair']} | — |",
        f"| Schema violations (after repair) | {m_b['schema_violation_after_repair']} | {m_c['schema_violation_after_repair']} | — |",
        f"| Latency p50 | {m_b['latency_p50']} | {m_c['latency_p50']} | {m_cg['latency_p50']} |",
        f"| Latency p95 | {m_b['latency_p95']} | {m_c['latency_p95']} | {m_cg['latency_p95']} |",
        f"| Errors (no valid response) | {m_b['errors']} | {m_c['errors']} | {m_cg['errors']} |",
        "",
        "## Hallucination rate (C verdicts reviewed)",
        "",
        f"- Flash reviewer: {halluc_flash} / {len(c_valid)} unfaithful ({halluc_flash / len(c_valid) * 100:.1f}%)" if c_valid else "- No data",
        f"- Free reviewer: {halluc_free} / {len(c_valid)} unfaithful ({halluc_free / len(c_valid) * 100:.1f}%)" if c_valid else "- No data",
        "",
        "## Escalation",
        "",
        f"- Escalation rate: {escalation_rate} ({escalation_count} / {len(c_valid)} events)",
        f"- Escalation triggers: reviewer flagged or score within 10 of threshold (90 or 40)",
        "",
        "## Cost per 100 events",
        "",
        "| Route | Cost per 100 events |",
        "|-------|-------------------|",
        "| A (pro) | ~$0.50-1.00 (Kilo pricing) |",
        "| B (flash) | ~$0.05-0.10 (Kilo pricing) |",
        "| C (free) | $0.00 |",
        "| C+guard (free + flash reviewer + pro escalation) | ~$0.05-0.15 |",
        "",
        "## Failure examples (3 worst C reasons vs A)",
        "",
    ]

    for rank, (diff, idx, a, c, item) in enumerate(worst[:3], 1):
        ev = item["event"] if item else {}
        lines += [
            f"### {rank}. score diff {diff}: A={a['score']} vs C={c['score']}",
            f"- Event: {ev.get('title', '?')} — {ev.get('city', '?')}, {ev.get('country', '?')} — {ev.get('start_local', '?')}",
            f"- Criteria: {item['criteria'] if item else '?'}",
            f"- A reason: {a.get('reason', '')}",
            f"- C reason: {c.get('reason', '')}",
            f"- C model: {c.get('actual_model', '?')}",
            "",
        ]

    lines += [
        "## Recommendation",
        "",
    ]

    # Generate recommendation based on data
    c_agree = m_c["decision_agreement"]
    cg_agree = m_cg["decision_agreement"]
    lines += [
        f"Decision agreement C vs A: {c_agree}. With guardrails: {cg_agree}.",
        f"Hallucination rate: {halluc_flash / len(c_valid) * 100:.1f}% (flash reviewer)." if c_valid else "",
        f"Escalation rate: {escalation_rate}.",
        "",
        "See raw data in `work/judge-eval/` for per-event detail.",
    ]

    report = "\n".join(lines) + "\n"
    report_path = WORK_DIR.parent / "JUDGE-EVAL-2026-10-23.md"
    report_path.write_text(report)
    logger.info("Report written to %s", report_path)

    # Also print a summary
    print("\n" + report)


# ---------- CLI ----------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=["extract", "judge", "report", "all"], required=True)
    parser.add_argument("--route", type=str, default=None, help="Filter to one route: A, B, or C")
    args = parser.parse_args()

    if args.phase in ("extract", "all"):
        phase_extract()
    if args.phase in ("judge", "all"):
        phase_judge(route_filter=args.route)
    if args.phase in ("report", "all"):
        phase_report()


if __name__ == "__main__":
    main()
