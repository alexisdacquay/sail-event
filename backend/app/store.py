"""In-memory store: typed dicts keyed by user_id; seed data."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from .adapters import FakeScorer, FixtureSearchProvider
from .models import Criteria, Event, EventStatus, Thresholds


class UserRecord:
    def __init__(
        self,
        user_id: str,
        username: str,
        criteria: Criteria,
        thresholds: Thresholds,
        ics_token: str,
    ) -> None:
        self.user_id = user_id
        self.username = username
        self.criteria = criteria
        self.thresholds = thresholds
        self.ics_token = ics_token
        self.events: dict[str, Event] = {}  # event_id -> Event
        self.events_by_link: dict[str, str] = {}  # link -> event_id


class Store:
    def __init__(self) -> None:
        self.users: dict[str, UserRecord] = {}  # user_id -> UserRecord
        self.ics_token_to_user: dict[str, str] = {}  # ics_token -> user_id
        self._run_counter: int = 0

    def next_run_id(self) -> str:
        self._run_counter += 1
        return str(self._run_counter)

    def add_user(self, record: UserRecord) -> None:
        self.users[record.user_id] = record
        self.ics_token_to_user[record.ics_token] = record.user_id

    def add_event(self, user_id: str, event: Event) -> None:
        user = self.users[user_id]
        user.events[event.id] = event
        user.events_by_link[event.link] = event.id


def _seed() -> Store:
    store = Store()

    user_id = "demo"
    ics_token = "demo-ics-token"
    criteria = Criteria(
        text="outdoor activities, live music, and art workshops near Portland",
        updated_at=datetime.now(UTC).isoformat(),
    )
    thresholds = Thresholds(lower_threshold=30, upper_threshold=70)

    user = UserRecord(
        user_id=user_id,
        username="demo",
        criteria=criteria,
        thresholds=thresholds,
        ics_token=ics_token,
    )
    store.add_user(user)

    # Seed fixture events: deduplicated, scored, and triaged
    provider = FixtureSearchProvider()
    scorer = FakeScorer()
    raw_events = provider.search([])

    seen_links: set[str] = set()
    for raw in raw_events:
        if raw.link in seen_links:
            continue
        seen_links.add(raw.link)

        score_val, reason = scorer.score(raw, criteria.text)

        if score_val > thresholds.upper_threshold:
            status = EventStatus.accepted
        elif score_val < thresholds.lower_threshold:
            status = EventStatus.rejected
        else:
            status = EventStatus.queued

        event = Event(
            id=str(uuid4()),
            title=raw.title,
            date_time=raw.date_time,
            place=raw.place,
            link=raw.link,
            description=raw.description,
            score=score_val,
            score_reason=reason,
            status=status,
        )
        store.add_event(user_id, event)

    return store


store = _seed()
