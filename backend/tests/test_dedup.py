"""#136 after-storage duplicate check: two real verdicts recorded from the owner's
London AI search (DeepSeek, replayed by FakeLanguageModel), and the merge rules."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from unittest.mock import patch

from app import orm
from app.adapters.llm_fake import FakeLanguageModel
from app.services.dedup import DUPLICATE_PREFIX, _inputs, dedup_run, same_as
from app.services.filters import attach_offset


def _ev(title, start, tz, country, venue, city, description, link="https://example.com/e", **kw) -> orm.Event:
    return orm.Event(title=title, date_time=attach_offset(start, tz, country), place=f"{venue}, {city}, {country}",
                     link=link, description=description, city=city, country=country, **kw)


def test_same_event_on_two_sites_with_different_titles():
    """Evidence rows 270 and 19: one Encode Club demo lunch, listed by two sites."""
    listed = _ev("Ship & Chips: Open Tech/AI Demos", "2026-10-30T13:30", "Europe/London", "GB", "Encode Hub", "London",
                 "Open tech and AI demo afternoon hosted by Encode Club at Encode Hub in London.",
                 link="https://hiddenevents.online/london/tech-events")
    own_page = _ev("Ship and Chips: Open Tech and AI Demos", "2026-10-30T13:30", "Europe/London", "GB", "Encode Hub", "London",
                   "Encode Club's Friday lunchtime open tech and AI demo slot in Hoxton: three minutes per demo, "
                   "lunch provided, free afternoon co-working. Free to attend.",
                   link="https://aievents.now/london/events/ship-and-chips-open-tech-ai-demos-2026-10-30")
    assert same_as(*_inputs(listed, [own_page]), model=FakeLanguageModel()) == 1


def test_two_events_same_day_same_venue_are_different():
    """Evidence rows 39 and 38: two shows at one venue, same day and hour."""
    cloud = _ev("Cloud & AI Infrastructure 2026", "2026-09-29T09:00", "Asia/Singapore", "SG", "Sands Expo Convention Centre",
                "Singapore", "Cloud & AI Infrastructure Asia 2026 explores AI-ready systems, cloud innovation and scalable "
                "infrastructure on 29–30 September in Singapore.")
    big_data = _ev("Big Data & AI World Asia 2026", "2026-09-29T09:00", "Asia/Singapore", "SG", "Sands Expo Convention Centre",
                   "Singapore", "Big Data & AI World Asia 2026 unites data and AI leaders in Singapore to explore analytics, "
                   "Gen AI and scalable data-driven innovation.")
    assert same_as(*_inputs(cloud, [big_data]), model=FakeLanguageModel()) is None


def test_merge_rules(_db_session):
    """Stored event kept, new one rejected; a pair naming each other keeps the better-scored one; an error keeps both;
    this run's own rejects are neither checked nor candidates."""
    db = _db_session
    user = db.query(orm.User).filter(orm.User.username == "demo").first()
    old_run = orm.Run(user_id=user.id, started_at=datetime.now(UTC), trigger="manual")
    run = orm.Run(user_id=user.id, started_at=datetime.now(UTC), trigger="manual")
    db.add_all([old_run, run])
    db.flush()

    def ev(title, status, run_id, minute, score=95):
        e = _ev(title, f"2026-10-29T18:{minute:02d}", "Europe/London", "GB", "Venue", "London", title,
                link=f"https://example.com/{minute}", user_id=user.id, status=status, run_id=run_id, score=score)
        db.add(e)
        return e

    stored = ev("Stored", "accepted", old_run.id, 0)
    a = ev("A", "accepted", run.id, 1)
    b = ev("B", "accepted", run.id, 2, score=98)
    c = ev("C", "queued", run.id, 3, score=80)
    d = ev("D", "accepted", run.id, 4)
    judged_out = ev("Judged out", "rejected", run.id, 5)
    db.commit()

    answers = {"A": "Stored", "B": "C", "C": "B", "D": RuntimeError("model down")}
    asked = []

    def fake_same_as(event_json, candidates_json, n, *, model):
        title = json.loads(event_json)["title"]
        asked.append(title)
        assert "Judged out" not in candidates_json
        answer = answers[title]
        if isinstance(answer, Exception):
            raise answer
        return [c["title"] for c in json.loads(candidates_json)].index(answer) + 1

    with patch("app.services.dedup.same_as", side_effect=fake_same_as):
        out = dedup_run(db, run, user.id, model=None, spent=0, workers=2)

    assert sorted(asked) == ["A", "B", "C", "D"]
    assert (out["dedup_merged"], out["dedup_errors"], out["short"]) == (2, 1, 0)
    assert stored.status == "accepted"
    assert (a.status, a.score_reason) == ("rejected", f"{DUPLICATE_PREFIX}Stored")
    assert (b.status, c.status, c.score_reason) == ("accepted", "rejected", f"{DUPLICATE_PREFIX}B")
    assert d.status == "accepted" and judged_out.status == "rejected"


def test_dedup_counts_in_stage_counts(client, auth_headers):
    """dedup_merged and dedup_errors are in every finished run's stageCounts."""
    sc = client.post("/api/search", headers=auth_headers("demo", "demo")).json()["stageCounts"]
    assert sc["dedup_errors"] == 0
    assert sc["accepted"] + sc["queued"] + sc["rejected"] == sc["events_judged"]
    assert sc["rejected_date_place"] + sc["rejected_off_topic"] + sc["rejected_other"] + sc["dedup_merged"] == sc["rejected"]
