from datetime import time

import streamlit as st

from pawpal_system import (
    CareTask,
    Owner,
    Pet,
    PlanningConstraints,
    Priority,
    Scheduler,
    TaskCategory,
)

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

st.subheader("Owner & Pet")
owner_name = st.text_input("Owner name", value="Jordan")
pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])

if "owner" not in st.session_state:
    st.session_state.owner = Owner(name=owner_name)

owner: Owner = st.session_state.owner
owner.name = owner_name

pet = next((p for p in owner.pets if p.name == pet_name), None)
if pet is None:
    pet = Pet(name=pet_name, species=species)
    owner.pets.append(pet)
else:
    pet.species = species

st.markdown("### Tasks")
st.caption("Add a few tasks for this pet. They feed directly into the scheduler below.")

col1, col2, col3 = st.columns(3)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    priority_choice = st.selectbox("Priority", ["low", "medium", "high"], index=2)

col4, col5, col6 = st.columns(3)
with col4:
    category_choice = st.selectbox(
        "Category", [c.value for c in TaskCategory], index=0
    )
with col5:
    has_fixed_time = st.checkbox("Fixed time?")
    fixed_time_value = st.time_input("Fixed time", value=time(8, 0), disabled=not has_fixed_time)
with col6:
    recurrence_choice = st.selectbox("Recurrence", ["none", "daily", "weekly"])

if st.button("Add task"):
    task = CareTask(
        title=task_title,
        category=TaskCategory(category_choice),
        duration_minutes=int(duration),
        priority=Priority(priority_choice),
        fixed_time=fixed_time_value if has_fixed_time else None,
        recurrence=None if recurrence_choice == "none" else recurrence_choice,
    )
    pet.add_task(task)

st.markdown("#### Task list")
filter_choice = st.radio("Show", ["All", "Incomplete", "Completed"], horizontal=True)
completed_filter = {"All": None, "Incomplete": False, "Completed": True}[filter_choice]
visible_tasks = owner.filter_tasks(completed=completed_filter, pet_name=pet.name)
visible_tasks = owner.sort_tasks_by_time(visible_tasks)

if visible_tasks:
    for t in visible_tasks:
        row = st.columns([2, 2, 2, 2, 2, 2, 3])
        row[0].write(t.title)
        row[1].write(t.category.value)
        row[2].write(f"{t.duration_minutes} min")
        row[3].write(t.priority.value)
        row[4].write(t.fixed_time.strftime("%H:%M") if t.fixed_time else "-")
        row[5].write(t.recurrence or "-")
        if t.completed:
            row[6].write("✅ done")
        else:
            if row[6].button("Complete", key=f"complete_{id(t)}", use_container_width=True):
                t.mark_complete()
                st.rerun()
else:
    st.info("No tasks match this filter.")

st.divider()

st.subheader("Blocked Time Windows")
st.caption("Time ranges the scheduler must avoid, e.g. a lunch break.")

if "blocked_windows" not in st.session_state:
    st.session_state.blocked_windows = []

col_b1, col_b2 = st.columns(2)
with col_b1:
    block_start = st.time_input("Blocked start", value=time(12, 0), key="block_start")
with col_b2:
    block_end = st.time_input("Blocked end", value=time(13, 0), key="block_end")
if st.button("Add blocked window", use_container_width=True):
    st.session_state.blocked_windows.append((block_start, block_end))

if st.session_state.blocked_windows:
    for i, (b_start, b_end) in enumerate(st.session_state.blocked_windows):
        bcol1, bcol2 = st.columns([3, 1])
        bcol1.write(f"{b_start.strftime('%H:%M')} - {b_end.strftime('%H:%M')}")
        if bcol2.button("Remove", key=f"remove_block_{i}", use_container_width=True):
            st.session_state.blocked_windows.pop(i)
            st.rerun()
else:
    st.caption("No blocked windows set.")

st.divider()

st.subheader("Build Schedule")
st.caption("Choose the planning window, then build today's schedule from the tasks above.")

col6, col7 = st.columns(2)
with col6:
    day_start = st.time_input("Day start", value=time(7, 0))
with col7:
    day_end = st.time_input("Day end", value=time(21, 0))

if st.button("Generate schedule"):
    constraints = PlanningConstraints(
        day_start=day_start,
        day_end=day_end,
        blocked_windows=list(st.session_state.blocked_windows),
    )
    scheduler = Scheduler()

    conflicts = scheduler.detect_conflicts(owner)
    for warning in conflicts:
        st.warning(warning)

    plan = scheduler.build_plan(owner, constraints)
    st.caption(plan.summary())
    st.text(plan.explain())
