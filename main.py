from datetime import time

from pawpal_system import (
    CareTask,
    Owner,
    Pet,
    PlanningConstraints,
    Priority,
    Scheduler,
    TaskCategory,
)

mochi = Pet(name="Mochi", species="dog", notes="allergic to chicken")
mochi.tasks = [
    CareTask("Give meds", TaskCategory.MEDS, 10, Priority.HIGH, fixed_time=time(8, 0)),
    CareTask("Evening brush", TaskCategory.GROOMING, 15, Priority.LOW),
    CareTask("Morning walk", TaskCategory.WALK, 30, Priority.HIGH, fixed_time=time(7, 0)),
    # Same pet, overlaps with "Morning walk" (7:00-7:30).
    CareTask("Teeth brushing", TaskCategory.GROOMING, 10, Priority.MEDIUM, fixed_time=time(7, 10)),
]

whiskers = Pet(name="Whiskers", species="cat")
whiskers.tasks = [
    CareTask("Grooming", TaskCategory.GROOMING, 20, Priority.LOW),
    CareTask("Feeding", TaskCategory.FEEDING, 10, Priority.HIGH, fixed_time=time(7, 30)),
    # Different pet, overlaps with Mochi's "Morning walk" (7:00-7:30).
    CareTask("Vet checkup", TaskCategory.OTHER, 20, Priority.HIGH, fixed_time=time(7, 0)),
]

owner = Owner(name="Alice", pets=[mochi, whiskers])

print("Conflict Check")
print("=" * 40)
conflicts = Scheduler().detect_conflicts(owner)
if conflicts:
    for warning in conflicts:
        print(warning)
else:
    print("No conflicts detected.")

# Mark a couple of tasks complete so filtering has something to show.
mochi.tasks[0].mark_complete()
whiskers.tasks[1].mark_complete()

constraints = PlanningConstraints(day_start=time(7, 0), day_end=time(9, 0))

plan = Scheduler().build_plan(owner, constraints)

print()
print("Today's Schedule")
print("=" * 40)
print(plan.explain())


def _describe(task: CareTask) -> str:
    pet_name = task.pet.name if task.pet else "?"
    when = task.fixed_time.strftime("%H:%M") if task.fixed_time else "no fixed time"
    status = "done" if task.completed else "pending"
    return f"  [{pet_name}] {task.title} ({when}, {task.priority.value}, {status})"


print()
print("All tasks sorted by time")
print("=" * 40)
for task in owner.sort_tasks_by_time():
    print(_describe(task))

print()
print("Incomplete tasks only")
print("=" * 40)
for task in owner.filter_tasks(completed=False):
    print(_describe(task))

print()
print("Mochi's tasks, sorted by time")
print("=" * 40)
mochi_tasks = owner.filter_tasks(pet_name="Mochi")
for task in owner.sort_tasks_by_time(mochi_tasks):
    print(_describe(task))
