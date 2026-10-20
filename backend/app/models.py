"""Pydantic models matching openapi.yaml schemas."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EventStatus(str, Enum):
    new = "new"
    accepted = "accepted"
    rejected = "rejected"
    queued = "queued"


class Criteria(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    text: str
    updated_at: str = Field(default="", alias="updatedAt")
    time_zone: str | None = Field(default=None, alias="timeZone")


class SaveCriteriaRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    text: str = Field(max_length=2000)
    time_zone: str | None = Field(default=None, alias="timeZone")


class Thresholds(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    lower_threshold: int = Field(alias="lowerThreshold")
    upper_threshold: int = Field(alias="upperThreshold")


class SearchResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    run_id: str = Field(alias="runId")
    events_found: int = Field(alias="eventsFound")
    events_new: int = Field(alias="eventsNew")
    stage_counts: dict | None = Field(default=None, alias="stageCounts")
    stopped_at_stage: str | None = Field(default=None, alias="stoppedAtStage")
    error: str | None = Field(default=None)


class DecisionRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    decision: Literal["accepted", "rejected"]


class Event(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    title: str
    date_time: str = Field(alias="dateTime")
    place: str
    link: str
    description: str
    start_tz: str | None = Field(default=None, alias="startTz")
    end_time: str | None = Field(default=None, alias="endTime")
    city: str = Field(default="")
    country: str = Field(default="ZZ")
    source_url: str | None = Field(default=None, alias="sourceUrl")
    band: str | None = Field(default=None)
    score: int
    score_reason: str = Field(alias="scoreReason")
    status: EventStatus
    decided_by: str | None = Field(default=None, alias="decidedBy")


class RegisterRequest(BaseModel):
    username: str = Field(max_length=150)
    password: str = Field(max_length=72)
    registrationCode: str | None = None

    @field_validator("password")
    @classmethod
    def _password_byte_limit(cls, v: str) -> str:
        if len(v.encode("utf-8")) > 72:
            raise ValueError("password must be at most 72 bytes when UTF-8 encoded")
        return v


class LoginRequest(BaseModel):
    username: str = Field(max_length=150)
    password: str = Field(max_length=72)

    @field_validator("password")
    @classmethod
    def _password_byte_limit(cls, v: str) -> str:
        if len(v.encode("utf-8")) > 72:
            raise ValueError("password must be at most 72 bytes when UTF-8 encoded")
        return v


class AuthResponse(BaseModel):
    token: str
    username: str
