"""Each invariant check catches its own violation and stays quiet on a clean case."""

from datetime import UTC, datetime

from invariants import check_events, check_isolation, check_run, check_stale, language

NOW = datetime(2026, 10, 21, 12, tzinfo=UTC)
PERSONA = {"text": "jazz in Berlin", "lang": "en", "country": "DE", "exclude": ["tribute"]}


def ev(**over):
    base = {
        "id": "1", "title": "Jazz night", "dateTime": "2026-11-02T20:00", "endTime": None,
        "country": "DE", "city": "Berlin", "link": "https://club.de/events/jazz-night",
        "description": "", "status": "accepted", "decidedBy": "auto", "score": 91,
        "scoreReason": "A jazz night in Berlin on the dates you gave matches your search.",
    }
    return {**base, **over}


def ids(findings):
    return sorted({inv for inv, _ in findings})


def test_clean_event_has_no_findings():
    assert check_events([ev()], PERSONA, NOW) == []


def test_each_event_invariant_fires():
    assert ids(check_events([ev(dateTime="2026-10-01")], PERSONA, NOW)) == ["I1"]
    assert ids(check_events([ev(dateTime="TBC")], PERSONA, NOW)) == ["I1"]
    assert ids(check_events([ev(country="US")], PERSONA, NOW)) == ["I2"]
    hedged = ev(scoreReason="A jazz show matches your search, though no place or dates were given.")
    assert ids(check_events([hedged], PERSONA, NOW)) == ["I3"]
    assert ids(check_events([hedged | {"decidedBy": "user"}], PERSONA, NOW)) == []
    spanish = ev(scoreReason="Un concierto de jazz en Berlín que encaja con lo que buscas.")
    assert ids(check_events([spanish], PERSONA, NOW)) == ["I5"]
    assert ids(check_events([ev(link="https://club.de/")], PERSONA, NOW)) == ["I6"]
    assert ids(check_events([ev(link="https://x.de/search?q=jazz")], PERSONA, NOW)) == ["I6"]
    assert ids(check_events([ev(), ev(id="2", title="JAZZ NIGHT!")], PERSONA, NOW)) == ["I7"]
    assert ids(check_events([ev(title="Beatles tribute band")], PERSONA, NOW)) == ["I12"]
    assert ids(check_events([ev()], {**PERSONA, "expect_kept": 0}, NOW)) == ["I13"]
    assert check_events([ev(status="rejected", dateTime="2020-01-01")], PERSONA, NOW) == []


def test_date_only_event_counts_until_end_of_day():
    assert check_events([ev(dateTime="2026-10-21")], PERSONA, NOW) == []


def test_language():
    assert language("A jazz night in Berlin on the dates you gave matches your search.") == "en"
    assert language("Un concierto de jazz en Berlín que encaja con lo que buscas.") == "es"
    assert language("東京のジャズライブ") == "ja"
    assert language("ok") is None


def test_run_invariants():
    good = {"stageCounts": {"results_fetched": 20, "events_extracted": 10, "events_judged": 6,
                            "accepted": 1, "queued": 2, "rejected": 3}, "eventsNew": 6}
    assert check_run(good, 0, 6) == []
    bad = {"stageCounts": {"events_extracted": 2, "events_judged": 6, "accepted": 1, "queued": 1, "rejected": 1},
           "eventsNew": 6, "error": "RuntimeError: Tavily API error", "stoppedAtStage": "search"}
    assert ids(check_run(bad, 0, 2)) == ["I10", "I4"]
    assert ids(check_run({"stoppedAtStage": "criteria", "error": ""}, 0, 0)) == ["I10"]


def test_stale_and_isolation():
    before = {"1": "old reason"}
    assert ids(check_stale(before, [ev(scoreReason="old reason")])) == ["I8"]
    assert check_stale(before, [ev(scoreReason="new reason")]) == []
    assert check_stale(before, [ev(scoreReason="old reason", decidedBy="user")]) == []
    assert ids(check_isolation({"a": {"1", "2"}, "b": {"2"}})) == ["I11"]
    assert check_isolation({"a": {"1"}, "b": {"2"}}) == []
