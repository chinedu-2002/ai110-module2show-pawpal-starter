"""PawPal+ Streamlit UI — connected to the backend logic layer."""

import streamlit as st
from datetime import date
from pawpal_system import Task, Pet, Owner, Scheduler

# ── Page config ──────────────────────────────────────────────
st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")
st.caption("Smart pet care management — track tasks, detect conflicts, and stay organized.")

# ── Session state initialization ─────────────────────────────
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan")
    st.session_state.scheduler = Scheduler(st.session_state.owner)

owner: Owner = st.session_state.owner
scheduler: Scheduler = st.session_state.scheduler

# ── Sidebar: Owner + Pet management ──────────────────────────
with st.sidebar:
    st.header("Owner Info")
    new_name = st.text_input("Owner name", value=owner.name)
    if new_name != owner.name:
        owner.name = new_name

    st.divider()
    st.header("Add a Pet")
    with st.form("add_pet_form", clear_on_submit=True):
        pet_name = st.text_input("Pet name")
        species = st.selectbox("Species", ["dog", "cat", "bird", "rabbit", "other"])
        age = st.number_input("Age", min_value=0, max_value=30, value=1)
        add_pet = st.form_submit_button("Add Pet")
        if add_pet and pet_name:
            if owner.get_pet(pet_name):
                st.warning(f"A pet named '{pet_name}' already exists.")
            else:
                owner.add_pet(Pet(name=pet_name, species=species, age=age))
                st.success(f"Added {pet_name}!")

    if owner.pets:
        st.divider()
        st.header("Your Pets")
        for pet in owner.pets:
            st.markdown(f"**{pet.name}** ({pet.species}, age {pet.age})")

# ── Main area: check if pets exist ───────────────────────────
if not owner.pets:
    st.info("Add at least one pet using the sidebar to get started.")
    st.stop()

# ── Add a Task ───────────────────────────────────────────────
st.subheader("Add a Task")

pet_names = [p.name for p in owner.pets]

with st.form("add_task_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        task_desc = st.text_input("Task description", placeholder="Morning walk")
        task_time = st.text_input("Time (HH:MM)", placeholder="08:00")
        target_pet = st.selectbox("Pet", pet_names)
    with col2:
        priority = st.selectbox("Priority", ["high", "medium", "low"])
        frequency = st.selectbox("Frequency", ["once", "daily", "weekly"])
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=15)

    add_task = st.form_submit_button("Add Task")
    if add_task and task_desc and task_time:
        pet = owner.get_pet(target_pet)
        if pet:
            new_task = Task(
                description=task_desc,
                time=task_time,
                frequency=frequency,
                priority=priority,
                duration_minutes=int(duration),
                due_date=date.today(),
            )
            pet.add_task(new_task)
            st.success(f"Added '{task_desc}' for {target_pet} at {task_time}.")

# ── Conflict Warnings ────────────────────────────────────────
conflicts = scheduler.detect_conflicts()
if conflicts:
    for warning in conflicts:
        st.warning(f"⚠ {warning}")

# ── Today's Schedule ─────────────────────────────────────────
st.divider()
st.subheader("Today's Schedule")

col_filter1, col_filter2 = st.columns(2)
with col_filter1:
    filter_pet = st.selectbox("Filter by pet", ["All"] + pet_names, key="filter_pet")
with col_filter2:
    filter_status = st.selectbox("Filter by status", ["All", "Pending", "Completed"], key="filter_status")

schedule = scheduler.get_daily_schedule()

# Apply filters
if filter_pet != "All":
    schedule = scheduler.filter_by_pet(filter_pet, schedule)
if filter_status == "Pending":
    schedule = scheduler.filter_by_status(False, schedule)
elif filter_status == "Completed":
    schedule = scheduler.filter_by_status(True, schedule)

if not schedule:
    st.info("No tasks match your filters for today.")
else:
    for i, task in enumerate(schedule):
        col_a, col_b, col_c = st.columns([4, 1, 1])
        with col_a:
            status_icon = "✅" if task.completed else "⏳"
            st.markdown(
                f"{status_icon} **{task.time}** — {task.description} "
                f"(*{task.pet_name}*, {task.priority} priority, {task.duration_minutes}min, {task.frequency})"
            )
        with col_b:
            if not task.completed:
                if st.button("Complete", key=f"complete_{id(task)}"):
                    new_task = scheduler.mark_task_complete(task)
                    if new_task:
                        st.toast(f"Next '{task.description}' scheduled for {new_task.due_date}")
                    st.rerun()
        with col_c:
            if st.button("Remove", key=f"remove_{id(task)}"):
                pet = owner.get_pet(task.pet_name)
                if pet:
                    pet.remove_task(task.description)
                st.rerun()

# ── Summary ──────────────────────────────────────────────────
st.divider()
all_tasks = owner.get_all_tasks()
total = len(all_tasks)
done = len([t for t in all_tasks if t.completed])
pending = total - done

col_s1, col_s2, col_s3 = st.columns(3)
col_s1.metric("Total Tasks", total)
col_s2.metric("Completed", done)
col_s3.metric("Pending", pending)
