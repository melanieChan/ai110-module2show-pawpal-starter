from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, time
from enum import Enum
from typing import Optional


class TaskCategory(Enum):
    WALK = "walk"
    FEEDING = "feeding"
    MEDS = "meds"
    ENRICHMENT = "enrichment"
    GROOMING = "grooming"
    OTHER = "other"


class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class CareTask:
    title: str
    category: TaskCategory
    duration_minutes: int
    priority: Priority
    fixed_time: Optional[time] = None
    recurrence: Optional[str] = None


@dataclass
class Pet:
    name: str
    species: str
    notes: str = ""
    tasks: list[CareTask] = field(default_factory=list)


@dataclass
class Owner:
    name: str
    pets: list[Pet] = field(default_factory=list)


@dataclass
class PlanningConstraints:
    day_start: time
    day_end: time
    blocked_windows: list[tuple[time, time]] = field(default_factory=list)


@dataclass
class ScheduledTask:
    task: CareTask
    start_time: time
    end_time: time
    reason: str = ""


@dataclass
class DailyPlan:
    plan_date: date
    pet: Pet
    scheduled: list[ScheduledTask] = field(default_factory=list)
    skipped: list[tuple[CareTask, str]] = field(default_factory=list)

    def summary(self) -> str:
        raise NotImplementedError

    def explain(self) -> str:
        raise NotImplementedError


class Scheduler:
    """Stateless scheduling service: builds a DailyPlan from a Pet's tasks and constraints."""

    def build_plan(self, pet: Pet, constraints: PlanningConstraints) -> DailyPlan:
        raise NotImplementedError

    def _sort_tasks(self, tasks: list[CareTask]) -> list[CareTask]:
        raise NotImplementedError

    def _fits(self, task: CareTask, remaining_minutes: int) -> bool:
        raise NotImplementedError
