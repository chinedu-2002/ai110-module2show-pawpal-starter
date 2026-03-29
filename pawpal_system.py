"""PawPal+ Logic Layer — Owner, Pet, Task, and Scheduler classes."""

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional


@dataclass
class Task:
    """Represents a single pet care activity."""

    description: str
    time: str  # "HH:MM" format
    frequency: str = "once"  # "once", "daily", "weekly"
    priority: str = "medium"  # "low", "medium", "high"
    duration_minutes: int = 15
    completed: bool = False
    due_date: Optional[date] = None
    pet_name: str = ""

    def __post_init__(self):
        if self.due_date is None:
            self.due_date = date.today()

    def mark_complete(self):
        """Mark this task as completed."""
        self.completed = True

    def __str__(self):
        status = "Done" if self.completed else "Pending"
        return (
            f"[{status}] {self.time} - {self.description} "
            f"({self.priority} priority, {self.duration_minutes}min, {self.frequency})"
        )


@dataclass
class Pet:
    """Stores pet details and a list of tasks."""

    name: str
    species: str
    age: int = 0
    tasks: list = field(default_factory=list)

    def add_task(self, task: Task):
        """Add a task to this pet's task list."""
        task.pet_name = self.name
        self.tasks.append(task)

    def remove_task(self, description: str) -> bool:
        """Remove a task by description. Returns True if removed."""
        for i, t in enumerate(self.tasks):
            if t.description == description:
                self.tasks.pop(i)
                return True
        return False

    def get_pending_tasks(self) -> list:
        """Return tasks that are not yet completed."""
        return [t for t in self.tasks if not t.completed]

    def __str__(self):
        return f"{self.name} ({self.species}, age {self.age}) — {len(self.tasks)} task(s)"


@dataclass
class Owner:
    """Manages multiple pets and provides access to all their tasks."""

    name: str
    pets: list = field(default_factory=list)

    def add_pet(self, pet: Pet):
        """Add a pet to this owner's list."""
        self.pets.append(pet)

    def remove_pet(self, pet_name: str) -> bool:
        """Remove a pet by name. Returns True if removed."""
        for i, p in enumerate(self.pets):
            if p.name == pet_name:
                self.pets.pop(i)
                return True
        return False

    def get_pet(self, pet_name: str) -> Optional[Pet]:
        """Retrieve a pet by name."""
        for p in self.pets:
            if p.name == pet_name:
                return p
        return None

    def get_all_tasks(self) -> list:
        """Return every task across all pets."""
        all_tasks = []
        for pet in self.pets:
            all_tasks.extend(pet.tasks)
        return all_tasks

    def __str__(self):
        pet_names = ", ".join(p.name for p in self.pets) or "none"
        return f"Owner {self.name} — pets: {pet_names}"


PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


class Scheduler:
    """The brain — retrieves, organizes, and manages tasks across pets."""

    def __init__(self, owner: Owner):
        self.owner = owner

    # ── Sorting ──────────────────────────────────────────────

    def sort_by_time(self, tasks: Optional[list] = None) -> list:
        """Return tasks sorted chronologically by their HH:MM time."""
        if tasks is None:
            tasks = self.owner.get_all_tasks()
        return sorted(tasks, key=lambda t: t.time)

    def sort_by_priority(self, tasks: Optional[list] = None) -> list:
        """Return tasks sorted by priority (high → medium → low)."""
        if tasks is None:
            tasks = self.owner.get_all_tasks()
        return sorted(tasks, key=lambda t: PRIORITY_ORDER.get(t.priority, 1))

    # ── Filtering ────────────────────────────────────────────

    def filter_by_status(self, completed: bool, tasks: Optional[list] = None) -> list:
        """Return only tasks matching the given completion status."""
        if tasks is None:
            tasks = self.owner.get_all_tasks()
        return [t for t in tasks if t.completed == completed]

    def filter_by_pet(self, pet_name: str, tasks: Optional[list] = None) -> list:
        """Return tasks belonging to a specific pet."""
        if tasks is None:
            tasks = self.owner.get_all_tasks()
        return [t for t in tasks if t.pet_name == pet_name]

    def filter_by_priority(self, priority: str, tasks: Optional[list] = None) -> list:
        """Return tasks with a specific priority level."""
        if tasks is None:
            tasks = self.owner.get_all_tasks()
        return [t for t in tasks if t.priority == priority]

    # ── Schedule generation ──────────────────────────────────

    def get_daily_schedule(self, target_date: Optional[date] = None) -> list:
        """Return today's tasks sorted by time."""
        if target_date is None:
            target_date = date.today()
        tasks = [t for t in self.owner.get_all_tasks() if t.due_date == target_date]
        return self.sort_by_time(tasks)

    # ── Conflict detection ───────────────────────────────────

    def detect_conflicts(self, tasks: Optional[list] = None) -> list:
        """Return warning strings for tasks scheduled at the same time."""
        if tasks is None:
            tasks = self.owner.get_all_tasks()

        time_map: dict[str, list[Task]] = {}
        for t in tasks:
            time_map.setdefault(t.time, []).append(t)

        warnings = []
        for time_slot, group in time_map.items():
            if len(group) > 1:
                names = ", ".join(
                    f"'{t.description}' ({t.pet_name})" for t in group
                )
                warnings.append(
                    f"Conflict at {time_slot}: {names} are scheduled at the same time."
                )
        return warnings

    # ── Recurring task logic ─────────────────────────────────

    def mark_task_complete(self, task: Task) -> Optional[Task]:
        """Mark a task complete; if recurring, create the next occurrence.

        Returns the newly created task if one was generated, else None.
        """
        task.mark_complete()

        if task.frequency == "daily":
            return self._create_next_occurrence(task, days=1)
        elif task.frequency == "weekly":
            return self._create_next_occurrence(task, days=7)
        return None

    def _create_next_occurrence(self, task: Task, days: int) -> Task:
        """Clone a recurring task with an updated due date."""
        next_date = (task.due_date or date.today()) + timedelta(days=days)
        new_task = Task(
            description=task.description,
            time=task.time,
            frequency=task.frequency,
            priority=task.priority,
            duration_minutes=task.duration_minutes,
            completed=False,
            due_date=next_date,
            pet_name=task.pet_name,
        )
        # Add to the correct pet
        pet = self.owner.get_pet(task.pet_name)
        if pet:
            pet.tasks.append(new_task)
        return new_task

    # ── Pretty printing ──────────────────────────────────────

    def print_schedule(self, target_date: Optional[date] = None):
        """Print a formatted daily schedule to the terminal."""
        if target_date is None:
            target_date = date.today()

        schedule = self.get_daily_schedule(target_date)
        conflicts = self.detect_conflicts(schedule)

        print(f"\n{'='*50}")
        print(f"  PawPal+ Schedule for {target_date}")
        print(f"{'='*50}")

        if conflicts:
            for w in conflicts:
                print(f"  [!] {w}")
            print()

        if not schedule:
            print("  No tasks scheduled for today.")
        else:
            for task in schedule:
                print(f"  {task}")

        print(f"{'='*50}\n")
