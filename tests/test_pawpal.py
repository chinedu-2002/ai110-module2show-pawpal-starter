"""Automated test suite for PawPal+ system."""

import pytest
from datetime import date, timedelta
from pawpal_system import Task, Pet, Owner, Scheduler


# ── Task Tests ───────────────────────────────────────────────


class TestTask:
    def test_mark_complete_changes_status(self):
        task = Task("Walk", "08:00")
        assert task.completed is False
        task.mark_complete()
        assert task.completed is True

    def test_default_due_date_is_today(self):
        task = Task("Feed", "09:00")
        assert task.due_date == date.today()

    def test_custom_due_date(self):
        d = date(2026, 4, 1)
        task = Task("Vet visit", "10:00", due_date=d)
        assert task.due_date == d

    def test_default_values(self):
        task = Task("Brush", "11:00")
        assert task.frequency == "once"
        assert task.priority == "medium"
        assert task.duration_minutes == 15
        assert task.completed is False

    def test_str_pending(self):
        task = Task("Walk", "08:00", priority="high", duration_minutes=30)
        assert "Pending" in str(task)
        assert "Walk" in str(task)

    def test_str_done(self):
        task = Task("Walk", "08:00")
        task.mark_complete()
        assert "Done" in str(task)


# ── Pet Tests ────────────────────────────────────────────────


class TestPet:
    def test_add_task_increases_count(self):
        pet = Pet("Mochi", "dog")
        assert len(pet.tasks) == 0
        pet.add_task(Task("Walk", "08:00"))
        assert len(pet.tasks) == 1
        pet.add_task(Task("Feed", "12:00"))
        assert len(pet.tasks) == 2

    def test_add_task_sets_pet_name(self):
        pet = Pet("Mochi", "dog")
        task = Task("Walk", "08:00")
        pet.add_task(task)
        assert task.pet_name == "Mochi"

    def test_remove_task(self):
        pet = Pet("Mochi", "dog")
        pet.add_task(Task("Walk", "08:00"))
        assert pet.remove_task("Walk") is True
        assert len(pet.tasks) == 0

    def test_remove_task_not_found(self):
        pet = Pet("Mochi", "dog")
        assert pet.remove_task("Nonexistent") is False

    def test_get_pending_tasks(self):
        pet = Pet("Mochi", "dog")
        t1 = Task("Walk", "08:00")
        t2 = Task("Feed", "12:00")
        pet.add_task(t1)
        pet.add_task(t2)
        t1.mark_complete()
        pending = pet.get_pending_tasks()
        assert len(pending) == 1
        assert pending[0].description == "Feed"

    def test_pet_with_no_tasks(self):
        pet = Pet("Mochi", "dog")
        assert pet.get_pending_tasks() == []
        assert len(pet.tasks) == 0


# ── Owner Tests ──────────────────────────────────────────────


class TestOwner:
    def test_add_pet(self):
        owner = Owner("Jordan")
        owner.add_pet(Pet("Mochi", "dog"))
        assert len(owner.pets) == 1

    def test_remove_pet(self):
        owner = Owner("Jordan")
        owner.add_pet(Pet("Mochi", "dog"))
        assert owner.remove_pet("Mochi") is True
        assert len(owner.pets) == 0

    def test_remove_pet_not_found(self):
        owner = Owner("Jordan")
        assert owner.remove_pet("Ghost") is False

    def test_get_pet(self):
        owner = Owner("Jordan")
        owner.add_pet(Pet("Mochi", "dog"))
        pet = owner.get_pet("Mochi")
        assert pet is not None
        assert pet.name == "Mochi"

    def test_get_pet_not_found(self):
        owner = Owner("Jordan")
        assert owner.get_pet("Ghost") is None

    def test_get_all_tasks_across_pets(self):
        owner = Owner("Jordan")
        p1 = Pet("Mochi", "dog")
        p2 = Pet("Whiskers", "cat")
        p1.add_task(Task("Walk", "08:00"))
        p2.add_task(Task("Feed", "09:00"))
        p2.add_task(Task("Play", "15:00"))
        owner.add_pet(p1)
        owner.add_pet(p2)
        assert len(owner.get_all_tasks()) == 3


