"""Field-test invariants: what must hold for every Sail-event user, whatever they typed.

Code checks these; an LLM never grades them. A finding is (invariant, evidence). Findings are
grouped by invariant and layer; one GitHub issue per (invariant, layer) cluster, titled by the
invariant, never per symptom. Layers: recall, extract, judge, pipeline, api, ui-state, copy.

| id  | invariant                                                                  | checked by          |
|-----|----------------------------------------------------------------------------|---------------------|
| I1  | no kept event is already over, or has a date that does not parse           | check_events        |
| I2  | when the criteria name a place, every kept event is in that country        | check_events        |
| I3  | no auto-accept whose reason hedges ("no place given", "not confirmed")     | check_events        |
| I4  | counters sum: judged = accepted+queued+rejected; new rows = eventsNew       | check_run           |
| I5  | the reason is written in the language of the criteria                      | check_events        |
| I6  | a kept event links to the event page, not a site root or a listing page    | check_events        |
| I7  | the same title on the same day never twice for one user                    | check_events        |
| I8  | after a criteria change nothing stays silently stale                       | check_stale         |
| I9  | decisions are reversible                                                   | battery.py (API)    |
| I10 | a run never surfaces a raw exception or a stop without a reason            | check_run           |
| I11 | no cross-user leakage                                                      | check_isolation     |
| I12 | exclusions written in the criteria are honoured                            | check_events        |
| I13 | a non-event or an injection keeps nothing                                  | check_events        |
| U1-4| page state on reload, result line = cards, slider, copy feedback           | e2e/field.spec.ts   |

"kept" = status accepted or queued. Severity: on an accepted event high, on a queued one medium.
Event dicts are the /api/events shape (dateTime, endTime, scoreReason, decidedBy, ...).
"""

from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta

KEPT = ("accepted", "queued")
HEDGE = re.compile(
    r"not confirmed|unconfirmed|rather than|no (?:place|city|location|date)s?\b|not specified"
    r"|although|though|however|but it is in|outside",
    re.I,
)
LISTING_LINK = re.compile(r"^https?://[^/]+/?$|/search|[?&]q=|/(?:events|calendar|agenda|whats-on)/?$", re.I)
RAW_ERROR = re.compile(r"\b\w*(?:Error|Exception)\b|Traceback|^'[A-Z_]+'$")
STOPWORDS = {
    "en": "the and your with for matches search this that from were given".split(),
    "es": "el la los las un una con para por que es del tu sin pero como".split(),
    "pt": "o os as um uma com para por que do da não seu sua mas como".split(),
    "de": "der die das und mit für ist nicht ein eine im auf zu ihre aber".split(),
    "fr": "le les des et avec pour est pas un une dans votre mais comme".split(),
}
_CJK = re.compile(r"[぀-ヿ一-鿿]")


def language(text: str) -> str | None:
    """Rough language of a sentence from stopwords; None when unsure."""
    if _CJK.search(text):
        return "ja"
    words = re.findall(r"[a-zà-ÿ]+", text.lower())
    hits = {lang: sum(w in sw for w in words) for lang, sw in STOPWORDS.items()}
    best = max(hits, key=hits.get)
    ranked = sorted(hits.values(), reverse=True)
    if ranked[0] < 3 or ranked[0] == ranked[1]:
        return None
    return best


def event_end(ev: dict) -> datetime | None:
    """When the event is over, in UTC. Date-only events end at the end of that day."""
    raw = ev.get("endTime") or ev.get("dateTime") or ""
    try:
        dt = datetime.fromisoformat(raw)
    except ValueError:
        return None
    if len(raw) == 10:
        dt += timedelta(days=1)
    # shortcut: a naive time is read as UTC (one day of slack is covered by the day rounding),
    # upgrade to the event's startTz if same-day cases become the question
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


