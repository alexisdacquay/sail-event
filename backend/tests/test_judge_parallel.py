"""#142: the judge stage scores events in parallel, safely."""

from __future__ import annotations

import json
import threading
import time
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.orm import Base, Criteria, Event, Run, User
from app.services import pipeline


def _score_for(title: str) -> int:
    return int(title.split()[-1]) * 5


class _SlowModel:
    """Sleeps per call; verdict keyed by event title, so thread order cannot change it."""

    model_id = "test:slow"

    def __init__(self, sleep_seconds: float = 0.1):
        self._sleep = sleep_seconds
        self.calls = 0
        self._lock = threading.Lock()

    def complete_json(self, *, variables, **kwargs):
        time.sleep(self._sleep)
        with self._lock:
            self.calls += 1
        title = json.loads(variables["event_json"])["title"]
        usage = type("U", (), {"tokens_in": 10, "tokens_out": 3})()
        return {"score": _score_for(title), "reason": f"r {title}", "is_event": True}, usage


def _add_events(db, user, n: int) -> list[Event]:
    events = [
        Event(
            user_id=user.id, title=f"Event {i:02d}", date_time="2026-10-20T21:00:00+02:00",
            place="Berlin", link=f"https://e.example.com/{i}", description="d",
            start_tz="Europe/Berlin", city="Berlin", country="DE",
            source_url=f"https://e.example.com/{i}", status="new",
        )
        for i in range(n)
    ]
    db.add_all(events)
    db.commit()
    return events


def _rows(events):
    return sorted((e.title, e.score, e.score_reason, e.status, e.decided_by) for e in events)


def test_parallel_judge_is_faster_and_identical(_db_session, monkeypatch):
    db = _db_session
    user = db.query(User).filter(User.username == "demo").first()
    crit = db.query(Criteria).filter(Criteria.user_id == user.id).first()
    events = _add_events(db, user, 20)

    def judge(concurrency):
        monkeypatch.setattr(pipeline, "JUDGE_CONCURRENCY", concurrency, raising=False)
        progress: list[int] = []
        t0 = time.monotonic()
        out = pipeline._judge_and_triage(
            events, crit, crit.text, user.time_zone, user, _SlowModel(), db,
            on_event_done=progress.append,
        )
        return time.monotonic() - t0, out, _rows(events), progress

    wall5, out5, rows5, progress5 = judge(5)
    for e in events:
        e.score = e.score_reason = e.decided_by = None
        e.status = "new"
    wall1, out1, rows1, _ = judge(1)

    # Relative, not fixed seconds: a loaded machine slows both runs alike; 5 workers ideally take 1/5
    assert wall5 <= wall1 / 3, f"5 workers took {wall5:.2f}s, 1 worker {wall1:.2f}s"
    assert rows5 == rows1
    assert out5 == out1
    llm_calls, tokens_in, tokens_out, _, _ = out5
    assert (llm_calls, tokens_in, tokens_out) == (20, 200, 60)
    assert progress5 == list(range(1, 21))  # completed events, never calls


def test_judge_error_counts_every_call_and_token():
    from datetime import datetime, timezone
    from app.services.extract import ExtractedEvent
    from app.services.judge import JudgeError, judge_event

    class _BadReason:
        model_id = "test:bad"

        def complete_json(self, **kwargs):
            usage = type("U", (), {"tokens_in": 7, "tokens_out": 2})()
            return {"score": 50, "reason": "see https://x.example.com", "is_event": True}, usage

    ev = ExtractedEvent(
        title="T", start_local="2026-10-20T21:00:00", start_tz="Europe/Berlin", end_local=None,
        venue=None, city="Berlin", country="DE", link="https://x.example.com", description="d",
        confidence=0.9, source_url="https://x.example.com", page_kind="single_event",
    )
    result = judge_event(
        ev, criteria_text="jazz", facets={}, user_tz="Europe/Berlin", model=_BadReason(),
        window_start=datetime(2026, 10, 19, tzinfo=timezone.utc),
        window_end=datetime(2026, 10, 21, tzinfo=timezone.utc),
    )
    assert isinstance(result, JudgeError)
    assert (result.calls, result.tokens_in, result.tokens_out) == (2, 14, 4)


