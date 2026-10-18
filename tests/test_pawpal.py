from datetime import time

from pawpal_system import CareTask, Owner, Pet, Priority, Scheduler, TaskCategory


def test_mark_complete_changes_task_status():
    task = CareTask("Morning walk", TaskCategory.WALK, 30, Priority.HIGH)
    assert task.completed is False

    task.mark_complete()

    assert task.completed is True


def test_adding_task_increases_pet_task_count():
    pet = Pet(name="Mochi", species="dog")
    assert len(pet.tasks) == 0

    pet.add_task(CareTask("Feeding", TaskCategory.FEEDING, 10, Priority.HIGH))

    assert len(pet.tasks) == 1


def _owner_with_two_pets():
    mochi = Pet(name="Mochi", species="dog")
    walk = CareTask("Morning walk", TaskCategory.WALK, 30, Priority.HIGH)
    walk.mark_complete()
    mochi.add_task(walk)
    mochi.add_task(CareTask("Feeding", TaskCategory.FEEDING, 10, Priority.HIGH))

    whiskers = Pet(name="Whiskers", species="cat")
    whiskers.add_task(CareTask("Litter box", TaskCategory.OTHER, 5, Priority.MEDIUM))

    return Owner(name="Jordan", pets=[mochi, whiskers])


def test_filter_tasks_by_completion_status():
    owner = _owner_with_two_pets()

    completed = owner.filter_tasks(completed=True)
    incomplete = owner.filter_tasks(completed=False)

    assert [t.title for t in completed] == ["Morning walk"]
    assert {t.title for t in incomplete} == {"Feeding", "Litter box"}


def test_filter_tasks_by_pet_name():
    owner = _owner_with_two_pets()

    mochi_tasks = owner.filter_tasks(pet_name="Mochi")

    assert {t.title for t in mochi_tasks} == {"Morning walk", "Feeding"}


def test_filter_tasks_by_completion_status_and_pet_name():
    owner = _owner_with_two_pets()

    tasks = owner.filter_tasks(completed=False, pet_name="Mochi")

    assert [t.title for t in tasks] == ["Feeding"]


def test_filter_tasks_with_no_filters_returns_everything():
    owner = _owner_with_two_pets()

    assert len(owner.filter_tasks()) == 3


def test_mark_complete_spawns_next_occurrence_for_daily_task():
    pet = Pet(name="Mochi", species="dog")
    task = CareTask("Morning walk", TaskCategory.WALK, 30, Priority.HIGH, recurrence="daily")
    pet.add_task(task)

    task.mark_complete()

    assert len(pet.tasks) == 2
    next_task = pet.tasks[1]
    assert next_task is not task
    assert next_task.completed is False
    assert next_task.title == "Morning walk"
    assert next_task.recurrence == "daily"
    assert next_task.pet is pet


def test_mark_complete_spawns_next_occurrence_for_weekly_task():
    pet = Pet(name="Mochi", species="dog")
    task = CareTask("Nail trim", TaskCategory.GROOMING, 15, Priority.LOW, recurrence="weekly")
    pet.add_task(task)

    task.mark_complete()

    assert len(pet.tasks) == 2
    assert pet.tasks[1].recurrence == "weekly"
    assert pet.tasks[1].completed is False


def test_mark_complete_does_not_spawn_for_non_recurring_task():
    pet = Pet(name="Mochi", species="dog")
    task = CareTask("One-off vet visit", TaskCategory.OTHER, 60, Priority.MEDIUM)
    pet.add_task(task)

    task.mark_complete()

    assert len(pet.tasks) == 1


def test_mark_complete_without_pet_does_not_error():
    task = CareTask("Morning walk", TaskCategory.WALK, 30, Priority.HIGH, recurrence="daily")

    task.mark_complete()

    assert task.completed is True


def test_mark_complete_does_not_spawn_for_unsupported_recurrence_value():
    pet = Pet(name="Mochi", species="dog")
    task = CareTask(
        "Vet checkup", TaskCategory.OTHER, 45, Priority.MEDIUM, recurrence="monthly"
    )
    pet.add_task(task)

    task.mark_complete()

    assert len(pet.tasks) == 1


def test_mark_complete_called_twice_does_not_spawn_duplicate_occurrence():
    pet = Pet(name="Mochi", species="dog")
    task = CareTask("Morning walk", TaskCategory.WALK, 30, Priority.HIGH, recurrence="daily")
    pet.add_task(task)

    task.mark_complete()
    task.mark_complete()

    assert len(pet.tasks) == 2
    assert task.completed is True


def test_detect_conflicts_flags_overlap_for_different_pets():
    mochi = Pet(name="Mochi", species="dog")
    mochi.add_task(CareTask("Walk", TaskCategory.WALK, 30, Priority.HIGH, fixed_time=time(8, 0)))

    whiskers = Pet(name="Whiskers", species="cat")
    whiskers.add_task(CareTask("Feeding", TaskCategory.FEEDING, 15, Priority.HIGH, fixed_time=time(8, 15)))

    owner = Owner(name="Alice", pets=[mochi, whiskers])

    warnings = Scheduler().detect_conflicts(owner)

    assert len(warnings) == 1
    assert "Walk" in warnings[0] and "Feeding" in warnings[0]


def test_detect_conflicts_flags_overlap_for_same_pet():
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(CareTask("Walk", TaskCategory.WALK, 30, Priority.HIGH, fixed_time=time(8, 0)))
    pet.add_task(CareTask("Meds", TaskCategory.MEDS, 10, Priority.HIGH, fixed_time=time(8, 10)))

    owner = Owner(name="Alice", pets=[pet])

    warnings = Scheduler().detect_conflicts(owner)

    assert len(warnings) == 1


def test_detect_conflicts_ignores_non_overlapping_and_flexible_tasks():
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(CareTask("Walk", TaskCategory.WALK, 30, Priority.HIGH, fixed_time=time(8, 0)))
    pet.add_task(CareTask("Meds", TaskCategory.MEDS, 10, Priority.HIGH, fixed_time=time(9, 0)))
    pet.add_task(CareTask("Playtime", TaskCategory.ENRICHMENT, 15, Priority.LOW))

    owner = Owner(name="Alice", pets=[pet])

    warnings = Scheduler().detect_conflicts(owner)

    assert warnings == []


def test_detect_conflicts_does_not_raise():
    owner = Owner(name="Alice", pets=[])

    warnings = Scheduler().detect_conflicts(owner)

    assert warnings == []