def check_events(events: list[dict], persona: dict, now: datetime) -> list[tuple[str, str]]:
    """I1 I2 I3 I5 I6 I7 I12 I13 over one user's events. persona keys: lang, country, exclude, expect_kept."""
    out: list[tuple[str, str]] = []
    kept = [e for e in events if e.get("status") in KEPT]
    seen: dict[tuple[str, str], str] = {}
    for e in kept:
        tag = f"{e.get('status')} {e.get('score')} «{e.get('title', '')[:40]}» {e.get('dateTime', '')[:16]} {e.get('city')},{e.get('country')}"
        end = event_end(e)
        if end is None:
            out.append(("I1", f"unparsed date: {tag}"))
        elif end < now:
            out.append(("I1", f"already over: {tag}"))
        if persona.get("country") and e.get("country") != persona["country"]:
            out.append(("I2", f"outside {persona['country']}: {tag}"))
        reason = e.get("scoreReason") or ""
        if e.get("status") == "accepted" and e.get("decidedBy") != "user" and HEDGE.search(reason):
            out.append(("I3", f"{tag} — {reason[:100]}"))
        lang = language(reason)
        if persona.get("lang") and lang and lang != persona["lang"]:
            out.append(("I5", f"reason in {lang}, criteria in {persona['lang']}: {reason[:80]}"))
        if LISTING_LINK.search(e.get("link") or ""):
            out.append(("I6", f"{tag} link {e.get('link')}"))
        key = (re.sub(r"\W+", " ", (e.get("title") or "").lower()).strip(), (e.get("dateTime") or "")[:10])
        if key in seen:
            out.append(("I7", f"{tag} duplicates {seen[key]}"))
        seen[key] = tag
        text = f"{e.get('title', '')} {e.get('description', '')}".lower()
        for word in persona.get("exclude") or []:
            if word.lower() in text:
                out.append(("I12", f"excluded «{word}» kept: {tag}"))
    if persona.get("expect_kept") == 0 and kept:
        out.append(("I13", f"{len(kept)} kept for «{persona.get('text', '')[:40]}»"))
    return out


def check_run(report: dict, events_before: int, events_after: int) -> list[tuple[str, str]]:
    """I4 and I10 over one /api/search report."""
    out: list[tuple[str, str]] = []
    c = report.get("stageCounts") or {}
    judged = c.get("events_judged", 0)
    decided = c.get("accepted", 0) + c.get("queued", 0) + c.get("rejected", 0)
    if judged != decided:
        out.append(("I4", f"judged {judged} ≠ accepted+queued+rejected {decided}"))
    if judged > c.get("events_extracted", judged):
        out.append(("I4", f"judged {judged} > extracted {c.get('events_extracted')}"))
    new = report.get("eventsNew")
    if new is not None and events_after - events_before != new:
        out.append(("I4", f"eventsNew {new} but the list grew by {events_after - events_before}"))
    err = report.get("error") or ""
    if err and RAW_ERROR.search(err):
        out.append(("I10", f"raw error shown: {err[:90]}"))
    if report.get("stoppedAtStage") and not err:
        out.append(("I10", f"stopped at {report['stoppedAtStage']} with no reason"))
    return out


def check_stale(before: dict[str, str], after: list[dict]) -> list[tuple[str, str]]:
    """I8: kept auto-decided events whose reason did not change after the criteria changed."""
    out: list[tuple[str, str]] = []
    for e in after:
        if e.get("status") in KEPT and e.get("decidedBy") != "user" and before.get(e["id"]) == e.get("scoreReason"):
            out.append(("I8", f"stale {e.get('status')} {e.get('score')} «{e.get('title', '')[:40]}»"))
    return out


def check_isolation(ids_by_user: dict[str, set[str]]) -> list[tuple[str, str]]:
    """I11: no event id appears for two users."""
    out: list[tuple[str, str]] = []
    users = list(ids_by_user)
    for i, a in enumerate(users):
        for b in users[i + 1 :]:
            shared = ids_by_user[a] & ids_by_user[b]
            if shared:
                out.append(("I11", f"{a} and {b} share {len(shared)} events"))
    return out
