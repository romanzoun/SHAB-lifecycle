from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Event:
    publication_id: str
    published_at: str
    event_type: str
    rule_id: str
    org_uid: str | None = None
    person_key: str | None = None
    plz: str | None = None
    canton: str | None = None
    role: str | None = None
    signing: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class ParseResult:
    publication_id: str
    published_at: str
    language: str | None
    sub_rubric: str | None
    org_uid: str | None
    canton: str | None
    plz: str | None
    events: list[Event]
    leftover_text: str
    status: str  # FULLY_PARSED | PARTIALLY_PARSED | DEFERRED | ERROR | INVALID_SOURCE