# ── Scheduler Tests ──────────────────────────────────────────


class TestSchedulerSorting:
    def setup_method(self):
        self.owner = Owner("Jordan")
        self.pet = Pet("Mochi", "dog")
        self.owner.add_pet(self.pet)
        # Add tasks out of chronological order
        self.pet.add_task(Task("Evening walk", "18:00", priority="high"))
        self.pet.add_task(Task("Morning walk", "07:30", priority="high"))
        self.pet.add_task(Task("Lunch feed", "12:00", priority="medium"))
        self.pet.add_task(Task("Nap check", "15:00", priority="low"))
        self.scheduler = Scheduler(self.owner)

    def test_sort_by_time_returns_chronological_order(self):
        sorted_tasks = self.scheduler.sort_by_time()
        times = [t.time for t in sorted_tasks]
        assert times == ["07:30", "12:00", "15:00", "18:00"]

    def test_sort_by_priority(self):
        sorted_tasks = self.scheduler.sort_by_priority()
        priorities = [t.priority for t in sorted_tasks]
        # All high tasks first, then medium, then low
        assert priorities == ["high", "high", "medium", "low"]


class TestSchedulerFiltering:
    def setup_method(self):
        self.owner = Owner("Jordan")
        self.mochi = Pet("Mochi", "dog")
        self.whiskers = Pet("Whiskers", "cat")
        self.owner.add_pet(self.mochi)
        self.owner.add_pet(self.whiskers)
        self.mochi.add_task(Task("Walk", "08:00", priority="high"))
        self.mochi.add_task(Task("Feed", "12:00", priority="medium"))
        self.whiskers.add_task(Task("Play", "15:00", priority="low"))
        self.scheduler = Scheduler(self.owner)

    def test_filter_by_pet(self):
        mochi_tasks = self.scheduler.filter_by_pet("Mochi")
        assert len(mochi_tasks) == 2
        assert all(t.pet_name == "Mochi" for t in mochi_tasks)

    def test_filter_by_pet_empty(self):
        result = self.scheduler.filter_by_pet("Ghost")
        assert result == []

    def test_filter_by_status_pending(self):
        pending = self.scheduler.filter_by_status(completed=False)
        assert len(pending) == 3

    def test_filter_by_status_completed(self):
        self.mochi.tasks[0].mark_complete()
        done = self.scheduler.filter_by_status(completed=True)
        assert len(done) == 1
        assert done[0].description == "Walk"

    def test_filter_by_priority(self):
        high = self.scheduler.filter_by_priority("high")
        assert len(high) == 1
        assert high[0].description == "Walk"


class TestSchedulerConflicts:
    def test_detects_same_time_conflict(self):
        owner = Owner("Jordan")
        pet = Pet("Mochi", "dog")
        owner.add_pet(pet)
        pet.add_task(Task("Walk", "08:00"))
        pet.add_task(Task("Vet visit", "08:00"))
        scheduler = Scheduler(owner)

        conflicts = scheduler.detect_conflicts()
        assert len(conflicts) == 1
        assert "08:00" in conflicts[0]
        assert "Walk" in conflicts[0]
        assert "Vet visit" in conflicts[0]

    def test_no_conflicts_when_different_times(self):
        owner = Owner("Jordan")
        pet = Pet("Mochi", "dog")
        owner.add_pet(pet)
        pet.add_task(Task("Walk", "08:00"))
        pet.add_task(Task("Feed", "12:00"))
        scheduler = Scheduler(owner)

        assert scheduler.detect_conflicts() == []

    def test_conflict_across_pets(self):
        owner = Owner("Jordan")
        p1 = Pet("Mochi", "dog")
        p2 = Pet("Whiskers", "cat")
        owner.add_pet(p1)
        owner.add_pet(p2)
        p1.add_task(Task("Walk Mochi", "09:00"))
        p2.add_task(Task("Feed Whiskers", "09:00"))
        scheduler = Scheduler(owner)

        conflicts = scheduler.detect_conflicts()
        assert len(conflicts) == 1
        assert "09:00" in conflicts[0]

    def test_no_tasks_no_conflicts(self):
        owner = Owner("Jordan")
        owner.add_pet(Pet("Mochi", "dog"))
        scheduler = Scheduler(owner)
        assert scheduler.detect_conflicts() == []


