from __future__ import annotations

import heapq
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
    pet: Optional[Pet] = None
    completed: bool = False

    def mark_complete(self) -> None:
        """Mark this task as completed. If it recurs daily/weekly, spawn the next occurrence on the same pet."""
        self.completed = True
        if self.pet is not None and self.recurrence in ("daily", "weekly"):
            self.pet.add_task(
                CareTask(
                    title=self.title,
                    category=self.category,
                    duration_minutes=self.duration_minutes,
                    priority=self.priority,
                    fixed_time=self.fixed_time,
                    recurrence=self.recurrence,
                )
            )


@dataclass
class Pet:
    name: str
    species: str
    notes: str = ""
    tasks: list[CareTask] = field(default_factory=list)

    def add_task(self, task: CareTask) -> None:
        """Add a task to this pet, linking the task back to it."""
        task.pet = self
        self.tasks.append(task)


@dataclass
class Owner:
    name: str
    pets: list[Pet] = field(default_factory=list)

    def get_all_tasks(self) -> list[CareTask]:
        """Return every task across all of this owner's pets, in one flat list."""
        all_tasks = []
        for pet in self.pets:
            for task in pet.tasks:
                task.pet = pet
                all_tasks.append(task)
        return all_tasks

    def filter_tasks(
        self,
        completed: Optional[bool] = None,
        pet_name: Optional[str] = None,
    ) -> list[CareTask]:
        """Return all tasks across pets, optionally narrowed by completion status and/or pet name."""
        tasks = self.get_all_tasks()
        if completed is not None:
            tasks = [t for t in tasks if t.completed == completed]
        if pet_name is not None:
            tasks = [t for t in tasks if t.pet is not None and t.pet.name == pet_name]
        return tasks

    def sort_tasks_by_time(self, tasks: Optional[list[CareTask]] = None) -> list[CareTask]:
        """Sort tasks by fixed_time ascending; tasks with no fixed time sort last."""
        tasks = self.get_all_tasks() if tasks is None else tasks
        return sorted(tasks, key=lambda t: (t.fixed_time is None, t.fixed_time or time.min))


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
    owner: Owner
    scheduled: list[ScheduledTask] = field(default_factory=list)
    skipped: list[tuple[CareTask, str]] = field(default_factory=list)

    def summary(self) -> str:
        """Return a one-line overview of how many tasks were scheduled vs. skipped."""
        total_minutes = sum(st.task.duration_minutes for st in self.scheduled)
        return (
            f"{self.owner.name}'s plan for {self.plan_date.isoformat()}: "
            f"{len(self.scheduled)} task(s) scheduled ({total_minutes} min), "
            f"{len(self.skipped)} skipped."
        )

    def explain(self) -> str:
        """Return the full plan with each scheduled/skipped task and the reason behind it."""
        lines = [self.summary(), ""]
        if self.scheduled:
            lines.append("Scheduled:")
            for st in self.scheduled:
                pet_name = st.task.pet.name if st.task.pet else "?"
                lines.append(
                    f"  {st.start_time.strftime('%H:%M')}-{st.end_time.strftime('%H:%M')} "
                    f"[{pet_name}] {st.task.title} [{st.task.priority.value}] - {st.reason}"
                )
        if self.skipped:
            lines.append("Skipped:")
            for task, reason in self.skipped:
                pet_name = task.pet.name if task.pet else "?"
                lines.append(f"  [{pet_name}] {task.title} [{task.priority.value}] - {reason}")
        return "\n".join(lines)


_PRIORITY_ORDER = {Priority.HIGH: 0, Priority.MEDIUM: 1, Priority.LOW: 2}


def _time_to_minutes(t: time) -> int:
    """Convert a time-of-day to minutes since midnight."""
    return t.hour * 60 + t.minute


