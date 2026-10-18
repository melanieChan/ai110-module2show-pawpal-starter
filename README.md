# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## 🧩 Implementation Summary

The logic layer lives in `pawpal_system.py` as plain Python dataclasses, kept separate from the Streamlit UI so the scheduling logic can be tested on its own (see `tests/test_pawpal.py` and `main.py`).

**Data model:**
- `Owner` holds a list of `Pet`s and exposes `get_all_tasks()`, which flattens every pet's tasks into one list (and tags each task with a back-reference to its `Pet`).
- `Pet` holds basic info (`name`, `species`, `notes`) and a list of `CareTask`s, added via `add_task()`.
- `CareTask` represents one piece of care (walk, feeding, meds, enrichment, grooming), with a `duration_minutes`, a `priority` (`LOW`/`MEDIUM`/`HIGH`), an optional `fixed_time` for things that must happen at a specific hour (like meds), and `mark_complete()` to track status.
- `PlanningConstraints` describes the planning window (`day_start`, `day_end`) and any `blocked_windows` (e.g. the owner is out at work).

**Scheduling:**
- `Scheduler.build_plan(owner, constraints)` is the entry point. It pulls every task across all of the owner's pets via `get_all_tasks()`, then:
  1. Places `fixed_time` tasks first, skipping any that fall outside the day or collide with a blocked window or each other.
  2. Computes the free time gaps left in the day.
  3. Sorts the remaining flexible tasks by priority (then shortest duration first) and greedily fills each gap, so higher-priority tasks get scheduled before lower-priority ones run out of room.
  4. Anything that doesn't fit anywhere ends up in `skipped`, with a reason.
- The result is a `DailyPlan`, made up of `ScheduledTask`s (task + start/end time + a plain-language reason it was placed there) and `skipped` tasks. `DailyPlan.summary()` gives a one-line overview, and `explain()` prints the full breakdown per pet, which is what powers "Today's Schedule" in `main.py` and the planned Streamlit output.

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

```
Today's Schedule
========================================
Alice's plan for 2026-10-17: 4 task(s) scheduled (70 min), 0 skipped.

Scheduled:
  07:00-07:30 [Mochi] Morning walk [high] - Fixed-time task (high priority) locked at 07:00.
  07:30-07:40 [Whiskers] Feeding [high] - Fixed-time task (high priority) locked at 07:30.
  07:40-08:00 [Whiskers] Grooming [low] - Low priority task placed at 07:40 in available time.
  08:00-08:10 [Mochi] Give meds [high] - Fixed-time task (high priority) locked at 08:00.#   ...
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
# Paste your pytest output here
```

## 📐 Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Owner.sort_tasks_by_time()` | Sorts a list of `CareTask`s (defaults to `get_all_tasks()`) by `fixed_time` ascending; tasks with no fixed time sort last. Separate from `Scheduler._sort_tasks()`, which orders *unscheduled flexible* tasks by priority then shortest duration while filling gaps. |
| Filtering | `Owner.filter_tasks(completed=None, pet_name=None)` | Returns tasks across all pets, optionally narrowed by completion status, pet name, or both. Composable with sorting, e.g. `owner.sort_tasks_by_time(owner.filter_tasks(completed=False))`. |
| Conflict handling | `Scheduler.detect_conflicts(owner)` | Lightweight check that sweeps all fixed-time tasks (sorted by start time) and returns a list of human-readable warning strings for any pair that overlaps — same pet or different pets. Never raises or modifies the schedule; it's purely advisory and independent of `build_plan()`, which separately resolves fixed-time conflicts by skipping the later task. |
| Recurring tasks | `CareTask.mark_complete()` | When a task's `recurrence` is `"daily"` or `"weekly"` and it's attached to a `Pet`, completing it automatically creates a fresh, incomplete clone (same title/category/duration/priority/fixed_time/recurrence) via `pet.add_task()`, so the next occurrence is ready to be scheduled. The completed task stays in place as a history record. |

See `main.py` for a runnable demo of all four: it adds tasks out of order and with overlapping fixed times, then prints the conflict warnings, the schedule, and the sorted/filtered task views.

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