class TestSchedulerRecurrence:
    def test_daily_task_creates_next_day(self):
        owner = Owner("Jordan")
        pet = Pet("Mochi", "dog")
        owner.add_pet(pet)
        today = date.today()
        task = Task("Walk", "08:00", frequency="daily", due_date=today)
        pet.add_task(task)
        scheduler = Scheduler(owner)

        new_task = scheduler.mark_task_complete(task)

        assert task.completed is True
        assert new_task is not None
        assert new_task.completed is False
        assert new_task.due_date == today + timedelta(days=1)
        assert new_task.description == "Walk"
        assert len(pet.tasks) == 2  # original + new

    def test_weekly_task_creates_next_week(self):
        owner = Owner("Jordan")
        pet = Pet("Mochi", "dog")
        owner.add_pet(pet)
        today = date.today()
        task = Task("Grooming", "10:00", frequency="weekly", due_date=today)
        pet.add_task(task)
        scheduler = Scheduler(owner)

        new_task = scheduler.mark_task_complete(task)

        assert new_task is not None
        assert new_task.due_date == today + timedelta(days=7)

    def test_once_task_no_recurrence(self):
        owner = Owner("Jordan")
        pet = Pet("Mochi", "dog")
        owner.add_pet(pet)
        task = Task("Vet visit", "10:00", frequency="once")
        pet.add_task(task)
        scheduler = Scheduler(owner)

        new_task = scheduler.mark_task_complete(task)

        assert task.completed is True
        assert new_task is None
        assert len(pet.tasks) == 1  # no new task added

    def test_recurring_task_preserves_attributes(self):
        owner = Owner("Jordan")
        pet = Pet("Mochi", "dog")
        owner.add_pet(pet)
        task = Task("Walk", "08:00", frequency="daily", priority="high", duration_minutes=30)
        pet.add_task(task)
        scheduler = Scheduler(owner)

        new_task = scheduler.mark_task_complete(task)

        assert new_task.priority == "high"
        assert new_task.duration_minutes == 30
        assert new_task.frequency == "daily"
        assert new_task.pet_name == "Mochi"


class TestSchedulerDailySchedule:
    def test_returns_only_todays_tasks(self):
        owner = Owner("Jordan")
        pet = Pet("Mochi", "dog")
        owner.add_pet(pet)
        today = date.today()
        tomorrow = today + timedelta(days=1)
        pet.add_task(Task("Walk", "08:00", due_date=today))
        pet.add_task(Task("Vet", "10:00", due_date=tomorrow))
        scheduler = Scheduler(owner)

        schedule = scheduler.get_daily_schedule(today)
        assert len(schedule) == 1
        assert schedule[0].description == "Walk"

    def test_daily_schedule_is_sorted(self):
        owner = Owner("Jordan")
        pet = Pet("Mochi", "dog")
        owner.add_pet(pet)
        today = date.today()
        pet.add_task(Task("Evening walk", "18:00", due_date=today))
        pet.add_task(Task("Morning walk", "07:00", due_date=today))
        pet.add_task(Task("Lunch", "12:00", due_date=today))
        scheduler = Scheduler(owner)

        schedule = scheduler.get_daily_schedule(today)
        times = [t.time for t in schedule]
        assert times == ["07:00", "12:00", "18:00"]

    def test_empty_schedule(self):
        owner = Owner("Jordan")
        owner.add_pet(Pet("Mochi", "dog"))
        scheduler = Scheduler(owner)
        assert scheduler.get_daily_schedule() == []