def test_worker_exception_cancels_pending_calls(_db_session, monkeypatch):
    db = _db_session
    user = db.query(User).filter(User.username == "demo").first()
    crit = db.query(Criteria).filter(Criteria.user_id == user.id).first()
    events = _add_events(db, user, 10)
    monkeypatch.setattr(pipeline, "JUDGE_CONCURRENCY", 2, raising=False)
    calls: list[int] = []
    lock = threading.Lock()

    def _raising(event, **kwargs):
        with lock:
            calls.append(1)
            n = len(calls)
        time.sleep(0.05)
        if n == 2:
            raise RuntimeError("boom")
        from app.services.judge import Verdict
        return Verdict(score=95, reason="t", fit={}, is_event=True, capped=False)

    with patch("app.services.pipeline.judge_event", side_effect=_raising):
        try:
            pipeline._judge_and_triage(events, crit, crit.text, user.time_zone, user, None, db)
            raised = False
        except RuntimeError:
            raised = True
    assert raised
    assert len(calls) <= 2 + 2
    assert all(e.status == "new" for e in events)


def test_event_spans_are_children_of_judge_span(_db_session, monkeypatch):
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

    exporter = InMemorySpanExporter()
    tp = TracerProvider()
    tp.add_span_processor(SimpleSpanProcessor(exporter))
    monkeypatch.setattr(pipeline, "tracer", tp.get_tracer("test"))
    monkeypatch.setattr(pipeline, "JUDGE_CONCURRENCY", 5, raising=False)

    db = _db_session
    user = db.query(User).filter(User.username == "demo").first()
    crit = db.query(Criteria).filter(Criteria.user_id == user.id).first()
    events = _add_events(db, user, 6)
    pipeline._judge_and_triage(events, crit, crit.text, user.time_zone, user, _SlowModel(0.01), db)

    spans = exporter.get_finished_spans()
    judge = [s for s in spans if s.name == "judge"]
    children = [s for s in spans if s.name == "event"]
    assert len(judge) == 1 and len(children) == 6
    assert all(s.parent is not None and s.parent.span_id == judge[0].context.span_id for s in children)


# ---------- two runs at once: file SQLite, one session per thread ----------


class _CountingModel:
    def __init__(self, inner, judge_sleep: float = 0.0):
        self._inner = inner
        self._sleep = judge_sleep
        self.model_id = inner.model_id
        self.calls = 0
        self._lock = threading.Lock()

    def complete_json(self, **kwargs):
        with self._lock:
            self.calls += 1
        if kwargs.get("prompt_name") == "judge":
            time.sleep(self._sleep)
        return self._inner.complete_json(**kwargs)


def _file_db(path):
    """File SQLite with the demo seed plus a second user with the same criteria."""
    from tests.conftest import _seed

    engine = create_engine(f"sqlite:///{path}", connect_args={"check_same_thread": False, "timeout": 30})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    s = Session()
    _seed(s)
    demo = s.query(User).filter(User.username == "demo").first()
    crit = s.query(Criteria).filter(Criteria.user_id == demo.id).first()
    other = User(username="demo2", password_hash=demo.password_hash, upper_threshold=90,
                 lower_threshold=40, time_zone="Europe/Berlin", ics_token="demo2-ics")
    s.add(other)
    s.flush()
    s.add(Criteria(user_id=other.id, text=crit.text, facets_json=crit.facets_json,
                   facets_version=crit.facets_version, facets_text_sha=crit.facets_text_sha))
    s.commit()
    s.close()
    return Session


def _run_in_thread(Session, username, model, results, barrier=None):
    s = Session()
    try:
        user = s.query(User).filter(User.username == username).first()
        if barrier:
            barrier.wait()
        with patch("app.services.pipeline.get_language_model", return_value=model):
            run = pipeline.run_pipeline(user, s, trigger="manual")
        results[username] = (run.llm_calls, run.error, json.loads(run.stage_counts))
    finally:
        s.close()