def _minutes_to_time(minutes: int) -> time:
    """Convert minutes since midnight back to a time-of-day."""
    minutes %= 24 * 60
    return time(hour=minutes // 60, minute=minutes % 60)


def _intervals_overlap(a_start: int, a_end: int, b_start: int, b_end: int) -> bool:
    """Return whether two [start, end) minute ranges overlap."""
    return a_start < b_end and b_start < a_end


def _overlaps_any(start: int, end: int, sorted_intervals: list[tuple[int, int]]) -> bool:
    """Check [start, end) against intervals sorted by start, stopping once intervals start past end."""
    for b_start, b_end in sorted_intervals:
        if b_start >= end:
            break
        if _intervals_overlap(start, end, b_start, b_end):
            return True
    return False


class Scheduler:
    """Stateless scheduling service: builds a DailyPlan from an Owner's tasks and constraints."""

    def build_plan(
        self,
        owner: Owner,
        constraints: PlanningConstraints,
        plan_date: Optional[date] = None,
    ) -> DailyPlan:
        """Build a DailyPlan by placing fixed-time tasks, then filling gaps by priority."""
        plan = DailyPlan(plan_date=plan_date or date.today(), owner=owner)

        all_tasks = owner.get_all_tasks()

        day_start = _time_to_minutes(constraints.day_start)
        day_end = _time_to_minutes(constraints.day_end)
        blocked: list[tuple[int, int]] = sorted(
            (_time_to_minutes(start), _time_to_minutes(end))
            for start, end in constraints.blocked_windows
        )

        fixed_tasks = sorted(
            (t for t in all_tasks if t.fixed_time is not None),
            key=lambda t: _time_to_minutes(t.fixed_time),
        )
        flexible_tasks = self._sort_tasks(
            [t for t in all_tasks if t.fixed_time is None]
        )

        # Place fixed-time tasks first; they must happen at a specific time or not at all.
        confirmed_fixed: list[tuple[int, int]] = []
        for task in fixed_tasks:
            start = _time_to_minutes(task.fixed_time)
            end = start + task.duration_minutes
            if start < day_start or end > day_end:
                plan.skipped.append((task, "fixed time falls outside the planning window"))
                continue
            if _overlaps_any(start, end, blocked) or _overlaps_any(start, end, confirmed_fixed):
                plan.skipped.append(
                    (task, "fixed time conflicts with a blocked window or another task")
                )
                continue
            plan.scheduled.append(
                ScheduledTask(
                    task=task,
                    start_time=_minutes_to_time(start),
                    end_time=_minutes_to_time(end),
                    reason=(
                        f"Fixed-time task ({task.priority.value} priority) "
                        f"locked at {task.fixed_time.strftime('%H:%M')}."
                    ),
                )
            )
            confirmed_fixed.append((start, end))

        # merge sorted lists
        # confirmed_fixed is already sorted since fixed_tasks is sorted and we only ever append to it in that same order.
        busy = list(heapq.merge(blocked, confirmed_fixed))

        # Compute the free gaps left in the day once blocked windows and fixed tasks are placed.
        gaps: list[tuple[int, int]] = []
        cursor = day_start
        for b_start, b_end in busy:
            if b_start > cursor:
                gaps.append((cursor, b_start))
            cursor = max(cursor, b_end)
        if cursor < day_end:
            gaps.append((cursor, day_end))

        # Greedily fill each gap with the highest-priority flexible tasks that fit.
        remaining_tasks = list(flexible_tasks)
        for gap_start, gap_end in gaps:
            gap_cursor = gap_start
            still_remaining = []
            for task in remaining_tasks:
                gap_left = gap_end - gap_cursor
                if self._fits(task, gap_left):
                    start = gap_cursor
                    end = start + task.duration_minutes
                    plan.scheduled.append(
                        ScheduledTask(
                            task=task,
                            start_time=_minutes_to_time(start),
                            end_time=_minutes_to_time(end),
                            reason=(
                                f"{task.priority.value.title()} priority task placed at "
                                f"{_minutes_to_time(start).strftime('%H:%M')} in available time."
                            ),
                        )
                    )
                    gap_cursor = end
                else:
                    still_remaining.append(task)
            remaining_tasks = still_remaining

        for task in remaining_tasks:
            plan.skipped.append((task, "not enough time remaining in the day"))

        plan.scheduled.sort(key=lambda st: _time_to_minutes(st.start_time))
        return plan

    def _sort_tasks(self, tasks: list[CareTask]) -> list[CareTask]:
        """Sort tasks by priority (high first), then by shortest duration."""
        return sorted(tasks, key=lambda t: (_PRIORITY_ORDER[t.priority], t.duration_minutes))

    def _fits(self, task: CareTask, remaining_minutes: int) -> bool:
        """Return whether a task's duration fits within the remaining time."""
        return task.duration_minutes <= remaining_minutes
