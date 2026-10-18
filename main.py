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
    CareTask("Morning walk", TaskCategory.WALK, 30, Priority.HIGH, fixed_time=time(7, 0)),
    CareTask("Give meds", TaskCategory.MEDS, 10, Priority.HIGH, fixed_time=time(8, 0)),
]

whiskers = Pet(name="Whiskers", species="cat")
whiskers.tasks = [
    CareTask("Feeding", TaskCategory.FEEDING, 10, Priority.HIGH, fixed_time=time(7, 30)),
    CareTask("Grooming", TaskCategory.GROOMING, 20, Priority.LOW),
]

owner = Owner(name="Alice", pets=[mochi, whiskers])

constraints = PlanningConstraints(day_start=time(7, 0), day_end=time(9, 0))

plan = Scheduler().build_plan(owner, constraints)

print("Today's Schedule")
print("=" * 40)
print(plan.explain())
