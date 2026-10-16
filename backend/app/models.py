"""Pydantic models matching openapi.yaml schemas."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class EventStatus(str, Enum):
    new = "new"
    accepted = "accepted"
    rejected = "rejected"
    queued = "queued"


class Criteria(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    text: str
    updated_at: str = Field(default="", alias="updatedAt")


class SaveCriteriaRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    text: str


class Thresholds(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    lower_threshold: int = Field(alias="lowerThreshold")
    upper_threshold: int = Field(alias="upperThreshold")


class SearchResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    run_id: str = Field(alias="runId")
    events_found: int = Field(alias="eventsFound")
    events_new: int = Field(alias="eventsNew")


class DecisionRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    decision: str


class Event(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    title: str
    date_time: str = Field(alias="dateTime")
    place: str
    link: str
    description: str
    score: int
    score_reason: str = Field(alias="scoreReason")
    status: EventStatus