def test_two_concurrent_runs_never_overspend(tmp_path, monkeypatch):
    from app.adapters.llm_fake import FakeLanguageModel

    # Calibrate: each user's calls with no budget pressure (fake model never repairs: 1 call per event)
    cal = _file_db(tmp_path / "cal.db")
    cal_res: dict = {}
    for name in ("demo", "demo2"):
        _run_in_thread(cal, name, _CountingModel(FakeLanguageModel()), cal_res)
    total = sum(r[0] for r in cal_res.values())
    n = {k: r[2]["events_to_judge"] for k, r in cal_res.items()}
    assert min(n.values()) > 0 and all(r[1] is None for r in cal_res.values())

    # Cap at the larger run's worst case (3 calls per event): either run fits alone, both do not
    cap = max(calls + 2 * n[k] for k, (calls, _, _) in cal_res.items())
    assert total + 2 * sum(n.values()) > cap, "precondition: both worst cases must not fit"
    monkeypatch.setenv("LLM_DAILY_CALLS", str(cap))

    Session = _file_db(tmp_path / "race.db")
    model = _CountingModel(FakeLanguageModel(), judge_sleep=0.02)
    barrier = threading.Barrier(2)
    results: dict = {}
    threads = [threading.Thread(target=_run_in_thread, args=(Session, name, model, results, barrier))
               for name in ("demo", "demo2")]
    for t in threads:
        t.start()
    for t in threads:
        t.join(60)

    assert set(results) == {"demo", "demo2"}
    s = Session()
    spent = sum(r.llm_calls or 0 for r in s.query(Run).all())
    s.close()
    assert spent <= cap, f"runs spent {spent} > cap {cap}"
    assert model.calls <= cap, f"model called {model.calls} > cap {cap}"
    stopped = [k for k, r in results.items()
               if r[1] == "budget: llm" or r[2].get("events_judged", 0) < n[k]]
    assert stopped, results


def test_leftover_recovery_skips_unfinished_runs(tmp_path, monkeypatch):
    """Run B for the same user, started while run A judges, must not judge A's events."""
    from app.services.judge import Verdict

    Session = _file_db(tmp_path / "same.db")
    first_call = threading.Event()
    b_done = threading.Event()
    lock = threading.Lock()
    judged: list[str] = []

    def _judge(event, **kwargs):
        with lock:
            judged.append(event.title)
            first = len(judged) == 1
        if first:
            first_call.set()
            b_done.wait(30)
        return Verdict(score=95, reason="t", fit={}, is_event=True, capped=False)

    def _run(results):
        s = Session()
        try:
            user = s.query(User).filter(User.username == "demo").first()
            run = pipeline.run_pipeline(user, s, trigger="manual")
            results.append(run.id)
        finally:
            s.close()

    a_res: list = []
    with patch("app.services.pipeline.judge_event", side_effect=_judge):
        a = threading.Thread(target=_run, args=(a_res,))
        a.start()
        assert first_call.wait(30)
        b_res: list = []
        _run(b_res)
        b_done.set()
        a.join(60)

    s = Session()
    a_events = s.query(Event).filter(Event.run_id == a_res[0]).all()
    # owner 2026-10-25: B re-stores and judges its own re-found listing events, never A's
    b_events = s.query(Event).filter(Event.run_id == b_res[0]).all()
    s.close()
    assert a_events
    assert len(judged) == len(a_events) + len(b_events), \
        f"{len(judged)} judge calls for {len(a_events)} A + {len(b_events)} B events"


def test_full_run_same_rows_and_counts_at_concurrency_1_and_5(tmp_path, monkeypatch):
    """Fake model: a run at JUDGE_CONCURRENCY=5 writes the same rows and stage_counts as at 1."""
    out = []
    for c in (5, 1):
        monkeypatch.setattr(pipeline, "JUDGE_CONCURRENCY", c)
        Session = _file_db(tmp_path / f"c{c}.db")
        s = Session()
        user = s.query(User).filter(User.username == "demo").first()
        run = pipeline.run_pipeline(user, s, trigger="manual")
        rows = sorted((e.title, e.score, e.score_reason, e.status, e.decided_by)
                      for e in s.query(Event).filter(Event.run_id == run.id).all())
        out.append((rows, json.loads(run.stage_counts), run.llm_calls, run.llm_tokens_in, run.llm_tokens_out))
        s.close()
    assert out[0][0]
    assert out[0] == out[1]
