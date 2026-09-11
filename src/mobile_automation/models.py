from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ActionStatus(StrEnum):
    COMPLETED = "completed"
    UNAVAILABLE = "unavailable"
    FAILED = "failed"


@dataclass(frozen=True)
class ActionResult:
    status: ActionStatus
    detail: str
    attempts: int
    evidence: dict[str, Any] = field(default_factory=dict)
