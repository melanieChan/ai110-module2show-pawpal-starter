from pawpal_system import CareTask, Pet, Priority, TaskCategory


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
