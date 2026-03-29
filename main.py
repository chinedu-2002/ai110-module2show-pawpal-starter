"""CLI demo script — verifies PawPal+ backend logic in the terminal."""

from datetime import date
from pawpal_system import Task, Pet, Owner, Scheduler


def main():
    # ── Create Owner and Pets ────────────────────────────────
    owner = Owner(name="Jordan")

    mochi = Pet(name="Mochi", species="dog", age=3)
    whiskers = Pet(name="Whiskers", species="cat", age=5)

    owner.add_pet(mochi)
    owner.add_pet(whiskers)

    print(owner)
    print(f"  {mochi}")
    print(f"  {whiskers}")

    # ── Add tasks (intentionally out of order) ───────────────
    mochi.add_task(Task("Evening walk", "18:00", frequency="daily", priority="high", duration_minutes=30))
    mochi.add_task(Task("Morning walk", "07:30", frequency="daily", priority="high", duration_minutes=30))
    mochi.add_task(Task("Lunch feeding", "12:00", frequency="daily", priority="medium", duration_minutes=10))
    mochi.add_task(Task("Vet appointment", "10:00", frequency="once", priority="high", duration_minutes=60))

    whiskers.add_task(Task("Morning feeding", "07:30", frequency="daily", priority="high", duration_minutes=5))
    whiskers.add_task(Task("Play time", "15:00", frequency="daily", priority="low", duration_minutes=20))
    whiskers.add_task(Task("Grooming", "10:00", frequency="weekly", priority="medium", duration_minutes=15))

    # ── Scheduler ────────────────────────────────────────────
    scheduler = Scheduler(owner)

    # Print today's full schedule (sorted by time)
    scheduler.print_schedule()

    # ── Demonstrate sorting by priority ──────────────────────
    print("Tasks sorted by priority:")
    for t in scheduler.sort_by_priority():
        print(f"  {t}")

    # ── Demonstrate filtering ────────────────────────────────
    print(f"\nTasks for Mochi only:")
    for t in scheduler.filter_by_pet("Mochi"):
        print(f"  {t}")

    print(f"\nHigh-priority tasks:")
    for t in scheduler.filter_by_priority("high"):
        print(f"  {t}")

    # ── Demonstrate conflict detection ───────────────────────
    print("\nConflict check:")
    conflicts = scheduler.detect_conflicts()
    if conflicts:
        for w in conflicts:
            print(f"  [!] {w}")
    else:
        print("  No conflicts found.")

    # ── Demonstrate recurring task completion ────────────────
    walk = mochi.tasks[0]  # Evening walk (daily)
    print(f"\nCompleting task: {walk.description}")
    new_task = scheduler.mark_task_complete(walk)
    print(f"  Original: {walk}")
    if new_task:
        print(f"  Next occurrence: {new_task} (due {new_task.due_date})")

    # ── Demonstrate mark_complete standalone ──────────────────
    grooming = whiskers.tasks[2]  # Grooming (weekly)
    print(f"\nCompleting task: {grooming.description}")
    new_grooming = scheduler.mark_task_complete(grooming)
    print(f"  Original: {grooming}")
    if new_grooming:
        print(f"  Next occurrence: {new_grooming} (due {new_grooming.due_date})")

    # ── Show pending vs completed ────────────────────────────
    pending = scheduler.filter_by_status(completed=False)
    done = scheduler.filter_by_status(completed=True)
    print(f"\nSummary: {len(done)} completed, {len(pending)} pending")


if __name__ == "__main__":
    main()
