"""SQLAlchemy 2.x ORM models for the Sail-event data model."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _uuid() -> str:
    return str(uuid4())


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("lower_threshold < upper_threshold", name="ck_user_thresholds"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    upper_threshold: Mapped[int] = mapped_column(Integer, nullable=False)
    lower_threshold: Mapped[int] = mapped_column(Integer, nullable=False)
    time_zone: Mapped[str] = mapped_column(String(64), nullable=False, server_default="UTC", default="UTC")
    ics_token: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, default=_uuid)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow)


class Criteria(Base):
    __tablename__ = "criteria"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), unique=True, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    facets_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    facets_version: Mapped[str | None] = mapped_column(String(16), nullable=True)
    facets_text_sha: Mapped[str | None] = mapped_column(String(64), nullable=True)
    parsed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (
        UniqueConstraint("user_id", "link", "date_time", name="uq_event_user_link_date"),
        CheckConstraint(
            "status IN ('new','accepted','rejected','queued')",
            name="ck_event_status",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    date_time: Mapped[str] = mapped_column(String, nullable=False)
    place: Mapped[str] = mapped_column(String, nullable=False)
    link: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    start_tz: Mapped[str | None] = mapped_column(String(64), nullable=True)
    end_time: Mapped[str | None] = mapped_column(String, nullable=True)
    source_url: Mapped[str | None] = mapped_column(String, nullable=True)
    page_kind: Mapped[str | None] = mapped_column(String(16), nullable=True)
    city: Mapped[str] = mapped_column(String, nullable=False, server_default="", default="")
    country: Mapped[str] = mapped_column(String(2), nullable=False, server_default="ZZ", default="ZZ")
    source_query: Mapped[str | None] = mapped_column(String, nullable=True)
    extraction_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    score_reason: Mapped[str | None] = mapped_column(String, nullable=True)
    judge_model: Mapped[str | None] = mapped_column(String, nullable=True)
    judge_version: Mapped[str | None] = mapped_column(String(16), nullable=True)
    criteria_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(8), nullable=False)
    decided_by: Mapped[str | None] = mapped_column(String(4), nullable=True)
    run_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("runs.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow)


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    events_found: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    events_new: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    trigger: Mapped[str] = mapped_column(String, nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    stage_counts: Mapped[str | None] = mapped_column(Text, nullable=True)
    search_calls: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0", default=0)
    llm_calls: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0", default=0)
    llm_tokens_in: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0", default=0)
    llm_tokens_out: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0", default=0)
    cost_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    stopped_at_stage: Mapped[str | None] = mapped_column(String(16), nullable=True)
    error_detail: Mapped[str | None] = mapped_column(Text, nullable=True)
